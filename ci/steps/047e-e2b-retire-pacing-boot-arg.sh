python3 - <<'PY'
import pathlib
p = pathlib.Path('device/board.toml')
t = p.read_text()
if '"dpu-retire-pacing' in t:
    raise SystemExit('retire pacing: dpu-retire-pacing already present in board.toml')
pieces = t.split('"kernel_args" = [')
if len(pieces) < 2:
    raise SystemExit('retire pacing: no kernel_args array in board.toml')
out = [pieces[0]]
for i, chunk in enumerate(pieces[1:], 1):
    body, brk, tail = chunk.partition(']')
    if not brk:
        raise SystemExit('retire pacing: unterminated kernel_args array')
    args = [a.strip() for a in body.split(',')]
    if i == 1:
        if '"gpu-dcvs=1"' not in args or '"usb=2"' not in args:
            raise SystemExit('retire pacing: first kernel_args array is not the iPadOS payload array')
        if '"dpu-early-done=1"' not in args:
            raise SystemExit('retire pacing: dpu-early-done=1 missing from payload kernel_args (E2b stacks on B1)')
        args.append('"dpu-retire-pacing=1"')
        out.append('"kernel_args" = [' + ', '.join(args) + ']' + tail)
    else:
        out.append('"kernel_args" = [' + body + ']' + tail)
t2 = ''.join(out)
if t2.count('"dpu-retire-pacing=1"') != 1:
    raise SystemExit('retire pacing: dpu-retire-pacing=1 not exactly once in board.toml')
if t2 != t:
    p.write_text(t2)
print('retire pacing: payload kernel_args += dpu-retire-pacing=1 (E2b pacing experiment)')
PY
python3 - <<'PY'
import pathlib
t = pathlib.Path('device/board.toml').read_text()
pieces = t.split('"kernel_args" = [')
if len(pieces) < 2:
    raise SystemExit('retire pacing verify: no kernel_args array in board.toml')
body = pieces[1].split(']')[0]
args = [a.strip() for a in body.split(',')]
if args.count('"dpu-retire-pacing=1"') != 1:
    raise SystemExit('retire pacing verify: dpu-retire-pacing=1 not exactly once in payload kernel_args')
if t.count('"dpu-retire-pacing=1"') != 1:
    raise SystemExit('retire pacing verify: dpu-retire-pacing=1 not exactly once in board.toml')
if args.count('"vsync=120"') != 1 or '"vsync=60"' in args:
    raise SystemExit('retire pacing verify: payload kernel_args vsync drift (E2b keeps 120)')
if '"vsync-fixed=1"' not in args:
    raise SystemExit('retire pacing verify: vsync-fixed=1 lost from payload kernel_args')
for a in ['"diag=1"', '"gpu-trace=1"', '"diag-export=600"', '"gpu-perf=1"', '"dpu-early-done=1"']:
    if t.count(a) != 1:
        raise SystemExit('retire pacing verify: measurement param drift: ' + a)
print('retire pacing verified: payload dpu-retire-pacing=1 exactly once, vsync=120 + vsync-fixed=1 kept, diag + dpu-early-done params intact')
PY
