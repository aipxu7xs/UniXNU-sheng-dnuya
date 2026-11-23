"""Verify the packaged native legacy display was compiled from the reviewed early-done source."""
import pathlib,json,sys
WANT={'drivers/GopFramebuffer/NativeLegacyDisplay.cpp': '81b84bc0cdeb076bac64546e71b28fc14e767e48a7d3535a9dd977ee194a81fc', 'drivers/GopFramebuffer/NativeLegacyRequest.h': '81e89e1f40f2f1d0919567f53bc0564c650488843082693d00b9ea256cafae21', 'drivers/GopFramebuffer/NativeGOPPresenter.cpp': '6260912583decf8c4374085c5021cffa2f59898fd5c2873d75871196839dab66'}
def verify(base):
 base=pathlib.Path(base).resolve()
 report=json.loads((base/'tree/build/native-legacy-display/build-report.json').read_text())
 recorded=report['source_sha256']
 for rel,digest in WANT.items():
  if recorded.get(rel)!=digest:raise ValueError('GopEarlyDone compiled source differs: '+rel)
 return recorded
if __name__=="__main__":
 base=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "UniXNU/out/sheng/ipados-27.0.1-24A446/sheng_ipados27")
 recorded=verify(base);print("GOP_EARLY_DONE_PACKAGED_SOURCE",recorded['drivers/GopFramebuffer/NativeLegacyDisplay.cpp'])
