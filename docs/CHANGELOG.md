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

### 测试

- 建立 pytest 测试框架（`tests/`，共 60 项用例）：`conftest.py` 提供按文件路径加载被测模块（兼容中文目录名）、`load_zip` 的 `get_path` 与三类弹窗 monkeypatch 隔离、插件 zip 工厂、规则 JSON/pkl 临时工作区，以及 Windows 目录联接工厂（无权限时自动 SKIP）。新增 `requirements-dev.txt` 固定 `pytest==9.1.1`，运行基准为 `pytest tests/`（在项目 `.venv`，Python 3.11 下执行）。
- 固化插件安装器回归测试（`tests/test_installer.py`，29 项）：合法 `plugin_id` 4 类（英文、数字下划线连字符、中文、纯数字）与非法 11 类（`../x`、`/abs`、`..\x`、`C:\x`、空值、纯空格、正/反斜杠、`.`、`..`、含点号）分别验证安装与拒绝；另覆盖缺 `plugin_id` 回退 `name`、合法 id 但目标为目录联接指向 `plugins/` 外、非 zip、缺 `manifest.json`、缺 `name`/`version`、非法 JSON、首次安装返回 `True`、含越界成员 zip 返回 `False`、同版本与低版本取消返回 `None`、同版本确认重装覆盖、`import_plugin_list()` 三列表分组，以及越界拒绝后既有插件目录与 `plugins/` 外哨兵文件均未被删除。
- 固化安装失败路径测试（`tests/test_installer_failures.py`，5 项）：只读文件与占用文件触发 `rmtree` 失败、manifest 读取后 zip 被损坏、zip 内文件与目录同名导致 `extractall` 真实失败，均确认 `install()` 返回 `False`、旧目录保留且弹出错误；目录不可写场景在当前环境无法用普通权限模拟，按约定标 SKIP 并给出原因。
- 固化 repeat 回归测试（`tests/test_repeat.py`，16 项）：压缩与分隔独立触发、原始连续次数门槛（不按压缩后次数）、外层 `enabled=false` 整条跳过、多规则 `max_times` 小者优先与同 `max_times` 长词优先、重复按词出现次数计口径、带空格/标点不识别、delete/replace 先于 repeat 且敏感词计数不变、真实 `subtitle_rules.json` 与 `default_subtitle_rules.json` 回归、缓存命中与失效重建两条路径下 repeat 状态一致。
- 固化 pkl 缓存校验回归测试（`tests/test_cache.py`，10 项）：冷启动重建并写入 `json_content_hash` 与 `schema_version`、同内容第二次加载命中不重建、JSON 内容变化失效、仅缩进与键顺序变化仍命中、schema 版本不匹配失效、哈希不匹配失效、损坏 pkl 自动重建不崩溃、旧载荷缺字段重建、`force_rebuild=True` 跳过校验并写回新哈希、命中与重建路径 repeat 规则一致。
- 验证结论（2026-10-22，`.venv` 下 `pytest tests/ -q`）：收集 60 项，**59 passed / 1 skipped**，唯一 SKIP 为「当前环境无法用普通权限模拟目录不可写」；目录联接越界用例在本机真实执行并通过（未走 SKIP）；`test_repeat.py` 对真实规则文件只读，未改写仓库内 JSON 或 pkl。任务全程未改动被测源码，测试运行后 `git status` 仅显示新增的 `tests/` 与 `requirements-dev.txt`。
- 归档自 `TODO.md`「可选增强 / 测试补强」中 5 项可自动化条目；`插件导入 GUI 手工冒烟`、`repeat 规则 GUI/真实缓存手工冒烟`、`主程序真实缓存手工冒烟` 3 项需真实界面操作，仍保留在该节待人工执行。

### 修复

