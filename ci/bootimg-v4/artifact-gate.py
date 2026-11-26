"""Verify the packaged images really used the v4 boot transport.

Checks the packaging outputs of one build:
- boot/boot.json records header_version 4 and a vendor_boot image whose
  recorded sha256/size match the shipped boot/vendor_boot.img byte for byte;
- boot/vendor_boot.json records the reviewed stock image as its input;
- boot/boot.img carries header version 4 and an empty ramdisk (the payload
  moved to vendor_boot), and boot/vendor_boot.img is a vendor_boot v4 image
  of exactly the stock partition size.
"""
import hashlib
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent


def verify(base):
    base = pathlib.Path(base).resolve()
    boot = base / 'boot'
    report = json.loads((boot / 'boot.json').read_text())
    if report.get('header_version') != 4:
        raise ValueError('packaged boot image header_version is not 4')
    if report.get('ramdisk_bytes') != 0:
        raise ValueError('packaged boot image still carries a ramdisk; payload did not move')
    vendor = boot / 'vendor_boot.img'
    if not vendor.is_file():
        raise ValueError('packaged vendor_boot.img missing')
    data = vendor.read_bytes()
    if pathlib.Path(str(report.get('vendor_boot', ''))).name != 'vendor_boot.img':
        raise ValueError('boot.json vendor_boot path does not name the shipped image')
    if report.get('vendor_boot_sha256') != hashlib.sha256(data).hexdigest():
        raise ValueError('boot.json vendor_boot_sha256 does not match the shipped image')
    if report.get('vendor_boot_bytes') != len(data):
        raise ValueError('boot.json vendor_boot_bytes does not match the shipped image')
    if data[:8] != b'VNDRBOOT':
        raise ValueError('shipped vendor_boot.img magic missing')
    version, page = struct.unpack_from('<2I', data, 8)
    if version != 4 or page != 4096:
        raise ValueError('shipped vendor_boot.img is not v4/4096')
    manifest = json.loads((HERE / 'stock-manifest.json').read_text())
    if len(data) != manifest['size']:
        raise ValueError('shipped vendor_boot.img size differs from the stock partition size')
    vreport = json.loads((boot / 'vendor_boot.json').read_text())
    if vreport.get('stock_sha256') != manifest['sha256']:
        raise ValueError('vendor_boot.json was not built from the reviewed stock image')
    boot_img = (boot / 'boot.img').read_bytes()
    if boot_img[:8] != b'ANDROID!':
        raise ValueError('boot.img magic missing')
    if struct.unpack_from('<I', boot_img, 40)[0] != 4:
        raise ValueError('boot.img header version field is not 4')
    print('BOOTIMG_V4_ARTIFACT_OK', json.dumps(
        {'vendor_boot_sha256': report['vendor_boot_sha256'],
         'vendor_boot_bytes': len(data)}, sort_keys=True))
    return report


if __name__ == '__main__':
    base = pathlib.Path(sys.argv[1] if len(sys.argv) > 1
                        else 'UniXNU/out/sheng/ipados-27.0.1-24A446/sheng_ipados27')
    verify(base)
