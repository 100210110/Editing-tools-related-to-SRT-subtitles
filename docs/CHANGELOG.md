# 变更日志

> 本文件记录**功能级 / 结构级**变更；日常小修小补由 git log 承担。
> 另：**检查 / 收尾类任务即使没有代码变更，也记录结论**，避免日后无法判断是否需要重新检查。
> 分工：本文件只记录**已完成**的变更，未完成的任务统一见 `TODO.md`。
> 格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，按时间倒序，最新在最上面。
> 已完成的事项从 `TODO.md` 迁移至此。

---

## [未发布]

### 检查

- 核实仓库卫生现状并归档 TODO #21：`AI_CONTEXT.md` §11 与 `TODO.md` #21 的描述（`cache/temp/ffmpeg-*.log` 与 `subtitle_rules.pkl` 被跟踪、`plugin_log/` 无 `.gitignore`）**已经过时**——`git ls-files` 显示 46 个跟踪文件中无 `.pkl`、无 `.log`、无 `plugin_log/`；根级 `.gitignore` 已覆盖 `*.log`、`*.pkl`、`软件本体/cache/{output,temp,plugin_backup}/`、`软件本体/output/`、`软件本体/plugins/*/plugin_log/`、`__pycache__/`、`build/`、`dist/`、`*.spec`、插件内 FFmpeg 二进制与 IDE/系统杂项；`git check-ignore` 对四类典型运行产物全部命中。工作区仍保留 4 个 `ffmpeg-*.log` 与规则 pkl（已被忽略，按“保留工作区文件”的要求不清除），`plugins/srt关键词替换/plugin_log/` 当前不存在（插件运行后才会生成，且已被忽略）。
- 补齐的唯一缺口是**文档准确性**：重写 `AI_CONTEXT.md` §3.4「仓库卫生现状」（跟踪文件数、产物不入库、`.gitignore` 覆盖范围、测试基础设施），关闭附录 A10（`plugin_log/` 策略 → 日志不入库，由 `RotatingFileHandler` 自行滚动 10 MB × 5），并给 §11「仓库卫生」条目加修复标注。
- 新增 `tests/test_repo_hygiene.py`（3 项）：`.gitignore` 必须包含 8 条关键规则；`git check-ignore` 必须命中 5 类典型运行产物；`git ls-files` 中不得出现 `.pkl`/`.log`/`plugin_log/`/`cache/` 路径。无 git 环境时自动 SKIP。
- 结论：TODO #21 的三条待办在代码/配置层面**早已完成**，本次只做核实 + 文档纠偏 + 回归护栏，未改动任何插件或主程序代码。
- 归档自 `TODO.md` #21，编号不复用。

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
- 手工冒烟结论（2026-10-22，作者在真机执行，3 项全部通过）：**插件导入 GUI**——正常 zip 可装、非 zip/缺 `manifest.json` 失败、同版本与低版本重装询问的“取消/确认”分支，失败项保留在 `FILE_LIST` 并弹窗、取消项保留且不报错；**repeat 规则 GUI/真实缓存**——规则编辑器新增/修改/禁用 repeat 规则并保存后，主程序连续处理两个 SRT 的输出、弹窗统计、编辑器提示与真实 `subtitle_rules.pkl` 的命中/失效均符合预期；**主程序真实缓存**——首次处理生成 pkl、第二次命中不重建、修改 `subtitle_rules.json` 后自动失效重建，且 repeat 输出一致。
- 归档自 `TODO.md`「可选增强 / 测试补强」全部 8 项（5 项自动化回归 + 3 项 GUI/真机手工冒烟）；该分类已清空，`TODO.md` 的「可选增强（长期）」小节保留但标注“当前无条目”。

### 文档

- 重写 `README.md`，从"零散使用笔记"改为面向使用者的完整说明：功能特性、快速开始（解压到可写目录 → 双击 → 拖入 → 点插件 → 导出）、使用说明（文件与列表 / 插件按钮 / 导入插件 / 导出 / 规则配置）、插件列表（4 个插件 + 状态 + 备注）、开发与构建（保留 #6 的安装节，补开发运行与打包命令）、已知限制、许可证与联系方式。
- **修正核心错误**：原 README 称"`config.json` 为删改词的配置，格式错误会覆盖"，实际规则在 `plugins/srt关键词替换/subtitle_rules.json`，`config.json` 只存名称/版本/更新日期/作者。新版给出三个文件的分工表，并说明 `default_subtitle_rules.json` 是兜底模板、`subtitle_rules.pkl` 是自动生成缓存。
- 规则说明按实际语义重写：推荐用「修改配置」按钮打开 PyQt5 规则编辑器；手工改 JSON 时注明 `delete.profanity` 计数、`delete.others` 仅删除、`repeat` 的 `enabled`/`max_times`/`interval` 各自含义与"按压缩前次数判断"、`replace` 分组树与 `source → word` 语义、`regex` 未实现、匹配区分大小写；并明确"JSON 语法错误会被默认规则覆盖工作文件"，需先备份。
- 补全此前完全缺失的说明：导入插件（zip 需进列表、manifest 要求、版本比较与询问、仅成功才刷新且不影响已处理产物）、导出（移动到 `output/`、同名加 `_1`/`_2`）、链式处理与 `cache/output` 的关系、重启刷新会清空缓存、插件运行期间主界面阻塞。
- 复核后追加的两处更正（2026-10-22 二次核对，均以源码为准）：①「srt加前缀」返回 `"popup": False`（`自动给srt加前缀.py:72`），主程序对假值只打印不弹窗，故"每次处理完都弹窗"的说法不成立，改为"关键词替换与 ASS 插件弹窗，「srt加前缀」结果看日志"；②规则编辑器实际是**一棵 `QTreeWidget` 带三个顶层根节点**（`subtitle_rule_editor.py:271-299`），不是三个独立树。
- 打包一节沿用 #6 的说明并补注：`打包exe指令.txt` 里的 `--name "v1.1.0"` 未跟随当前版本，打包前需改成实际版本号（与 `AI_CONTEXT.md` §9.3 的记录一致）。
- 依据实际发布产物补充两条说明（`发布zip/`）：①主程序包形如 `Re工具箱 - vX.Y.Z.zip`，另有「- 无插件」版，包内 exe 同名带版本号；插件单独发布（`srt关键词替换-v1.3.0.zip`，根目录含 `manifest.json`、`__init__.exe`、`subtitle_rules.json`）。②由此得出一条此前未记录的**规则丢失风险**：`load_zip.py:272/279` 安装时先 `rmtree` 旧插件目录再 `extractall`，而插件 zip 自带 `subtitle_rules.json`，所以升级/重装「srt关键词替换」会用 zip 里的规则覆盖用户改过的规则。README 已在「规则配置」中写明升级前先备份。
- 已知限制集中列出：ASS 插件需自备 FFmpeg（路径固定、仓库与发布包均未附带、未做端到端验证）、ASS 插件未进入发布产物、前缀插件假设四行结构、同名文件互相覆盖、程序目录必须可写、打包后规则编辑器"新建"路径未验证。
- 保留原 README 仍有效的内容与作者语气：`config.json` 里的联系方式（B 站 / Q 群 / GitHub）、DeepSeek AI 辅助记录、MIT 许可与版权人、"两天速成 UI"那句玩笑，以及"缓存暂存 → 继续处理 → 导出"的使用路径。
- 验证方式（2026-10-22）：逐条对照 `AI_CONTEXT.md` §9.6 冒烟清单与源码复核，涉及界面按钮文案（`插件调度主程序.py:215-280`、`408-413`）、前缀格式（`自动给srt加前缀.py:53` 的中文冒号）、ASS 报错文案（`ass转码透明底视频.py:111`）、删词统计口径（`srt_keyword_editor.py:32-57`，降序前 10）、规则读取失败的回退链（`build_automaton.py` 的 `_get_json`）、移动与同名后缀（`插件调度主程序.py:378-399`）、去重与多选（`468`、`216`）。**未重新执行 GUI 手工冒烟**，新版描述以静态核对为准。
- §9.6 未覆盖但 README 已描述的行为（遗留提醒，后续真机冒烟可补）：拖入去重、"移除选中"多选删除、"清空所有"连带清空 `cache/output`、导出后清空列表、导出同名 `_1`/`_2` 后缀、"重启刷新"清缓存、同名 basename 互相覆盖、规则 JSON 读不出来时被默认规则覆盖、插件同步阻塞导致的"未响应"、插件失败弹窗的折行阈值、文明小助手前 10 排名、前缀插件四行假设与重复叠加、日志面板实时输出与清空、打包 exe 全流程。以上均在源码中找到依据（含 #25 的隔离脚本验证与 `tests/` 单测），但 §9.6 十条冒烟项未逐条覆盖它们。
- 归档自 `TODO.md` #7，编号不复用。

