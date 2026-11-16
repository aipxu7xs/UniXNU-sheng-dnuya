python3 - <<'PY'
import pathlib
p = pathlib.Path('device/board.toml')
t = p.read_text()
pieces = t.split('"kernel_args" = [')
if len(pieces) < 2:
    raise SystemExit('usb diagnostics: no kernel_args array in board.toml')
out = [pieces[0]]
touched = 0
for chunk in pieces[1:]:
    body, brk, tail = chunk.partition(']')
    if not brk:
        raise SystemExit('usb diagnostics: unterminated kernel_args array')
    args = [a.strip() for a in body.split(',')]
    if '"usb=1"' in args or '"usb=2"' in args:
        args = ['"usb=2"' if a == '"usb=1"' else a for a in args]
        if '"log-sys=1"' not in args:
            args.append('"log-sys=1"')
        touched += 1
        out.append('"kernel_args" = [' + ', '.join(args) + ']' + tail)
    else:
        out.append('"kernel_args" = [' + body + ']' + tail)
if not touched:
    raise SystemExit('usb diagnostics: no kernel_args array carries usb=1')
t2 = ''.join(out)
if t2 != t:
    p.write_text(t2)
print('usb diagnostics: %d kernel_args arrays -> usb=2 + log-sys=1' % touched)
PY
python3 - <<'PY'
import pathlib
t = pathlib.Path('device/board.toml').read_text()
if '"usb=1"' in t:
    raise SystemExit('usb diagnostics: usb=1 still present')
hits = 0
for chunk in t.split('"kernel_args" = [')[1:]:
    body = chunk.split(']')[0]
    args = [a.strip() for a in body.split(',')]
    if '"usb=2"' in args:
        hits += 1
        if '"log-sys=1"' not in args:
            raise SystemExit('usb diagnostics: log-sys=1 missing')
if hits != 2:
    raise SystemExit('usb diagnostics: expected 2 arrays with usb=2, got %d' % hits)
print('usb diagnostics verified: %d arrays carry usb=2 + log-sys=1' % hits)
PY
