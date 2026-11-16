# PIT: raw.githubusercontent.com failed DNS resolution on the runner
# (run 43395310378). Fetch through the API with the workflow token first;
# fall back to raw with retries.
python3 - <<'PY'
import base64, json, os, subprocess, urllib.request
ref = 'b87a4cb89377914fdb0e11482a3e9221491db817'
api = ('https://api.github.com/repos/niuzicheng666-source/UniXNU-sheng/'
       'contents/scripts/fetch-babylon-abldtb.py?ref=' + ref)
req = urllib.request.Request(api, headers={
    'Accept': 'application/vnd.github+json',
    'Authorization': 'Bearer ' + os.environ.get('GITHUB_TOKEN', ''),
    'User-Agent': 'sheng-ci'})
try:
    data = json.loads(urllib.request.urlopen(req, timeout=60).read())
    blob = base64.b64decode(data['content'])
    open('device/scripts/fetch-sheng-abldtb.py', 'wb').write(blob)
    print('fetched fetch-babylon-abldtb.py via api (%d bytes)' % len(blob))
except Exception as error:
    print('api fetch failed (%s); falling back to raw' % error)
    raw = ('https://raw.githubusercontent.com/niuzicheng666-source/UniXNU-sheng/'
           + ref + '/scripts/fetch-babylon-abldtb.py')
    subprocess.run(['curl', '-fsSL', '--retry', '5', '--retry-delay', '3',
                    '--retry-connrefused', '-o',
                    'device/scripts/fetch-sheng-abldtb.py', raw], check=True)
    print('fetched via raw')
PY
python3 - <<'PY'
import pathlib
p = pathlib.Path('device/scripts/fetch-sheng-abldtb.py')
t = p.read_text()
t = t.replace('EXPECTED_MSM_ID = (0x207, 0x20000)',
              'EXPECTED_MSM_ID = (0x218, 0x20000)  # this handset: ABL "Chiptype: 536"')
t = t.replace("OUTPUT = Path('build/babylon/babylon.dtb')",
              "OUTPUT = Path('build/sheng/sheng.dtb')")
p.write_text(t)
b = pathlib.Path('device/board.toml')
bt = b.read_text()
old = '"scripts/import-sheng-uefi.py", "scripts/check-sheng.py"]'
new = '"scripts/import-sheng-uefi.py", "scripts/check-sheng.py", "scripts/fetch-sheng-abldtb.py"]'
if old not in bt:
    raise SystemExit('board.toml preflight anchor not found')
b.write_text(bt.replace(old, new, 1))
print('fetch-sheng-abldtb.py added AFTER check-sheng.py; board.toml preflight patched')
PY
