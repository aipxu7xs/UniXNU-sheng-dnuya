import pathlib,hashlib,json,sys
EXPECTED={'scripts/build-boot-runtime.py': 'e12f1e854b26106a5dc0ffb7343a0967205ea5531c15390bde3d01ea943ec870', 'scripts/data/mesa-reviewed-fixes.json': '39ba36c76edc8590b2537239dd8911ec27f60cec1a119dd715b990963f14d54f', 'patches/mesa/reviewed-board-fixes.patch': 'b02a6d5407dc6c66fa1c779002fa03e1e1a6b1058e6b34d21ee716dd2febfa55', 'scripts/data/adreno-compiler-inputs.json': 'c0bf0ed39ca65ee6b59dcb73e74ac99d30467616bdd3fd3949ed6402538e0f7a', 'scripts/mesa_reviewed_fixes.py': 'f55aec7f07d63412237c93eef08b8275833fed42f0066b91064c58f49861347e', 'scripts/data/mesa160-fixes.json': '7bfa66ddad0b724dfeac127d7619e57ef572b91f3531f800cf485a359ec19b68', 'patches/mesa/reviewed-mesa160.patch': '923317663d2da2d2069da7cd247b97d68c4a11e5e9678b723765b928a2886fcc'}
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'UniXNU')
for rel,digest in EXPECTED.items():
 assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==digest,rel+' Mesa160 installed source drift'
 assert not (pathlib.Path('device')/rel).exists(),rel+' device override'
pins=json.loads((root/'scripts/data/adreno-compiler-inputs.json').read_text())
assert len(pins['patches'])==26 and pins['patches'][-1]=='patches/mesa/reviewed-mesa160.patch'
print('MESA160_PREBUILD_SOURCE',json.dumps(EXPECTED,sort_keys=True))
