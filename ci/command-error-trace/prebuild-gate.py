import pathlib,hashlib,json,sys
EXPECTED={'drivers/AdrenoMetal/NativeBridgeMetalFrontend.mm': '8488fc727da33e7919a1fef856cd3f0ea3d99abdd0e16dd05e1d0e7832cd59ee'}
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'UniXNU')
for rel,digest in EXPECTED.items():
 assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==digest,rel+' CommandErrorTrace installed source drift'
src=(root/'drivers/AdrenoMetal/NativeBridgeMetalFrontend.mm').read_text()
assert 'erec.type=20' in src and 'mrec.type=21' in src,'CommandErrorTrace probe records missing from installed source'
print('COMMAND_ERROR_TRACE_PREBUILD_SOURCE',json.dumps(EXPECTED,sort_keys=True))
