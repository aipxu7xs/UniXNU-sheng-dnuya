python3 scripts/extract-files.py
python3 scripts/extract-files.py --check
# fetch-sources.py clones with --sparse (cone mode by default in current git), then runs
# `sparse-checkout add` with the lock's leading-slash patterns, which cone mode rejects. Create the two
# locked clones in non-cone mode first; fetch-sources.py then verifies their commits and contents.
python3 - <<'PY'
import json, pathlib, subprocess
root = pathlib.Path('drivers/Ath12kWifi')
lock = json.loads((root / 'tools/source-lock.json').read_text())
for name in ('linux', 'freebsd'):
    source, directory = lock[name], root / 'deps' / name
    if directory.exists():
        continue
    directory.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['git', 'clone', '--depth', '1', '--branch', source['ref'], '--filter=blob:none', '--sparse',
                    source['url'], str(directory)], check=True)
    subprocess.run(['git', '-C', str(directory), 'sparse-checkout', 'set', '--no-cone', *source['paths']], check=True)
PY
python3 drivers/Ath12kWifi/tools/fetch-sources.py
