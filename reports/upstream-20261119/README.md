# sheng / iPadOS 27 fixed upstream integration

Snapshot: `92158731b9f32509b7ccd612ab25eea118f24eaa68b32aa8722be424b646f547`. Target: iPadOS 27.0.1, 24A446. Source review completed on 2026-11-19.

## Meaning of the decisions

`integrated` means the applicable terminal source is selected in the sealed overlay/component installer. It does not mean that the new source has passed native compilation or booted on this device. Historical intermediate commits are covered by the selected terminal source, with per-file source hashes and explicit retained adaptations. `not-applicable` identifies documentation, unselected profiles/components, superseded historical paths, or rolling dependency HEADs outside the selected ABI/source locks. `pending-validation` is used for unmerged PR material and any unfinished validation.

## Complete fixed inventories

- Root history: 1416 commits, 849 integrated and 567 not applicable; zero unresolved source decisions.
- Root endpoint delta: 443 entries, including 52 directory containers. 127 source files and 7 changed component links are selected. Directory containers are not independent code changes.
- SoC: all 9 commits from a9f45dc6 through 2dc650ca are selected by the existing exact SoC pin.
- Component extension: 881 commits; 242 covered by selected code and 639 rolling external dependency changes outside the official source locks.
- 56 captured source repositories have explicit HEAD-upgrade dispositions. Sixteen distinct canonical component repositories provide the selected 11 top-level plus 7 device links (two repositories appear in both groups).
- 15,482 unmerged-PR file records are separate. Their 3,826 target-potential records remain pending upstream integration/target validation and are not reported as merged updates.
- Supplemental framework commit 8542980d changes only device records/documentation; the fixed code endpoint remains 519d8024.

## Effective build provenance

The legacy root checkouts remain device 68800685, framework 71b8a5a3 and UEFI b303410c. CI applies the existing reviewed repairs first, then the complete fixed endpoint overlay immediately before packaging. The parent Git index and actual component checkout HEADs are advanced together, so source fetching cannot silently restore older component links. `ci/frozen-sync/sources.json` and the hard-coded installer manifest hash bind every changed source preimage/postimage. `frozen-upstream-effective.json` and the postbuild record distinguish the root checkout identities from the selected fixed source endpoints.

QcaBluetooth fa528145 and QcomDwc3 f5edd26d include the captured extra runtime fixes. USB retains the measured device-only adapter. Adreno740's captured alternative head and the selected pin have the same full Git tree; ShengUfs likewise. ArmCpu, AdrenoMetal, Wi-Fi and touch post-pin endpoint deltas are documentation only. The new Metal pair is AdrenoMetal c9ebd2fb plus translator 46e7cc96 and exact patches 0063/0064. Mesa160 and its ordered repair stack are preserved. GIC plain stores, iPadOS diagnostics and firmware hooks remain in place. Platform sleep stays disabled.

## Validation and device state

Host checks: 651 Python sources, 187 TOML files, 140 shell scripts, workflow parsing/order, exact root preimages, tamper rejection, repeat application with zero source writes, and the existing Python tests (41 passed, 1 skipped). These checks are host-only. Native CI, exact artifact validation and hardware qualification are tracked separately.

The device was observed in fastboot on slot A at 2026-11-19 18:29 China time; recovery ADB was absent. No device write occurred in this continuation. The previous B-slot restoration still requires recovery readback, and the prior ABL load/authentication failure remains unresolved. Preserve userdata and the retained Data seed. Do not format, erase, reset Data, write userdata, or substitute the unrelated mayfly recovery image. New persistent deployment is gated on the native artifact, recovery readback, rollback and ABL evidence.
