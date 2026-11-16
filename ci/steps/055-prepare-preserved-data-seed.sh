python3 - <<'PY'
import hashlib, json, os, pathlib, urllib.request
inputs = json.loads(pathlib.Path(os.environ['GITHUB_EVENT_PATH']).read_text())['inputs']
path = pathlib.Path('UniXNU/out/sheng/ipados-27.0.1-24A446/sheng_ipados27/runtime/data.dbr')
url, digest = inputs.get('data_seed_url', ''), inputs.get('data_seed_sha256', '').lower()
if url:
    print('::add-mask::' + url)
    if not url.startswith('https://') or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
        raise SystemExit('A seed URL requires HTTPS and its SHA-256')
    with urllib.request.urlopen(url, timeout=120) as source:
        data = source.read(64 * 1024 * 1024 + 1)
    if len(data) > 64 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != digest:
        raise SystemExit('Seed size or SHA-256 mismatch')
    if path.exists() and path.read_bytes() != data:
        raise SystemExit('Saved seed differs; preserve and inspect it instead of replacing this installation')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
if not path.is_file() and os.environ['INIT_DATA'] != 'true':
    raise SystemExit('No saved seed. Supply the ORIGINAL seed for an existing installation, or select init_data for a FIRST installation')
PY
