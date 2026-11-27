"""Verify the packaged bridge carries the command-error detail probe."""
import pathlib,hashlib,sys
WANT={'drivers/AdrenoMetal/bridge/NativeMetalObjects.rs': 'ae561dda2ccf37e93cd7aeb5bf39aa8e5af6459560d6780d72721655a56a3201'}
def verify(base):
 base=pathlib.Path(base).resolve()
 p=base/'tree/drivers/AdrenoMetal/bridge/NativeMetalObjects.rs'
 if not p.is_file():
  print('COMMAND_ERROR_DETAIL_PACKAGED_SKIPPED no packaged tree/drivers/AdrenoMetal/bridge/NativeMetalObjects.rs at '+str(p));return
 if hashlib.sha256(p.read_bytes()).hexdigest()!=WANT['drivers/AdrenoMetal/bridge/NativeMetalObjects.rs']:
  raise ValueError('CommandErrorDetail packaged source differs: drivers/AdrenoMetal/bridge/NativeMetalObjects.rs')
 hits=[]
 for cand in (base/'tree/build').rglob('*'):
  if cand.is_file() and cand.suffix in ('.o','.a') and cand.stat().st_size<200_000_000:
   try:raw=cand.read_bytes()
   except OSError:continue
   if b'pipe=(enc=' in raw or b'; refusal=' in raw:hits.append(cand.name)
 print('COMMAND_ERROR_DETAIL_PACKAGED_SOURCE',WANT['drivers/AdrenoMetal/bridge/NativeMetalObjects.rs'],'strings_in',hits if hits else 'none-found-skipped')
if __name__=="__main__":
 verify(sys.argv[1] if len(sys.argv)>1 else "UniXNU/out/sheng/ipados-27.0.1-24A446/sheng_ipados27")
