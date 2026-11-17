#!/usr/bin/env python3
"""Install the CPU-qualified repaired source into the fixed framework cache."""
import argparse, importlib.util, json, os, pathlib, shutil, subprocess, sys
from bridge_guard import SPEC, digest, canonical
HERE=pathlib.Path(__file__).resolve().parent

def check_support(support):
    for name,sha in SPEC['support'].items():
        p=support/name
        if p.is_symlink() or not p.is_file() or digest(p)!=sha:raise RuntimeError('Sealed support input mismatch: '+name)

def check_framework(root):
    if subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()!=SPEC['framework']:raise RuntimeError('Framework revision mismatch')
    for name,sha in SPEC['framework_inputs'].items():
        if digest(root/name)!=sha:raise RuntimeError('Framework builder input drift: '+name)
    component=root/'drivers/AdrenoMetal'
    if subprocess.check_output(['git','-C',str(component),'rev-parse','HEAD'],text=True).strip()!=SPEC['component']:raise RuntimeError('AdrenoMetal revision mismatch')
    if subprocess.check_output(['git','-C',str(component),'status','--porcelain','--untracked-files=all'],text=True).strip():raise RuntimeError('AdrenoMetal source is dirty')

def main():
    p=argparse.ArgumentParser();p.add_argument('--framework',type=pathlib.Path,required=True);p.add_argument('--native-support',type=pathlib.Path,required=True);p.add_argument('--archive',type=pathlib.Path,required=True);a=p.parse_args()
    root=a.framework.resolve();support=a.native_support.resolve()
    if os.environ.get('NMB_PREBUILT_BRIDGE'):raise RuntimeError('Native qualification rejects NMB_PREBUILT_BRIDGE')
    check_support(support);check_framework(root)
    dest=root/'.cache/gpu-reference/metal2vulkan';installed=root/'scripts/translator-native-support'
    if dest.exists() or installed.exists():raise RuntimeError('Refuse overwriting existing translator/support cache')
    spec=importlib.util.spec_from_file_location('frozen_prepare',support/'prepare.py');prepare=importlib.util.module_from_spec(spec);spec.loader.exec_module(prepare)
    if digest(a.archive)!=prepare.LOCK['archive_sha256']:raise RuntimeError('Translator archive digest mismatch')
    # All destinations are under the caller-selected framework. Frozen support remains read-only.
    installed.mkdir(parents=True)
    for name in SPEC['support']:shutil.copyfile(support/name,installed/name)
    for name in ['bridge_guard.py','translator-bridge-spec.json']:shutil.copyfile(HERE/name,root/'scripts'/name)
    prepare.O=installed
    modes=prepare.extract(a.archive,dest)
    subprocess.run(['git','init','--quiet',str(dest)],check=True)
    for patch,stage in [('overlay-0053.patch','baseline'),('combined.patch','combined')]:
        subprocess.run(['git','-c','core.longpaths=true','-c','core.autocrlf=false','apply','--check',str(installed/patch).removeprefix('\\\\?\\')],cwd=dest,check=True)
        subprocess.run(['git','-c','core.longpaths=true','-c','core.autocrlf=false','apply',str(installed/patch).removeprefix('\\\\?\\')],cwd=dest,check=True)
        if stage=='baseline':prepare.restore_layout(dest,json.loads((installed/'byte-layout.json').read_text()))
        prepare.verify(dest,stage)
    prepare.apply_qualification_repair(dest)
    shutil.copyfile(installed/'product-Cargo.lock',dest/'Cargo.lock')
    for name,mode in modes.items():
        if (dest/name).exists():(dest/name).chmod(mode)
    # Import the installed helper so its relative support contract is the one the builder uses.
    spec=importlib.util.spec_from_file_location('installed_guard',root/'scripts/bridge_guard.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
    source_id=guard.verify_source(dest);component=guard.verify_component(root)
    shutil.copyfile(HERE/'build-adreno-metal-bridge.py',root/'scripts/build-adreno-metal-bridge.py')
    plugin=root/'scripts/build-adreno-metal-plugin.py';text=plugin.read_text()
    old="manifest['bridge_component'] = bridge_identity['component']"
    assert text.count(old)==1
    plugin.write_text(text.replace(old,old+"\nmanifest['bridge_identity'] = bridge_identity"))
    evidence=root/'build/adreno-metal-bridge';evidence.mkdir(parents=True,exist_ok=True)
    record=dict(status='EXACT_SOURCE_INSTALLED',source=str(dest),source_files=7471,source_sha256=source_id,runtime_guard=SPEC['guard'],runtime_guard_inputs=587,cpu_run=SPEC['cpu_run'],cpu_toolchain=SPEC['cpu_toolchain'],bridge_toolchain=SPEC['bridge_toolchain'],component=SPEC['component'],component_inputs_sha256=canonical(component),support=SPEC['support'],native_arm64e='NOT_RUN',gpu='NOT_RUN',plugin='NOT_RUN')
    (evidence/'installation.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
if __name__=='__main__':main()
