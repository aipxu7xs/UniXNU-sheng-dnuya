"""Verify the packaged Metal bridge carries the step-refusal-cause probe."""
import pathlib,hashlib,sys
PATCH='c261e55274c5ed926b845e35ffff8c495d03efc73428f646af7ade9710f1d958'
PROBE_LINES=[
 '// P0 probe (2D): record the step\'s own refusal first, so a',
 'let refusal = step_error(device, error, &mut state.refusal);',
 'Some(failed) if matches!(refusal, CommandBufferError::Refused) => CommandBufferError::PipelineCreation(',
 '_ => refusal,',
]
def verify(base):
 base=pathlib.Path(base).resolve()
 p=base/'tree/drivers/AdrenoMetal/bridge/patches/0053-main-optimizations-on-development-8b9b2875.patch'
 if not p.is_file():
  print('STEP_REFUSAL_CAUSE_PACKAGED_SKIPPED no packaged tree/drivers/AdrenoMetal/bridge/patches/0053-main-optimizations-on-development-8b9b2875.patch at '+str(p));return
 if hashlib.sha256(p.read_bytes()).hexdigest()!=PATCH:
  raise ValueError('StepRefusalCause packaged patch differs: drivers/AdrenoMetal/bridge/patches/0053-main-optimizations-on-development-8b9b2875.patch')
 modrs=base/'tree/.cache/gpu-reference/metal2vulkan/crates/metal2vulkan-runtime/src/command_buffer/mod.rs'
 if not modrs.is_file():
  print('STEP_REFUSAL_CAUSE_PACKAGED_SKIPPED no packaged tree/.cache/gpu-reference/metal2vulkan/crates/metal2vulkan-runtime/src/command_buffer/mod.rs at '+str(modrs));return
 src=modrs.read_text()
 missing=[ln for ln in PROBE_LINES if ln not in src]
 if missing:
  raise ValueError('StepRefusalCause probe lines missing from packaged mod.rs: '+'; '.join(missing))
 print('STEP_REFUSAL_CAUSE_PACKAGED_SOURCE',PATCH[:12],'probe_lines_present',len(PROBE_LINES))
if __name__=="__main__":
 verify(sys.argv[1] if len(sys.argv)>1 else "UniXNU/out/sheng/ipados-27.0.1-24A446/sheng_ipados27")
