python3 - <<'PY'
import pathlib
p = pathlib.Path('UniXNU/scripts/build-fileset-release-reference.py')
t = p.read_text()
old = 'native_[a-z0-9_]+|boot_log_rounds|boot_cache_input_capture'
new = ('native_[a-z0-9_]+|cs_native4k_[a-z0-9_]+|iokit_[a-z0-9_]+|ml_[a-z0-9_]+|'
       'sheng_[a-z0-9_]+|boot_log_rounds|boot_cache_input_capture')
if 'cs_native4k_[a-z0-9_]+' in t:
    print('fileset reference stubs: already patched')
elif old not in t:
    raise SystemExit('fileset reference: stub regex anchor not found')
else:
    p.write_text(t.replace(old, new, 1))
    print('fileset reference stubs: prefixes extended (cs_native4k/iokit/ml/sheng)')
PY
