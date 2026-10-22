# 待办事项清单

> 只记录**未完成**的任务；已完成的历史变更见 `CHANGELOG.md`。
> 大项全部完成后整节移入 CHANGELOG；大项进行中时，已完成的子项可打勾留痕（`- [x]`）。
> 按优先级排序，完成后请移入 `CHANGELOG.md`。
> **最后更新**：2026-10-22

**编号规则**：
- 编号一旦分配即永久占用，归档、完成、删除均不回收、不复用。
- 「当前最大编号」记录历史峰值，新任务一律取该值 +1。
- 现存编号允许跳号，不要重排。
- 当前最大编号：25。

> 来源：`AI_CONTEXT.md` §11 共 24 行（高 2 / 中 10 / 低 12），编号 1–24 与表格行一一对应；优先级按该节级别映射。
> 归档：#1、#2、#3、#5 已于 2026-10-22 完成并移入 `CHANGELOG.md`；#25（手工冒烟新增）同日完成并移入。编号均不复用。

---

## 🟡 中优先级

### 4. 处理 regex 节点空操作

**背景**：`regex` 分支为空，规则中的 regex 配置不会生效且没有提示（`AI_CONTEXT.md` §11「`regex` 节点空操作」）。建议按 §11.1 第 2 步处理。

**待办**：
- [ ] 决定实现 regex 匹配，或从 schema、编辑器与默认规则中移除该类型
- [ ] 若实现：在 `_process_node` 增加 regex 解析并接入处理链路，补充非法正则的错误提示
- [ ] 若移除：在编辑器加载/保存时拒绝或迁移 `type: regex` 节点

**关联文件**：
- `软件本体/plugins/srt关键词替换/build_automaton.py`
- `软件本体/plugins/srt关键词替换/subtitle_rule_editor.py`

---

### 6. 建立正式依赖清单

**背景**：仓库没有 `requirements.txt` / `pyproject.toml`，`.venv/old_requirements.txt` 缺少 PyQt5 且含未使用包，新环境难以复现（`AI_CONTEXT.md` §11「无正式依赖清单」）。建议按 §11.1 第 3 步处理。

**待办**：
- [ ] 新增根级 `requirements.txt` 或 `pyproject.toml`，按 runtime / dev / build 分组并固定版本
- [ ] 补入 PyQt5，确认无隐式引用后移除 `pysub-parser`、`Unidecode`
- [ ] 在 README / 构建说明中给出可复现安装命令，并按 §9.6「启动」项验证

**关联文件**：
- `.venv/old_requirements.txt`
- `软件本体/plugins/srt关键词替换/subtitle_rule_editor.py`
- `打包exe指令.txt`

---

### 7. 更新 README 与实现对齐

**背景**：README 称 `config.json` 是删改词配置、格式错误会被覆盖；实际规则在 `subtitle_rules.json`，`config.json` 只存版本/作者（`AI_CONTEXT.md` §11「README 与当前实现不一致」）。建议按 §11.1 第 4 步处理。

**待办**：
- [ ] 改写规则说明：以 `subtitle_rules.json` 与规则编辑器为准，注明 `config.json` 仅存版本/作者
- [ ] 补全规则编辑器、导入/导出插件、ASS 插件与导出目录的说明
- [ ] 按 §9.6 冒烟清单逐项核对 README 描述与实际行为

**关联文件**：
- `Editing-tools-related-to-SRT-subtitles/README.md`
- `软件本体/config.json`
- `软件本体/plugins/srt关键词替换/build_automaton.py`

---

### 8. 补齐 ASS 插件 FFmpeg 依赖

**背景**：代码要求 `ffmpeg/bin/ffmpeg.exe`，仓库该目录为空，发布包中也未发现 FFmpeg，源码环境下 ASS 功能不可用（`AI_CONTEXT.md` §11「ASS 插件缺少 FFmpeg」）。