### 变更

- 缓存输出改用**来源哈希前缀**，修掉不同目录同名 SRT 互相覆盖（TODO #12，用户口径：选哈希前缀方案）：输出名统一为 `<12位哈希>__<原文件名>`，哈希取源文件绝对路径（`os.path.normcase` 后）的 SHA-1 前 12 位——同一路径重复处理结果稳定，不同目录的同名文件则天然分开；已经带前缀的中间产物**沿用原名**，链式处理不会叠加第二层前缀。
  - 关键词替换插件：`common.py` 新增 `cache_output_name()` / `strip_cache_prefix()`，`srt_keyword_editor.main()` 用它构造输出路径；「文明小助手」统计仍按**原始文件名**展示，不出现哈希串（`软件本体/plugins/srt关键词替换/common.py`、`srt_keyword_editor.py`）。
  - 前缀插件：自身是单文件插件、无法 import 上面的 `common.py`，按**同一口径**复制了 `CACHE_NAME_PREFIX_RE` / `cache_output_name()` / `strip_cache_prefix()`（`软件本体/plugins/srt加前缀/自动给srt加前缀.py`）；说话人前缀也改为从原始文件名取，链式处理时不会变成 `0123456789ab__ep01：`。
  - 主程序：`move_all_files()` 导出时先 `strip_cache_prefix()` 还原原始文件名，同名再走原有 `_1`/`_2` 递增后缀，所以 `output/` 里的文件名与改动前一致（`软件本体/插件调度主程序.py`）。
- 变更 `tests/test_srt_prefix.py` 两项 main 端到端断言：输出名断言改为“以 `__a.srt` / `__ep03.srt` 结尾”，内容断言改为读取 `completed_output_lists` 返回的实际路径（不再假设 `<cache>/a.srt`）。
- 新增 `tests/test_cache_naming.py`（9 项）：同 basename 不同目录前缀不同、前缀稳定且幂等（已带前缀不再叠加）、`strip_cache_prefix` 还原且不误剥非 12 位十六进制前缀、两个插件口径一致；关键词替换插件 main（桩掉处理器）处理两个同名文件产出两份且统计不含 `__`；前缀插件 main 处理两个同名文件产出两份、说话人用原名，输入已带前缀时也取原名；`move_all_files` 导出还原原名并生成 `ep01.srt` / `ep01_1.srt`、缓存目录被移空。`conftest.py` 新增 `keyword_common_module` / `keyword_processor_module` / `prefix_plugin_module` 三个 fixture。
- `README.md` 三处同步：文件与列表的“请不要拖入同名文件”改为“可以放心拖入同名文件”，导出说明补充前缀会被剥离，已知限制里的“同名文件会互相覆盖”改为说明缓存名带哈希前缀（附“不是损坏”的提醒）；同时更新 #17 遗留的“打包后新建路径未验证”表述。
- **歧义说明**：TODO 只写了“哈希前缀或保留相对路径”，未规定长度与分隔符，这里取“12 位 + `__`”（12 位十六进制足以避碰，`__` 便于用 `strip_cache_prefix` 稳定剥离）；同名文件的敏感词统计仍按原文件名合并为一条，未按目录拆分。
- 归档自 `TODO.md` #12，编号不复用。

- 删除 `load_zip.py` 中失效的测试入口 `test_plugins_list()`（TODO #19）：该函数循环内只保留最后一个 `PluginInstaller`，空列表时 `plugin_zip` 未定义会抛 `UnboundLocalError`，且只对最后一个包调 `check_version_and_install()`；主程序从未调用它，正式入口是 `import_plugin_list()`。已确认全仓库无引用（仅 `AI_CONTEXT.md` §11 与 `TODO.md` 提及），直接删除；如需“遍历全部并正确处理空列表”的验证入口，应另建 pytest 用例而非保留 GUI 半成品函数（`软件本体/load_zip.py`）。
- 归档自 `TODO.md` #19，编号不复用。

