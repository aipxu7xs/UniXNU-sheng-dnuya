"""Host checks only; never execute Cargo or report native success."""
import ast,hashlib,importlib.util,json,pathlib,subprocess,sys,yaml
O=pathlib.Path(__file__).resolve().parent
checks=[]
for name in ['prepare.py','run-native.py','guard.py']:
    ast.parse((O/name).read_text());checks.append('AST '+name)
spec=importlib.util.spec_from_file_location('runner',O/'run-native.py');m=importlib.util.module_from_spec(spec);sys.path.insert(0,str(O));spec.loader.exec_module(m)
m.validate_nextest(0,'Summary [1s] 2 tests run: 2 passed, 10 skipped',['a','b'])
for code,text in [(1,'Summary [1s] 2 tests run: 2 passed'),(0,'Summary [1s] 2 tests run: 1 passed, 1 failed'),(0,'Summary [1s] 1 tests run: 1 passed'),(0,'no summary'),(0,'SKIP a\nSummary [1s] 2 tests run: 2 passed')]:
    try:m.validate_nextest(code,text,['a','b'])
    except AssertionError:pass
    else:raise AssertionError('false pass accepted')
checks.append('nextest summary positive + 5 negatives')
y=yaml.safe_load((O/'qualification.yml').read_text());job=y['jobs']['native-cpu'];assert job['runs-on']=='macos-26-intel'
for i,step in enumerate(job['steps']):
    if 'run' in step:
        p=O/('.check-'+str(i)+'.sh');p.write_text(step['run'])
        subprocess.run([sys.argv[1],'-n',str(p)],check=True);p.unlink()
checks.append('YAML + Bash AST')
s=(O/'run-native.py').read_text();assert "['cargo','generate-lockfile']" in s and "'reviewed fresh lock is required before qualification'" in s
assert "['cargo','fetch','--locked']" in s and "args=['--locked','--release'" in s
assert "state['status']='LOCK_RESOLUTION_ONLY'" in s
checks.append('resolution cannot qualify; reviewed lock required')
assert 'METAL2VULKAN_COMPILE_ON_ASKING_THREAD' not in s and 'releasing_footprints_drops_probes_outside_the_lock' not in s
for required in ['a_depth_or_stencil_format_held_combined_is_an_attachment_of_its_combined_image','canon::tests::static_vectors','canon::tests::generic_pointers','a_kept_footprint_is_read_while_its_command_buffer_s_state_is_locked','device::compiles::tests','pipeline::pool::tests']:assert required in s,required
checks.append('exact refreshed focused test names; no removed env mode')
src=pathlib.Path('translator-refresh-native-plan/source') if False else O/'source'
assert (src/'crates/metal2vulkan-runtime/src/device/compiles.rs').is_file()
from prepare import verify,LOCK
assert verify(src)==7650
from guard import fingerprint
actual,names=fingerprint(src);assert actual==LOCK['guard'] and len(names)==615
checks.append('reconstructed source 7650 files and 615 runtime inputs exact')
from prepare import check_inputs
check_inputs();checks.append('sealed support input hashes')
assert "assert digest(archive)==LOCK['archive_sha256'], 'archive digest mismatch'" in (O/'prepare.py').read_text();checks.append('archive digest pinned before extraction')
result={'status':'PASS_HOST','checks':checks,'native_executed':False,'source_reconstruction':'separate background job','lock':'NOT_RESOLVED','gpu':'NOT_RUN','device':'NOT_RUN'}
(O/'validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
