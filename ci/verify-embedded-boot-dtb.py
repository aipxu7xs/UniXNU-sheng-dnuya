#!/usr/bin/env python3
"""Verify that boot.json describes the Android boot image and its embedded FDT."""
import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path

ANDROID_MAGIC = b"ANDROID!"
FDT_MAGIC = b"\xd0\x0d\xfe\xed"
DEFAULT_PAGE_SIZE = 4096
MIN_DTB_BYTES = 400_000


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_u32(data: bytes, offset: int, label: str) -> int:
    if offset < 0 or offset + 4 > len(data):
        raise ValueError(f"truncated boot image while reading {label}")
    return struct.unpack_from("<I", data, offset)[0]


def extract_embedded_dtb(image: bytes, report: dict) -> tuple[bytes, bytes, int]:
    """Return the complete kernel payload, appended FDT, and header version."""
    if not isinstance(report, dict):
        raise ValueError("boot.json root must be an object")
    if len(image) < 44 or image[:8] != ANDROID_MAGIC:
        raise ValueError("boot image magic/header missing")
    version = read_u32(image, 40, "header version")
    if version > 4:
        raise ValueError(f"unsupported Android boot header version {version}")
    if version >= 3:
        kernel_size = read_u32(image, 8, "kernel size")
        ramdisk_size = read_u32(image, 12, "ramdisk size")
        header_size = read_u32(image, 20, "header size")
        if header_size < 44 or header_size > 1_048_576:
            raise ValueError("invalid Android v3+ header size")
        page_size = DEFAULT_PAGE_SIZE
        kernel_start = page_size * max(1, (header_size + page_size - 1) // page_size)
        ramdisk_start = kernel_start + page_size * ((kernel_size + page_size - 1) // page_size)
    else:
        kernel_size = read_u32(image, 8, "kernel size")
        ramdisk_size = read_u32(image, 16, "ramdisk size")
        page_size = read_u32(image, 36, "page size")
        if page_size < 512 or page_size > 65_536 or page_size & (page_size - 1):
            raise ValueError("invalid legacy Android boot page size")
        kernel_start = page_size
        ramdisk_start = page_size * (1 + (kernel_size + page_size - 1) // page_size)
    kernel_end = kernel_start + kernel_size
    if kernel_size <= 0 or kernel_end > len(image):
        raise ValueError("truncated or empty Android kernel section")
    if ramdisk_start + ramdisk_size > len(image):
        raise ValueError("truncated Android ramdisk section")
    kernel = image[kernel_start:kernel_end]
    if len(kernel) != kernel_size:
        raise ValueError("truncated Android kernel section")
    unpacker = zlib.decompressobj(16 + zlib.MAX_WBITS)
    try:
        decoded = unpacker.decompress(kernel)
        decoded += unpacker.flush()
    except zlib.error as exc:
        raise ValueError("kernel gzip stream is invalid") from exc
    if not unpacker.eof or unpacker.unconsumed_tail or not decoded:
        raise ValueError("kernel gzip stream is incomplete or empty")
    dtb = unpacker.unused_data
    if len(dtb) < 8 or dtb[:4] != FDT_MAGIC:
        raise ValueError("gzip stream is not followed by an embedded FDT")
    dtb_size = struct.unpack_from(">I", dtb, 4)[0]
    if dtb_size != len(dtb):
        raise ValueError("embedded FDT size does not match its container")
    if not isinstance(report.get("header_version"), int) or isinstance(report.get("header_version"), bool):
        raise ValueError("boot.json header_version is not an integer")
    if report["header_version"] != version:
        raise ValueError("boot.json header_version does not match boot.img")
    return kernel, dtb, version


def verify(image: bytes, report: dict) -> dict:
    if not isinstance(report, dict):
        raise ValueError("boot.json root must be an object")
    required = ("kernel_sha256", "dtb_sha256", "image_sha256", "image_bytes", "header_version")
    missing = [key for key in required if key not in report]
    if missing:
        raise ValueError("boot.json missing fields: " + ", ".join(missing))
    for key in ("kernel_sha256", "dtb_sha256", "image_sha256"):
        value = report[key]
        if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
            raise ValueError(f"boot.json {key} is not a lowercase SHA-256 digest")
    if not isinstance(report["image_bytes"], int) or isinstance(report["image_bytes"], bool):
        raise ValueError("boot.json image_bytes is not an integer")
    if report["image_bytes"] != len(image):
        raise ValueError("boot.json image_bytes does not match boot.img")
    if report["image_sha256"] != sha256(image):
        raise ValueError("boot.json image_sha256 does not match boot.img")
    kernel, dtb, version = extract_embedded_dtb(image, report)
    if report["kernel_sha256"] != sha256(kernel):
        raise ValueError("boot.json kernel_sha256 does not match boot.img kernel")
    if report["dtb_sha256"] != sha256(dtb):
        raise ValueError("boot.json dtb_sha256 does not match embedded FDT")
    if len(dtb) < MIN_DTB_BYTES:
        raise ValueError(f"embedded FDT is only {len(dtb)} bytes; expected at least {MIN_DTB_BYTES}")
    if b"__symbols__\x00" not in dtb:
        raise ValueError("embedded FDT has no __symbols__ node")
    return {"header_version": version, "image_bytes": len(image), "kernel_bytes": len(kernel),
            "dtb_bytes": len(dtb), "kernel_sha256": sha256(kernel), "dtb_sha256": sha256(dtb),
            "image_sha256": sha256(image)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.image.read_bytes(), json.loads(args.report.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.exit(1, f"embedded boot DTB verification failed: {exc}\n")
    print("embedded boot DTB verified: " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
