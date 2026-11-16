python3 - <<'PY'
import hashlib, json, pathlib
base = pathlib.Path('UniXNU/out/sheng/ipados-27.0.1-24A446/sheng_ipados27')
manifest = json.loads((base / 'package.manifest.json').read_text())
expected = {'driver:ArmCpu': 'acba4ee2674cfb23434431feb124871ae9b3b581', 'driver:Adreno740': '1c9029bc3216a39d9e514ba41dee12e95e8f3598'}
for key, commit in expected.items():
    assert manifest['revisions'].get(key) == commit, (key, manifest['revisions'].get(key), commit)
probe = base / 'tree/kits/sheng/GpuPowerProbe.cpp'
assert probe.is_file(), 'Missing assembled GPU probe'
assert 'kSelfTestPluginOpenType = 0x4147' in probe.read_text()
print('Verified packaged upstream revisions:', expected)
PY
