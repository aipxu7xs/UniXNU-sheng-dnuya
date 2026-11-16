python3 - <<'PY'
import pathlib,hashlib,json
EXPECTED={'scripts/build-boot-runtime.py': 'e12f1e854b26106a5dc0ffb7343a0967205ea5531c15390bde3d01ea943ec870', 'scripts/data/adreno-compiler-inputs.json': '9217fa6f709d8ff5fdb41d6a7d35fbb6f7d70f6aed832f6ec57c9468af932f49', 'scripts/mesa_reviewed_fixes.py': 'dd0aa581cdba379947d45bb63e575458c26e23d828eb37b49c9135b4ff1ff56f', 'scripts/data/mesa-reviewed-fixes.json': '39ba36c76edc8590b2537239dd8911ec27f60cec1a119dd715b990963f14d54f', 'patches/mesa/reviewed-board-fixes.patch': 'b02a6d5407dc6c66fa1c779002fa03e1e1a6b1058e6b34d21ee716dd2febfa55'}
for rel,digest in EXPECTED.items():
 assert hashlib.sha256((pathlib.Path('UniXNU')/rel).read_bytes()).hexdigest()==digest,rel+' reviewed Mesa installation drift'
 assert not (pathlib.Path('device')/rel).exists(),rel+' device override'
pins=json.loads(pathlib.Path('UniXNU/scripts/data/adreno-compiler-inputs.json').read_text())
assert pins['mesa']['commit']=='85fda3b36405bcaea8bffc64aa4f2651dc90770d' and len(pins['patches'])==25
print('MESA_V2_PREBUILD_SOURCE',json.dumps(EXPECTED,sort_keys=True))
PY