- 插件安装前校验 manifest 的 `plugin_id`（未提供时回退 `name`）：仅允许字母、数字、下划线、连字符与中文，拒绝空值、`.`/`..`、路径分隔符、盘符与绝对路径，校验失败时中止安装并提示（`软件本体/load_zip.py`）。
- 用 `os.path.realpath` + `os.path.commonpath` 校验安装目标必须位于 `plugins/` 下（Windows 经 `normcase` 忽略大小写），并在 `shutil.rmtree` 前再次校验；原有 zip 成员路径检查保持不变（`软件本体/load_zip.py`）。
- 验证结论（2026-10-22，临时无头脚本 + 模拟弹窗）：正常 zip 可安装；`../x`、`/abs`、`..\x`、`C:\x`、空值与非法字符均被拒绝，已有插件目录及 `plugins/` 外哨兵目录未被删除；越界目标路径被拒绝。符号链接场景因 Windows 权限不足未执行（SKIP）。
- `install()` 现在返回真实安装结果：成功 `True`；路径校验、旧目录清理、解压等任一环节异常返回 `False`，错误弹窗保留；`load_zip_json()` 同时覆盖非 zip、缺失 `manifest.json` 等打开/解析失败（`软件本体/load_zip.py`）。
- `check_version_and_install()` 改为三态返回：`True`=安装成功、`False`=安装失败、`None`=用户取消重装；取消不再计为失败（`软件本体/load_zip.py`）。
- `import_plugin_list()` 按单项结果归入 `success_list` / `failed_files` / `skipped_files`；主程序现有逻辑无需改动，仍只从 `FILE_LIST` 移除成功项，失败项保留并弹窗，取消项保留且不报错（`软件本体/load_zip.py`）。
- 验证结论（2026-10-22，临时无头脚本 + 模拟弹窗）：正常 zip 成功；非 zip、缺 `manifest.json`、缺 `name`/`version`、含越界成员 zip、模拟清理失败均进入 `failed_files` 且不删除既有目录；同版本/低版本取消重装进入 `skipped_files`，不计失败；混合导入三条列表均正确。真实弹窗点击尚未手工验证，脚本以模拟 `No`/`Yes` 覆盖返回语义。
- pkl 缓存校验改用规则 JSON 的内容哈希：`json.dumps(json.loads(content), sort_keys=True, ensure_ascii=False)` 规范化后取 SHA-256，纯缩进/键顺序变化不触发重建；新增 `CACHE_SCHEMA_VERSION = 2` 标识载荷结构，载荷写入 `json_content_hash` 与 `schema_version`（`软件本体/plugins/srt关键词替换/build_automaton.py`）。
- `_load_from_cache()` 改为完整校验链：pkl 缺失、`pickle.load` 异常、载荷非 dict、schema 版本不一致、内容哈希不一致、必要字段缺失均返回 `None` 并自动重建；`force_rebuild=True` 跳过校验强制重建并写回新哈希。原 `_is_cache_valid()`（仅按 mtime 判断）已移除。
- `load_rules()` 在缓存校验前先调用 `_get_json()` 重新读取当前 JSON，保证哈希基于实际生效的规则文件（含回退写入的默认配置）；重建前清空旧解析状态，避免复用实例时残留旧规则。
- 确认 `subtitle_rules.pkl` 已不受版本控制（自提交 `9cade55` 起移出索引），`.gitignore` 已含 `*.pkl`；工作区 pkl 保留，本任务无需再执行 `git rm --cached`。
- 补充 AI_CONTEXT 维护规则：§10.5 新增「AI_CONTEXT §11 修复标注」，§11 已修复条目在问题描述末尾括注日期，不改写原诊断；本次已为 #1、#2、#3、#5 添加标注（`docs/AI_CONTEXT.md`）。
- 验证结论（2026-10-22，临时无头脚本，45 项全通过）：覆盖冷启动生成 pkl、mtime 反向仍命中、JSON 内容变化失效、仅格式化命中、schema 版本变化失效、损坏/非字典/旧字段缺失 pkl 自动重建、`force_rebuild` 跳过校验并更新哈希、`_load_from_cache()` 返回值；真实默认规则在构建/命中/失效三条路径下 repeat 行为与缓存状态一致。未走主程序与规则编辑器 GUI，已记入 TODO 长期测试补强。
- 归档自 `TODO.md` #1、#2、#5，编号不复用。

### 说明

- TODO 初始化后已完成 #1、#2、#3、#5（插件安装路径穿越、安装失败仍报成功、repeat 规则、pkl 缓存校验与入库）；其余 20 项待办不变。
- 2026-10-22 补充 pytest 测试框架与 5 项回归固化（见上文「测试」节），`TODO.md` 中对应条目已打勾留痕；GUI/主程序手工冒烟 3 项仍待人工执行。
