python3 - <<'PY'
import pathlib
p = pathlib.Path('device/scripts/build-gop-legacy-display-27.py')
t = p.read_text()
anchor = "    cmd += ['-Wall', '-Wextra', '-Werror', '-Wno-unused-parameter', '-Wno-unnecessary-virtual-specifier', '-Wno-c99-designator',\n            '-Wno-reorder-init-list', '-Wno-deprecated-enum-enum-conversion', '-I', str(ROOT / '.cache/xnu-work/osfmk'), *extra]"
assert t.count(anchor) == 1, 'compile_cpp anchor not unique: %d' % t.count(anchor)
new = anchor.replace("*extra]", "*extra, '-Oz', '-fno-asynchronous-unwind-tables', '-fno-unwind-tables']")
t = t.replace(anchor, new, 1)
assert new in t, 'compile_cpp replacement did not land'
anchor_c = "    cmd += ['-Wall', '-Wextra', '-Werror', '-mgeneral-regs-only', '-I', str(ROOT / '.cache/xnu-work/osfmk'), '-I', str(ROOT / 'kits/sheng')]"
assert t.count(anchor_c) == 1, 'compile_c anchor not unique: %d' % t.count(anchor_c)
new_c = anchor_c.replace("'-I', str(ROOT / 'kits/sheng')]", "'-I', str(ROOT / 'kits/sheng'), '-Oz', '-fno-asynchronous-unwind-tables', '-fno-unwind-tables']")
t = t.replace(anchor_c, new_c, 1)
assert new_c in t, 'compile_c replacement did not land'
p.write_text(t)
print('build-gop-legacy-display-27.py: compile_cpp and compile_c now emit -Oz')
PY
python3 - <<'PY'
import pathlib
t = pathlib.Path('device/scripts/build-gop-legacy-display-27.py').read_text()
import re
n = len(re.findall(r"-Os\b", t)) + len(re.findall(r"-Oz\b", t))
assert n >= 3, 'expected at least 3 -Os/-Oz tokens (2 patched -Oz + 1 official VPU -Os), got %d' % n
assert t.count('-fno-asynchronous-unwind-tables') >= 2, 'no-unwind flags not landed: %d' % t.count('-fno-asynchronous-unwind-tables')
assert "*extra, '-Oz'" in t and "kits/sheng'), '-Oz'" in t, 'patched -Oz anchors missing'
import ast
ast.parse(t)
print('assertion ok: -Os/-Oz tokens =', n, '; anchors applied; script parses')
PY