- 新建根级 `requirements.txt`（runtime，严格 `==` 固定）：`PySimpleGUI==6.0`、`tkinterdnd2==0.4.3`、`pyahocorasick==2.3.1`、`pyass==0.1.4`、`packaging==26.1`、`PyQt5==5.15.11`；只列直接依赖，`PyQt5-Qt5`/`PyQt5-sip` 等间接依赖交给 pip 按上游约束解析。
- 调整 `requirements-dev.txt` 为 `-r requirements.txt` + `# test`（`pytest==9.1.1`）+ `# build`（`pyinstaller==6.20.0`），原先只有 pytest 一行。
- 补入 `PyQt5`：`.venv/old_requirements.txt` 一直缺该包，而规则编辑器 (`subtitle_rule_editor.py:5-11`) 依赖它，新环境按旧清单安装后打开编辑器会 `ModuleNotFoundError`。
- 移除 `pysub-parser`、`Unidecode`：AST 扫描 `软件本体/` 下 12 个 `.py` 的全部 import，两者零引用（全工作区 grep 也只在文档中出现），确认无隐式引用后从清单剔除（`Unidecode` 原为 `pysub-parser` 的传递依赖，一并消失）。
- 依赖核实结论（2026-10-22）：`PySimpleGUI` 6.0 在公开 PyPI 上存在（同页另有 6.2/6.3），wheel 为 `py3-none-any` 纯 Python 包，License 为 **LGPLv3**，无授权码或注册校验，普通 `pip install` 即可，**附录 A6 的授权疑问就此关闭**；`packaging` 实际安装 26.1，公开索引上已是 26.x 系列（最新 26.3），AI_CONTEXT §2.1 原记录的 26.1 与实测一致，无需更正；`pyass` 确认为 `xIceArcher/pyass`（ASS 解析库），非同名包；`PyQt5` 5.15.11 附带 `PyQt5-Qt5` 5.15.2 与 `PyQt5_sip` 12.18.0。
- README 新增「环境准备与安装」（Windows + Python 3.11.x、runtime/dev 两条安装命令）与「打包 exe」（指向工作区根目录的 `打包exe指令.txt`，说明需在 `软件本体/` 内执行）两节；规则与插件说明等段落未动，留给 #7。
- 验证结论（2026-10-22）：`pip install -r requirements.txt --dry-run --ignore-installed` 与 dev 版均解析通过（pip 26.1.2）；另建干净 venv（Python 3.11.9）实装 `requirements-dev.txt`，6 个包逐个 import 成功、`tkinterdnd2` 的 TkDnD 原生库初始化成功、主程序启动不报错、`pytest tests/` 为 **59 passed / 1 skipped**，与开发环境一致。新环境间接依赖存在小幅漂移：`PyQt5_sip` 12.18.0 → 12.20.0、`pyinstaller-hooks-contrib` 2026.4 → 2026.9（均在 PyQt5/PyInstaller 的上游约束内），未做锁定。
- 归档自 `TODO.md` #6，编号不复用。

### 打包

- 建立可复用的打包脚本 `build_beta.py`（工作区根，**不在 git 仓库内**）与四条 PyInstaller 命令，一次产出主程序 `Re工具箱 - v1.4.0b` 与 `srt加前缀`、`srt关键词替换`、`测试插件` 三个插件 exe；`ass转码透明底视频` 按约定不打包（缺 FFmpeg、未完善）。
- 版本：`软件本体/config.json` → `1.4.0b` / `2026-10-22`；插件版本与主程序**解耦**（作者口径：插件有改动才递增，小改第三位、大改第二位）：`srt加前缀` 1.0.1 → **1.1.0**（解析重写 + 计数语义变更）、`srt关键词替换` 1.3.0 → **1.4.0**（新增 repeat + 缓存校验改造）、`测试插件` 1.0.0 → **1.1.0**（按钮由 1 个扩展为「测试弹窗」+「测试报错」，多按钮布局属大改动）。三个 manifest 都没有日期字段，按约定未新增。`ass转码透明底视频` 仍未改动、未打包，保持 1.0.0。
- 版本复核（2026-10-22 打包后，作者指出与旧版差异大）：`测试插件` 上一轮误按「本次无改动」保留 1.0.0，已更正为 **1.1.0**（`软件本体/plugins/测试插件/manifest.json`），并重打单独恢复包 `发布zip/测试插件/测试插件-v1.1.0.zip`（根目录 `manifest.json` + `__init__.exe`）。1.4.0b 测试产物目录内的 manifest 仍为 1.0.0，导入 1.1.0 时走「已安装版本较旧」的升级分支。
- 产物（不入库）：`发布zip/Re工具箱/Re工具箱 - v1.4.0b-测试/`，结构对齐 v1.3.0 解包目录——主程序 12.2 MB、`srt关键词替换/__init__.exe` 35.9 MB、`测试插件/__init__.exe` 11.4 MB、`srt加前缀/自动给srt加前缀.exe` 6.8 MB，另有 `config.json`、`cache/{output,temp}`、`output`、`plugins/*`（manifest + exe，关键词插件附工作副本 `subtitle_rules.json`；不含 pkl）。
- 冷构建耗时（`.venv` Python 3.11.9 + PyInstaller 6.20.0）：主程序 14.7 s、前缀 7.9 s、关键词 38.1 s、测试 12.1 s，合计 72.8 s。
- 命令要点（完整命令见 `AI_CONTEXT.md` §9.3/§9.4）：四个目标统一 `--onefile --windowed`（GUI 子系统；宿主以管道启动时 stdin/stdout/stderr 仍然有效，已用 v1.3.0 参考包与本次产物双向核实，且不会闪控制台）；关键词插件必须 `--add-data default_subtitle_rules.json`（`common.get_path` 默认 `use_program_dir=False`，从 `_MEIPASS` 读默认规则）；主程序保留 `--collect-all tkinterdnd2 --add-data icon.ico`。
- **打包配置的两个坑（本次踩到并已解决）**：① 指定 `--specpath` 后，`--add-data`/`-i` 的相对路径按 spec 目录解析，必须写绝对路径，否则报 `Unable to find '<spec>\icon.ico'`；② 入口文件名是 `__init__.py` 时，PyInstaller **只把父目录**加入模块搜索路径，同目录的 `common`/`build_automaton`/`srt_keyword_editor`/`subtitle_rule_editor`（以及测试插件的 `test`/`test_1`）不会被打入，运行时 `ModuleNotFoundError`——必须显式 `--paths <插件目录>`。
- 验证结论（2026-10-22，干净目录只放 exe + `config.json` + `plugins/`，无源码、无 pkl）：主窗口正常、底部显示 `1.4.0b (2026-10-22)`、按钮按 `debug`(2 个)/`字幕处理`(3 个) 分组；argv 注入两个 SRT 后列表框刷新为 2 项（`console` 日志「更新列表框，当前共 2 个文件」）；点「srt加前缀」→ 多行字幕只在首行加 `文件名：`，再次点击不叠加；点「srt关键词替换」→ `哈哈哈哈哈哈→哈哈哈`、`完了完了完了完了→完了 完了`（repeat 生效）、按文件名统计敏感词并弹「文明小助手」；`subtitle_rules.pkl` 与 `plugin_log/` 均生成在**插件 exe 旁**（#5 的路径策略在打包环境成立）；第二次运行命中缓存不重建，向 `subtitle_rules.json` 追加敏感词后自动失效重建且新词被删；「修改配置」打开的 PyQt5 编辑器能正确读取 exe 旁的规则（Delete/Repeat/Replace 三个根节点）；点「导出」把 `cache/output` 移到 `output/` 并清空列表；同版本插件 zip 触发「已安装版本与当前版本相同，是否重装？」的 Yes/No 询问；测试插件弹窗显示收到的参数 JSON。三个插件 exe 另按 stdin/stdout 协议单独调用，均返回合法 JSON，前缀插件的 `total/processed/skipped/failed` 与 #11 规格一致（4 输入 → 2 处理 / 2 跳过 / 1 失败）。
- 打包警告（均无害，建议后续清理）：主程序 `--hidden-import=tkdnd` 报 `ERROR: Hidden import 'tkdnd' not found`（tkinterdnd2 0.4.3 没有同名 Python 模块，Tcl 库由 `--collect-all tkinterdnd2` 带入，拖放注册正常）；关键词插件报 `WARNING: Hidden import "sip" not found`（PyQt5 hook 的旧式探测，实际使用 `PyQt5.sip`）。
- 未验证（需真机人工）：鼠标真实拖放（TkDND 初始化与 `drop_target_register` 已随窗口创建成功）、测试插件「测试报错」的 `KeyboardInterrupt` 分支、规则编辑器「新建→保存」的实际落盘位置（见 `AI_CONTEXT.md` 附录 A7）。

