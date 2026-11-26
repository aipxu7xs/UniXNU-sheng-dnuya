import pathlib,hashlib,json,re,sys
EXPECTED={'drivers/GopFramebuffer/NativeLegacyDisplay.cpp': 'b92a7fa026c215c708a5d1a4a1f0e3a67d67dfc84f8a2cbbadba362f10d5d8fd', 'drivers/GopFramebuffer/NativeLegacyRequest.h': '81e89e1f40f2f1d0919567f53bc0564c650488843082693d00b9ea256cafae21', 'drivers/GopFramebuffer/NativeGOPPresenter.cpp': '6260912583decf8c4374085c5021cffa2f59898fd5c2873d75871196839dab66'}
INTRODUCED={'dpu-retire-pacing'}
STACKED={'dpu-early-done'}
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'UniXNU')
for rel,digest in EXPECTED.items():
 assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==digest,rel+' DpuRetirePacing installed source drift'
board=pathlib.Path('device/board.toml').read_text()
assert board.count('"dpu-retire-pacing=1"')==1,'dpu-retire-pacing=1 must appear exactly once in device/board.toml'
assert board.count('"dpu-early-done=1"')==1,'dpu-early-done=1 must appear exactly once in device/board.toml (DpuRetirePacing stacks on GopEarlyDone)'
src=(root/'drivers/GopFramebuffer/NativeLegacyDisplay.cpp').read_text()
read_names=set(re.findall(r'PE_parse_boot_argn\("([^"]+)"',src))
assert INTRODUCED<=read_names,'patch-introduced boot-arg missing from installed source: '+str(INTRODUCED-read_names)
assert STACKED<=read_names,'stacked patch boot-arg missing from installed source: '+str(STACKED-read_names)
for name in INTRODUCED|STACKED:
 assert '"'+name+'=' in board,'boot-arg not fed by device/board.toml kernel_args: '+name
print('DPU_RETIRE_PACING_PREBUILD_SOURCE',json.dumps(EXPECTED,sort_keys=True))
