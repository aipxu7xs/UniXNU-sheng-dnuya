import pathlib,hashlib,json,sys
EXPECTED={'drivers/AdrenoMetal/NativeBridgeMetalFrontend.mm': 'a97d624c2506a8e80ac891acaf714924778ae9ec5ac1d53b5907c5bd98677530'}
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'UniXNU')
for rel,digest in EXPECTED.items():
 assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==digest,rel+' CommandErrorTrace installed source drift'
src=(root/'drivers/AdrenoMetal/NativeBridgeMetalFrontend.mm').read_text()
assert 'erec.type=20' in src and 'mrec.type=21' in src,'CommandErrorTrace probe records missing from installed source'
print('COMMAND_ERROR_TRACE_PREBUILD_SOURCE',json.dumps(EXPECTED,sort_keys=True))
