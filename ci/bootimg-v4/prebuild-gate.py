"""Prebuild gate for the v4 boot transport experiment.

Asserts, before packaging starts:
- the framework's scripts/unixnu/bootimg.py is exactly the reviewed patched
  source (payload moved into vendor_boot for header v4), and the
  scripts/unixnu/vendor_boot.py it imports is the frozen upstream module;
- device/board.toml carries the reviewed v4 transport settings;
- the stock vendor_boot image is staged at the path board.toml references,
  with the reviewed size and sha256, and parses as a vendor_boot v4 image.
"""
import hashlib
import json
import pathlib
import struct
import sys
import tomllib

EXPECTED = {
    'scripts/unixnu/bootimg.py': '6fcce94fa7ecf82dbc266391eec84b6cb05c1fe7a92b8e56594e12eb24adf85d',
    'scripts/unixnu/vendor_boot.py': '11e9cac117d46b7ad7b826395357a6d82713c2b65f3c1a23acf11f23f721500f',
}
HERE = pathlib.Path(__file__).resolve().parent

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'UniXNU')
for rel, digest in EXPECTED.items():
    assert hashlib.sha256((root / rel).read_bytes()).hexdigest() == digest, \
        rel + ' BootimgV4 installed source drift'

board = tomllib.loads(pathlib.Path('device/board.toml').read_text())
image = board.get('bootimg', {}).get('image', {})
assert image.get('header_version') == 4, 'board bootimg header_version is not 4'
assert image.get('ramdisk_compression') == 'uefi-chunks', 'board ramdisk_compression is not uefi-chunks'
assert image.get('os_version') == '17.0.0' and image.get('os_patch_level') == '2026-08', \
    'board bootimg os metadata drift'
vendor = board.get('bootimg', {}).get('vendor_boot', {})
assert vendor.get('stock') == 'stock/vendor_boot.img', 'board vendor_boot stock path drift'
assert vendor.get('ramdisk_address') == 0x1000000, 'board vendor_boot ramdisk_address drift'

manifest = json.loads((HERE / 'stock-manifest.json').read_text())
stock = pathlib.Path('device/stock/vendor_boot.img')
data = stock.read_bytes()
assert len(data) == manifest['size'], 'staged stock vendor_boot size drift'
assert hashlib.sha256(data).hexdigest() == manifest['sha256'], 'staged stock vendor_boot sha256 drift'
assert data[:8] == b'VNDRBOOT', 'staged stock vendor_boot magic missing'
version, page = struct.unpack_from('<2I', data, 8)
assert version == 4 and page == 4096, 'staged stock vendor_boot is not v4/4096'
print('BOOTIMG_V4_PREBUILD_OK', json.dumps(
    {'bootimg_py': EXPECTED['scripts/unixnu/bootimg.py'],
     'stock_sha256': manifest['sha256']}, sort_keys=True))
