#!/usr/bin/env bash
# Guard GPU self-test buffers that have no CPU mapping.
# Runs after 010-repair-gpu-selftest-iova-and-kernel-client-contract.sh, whose
# transforms leave the mapping() call sites untouched. On this device the
# buffers can be device-mapped yet have no CPU mapping, so mapping() returns
# null and the first fill store faults at address 0. Skip the affected
# sub-tests when a mapping is missing; callers already tolerate failure.
set -euo pipefail
python3 - <<'PY'
from pathlib import Path

def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("expected exactly one anchor: " + old[:80])
    return text.replace(old, new, 1)

p = Path("package/GpuPowerProbe.cpp")
text = p.read_text(encoding="utf-8")
if "if (!iw || !tw)" in text or "if (bw && iw)" in text or "if (tw && iw)" in text:
    raise ValueError("guards already applied; refusing to patch twice")

# ucRound: both CPU mappings are dereferenced by the fill loop and the IB
# build. Bail through the step-010 finish lambda so the BOs are still freed.
old = "    volatile uint32_t *iw = static_cast<volatile uint32_t *>(ibMem->mapping()), *tw = static_cast<volatile uint32_t *>(tgtMem->mapping());\n"
text = once(text, old, old + "    if (!iw || !tw) { step(kIOReturnNotReady); return finish(-1); }\n")

# ucStress big-buffer block: wrap the dereferences in a mapping check.
old = """            volatile uint32_t *bw = static_cast<volatile uint32_t *>(bm->mapping());
            volatile uint32_t *iw = static_cast<volatile uint32_t *>(im->mapping());
"""
text = once(text, old, old + "            if (bw && iw) {\n")
old = """            }
        }
    }
    // Burst:"""
new = """            }
            }
        }
    }
    // Burst:"""
text = once(text, old, new)

# ucStress burst block: same pattern.
old = """            volatile uint32_t *tw = static_cast<volatile uint32_t *>(tm->mapping());
            volatile uint32_t *iw = static_cast<volatile uint32_t *>(im->mapping());
"""
text = once(text, old, old + "            if (tw && iw) {\n")
old = """            }
        }
    }
    // Drain and free"""
new = """            }
            }
        }
    }
    // Drain and free"""
text = once(text, old, new)

for guard in ("if (!iw || !tw)", "if (bw && iw)", "if (tw && iw)"):
    if text.count(guard) != 1:
        raise ValueError("guard missing or duplicated after patch: " + guard)
p.write_text(text, encoding="utf-8", newline="\n")
print("GPU selftests: unmapped-buffer guards added (ucRound, ucStress x2)")
PY
