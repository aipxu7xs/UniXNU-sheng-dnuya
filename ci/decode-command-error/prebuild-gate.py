import pathlib,hashlib,json,subprocess,sys
EXPECTED={'scripts/decode-gpu-trace.py': '9cdfa3e17722b8319cf089430bcaa620527b98440f885dd43ffb60b783110916'}
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'device')
for rel,digest in EXPECTED.items():
 assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==digest,rel+' DecodeCommandError installed source drift'
src=(root/'scripts/decode-gpu-trace.py').read_text()
assert 'kind==20' in src and 'command_error_check' in src,'DecodeCommandError type=20/21 support missing from installed source'
subprocess.run([sys.executable,'-m','py_compile',str(root/'scripts/decode-gpu-trace.py')],check=True)
print('DECODE_COMMAND_ERROR_PREBUILD_SOURCE',json.dumps(EXPECTED,sort_keys=True))
