python3 - <<'PY'
import base64,hashlib,json,pathlib,zlib,runpy
payload=zlib.decompress(base64.b64decode(pathlib.Path('reviewed-source-bundle.b64').read_text()))
assert hashlib.sha256(payload).hexdigest()=='b6c1f5bd9841dfd9bf2338fbc8b54cfa660e389576ee2170928c5c5fe5fb947d','reviewed helper bundle identity mismatch'
files=json.loads(payload);root=pathlib.Path('reviewed-source-bundle')
for rel,row in files.items():
 path=pathlib.PurePosixPath(rel);assert not path.is_absolute() and '..' not in path.parts
 data=base64.b64decode(row['base64']);assert hashlib.sha256(data).hexdigest()==row['sha256'],rel
 target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
report={}
for key,relative,args in [('core','core/apply.py',('device',)),('shared','core/shared/apply.py',('device',)),('diagnostic','diagnostic/apply.py',('device',)),('bluetooth','peripheral/apply.py',('device/drivers/QcaBluetooth','bluetooth-counters')),('iris','iris/apply.py',('device/drivers/QcomIris',))]:
 report[key]=runpy.run_path(str(root/relative))['apply'](*args)
# Final source hashes close over all package changes including overlapping BootLog core/shared/diagnostic edits.
paths=set()
for spec in ('core/spec.json','core/shared/spec.json','diagnostic/spec.json'):
 for row in json.loads((root/spec).read_text())['files']:paths.add('device/'+row['path'])
for row in json.loads((root/'peripheral/selected/manifest.json').read_text())['bluetooth-counters']['files']:paths.add('device/drivers/QcaBluetooth/'+row['path'])
for rel in runpy.run_path(str(root/'iris/apply.py'))['PINS']:paths.add('device/drivers/QcomIris/'+rel)
report['source_sha256']={p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in sorted(paths)}
pathlib.Path('reviewed-source-report.json').write_text(json.dumps(report,indent=2))
print('REVIEWED_SOURCE_BATCH',json.dumps(report['source_sha256'],sort_keys=True))
PY