**待办**：
- [ ] 确定 FFmpeg 分发策略：随包附带可执行文件，或在文档中声明外部安装路径
- [ ] 增加启动前检测与可读错误提示，替代直接抛 `FileNotFoundError`
- [ ] 准备 FFmpeg 后按 §9.6「ASS」项验证 `test.ass` 生成透明 `.mov`

**关联文件**：
- `软件本体/plugins/ass转码透明底视频/ass转码透明底视频.py`
- `软件本体/plugins/ass转码透明底视频/ffmpeg/bin/`

---

### 9. 确认 ASS 插件发布策略

**背景**：现有 `v1.x/` 与 `发布zip/` 清单均无 ASS 插件，是否对外发布、通过何种渠道分发仍**未确认**（`AI_CONTEXT.md` §11「ASS 插件未出现在现有发布产物」）。

**待办**：
- [ ] 与作者确认 ASS 插件是否发布、目标版本与分发渠道
- [ ] 若发布：纳入发布包清单和版本号管理，补齐 manifest 与安装包
- [ ] 若不发布：在 README 标注为实验/内部插件，避免用户误装

**关联文件**：
- `软件本体/plugins/ass转码透明底视频/manifest.json`
- `发布zip/`

---

### 10. 插件执行改为非阻塞

**背景**：`proc.communicate()` 在 UI 事件循环内同步等待，无超时、取消与进度，ASS 渲染或大批量 SRT 会让窗口“无响应”（`AI_CONTEXT.md` §11「主界面在插件运行期间阻塞」）。建议按 §11.1 第 5 步处理。

**待办**：
- [ ] 将插件调用移出 UI 事件循环（线程/进程 + 事件回传），保持现有 stdin/stdout JSON 协议不变
- [ ] 增加忙碌状态、超时与取消入口，避免窗口假死
- [ ] 按 §9.6 的 ASS / 批量 SRT 场景验证 UI 响应与结果链

**关联文件**：
- `软件本体/插件调度主程序.py`

---

### 11. 修正 SRT 前缀解析与计数

**背景**：前缀插件按 `range(2, len(lines), 4)` 假设固定四行结构，多行字幕会错位；重复运行会叠加前缀；`processed` 统计的是输入数而非成功数（`AI_CONTEXT.md` §11「SRT 前缀插件假设固定四行结构」）。

**待办**：
- [ ] 改为按空行分块解析 SRT，基于序号/时间轴定位文本块，兼容多行字幕与样式标签
- [ ] 增加幂等判断：已带 `文件名：` 前缀时跳过或替换，不重复叠加
- [ ] `processed` 改为成功处理数，并用多行字幕验证（参考 §9.6「前缀」，承接 §11.1 第 6 步）

**关联文件**：
- `软件本体/plugins/srt加前缀/自动给srt加前缀.py`

---

### 12. 避免缓存同名文件覆盖

**背景**：两个插件都写 `cache/output/<basename>`，不同目录的同名 SRT 会互相覆盖，批量处理多目录时可能丢结果（`AI_CONTEXT.md` §11「同名文件在缓存中互相覆盖」）。

**待办**：
- [ ] 设计缓存命名规则：保留相对路径、加哈希前缀或按批次建子目录
- [ ] 同步修改两个插件的输出路径与主程序 `move_all_files` 的导出映射
- [ ] 批量加入同名 SRT 验证链式处理与导出结果不互相覆盖

**关联文件**：
- `软件本体/plugins/srt关键词替换/srt_keyword_editor.py`
- `软件本体/plugins/srt加前缀/自动给srt加前缀.py`
- `软件本体/插件调度主程序.py`

---

## 🟢 低优先级

### 13. 容错损坏的插件 manifest

**背景**：`scan_plugins` 直接 `json.load`，没有 try/except，一个 manifest 写错就会阻止整个工具启动（`AI_CONTEXT.md` §11「损坏的 manifest 会让主程序启动崩溃」）。