### 修复

- 检测跨节点重复 `source`（TODO #16）：`_process_node()` 在建立“源词 → 正确词”映射时比对既有映射，冲突则记入新属性 `source_conflicts`（`(源词, 先出现的正确词, 后出现的正确词)`）并在 stderr 打印告警；**覆盖语义保持不变**（仍然后写入者生效），只把“静默冲突”变成“可见冲突”（`软件本体/plugins/srt关键词替换/build_automaton.py`）。
- `common.py` 新增 `find_duplicate_sources(rules)`：递归 `replace` 树（只统计 `enabled` 节点，与主处理器口径一致），返回 `[{"source": ..., "targets": [目标词...]}]`；同一替换项内部重复不算冲突（沿用 `remove_source`/`add_source` 的单项去重）（`软件本体/plugins/srt关键词替换/common.py`）。
- 编辑器三层提示：`SubtitleEditor.collect_sources()` 汇总“源词 → 所属正确词”；新增 `confirm_duplicate_sources()`，`save_to_file()` 写盘前扫描，冲突时列出「· 源词 → A / B」并询问是否继续，选“否”则**不落盘**（返回 `False`）；`ReplaceItemDialog` 新增 `known_sources` 参数，`add_source()` 发现该源词已属于别的替换项时先确认（`软件本体/plugins/srt关键词替换/subtitle_rule_editor.py`）。
- 出厂规则零冲突：`subtitle_rules.json` 与 `default_subtitle_rules.json` 扫描结果均为 0 条，测试固化该结论，避免以后改规则时无意引入冲突。
- 新增 `tests/test_duplicate_sources.py`（11 项）：扫描函数 5 项（无冲突、跨节点冲突、同 item 重复不算、嵌套分组、禁用节点忽略）；处理端 3 项（`source_conflicts` 内容 + stderr 告警 + 后写入者生效、无冲突时为空、两个出厂 JSON 零冲突）；编辑器 3 项（冲突时选“否”不落盘、选“是”正常保存、`collect_sources()` 正确映射）。
- **歧义说明**：TODO 写的是“发现重复则报错并列出冲突节点”。这里没有做成硬性拒绝（直接禁止保存），因为历史规则里可能存在用户刻意保留的“同源词多目标”写法，硬拦会让人无法保存任何改动；最终采用“列出冲突 + 询问，默认不保存”，既暴露问题又不锁死流程。
- 已知局限：`source_conflicts` 只在重建自动机时产生，命中 pkl 缓存时为空（缓存载荷未含该字段，改动需升 `CACHE_SCHEMA_VERSION`）；因此冲突提醒以编辑器侧为准，处理端告警是“重建时才会出现”的兜底。
- 归档自 `TODO.md` #16，编号不复用。

- 重叠匹配改为**长词优先后全局选择**（TODO #15）：`_resolve_overlaps()` 原按 `(start 升序, end 降序)` 排序后线性过滤，只有“同起点”时才成立长词优先——起点更早的短词会先占位，把后面更长的词挤掉（`abcdef` 里 `ab`(0-2) 与 `bcde`(1-5) 只剩 `ab`）。现改为按 `(长度降序, 起点升序)` 的区间调度：先放最长匹配，再放与已选区间不冲突的，最后按起点升序交回调用方；长词优先对任意起点组合都成立，且结果与自动机遍历顺序无关（`软件本体/plugins/srt关键词替换/build_automaton.py`）。
- 等长重叠的平局规则明确为“起点更早者优先”，删除与替换不再可能同时命中同一段文本；被挤掉的重叠短词也不计入敏感词次数。
- 新增 `tests/test_overlap.py`（7 项）：后起长词胜过先起短词、包含关系丢短词、同起点取长词、互不重叠全保留、等长重叠取先起点、`_resolve_overlaps` 正序/逆序输入结果一致、被挤掉的敏感词不计数。
- **歧义说明**：TODO 写的是“区间调度/优先队列等策略选择全局最优匹配，落实长词优先”。严格意义的“全局最优”若按“覆盖字符数最多”定义，会在 `ab` vs `bc`+`de` 这类场景牺牲长词；本实现以“长词优先”为第一目标（按长度降序贪心 + 区间不冲突），与 TODO 标题一致。
- 归档自 `TODO.md` #15，编号不复用。

