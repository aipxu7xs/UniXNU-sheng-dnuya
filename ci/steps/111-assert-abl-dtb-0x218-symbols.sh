python3 - <<'PY'
import hashlib, json, pathlib
candidates = list(pathlib.Path('UniXNU/out/sheng').glob('*/*/tree/build/sheng/sheng.dtb'))
if len(candidates) != 1:
    raise SystemExit('expected one assembled-tree sheng.dtb, found %d' % len(candidates))
p = candidates[0]
work = p.parents[3]
report = json.loads((work / 'boot/boot.json').read_text())
if hashlib.sha256(p.read_bytes()).hexdigest() != report['dtb_sha256']:
    raise SystemExit('DTB differs from the input recorded by boot image assembly')
if not p.is_file():
    raise SystemExit('sheng.dtb missing: the ABL dtb step produced nothing')
data = p.read_bytes()
problems = []
if data[:4] != bytes([0xd0, 0x0d, 0xfe, 0xed]):
    problems.append('wrong fdt magic')
if b'__symbols__\x00' not in data:
    problems.append('no __symbols__ node (ABL dtbo overlay would fail)')
if len(data) < 400000:
    problems.append('only %d bytes; the vendor_boot 0x218 tree is ~506 KB' % len(data))
if problems:
    raise SystemExit('ABL dtb assertion failed: ' + '; '.join(problems))
print('abl dtb ok: %d bytes, __symbols__ present' % len(data))
PY
