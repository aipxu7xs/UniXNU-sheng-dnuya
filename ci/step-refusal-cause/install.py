"""Install the deferred step refusal cause (don't let PipelineCreation mask it) probe (P0 probe Step 1). Root: the framework checkout (the "UniXNU" checkout in CI); it appends the probe hunk to drivers/AdrenoMetal/bridge/patches/0053-main-optimizations-on-development-8b9b2875.patch in the CI worktree (a patch-install step like gop/mesa160 -- NOT an AdrenoMetal commit, the frozen submodule pointer does not move)."""
import pathlib,json,hashlib,argparse
O=pathlib.Path(__file__).resolve().parent
PIN='5bee94dc3d19b34c9c1bb233f940f193fea0c9ffd84d594af26e5b2eaab6c8c3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def install(root,check=False):
 root=pathlib.Path(root).resolve();sp=O/"install-spec.json"
 if sha(sp)!=PIN:raise ValueError("StepRefusalCause install manifest differs")
 spec=json.loads(sp.read_text(encoding="utf-8"));pending=[]
 for name,digest in spec["required"].items():
  if sha(root/name)!=digest:raise ValueError("StepRefusalCause prerequisite differs: "+name)
 for f in spec["files"]:
  p=root/f["path"];got=sha(p);raw=f["after"].encode()
  if p.is_symlink() or got not in (f["before_sha256"],f["after_sha256"]):raise ValueError("StepRefusalCause integration drift: "+f["path"])
  if hashlib.sha256(raw).hexdigest()!=f["after_sha256"]:raise ValueError("StepRefusalCause corrupt payload")
  if got!=f["after_sha256"]:pending.append((p,got,raw))
 for p,got,raw in pending:
  if sha(p)!=got:raise ValueError("StepRefusalCause target changed during preflight")
 if not check:
  for p,got,raw in pending:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 return {"check_only":check,"files":{**spec["required"],**{f["path"]:f["after_sha256"] for f in spec["files"]}},"pending":len(pending)}
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("root");p.add_argument("--check",action="store_true");a=p.parse_args();print(json.dumps(install(a.root,a.check),indent=2))