- 重写拖放路径解析 `parse_dropped_files()`（TODO #22）：原实现只要数据里出现花括号就 `re.findall(r'{([^{}]*)}', data)` 并直接返回，混合格式（`{带空格路径} 普通路径`）会丢掉未包裹的路径；完全无花括号时按空格 `split(' ')`，`C:\my subtitle.srt` 必被拆坏。现在改为单遍扫描：`{...}` 内原样取整段（保留空格、中文、`\n`），`{` 未闭合时退化为普通字符，其余片段按任意空白切分（`\n`、多个空格一并处理），因此花括号分组与换行分隔两种主流格式都覆盖（`软件本体/插件调度主程序.py`）。
- 无花括号且切出多段时，用**磁盘存在性**做保守还原（新增 `_merge_existing_tokens()`）：从最长组合开始试，只有拼起来确实是一个真实存在的路径才合并，否则保持逐段拆分。这样 TkDND 万一没加花括号，带空格的真实路径也能还原，而不会凭猜测把两个文件错误合并。
- 顺带删除因此不再使用的 `import re`。
- 新增 `tests/test_drop_paths.py`（11 项）：花括号单路径/多路径、中文带空格、反斜杠路径、无花括号普通路径、磁盘上真实存在的单个与两个带空格文件、混合格式、换行分隔、空输入与纯空白、未闭合括号的退化行为；`conftest.py` 新增会话级 `main_program_module` fixture（占位标准流 + 临时加入 `软件本体/` 到 `sys.path`，加载后全部还原）。
- 归档自 `TODO.md` #22，编号不复用。


- 修正关键词替换插件的参数日志（TODO #23）：`logger.info("params: {str(params)}")` 少了 f 前缀，落盘的是字面量 `params: {str(params)}`，排查时看不到实际传入的 `output_path` / `pending_file_lists`。改为惰性格式化的 `logger.info("params: %s", params)`，只有真正输出日志时才做 `str()`（`软件本体/plugins/srt关键词替换/srt_keyword_editor.py`）。
- 扫描同插件其余日志调用（`srt_keyword_editor.py`、`subtitle_rule_editor.py`、`__init__.py`、`common.py`）：其余均为 f-string 或 `str(...)` 参数，无同类问题。
- 新增 `tests/test_plugin_logging.py`（2 项）：用 AST 扫描 `软件本体/` 下全部 `.py`，禁止 `logger.<level>("…{…}…")` 这种“纯字面量里带 `{}` 占位符”的写法（f-string 会被解析成 `JoinedStr`，不受影响，`%s` 风格也不受影响）；另单项锁定 `params:` 那条必须把参数作为第二个实参传入。
- 归档自 `TODO.md` #23，编号不复用。

- 导入/重装插件时**自动备份将被覆盖的文件**（TODO #27，2026-10-22 真机测试 T15）：插件 zip 自带 `subtitle_rules.json`，而 `install()` 直接 `rmtree` + `extractall`，升级或同版本重装都会静默覆盖用户调过的规则，此前只能靠 README 提醒"升级前自己备份"。现在 `install()` 的顺序固定为「成员路径校验 → 备份 → `rmtree` → `extractall`」，任一前置步骤失败都不会删除旧目录（`软件本体/load_zip.py`）。
  - `_collect_overwrites()` 用 `ZipInfo.file_size` + CRC32 与磁盘文件比对，**只备份内容确有差异**的同名文件；大小相同再算 CRC32，内容一致直接跳过，避免把没改过的 `__init__.exe` 之类也堆一份。
  - `_backup_overwrites()` 复制到 `cache/plugin_backup/<plugin_id>/<时间戳>/` 并保留相对路径；目录名同秒冲突时追加 `_1`、`_2`。备份目录刻意放在插件目录之外：既不被 `rmtree` 连带删除，也不会被主程序当成插件扫描。备份失败即抛异常，`install()` 返回 `False`，弹窗里附上已生成的备份路径。
  - 顺带修正顺序缺陷：zip 成员路径校验原本在 `rmtree` **之后**，含 `../` 的坏包会先删掉旧目录再报错，现在提到最前面。
  - `import_plugin_list()` 返回值新增 `backups`（`{zip_path: {name, dir, files}}`）；主程序在安装成功后弹一次「插件文件已备份」，列出被覆盖的文件（超过 8 个折叠为"等共 N 个"）与备份目录，批量导入不会逐个刷屏（`软件本体/插件调度主程序.py:620-640`）。
  - 新增 `tests/test_installer_backup.py`（8 项）：覆盖用户改过的规则文件前先备份、内容一致不产生备份、全新安装不备份、同版本重装同样备份、备份失败不删除旧插件、不安全路径的包不删旧插件、批量导入返回备份信息、无覆盖时不返回备份；`pytest tests/` **120 passed / 1 skipped**。
  - 真实包验证（`srt关键词替换-v1.4.0.zip`，含 37 MB `__init__.exe`）：预置 1.3.0 与被改过的规则后导入，备份 `manifest.json` + `subtitle_rules.json` 两份、内容一致的 `__init__.exe` 跳过，备份落在 `cache/plugin_backup/` 下、`plugins/` 外，7 项断言全通过。
  - `README.md`「规则配置」第 3 条与「导入插件」节同步改写：不再要求用户手动复制，改为说明自动备份位置与找回方法；`.gitignore` 新增 `软件本体/cache/plugin_backup/`，避免备份目录被误提交。
