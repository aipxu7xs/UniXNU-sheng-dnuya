python3 - <<'PY'
import pathlib,hashlib,json,tomllib,subprocess,re
base=pathlib.Path('UniXNU/out/sheng/ipados-27.0.1-24A446/sheng_ipados27');tree=base/'tree';manifest=json.loads((base/'package.manifest.json').read_text())
assert manifest['revisions']['package:main']=='71b8a5a3d78edfe6404a706c1ebccd9915fb3c5e'
assert manifest['revisions']['driver:ShengUfs']=='9d527ae1a8d36a7ff210f9f4c9b429549c34c991','effective device-priority UFS revision mismatch'
EXPECTED={'device/drivers/QcaBluetooth/include/qbt.h': '1fbea14a44ef858a58e7deccacb12ff45600b2da9c77cedc212d65810aae1e5b', 'device/drivers/QcaBluetooth/src/qbt_core.c': '890c2073a7c50a0d35349784244bcca5b71d49a9518ac504e078950578b56051', 'device/drivers/QcaBluetooth/tests/runtime.c': '961f328eb9f87344ac040aadb489d5f9a1cde77d0af2f3d9a9f2017acbff39b5', 'device/drivers/QcomIris/include/QcomIrisVpu.h': 'd1bc160f65f2bddc4efcca0957060cc2a16f99eb4eda1f2108af9da7eefd242b', 'device/drivers/QcomIris/kernel/VtHost.cpp': '65881067607902fbad0f33d7190567a2cd1b173a052fa523b0cb220fac4a5c1d', 'device/drivers/QcomIris/src/IrisCore.c': 'a818979de6094de32004117f17e16e5aff8e6b8e1708ec51318a40690ca40492', 'device/drivers/QcomIris/src/IrisVpu.c': '4a28e46cb5c510d4452cde1d0d3477f47a3d757d1ea61d53ddcb348121d2196b', 'device/package/BootDiagExport.c': '2acb848932c30968ed36c7f61580a1575006059b68ec66aff4c2acf18819d81d', 'device/package/BootLatencyFiles.h': 'a2c0d331258a958f371d0c52d71689b832bd0f98cb7f9349a704fc4f8909cec2', 'device/package/BootLog.c': '4e3c9f1c7131317dcb11dfbc1f66275427a7fbe94e59ae79cc92f04f789a7499', 'device/package/BootProgress.c': '1b024d49ffe29efdf7afca51e2672c2154ee30a6b1a2c42fb0f0a71293b458e0', 'device/package/BootTime.h': '8b10cf616cf982b35c808eb00d124d93f3f665cee459f390d7c439a0d9e8649b', 'device/package/BootUiTraceProbe.c': 'ad35538214db3032a68878b5206ee6d5114b5ffbc80e5389e1074c54d3bdc256', 'device/package/HidInputProbe.cpp': '8f5bc71007b4112e9376c044a47a66afbdd827c2ec6f10b7d169a6e8b1041605', 'device/package/ShengBattmgr.c': 'f7698335bf56ab46132014094197799a406105cb7cbca30eab809035e7a22e51', 'device/package/SourceStorage.cpp': '9f9b429404dea054d338ac615a32e00061fc5e5db6ea5356634224b16566ac77', 'device/package/TouchProbe.cpp': '988f6203d149324fdac1b45b4d4b2bff354a1a2e66a58d6f4232b7e7019269ca', 'device/drivers/ShengUfs/NativeUfs.cpp': '35213b6da13b16c2fd6fdd905bb0919657820dad2a5cce7ae2783ad53521e1e6', 'UniXNU/scripts/unixnu/package.py': 'fbca6a8e6c5923e44a09083221229ac1f469b8491821c36842d8f148b436c3e9', 'UniXNU/scripts/unixnu/firmware.py': '4994e4c6428bbc7c0acda4fcdc150e0b3a43608cf2e4d057075d230faf93b9da', 'UniXNU/scripts/unixnu/sheng_firmware_backports.py': 'c1aa9d7e8f08c8d8b1c87fcd35ee50c53ee33c9ead455959c5372ec5c2ba6c70', 'UniXNU/scripts/unixnu/sheng_firmware_backports.json': 'a7d9f1f3dc517b406edc98cb9366867db4b6e68b9a4d7727c3afaaac7b379d30', 'device/board.toml': '1a9e8fdbd5309a37712fdc446f9fd38259ca2ebdefe0a89cf49876a0d998c392', 'UniXNU/components.toml': 'a4e475c1f627e317ddcc1753b7246992241aa883740bc1ad113bca59ef4e5059'}
for rel,digest in EXPECTED.items():
 path=pathlib.Path(rel)
 assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,rel+' checkout changed after prebuild'
 if rel.startswith('device/package/'):actual=tree/'kits/sheng'/rel.removeprefix('device/package/')
 elif rel.startswith('device/drivers/'):actual=tree/'drivers'/rel.removeprefix('device/drivers/')
 elif rel.startswith('UniXNU/'):actual=tree/rel.removeprefix('UniXNU/')
 else:continue
 assert hashlib.sha256(actual.read_bytes()).hexdigest()==digest,str(actual)+' resolved-tree source precedence mismatch'
