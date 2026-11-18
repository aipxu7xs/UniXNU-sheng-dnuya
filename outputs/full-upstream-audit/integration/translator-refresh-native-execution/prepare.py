"""Reconstruct exact refreshed source; no inherited native qualification."""
import argparse, hashlib, json, os, pathlib, shutil, subprocess, tarfile, urllib.request
O=pathlib.Path(__file__).resolve().parent
GIT=os.environ.get('GIT_EXE','git')
LOCK=json.loads((O/'inputs.lock.json').read_text())
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def check_inputs():
    for n,h in LOCK['files'].items(): assert digest(O/n)==h, 'support drift: '+n
def verify(s,stage='repaired'):
    expected=json.loads((O/'tree-manifest.json').read_text())[stage]
    actual={p.relative_to(s).as_posix():digest(p) for p in s.rglob('*') if p.is_file() and p.relative_to(s).parts[0] not in {'.git','target'} and p.relative_to(s).as_posix()!='Cargo.lock'}
    assert actual==expected, 'full source mismatch'
    return len(actual)
def extract(archive,dest):
    assert not dest.exists(), 'destination exists'
    with tarfile.open(archive) as t:
        members=t.getmembers(); seen=set(); pending=[]
        for m in members:
            rel=pathlib.PurePosixPath(m.name)
            assert not rel.is_absolute() and '..' not in rel.parts and chr(92) not in m.name
            if len(rel.parts)<2: continue
            name='/'.join(rel.parts[1:]); assert m.isdir() or m.isfile(), 'nonregular archive entry'
            if m.isdir(): continue
            assert name not in seen; seen.add(name); pending.append((m,name))
        assert len(pending)<100000
        dest.mkdir(parents=True)
        for m,name in pending:
            p=dest/name;p.parent.mkdir(parents=True,exist_ok=True)
            with t.extractfile(m) as src,p.open('wb') as dst: shutil.copyfileobj(src,dst)
            p.chmod(m.mode & 0o777)
def download(url,p):
    assert not p.exists()
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'refreshed-native-qualification'}),timeout=180) as r,p.open('wb') as f: shutil.copyfileobj(r,f)
def main():
    a=argparse.ArgumentParser();a.add_argument('--archive',type=pathlib.Path);a.add_argument('--nextest',action='store_true');args=a.parse_args();check_inputs()
    E=O/'evidence';E.mkdir(exist_ok=True)
    if args.nextest:
        p=O/'nextest.crate';download('https://crates.io/api/v1/crates/cargo-nextest/0.9.100/download',p)
        assert digest(p)==LOCK['nextest_sha256'];extract(p,O/'nextest-source')
        assert (O/'nextest-source/Cargo.lock').is_file();return
    archive=args.archive or O/'upstream.tar.gz'
    if not args.archive: download(LOCK['archive_url'],archive)
    assert digest(archive)==LOCK['archive_sha256'], 'archive digest mismatch'
    s=O/'source';extract(archive,s)
    rows=json.loads((O/'upstream-manifest.json').read_text())['files'];verify(s,'upstream')
    for row in rows:
        p=s/row['path'];data=p.read_bytes()
        assert hashlib.sha1(b'blob '+str(len(data)).encode()+bytes([0])+data).hexdigest()==row['git_blob']
        p.chmod(int(row['mode'][-3:],8))
    subprocess.run([GIT,'init','--quiet',str(s)],check=True)
    assert pathlib.Path(subprocess.check_output([GIT,'-C',str(s),'rev-parse','--show-toplevel'],text=True).strip()).resolve()==s.resolve()
    for arg in ['--check',None]:
        cmd=[GIT,'-C',str(s),'-c','core.autocrlf=false','apply']
        if arg:cmd.append(arg)
        subprocess.run(cmd+[str(O/'overlay.patch')],check=True)
    verify(s,'overlay')
    repair=json.loads((O/'repair.json').read_text())
    for row in repair['files']:
        p=s/row['path'];assert digest(p)==row['before_sha256']
        payload=O/'repair-compiles.rs';assert digest(payload)==row['after_sha256'];p.write_bytes(payload.read_bytes())
    guard='crates/metal2vulkan-validation/runtime-sources.sha256'
    (s/guard).write_bytes((LOCK['guard']+chr(10)).encode())
    verify(s)
    from guard import fingerprint
    actual,names=fingerprint(s);assert actual==LOCK['guard'] and len(names)==615
    (E/'source-preparation.json').write_text(json.dumps({'status':'EXACT_SOURCE_PASS','files':7650,'guard':actual,'inputs':len(names),'archive_sha256':digest(archive),'native_executed':False},indent=2))
if __name__=='__main__':main()