- 导入插件前增加**包完整性校验**（TODO #26，2026-10-22 真机测试 T11）：`PluginInstaller.validate_package()` 用 `zipfile.namelist()` 静态检查 manifest 里每个按钮的 `executable` 能否在包内解析到（原样 → 去扩展名 + `.py` → + `.exe`，与主程序 `_resolve_executable` 同源），失败即返回 `False`，原因写入 `rejection_reason`；`check_version_and_install()` 在版本比较之前调用它。修复前 `install()` 先 `rmtree` 旧目录再 `extractall`，导入一个按钮指向不存在文件的 zip 会**先删掉正常插件、再装上一个加载失败的空壳**，主程序扫描时才整插件跳过告警；现在旧目录一个字节都不动。同时拦下多按钮缺 `label`/`executable`、`buttons` 为空、exe 只在压缩包子目录里等非法包（`软件本体/load_zip.py`）。新增 `tests/test_installer_package_check.py`（12 项，含“坏包不得删除已安装插件”核心回归）；`pytest tests/` 112 passed / 1 skipped。配套调整导入失败提示：原来坏包会**连弹两次**（“插件包不完整”详情 + “以下文件未导入”汇总），现在单包不弹窗、原因经 `failed_reasons` 汇总到主程序的一次弹窗里，标题固定为“导入插件失败”，正文在文件路径下缩进显示「原因：…」；`validate_package(show_error=False)` 与 `check_version_and_install(show_error=False)` 保留默认弹窗行为，直接调用时不受影响（`软件本体/load_zip.py`、`软件本体/插件调度主程序.py:601-611`）。源码模式真机复验：坏包只弹一次、旧插件字节未变，好包仍可正常升级。
- 插件安装前校验 manifest 的 `plugin_id`（未提供时回退 `name`）：仅允许字母、数字、下划线、连字符与中文，拒绝空值、`.`/`..`、路径分隔符、盘符与绝对路径，校验失败时中止安装并提示（`软件本体/load_zip.py`）。
- 用 `os.path.realpath` + `os.path.commonpath` 校验安装目标必须位于 `plugins/` 下（Windows 经 `normcase` 忽略大小写），并在 `shutil.rmtree` 前再次校验；原有 zip 成员路径检查保持不变（`软件本体/load_zip.py`）。
- 验证结论（2026-10-22，临时无头脚本 + 模拟弹窗）：正常 zip 可安装；`../x`、`/abs`、`..\x`、`C:\x`、空值与非法字符均被拒绝，已有插件目录及 `plugins/` 外哨兵目录未被删除；越界目标路径被拒绝。符号链接场景因 Windows 权限不足未执行（SKIP）。
- `install()` 现在返回真实安装结果：成功 `True`；路径校验、旧目录清理、解压等任一环节异常返回 `False`，错误弹窗保留；`load_zip_json()` 同时覆盖非 zip、缺失 `manifest.json` 等打开/解析失败（`软件本体/load_zip.py`）。
- `check_version_and_install()` 改为三态返回：`True`=安装成功、`False`=安装失败、`None`=用户取消重装；取消不再计为失败（`软件本体/load_zip.py`）。
- `import_plugin_list()` 按单项结果归入 `success_list` / `failed_files` / `skipped_files`；主程序现有逻辑无需改动，仍只从 `FILE_LIST` 移除成功项，失败项保留并弹窗，取消项保留且不报错（`软件本体/load_zip.py`）。
- 验证结论（2026-10-22，临时无头脚本 + 模拟弹窗）：正常 zip 成功；非 zip、缺 `manifest.json`、缺 `name`/`version`、含越界成员 zip、模拟清理失败均进入 `failed_files` 且不删除既有目录；同版本/低版本取消重装进入 `skipped_files`，不计失败；混合导入三条列表均正确。真实弹窗点击当时尚未手工验证，脚本以模拟 `No`/`Yes` 覆盖返回语义（2026-10-22 已由作者真机手工冒烟补齐，见「测试」节）。
- pkl 缓存校验改用规则 JSON 的内容哈希：`json.dumps(json.loads(content), sort_keys=True, ensure_ascii=False)` 规范化后取 SHA-256，纯缩进/键顺序变化不触发重建；新增 `CACHE_SCHEMA_VERSION = 2` 标识载荷结构，载荷写入 `json_content_hash` 与 `schema_version`（`软件本体/plugins/srt关键词替换/build_automaton.py`）。
- `_load_from_cache()` 改为完整校验链：pkl 缺失、`pickle.load` 异常、载荷非 dict、schema 版本不一致、内容哈希不一致、必要字段缺失均返回 `None` 并自动重建；`force_rebuild=True` 跳过校验强制重建并写回新哈希。原 `_is_cache_valid()`（仅按 mtime 判断）已移除。
- `load_rules()` 在缓存校验前先调用 `_get_json()` 重新读取当前 JSON，保证哈希基于实际生效的规则文件（含回退写入的默认配置）；重建前清空旧解析状态，避免复用实例时残留旧规则。
- 确认 `subtitle_rules.pkl` 已不受版本控制（自提交 `9cade55` 起移出索引），`.gitignore` 已含 `*.pkl`；工作区 pkl 保留，本任务无需再执行 `git rm --cached`。
- 补充 AI_CONTEXT 维护规则：§10.5 新增「AI_CONTEXT §11 修复标注」，§11 已修复条目在问题描述末尾括注日期，不改写原诊断；本次已为 #1、#2、#3、#5 添加标注（`docs/AI_CONTEXT.md`）。
- 验证结论（2026-10-22，临时无头脚本，45 项全通过）：覆盖冷启动生成 pkl、mtime 反向仍命中、JSON 内容变化失效、仅格式化命中、schema 版本变化失效、损坏/非字典/旧字段缺失 pkl 自动重建、`force_rebuild` 跳过校验并更新哈希、`_load_from_cache()` 返回值；真实默认规则在构建/命中/失效三条路径下 repeat 行为与缓存状态一致。未走主程序与规则编辑器 GUI，已记入 TODO 长期测试补强。
- 归档自 `TODO.md` #1、#2、#5，编号不复用。

**#25 无插件变动时不再重建主窗口（`软件本体/插件调度主程序.py`）**

- 调查结论一：`FILE_LIST` 在重建窗口时**不会丢失**。它是模块级全局变量（`62`），`init_program()` 只声明 `global FILE_LIST`（`425`）并追加命令行参数、刷新列表框，从不 clear 或重置；实测成功/失败/取消/无变动四类场景下列表项均完整保留，成功场景仅移除导入成功的 zip。
- 调查结论二：重建会**连带删除用户已处理的中间产物**。`init_program()` 原本无条件 `clear_folder(cache/output)`，而插件运行成功后主程序用 `completed_output_lists` 把 `FILE_LIST` 覆写为 `cache/output` 下的路径（`357`），因此失败或取消重装这类“插件根本没变”的操作一旦触发重建，就会删掉链式处理结果并把列表留成悬空路径。
- 调查结论三（另记）：`import_plugin_list(FILE_LIST)` 传入整个列表且不按扩展名过滤（`534`），列表里混有 SRT 时这些字幕会被计入 `failed_files` 并出现在“以下文件未导入”弹窗中。本次未改动该行为（`TODO.md` 手工冒烟项仍按“非 zip 视作失败”验收），如需过滤应另开条目。
- 改动一（`534-562`）：`import_plugin` 分支改为**仅当 `success_list` 非空时**才移除 zip、销毁 Tk 根并重建窗口；失败、取消重装与无变动场景只弹窗（仅失败）并打印“本次导入未安装任何插件，窗口保持不变”，随后 `continue`。`load_zip.py` 的返回值语义未改动。
- 改动二（`423-441`）：`init_program()` 增加 `clear_cache=True` 参数，缓存清理改为受其控制；“导入插件”的重建路径传 `clear_cache=False`（`557`），“重启刷新”仍按重启语义清空缓存（`521-532`），首次启动行为不变。同步修正返回值说明为 5 元组。
- 验证结论（2026-10-22，隔离副本 + 桩化 PySimpleGUI/TkDND 驱动 `main()` 事件循环，未触碰仓库目录）：成功导入 → 重建 1 次、zip 移除、`cache/output` 产物存活；失败导入 → **不重建**、弹错误框、列表不变、产物存活；取消重装 → **不重建**、无弹窗、列表不变、产物存活；无变动 → **不重建**；列表为链式产物时成功与取消两条路径产物均存活。`pytest tests/` 仍为 59 passed / 1 skipped，`py_compile` 通过。本次改动行为以隔离脚本验证；§9.6「插件导入」场景随后于同日由作者真机手工冒烟通过（见「测试」节），但「无变动」边界与“窗口未重建”是否被显式观察到未单独记录。
- 归档自 `TODO.md` #25（手工冒烟时新增），编号不复用。

