# 待办事项清单

> 只记录**未完成**的任务；已完成的历史变更见 `CHANGELOG.md`。
> 大项全部完成后整节移入 CHANGELOG；大项进行中时，已完成的子项可打勾留痕（`- [x]`）。
> 按优先级排序，完成后请移入 `CHANGELOG.md`。
> **最后更新**：2026-10-23

**编号规则**：
- 编号一旦分配即永久占用，归档、完成、删除均不回收、不复用。
- 「当前最大编号」记录历史峰值，新任务一律取该值 +1。
- 现存编号允许跳号，不要重排。
- 当前最大编号：27。

> 来源：`AI_CONTEXT.md` §11 共 24 行（高 2 / 中 10 / 低 12），编号 1–24 与表格行一一对应；优先级按该节级别映射。
> 归档：#1、#2、#3、#5、#6、#7、#11、#13、#14、#25、#26 已于 2026-10-22 完成并移入 `CHANGELOG.md`；同日「可选增强 / 测试补强」8 项（5 项自动化回归 + 3 项手工冒烟）亦已归档，该分类不占编号；#27 已于 2026-10-23 完成并移入 `CHANGELOG.md`；#19 已于 2026-10-23（夜间批量）完成并移入 `CHANGELOG.md`；#23 已于 2026-10-23（夜间批量）完成并移入 `CHANGELOG.md`；#22 已于 2026-10-23（夜间批量）完成并移入 `CHANGELOG.md`；#21 已于 2026-10-23（夜间批量）核实完成并移入 `CHANGELOG.md`；#12 已于 2026-10-23（夜间批量）按“哈希前缀”方案完成并移入 `CHANGELOG.md`；#15 已于 2026-10-23（夜间批量）完成并移入 `CHANGELOG.md`；#16 已于 2026-10-23（夜间批量）完成并移入 `CHANGELOG.md`。编号均不复用。

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

## 🟢 低优先级


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

### 20. 规范测试插件异常模拟

**背景**：测试插件用 `raise KeyboardInterrupt` 模拟错误，它不是 `Exception`，会走 Python 默认 traceback 而非统一异常处理（`AI_CONTEXT.md` §11「测试插件用 `raise KeyboardInterrupt` 模拟错误」）。

**待办**：
- [ ] 改为 `raise RuntimeError` 或普通 `Exception`，验证统一错误 JSON 与 stderr 输出
- [ ] 保留“测试报错”按钮用途，并标注仅用于调试
- [ ] 确认主程序错误弹窗路径符合预期

**关联文件**：
- `软件本体/plugins/测试插件/__init__.py`

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

（当前无条目。原「测试补强」8 项已于 2026-10-22 全部完成并归档，见 `CHANGELOG.md` 同日「测试」节。）

---

**文档版本**：v1.0
**维护原则**：完成任务后移入 `CHANGELOG.md`，新需求加到对应优先级（编号规则见文首）
