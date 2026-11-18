import pathlib,re,hashlib,json,sys
O=pathlib.Path(__file__).resolve().parent
def fingerprint(S):
 C=S/'crates';b=(C/'metal2vulkan-validation/build.rs').read_text(encoding='utf-8')
 names=re.findall(r'"([^"]+)"',b.split('let listed = [',1)[1].split('];',1)[0])
 for tree,rs in [('metal2vulkan/src/bind',True),('metal2vulkan-runtime/src',False)]:
  for p in (C/tree).rglob('*'):
   rel=p.relative_to(C);parts=p.relative_to(C/tree).parts
   if p.is_file() and not any(n.startswith('.') or n=='tests' for n in parts) and p.name!='tests.rs' and not p.name.endswith('_tests.rs') and (not rs or p.suffix=='.rs'):names.append(rel.as_posix())
 h=hashlib.sha256()
 for n in sorted(names):
  d=(C/n).read_bytes();h.update(n.encode());h.update(bytes([0]));h.update(len(d).to_bytes(8,'little'));h.update(d)
 return h.hexdigest(),sorted(names)
if __name__=='__main__':
 S=pathlib.Path(sys.argv[1]);digest,names=fingerprint(S);p=S/'crates/metal2vulkan-validation/runtime-sources.sha256'
 if '--write' in sys.argv:p.write_bytes((digest+chr(10)).encode())
 else:assert p.read_text().strip()==digest,(p.read_text().strip(),digest)
 (O/'runtime-guard.json').write_text(json.dumps({'platform_path_encoding':'POSIX/macOS','sha256':digest,'input_count':len(names),'inputs':names},indent=2))
 print('Runtime guard',digest,len(names))
