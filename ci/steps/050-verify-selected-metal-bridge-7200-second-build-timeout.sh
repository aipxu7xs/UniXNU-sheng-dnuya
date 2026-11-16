python3 - <<'PY'
import ast,pathlib
path=pathlib.Path('UniXNU/scripts/build-adreno-metal-bridge.py')
tree=ast.parse(path.read_text())
limits=[keyword.value.value for node in ast.walk(tree) if isinstance(node,ast.Call) for keyword in node.keywords if keyword.arg=='timeout' and isinstance(keyword.value,ast.Constant)]
assert limits==[7200],limits
assert '0053-main-optimizations-on-development-8b9b2875.patch' in path.read_text()
print('METAL_BRIDGE_TIMEOUT',7200,'job budget 360 minutes')
PY
