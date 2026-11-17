"""Exact repaired translator contract and bridge build provenance."""
import hashlib,json,os,pathlib,subprocess
HERE=pathlib.Path(__file__).resolve().parent
SPEC=json.loads((HERE/'translator-bridge-spec.json').read_text())
def digest(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def canonical(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def verify_support():
    for name,sha in SPEC['support'].items():
        p=HERE/'translator-native-support'/name
        if not p.is_file() or p.is_symlink() or digest(p)!=sha: raise RuntimeError('Sealed support input mismatch: '+name)
def verify_component(root):
    component=root/'drivers/AdrenoMetal'
    if output(['git','-C',component,'rev-parse','HEAD'])!=SPEC['component']:raise RuntimeError('AdrenoMetal revision mismatch')
    if output(['git','-C',component,'status','--porcelain','--untracked-files=all']):raise RuntimeError('AdrenoMetal source is dirty')
    return {p.relative_to(component).as_posix():digest(p) for n in output(['git','-C',component,'ls-files']).splitlines() if (p:=component/n).is_file()}
def verify_source(source):
    verify_support()
    expected=json.loads((HERE/'translator-native-support/tree-manifest.json').read_text())['repaired']
    actual={}
    for p in source.rglob('*'):
        rel=p.relative_to(source).as_posix()
        if rel.split('/')[0] in {'.git','target'}: continue
        if p.is_symlink(): raise RuntimeError('symlink in translator: '+rel)
        if p.is_file() and rel!='Cargo.lock': actual[rel]=digest(p)
    if actual!=expected: raise RuntimeError('Translator repaired byte tree mismatch: '+str([n for n in expected if actual.get(n)!=expected[n]][:10])+str(sorted(actual.keys()-expected.keys())[:10]))
    lock=source/'Cargo.lock'
    if not lock.is_file() or digest(lock)!=SPEC['cpu_lock']: raise RuntimeError('CPU workspace lock drift')
    import importlib.util
    spec=importlib.util.spec_from_file_location('native_guard',HERE/'translator-native-support/guard.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    guard,names=module.fingerprint(source)
    if guard!=SPEC['guard'] or len(names)!=587:raise RuntimeError('Runtime guard mismatch')
    return canonical(expected)
def output(command):
    return subprocess.check_output([str(x) for x in command],text=True).strip()
def build_provenance(root,source,manifest,cargo_path,llvm_as,target,checked):
    if output(['git','-C',root,'rev-parse','HEAD'])!=SPEC['framework']:raise RuntimeError('Framework revision mismatch')
    for key in ['RUSTC','RUSTC_WRAPPER','RUSTC_WORKSPACE_WRAPPER']:
        if os.environ.get(key):raise RuntimeError('Unqualified compiler override: '+key)
    # This is a different Cargo package from the CPU workspace. Generate and retain its own lock.
    toolchain='1.98.0'
    if not manifest.with_name('Cargo.lock').exists():
        subprocess.run([cargo_path,'+'+toolchain,'generate-lockfile','--manifest-path',manifest],check=True,cwd=root)
    lock=manifest.with_name('Cargo.lock')
    rustc=pathlib.Path(output(['rustup','which','--toolchain',toolchain,'rustc']))
    cargo=pathlib.Path(output(['rustup','which','--toolchain',toolchain,'cargo']))
    sysroot=pathlib.Path(output([rustc,'--print','sysroot']))
    rust_src=sysroot/'lib/rustlib/src/rust'
    if not rust_src.is_dir():raise RuntimeError('Rust 1.98.0 rust-src component required')
    std={p.relative_to(rust_src).as_posix():digest(p) for p in rust_src.rglob('*') if p.is_file()}
    libraries={p.relative_to(sysroot).as_posix():digest(p) for p in (sysroot/'lib').rglob('*') if p.is_file() and rust_src not in p.parents}
    sdk='iphoneos' if target in {'ios','ios27'} else 'macosx'
    sdk_path=pathlib.Path(output(['xcrun','--sdk',sdk,'--show-sdk-path']))
    sdk_inputs={p.relative_to(sdk_path).as_posix():digest(p) for p in sdk_path.rglob('*') if p.is_file()}
    native_tools={}
    for tool in ['clang','ar','ld']:
        path=pathlib.Path(output(['xcrun','--sdk',sdk,'--find',tool]));native_tools[tool]=dict(path=str(path),sha256=digest(path))
    env_keys=['RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','RUSTDOCFLAGS','RUSTC','RUSTC_WRAPPER','RUSTC_WORKSPACE_WRAPPER','RUSTUP_TOOLCHAIN','SDKROOT','CC','CXX','AR','CFLAGS','CXXFLAGS','LDFLAGS','MACOSX_DEPLOYMENT_TARGET','IPHONEOS_DEPLOYMENT_TARGET']
    configs={}
    for parent in [root,*root.parents]:
        for name in ['.cargo/config','.cargo/config.toml']:
            p=parent/name
            if p.is_file():configs[str(p)]=digest(p)
    cargo_home=pathlib.Path(os.environ.get('CARGO_HOME',pathlib.Path.home()/'.cargo'))
    for name in ['config','config.toml']:
        p=cargo_home/name
        if p.is_file():configs['cargo-home/'+name]=digest(p)
    return dict(schema=1,source=verify_source(source),guard=SPEC['guard'],component_inputs=verify_component(root),support=SPEC['support'],
        framework=output(['git','-C',root,'rev-parse','HEAD']),
        bridge_lock_sha256=digest(lock),bridge_manifest_sha256=digest(manifest),cpu_lock_sha256=SPEC['cpu_lock'],
        toolchain=dict(selected=toolchain,rustc=output([rustc,'-vV']),cargo=output([cargo,'-Vv']),rustc_sha256=digest(rustc),cargo_sha256=digest(cargo),rust_src_sha256=canonical(std),libraries_sha256=canonical(libraries)),
        sdk=dict(name=sdk,path=str(sdk_path),inputs_sha256=canonical(sdk_inputs),tools=native_tools,version=output(['xcrun','--sdk',sdk,'--show-sdk-version']),xcode=output(['xcodebuild','-version']),clang=output(['xcrun','--sdk',sdk,'clang','--version'])),
        llvm_as=dict(path=str(pathlib.Path(llvm_as).resolve()),version=output([llvm_as,'--version']),sha256=digest(pathlib.Path(llvm_as))),
        environment={k:v for k,v in os.environ.items() if k in env_keys or k.startswith(('CARGO_TARGET_','CARGO_PROFILE_','CARGO_BUILD_'))},configs=configs,
        builder_sha256=digest(root/'scripts/build-adreno-metal-bridge.py'),guard_helper_sha256=digest(HERE/'bridge_guard.py'),spec_sha256=digest(HERE/'translator-bridge-spec.json'),
        effective_overrides=dict(RUSTC_BOOTSTRAP='1' if target in {'ios27','macos27'} else os.environ.get('RUSTC_BOOTSTRAP',''),IPHONEOS_DEPLOYMENT_TARGET='27.0' if target=='ios27' else '17.0',MACOSX_DEPLOYMENT_TARGET='27.0' if target=='macos27' else '14.0'),checked=checked)
def bind_identity(identity,provenance,air_paths):
    identity['qualification']=provenance
    identity['assembled_fixtures']={name:digest(p) for name,p in air_paths.items()}
    # A lock/toolchain change also invalidates the runtime shader cache namespace.
    identity['runtime']=canonical(identity)[:32]
    return identity
