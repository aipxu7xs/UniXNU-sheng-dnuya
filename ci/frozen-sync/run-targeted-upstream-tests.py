"""Run selected unchanged upstream build tests on the native POSIX build host."""
from pathlib import Path
import json
import subprocess
import sys
SUITES = ('test_archive_providers.py', 'test_firmware_toolchain.py', 'test_payload_pending.py', 'test_release_reference.py', 'test_root_policy_inputs.py')
root = Path(sys.argv[1]).resolve(strict=True)
results = []
for name in SUITES:
    result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests/build', '-p', name], cwd=root)
    results.append(dict(suite=name, exit=result.returncode))
print('TARGETED_UPSTREAM_TESTS', json.dumps(results))
if any(row['exit'] for row in results):
    raise SystemExit(1)
