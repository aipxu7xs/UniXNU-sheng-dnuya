import pathlib,hashlib,json,sys
EXPECTED={'scripts/build-boot-runtime.py': 'e12f1e854b26106a5dc0ffb7343a0967205ea5531c15390bde3d01ea943ec870', 'scripts/data/mesa-reviewed-fixes.json': '39ba36c76edc8590b2537239dd8911ec27f60cec1a119dd715b990963f14d54f', 'patches/mesa/reviewed-board-fixes.patch': 'b02a6d5407dc6c66fa1c779002fa03e1e1a6b1058e6b34d21ee716dd2febfa55', 'scripts/data/mesa160-fixes.json': '7bfa66ddad0b724dfeac127d7619e57ef572b91f3531f800cf485a359ec19b68', 'patches/mesa/reviewed-mesa160.patch': '923317663d2da2d2069da7cd247b97d68c4a11e5e9678b723765b928a2886fcc', 'scripts/data/adreno-compiler-inputs.json': 'cfc0b4cd0f666bca8be38414e4b25fc8a10df5ef4beb9ef5f9b5b1b0613c71e0', 'scripts/mesa_reviewed_fixes.py': 'b339eb5410954511e1f1464b29003eee65bea94a67109b8b1f4e1635225aa894', 'scripts/data/mesa160-header-order.json': 'baac241537642b6b39ee67750d67790f03e23497cf162a3d890fd1928d3a10b7', 'patches/mesa/reviewed-mesa160-header-order.patch': 'ac2da522fe17c1bc2576f44ef130b6b0daad51f24400b9bdedb89e9d28caa15b'}
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'UniXNU')
for rel,digest in EXPECTED.items():
 assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==digest,rel+' Mesa160 installed source drift'
 assert not (pathlib.Path('device')/rel).exists(),rel+' device override'
pins=json.loads((root/'scripts/data/adreno-compiler-inputs.json').read_text())
assert len(pins['patches'])==27 and pins['patches'][-2:]==['patches/mesa/reviewed-mesa160.patch','patches/mesa/reviewed-mesa160-header-order.patch']
print('MESA160_PREBUILD_SOURCE',json.dumps(EXPECTED,sort_keys=True))
