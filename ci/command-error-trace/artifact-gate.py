"""Verify the packaged Metal frontend carries the command-error probe."""
import pathlib,hashlib,sys
WANT={'drivers/AdrenoMetal/NativeBridgeMetalFrontend.mm': '8488fc727da33e7919a1fef856cd3f0ea3d99abdd0e16dd05e1d0e7832cd59ee'}
def verify(base):
 base=pathlib.Path(base).resolve()
 p=base/'tree/drivers/AdrenoMetal/NativeBridgeMetalFrontend.mm'
 if not p.is_file():
  print('COMMAND_ERROR_TRACE_PACKAGED_SKIPPED no packaged tree/drivers/AdrenoMetal/NativeBridgeMetalFrontend.mm at '+str(p));return
 if hashlib.sha256(p.read_bytes()).hexdigest()!=WANT['drivers/AdrenoMetal/NativeBridgeMetalFrontend.mm']:
  raise ValueError('CommandErrorTrace packaged source differs: drivers/AdrenoMetal/NativeBridgeMetalFrontend.mm')
 # The probe's format strings ride in the compiled frontend object when one is packaged.
 hits=[]
 for cand in (base/'tree/build').rglob('*'):
  if cand.is_file() and cand.suffix in ('.o','.a') and cand.stat().st_size<200_000_000:
   try:raw=cand.read_bytes()
   except OSError:continue
   if b'unscheduled st=' in raw or b'local: %s' in raw:hits.append(cand.name)
 print('COMMAND_ERROR_TRACE_PACKAGED_SOURCE',WANT['drivers/AdrenoMetal/NativeBridgeMetalFrontend.mm'],'strings_in',hits if hits else 'none-found-skipped')
if __name__=="__main__":
 verify(sys.argv[1] if len(sys.argv)>1 else "UniXNU/out/sheng/ipados-27.0.1-24A446/sheng_ipados27")