**#11 SRT 前缀解析、幂等与计数（`软件本体/plugins/srt加前缀/自动给srt加前缀.py`）**

- 解析改为**按空行分块**，替换原 `range(2, len(lines), 4)` 的四行假设：连续空行归一为一个分隔块；块内用正则 `TIME_LINE_RE` 定位时间轴行（毫秒分隔符 `,` 与 `.` 都接受，序号行可缺失），只在**时间轴下一行**即第一个文本行加前缀，多行文本的后续行原样保留。
- 幂等判断：只有当第一个文本行以 `<输入文件 basename（不含扩展名）>：` 开头时才跳过该块；其他 `XXX：` 前缀（如手写 `主持人：`）视为无前缀，照常叠加成 `ep01：主持人：…`。判断只看首个文本行，块内其他行不参与。
- 编码与行尾：读 `utf-8-sig`（自动去 BOM），写 `utf-8` 无 BOM、`newline='\n'` 固定行尾；输入接受 `\n` 与 `\r\n`。
- 计数语义：`processed` 由“输入文件数”改为**成功写入 `cache/output` 的文件数**（幂等跳过也计入，因为文件已正确落地）；新增 `total`（输入总数）、`skipped`（非 `.srt` + 幂等跳过）、`failed`（路径不存在/不可读、读取/写入异常、无有效字幕块）。`status` 与 `completed_output_lists` 语义不变。注：幂等跳过同时计入 `processed` 与 `skipped`，故 `total = processed + failed`，而 `skipped` 与 `processed` 有重叠。
- 边界口径：块内没有时间轴行的块**原样保留、不加前缀**，只在 stderr 提示；空文件、只有空白、完全没有时间轴行时抛 `SrtFormatError`，文件计入 `failed` 且不写输出。幂等跳过仍写一份原样副本到 `cache/output`，避免 `FILE_LIST` 被替换后丢文件。
- 新增 `tests/test_srt_prefix.py`（25 项）：块解析单块/多块/多行文本/缺序号/`.` 分隔/CRLF/BOM/连续空行/块尾无空行/非字幕块保留，幂等命中与不命中、按首行判断、混合块只补未带前缀的块，空文件/纯空白/无时间轴三类失败，`main` 端到端的混合输入计数、全成功、全失败、幂等副本落地、仅非 SRT，以及路径不存在/同名目录/不存在的非 SRT 三项归类；输出内容均逐行比对，且全部写在 `tmp_path`。
- 验证结论（2026-10-22）：`pytest tests/test_srt_prefix.py -v` 25 passed；全量 `pytest tests/` 为 **84 passed / 1 skipped**（原 60 项 + 新增 25 项，SKIP 仍为目录不可写）。另按插件真实协议（子进程 stdin/stdout）做了一次冒烟：标准 SRT、多行 SRT、非 SRT、空文件混合输入得到 `total=4 / processed=2 / skipped=1 / failed=1`，多行只给首行加前缀；随后把 `cache/output` 产物作为输入再跑两次，`skipped=2`、前缀出现次数不增加、内容三次一致，幂等成立。未在真机 GUI 上点按钮（§9.6「前缀」项仍需人工确认）。
- 未改动：manifest、`cache/output/<basename>` 同名覆盖行为（属 #12）、主程序与其他插件。
- 归档自 `TODO.md` #11，编号不复用。

**#11 后续修正：不可处理的 `.srt` 路径改计失败（同日，作者口径确认）**

- `main()` 的文件过滤拆成两步：先按扩展名分流（非 `.srt` → `skipped`，本来就不归这个插件管），再单独判断 `os.path.isfile`；扩展名是 `.srt` 但路径不存在、指向目录或不可读时计入 `failed`，并打印「文件不存在或不可读」。原实现把两个条件合并在 `not (isfile and endswith)` 里，导致不存在的 `.srt` 被算成“跳过”，与“不可处理不能计跳过”的口径冲突。
- `tests/test_srt_prefix.py` 相应增加 3 项：路径不存在计 `failed`、同名目录冒充 `.srt` 计 `failed`、不存在的非 `.srt` 仍计 `skipped`（非 SRT 的分类不受路径是否存在影响）。
- 验证结论（2026-10-22）：`pytest tests/test_srt_prefix.py -q` 25 passed；全量 `pytest tests/` 为 **84 passed / 1 skipped**；`py_compile` 通过。

**#13 容错损坏的插件 manifest（同时清掉 #14 的重复扫描）**