**待办**：
- [ ] 为每个 manifest 的读取与校验加 try/except，失败时跳过并提示插件名与原因
- [ ] 在 `init_program` 汇总扫描告警，不因单插件失败中断启动
- [ ] 用故意损坏的 manifest 按 §9.6「启动」「插件发现」项验证

**关联文件**：
- `软件本体/插件调度主程序.py`

---

### 14. 移除重复的插件扫描

**背景**：`init_program` 内 `scan_plugins()` 被调用两次，多一次扫描，当前无功能影响（`AI_CONTEXT.md` §11「`scan_plugins()` 重复调用」）。

**待办**：
- [ ] 删除 `init_program` 中重复的 `scan_plugins()` 调用，保留一次
- [ ] 按 §9.6「插件发现」项确认按钮数量与分组不变

**关联文件**：
- `软件本体/插件调度主程序.py`

---

### 15. 修正重叠匹配选择策略

**背景**：匹配排序后线性过滤，最长匹配只在同起点时成立，起点更早的短词可能先占位（`AI_CONTEXT.md` §11「最长匹配只在同起点时成立」）。

**待办**：
- [ ] 用区间调度/优先队列等策略选择全局最优匹配，落实长词优先
- [ ] 为重叠、包含、同起点场景补单元测试（承接 §11.1 第 6 步）
- [ ] 用固定样例核对删除/替换输出与敏感词计数

**关联文件**：
- `软件本体/plugins/srt关键词替换/build_automaton.py`

---

### 16. 检测跨节点重复 source

**背景**：不同节点的相同 `source` 后者覆盖前者，编辑器只防单个 item 内重复，规则冲突不易发现（`AI_CONTEXT.md` §11「不同节点的相同 `source` 后者覆盖前者」）。

**待办**：
- [ ] 保存/构建规则时扫描全局 source，发现重复则报错并列出冲突节点
- [ ] 在编辑器添加 source 时提示是否已存在于其他节点
- [ ] 为跨节点重复 source 场景补规则校验测试

**关联文件**：
- `软件本体/plugins/srt关键词替换/build_automaton.py`
- `软件本体/plugins/srt关键词替换/subtitle_rule_editor.py`

---

### 17. 修复打包后新建规则路径

**背景**：`new_file()` 用 `os.path.dirname(__file__)` 生成工作文件路径，单文件 exe 下 `__file__` 位于 `_MEIPASS`，可能无法保存；该问题**未在打包环境验证**（`AI_CONTEXT.md` §11「打包后“新建”规则文件路径可能指向只读临时目录」）。

**待办**：
- [ ] 改用 `get_path(use_program_dir=True)` 或显式程序目录生成工作文件路径
- [ ] 打包后实测“新建 → 保存 → 重新加载”，记录结论（参考 §9.6「规则编辑器」）
- [ ] 若目标不可写，给出只读错误提示与“另存为”引导

**关联文件**：
- `软件本体/plugins/srt关键词替换/subtitle_rule_editor.py`
- `软件本体/plugins/srt关键词替换/common.py`

---

### 18. 统一规则编辑器退出协议

**背景**：编辑器用 `sys.exit` 退出，`__init__.py` 的 `except Exception` 捕获不到 `SystemExit`，主程序可能收不到 JSON（`AI_CONTEXT.md` §11「规则编辑器退出用 `sys.exit`，`__init__.py` 的 `except Exception` 捕获不到 `SystemExit`」）。

**待办**：
- [ ] 编辑器关闭时按插件协议输出统一 JSON，再正常退出（或把结果交回 `event_*` 统一输出）
- [ ] 调整 `__init__.py` 的事件分发/异常处理，明确捕获 `SystemExit` 或避免在子函数直接退出
- [ ] 验证编辑器关闭后主程序能正常收尾且不报错

**关联文件**：
- `软件本体/plugins/srt关键词替换/subtitle_rule_editor.py`
- `软件本体/plugins/srt关键词替换/__init__.py`

---

### 19. 清理失效的安装测试入口

