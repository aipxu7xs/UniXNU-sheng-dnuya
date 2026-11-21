import pathlib,json,hashlib,argparse
O=pathlib.Path(__file__).resolve().parent
PIN='b10c33ad8f9d8ec29be1959025ab7a3819d4b7b913df405725b987e67889c86d'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def install(root,check=False):
 root=pathlib.Path(root).resolve();sp=O/"install-spec.json"
 if sha(sp)!=PIN:raise ValueError("Mesa160 install manifest differs")
 spec=json.loads(sp.read_text(encoding="utf-8"));pending=[]
 for name in list(spec["required"])+[f["path"] for f in spec["files"]]:
  p=pathlib.PurePosixPath(name)
  if p.is_absolute() or ".." in p.parts:raise ValueError("Unsafe repair payload path")
  target=root/name
  if any(q.is_symlink() for q in [target,*target.parents] if q==root or root in q.parents):raise ValueError("Symlink in repair target: "+name)
 for name,digest in spec["required"].items():
  if sha(root/name)!=digest:raise ValueError("Mesa160 prerequisite differs: "+name)
 for f in spec["files"]:
  p=root/f["path"];got=sha(p);raw=f["after"].encode()
  if p.is_symlink() or got not in (f["before_sha256"],f["after_sha256"]):raise ValueError("Mesa160 integration drift: "+f["path"])
  if hashlib.sha256(raw).hexdigest()!=f["after_sha256"]:raise ValueError("Mesa160 corrupt payload")
  if got!=f["after_sha256"]:pending.append((p,got,raw))
 for p,got,raw in pending:
  if sha(p)!=got:raise ValueError("Mesa160 target changed during preflight")
 if not check:
  for p,got,raw in pending:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 return {"check_only":check,"files":{**spec["required"],**{f["path"]:f["after_sha256"] for f in spec["files"]}},"pending":len(pending)}
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("framework");p.add_argument("--check",action="store_true");a=p.parse_args();print(json.dumps(install(a.framework,a.check),indent=2))
