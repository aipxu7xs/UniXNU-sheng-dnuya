#!/usr/bin/env bash
set -euo pipefail
BASE="UniXNU/out/sheng/ipados-27.0.1-24A446/sheng_ipados27"
python3 - "$BASE" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1]) / 'tree/build/sheng/sheng.dtb'
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
print('assembled ABL DTB input ok: %d bytes, __symbols__ present' % len(data))
PY
python3 "$GITHUB_WORKSPACE/ci-self/ci/verify-embedded-boot-dtb.py" --image "$BASE/boot/boot.img" --report "$BASE/boot/boot.json"