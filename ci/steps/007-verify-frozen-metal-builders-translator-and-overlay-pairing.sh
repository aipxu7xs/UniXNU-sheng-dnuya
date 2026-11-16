python3 - <<'PY'
import hashlib,json,pathlib,ast
root=pathlib.Path('UniXNU')
FILES={'scripts/build-adreno-metal-bridge.py': '83fb5781a5da900b4661870bf4b9e87194985141be6522d450af82b02e18d67f', 'scripts/build-adreno-metal-plugin.py': '332401a82955428ee88e0563e0c9a3c686641096e498fccb0eaddaedeb2682ac', 'scripts/data/gpu-metal-vulkan-inputs.json': '090a7c255f1a393e3013b4b54b94048dc463e5d3ea1fff8cf580beea46a576cb'}
for relative,digest in FILES.items():
 path=root/relative
 assert not (pathlib.Path('device')/relative).exists(),relative+' device override'
 assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,relative+' frozen-source mismatch'
 if path.suffix=='.py':ast.parse(path.read_text())
pins=json.loads((root/'scripts/data/gpu-metal-vulkan-inputs.json').read_text())
assert pins['translator']['commit']=='8b9b2875ab2ca32de30db6d5c396e1469e164bee'
assert '0053-main-optimizations-on-development-8b9b2875.patch' in (root/'scripts/build-adreno-metal-bridge.py').read_text()
print('FROZEN_METAL_SOURCE',json.dumps(FILES,sort_keys=True))
PY
