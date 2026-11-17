#!/usr/bin/env python3
"""Verify the retained compilation result and arm64e archive on the native host."""
import argparse, importlib.util, json, pathlib, subprocess

def main():
    p=argparse.ArgumentParser();p.add_argument('--framework',type=pathlib.Path,required=True);p.add_argument('--target',choices=['ios27','macos27'],default='ios27');a=p.parse_args();root=a.framework.resolve()
    spec=importlib.util.spec_from_file_location('installed_guard',root/'scripts/bridge_guard.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
    out=root/'build/adreno-metal-bridge';archive=out/a.target/'libadreno_metal_bridge.a'
    record=json.loads(archive.with_suffix('.a.json').read_text());result=json.loads((out/('result-'+a.target+'.json')).read_text());identity=json.loads((out/('provenance-'+a.target+'.json')).read_text())
    assert result['status']=='COMPILE_PASS' and result['native_arm64e']=='PASS','Native compilation not qualified'
    assert result['identity']==record['identity']==identity,'Identity metadata mismatch'
    sha=g.digest(archive);assert result['archive_sha256']==record['sha256']==sha,'Archive digest mismatch'
    arch=subprocess.check_output(['xcrun','lipo','-archs',str(archive)],text=True).strip();assert arch==result['architecture']=='arm64e','Archive is not arm64e'
    provenance=identity['qualification'];source=root/'.cache/gpu-reference/metal2vulkan'
    fresh=g.build_provenance(root,source,out/'Cargo.toml','cargo',provenance['llvm_as']['path'],a.target,provenance['checked'])
    assert fresh==provenance,'Provenance changed after compilation'
    fixtures={n:out/f for n,f in [('runtime_examples','runtime_examples.air'),('function_constant','function_constant.air'),('scanout','scanout_convert.air')]}
    assert {n:g.digest(f) for n,f in fixtures.items()}==identity['assembled_fixtures'],'Fixture bytes changed'
    base=dict(identity);base['runtime']=__import__('hashlib').sha256((identity['translator']+'\n'+identity['source_tree']+('\nchecked-draws' if provenance['checked'] else '')).encode()).hexdigest()[:32]
    assert g.canonical(base)[:32]==identity['runtime'],'Runtime identity mismatch'
    print(json.dumps(dict(status='ARCHIVE_PROVENANCE_PASS',sha256=sha,architecture=arch,cpu_toolchain=g.SPEC['cpu_toolchain'],bridge_toolchain=g.SPEC['bridge_toolchain'],gpu='NOT_RUN',device='NOT_RUN'),indent=2))
if __name__=='__main__':main()
