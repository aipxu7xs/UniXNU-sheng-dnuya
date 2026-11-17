#!/usr/bin/env python3
"""Reconstruct exact sealed bytes. Never update expected hashes."""
import argparse, hashlib, json, pathlib, shutil, subprocess, tarfile, urllib.request
O=pathlib.Path(__file__).resolve().parent
LOCK=json.loads((O/'inputs.lock.json').read_text())
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def fetch(url,p,h):
    if not p.exists():
        req=urllib.request.Request(url,headers={'User-Agent':'sealed-native-qualification'})
        with urllib.request.urlopen(req,timeout=180) as r,p.open('wb') as f:shutil.copyfileobj(r,f)
    assert digest(p)==h, 'download digest mismatch: '+str(p)
def check_inputs():
    for n,h in LOCK['files'].items():assert digest(O/n)==h,'input mismatch: '+n
def verify(s,stage):
    expected=json.loads((O/'tree-manifest.json').read_text())[stage]
    actual={p.relative_to(s).as_posix():digest(p) for p in s.rglob('*') if p.is_file() and p.relative_to(s).parts[0] not in {'.git','target'} and p.relative_to(s).as_posix()!='Cargo.lock'}
    assert actual==expected, json.dumps({'missing':sorted(expected.keys()-actual.keys()),'extra':sorted(actual.keys()-expected.keys()),'different':[n for n in actual.keys()&expected.keys() if actual[n]!=expected[n]]})
    return len(actual)
def extract(archive,dest):
    assert not dest.exists(),'refuse overwriting '+str(dest)
    dest.mkdir(parents=True);modes={}
    with tarfile.open(archive) as t:
        for m in t.getmembers():
            parts=pathlib.PurePosixPath(m.name).parts
            assert not m.name.startswith('/') and '..' not in parts
            if len(parts)<2:continue
            rel=pathlib.Path(*parts[1:]);p=dest/rel
            assert m.isfile() or m.isdir(),'unsupported archive entry: '+m.name
            if m.isdir():p.mkdir(parents=True,exist_ok=True);continue
            p.parent.mkdir(parents=True,exist_ok=True)
            with t.extractfile(m) as src,p.open('wb') as dst:shutil.copyfileobj(src,dst)
            p.chmod(m.mode & 0o777);modes[rel.as_posix()]=m.mode & 0o777
    return modes
def restore_layout(s,rows):
    for row in rows:
        p=s/row['path'];assert row['operation']=='LF_to_CRLF'
        assert digest(p)==row['input_sha256'],'byte-layout input drift'
        data=p.read_bytes();changed=data.replace(bytes([13,10]),bytes([10])).replace(bytes([10]),bytes([13,10]))
        assert hashlib.sha256(changed).hexdigest()==row['output_sha256'],'byte-layout output drift'
        p.write_bytes(changed)
def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',type=pathlib.Path);p.add_argument('--git',default='git');p.add_argument('--nextest',action='store_true');a=p.parse_args()
    check_inputs();E=O/'evidence';E.mkdir(exist_ok=True)
    if a.nextest:
        archive=O/'cargo-nextest-0.9.100.crate';fetch(LOCK['nextest_url'],archive,LOCK['nextest_sha256'])
        extract(archive,O/'nextest-source');assert (O/'nextest-source/Cargo.lock').is_file()
        shutil.copyfile(O/'nextest-source/Cargo.lock',E/'nextest-Cargo.lock');return
    archive=a.archive or O/'translator.tar.gz'
    if a.archive:assert digest(archive)==LOCK['archive_sha256']
    else:fetch(LOCK['archive_url'],archive,LOCK['archive_sha256'])
    s=O/'source';modes=extract(archive,s)
    # Anchor patch paths here, even when this bundle is inside a checkout.
    subprocess.run([a.git,'init','--quiet',str(s)],check=True)
    for patch,stage in [('overlay-0053.patch','baseline'),('combined.patch','combined')]:
        subprocess.run([a.git,'-c','core.autocrlf=false','apply','--check',str(O/patch)],cwd=s,check=True)
        subprocess.run([a.git,'-c','core.autocrlf=false','apply',str(O/patch)],cwd=s,check=True)
        if stage=='baseline':
            restore_layout(s,json.loads((O/'byte-layout.json').read_text()))
        count=verify(s,stage);print(stage,count,'files exact')
    for n,mode in modes.items():
        if (s/n).exists():(s/n).chmod(mode)
    from guard import fingerprint
    guard,names=fingerprint(s);assert guard==(s/'crates/metal2vulkan-validation/runtime-sources.sha256').read_text().strip()
    (E/'source-preparation.json').write_text(json.dumps({'status':'BYTE_RECONSTRUCTION_PASS','files':count,'guard':guard,'guard_inputs':len(names),'executable_files':[n for n,m in modes.items() if m&0o111],'native_executed':False},indent=2))
if __name__=='__main__':main()
