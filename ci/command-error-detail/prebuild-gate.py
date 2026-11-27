import pathlib,hashlib,json,sys
EXPECTED={'drivers/AdrenoMetal/bridge/NativeMetalObjects.rs': 'ae561dda2ccf37e93cd7aeb5bf39aa8e5af6459560d6780d72721655a56a3201',
 'drivers/AdrenoMetal/NativeBridgeMetalFrontend.mm': 'a97d624c2506a8e80ac891acaf714924778ae9ec5ac1d53b5907c5bd98677530'}
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'UniXNU')
for rel,digest in EXPECTED.items():
 assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==digest,rel+' CommandErrorDetail installed source drift'
src=(root/'drivers/AdrenoMetal/bridge/NativeMetalObjects.rs').read_text()
assert 'StackBuf' in src and 'pipe=(enc=' in src,'CommandErrorDetail probe text missing from installed source'
fem=(root/'drivers/AdrenoMetal/NativeBridgeMetalFrontend.mm').read_text()
assert 'erec.type=20' in fem,'CommandErrorDetail stacks on CommandErrorTrace: type=20 writer missing'
print('COMMAND_ERROR_DETAIL_PREBUILD_SOURCE',json.dumps(EXPECTED,sort_keys=True))
