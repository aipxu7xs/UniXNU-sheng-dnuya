"""Self-test the installed decoder: synthetic type=20/21 records must decode
and the completeness check must pass a whole chain and fail a cut one."""
import importlib.util,pathlib,struct,sys
def load(script):
 spec=importlib.util.spec_from_file_location('decode_gpu_trace',script);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def rec(kind,seq,t0,t1,t2,t3,a,b,c,d,tid,cpu0,cpu1,tid2):
 return struct.pack('<II4Q8I',kind,seq,t0,t1,t2,t3,a,b,c,d,tid,cpu0,cpu1,tid2)
def chunk20(text,part,parts,status,commit,trace,now):
 raw=text.encode()
 off=part*36;piece=raw[off:off+36].ljust(36,b'\0')
 t3,b,c,d,tid,cpu0,cpu1,tid2=struct.unpack('<Q7I',piece)
 a=part|(parts<<8)|(status<<16)
 return rec(20,0,now,commit,trace,t3,a,b,c,d,tid,cpu0,cpu1,tid2)
def meta21(parts,truncated,commit,trace,now,encode_us=1234,passes=2,draws=9,kpx=512,blits=1):
 a=parts|(truncated<<8)|(1<<16)
 return rec(21,0,now,commit,trace,encode_us,a,passes,draws,kpx,7,blits,0,8)
def verify(script):
 m=load(pathlib.Path(script))
 now=1_700_000_000
 whole='Refused; test command buffer error text that spans two chunks.'
 blob=b''.join([chunk20(whole,0,2,5,11,22,now),chunk20(whole,1,2,5,11,22,now),meta21(2,0,11,22,now)])
 blob+=chunk20('short',0,2,5,12,23,now)+meta21(2,1,12,23,now)
 rows=m.frontend_details(blob)
 assert len([r for r in rows if r['name']=='command_error'])==3,'expected 3 command_error rows'
 assert len([r for r in rows if r['name']=='command_error_meta'])==2,'expected 2 command_error_meta rows'
 out=m.command_error_check(rows)
 assert len(out)==2,'expected 2 checked command buffers'
 good=[r for r in out if r['sequence']==11][0];cut=[r for r in out if r['sequence']==12][0]
 assert good['complete'] and good['text']==whole and good['parts_seen']==2 and good['parts_expected']==2 and not good['truncated'],'whole chain must verify'
 assert good['encode_us']==1234 and good['passes']==2 and good['draws']==9 and good['kpx']==512 and good['blits']==1,'metadata must round-trip'
 assert not cut['complete'] and cut['text'] is None and cut['truncated'],'cut chain must fail the check'
 print('DECODE_COMMAND_ERROR_ARTIFACT_OK',good['sequence'],'complete',cut['sequence'],'incomplete-as-expected')
if __name__=="__main__":
 verify(sys.argv[1] if len(sys.argv)>1 else "device/scripts/decode-gpu-trace.py")
