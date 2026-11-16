set -euo pipefail
python3 - <<'PY'
import pathlib
source = '"""Install one upstream checksum-pinned macOS ipsw binary without Homebrew tap evaluation."""\nfrom pathlib import Path\nimport argparse,hashlib,os,platform,tarfile,urllib.request,time,struct\nVERSION=\'3.1.749\'\nASSETS={\'x86_64\':(\'macOS_x86_64_extras\',\'ce1c0e3b3d1382186061f14cdbbc1a07277473b3910d19e2beb87246a291ef51\',0x01000007),\'arm64\':(\'macOS_arm64_extras\',\'ea061d5f671c4703b571456886ac5d986a0f865a8c97a1914e0cbf41a270bdcc\',0x0100000c)}\ndef install(archive,dest,arch):\n suffix,want,cpu=ASSETS[arch];archive=Path(archive);dest=Path(dest)\n if hashlib.sha256(archive.read_bytes()).hexdigest()!=want:raise ValueError(\'ipsw archive digest mismatch\')\n with tarfile.open(archive,\'r:gz\') as tar:\n  members=[m for m in tar.getmembers() if m.isfile() and Path(m.name).name==\'ipsw\']\n  if len(members)!=1:raise ValueError(\'Expected one regular ipsw executable\')\n  member=members[0]\n  if member.size>256*1024*1024:raise ValueError(\'Executable unexpectedly large\')\n  data=tar.extractfile(member).read()\n if len(data)<32 or struct.unpack_from(\'<I\',data)[0]!=0xfeedfacf or struct.unpack_from(\'<I\',data,4)[0]!=cpu:raise ValueError(\'Wrong Mach-O host architecture\')\n dest.mkdir(parents=True,exist_ok=True);p=dest/\'ipsw\';tmp=dest/\'ipsw.partial\';tmp.write_bytes(data);os.chmod(tmp,0o755);tmp.replace(p)\n print(\'Verified ipsw\',VERSION,arch,hashlib.sha256(data).hexdigest());return p\nif __name__==\'__main__\':\n p=argparse.ArgumentParser();p.add_argument(\'--archive\',type=Path);p.add_argument(\'--dest\',type=Path,required=True);p.add_argument(\'--arch\',choices=ASSETS,default=platform.machine());a=p.parse_args()\n if a.arch not in ASSETS:raise SystemExit(\'Unsupported host\')\n archive=a.archive\n if archive is None:\n  a.dest.mkdir(parents=True,exist_ok=True);archive=a.dest/(\'ipsw-\'+VERSION+\'.tar.gz\');suffix=ASSETS[a.arch][0];url=f\'https://github.com/blacktop/ipsw/releases/download/v{VERSION}/ipsw_{VERSION}_{suffix}.tar.gz\'\n  for attempt in range(4):\n   try:\n    with urllib.request.urlopen(url,timeout=90) as r,archive.open(\'wb\') as f:\n     while chunk:=r.read(1024*1024):f.write(chunk)\n    break\n   except Exception:\n    if attempt==3:raise\n    time.sleep(2*(attempt+1))\n install(archive,a.dest,a.arch)\n'
p=pathlib.Path('install-pinned-ipsw.py');p.write_text(source)
assert p.is_file()
PY
python3 install-pinned-ipsw.py --arch x86_64 --dest "$RUNNER_TEMP/sheng-tools/bin"
export PATH="$RUNNER_TEMP/sheng-tools/bin:$PATH"
echo "$RUNNER_TEMP/sheng-tools/bin" >> "$GITHUB_PATH"
ipsw version
brew install --formula dtc llvm lld cmake mtools ninja glslang shaderc spirv-tools bison pkgconf rustup openssl@3
LLVM_PREFIX="$(brew --prefix llvm)"
LLD_PREFIX="$(brew --prefix lld)"
BISON_PREFIX="$(brew --prefix bison)"
RUSTUP_PREFIX="$(brew --prefix rustup)"
OPENSSL_PREFIX="$(brew --prefix openssl@3)"
# GITHUB_PATH only affects later steps; export the same precedence for this shell.
export PATH="$HOME/.cargo/bin:$LLVM_PREFIX/bin:$LLD_PREFIX/bin:$BISON_PREFIX/bin:$RUSTUP_PREFIX/bin:$OPENSSL_PREFIX/bin:$PATH"
{
  # The runner prepends each entry, so write these in reverse precedence.
  echo "$OPENSSL_PREFIX/bin"
  echo "$RUSTUP_PREFIX/bin"
  echo "$BISON_PREFIX/bin"
  echo "$LLD_PREFIX/bin"
  echo "$LLVM_PREFIX/bin"
  echo "$HOME/.cargo/bin"
} >> "$GITHUB_PATH"
rustup toolchain install 1.98.0 --profile minimal --component rust-src
rustup run 1.98.0 rustc --version
rustup run 1.98.0 cargo --version
# Preserve the original fail-fast tool gate and check executable permissions.
ok=1
for t in clang xcodebuild make git ninja cmake dtc fdtget fdtput aea compression_tool mformat mcopy ipsw glslangValidator glslc spirv-val bison codesign hdiutil; do
  command -v "$t" >/dev/null || { echo "missing tool: $t"; ok=0; }
done
for t in lld-link llvm-lib llvm-rc llvm-nm llvm-objcopy; do
  [ -x "$LLVM_PREFIX/bin/$t" ] || [ -x "$LLD_PREFIX/bin/$t" ] || { echo "missing tool: $t"; ok=0; }
done
[ -f "$OPENSSL_PREFIX/include/openssl/evp.h" ] || { echo "missing OpenSSL 3 headers"; ok=0; }
[ "$ok" = 1 ]
# Execute native tools now: an incompatible host binary must fail before release.
"$LLVM_PREFIX/bin/clang" --version
"$LLD_PREFIX/bin/lld-link" --version
"$BISON_PREFIX/bin/bison" --version
"$OPENSSL_PREFIX/bin/openssl" version