assert next(x for x in tomllib.loads((tree/'components.toml').read_text())['component'] if x['id']=='ShengUfs')['revision']=='9d527ae1a8d36a7ff210f9f4c9b429549c34c991'
kernel=base/'kernel/kernel.macho';assert hashlib.sha256(kernel.read_bytes()).hexdigest()==manifest['outputs']['kernel.macho']['sha256']
firmware=json.loads((base/'logs/firmware-backports-after-preflight.json').read_text())
assert firmware['stage']=='after-preflight' and firmware['guard']=='0' and firmware['expected_uefi']=='b303410c8e401fc9419ae65a024356ed09a438ef'
assert len(firmware['files'])==4
for row in firmware['files']:
 want='b303410c8e401fc9419ae65a024356ed09a438ef' if row['path'].endswith('SecureBootHandler.c') else 'cfb93724a06ff86ff5ba971413368a7809ee42a5'
 assert row['pin']==want and row['state']=='already-applied',row
 assert hashlib.sha256(pathlib.Path(row['path']).read_text().replace(chr(13)+chr(10),chr(10)).encode()).hexdigest()==row['after_sha256_lf']
# Read native entry nlist records directly; outer MH_FILESET symbol tables may be empty.
import importlib.util
parser_path=tree/'kits/XnuPrelink/kc_image.py'
spec=importlib.util.spec_from_file_location('reviewed_kc_image',parser_path);parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)
"""Inspect defined nlist_64 records in the native entry, never outer fileset nm output."""
import struct
def native_symbol_rows(data,Image):
 root=Image(data);assert root.kind==0xc,'expected MH_FILESET'
 assert 'com.apple.kernel' in root.entries,'native fileset entry absent'
 at=root.entries['com.apple.kernel'][1];assert at>0 and at+32<=len(data)
 native=Image(data,at);found=native.command(2);assert found and found[1]>=24,'native LC_SYMTAB absent'
 symoff,count,stroff,strsize=struct.unpack_from('<4I',data,found[0]+8)
 assert symoff+count*16<=len(data) and stroff+strsize<=len(data),'native symbol table out of bounds'
 rows=[]
 for index in range(count):
  strx,kind,sect,desc,value=struct.unpack_from('<IBBHQ',data,symoff+16*index)
  if kind&0xe0 or kind&0x0e!=0x0e:continue
  assert 0<sect<=len(native.sections),'invalid N_SECT section ordinal'
  if not strx:continue
  assert strx<strsize,'symbol string offset outside table'
  end=data.find(bytes(1),stroff+strx,stroff+strsize);assert end>=0,'unterminated symbol name'
  rows.append({'name':data[stroff+strx:end].decode(),'type':kind,'section':sect,'desc':desc,'value':value,'nlist_offset':symoff+16*index})
 return root,native,rows

def diagnostic_symbol_report(data,Image):
 root,native,rows=native_symbol_rows(data,Image);report={}
 def strong(matches,label):
  assert matches,'missing native diagnostic symbol '+label
  assert len({r['value'] for r in matches})==1,'ambiguous native symbol '+label
  assert all(not r['desc']&0xc0 for r in matches),'weak native diagnostic symbol '+label
  for r in matches:
   section=native.sections[r['section']-1]
   assert section['va']<=r['value']<section['va']+section['size'],'symbol outside declared section '+label
  return matches
 for name in ('boot_diag_scan','boot_diag_stream','boot_diag_request'):
  matches=strong([r for r in rows if r['name'] in (name,'_'+name)],name)
  if name!='boot_diag_request':
   assert all(native.sections[r['section']-1]['segment']=='__TEXT_EXEC' for r in matches),'diagnostic function outside native executable section'
  report[name]=matches
 for label in ('request','status'):
  matches=[r for r in rows if 'unixnu_diag_'+label in r['name'] and 'sysctl' in r['name'].lower()]
  report[label+'_oid_symbols']=strong(matches,'unixnu_diag_'+label)
 report['fileset_native_offset']=native.at;report['native_defined_section_symbols']=len(rows);report['outer_defined_section_symbols']=sum(map(len,root.symbols().values()))
 return report

report=diagnostic_symbol_report(kernel.read_bytes(),parser.Image)
(base/'reviewed-source-audit.json').write_text(json.dumps({'source_sha256':EXPECTED,'ufs':'9d527ae1a8d36a7ff210f9f4c9b429549c34c991','diagnostic_symbols':report,'board_sha256':EXPECTED['device/board.toml']},indent=2))
print('REVIEWED_PACKAGED_SOURCE_IDENTITY',json.dumps(report,sort_keys=True))
PY