**背景**：`test_plugins_list()` 循环结束后只安装最后一个插件，空列表时 `plugin_zip` 未定义，且主程序未使用该函数（`AI_CONTEXT.md` §11「`test_plugins_list()` 是失效/有缺陷的测试入口」）。

**待办**：
- [ ] 删除该死代码，或改写为遍历全部插件并正确处理空列表的正式测试入口
- [ ] 若保留，补空列表、多插件、失败中断三种验证

**关联文件**：
- `软件本体/load_zip.py`

---

### 20. 规范测试插件异常模拟

**背景**：测试插件用 `raise KeyboardInterrupt` 模拟错误，它不是 `Exception`，会走 Python 默认 traceback 而非统一异常处理（`AI_CONTEXT.md` §11「测试插件用 `raise KeyboardInterrupt` 模拟错误」）。

**待办**：
- [ ] 改为 `raise RuntimeError` 或普通 `Exception`，验证统一错误 JSON 与 stderr 输出
- [ ] 保留“测试报错”按钮用途，并标注仅用于调试
- [ ] 确认主程序错误弹窗路径符合预期

**关联文件**：
- `软件本体/plugins/测试插件/__init__.py`

---

### 21. 清理仓库运行产物

**背景**：`cache/temp/ffmpeg-*.log` 与 `subtitle_rules.pkl` 被跟踪，`plugin_log/` 未跟踪且无 `.gitignore`，运行产物可能被误提交（`AI_CONTEXT.md` §11「仓库卫生」）。建议按 §11.1 第 3 步处理，与 #5 联动。

**待办**：
- [ ] 新增 `.gitignore`，忽略 `cache/`、`temp/`、`plugin_log/`、`*.pkl`、`ffmpeg-*.log` 等运行产物
- [ ] 从版本控制移除已跟踪的 `subtitle_rules.pkl` 与 `cache/temp/ffmpeg-*.log`（保留工作区文件）
- [ ] 明确 `plugin_log/` 的保留策略与是否入库（见 `AI_CONTEXT.md` 附录 A10）

**关联文件**：
- `软件本体/plugins/srt关键词替换/subtitle_rules.pkl`
- `软件本体/cache/temp/ffmpeg-*.log`
- `软件本体/plugins/srt关键词替换/plugin_log/`

---

### 22. 修正拖放路径空格拆分

**背景**：拖放路径解析在无花括号时按空格拆分，某些来源的含空格路径会被拆坏；TkDND 通常会给含空格路径加花括号，风险有限（`AI_CONTEXT.md` §11「拖放路径解析在无花括号时按空格拆分」）。

**待办**：
- [ ] 优先按 TkDND 花括号分组解析，仅在无花括号时使用更保守的路径识别
- [ ] 覆盖含空格、中文、多文件、花括号包裹四类路径测试
- [ ] 按 §9.6「拖拽」项验证

**关联文件**：
- `软件本体/插件调度主程序.py`

---

### 23. 修复日志缺失 f-string

**背景**：`logger.info("params: {str(params)}")` 缺少 f 前缀，日志记录的是字面量而不是参数，影响排查（`AI_CONTEXT.md` §11「日志语句缺少 f-string」）。

**待办**：
- [ ] 改为 `logger.info("params: %s", params)` 或 f-string
- [ ] 扫描同插件其他日志占位符，确保参数被正确渲染

**关联文件**：
- `软件本体/plugins/srt关键词替换/srt_keyword_editor.py`

---

### 24. 调整 FFmpeg 启动与日志

**背景**：FFmpeg 以 `CREATE_NEW_CONSOLE` 启动并带 `-report`，可能闪控制台，并在 `cache/temp` 留下 ffmpeg 日志（`AI_CONTEXT.md` §11「FFmpeg 以 `CREATE_NEW_CONSOLE` 启动并带 `-report`」）。

**待办**：
- [ ] Windows 下改用 `CREATE_NO_WINDOW`，避免弹出控制台
- [ ] 去掉 `-report`，或改为受控临时文件/按需开启
- [ ] 按 §9.6「ASS」项验证成功/失败路径均无残留日志

