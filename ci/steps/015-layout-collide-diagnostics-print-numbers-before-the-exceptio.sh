python3 - <<'PY'
import pathlib
p = pathlib.Path('UniXNU/kits/XnuPrelink/fileset_layout.py')
t = p.read_text()
old = "        if code_end > self.roots['__DATA']['va']:\n            raise ValueError('Native code would collide with collection data')"
assert t.count(old) == 1, 'collide branch not unique: %d' % t.count(old)
new = ("        if code_end > self.roots['__DATA']['va']:\n"
       "            print(f'LAYOUT COLLIDE: __DATA.va={self.roots[\"__DATA\"][\"va\"]:#x} code_end={code_end:#x} '\n"
       "                  f'over_by={code_end - self.roots[\"__DATA\"][\"va\"]:#x} native_text_exec={next(s for s in self.native.segments if s[\"name\"] == \"__TEXT_EXEC\")[\"size\"]:#x}')\n"
       "            raise ValueError('Native code would collide with collection data')")
t = t.replace(old, new, 1)
assert 'LAYOUT COLLIDE' in t and t.count(old) == 0
import ast
ast.parse(t)
p.write_text(t)
print('layout diagnostics patched')
PY
