# sheng / iPadOS 27 上游逐项采用清单

适用目标：iPadOS 27.0.1（24A446）。审计固定快照不变，按用户最新仓库规则重新判断。

| 仓库 | 同步规则 | 本次范围 |
| --- | --- | --- |
| unixnu-sheng | 全部同步，保留已申明本地适配 | 158 个文件或 gitlink 终点变化，全部已作源码采用判断 |
| unixnu | 通用改动逐项判断 sheng / iPadOS 27 是否需要 | 20 个采用项，其余每项均有排除理由 |
| unixnu-sm8550-common | 全部同步，其他设备专属除外 | 9 个提交、10 个变化路径；本范围未发现其他设备专属改动 |

## unixnu：需要的通用更新

| 路径 | 是否需要 | 判断及采用范围 |
| --- | --- | --- |
| `components.toml` | 需要 | 绑定所选组件版本及所需源码清单；原有其他 ABI 元数据不代表本次启用。 |
| `devices.toml` | 部分需要 | 只更新 sheng 记录；其他设备的记录更新已恢复。 |
| `drivers/AdrenoMetal` | 需要 | 采用共享 Metal frontend、Rust bridge 和 translator 修复；macOS Shader Cache.app 工具不在 iPadOS 构建入口。 |
| `drivers/ArmCpu` | 需要 | 采用 MMIO 单条汇编读写修复；平台睡眠代码保留为共享组件源码，当前 sleep-disabled=1 且未启用 platform-sleep。 |
| `scripts/build-adreno-metal-bridge.py` | 需要 | 选择 translator 46e7cc96、0063/0064 补丁，并加独立 iOS Mach 0065 适配；目标 ios27/arm64e。 |
| `scripts/build-boot-runtime.py` | 部分需要 | 保留系统临时挂载目录修复；不采用桌面图标缓存函数及其 LaunchDaemon。 |
| `scripts/build-fileset-release-reference.py` | 部分需要 | 保留编译/链接阶段门禁及诊断符号；不采用 macOS target/ABI 扩展。 |
| `scripts/build-sheng-source-storage.py` | 需要 | 存储输入预检查与失败日志；供 sheng 原生存储构建使用。 |
| `scripts/data/gpu-metal-vulkan-inputs.json` | 需要 | 固定实际 translator 版本和输入哈希，与 bridge 及产物门禁一致。 |
| `scripts/unixnu/cli.py` | 需要 | 构建前工具链/内核预检查、payload 构建完成标志，拒绝未完成产物。 |
| `scripts/unixnu/firmware.py` | 需要 | 固件工具链一致性检查；保留已有 sheng firmware callbacks。 |
| `scripts/unixnu/kernel.py` | 需要 | 内核构建前检查及根信任策略输入验证。 |
| `scripts/unixnu/payload.py` | 需要 | payload pending/complete 生命周期；失败残留不得当成可用镜像。 |
| `scripts/unixnu/root_policies.py` | 需要 | 验证 OS/SystemOS 的安装者公钥、镜像记录与 UUID；原子安装策略输入。 |
| `scripts/unixnu/util.py` | 需要 | 统一验证 CLANGPDB 工具和 clang/LLD 版本；这是构建主机工具，与 guest 目标无冲突。 |
| `tests/build/test_archive_providers.py` | 主机验证需要 | 验证归档供应者相关通用输入路径。 |
| `tests/build/test_firmware_toolchain.py` | 主机验证需要 | 验证固件构建工具链检查。 |
| `tests/build/test_payload_pending.py` | 主机验证需要 | 验证不完整 payload 的拒绝行为。 |
| `tests/build/test_release_reference.py` | 部分需要 | 保留编译/链接门禁回归；删除 macOS target-definition 测试。 |
| `tests/build/test_root_policy_inputs.py` | 主机验证需要 | 验证根信任策略输入，覆盖无效输入及 owner key 一致性。 |

## 明确未采用的桌面更新

- `scripts/make-gpu-addon.py` 本次上游增量：macOS Shader Cache.app / Aqua 注册，已恢复预整合版本。
- `tests/build/test_icon_cache_job.py`、`test_shader_cache_addon.py`：随桌面功能一起退出本次采用清单。
- `build-boot-runtime.py` 的桌面 icon-cache 函数和 LaunchDaemon；保留系统临时挂载修复。
- release reference 的 macOS target/ABI 扩展；保留编译/链接失败门禁。
- `devices.toml` 中其他设备更新；只保留 sheng 条目。

## sheng 源码中仍存在的 macOS 内容

这是按“unixnu-sheng 全部同步”保留的上游内容，不等于 iPadOS 构建采用。完整 JSON 对每条记录分别给出源码采用和目标需要性。
- macOS lab/安装脚本、专用报告和政策输入：源码同步，iPadOS 不执行。
- 合盖、键盘指针、平台睡眠：共享或条件分支保留；当前 profile 的 `sleep-disabled=1`，无 `platform-sleep=1`。
- macOS ShaderCache 应用及 Bluetooth macOS 工具位于固定组件源码中；ios27 构建入口不选择它们。
- Darwin Mach 内存读取是 iOS/macOS 共享接口。新增 0065 解决 iOS 编译缺失，不是桌面功能。

## 完整清单与证据

- `repository-endpoint-adoption-inventory.json`：全部文件/gitlink 终点及目标判断。
- `root-commit-dispositions.jsonl`：完整 1,416 个 root 历史提交及逐文件终点覆盖。
- `soc-commit-dispositions.jsonl`：9 个提交的实际文件列表；`soc-endpoint-file-dispositions.json`：10 个变化路径。
- `component-dispositions.json`：16 个组件的固定版本、保留适配和不选用的平台工具。
- 未合并 PR 与正式上游分开列出；未将候选 PR 计为已合入。

## 验证边界

源码同步与目标判断已列明；主机验证、原生 CI、实际产物、设备启动分开记录。前一轮原生 run 44507255994 编译失败；0065 尚待原生重编译。没有据此声称实机成功，也未写入设备分区。