**关联文件**：
- `软件本体/plugins/ass转码透明底视频/ass转码透明底视频.py`

---

## 💡 可选增强（长期）

> 本分类暂不编号，转正后按编号规则分配。

### 测试补强

> 覆盖已修改但尚未完整验证的场景，完成后转正编号或直接归档。
> **2026-10-22**：其中 5 项可自动化条目已固化为 `tests/` 下的 pytest 用例并归档（见 `CHANGELOG.md` 同日「测试」节）；剩余 3 项为 GUI/主程序真实链路手工冒烟，仍需人工在真机执行。

- [ ] **插件导入 GUI 手工冒烟**：通过主程序“导入插件”验证正常 zip、非 zip/缺 manifest 失败、同版本与低版本重装询问的“取消/确认”，确认失败项保留在 `FILE_LIST` 并弹窗、取消项保留且不报错（来源：#1、#2；真实弹窗交互尚未手工验证）。
- [x] **固化插件安装器回归测试**（已完成 2026-10-22，见 `CHANGELOG.md`；落在 `tests/test_installer.py`）：将 #1/#2 的临时无头脚本转为可重复执行的测试，覆盖 `plugin_id` 越界、安装目标越界、非 zip/缺 manifest、`install()` 成功/失败/取消三态与混合导入列表（来源：#1、#2；临时脚本已删除）。
- [x] **补测符号链接/目录联接越界**（已完成 2026-10-22，见 `CHANGELOG.md`；`tests/test_installer.py` 用 `mklink /J` 真实执行，未跳过）：在具备创建符号链接权限的 Windows 环境验证 `realpath` 拦截，并覆盖大小写路径与损坏链接（来源：#1；临时测试因 WinError 1314 跳过）。
- [x] **补测真实清理/解压失败**（已完成 2026-10-22，见 `CHANGELOG.md`；落在 `tests/test_installer_failures.py`）：用只读或占用目录触发 `rmtree` 失败、用损坏 zip 或权限不足触发解压失败，确认 `install()` 返回 `False`、弹窗正常且旧目录状态符合预期（来源：#2；此前仅用 monkeypatch 与越界成员间接覆盖）。
- [ ] **repeat 规则 GUI/真实缓存手工冒烟**：用规则编辑器新增、修改、禁用 repeat 规则并保存，再通过主程序连续处理两个 SRT，确认输出、弹窗统计、编辑器提示与真实 `subtitle_rules.pkl` 的命中/失效均符合预期（来源：#3；临时脚本仅覆盖 `SubtitleRuleProcessor`，未走 PyQt 界面与主程序链路）。
- [x] **固化 repeat 回归测试**（已完成 2026-10-22，见 `CHANGELOG.md`；落在 `tests/test_repeat.py`）：将 #3 的临时无头脚本转为可重复执行的测试，覆盖压缩/分隔独立触发、原始次数门槛、外层禁用、多规则与长词优先级、delete/replace 交互、真实默认规则回归及新旧缓存行为（来源：#3；临时脚本已删除）。
- [x] **固化 pkl 缓存校验回归测试**（已完成 2026-10-22，见 `CHANGELOG.md`；落在 `tests/test_cache.py`）：将 #5 的临时无头脚本转为可重复执行的测试，覆盖冷启动、命中、内容变化、仅格式化、schema 版本/字段缺失、损坏 pkl、`force_rebuild` 与 repeat 状态恢复（来源：#5；临时脚本已删除）。
- [ ] **主程序真实缓存手工冒烟**：通过主程序连续处理 SRT，确认首次生成 pkl、第二次命中不重建、修改 `subtitle_rules.json` 后自动失效重建，且 repeat 输出一致（来源：#5；临时脚本仅覆盖 `SubtitleRuleProcessor`，未走主程序链路）。

---

**文档版本**：v1.0
**维护原则**：完成任务后移入 `CHANGELOG.md`，新需求加到对应优先级（编号规则见文首）
