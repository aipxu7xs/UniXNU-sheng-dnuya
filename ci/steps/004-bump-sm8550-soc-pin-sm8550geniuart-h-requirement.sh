python3 - <<'PY'
import pathlib
OLD = 'a9f45dc60c035084b95463781538380f4c3606c9'
NEW = '2dc650ca76ae38715cd0712e60a44b14fe251745'
for rel in ('device/feeds.toml', 'device/unixnu.lock'):
    p = pathlib.Path(rel)
    t = p.read_text()
    if OLD in t:
        p.write_text(t.replace(OLD, NEW))
        print(rel + ': SoC pin ' + OLD[:8] + ' -> ' + NEW[:8])
    elif NEW in t:
        print(rel + ': already on ' + NEW[:8])
    else:
        raise SystemExit(rel + ': unexpected SoC pin; inspect feeds.toml')
PY
