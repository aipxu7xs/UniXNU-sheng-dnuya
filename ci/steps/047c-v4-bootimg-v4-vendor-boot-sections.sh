python3 - <<'PY'
import pathlib, tomllib
p = pathlib.Path('device/board.toml')
t = p.read_text()
if '["bootimg"."image"]' in t or '["bootimg"."vendor_boot"]' in t:
    raise SystemExit('bootimg v4 sections already present in board.toml')
INJECT = ('\n["bootimg"."image"]\n'
          '"header_version" = 4\n'
          '"os_version" = "17.0.0"\n'
          '"os_patch_level" = "2026-08"\n'
          '"ramdisk_compression" = "uefi-chunks"\n'
          '"ramdisk_max_bytes" = 199229440\n'
          '\n'
          '["bootimg"."vendor_boot"]\n'
          '"stock" = "stock/vendor_boot.img"\n'
          '"ramdisk_address" = 0x1000000\n')
lines = t.split('\n')
idx = [i for i, line in enumerate(lines) if '"dtb_node"' in line]
if len(idx) != 1:
    raise SystemExit('bootimg v4: dtb_node anchor missing or ambiguous')
i = idx[0]
t2 = '\n'.join(lines[:i + 1]) + INJECT + '\n'.join(lines[i + 1:])
board = tomllib.loads(t2)
image = board.get('bootimg', {}).get('image', {})
vendor = board.get('bootimg', {}).get('vendor_boot', {})
if image.get('header_version') != 4 or image.get('ramdisk_compression') != 'uefi-chunks':
    raise SystemExit('bootimg v4: injected image settings do not parse back')
if vendor.get('stock') != 'stock/vendor_boot.img' or vendor.get('ramdisk_address') != 0x1000000:
    raise SystemExit('bootimg v4: injected vendor_boot settings do not parse back')
if '"dpu-early-done=1"' in t2:
    raise SystemExit('bootimg v4: dpu-early-done must stay out of the v4 experiment line')
p.write_text(t2)
print('bootimg v4: header_version=4, ramdisk moved to vendor_boot (stock/vendor_boot.img)')
PY
