python3 - <<'PY'
import ast
import pathlib
patches = [
    ('device/scripts/build-qcom-iris.py', "    (out / (source.stem + '.command.json')).write_text", '    ', 'cmd'),
    ('UniXNU/scripts/build-arm-driver.py', "(out / 'compile-command.json').write_text", '', 'command'),
    ('UniXNU/scripts/build-sheng-source-drivers.py', '    return command', '    ', 'command'),
]
for rel, marker, indent, argv in patches:
    p = pathlib.Path(rel)
    t = p.read_text()
    assert t.count(marker) == 1, (rel, 'optimization anchor must be unique')
    lines = [
        indent + "if __import__('os').environ.get('UNIXNU_IPSW_BUILD') == '24A446':",
        indent + '    ' + argv + ".append('-Oz')",
        indent + '    ' + "print('BOARD_OPT', str(source), [v for v in " + argv + " if v.startswith('-O')], file=__import__('sys').stderr, flush=True)",
    ]
    replacement = chr(10).join(lines) + chr(10) + marker
    t = t.replace(marker, replacement, 1)
    assert replacement in t, (rel, 'optimization replacement missing')
    ast.parse(t)
    p.write_text(t)
    print('Patched independent builder:', rel)
PY
