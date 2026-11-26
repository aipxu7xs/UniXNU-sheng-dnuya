python3 - <<'PY'
import pathlib
p = pathlib.Path('device/board.toml')
t = p.read_text()
if '"vsync=60"' in t:
    raise SystemExit('published refresh: vsync=60 already present in board.toml')
pieces = t.split('"kernel_args" = [')
if len(pieces) < 2:
    raise SystemExit('published refresh: no kernel_args array in board.toml')
out = [pieces[0]]
for i, chunk in enumerate(pieces[1:], 1):
    body, brk, tail = chunk.partition(']')
    if not brk:
        raise SystemExit('published refresh: unterminated kernel_args array')
    args = [a.strip() for a in body.split(',')]
    if i == 1:
        if '"gpu-dcvs=1"' not in args or '"usb=2"' not in args:
            raise SystemExit('published refresh: first kernel_args array is not the iPadOS payload array')
        if args.count('"vsync=120"') != 1:
            raise SystemExit('published refresh: vsync=120 not exactly once in payload kernel_args')
        args = ['"vsync=60"' if a == '"vsync=120"' else a for a in args]
        out.append('"kernel_args" = [' + ', '.join(args) + ']' + tail)
    else:
        out.append('"kernel_args" = [' + body + ']' + tail)
t2 = ''.join(out)
if t2.count('"vsync=60"') != 1:
    raise SystemExit('published refresh: vsync=60 not exactly once in board.toml')
if t2 != t:
    p.write_text(t2)
print('published refresh: payload kernel_args vsync=120 -> vsync=60 (E1 pacing experiment)')
PY
python3 - <<'PY'
import pathlib
t = pathlib.Path('device/board.toml').read_text()
pieces = t.split('"kernel_args" = [')
if len(pieces) < 2:
    raise SystemExit('published refresh verify: no kernel_args array in board.toml')
body = pieces[1].split(']')[0]
args = [a.strip() for a in body.split(',')]
if args.count('"vsync=60"') != 1 or '"vsync=120"' in args:
    raise SystemExit('published refresh verify: payload kernel_args not at vsync=60')
if '"vsync-fixed=1"' not in args:
    raise SystemExit('published refresh verify: vsync-fixed=1 lost from payload kernel_args')
for a in ['"diag=1"', '"gpu-trace=1"', '"diag-export=600"', '"gpu-perf=1"', '"dpu-early-done=1"']:
    if t.count(a) != 1:
        raise SystemExit('published refresh verify: measurement param drift: ' + a)
print('published refresh verified: payload vsync=60 exactly once, vsync-fixed=1 kept, diag + dpu-early-done params intact')
PY
