import pathlib,hashlib,json,sys
EXPECTED={'drivers/AdrenoMetal/bridge/patches/0053-main-optimizations-on-development-8b9b2875.patch': 'c261e55274c5ed926b845e35ffff8c495d03efc73428f646af7ade9710f1d958'}
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'UniXNU')
for rel,digest in EXPECTED.items():
 assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==digest,rel+' StepRefusalCause installed source drift'
src=(root/'drivers/AdrenoMetal/bridge/patches/0053-main-optimizations-on-development-8b9b2875.patch').read_text()
assert '// P0 probe (2D):' in src and 'let refusal = step_error(device, error, &mut state.refusal);' in src,'StepRefusalCause probe hunk missing from installed 0053.patch'
assert '@@ -5328,11 +5351,16 @@ impl CommandBufferShared {' in src,'StepRefusalCause probe hunk header missing from installed 0053.patch'
print('STEP_REFUSAL_CAUSE_PREBUILD_SOURCE',json.dumps(EXPECTED,sort_keys=True))
