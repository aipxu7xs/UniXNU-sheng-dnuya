"""Reassemble the reviewed stock vendor_boot.img from chunks stored in this repo.

The v4 boot transport rebuilds the vendor_boot image from the stock one
(scripts/unixnu/vendor_boot.py in the framework), so the stock image from the
official CN package (OS3.0.306.0.WNXCNXM) must be present in the device
checkout at stock/vendor_boot.img, the path device/board.toml references.
The image is stored under ci/bootimg-v4/stock/ as base64 chunks of its xz
stream because of its size and because the push channel for this repo is
text-only with a per-request size cap; this step decodes, decompresses and
verifies size, sha256 and the vendor_boot v4 header before anything
consumes it.
"""
import base64
import hashlib
import json
import lzma
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent


def main():
    manifest = json.loads((HERE / 'stock-manifest.json').read_text())
    out = pathlib.Path('device/stock/vendor_boot.img')
    out.parent.mkdir(parents=True, exist_ok=True)
    stream = b''.join(
        base64.b64decode((HERE / 'stock' / name).read_bytes())
        for name in manifest['chunks'])
    raw = lzma.decompress(stream)
    digest = hashlib.sha256(raw)
    total = len(raw)
    out.write_bytes(raw)
    if total != manifest['size']:
        raise ValueError(f'stock vendor_boot size drift: {total} != {manifest["size"]}')
    if digest.hexdigest() != manifest['sha256']:
        raise ValueError('stock vendor_boot sha256 drift')
    data = out.read_bytes()
    if data[:8] != b'VNDRBOOT':
        raise ValueError('stock vendor_boot: header magic missing')
    version, page = struct.unpack_from('<2I', data, 8)
    if version != 4 or page != 4096:
        raise ValueError(f'stock vendor_boot: unexpected version/page {version}/{page}')
    print('STOCK_VENDOR_BOOT_STAGED', json.dumps(
        {'path': str(out), 'size': total, 'sha256': digest.hexdigest()}, sort_keys=True))


if __name__ == '__main__':
    sys.exit(main())
