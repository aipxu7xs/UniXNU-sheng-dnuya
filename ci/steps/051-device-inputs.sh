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
    # Resolve the immutable lock directly, independently of a moving branch/tag.
    commit = source['commit']
    assert len(commit) == 40 and all(c in '0123456789abcdef' for c in commit)
    subprocess.run(['git', 'init', '--quiet', str(directory)], check=True)
    subprocess.run(['git', '-C', str(directory), 'remote', 'add', 'origin', source['url']], check=True)
    subprocess.run(['git', '-C', str(directory), 'sparse-checkout', 'set', '--no-cone', *source['paths']], check=True)
    subprocess.run(['git', '-C', str(directory), 'fetch', '--depth', '1', '--filter=blob:none', 'origin', commit], check=True)
    fetched = subprocess.check_output(['git', '-C', str(directory), 'rev-parse', 'FETCH_HEAD^{commit}'], text=True).strip()
    assert fetched == commit, f'{name}: fetched object differs from source lock'
    subprocess.run(['git', '-C', str(directory), 'checkout', '--detach', commit], check=True)
    actual = subprocess.check_output(['git', '-C', str(directory), 'rev-parse', 'HEAD'], text=True).strip()
    assert actual == commit, f'{name}: checkout differs from source lock'
PY
python3 drivers/Ath12kWifi/tools/fetch-sources.py
