"""Reassemble the reviewed stock vendor_boot.img from chunks stored in this repo.

The v4 boot transport rebuilds the vendor_boot image from the stock one
(scripts/unixnu/vendor_boot.py in the framework), so the stock image from the
official CN package (OS3.0.306.0.WNXCNXM) must be present in the device
checkout at stock/vendor_boot.img, the path device/board.toml references.
The image is stored split into chunks under ci/bootimg-v4/stock/ because of
its size; this step concatenates them and verifies size, sha256 and the
vendor_boot v4 header before anything consumes it.
"""
import hashlib
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent


def main():
    manifest = json.loads((HERE / 'stock-manifest.json').read_text())
    out = pathlib.Path('device/stock/vendor_boot.img')
    out.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    total = 0
    with out.open('wb') as fh:
        for name in manifest['chunks']:
            data = (HERE / 'stock' / name).read_bytes()
            digest.update(data)
            total += len(data)
            fh.write(data)
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
