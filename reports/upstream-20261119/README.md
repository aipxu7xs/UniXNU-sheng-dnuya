# sheng / iPadOS 27 repository-scoped upstream integration

The target is iPadOS 27.0.1, 24A446. The fixed audit snapshot is unchanged.

The user clarified the adoption policy: synchronize the complete sheng repository; enumerate shared framework changes and select those needed by sheng/iPadOS 27; synchronize all SM8550-common changes except adaptations exclusive to another board. Source synchronization and target activation are distinct fields in the endpoint inventory.

The sealed installer contains 167 root source files and 16 canonical component HEAD/index bindings. All 158 sheng endpoint file/gitlink changes are selected, preserving declared local adaptations. Twenty framework file/gitlink entries are selected wholly or in documented parts. The SoC range contains nine commits and ten changed paths; none is an adaptation exclusive to another device.

Desktop icon-cache generation, the new Aqua/Shader Cache registration, macOS reference-target expansion and other-board catalog changes are excluded from the selected framework delta. Full upstream sheng sources, including non-iPadOS utilities, remain synchronized. The iPadOS configuration disables platform sleep and uses the ios27 build entrypoint. A source-scope gate checks the exact shared builders, profile and data-preserving arguments. The native Metal artifact gate rejects desktop addon entries.

See README.zh.md for the per-item shared-framework list, repository-endpoint-adoption-inventory.json for every endpoint decision, root-commit-dispositions.jsonl for all 1,416 root commits, soc-commit-dispositions.jsonl for every SoC commit and file, and component-dispositions.json for all selected components and unselected platform tools. Unmerged PRs remain separate from upstream mainline adoption.

The previous native run 44507255994 failed while compiling the Metal translator for iOS. Patch 0065 shares the existing Darwin Mach memory path with iOS; a fresh native rebuild is required. Host checks are not native-build, artifact or hardware evidence. No qualified new image or successful device boot is claimed. Deployment still requires recovery rollback readback, ABL loading and preservation of the existing Data state.
