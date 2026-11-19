python3 - <<'PY'
import hashlib, json, pathlib
base = pathlib.Path('UniXNU/out/sheng/ipados-27.0.1-24A446/sheng_ipados27')
manifest = json.loads((base / 'package.manifest.json').read_text())
expected = {'driver:ArmCpu': '5f3702697ed80fd2e98594de1af7e32b4b77b08b', 'driver:Adreno740': '1c9029bc3216a39d9e514ba41dee12e95e8f3598', 'driver:AdrenoMetal': 'c9ebd2fb17253996f0a8d835c9ab7c2f740778e1', 'soc:sm8550': '2dc650ca76ae38715cd0712e60a44b14fe251745'}
for key, commit in expected.items():
    assert manifest['revisions'].get(key) == commit, (key, manifest['revisions'].get(key), commit)
probe = base / 'tree/kits/sheng/GpuPowerProbe.cpp'
assert probe.is_file(), 'Missing assembled GPU probe'
assert 'kSelfTestPluginOpenType = 0x4147' in probe.read_text()
print('Verified packaged upstream revisions:', expected)
PY
