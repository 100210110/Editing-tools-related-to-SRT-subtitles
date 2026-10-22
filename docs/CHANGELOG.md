# 变更日志

> 本文件记录**功能级 / 结构级**变更；日常小修小补由 git log 承担。
> 另：**检查 / 收尾类任务即使没有代码变更，也记录结论**，避免日后无法判断是否需要重新检查。
> 分工：本文件只记录**已完成**的变更，未完成的任务统一见 `TODO.md`。
> 格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，按时间倒序，最新在最上面。
> 已完成的事项从 `TODO.md` 迁移至此。

---

## [未发布]

### 新增

- 实现 `repeat` 重复词规则（`软件本体/plugins/srt关键词替换/build_automaton.py`）：外层 `enabled=false` 时整条规则不生效（不识别、不压缩、不加分隔符）；`interval.enabled` 只控制是否插入分隔符，不影响压缩与识别。
- 识别语义：只识别无空格、无标点的连续同词重复（如 `哈哈哈哈`）；`哈 哈 哈`、`哈，哈` 不视为重复。
- 压缩与分隔相互独立：原始连续次数超过 `max_times` 时只保留 `max_times` 个；`interval.enabled=true` 且原始连续次数 ≥ `min_consecutive` 时，在保留的词之间插入 `separator`，门槛按压缩前次数计算。
- 处理顺序为 delete/replace → repeat → 输出；敏感词计数在 delete 阶段定稿，repeat 不改变计数。同位置多规则按 `max_times` 小者优先，其次长词优先。
- 实现选用 Aho-Corasick：复用项目已有 `pyahocorasick` 依赖，可一次扫描全部重复词；repeat 使用独立自动机并在 delete/replace 之后执行，避免同一关键词的删除/替换动作被覆盖（若用正则需逐个转义，且难以处理重叠与优先级）。
- pkl 缓存载荷新增 `repeat_automaton` / `repeat_rule_map`；旧缓存缺少这两个键时加载失败并自动强制重建（`_save_to_cache` / `_load_from_cache`）。
- 规则编辑器为 Repeat 对话框补充 tooltip，说明外层启用、压缩与分隔独立、门槛按原始次数、分隔符作用；默认规则 JSON 与新语义一致，无需修改（`软件本体/plugins/srt关键词替换/subtitle_rule_editor.py`）。
- 验证结论（2026-10-22，临时无头脚本，38 项全通过）：覆盖仅压缩、仅分隔、压缩+分隔、压缩但不分隔、未达间隔门槛、原始次数门槛、间隔关闭仍压缩、外层禁用、多规则优先级、长词优先、空格/标点不识别、delete/replace 交互与敏感词计数、真实默认规则回归，以及缓存命中、JSON 更新后不删 pkl 自动失效、旧缓存重建、`force_rebuild`。长词优先按“词出现次数”口径验证：`哈哈哈哈` 中 `哈哈` 恰好 2 次，不压缩；`哈哈哈哈哈哈` → `哈哈哈哈`（规格原例 `哈哈哈哈 → 哈哈` 按此口径属于笔误，已按确认口径验证）。
- 归档自 `TODO.md` #3，编号不复用。

### 修复

- 插件安装前校验 manifest 的 `plugin_id`（未提供时回退 `name`）：仅允许字母、数字、下划线、连字符与中文，拒绝空值、`.`/`..`、路径分隔符、盘符与绝对路径，校验失败时中止安装并提示（`软件本体/load_zip.py`）。
- 用 `os.path.realpath` + `os.path.commonpath` 校验安装目标必须位于 `plugins/` 下（Windows 经 `normcase` 忽略大小写），并在 `shutil.rmtree` 前再次校验；原有 zip 成员路径检查保持不变（`软件本体/load_zip.py`）。
- 验证结论（2026-10-22，临时无头脚本 + 模拟弹窗）：正常 zip 可安装；`../x`、`/abs`、`..\x`、`C:\x`、空值与非法字符均被拒绝，已有插件目录及 `plugins/` 外哨兵目录未被删除；越界目标路径被拒绝。符号链接场景因 Windows 权限不足未执行（SKIP）。
- `install()` 现在返回真实安装结果：成功 `True`；路径校验、旧目录清理、解压等任一环节异常返回 `False`，错误弹窗保留；`load_zip_json()` 同时覆盖非 zip、缺失 `manifest.json` 等打开/解析失败（`软件本体/load_zip.py`）。
- `check_version_and_install()` 改为三态返回：`True`=安装成功、`False`=安装失败、`None`=用户取消重装；取消不再计为失败（`软件本体/load_zip.py`）。
- `import_plugin_list()` 按单项结果归入 `success_list` / `failed_files` / `skipped_files`；主程序现有逻辑无需改动，仍只从 `FILE_LIST` 移除成功项，失败项保留并弹窗，取消项保留且不报错（`软件本体/load_zip.py`）。
- 验证结论（2026-10-22，临时无头脚本 + 模拟弹窗）：正常 zip 成功；非 zip、缺 `manifest.json`、缺 `name`/`version`、含越界成员 zip、模拟清理失败均进入 `failed_files` 且不删除既有目录；同版本/低版本取消重装进入 `skipped_files`，不计失败；混合导入三条列表均正确。真实弹窗点击尚未手工验证，脚本以模拟 `No`/`Yes` 覆盖返回语义。
- 归档自 `TODO.md` #1、#2，编号不复用。

### 说明

- TODO 初始化后完成前三项（#1 插件安装路径穿越、#2 安装失败仍报成功、#3 repeat 规则）；其余 21 项待办不变。
