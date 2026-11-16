python3 - <<'PY'
import pathlib
helper = '#!/usr/bin/env python3\n"""sheng diagnostic: make the XNU SError unhandled branch print its syndrome.\n\narm64_implementation_specific_error() drops esr/far and panics with a fixed text,\nso the early SError seen on 24A446 cannot be attributed. This only widens that\npanic message; no control flow, mapping or driver behaviour changes.\n"""\nimport pathlib\n\nSOURCE = pathlib.Path(\'.cache/xnu-work/osfmk/arm64/sleh.c\')\nMARKER = \'SHENG SERROR DIAG\'\nOLD = \'\\tpanic_plain("Unhandled implementation specific error\\\\n");\'\nNEW = (\n    \'\\t/* SHENG SERROR DIAG: report the syndrome the unhandled branch hides. */\\n\'\n    \'\\tpanic_plain("SError unhandled: esr=0x%016llx ec=%u iss=0x%08x\\\\n"\\n\'\n    \'\\t    "\\\\tfar=0x%016llx pc=0x%016llx lr=0x%016llx\\\\n",\\n\'\n    \'\\t    (unsigned long long)esr, (unsigned)ESR_EC(esr), (unsigned)ESR_ISS(esr),\\n\'\n    \'\\t    (unsigned long long)far, (unsigned long long)get_saved_state_pc(state),\\n\'\n    \'\\t    (unsigned long long)get_saved_state_lr(state));\\n\'\n)\n\n\ndef main():\n    if not SOURCE.is_file():\n        raise SystemExit(\'sleh.c not prepared: %s\' % SOURCE)\n    text = SOURCE.read_text(encoding=\'utf-8\')\n    if MARKER in text:\n        print(\'sleh.c: SError syndrome diagnostic already installed\')\n        return\n    if text.count(OLD) != 1:\n        raise SystemExit(\'SError panic branch not unique: %d\' % text.count(OLD))\n    text = text.replace(OLD, NEW, 1)\n    assert MARKER in text and OLD not in text\n    SOURCE.write_text(text, encoding=\'utf-8\')\n    print(\'sleh.c: SError syndrome diagnostic installed\')\n\n\nif __name__ == \'__main__\':\n    main()\n'
pathlib.Path('UniXNU/scripts/sheng-serror-diag.py').write_text(helper, encoding='utf-8')
p = pathlib.Path('UniXNU/scripts/build-xnu-4k-baseline.sh')
t = p.read_text(encoding='utf-8')
anchor = 'python3 scripts/prepare-xnu-source.py' + chr(10)
assert t.count(anchor) == 1, 'prepare-xnu-source anchor must be unique'
call = 'python3 ' + chr(34) + '$ROOT/scripts/sheng-serror-diag.py' + chr(34) + chr(10)
assert call not in t, 'diagnostic call already inserted'
t = t.replace(anchor, call + anchor, 1)
assert call in t
p.write_text(t, encoding='utf-8')
print('build-xnu-4k-baseline.sh: SError diagnostic hook inserted')
PY
