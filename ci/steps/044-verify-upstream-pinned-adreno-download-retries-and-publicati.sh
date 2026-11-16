python3 - <<'PY'
import ast,hashlib,pathlib
p=pathlib.Path('UniXNU/scripts/fetch-adreno-inputs.py')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='134d51c8f409673d78f97250f38ba370dbe4324e73ccee1b948f74831a3d3ca1','unexpected Adreno input fetch source'
t=ast.parse(p.read_text());download=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='download')
assert any(isinstance(n,ast.For) and ast.unparse(n.iter)=='range(3)' for n in ast.walk(download))
assert any(isinstance(n,ast.Call) and any(k.arg=='timeout' and isinstance(k.value,ast.Constant) and k.value.value==45 for k in n.keywords) for n in ast.walk(download))
assert 'raw.githubusercontent.com' in p.read_text() and 'temporary.replace(path)' in p.read_text()
print('UPSTREAM_PINNED_ADRENO_DOWNLOAD',3,45,'atomic publication and hash verification')
PY
