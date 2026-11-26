"""Verify the packaged native legacy display was compiled from the reviewed retire-pacing source (stacked on early-done)."""
import pathlib,json,sys
WANT={'drivers/GopFramebuffer/NativeLegacyDisplay.cpp': 'b92a7fa026c215c708a5d1a4a1f0e3a67d67dfc84f8a2cbbadba362f10d5d8fd', 'drivers/GopFramebuffer/NativeLegacyRequest.h': '81e89e1f40f2f1d0919567f53bc0564c650488843082693d00b9ea256cafae21', 'drivers/GopFramebuffer/NativeGOPPresenter.cpp': '6260912583decf8c4374085c5021cffa2f59898fd5c2873d75871196839dab66'}
def check_object_strings(base):
 build_dir=base/'tree/build/native-legacy-display'
 candidates=[build_dir/'NativeLegacyDisplay.o',build_dir/'NativeLegacyDisplay.late.o']
 found=[p for p in candidates if p.is_file()]
 if not found:
  print('DPU_RETIRE_PACING_STRINGS_SKIPPED no compiled NativeLegacyDisplay object beside build-report.json')
  return
 for p in found:
  raw=p.read_bytes()
  if b'sheng-dpu-retire-pacing' in raw:raise ValueError('DpuRetirePacing compiled object still reads sheng-dpu-retire-pacing: '+p.name)
  if b'dpu-retire-pacing' not in raw:raise ValueError('DpuRetirePacing compiled object lacks dpu-retire-pacing: '+p.name)
  if b'dpu-early-done' not in raw:raise ValueError('DpuRetirePacing compiled object lacks the stacked dpu-early-done: '+p.name)
 print('DPU_RETIRE_PACING_STRINGS_OK',[p.name for p in found])
def verify(base):
 base=pathlib.Path(base).resolve()
 report=json.loads((base/'tree/build/native-legacy-display/build-report.json').read_text())
 recorded=report['source_sha256']
 for rel,digest in WANT.items():
  if recorded.get(rel)!=digest:raise ValueError('DpuRetirePacing compiled source differs: '+rel)
 check_object_strings(base)
 return recorded
if __name__=="__main__":
 base=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "UniXNU/out/sheng/ipados-27.0.1-24A446/sheng_ipados27")
 recorded=verify(base);print("DPU_RETIRE_PACING_PACKAGED_SOURCE",recorded['drivers/GopFramebuffer/NativeLegacyDisplay.cpp'])
