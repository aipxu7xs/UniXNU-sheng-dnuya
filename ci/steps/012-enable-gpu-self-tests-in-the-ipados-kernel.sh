python3 - <<'PY'
import pathlib
p = pathlib.Path('package/BootWatchdogPolicy.c')
t = p.read_text(encoding='utf-8')
anchor = '#if XNU_TARGET_OS_OSX'
assert t.count(anchor) == 1, 'builtin boot-args OS guard drifted'
assert 'gpu-selftest=1' not in t, 'selftest argument unexpectedly already present'
patch = chr(10).join(['#if XNU_TARGET_OS_IOS', chr(34) + ' gpu-selftest=1 log-gpu=1 log-display=1 log-power=1' + chr(34), '#endif', anchor])
t = t.replace(anchor, patch, 1)
assert patch in t and 'gpu-pool=0' in t
p.write_text(t, encoding='utf-8')
print('iPadOS builtin boot arguments: gpu-selftest=1')
PY
