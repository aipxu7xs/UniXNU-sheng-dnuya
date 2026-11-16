python3 - <<'PY'
import pathlib,json,hashlib,zlib,base64,runpy
raw=zlib.decompress(base64.b64decode(pathlib.Path('reviewed-mesa-bundle.b64').read_text()))
assert hashlib.sha256(raw).hexdigest()=='7d0bf07f450718b3d6df35d5b6869a5425ea575172b6339311b1e230675e149f'
for name,row in json.loads(raw).items():
 assert name in ('install.py','install-spec.json')
 data=row['text'].encode();assert hashlib.sha256(data).hexdigest()==row['sha256']
 p=pathlib.Path('reviewed-mesa-bundle')/name;p.parent.mkdir(exist_ok=True);p.write_bytes(data)
report=runpy.run_path('reviewed-mesa-bundle/install.py')['install']('UniXNU')
assert len(report)==5
print('MESA_V2_SOURCE_INSTALL',json.dumps(report))
PY
