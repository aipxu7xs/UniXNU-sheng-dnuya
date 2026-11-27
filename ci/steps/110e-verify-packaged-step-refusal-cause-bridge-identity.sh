python3 - <<'PY'
# 110e: verify the packaged Metal bridge carries the step-refusal-cause (2D)
# probe, in the step-110 identity chain. The 2D probe rides inside
# drivers/AdrenoMetal/bridge/patches/0053-....patch (appended hunk, installed
# in the CI worktree before packaging; NOT an AdrenoMetal commit). Base 110
# already proves the chain self-consistent for whatever patch file is in the
# tree; this variant pins the probe-specific facts: the packaged patch file
# carries the probe hunk, the packaged mod.rs carries the probe lines, and
# the runtime id recomputed from the probe-carrying tree matches the build
# record. The runtime id changes with the patch content (states[-1]), so the
# first boot on this image re-triggers the shader cache (PrimeShaders.h).
import hashlib,json,pathlib,subprocess,tempfile,os
BASE=pathlib.Path('UniXNU/out/sheng/ipados-27.0.1-24A446/sheng_ipados27')
TRANSLATOR='8b9b2875ab2ca32de30db6d5c396e1469e164bee'
PATCH_REL='drivers/AdrenoMetal/bridge/patches/0053-main-optimizations-on-development-8b9b2875.patch'
MODRS_REL='crates/metal2vulkan-runtime/src/command_buffer/mod.rs'
PROBE_LINES=[
 '// P0 probe (2D): record the step\'s own refusal first, so a',
 'let refusal = step_error(device, error, &mut state.refusal);',
 'Some(failed) if matches!(refusal, CommandBufferError::Refused) => CommandBufferError::PipelineCreation(',
 '_ => refusal,',
]
def sha(path):return hashlib.file_digest(path.open('rb'),'sha256').hexdigest()
def translator_tree(source,overlay):
 assert subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()==TRANSLATOR
 with tempfile.TemporaryDirectory() as td:
  env=dict(os.environ,GIT_INDEX_FILE=str(pathlib.Path(td)/'index'))
  def git(*args):return subprocess.check_output(['git','-C',str(source),*args],env=env,text=True).strip()
  git('read-tree','HEAD');git('apply','--cached',str(overlay.resolve()));expected=git('write-tree')
  git('read-tree','HEAD');git('add','-A');actual=git('write-tree')
  assert actual==expected,'translator working tree differs from selected overlay'
  return actual
def verify():
 manifest=json.loads((BASE/'package.manifest.json').read_text())
 tree=BASE/'tree';build=tree/'build'
 record=json.loads((build/'adreno-metal-bridge/ios27/libadreno_metal_bridge.a.json').read_text());identity=record['identity']
 patch=tree/PATCH_REL
 assert patch.is_file(),'packaged 0053.patch missing'
 ptext=patch.read_text()
 assert '// P0 probe (2D):' in ptext and '@@ -5328,11 +5351,16 @@ impl CommandBufferShared {' in ptext,'packaged 0053.patch does not carry the 2D probe hunk'
 modrs=tree/'.cache/gpu-reference/metal2vulkan'/MODRS_REL
 assert modrs.is_file(),'packaged mod.rs missing'
 src=modrs.read_text()
 missing=[ln for ln in PROBE_LINES if ln not in src]
 assert not missing,'2D probe lines missing from packaged mod.rs: '+'; '.join(missing)
 source_tree=translator_tree(tree/'.cache/gpu-reference/metal2vulkan',patch)
 assert identity['source_tree']==source_tree
 assert identity['runtime']==hashlib.sha256((TRANSLATOR+'\n'+source_tree).encode()).hexdigest()[:32]
 print('STEP_REFUSAL_CAUSE_BRIDGE_IDENTITY',identity['runtime'],'probe_hunk_in_patch',True,'probe_lines_in_modrs',len(PROBE_LINES))
if __name__=='__main__':verify()
PY
