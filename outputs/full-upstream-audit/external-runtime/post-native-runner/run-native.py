#!/usr/bin/env python3
"""Intel CPU qualification only. Every selected test must execute; no GPU claim."""
import hashlib,json,os,pathlib,platform,re,shutil,subprocess,sys,time,traceback
from prepare import check_inputs,verify,LOCK
from guard import fingerprint
O=pathlib.Path(__file__).resolve().parent;S=O/'source';E=O/'evidence';E.mkdir(exist_ok=True)
results=[];state={'status':'RUNNING','gpu':'NOT_RUN','adreno':'NOT_RUN','ios_bridge':'NOT_RUN','commands':results}
def save(): (E/'native-results.json').write_text(json.dumps(state,indent=2))
def run(name,cmd,env,cwd=S):
    start=time.monotonic();log=E/(name+'.log')
    with log.open('wb') as f:r=subprocess.run(cmd,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT)
    text=log.read_text(errors='replace');results.append({'name':name,'command':cmd,'exit':r.returncode,'seconds':time.monotonic()-start,'log':log.name});save()
    print(name,r.returncode,flush=True)
    return r.returncode,text
CHECKS=[('299','metal2vulkan-runtime','test(a_depth_or_stencil_format_held_combined_is_an_attachment_of_its_combined_image)',{},[]),('410','metal2vulkan-air','test(canon::tests::static_vectors)',{},['canon::tests::static_vectors']),('412','metal2vulkan-air','test(canon::tests::generic_pointers)',{},['canon::tests::generic_pointers']),('614-pure','metal2vulkan-runtime','test(releasing_footprints_drops_probes_outside_the_lock)',{},[])]
for v in ['0','1']:CHECKS.append(('397-'+v,'metal2vulkan-runtime','test(device::compiles::tests) or test(pipeline::pool::tests)',{'METAL2VULKAN_COMPILE_ON_ASKING_THREAD':v},['device::compiles::tests','pipeline::pool::tests']))
def main():
    check_inputs();assert platform.system()=='Darwin' and platform.machine()=='x86_64','requires native macos-26-intel, no emulation'
    assert platform.mac_ver()[0].split('.')[0]=='26','runner OS major drift'
    verify(S,'combined');guard,names=fingerprint(S);assert guard==(S/'crates/metal2vulkan-validation/runtime-sources.sha256').read_text().strip()
    assert os.access(S/'scripts/rustc-wrapper',os.X_OK)
    env=os.environ.copy();env.update(RUSTUP_TOOLCHAIN=LOCK['rust'],RUSTFLAGS='-Dwarnings',RUSTDOCFLAGS='-Dwarnings',RUSTC_WRAPPER=str(S/'scripts/rustc-wrapper'),CARGO_TARGET_DIR=str(S/'target'),CARGO_TERM_COLOR='never',NEXTEST_COLOR='never',CI='true')
    env.pop('CARGO_ENCODED_RUSTFLAGS',None);env.pop('CARGO_BUILD_RUSTFLAGS',None)
    for k in ['RUSTUP_DIST_SERVER','RUSTUP_UPDATE_ROOT']:assert not env.get(k),'unexpected rustup mirror'
    for name,cmd in [('host',['sw_vers']),('xcode',['xcodebuild','-version']),('sdk',['xcrun','--sdk','macosx','--show-sdk-path']),('rustc',['rustc','-Vv']),('cargo',['cargo','-V']),('rustfmt',['rustfmt','--version']),('clippy-version',['cargo','clippy','--version']),('nextest-version',['cargo','nextest','--version']),('components',['rustup','component','list','--installed'])]:
        code,text=run(name,cmd,env);assert code==0,name
        if name=='rustc':assert 'host: x86_64-apple-darwin' in text
        if name=='nextest-version':assert re.search(r'cargo-nextest 0[.]9[.]100(?: |$)',text.strip()),text
        if name=='components':assert 'rustfmt-' in text and 'clippy-' in text
    # The six selected groups use typed synthetic IR, fake Vulkan dispatch, or pure ownership.
    # Inventory tools for later broader suites; absence never removes a selected test.
    inventory={}
    for tool in ['llvm-as','llvm-dis','spirv-as','spirv-val']:
        executable=shutil.which(tool);inventory[tool]={'path':executable,'required_by_selected_six':False,'status':'AVAILABLE' if executable else 'NOT_INSTALLED'}
        if executable:run('optional-'+tool,[executable,'--version'],env)
    (E/'fixture-tools.json').write_text(json.dumps(inventory,indent=2))
    code,_=run('resolve-lock',['cargo','generate-lockfile'],env);assert code==0,'dependency lock generation failed'
    shutil.copyfile(S/'Cargo.lock',E/'Cargo.lock');lockhash=hashlib.sha256((S/'Cargo.lock').read_bytes()).hexdigest();state['cargo_lock_sha256']=lockhash
    steps=[('fmt',['cargo','fmt','--all','--','--check']),('api',[sys.executable,'scripts/api-signatures/signatures.py','--check']),('refusals',[sys.executable,'scripts/refusal-surface/refusal_surface.py','--check']),('clippy',['cargo','clippy','--locked','-p','metal2vulkan-air','-p','metal2vulkan','-p','metal2vulkan-runtime','--all-targets','--all-features','--','-D','warnings']),('rustdoc',['cargo','doc','--locked','-p','metal2vulkan-air','-p','metal2vulkan','-p','metal2vulkan-runtime','--all-features','--no-deps'])]
    failures=[]
    for name,cmd in steps:
        code,_=run(name,cmd,env)
        if code:failures.append(name)
    for name,crate,expr,more,required in CHECKS:
        e=env.copy();e.update(more);args=['--locked','--release','-p',crate,'--all-features','-E',expr]
        start=time.monotonic()
        with (E/(name+'-list.json')).open('wb') as out,(E/(name+'-list.stderr')).open('wb') as err:
            r=subprocess.run(['cargo','nextest','list',*args,'--message-format','json'],cwd=S,env=e,stdout=out,stderr=err)
        row={'name':name+'-list','exit':r.returncode,'seconds':time.monotonic()-start,'environment':more};results.append(row);save()
        try:
            assert r.returncode==0,'list build failed'
            listing=json.loads((E/(name+'-list.json')).read_text());selected=[]
            for suite in listing['rust-suites'].values():
                for test,meta in suite['testcases'].items():
                    if meta['filter-match']['status']=='matches':
                        assert not meta['ignored'],'ignored selected test '+test
                        selected.append(test)
            assert selected,'empty selection'
            for prefix in required:assert any(prefix in n for n in selected),'missing test family '+prefix
            row['selected']=selected
            code,text=run(name,['cargo','nextest','run',*args,'--no-capture'],e)
            assert code==0,'test command failed'
            counts=re.findall(r'([0-9]+) passed',text)
            assert counts and int(counts[-1])==len(selected),'passed count differs from selected tests'
            assert not re.search(r'SKIPPED|KEPT-SPARSE: no sparse|[1-9][0-9]* (?:failed|ignored)',text),'skip/ignore/failure in selected tests'
            row['status']='PASS'
        except (AssertionError,KeyError,ValueError) as ex:
            row['status']='FAIL';row['reason']=str(ex);failures.append(name)
        save()
    verify(S,'combined');assert hashlib.sha256((S/'Cargo.lock').read_bytes()).hexdigest()==lockhash,'Cargo.lock changed during locked run'
    state['failures']=failures;state['status']='FOCUSED_CPU_PASS' if not failures else 'FAIL';save()
    return 1 if failures else 0
if __name__=='__main__':
    save()
    try:code=main()
    except Exception as ex:
        state['status']='FAIL';state['exception']=str(ex);save();traceback.print_exc();code=1
    finally:
        if (S/'Cargo.lock').is_file():shutil.copyfile(S/'Cargo.lock',E/'Cargo.lock')
    sys.exit(code)