- `scan_plugins()` 拆成五个函数：`_load_manifest()`（读取 + 粗校验）、`_resolve_executable()`（原值 → `.py` → `.exe` 的解析）、`_build_buttons()`（两种 manifest 格式转按钮）、`scan_plugins()`、`warn_broken_plugins()`（汇总告警）。返回值从 `buttons` 变为 `(buttons, failures)`，`failures` 是 `[(插件目录名, 原因)]`。
- 容错范围（单个插件出问题只跳过它自己，其余照常加载）：JSON 语法错误、顶层不是对象、缺 `name`、既无 `executable` 也无 `buttons`、`buttons` 不是数组/为空/含非对象条目、按钮缺 `label` 或 `executable`、声明的可执行文件找不到。`manifest.json` 根本不存在的目录仍按原样**静默忽略**（那是“不是插件”，不是“插件坏了”）。
- 告警方式：`init_program()` 建好窗口、刷新完列表后调用 `warn_broken_plugins()`——逐条打印“⚠️ 插件加载失败，已跳过：<目录> —— <原因>”进日志面板，然后**只弹一次** `sg.popup`，标题“插件加载告警”，正文按 `目录：原因` 列全。不再每个失败插件弹一个窗。
- **同时清理 #14**：`init_program()` 里重复的两次 `scan_plugins()` 合并为一次（原先第一次的返回值从未被使用），因此告警天然只出现一次；`#14` 两条待办（删除重复调用、确认按钮数与分组不变）均已满足并归档。
- 行为变化（有意为之，记录在案）：① 多按钮插件里**任一**按钮的可执行文件缺失，整个插件跳过（旧行为只跳过该按钮并 print，会让人误以为插件正常）；② `name` 变为强制字段（旧代码在旧格式下会用目录名兜底），与 `load_zip.py` 安装时的要求对齐。
- 新增 `tests/test_scan_plugins.py`（16 项）：`_load_manifest` 的正常/语法错误/缺 `name`/缺 `executable` 与 `buttons`/非对象/`buttons` 非数组，`_resolve_executable` 的扩展名补全，`scan_plugins` 的正常、单坏、可执行文件缺失、按钮级缺失、混合 2 正常 + 3 坏、无 manifest 目录静默、目录不存在，以及 `warn_broken_plugins` 只弹一次窗且日志逐条。用 `FakeSG` 桩顶掉 PySimpleGUI/tkinterdnd2 后按路径加载主程序模块。
- 验证结论（2026-10-22）：`pytest tests/test_scan_plugins.py -q` 16 passed；全量 `pytest tests/` 为 **100 passed / 1 skipped**；`py_compile` 通过。另在临时目录搭了“1 正常 + JSON 坏 + 可执行文件缺”的 plugins 目录，桩化 GUI 后跑真实 `init_program()`：正常插件 1 个按钮、窗口创建 1 次、弹窗 1 次且正文列出两条、日志两行；再跑一次 `init_program(clear_cache=False)` 复现“导入插件后重建”，同样只弹一次。用真实 `软件本体/plugins` 扫描得 6 个按钮、0 失败，与改动前一致。**未在真机上点按钮验证弹窗外观**（§9.6「插件容错」项仍需人工确认）。

### 说明

- 2026-10-22 完成 1.4.0b beta 打包与干净环境验证，详见上文「打包」节。遗留：① `打包exe指令.txt` 仍是 v1.1.0 时代的单条主程序命令，本次按约束未改，建议按 §9.3/§9.4 回填四条命令或改为指向 `build_beta.py`；② 打包暴露的代码问题（规则编辑器「新建」用 `__file__` 定位保存路径、前缀插件未给 stderr 做 `None` 保护、测试插件的 `test` 模块与标准库同名）本次只记录未修，处理意见见任务汇报与 `AI_CONTEXT.md` §11。

- 2026-10-22 完成 #13（容错损坏的插件 manifest）并顺带清掉 #14（重复扫描），详见上文「修复」节末段。遗留：① 告警弹窗在“导入插件后重建窗口”时会**再弹一次**（同一批失败项每次都汇总提示，未做“本会话已提示过”的去重）；② 多按钮插件只要一个按钮的 `executable` 缺失就整插件跳过，若将来出现“按钮可选”的需求需再调整；③ `name` 改为强制字段，手工拷贝进 `plugins/` 且没有 `name` 的老插件会被跳过（`load_zip.py` 安装的插件都带 `name`，正常不会遇到）。
- TODO 初始化后已完成 #1、#2、#3、#5（插件安装路径穿越、安装失败仍报成功、repeat 规则、pkl 缓存校验与入库）；其余 20 项待办不变。
- 2026-10-22 补充 pytest 测试框架与 5 项回归固化（见上文「测试」节）；同日作者在真机完成 3 项 GUI/主程序手工冒烟并全部通过，「可选增强 / 测试补强」整节已归档，`TODO.md` 该分类清空。
- 2026-10-22 完成手工冒烟新增的 #25（无插件变动时不再重建主窗口），详见上文「修复」节末段。遗留：“重启刷新”按钮仍会清空 `cache/output`（按重启语义保留现状）；`import_plugin_list` 不按扩展名过滤、SRT 会被计入失败列表，未在本次处理。
- 2026-10-22 完成 #6（正式依赖清单），详见上文「变更」节。遗留：间接依赖未锁定，干净环境实测 `PyQt5_sip` 与 `pyinstaller-hooks-contrib` 会比现有 `.venv` 更新一档；`.venv/old_requirements.txt` 按约定保留未动，已由 `requirements.txt` 取代；README 的规则/插件说明段落属 #7，本次未动。
- 2026-10-22 完成 #7（README 与实现对齐），详见上文「文档」节。新版 README 依据源码静态核对重写，未重跑 GUI 手工冒烟；ASS 插件章节按"实验性 + 需自备 FFmpeg"标注，FFmpeg 分发策略仍待 #8 决定。
- 2026-10-22 完成 #11（SRT 前缀解析、幂等与计数），详见上文「修复」节末段。遗留：①`{\an8}` 之类**行首样式标签会被前缀挡在标签前**（`ep01：{\an8}…`），本次按确认规格未做标签特殊处理；**作者已明确决定不修**（2026-10-22）：本工具定位是精修字幕之前的批量减负环节，产物后续还要过人工精校与样式特效，此场景触发概率低、命中行数少，手工调整即可，不值得为它增加标签解析复杂度；②不存在或不可读的 `.srt` 路径**已修正为计入 `failed`**（见同上「#11 后续修正」段）；③非 UTF-8（如 GBK）字幕解码失败会计入 `failed`、该文件不产出，**作者决定不做编码回退**（2026-10-22：实际字幕源绝大多数是 UTF-8，遇到时先自行转码即可）；④`processed` 与 `skipped` 在幂等场景重叠，`total = processed + failed` 而非三者相加。
- 2026-10-22 记录项目定位：本工具是**精修字幕之前的批处理环节**，产物交给人工精校与样式特效，故取舍上优先保证结构与文件不丢，而非逐字元精确（`AI_CONTEXT.md` §1.1、`README.md` 开头）。据此把上条 ①「行首样式标签被前缀挡在前面」正式列为**不修**，并在 §5.6 同步注明理由。
