"""Verify actual Mesa160 runtime source and generated compiler/plugin identity."""
import pathlib,json,hashlib,subprocess,sys
EXPECTED={'scripts/build-boot-runtime.py': 'fb732b7aadd6c8f64e8edbf14e5647682901f1f89a0908e1cc41574f43610cdb', 'scripts/data/mesa-reviewed-fixes.json': '39ba36c76edc8590b2537239dd8911ec27f60cec1a119dd715b990963f14d54f', 'patches/mesa/reviewed-board-fixes.patch': 'b02a6d5407dc6c66fa1c779002fa03e1e1a6b1058e6b34d21ee716dd2febfa55', 'scripts/data/mesa160-fixes.json': '7bfa66ddad0b724dfeac127d7619e57ef572b91f3531f800cf485a359ec19b68', 'patches/mesa/reviewed-mesa160.patch': '923317663d2da2d2069da7cd247b97d68c4a11e5e9678b723765b928a2886fcc', 'scripts/data/mesa160-header-order.json': 'baac241537642b6b39ee67750d67790f03e23497cf162a3d890fd1928d3a10b7', 'patches/mesa/reviewed-mesa160-header-order.patch': 'ac2da522fe17c1bc2576f44ef130b6b0daad51f24400b9bdedb89e9d28caa15b', 'scripts/data/mesa160-source-mods.json': '70ab2b9b2a752d1d4ec9feb4f4592ea00b69b7cea4ddcae335ce3deb45704074', 'patches/mesa/reviewed-mesa160-source-mods.patch': 'a56f1619687b468e1674cf9a985295a3b73702af6b944725de0160b2117ebc04', 'scripts/data/mesa160-lrz-compat.json': '9eb287e70feb646f9b784624d14841d4ce05b04f619b70bf1a05d6f5c6db787c', 'patches/mesa/reviewed-mesa160-lrz-compat.patch': 'df4088bb4ba22aff7fdc76433af4962370ebfb85c0b6021670c19c2c31a7fd15', 'scripts/data/adreno-compiler-inputs.json': '49fb00711b62c0bce299c52fba60e6478cdd575bcb9b3f0ef558b4c427d40b90', 'scripts/mesa_reviewed_fixes.py': '4857653a9d10b9c390f2dfee575615b09b1730e0e264e1ee13f83575babb1654', 'scripts/data/mesa160-lifecycle.json': 'dce0d2e9daf15351fdcd319e2e86834fc1cd2e48603dcfd7ef4d1b86a7d69803', 'patches/mesa/reviewed-mesa160-lifecycle.patch': '0072c1b793706f472c6a4011ae4d5d965ebf204bb86db25476db0b6cd6c71bfc'}
PRODUCERS={'scripts/mesa_patch_identity.py': '60f03967f4d2b56807b7b3d984181792cb810abbbc6392161d4c82b03d4433a7', 'scripts/build-turnip-darwin.py': '97ae7fcf7ff3475bb5bee481c1bc3cd3d564927821a21a6472c459a46cf5e294', 'scripts/build-adreno-metal-plugin.py': '332401a82955428ee88e0563e0c9a3c686641096e498fccb0eaddaedeb2682ac'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(tree):
 tree=pathlib.Path(tree).resolve()
 for rel,digest in {**EXPECTED,**PRODUCERS}.items():
  if sha(tree/rel)!=digest:raise ValueError("Mesa160 resolved installation/producer drift: "+rel)
 m=json.loads((tree/"scripts/data/mesa-reviewed-fixes.json").read_text());c=json.loads((tree/"scripts/data/mesa160-fixes.json").read_text());d=json.loads((tree/"scripts/data/mesa160-header-order.json").read_text());e=json.loads((tree/"scripts/data/mesa160-source-mods.json").read_text());f=json.loads((tree/"scripts/data/mesa160-lrz-compat.json").read_text());g=json.loads((tree/"scripts/data/mesa160-lifecycle.json").read_text());pins=json.loads((tree/"scripts/data/adreno-compiler-inputs.json").read_text())
 expected=[x["upstream"] for x in m["ordered_existing_overlays"]]+[m["new_patch"],c["new_patch"],d["new_patch"],e["new_patch"],f["new_patch"],g["new_patch"]]
 if pins["patches"]!=expected or len(expected)!=30:raise ValueError("Mesa160 ordered stack differs")
 for item in m["ordered_existing_overlays"]:
  if sha(tree/item["upstream"])!=item["sha256"]:raise ValueError("Mesa160 overlay drift")
 source=tree/".cache/mesa-work"
 for rev,want in [("HEAD",m["mesa"]),("HEAD^{tree}",m["mesa_tree"])]:
  if subprocess.check_output(["git","-C",str(source),"rev-parse",rev],text=True).strip()!=want:raise ValueError("Mesa160 actual Git identity differs")
 sys.path.insert(0,str(tree/"scripts"))
 from mesa_patch_identity import validate_recorded_patches
 validate_recorded_patches(tree,source,pins)
 final={f["path"]:f["after_sha256"] for f in m["files"]};final.update({f["path"]:f["after_sha256"] for f in c["files"]});final.update({f["path"]:f["after_sha256"] for f in d["files"]});final.update({f["path"]:f["after_sha256"] for f in e["files"]});final.update({x["path"]:x["after_sha256"] for x in f["files"]});final.update({x["path"]:x["after_sha256"] for x in g["files"]})
 for path,digest in final.items():
  if sha(source/path)!=digest:raise ValueError("Mesa160 actual source differs: "+path)
 report=json.loads((tree/"build/mesa-reviewed-source.json").read_text())
 wanted={"mesa":m["mesa"],"mesa_tree":m["mesa_tree"],"patch_count":30,"semantic_backports":185,"reviewed_patch_sha256":m["patch_sha256"],"compound_patch_sha256":c["patch_sha256"],"lifecycle_patch_sha256":g["patch_sha256"],"lifecycle_source_sha256":{x["path"]:x["after_sha256"] for x in g["files"]},"lrz_compat_patch_sha256":f["patch_sha256"],"lrz_compat_source_sha256":{x["path"]:x["after_sha256"] for x in f["files"]},"source_mods_patch_sha256":e["patch_sha256"],"source_mods_source_sha256":{f["path"]:f["after_sha256"] for f in e["files"]},"header_order_patch_sha256":d["patch_sha256"],"header_order_source_sha256":{f["path"]:f["after_sha256"] for f in d["files"]},"source_sha256":final,"compound_source_sha256":{f["path"]:final[f["path"]] for f in c["files"]},"freedreno_commits":m["freedreno_commits"],"nir_commits":m["nir_commits"],"compound_commits":c["commits"]}
 for k,v in wanted.items():
  if report.get(k)!=v:raise ValueError("Mesa160 runtime report differs: "+k)
 record=json.loads((tree/"build/mesa-tu-ios27/builtin-build-profile.json").read_text());profile=record["profile"]
 diff=subprocess.check_output(["git","-C",str(source),"diff","HEAD","--binary"])
 names=subprocess.check_output(["git","-C",str(source),"ls-files","--others","--exclude-standard","-z"]).split(bytes([0]))
 extras={name.decode():sha(source/name.decode()) for name in names if name and (source/name.decode()).is_file()}
 identities={"mesa_revision":m["mesa"],"target":"ios27","source_diff_sha256":hashlib.sha256(diff).hexdigest(),"extra_sources":extras,"patch_guard_sha256":sha(tree/"scripts/mesa_patch_identity.py"),"build_script_sha256":sha(tree/"scripts/build-turnip-darwin.py")}
 for k,v in identities.items():
  if profile.get(k)!=v:raise ValueError("Mesa160 compiler profile differs: "+k)
 source_id=hashlib.sha256(json.dumps(profile,sort_keys=True,separators=(",",":")).encode()).hexdigest()
 if record["source_id"]!=source_id:raise ValueError("Mesa160 compiler source_id differs")
 plugin=json.loads((tree/"build/adreno-metal-plugin27/NativeAdrenoMetal.bundle/gpu-build.json").read_text())
 if plugin.get("turnip")!=record or plugin.get("target")!="ios27":raise ValueError("Mesa160 plugin carries stale profile/target")
 build_id=hashlib.sha256(json.dumps(dict(mesa_revision=m["mesa"],source_diff_sha256=profile["source_diff_sha256"],extra_sources=extras),sort_keys=True).encode()).hexdigest()[:40]
 ninja=(tree/"build/mesa-tu-ios27/build.ninja").read_text()
 if source_id not in ninja or build_id not in ninja:raise ValueError("Mesa160 actual build rules carry stale identities")
 report["compiled_profile"]=record;report["pipeline_build_id"]=build_id
 return report
if __name__=="__main__":
 base=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "UniXNU/out/sheng/ipados-27.0.1-24A446/sheng_ipados27")
 report=verify(base/"tree");(base/"mesa-reviewed-source.json").write_text(json.dumps(report,indent=2));print("MESA160_PACKAGED_SOURCE",report["mesa"],report["patch_count"],len(report["compound_commits"]))
