python3 - <<'PY'
import hashlib,json,pathlib,struct,zlib,os,subprocess,tempfile
BASE=pathlib.Path('UniXNU/out/sheng/ipados-27.0.1-24A446/sheng_ipados27')
COMPONENT='54c18dcffc359d21f4e620c3b38b3908cecc46a5';TRANSLATOR='8b9b2875ab2ca32de30db6d5c396e1469e164bee'
def sha(path):return hashlib.file_digest(path.open('rb'),'sha256').hexdigest()
def translator_tree(source,overlay):
 assert subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()==TRANSLATOR
 # Scratch index only: bind actual patched worktree and exact selected overlay to the same Git tree.
 with tempfile.TemporaryDirectory() as td:
  env=dict(os.environ,GIT_INDEX_FILE=str(pathlib.Path(td)/'index'))
  def git(*args):return subprocess.check_output(['git','-C',str(source),*args],env=env,text=True).strip()
  git('read-tree','HEAD');git('apply','--cached',str(overlay.resolve()));expected=git('write-tree')
  git('read-tree','HEAD');git('add','-A');actual=git('write-tree')
  assert actual==expected,'translator working tree differs from selected overlay'
  return actual
def verify():

 manifest=json.loads((BASE/'package.manifest.json').read_text())
 assert manifest['revisions']['package:main']=='71b8a5a3d78edfe6404a706c1ebccd9915fb3c5e'
 assert manifest['revisions']['driver:AdrenoMetal']==COMPONENT
 tree=BASE/'tree';build=tree/'build'
 expected_scripts={'scripts/build-adreno-metal-bridge.py':'83fb5781a5da900b4661870bf4b9e87194985141be6522d450af82b02e18d67f','scripts/build-adreno-metal-plugin.py':'332401a82955428ee88e0563e0c9a3c686641096e498fccb0eaddaedeb2682ac','scripts/data/gpu-metal-vulkan-inputs.json':'090a7c255f1a393e3013b4b54b94048dc463e5d3ea1fff8cf580beea46a576cb'}
 for relative,digest in expected_scripts.items():assert sha(tree/relative)==digest,relative+' assembled-tree override'
 record=json.loads((build/'adreno-metal-bridge/ios27/libadreno_metal_bridge.a.json').read_text());identity=record['identity']
 assert identity['target']=='ios27' and identity['component']==COMPONENT and identity['translator']==TRANSLATOR
 assert sha(build/'adreno-metal-bridge/ios27/libadreno_metal_bridge.a')==record['sha256']
 plugin=build/'adreno-metal-plugin27/NativeAdrenoMetal.bundle/gpu-build.json'
 info=json.loads(plugin.read_text())
 assert info['target']=='ios27' and info['component']==COMPONENT and info['bridge_component']==COMPONENT
 assert info['runtime']==identity['runtime'] and info['cache_build']==info['runtime']+'-'+info['turnip_uuid']
 assert len(info['turnip_uuid'])==32 and not info['runtime_draw_checks']
 source_tree=translator_tree(tree/'.cache/gpu-reference/metal2vulkan',tree/'drivers/AdrenoMetal/bridge/patches/0053-main-optimizations-on-development-8b9b2875.patch')
 assert identity['source_tree']==source_tree
 assert identity['runtime']==hashlib.sha256((TRANSLATOR+'\n'+source_tree).encode()).hexdigest()[:32]
 bundle=plugin.parent
 expected_entries={name:(bundle/name).read_bytes() for name in ('gpu-build.json','NativeAdrenoMetal','libvulkan_freedreno.dylib')}
 assert all(expected_entries.values()),'empty signed bundle output'
 # Match the selected plugin builder's actual hash algorithm exactly (it excludes tools and .c).
 digest=hashlib.sha256();component=tree/'drivers/AdrenoMetal'
 for path in sorted(component.rglob('*')):
  if path.is_file() and '.git' not in path.parts and path.relative_to(component).parts[0]!='tools' and path.suffix in ('.h','.mm','.cpp','.rs','.patch'):
   digest.update(str(path.relative_to(component)).encode());digest.update(path.read_bytes())
 assert info['metal_source_sha256']==digest.hexdigest()
 inputs=json.loads((BASE/'runtime/inputs.json').read_text())['inputs'];addon=pathlib.Path(inputs['gpu_addon']['path'])
 assert sha(addon)==inputs['gpu_addon']['sha256']==manifest['runtime']['inputs']['gpu_addon']
 data=addon.read_bytes();assert data[:8]==b'NGPUADD2' and len(data)>=24 and struct.unpack_from('<Q',data,16)[0]==len(data)
 at=24;found={}
 for _ in range(struct.unpack_from('<I',data,8)[0]):
  assert at+24<=len(data)
  length,mode,size,packed=struct.unpack_from('<IIQQ',data,at);at+=24
  assert 1<length<=160 and at+length<=len(data) and data[at+length-1]==0
  name=data[at:at+length-1].decode();assert not name.startswith('/') and '..' not in pathlib.PurePosixPath(name).parts
  at+=(length+7)&~7;assert at+packed<=len(data)
  for basename,expected in expected_entries.items():
   if name.endswith('NativeAdrenoMetal.bundle/'+basename):
    assert basename not in found,'duplicate embedded '+basename
    body=zlib.decompress(data[at:at+packed]);assert len(body)==size and body==expected,'embedded bytes differ: '+name
    found[basename]=name
  at+=(packed+7)&~7
 assert at==len(data) and set(found)==set(expected_entries),found
 assert len({path.rsplit('/',1)[0] for path in found.values()})==1,'bundle entries have different prefixes'
 print('METAL_ARTIFACT_IDENTITY',COMPONENT,TRANSLATOR,identity['runtime'],info['cache_build'],found)
if __name__=='__main__':verify()
PY
