python3 - <<'PY'
import ast, pathlib
helper = '"""Controlled sheng GICR priority-store instruction experiment; no register changes."""\nfrom pathlib import Path\n\nOLD = \'\'\'  for (unsigned offset = 0x400; offset < 0x420; offset += 4) {\n    write32 (sgi, offset, 0x80808080);\n  }\'\'\'\nNEW = \'\'\'  // sheng experiment: preserve eight 32-bit priority writes without address writeback.\n  // The 24A446 fault PC was a post-index STR at this loop (ESR 0x96000010).\n  // Keep register offsets, values and the final barrier unchanged.\n  for (unsigned offset = 0x400; offset < 0x420; offset += 4) {\n    const uint32_t priority = 0x80808080;\n    const uintptr_t address = sgi + offset;\n    __asm__ volatile ("str %w0, [%1]" :: "r" (priority), "r" (address) : "memory");\n  }\'\'\'\n\ndef apply(text):\n    if NEW in text:\n        assert text.count(NEW) == 1 and OLD not in text\n        return text\n    assert text.count(OLD) == 1, \'GICR priority loop missing or ambiguous\'\n    start = text.index(\'bool ArmCpu::wakeRedistributor (bool local)\')\n    end = text.index(\'bool ArmCpu::prepareGic (void)\', start)\n    assert OLD in text[start:end], \'priority loop outside intended function\'\n    result = text.replace(OLD, NEW, 1)\n    assert result.count(NEW) == 1 and OLD not in result\n    return result\n\ndef patch(path):\n    source = Path(path)\n    original = source.read_text(encoding=\'utf-8\')\n    result = apply(original)\n    if result != original:\n        source.write_text(result, encoding=\'utf-8\')\n    print(\'GIC_PRIORITY_STORE: plain STR, offsets 0x400..0x41c, value 0x80808080\')\n'
pathlib.Path('UniXNU/scripts/sheng-gic-priority.py').write_text(helper, encoding='utf-8')
p = pathlib.Path('UniXNU/scripts/build-arm-driver.py')
t = p.read_text(encoding='utf-8')
anchor = "source = ROOT / 'drivers' / directory / filename"
hook = "if identifier == 'ArmCpu' and __import__('os').environ.get('UNIXNU_IPSW_BUILD') == '24A446':\n    __import__('runpy').run_path(str(ROOT / 'scripts/sheng-gic-priority.py'))['patch'](source)"
assert t.count(anchor) == 1 and hook not in t
t = t.replace(anchor, anchor + chr(10) + hook, 1)
assert hook in t
ast.parse(t)
p.write_text(t, encoding='utf-8')
PY
