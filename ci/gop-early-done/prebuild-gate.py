import pathlib,hashlib,json,sys
EXPECTED={'drivers/GopFramebuffer/NativeLegacyDisplay.cpp': '81b84bc0cdeb076bac64546e71b28fc14e767e48a7d3535a9dd977ee194a81fc', 'drivers/GopFramebuffer/NativeLegacyRequest.h': '81e89e1f40f2f1d0919567f53bc0564c650488843082693d00b9ea256cafae21', 'drivers/GopFramebuffer/NativeGOPPresenter.cpp': '6260912583decf8c4374085c5021cffa2f59898fd5c2873d75871196839dab66'}
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'UniXNU')
for rel,digest in EXPECTED.items():
 assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==digest,rel+' GopEarlyDone installed source drift'
board=pathlib.Path('device/board.toml').read_text()
assert board.count('"dpu-early-done=1"')==1,'dpu-early-done=1 must appear exactly once in device/board.toml'
print('GOP_EARLY_DONE_PREBUILD_SOURCE',json.dumps(EXPECTED,sort_keys=True))
