# AI_CONTEXT：Re工具箱 · 字幕处理工具合集

> 文档性质：项目交接文档（供后续 AI 助手与开发者使用）
> 生成日期：2026-10-22
> 勘察对象：`Editing-tools-related-to-SRT-subtitles/软件本体`
> 代码快照：git 仓库 `Editing-tools-related-to-SRT-subtitles`，分支 `main`，HEAD `5ff5463`（2026-10-22，领先 `origin/main` 1 个提交）
> 勘察方式：只读静态阅读源码、配置、发布产物与 git 记录；**未启动 GUI、未实际执行插件、未修改任何现有代码或配置**

## 路径与证据约定

- 下文 `软件本体/...` 均指 `Editing-tools-related-to-SRT-subtitles/软件本体/...`；工作区根目录为 `E:/projects/ReToolbox`。
- 引用格式为 `路径:行号`，行号基于上述代码快照；路径统一使用正斜杠。
- “已确认”表示结论可由源码、配置、git 记录或文件系统直接验证；“未确认”表示需要实际运行、打包或外部环境才能确认。
- 本文所说的“发布快照”指工作区根目录下的 `v1.0.0/`、`v1.1.0/`、`v1.1.0b/`、`v1.2.0/`、`v1.3.0/`、`v1.3.0b/` 与 `发布zip/`。

---

## 1. 项目概览

### 1.1 一句话定位

Re工具箱是一个 **Windows 桌面端的字幕后期处理工具台**：用户把 SRT/ASS 文件拖入主程序，主程序自动扫描 `plugins/` 下的插件并生成按钮；插件以独立进程运行，通过标准输入/输出传递文件列表，处理结果先写入 `cache/output`，可连续调用多个插件，最后统一导出到 `output/`。

项目来自视频后期场景，目标是减少字幕处理中的重复劳动（`Editing-tools-related-to-SRT-subtitles/README.md:1-2`）。

### 1.2 项目身份

| 项目 | 内容 | 依据 |
|---|---|---|
| 显示名称 | Re工具箱 / 字幕处理工具合集 / 视频后期工具箱 | `软件本体/插件调度主程序.py:280`、`软件本体/config.json:1-4` |
| 当前版本 | `1.3.0` | `软件本体/config.json:4` |
| 配置中的更新日期 | `2026-06-17` | `软件本体/config.json:5` |
| 代码仓库最新提交 | `5ff5463 feat: 窗口size由固定改为自动`（2026-10-22） | `git log` |
| 作者 | Re（B站、Q群、GitHub 100210110）；配置中还列出 DeepSeek 作为 AI 辅助 | `软件本体/config.json:7-35` |
| 许可证 | MIT | `Editing-tools-related-to-SRT-subtitles/LICENSE:1-3` |
| 技术形态 | 本地桌面 GUI，无服务端、无数据库、无网络调用 | 详见第 2、8 节 |
| 主要入口 | `软件本体/插件调度主程序.py` | `软件本体/插件调度主程序.py:475-590` |
| 核心源码规模 | 约 2,787 行 Python（`wc -l`，含测试插件与旧注释） | `wc -l` 统计 |

### 1.3 核心功能与实现状态

| 功能 | 实现位置 | 状态 |
|---|---|---|
| 拖拽文件、列表暂存、多选移除、清空 | `软件本体/插件调度主程序.py:68-108`、`214-230` | 已实现 |
| 自动扫描插件目录、按类别分组生成按钮 | `软件本体/插件调度主程序.py:112-205`、`234-271` | 已实现 |
| 多按钮插件与按钮级 `event` 路由 | `软件本体/插件调度主程序.py:138-184`、`559-571`；`软件本体/plugins/srt关键词替换/__init__.py:66-78` | 已实现 |
| 插件导入（zip）、版本比较、解压安装、重启刷新 | `软件本体/load_zip.py:38-165`；`软件本体/插件调度主程序.py:530-552` | 已实现 |
| 缓存式链式处理与统一导出 | `软件本体/插件调度主程序.py:298-337`、`375-398`、`573-582` | 已实现 |
| SRT 文件名作为说话人前缀 | `软件本体/plugins/srt加前缀/自动给srt加前缀.py:12-75` | 已实现 |
| 敏感词删除、错词替换、重复词压缩、删除次数统计（“文明小助手”） | `软件本体/plugins/srt关键词替换/build_automaton.py:56-403`、`srt_keyword_editor.py:32-139` | 已实现（含 `repeat` 压缩与可选分隔）；`regex` 规则未实现，见 6.5、11 节 |
| 规则可视化编辑（PyQt5 树形编辑器） | `软件本体/plugins/srt关键词替换/subtitle_rule_editor.py:19-857` | 已实现 |
| ASS 字幕转透明底 MOV（FFmpeg + qtrle/argb） | `软件本体/plugins/ass转码透明底视频/ass转码透明底视频.py:62-189` | 代码已实现；FFmpeg 未随仓库提供，未做运行验证 |
| 测试插件（弹窗/报错） | `软件本体/plugins/测试插件/__init__.py:14-78` | 调试用途，非生产功能 |
| 自动化测试 / CI | `tests/`（pytest，`conftest.py` + 4 个测试模块，60 项用例）；`requirements-dev.txt` | 2026-10-22 已建立测试框架并固化安装器 / repeat / pkl 缓存回归，**无 CI**；见 `CHANGELOG.md` |

### 1.4 业务背景与使用方式

- 典型用户是视频剪辑/字幕后期人员：把一集视频对应的 SRT 文件拖入工具，先做敏感词清洗或错词替换，再按文件名批量加说话人前缀，最后导出。
- 每个插件只做一件事，主程序不关心字幕内容，只负责“收集文件 → 调用插件 → 接收处理结果 → 更新文件列表”。
- 处理结果默认先写 `cache/output`，因此可以继续点击其他插件做链式处理；最终通过“导出”移动到 `output/`（`软件本体/插件调度主程序.py:573-582`）。
- ASS 插件面向需要把字幕渲染成带 Alpha 通道 MOV 的后期流程，输出格式为 QuickTime Animation（`qtrle`）+ `argb`（`软件本体/plugins/ass转码透明底视频/ass转码透明底视频.py:139-149`）。

### 1.5 工作区组成与关系

工作区根目录**不是** git 仓库；真正的 git 仓库位于 `Editing-tools-related-to-SRT-subtitles/`（其 `.git` 目录存在，`git -C` 可操作）。

| 路径 | 类型 | 作用 | 与本项目的关系 | 依据 |
|---|---|---|---|---|
| `Editing-tools-related-to-SRT-subtitles/` | git 仓库根 | 仓库级 README、LICENSE、logo、核心源码目录 | 交接主对象 | `git -C ... status`、`git remote -v` |
| `软件本体/` | 源码目录 | 主程序、插件、配置、运行缓存 | 本次勘察核心 | 目录树 |
| `v1.0.0/`、`v1.1.0/`、`v1.1.0b/`、`v1.2.0/`、`v1.3.0/`、`v1.3.0b/` | 历史发布快照 | 各版本 exe、插件、部分源码副本、构建目录 | 追溯旧实现或对比版本时参考，不是当前开发主线 | 目录内容 |
| `发布zip/` | 发布压缩包集合 | 主程序与插件的可分发 zip | 发布产物，不是源码入口 | `发布zip/` 目录与 zip 清单 |
| `打包exe指令.txt` | 构建脚本片段 | 主程序 PyInstaller 命令 | 构建参考；版本名仍写 v1.1.0，已过期 | `打包exe指令.txt:1` |
| `.venv/` | Python 虚拟环境 | 开发依赖（Python 3.11.9） | 本地运行/打包环境参考 | `.venv/pyvenv.cfg`、`.venv/old_requirements.txt` |
| `Editing-tools-related-to-SRT-subtitles/docs/AI_CONTEXT.md` | 本文档 | 交接说明 | 已随 `docs/` 迁入 git 仓库并由 git 跟踪 | 本文件 |

发布状态补充：

- `发布zip/Re工具箱/Re工具箱 - v1.3.0.zip` 内含主程序 exe、`config.json`、`plugins/srt关键词替换/`（`__init__.exe`、规则 JSON、pkl），以及 `plugins/srt加前缀`、`plugins/测试插件`。
- 另有 `发布zip/Re工具箱/Re工具箱 - v1.3.0 - 无插件.zip`，是不带插件的分发版本。
- 在现有 `v1.x` 目录和 `发布zip/` 中**未发现** `ass转码透明底视频` 插件的发布目录或压缩包；该插件是否曾单独发布，**未确认**。
- `v1.1.0b/` 保存了当时的源码副本与 PyInstaller `build/`、`dist/`；`v1.0.0/` 保存了旧版 `插件调度主程序.py`。这些可作为历史对照，但不应作为当前实现依据。

---

## 2. 技术栈与版本

### 2.1 技术栈总览

以下版本来自工作区 `.venv` 的实际安装记录；仓库内没有 `requirements.txt`、`pyproject.toml` 或 `setup.py`，因此**这些版本是当前开发环境的快照，不是项目声明的依赖约束**。

| 类别 | 技术 / 包 | 版本 | 用途 | 依据 |
|---|---|---|---|---|
| 语言 | Python | 3.11.9 | 主程序与全部插件 | `.venv/pyvenv.cfg` |
| 主 GUI | PySimpleGUI | 6.0 | 主窗口、按钮、弹窗、日志 | `软件本体/插件调度主程序.py:1`；`.venv/Lib/site-packages` |
| 拖拽 | tkinterdnd2 | 0.4.3 | 文件拖放到列表框 | `软件本体/插件调度主程序.py:2` |
| 规则编辑器 GUI | PyQt5 | 5.15.11 | 树形规则编辑窗口 | `软件本体/plugins/srt关键词替换/subtitle_rule_editor.py:5-11` |
| PyQt 运行时 | PyQt5-Qt5 / PyQt5_sip | 5.15.2 / 12.18.0 | PyQt5 依赖 | `.venv/Lib/site-packages` |
| 多模式匹配 | pyahocorasick（导入名 `ahocorasick`） | 2.3.1 | Aho-Corasick 自动机 | `软件本体/plugins/srt关键词替换/build_automaton.py:3` |
| ASS 解析 | pyass | 0.1.4 | 读取 ASS 事件、结束时间 | `软件本体/plugins/ass转码透明底视频/ass转码透明底视频.py:5` |
| 版本比较 | packaging | 26.1 | 插件版本排序比较 | `软件本体/load_zip.py:7` |
| 打包 | PyInstaller | 6.20.0 | 生成单文件 exe | `.venv/old_requirements.txt`、`打包exe指令.txt:1` |
| 媒体处理 | FFmpeg（外部可执行文件） | 版本未知 | ASS 渲染透明底视频 | `软件本体/plugins/ass转码透明底视频/ass转码透明底视频.py:69`、`137-149` |
| 标准库 | `subprocess`、`zipfile`、`pickle`、`logging`、`json`、`re`、`shutil`、`io` | Python 3.11 自带 | 进程、安装、缓存、日志、解析 | 各模块 import |
| 系统能力 | `notepad.exe`、`explorer.exe`、`CREATE_NEW_CONSOLE` | Windows | 打开配置、打开导出目录、FFmpeg 子进程 | `软件本体/插件调度主程序.py:568`、`580`；`ass转码透明底视频.py:156-164` |

### 2.2 运行时要求

- **操作系统**：Windows。代码使用了 `notepad.exe`、`explorer.exe`、`subprocess.CREATE_NEW_CONSOLE`、`plugins\\{plugin_id}` 等 Windows 专有写法（`软件本体/插件调度主程序.py:568-580`、`load_zip.py:77`、`ass转码透明底视频.py:156-164`）。
- **Python**：开发/打包建议 Python 3.11.x；代码使用 `match/case`（3.10+）与 `sys.stdin.reconfigure`（3.7+），因此在 3.10 以下无法运行。
- **开发依赖**：以实际 import 为准，至少需要 PySimpleGUI、tkinterdnd2、pyahocorasick、pyass、packaging、PyQt5、PyInstaller。
- **外部二进制**：ASS 插件运行时必须存在 FFmpeg（见 8.5）；仓库内 `plugins/ass转码透明底视频/ffmpeg/bin/` 为空目录。
- **写权限**：程序目录下需要可写 `cache/output`、`cache/temp`、`output`、插件规则文件与插件日志；若安装到 `Program Files` 等只读目录，相关功能会失败。
- **GUI 环境**：PySimpleGUI/tkinter 需要桌面会话；PyQt5 编辑器需要 Qt 运行库。

### 2.3 没有使用的技术

- 没有 Web 框架、HTTP API、RPC、数据库或 ORM。
- 没有 `os.environ` / `.env` 读取（全目录 grep 未发现）。
- 没有网络请求代码；`config.json` 中的 URL 只是作者联系方式，不会被程序访问。

---

## 3. 目录结构

### 3.1 `软件本体/` 目录树

```text
软件本体/
├── 插件调度主程序.py          # 主程序：GUI、插件扫描、子进程调度、导入/导出
├── load_zip.py                # 插件 zip 安装器：读取 manifest、比较版本、解压
├── config.json                # 主程序元信息（版本、日期、作者）
├── icon.ico                   # 主窗口/关于窗口图标
├── cache/
│   ├── output/                # 插件处理结果缓存；启动时会被清空
│   └── temp/                  # 插件临时文件；FFmpeg 日志也落在这里
├── output/                    # 用户最终导出的文件（持久）
└── plugins/
    ├── srt加前缀/
    │   ├── manifest.json
    │   └── 自动给srt加前缀.py
    ├── srt关键词替换/
    │   ├── manifest.json
    │   ├── __init__.py         # 插件入口/事件分发
    │   ├── common.py           # 路径工具、日志初始化
    │   ├── build_automaton.py  # 规则解析、AC 自动机、缓存、文本处理
    │   ├── srt_keyword_editor.py # 批量处理入口（读 stdin，写 stdout JSON）
    │   ├── subtitle_rule_editor.py # PyQt5 规则编辑器
    │   ├── subtitle_rules.json # 当前生效规则
    │   ├── default_subtitle_rules.json # 默认规则模板
    │   ├── subtitle_rules.pkl  # 自动机与规则缓存（被 git 跟踪）
    │   └── plugin_log/         # 运行日志（当前未被 git 跟踪）
    ├── ass转码透明底视频/
    │   ├── manifest.json
    │   ├── ass转码透明底视频.py
    │   ├── test.ass
    │   └── ffmpeg/             # 期望的 FFmpeg 目录；当前 bin/ 为空
    └── 测试插件/
        ├── manifest.json
        ├── __init__.py
        ├── test.py
        └── test_1.py
```

### 3.2 主要目录/文件职责

| 路径 | 职责 | 关键依据 |
|---|---|---|
| `软件本体/插件调度主程序.py` | 唯一主入口；构建 UI、扫描插件、维护文件列表、启动插件子进程、导入插件、导出文件 | `112-205`、`298-372`、`423-590` |
| `软件本体/load_zip.py` | 插件安装器类 `PluginInstaller`；从 zip 根目录读取 `manifest.json`，按版本决定是否安装，解压到 `plugins/<plugin_id>/` | `38-165` |
| `软件本体/config.json` | 主程序名称、版本、更新日期、作者信息；主程序只读取 `version` 与 `update_date` | `插件调度主程序.py:50-59` |
| `软件本体/cache/output/` | 插件输出暂存；**首次启动**时清空，插件导入后的窗口重建不清空；链式处理的载体 | `插件调度主程序.py:307-310`、`440-441` |
| `软件本体/cache/temp/` | 插件的临时目录（ASS 临时字幕、FFmpeg `-report` 日志等） | `插件调度主程序.py:307-310`；`ass转码透明底视频.py:126-133` |
| `软件本体/output/` | 最终导出目录；由“导出/导出并打开位置”按钮写入 | `插件调度主程序.py:573-582` |
| `plugins/<插件目录>/manifest.json` | 插件元数据与按钮声明；主程序扫描的唯一入口条件 | `插件调度主程序.py:130-204` |
| `plugins/srt关键词替换/*` | 规则驱动的字幕清洗插件；含 PyQt5 规则编辑器 | 见 5.4、5.5 |
| `plugins/srt加前缀/*` | 最简单的插件样板：读 JSON、处理 SRT、写缓存、返回 JSON | `自动给srt加前缀.py:28-75` |
| `plugins/ass转码透明底视频/*` | 用 pyass 取时长、用 FFmpeg 渲染透明 MOV | 见 5.7 |
| `plugins/测试插件/*` | PySimpleGUI 弹窗与报错测试，用于验证协议/按钮事件 | `测试插件/__init__.py:14-78` |

### 3.3 仓库级文件

| 路径 | 说明 |
|---|---|
| `Editing-tools-related-to-SRT-subtitles/README.md` | 用户向说明；内容停留在较早版本，见 11 节 |
| `Editing-tools-related-to-SRT-subtitles/LICENSE` | MIT License，Copyright (c) 2026 realcan |
| `Editing-tools-related-to-SRT-subtitles/logo/` | 图标资源（`icon.ico`、`画板1.png`、`绪山真寻的本体.ico`） |
| `Editing-tools-related-to-SRT-subtitles/docs/` | 交接文档目录（`AI_CONTEXT.md`、`TODO.md`、`CHANGELOG.md`），已随代码入库并由 git 跟踪 |
| `打包exe指令.txt` | 主程序 PyInstaller 命令，版本名未更新 |
| `.venv/old_requirements.txt` | UTF-16 编码的旧依赖清单；不含 PyQt5，含未使用的 `pysub-parser`、`Unidecode` |

### 3.4 仓库卫生现状

- git 只跟踪 31 个文件（`git ls-files`）。
- `cache/temp/ffmpeg-*.log` 四个日志被 git 跟踪；`subtitle_rules.pkl` 也被跟踪（`git ls-files`）。
- `plugins/srt关键词替换/plugin_log/` 当前是 untracked（`git status` 显示 `?? .../plugin_log/`），且仓库没有 `.gitignore`。
- 测试基础设施：勘察时（2026-10-22 前）没有 `tests/`、`pytest.ini`、`tox.ini`、GitHub Actions；现已建立 `tests/`（pytest）与 `requirements-dev.txt`，仍无 CI（见 9.5）。

---

## 4. 架构设计

### 4.1 分层视图

| 层 | 组成 | 职责 | 依赖方向 |
|---|---|---|---|
| 表现层（宿主 UI） | `插件调度主程序.py`、`BuildLayout` | 窗口、文件列表、日志、插件按钮、导入/导出交互 | 依赖插件清单与 `load_zip` |
| 插件运行时 | `scan_plugins`、`run_script_plugin` | 发现插件、拼装请求 JSON、启动子进程、解析响应 | 依赖 `subprocess` 与插件可执行文件 |
| 插件实现层 | 四个 `plugins/*` | 各自完成字幕处理；不直接操作主程序内存 | 通过 stdin/stdout 与宿主通信 |
| 规则/配置层 | `config.json`、`manifest.json`、`subtitle_rules.json`、`*.pkl` | 描述程序、插件、规则与缓存 | 被宿主、插件读取 |
| 通用工具层 | `load_zip.py`、各插件 `get_path`、`common.setup_logger` | 安装、路径解析、日志 | 被上层复用 |
| 分发层 | PyInstaller exe、`发布zip/`、`v1.x` 快照 | 生成并分发独立可执行文件 | 不属于运行时代码 |

### 4.2 运行时结构图

```text
┌──────────────────────────────┐
│ 用户：拖入 SRT / ASS 文件      │
└──────────────┬───────────────┘
               │ TkDND
┌──────────────▼───────────────┐
│ 插件调度主程序.py             │
│  - FILE_LIST（全局列表）       │
│  - scan_plugins()             │
│  - BuildLayout                │
└───────┬───────────────┬──────┘
        │ 读取          │ 点击插件按钮
        ▼               ▼
┌───────────────┐  ┌────────────────────────────┐
│ plugins/*/    │  │ run_script_plugin()         │
│ manifest.json │  │  stdin: JSON 请求            │
└───────────────┘  │  stdout: JSON 响应           │
                   │  stderr: 日志/错误            │
                   └──────────────┬─────────────┘
                                  │ subprocess
                   ┌──────────────▼─────────────┐
                   │ 插件进程（.py / .exe）       │
                   │  srt加前缀 / srt关键词替换 / │
                   │  ass转码 / 测试插件          │
                   └──────────────┬─────────────┘
                                  │ 写入
                   ┌──────────────▼─────────────┐
                   │ cache/output（同名覆盖）     │
                   └──────────────┬─────────────┘
                                  │ 导出
                   ┌──────────────▼─────────────┐
                   │ output/（最终文件，持久）    │
                   └────────────────────────────┘
```

### 4.3 模块依赖关系

| 模块 | 直接依赖 | 被谁调用 | 备注 |
|---|---|---|---|
| `插件调度主程序.py` | `PySimpleGUI`、`tkinterdnd2`、`load_zip.import_plugin_list`、标准库 | 用户直接启动 | 主进程 |
| `load_zip.py` | `PySimpleGUI`、`packaging.version`、`zipfile` | 主程序的“导入插件” | 安装逻辑与 UI 混在一起 |
| `plugins/srt关键词替换/__init__.py` | `common`、`srt_keyword_editor`、`subtitle_rule_editor` | 主程序按 `manifest.buttons[].executable` 启动 | 子进程入口 |
| `srt_keyword_editor.py` | `build_automaton.SubtitleRuleProcessor`、`common` | `__init__.py` 的 `event_main` | 真正处理 SRT |
| `build_automaton.py` | `ahocorasick`、`pickle`、自带 `get_path` | `srt_keyword_editor`、规则编辑器间接 | 规则解析与匹配核心 |
| `subtitle_rule_editor.py` | `PyQt5`、`common` | `__init__.py` 的 `event_subtitle_rule_editor` | 独立 GUI |
| `自动给srt加前缀.py` | 标准库 | 主程序 | 无 `common` 依赖，自包含 |
| `ass转码透明底视频.py` | `pyass`、`subprocess`、FFmpeg | 主程序 | FFmpeg 外部依赖 |
| `测试插件/__init__.py` | `test.py` / `test_1.py`、PySimpleGUI | 主程序 | 调试用 |

### 4.4 插件发现规则

`scan_plugins()` 的逻辑（`软件本体/插件调度主程序.py:112-205`）：

1. 以程序目录下的 `plugins/` 为根（开发环境取 `__file__` 目录，打包后取 `sys.executable` 目录）。
2. 只扫描一级子目录；子目录必须存在 `manifest.json` 才会被识别。
3. **新版多按钮格式**：`manifest.json` 含 `buttons` 数组；每个按钮读取 `label`、`executable`、`type`、`event`、`tooltip`。
4. 可执行文件解析：先尝试 `executable` 原值；不存在则依次尝试 `.py`、`.exe` 后缀（`146-161`）。
5. **旧版单按钮格式**：没有 `buttons` 时读取 `name`、`executable`、`description`，类型固定为 `script`（`186-204`）。
6. 生成唯一 key：`BTN_{插件目录名}_{按钮标签}`（`174`、`195`）。
7. `BuildLayout.build_middle()` 按 `(category, plugin_folder)` 分组，先输出类别标题，再输出该插件的按钮行；行数超过 7 时启用垂直滚动（`234-271`）。

注意：`scan_plugins()` 在 `init_program()` 中被调用了两次（`438`、`448`），属于重复扫描；当前不影响功能，但会多一次磁盘/JSON 读取。

### 4.5 进程边界与通信

- 每个插件是**独立子进程**，不是 Python 模块级调用；主程序不 import 插件代码。
- 主程序把请求 JSON 写入子进程 stdin，关闭 stdin 后读取 stdout/stderr（`软件本体/插件调度主程序.py:330-337`）。
- 插件约定：**stdout 只输出一个 JSON 响应**；日志、进度、异常栈写 stderr。
- 主程序不设置超时；`proc.communicate(json_str)` 会一直阻塞到插件退出（`337`）。
- 开发环境（未 `sys.frozen`）且插件是 `.py`：用 `sys.executable` 启动；打包后：直接执行插件 exe（`323-328`）。

### 4.6 路径解析策略

项目没有统一的路径模块，而是在多个文件中重复实现了 `get_path()`，且默认参数不完全一致：

| 文件 | 默认 `use_program_dir` | 行为 | 用途 |
|---|---|---|---|
| `软件本体/插件调度主程序.py:22-48` | `True` | 打包后取 exe 所在目录；否则取脚本目录 | 配置、插件目录、缓存、导出 |
| `软件本体/load_zip.py:10-36` | `True` | 同上 | 计算插件安装路径 |
| `软件本体/plugins/srt关键词替换/common.py:8-34` | `False` | 打包后默认取 `sys._MEIPASS`（只读资源目录）；显式 `True` 才取 exe 目录 | 日志、规则文件、默认规则资源 |
| `软件本体/plugins/srt关键词替换/build_automaton.py:27-53` | `True` | 与主程序相同 | 规则 JSON / pkl 路径 |
| `软件本体/plugins/ass转码透明底视频/ass转码透明底视频.py:18-44` | `True` | 与主程序相同 | FFmpeg 路径 |

这套约定支持“单文件 exe + 外部可写目录”：`icon.ico`、`default_subtitle_rules.json` 等只读资源通过 `--add-data` 打进 `sys._MEIPASS`；规则、缓存、日志写到 exe 旁边。代价是逻辑重复、默认值容易踩坑，详见 11 节。

### 4.7 链式处理模型

1. 初始 `FILE_LIST` 保存用户拖入的原始文件路径。
2. 插件处理成功后，把**输出文件路径**放进 `completed_output_lists`；主程序用它整体替换 `FILE_LIST`（`软件本体/插件调度主程序.py:356-358`）。
3. 下一次点击插件时，处理对象已经是 `cache/output` 中的文件。
4. 多个 SRT 插件都以“原 basename”写到同一个 `cache/output`，因此后一个插件会覆盖前一个插件的同名输出；但内容是在前一步输出上继续处理的，效果上形成“原地链式变换”。
5. 导出时 `move_all_files()` 把 `cache/output` 内文件移动到 `output/`，同名文件追加 `_1`、`_2` 等后缀（`375-387`），然后清空 `FILE_LIST`。

该模型简单有效，但**不保留每一步中间文件**，且不同目录下的同名输入会互相覆盖（详见 11 节）。

---

## 5. 核心业务流程

### 5.1 主程序启动

| 步骤 | 行为 | 代码位置 |
|---|---|---|
| 1 | 读取 `config.json`；失败时使用内嵌默认配置，版本显示“配置文件丢失” | `软件本体/插件调度主程序.py:50-59` |
| 2 | 初始化：确定程序目录；`clear_cache=True` 时清空 `cache/output`（保留目录本身） | `423-441` |
| 3 | 扫描插件，构建按钮列表 | `438`、`448` |
| 4 | 创建隐藏的 Tk 根窗口（供 TkDND 使用），再创建 PySimpleGUI 主窗口 | `444-452` |
| 5 | 给 `-FILE_LIST-` 控件注册 `DND_FILES`，绑定 `<<Drop>>` | `455-457` |
| 6 | 将命令行参数追加到 `FILE_LIST` 并刷新 | `460-465` |
| 7 | 构建 `button_map`，进入事件循环 | `471-485` |
| 8 | 窗口关闭时退出循环并关闭窗口 | `487-489`、`587` |

`init_program(clear_cache=True)` 的返回值是 `(window, button_map, program_dir, root, cache_dir)`（`473`、`479`）；“重启刷新”按重启语义销毁旧窗口和 Tk 根、重新调用 `init_program()`（清空 `cache/output`，`521-532`）；“导入插件”仅在真正装上了插件时才重建，且传 `clear_cache=False` 保留已处理的中间产物（`534-562`）。`FILE_LIST` 是模块级全局变量，重建窗口时不会丢失（见 5.2）。

### 5.2 文件拖入与列表管理

| 步骤 | 行为 | 代码位置 |
|---|---|---|
| 1 | TkDND 触发 `on_drop(event, window)` | `87-108`、`455-457` |
| 2 | `parse_dropped_files()` 解析：优先处理 `{...}` 包裹的路径；否则按换行；再否则按空格拆分 | `68-79` |
| 3 | 用 `set` 去重，追加到全局 `FILE_LIST` | `96-102` |
| 4 | 只有新增文件时才刷新列表框 | `104-107` |
| 5 | “移除选中”从列表删除；“清空所有”清空列表并清空 `cache/output` | `491-512` |

注意：列表项是**原始路径字符串**，不做扩展名过滤；是否处理由各插件自行判断。文件夹路径也会被接受，但通常会被插件跳过。

`FILE_LIST` 是模块级全局变量（`62`），主窗口重建（重启刷新、导入插件）时**不会清空**；但插件运行成功后会被插件返回的 `completed_output_lists` 整体覆写为 `cache/output` 下的路径（`357`），此时列表项已不是用户最初拖入的原始文件。

### 5.3 点击插件按钮后的调度

| 步骤 | 行为 | 代码位置 |
|---|---|---|
| 1 | 事件名命中 `button_map` 中的 key | `559-560` |
| 2 | 若 `type == "script"`，调用 `run_script_plugin(btn_info, window)` | `561-563` |
| 3 | 若 `type == "config"`，用 `notepad.exe` 打开配置文件 | `565-569` |
| 4 | 准备 `cache/output`、`cache/temp`，构造请求 JSON | `302-320` |
| 5 | 根据开发/打包环境选择 `python plugin.py` 或 `plugin.exe` | `323-328` |
| 6 | `subprocess.Popen(..., stdin=PIPE, stdout=PIPE, stderr=PIPE, encoding='utf-8')`，同步 `communicate` | `330-337` |
| 7 | 返回码为 0：解析 stdout JSON；有 `popup` 则弹窗；有 `completed_output_lists` 则替换 `FILE_LIST` 并刷新 | `340-361` |
| 8 | 返回码非 0：把 stderr 作为错误弹窗（超过 500 字符或 10 行则用滚动窗口） | `362-372` |

请求 JSON 的字段见 7.2；响应 JSON 的字段见 7.3。主程序对 stdout 的 JSON 解析失败时只打印日志，不会弹窗（`359-361`）。

### 5.4 SRT 关键词替换主流程

这是项目中最复杂、也是当前主打的插件。入口链路为：
`manifest.json` → `__init__.py` 的 `event_main` → `srt_keyword_editor.main` → `SubtitleRuleProcessor`。

| 步骤 | 行为 | 代码位置 |
|---|---|---|
| 1 | `__init__.py` 读取 stdin JSON，按 `event` 分发；默认 `main` | `软件本体/plugins/srt关键词替换/__init__.py:52-78` |
| 2 | `event_main` 调用 `srt_keyword_editor.run(params)` | `17-24` |
| 3 | 从请求中取 `output_path`、`pending_file_lists`，创建输出目录 | `srt_keyword_editor.py:63-76` |
| 4 | 构建 `SubtitleRuleProcessor`，调用 `load_rules()` | `86-88` |
| 5 | 校验 pkl 缓存的 `schema_version` 与 JSON 内容哈希：均匹配则 `pickle.load` 恢复自动机、映射与 repeat 状态；否则重新解析 JSON、构建自动机并写回缓存（`force_rebuild=True` 跳过校验强制重建） | `build_automaton.py:343-437` |
| 6 | 解析 `delete`：所有词加入删除列表；`profanity` 子类加入敏感词集合；去重 | `104-112` |
| 7 | 解析 `replace`：递归遍历分组；`correction` 节点建立“源词 → 正确词”双向映射；`group` 节点递归子项；`regex` 空操作 | `163-186` |
| 8 | 解析 `repeat`：`enabled=false` 的规则整条跳过；填充重复词规则映射（`max_times`、间隔开关、门槛、分隔符） | `122-161` |
| 9 | 构建主 AC 自动机：只加入 `delete_words` 和 `replace_source_to_word` 的源词；repeat 另建独立自动机 | `199-221` |
| 10 | 逐文件读取文本，重置敏感词计数，调用 `process_text()` | `srt_keyword_editor.py:90-119` |
| 11 | `process_text()` 用主自动机收集 delete/replace 匹配，解析重叠，按位置从右到左删除/替换 | `build_automaton.py:223-258`、`315-337` |
| 12 | 在清理后的文本上执行 repeat：连续同词重复按 `max_times` 压缩；满足间隔条件时插入分隔符；不改变敏感词计数 | `260-313` |
| 13 | 写回 `cache/output/<原 basename>.srt`，记录成功列表 | `srt_keyword_editor.py:104-113` |
| 14 | 统计每个文件删除的 profanity 次数，按降序取前 10，生成“文明小助手”文案 | `32-57`、`81-123` |
| 15 | stdout 输出 JSON（含 `popup` 与 `completed_output_lists`） | `127-139` |

关键语义：

- **大小写敏感**：AC 自动机默认精确匹配；英文变体靠规则里的人工枚举（如 `Kamu`、`karm`、`come`）覆盖，没有统一转小写逻辑（`build_automaton.py:199-221`）。
- **删除计数**：只有 `delete.profanity` 中的词会累加计数；`delete.others` 只删除、不计数（`104-112`、`249-254`）。
- **最长匹配**：`_resolve_overlaps()` 先按起点升序、终点降序排序，再线性过滤；**只有起点相同的候选才保证长词优先**，起点不同的重叠不保证全局最长匹配（`223-239`）。
- **同位置冲突**：删除与替换若落在同一区间，最终结果取决于匹配收集顺序与排序稳定性；没有显式优先级（`223-258`）。
- **repeat 生效条件**：外层 `enabled=false` 时整条规则不生效（不识别、不压缩、不加分隔符）；`interval.enabled` 只控制是否插入分隔符，压缩与识别不受其影响（`122-161`、`269-276`）。
- **repeat 识别与处理**：只识别无空格、无标点的连续同词重复；重复次数按“词出现次数”计算（如 `哈哈哈哈` 中 `哈哈` 计 2 次）；原始次数超过 `max_times` 时压缩，达到 `min_consecutive` 时可插入 `separator`；同位置多规则按 `max_times` 小者优先、再长词优先；处理顺序为 delete/replace → repeat，repeat 不改变敏感词计数（`260-313`、`315-337`）。
- **输出命名**：与输入同 basename，不保留目录层级；同名输入会覆盖（`104-108`）。
- **规则缓存**：`subtitle_rules.pkl` 只通过 mtime 判断是否过期；如果 pkl 来自旧版本但 mtime 较新（例如 git checkout 后），会直接加载旧缓存；载荷已包含 repeat 状态，缺少 repeat 键的旧缓存会触发重建（`339-403`）。

### 5.5 规则编辑器流程

入口为 `manifest.json` 的第二个按钮：`event = "subtitle_rule_editor"` → `__init__.py` 的 `event_subtitle_rule_editor()` → `subtitle_rule_editor.run()`。

| 步骤 | 行为 | 代码位置 |
|---|---|---|
| 1 | 先读取 `default_subtitle_rules.json` 作为模板（打包后从 `sys._MEIPASS` 读） | `subtitle_rule_editor.py:169-182` |
| 2 | 再读取工作文件 `subtitle_rules.json`；存在则覆盖模板数据 | `184-190` |
| 3 | 构建 PyQt5 主窗口：工具栏（新建/打开/保存/另存为）+ 三棵树（Delete/Repeat/Replace） | `245-299` |
| 4 | 右键菜单按节点类型提供编辑、删除、切换启用、添加子分组/子项 | `757-844` |
| 5 | 保存时 `json.dump(..., indent=4)`，再用正则压缩含 `source` 的叶节点 | `192-212` |
| 6 | 退出时 `sys.exit(app.exec_())` | `852-857` |

规则编辑器的语义补充：

- “启用”状态会写入 JSON 的 `enabled` 字段；主处理器在解析时跳过 `enabled=false` 的节点（`build_automaton.py:163-181`）。
- 编辑器支持 `repeat` 规则的增删改（`514-556`），并在 Repeat 对话框提供语义 tooltip（外层启用、压缩与分隔独立、门槛按原始次数、分隔符作用）；保存后由主处理器解析并生效，见 5.4 与 6.5。
- `ReplaceItemDialog` 只防止同一个 item 的 `source` 列表内重复（`108-115`），不检查不同 item/分组之间的源词冲突；主处理器后写入的映射会覆盖先写入的（`build_automaton.py:171-176`）。
- 打包后“新建”把保存目标设为 `os.path.dirname(__file__)/subtitle_rules.json`（`214-218`）；在 PyInstaller 单文件模式下 `__file__` 可能位于临时解压目录，存在写入只读/临时目录的风险，**未在打包环境验证**。

### 5.6 SRT 加前缀流程

| 步骤 | 行为 | 代码位置 |
|---|---|---|
| 1 | 从 stdin 读取 JSON，取 `output_path` 与 `pending_file_lists` | `软件本体/plugins/srt加前缀/自动给srt加前缀.py:28-46` |
| 2 | 只处理后缀为 `.srt`（大小写不敏感）的路径；其他路径打印跳过 | `50-66` |
| 3 | 用输入文件名（不含扩展名）加中文全角冒号 `：` 作为前缀 | `53` |
| 4 | 按 `range(2, len(lines), 4)` 在每四行的第三行（文本行）前插入前缀 | `19-20` |
| 5 | 写入 `cache/output/<原 basename>` | `55-61` |
| 6 | stdout 返回 `status`、`processed`（注意：这里用的是输入文件数，不是成功数）、`completed_output_lists`、`popup: False` | `68-74` |

该插件假设 SRT 严格为“序号 / 时间轴 / 单行文本 / 空行”四行结构；多行字幕、缺少空行、时间轴后有多行文本时，插入位置会错位。重复运行会把文件名前缀再次叠加，而不是幂等处理。

### 5.7 ASS 转透明底视频流程

| 步骤 | 行为 | 代码位置 |
|---|---|---|
| 1 | 从 stdin 读取 JSON，取 `output_path`、`temp_path`、`pending_file_lists` | `软件本体/plugins/ass转码透明底视频/ass转码透明底视频.py:201-219` |
| 2 | 只处理 `.ass` 文件；其他扩展名静默跳过 | `222-224` |
| 3 | `pyass.load()` 读取 ASS 事件，取所有 `event.end` 的最大值作为视频时长 | `77-91` |
| 4 | 从 ASS 头解析 `PlayResX` / `PlayResY`；缺失时默认 1920×1080 | `93-107` |
| 5 | 复制 ASS 到 `cache/temp/_temp_sub_<pid>.ass`，避免路径/编码问题 | `126-133` |
| 6 | 调用 FFmpeg：`-f lavfi -i "color=color=black@0:size=WxH:rate=60,format=rgba,subtitles=temp.ass:alpha=1"` | `137` |
| 7 | 输出 `qtrle` + `argb` 的 `.mov`，`-y` 覆盖已有文件 | `139-149` |
| 8 | 在 Windows 上以 `CREATE_NEW_CONSOLE` 启动 FFmpeg 子进程，工作目录设为临时目录 | `156-173` |
| 9 | 结束后删除临时 ASS；FFmpeg 的 `-report` 日志留在 `cache/temp` | `181-189` |
| 10 | 成功则写 `cache/output/<basename>.mov`；全部失败时返回错误 JSON 并以退出码 1 结束 | `229-266` |

运行前提：`plugins/ass转码透明底视频/ffmpeg/bin/ffmpeg.exe` 必须存在（`69`、`110-111`）。当前仓库该目录为空，直接运行会抛出“不是, 你 FFmpeg 呢”。

### 5.8 插件导入与导出

**插件导入**（`软件本体/load_zip.py`）：

1. 主程序“导入插件”把 `FILE_LIST` 传给 `import_plugin_list()`（`软件本体/插件调度主程序.py:530-533`）。
2. `PluginInstaller.load_zip_json()` 从 zip 根读取 `manifest.json`，要求 `name`、`version`，`plugin_id` 缺省时使用 `name`；安装路径为 `plugins/<plugin_id>/`（`66-81`）。
3. `check_version_and_install()` 读取已安装版本的 manifest，用 `packaging.version.parse` 比较：
   - 未安装 → 直接安装；
   - 新版本更高 → 安装；
   - 版本相同/更低 → 弹窗询问是否重装（`84-118`）。
4. `install()` 先 `shutil.rmtree` 目标目录，再逐项校验 zip 成员路径（拒绝绝对路径、`..`、以 `/` 开头），最后 `extractall`（`121-134`）。
5. 安装完成后主程序从 `FILE_LIST` 移除成功导入的 zip，销毁并重建窗口；**重建只在 `success_list` 非空时发生**，失败、取消重装与无变动场景只弹窗（失败时）并保持窗口不变，避免无谓刷新与清空 `cache/output`（`534-562`）。
6. 重建走 `init_program(clear_cache=False)`（`557`），因此链式处理留在 `cache/output` 的中间产物不会被删除；`FILE_LIST` 是模块级全局变量，重建后列表项与顺序均保留（`62`、`425`）。

**导出**：

- “导出”：`move_all_files(cache/output, output)`，清空 `FILE_LIST`（`573-576`）。
- “导出并打开位置”：同上，再用 `explorer` 打开 `output/`（`578-582`）。
- 同名目标文件用 `_1`、`_2` 递增后缀避免覆盖（`375-387`）。

---

## 6. 数据模型

### 6.1 总体说明

项目**不使用数据库、ORM、迁移工具或表结构**。数据模型由以下四类组成：

1. JSON 配置文件（程序、插件、规则）；
2. Python 进程内的规则对象与 AC 自动机；
3. `pickle` 缓存文件；
4. 文件系统目录（输入列表、缓存、导出）。

### 6.2 持久化文件一览

| 文件 | 格式 | 生产者 | 消费者 | 生命周期/说明 |
|---|---|---|---|---|
| `软件本体/config.json` | JSON | 人工维护 | 主程序 | 读取 `version`、`update_date`；其余字段仅展示/备用 |
| `plugins/*/manifest.json` | JSON | 插件作者/安装包 | 主程序 `scan_plugins`、`load_zip` | 每个插件必须位于自身目录根部 |
| `plugins/srt关键词替换/subtitle_rules.json` | JSON | 规则编辑器/人工 | `SubtitleRuleProcessor` | 当前生效规则；编辑器默认保存目标 |
| `plugins/srt关键词替换/default_subtitle_rules.json` | JSON | 开发者 | 规则编辑器、处理器兜底复制 | 打包时作为只读资源 |
| `plugins/srt关键词替换/subtitle_rules.pkl` | Python pickle | `SubtitleRuleProcessor._save_to_cache` | `_load_from_cache` | AC 自动机与映射缓存；被 git 跟踪 |
| `plugins/srt关键词替换/plugin_log/*.log` | 文本 | `common.setup_logger` | 人工排查 | `plugin_error.log` 始终写；`plugin_info.log` 仅在 `debug=true` 时写 |
| `软件本体/cache/output/` | 文件目录 | 各插件 | 后续插件/导出 | 首次启动时清空；窗口重建不清空 |
| `软件本体/cache/temp/` | 文件目录 | ASS 插件、FFmpeg | 插件自身 | 启动时不清空；可能残留 FFmpeg 日志 |
| `软件本体/output/` | 文件目录 | 导出动作 | 用户 | 持久保留 |

### 6.3 `config.json` 字段

| 字段 | 类型 | 示例/说明 | 是否被代码读取 |
|---|---|---|---|
| `name` | string | `字幕处理工具合集` | 否（仅展示性） |
| `description` | string | 插件控制台说明 | 否 |
| `version` | string | `1.3.0`，显示在窗口底部 | 是（`插件调度主程序.py:58`） |
| `update_date` | string | `2026-06-17` | 是（`59`） |
| `others` | string | 作者备注“这个配置文件没什么用” | 否 |
| `authors` | array | 作者与联系方式 | 否 |

### 6.4 `manifest.json` 字段

新版多按钮格式（当前三个生产插件均使用）：

| 字段 | 类型 | 必填 | 说明 | 依据 |
|---|---|---|---|---|
| `name` | string | 是 | 插件名 | 各 manifest |
| `category` | string | 否 | 主界面分组标题，默认“未分类” | `插件调度主程序.py:135` |
| `version` | string | 是（导入时） | 版本比较 | `load_zip.py:72`、`97-115` |
| `description` | string | 否 | 插件描述 | `load_zip.py:73` |
| `debug` | bool | 否 | 控制 `plugin_info.log` 是否写入 | `common.py:54-59` |
| `buttons` | array | 是（新版） | 按钮列表 | `插件调度主程序.py:138` |
| `buttons[].label` | string | 是 | 按钮文字，也参与 key | `140-144` |
| `buttons[].executable` | string | 是 | 脚本/exe 文件名（可省略扩展名） | `144-161` |
| `buttons[].type` | string | 否 | `script` 或 `config`；缺省按扩展名推断 | `164-172` |
| `buttons[].event` | string | 否 | 传给插件的事件名 | `183`、`317-318` |
| `buttons[].tooltip` | string | 否 | 悬停提示 | `178` |
| `plugin_id` | string | 否 | 安装目录名；缺省用 `name` | `load_zip.py:74-77` |

旧版单按钮格式：

| 字段 | 说明 |
|---|---|
| `name` | 按钮文字/插件名 |
| `executable` | 脚本/exe 文件名 |
| `description` | 按钮 tooltip |
| `category` | 分组 |

### 6.5 `subtitle_rules.json` 结构

顶层三个键：

```json
{
  "delete": {
    "profanity": ["傻逼", "卧槽", "..."],
    "others": ["呃", "huh", "uh"]
  },
  "repeat": [
    {
      "word": "哈",
      "enabled": true,
      "max_times": 3,
      "interval": {
        "enabled": false,
        "min_consecutive": 3,
        "separator": " "
      }
    }
  ],
  "replace": [
    {
      "word": "我的世界",
      "type": "group",
      "enabled": true,
      "items": [
        {
          "word": "卡慕",
          "enabled": true,
          "source": ["卡布", "卡莫", "卡木"]
        }
      ]
    }
  ]
}
```

字段说明：

| 路径 | 类型 | 说明 | 处理逻辑 |
|---|---|---|---|
| `delete.profanity` | string[] | 敏感词列表 | 删除并计数 |
| `delete.others` | string[] | 其他要删除的词 | 删除但不计数 |
| `repeat[]` | object[] | 重复词规则 | 解析后生效；外层禁用则整条跳过 |
| `repeat[].word` | string | 连续重复的匹配词 | 仅识别无空格、无标点的连续同词 |
| `repeat[].enabled` | bool | 是否启用 | `false` 时整条规则不生效 |
| `repeat[].max_times` | int | 最大保留次数 | 原始连续次数超过该值时只保留该次数 |
| `repeat[].interval.enabled` | bool | 是否启用分隔符 | 仅控制是否插入分隔符，不影响压缩与识别 |
| `repeat[].interval.min_consecutive` | int | 最小连续次数 | 原始连续次数达到该值时插入分隔符（按压缩前计数） |
| `repeat[].interval.separator` | string | 分隔符 | 插入在保留的重复词之间 |
| `replace[]` | object[] | 替换规则树 | 递归解析 |
| `replace[].type` | string | `group` / `correction` / `regex` | `group` 递归；`correction` 建映射；`regex` 空操作（`177-179`） |
| `replace[].word` | string | 分组名或正确词 | `correction` 的目标词 |
| `replace[].enabled` | bool | 是否启用 | `false` 时整棵子树跳过 |
| `replace[].items` | object[] | `group` 的子节点 | 仅 `group` 使用 |
| `replace[].source` | string[] | `correction` 的源词列表 | 建立“源词 → 正确词”映射 |

数据语义：

- 处理器的映射是**扁平**的：递归遍历所有启用的 `correction` 节点，最终只保留 `source → word` 一张表；分组层级只用于编辑和启用/禁用，不参与运行时匹配。
- 同一个 `source` 出现在多个 `correction` 节点时，后遍历到的会覆盖先前的目标词（`build_automaton.py:171-176`）。
- 删除词通过 `list(set(...))` 去重，顺序不稳定，但删除语义与顺序无关（`104-112`）。
- repeat 的压缩与分隔相互独立：外层 `enabled` 控制整条规则；`max_times` 控制保留次数；`interval.enabled` + `min_consecutive` 控制分隔符。重复次数按“词出现次数”计算（`哈哈哈哈` 中 `哈哈` 计 2 次）；处理在 delete/replace 之后，不改变敏感词计数（`build_automaton.py:122-161`、`260-313`）。
- 同一位置命中多个 repeat 规则时，`max_times` 小者优先，其次长词优先（`294-306`）。
- `default_subtitle_rules.json` 与 `build_automaton.py` 中的 `default_config` 是两份默认规则来源，内容近似但**未逐字比对**；修改默认规则时需要同步两处（`build_automaton.py:10`、`default_subtitle_rules.json`）。
- 规则 JSON 没有 `schema_version` 字段，也没有迁移机制。

### 6.6 `subtitle_rules.pkl` 缓存载荷

`_save_to_cache()` 写入以下键（`build_automaton.py:390-409`）：

| 键 | 内容 |
|---|---|
| `automaton` | `ahocorasick.Automaton` 实例（delete/replace） |
| `repeat_automaton` | `ahocorasick.Automaton` 实例（repeat），无规则时为 `None` |
| `repeat_rule_map` | 重复词 → `{max_times, interval}` 规则映射 |
| `delete_words` | 去重后的删除词列表 |
| `profanity_set` | 敏感词集合 |
| `replace_word_to_sources` | 正确词 → 源词列表 |
| `replace_source_to_word` | 源词 → 正确词 |
| `all_keywords` | 所有关键词（当前仅供缓存/调试） |
| `raw_config` | 原始规则 JSON |
| `json_content_hash` | 规则 JSON 规范化后的 SHA-256（`_calculate_json_hash()`） |
| `schema_version` | 缓存载荷结构版本，当前 `CACHE_SCHEMA_VERSION = 2` |

缓存有效性校验（`_load_from_cache()`，`354-388`）：载荷必须是 dict；`schema_version` 必须等于 `CACHE_SCHEMA_VERSION`；`json_content_hash` 必须等于当前规则 JSON 规范化后的 SHA-256（`json.dumps(json.loads(content), sort_keys=True, ensure_ascii=False)` 后计算，纯格式变化不失效）。任一不匹配、pkl 缺失/损坏或字段不完整时返回 `None`，`load_rules()` 自动重建并写回（`343-437`）。

### 6.7 运行时消息模型

**宿主 → 插件（stdin JSON）**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `output_path` | string | `cache/output` 的绝对路径 |
| `temp_path` | string | `cache/temp` 的绝对路径 |
| `pending_file_lists` | string[] | 当前待处理文件路径列表 |
| `event` | string | 按钮声明的事件名；无则为 `main` |

**插件 → 宿主（stdout JSON）**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `status` | string/bool | 插件自定义；关键词插件用 `"ok"`，`__init__.py` 错误时用 `false` |
| `processed` | int | 成功处理数量（不同插件口径不完全一致） |
| `completed_output_lists` | string[] | 处理后的文件路径，用于替换主程序 `FILE_LIST` |
| `popup` | bool/object | `false` 不弹窗；对象 `{title, message}` 由主程序弹窗 |

### 6.8 实体关系

```text
主程序 config.json
      │ 1
      │
      │ N
plugins/<dir>/manifest.json ──1──> 若干按钮（buttons[]）
      │
      ├── srt关键词替换 ──1──> subtitle_rules.json ──1──> subtitle_rules.pkl（缓存）
      │                              │
      │                              └── N 个规则节点（delete/repeat/replace）
      │
      ├── srt加前缀
      ├── ass转码透明底视频 ──依赖──> ffmpeg/bin/ffmpeg.exe（未随仓库提供）
      └── 测试插件
```

- 一个插件目录对应一个 `manifest.json`；一个 manifest 可声明多个按钮。
- 关键词插件只有一个工作规则文件和一份 pkl 缓存。
- 运行缓存与导出目录不是实体表，只是文件系统状态。

---

## 7. 接口清单

### 7.1 对外 API

**没有** HTTP、WebSocket、gRPC、消息队列等对外 API。所有接口都是本机进程协议/文件协议：

1. 主程序 ↔ 插件：stdin/stdout JSON；
2. 主程序 ↔ 插件安装包：zip + `manifest.json`；
3. 主程序 ↔ 文件系统：文件列表、缓存目录、导出目录。

### 7.2 插件请求接口（宿主 → 插件）

- 传输：子进程标准输入，UTF-8 文本，单个 JSON 对象后关闭 stdin。
- 构造位置：`软件本体/插件调度主程序.py:312-320`。

| 字段 | 必需 | 来源 | 说明 |
|---|---|---|---|
| `output_path` | 是 | `program_dir/cache/output` | 插件应把结果写到这里 |
| `temp_path` | 是 | `program_dir/cache/temp` | 临时文件目录 |
| `pending_file_lists` | 是 | 主程序全局 `FILE_LIST` | 待处理文件 |
| `event` | 否 | `manifest.buttons[].event` | 仅在按钮声明了 event 时添加 |

### 7.3 插件响应接口（插件 → 宿主）

- 传输：子进程标准输出，单个 JSON 对象；日志必须写 stderr。
- 解析位置：`软件本体/插件调度主程序.py:340-361`。

| 字段 | 类型 | 必需 | 宿主行为 |
|---|---|---|---|
| `status` | string/bool | 否 | 仅打印，不参与分支判断 |
| `processed` | int | 否 | 仅打印/展示 |
| `completed_output_lists` | string[] | 否 | 若存在，整体替换 `FILE_LIST` 并刷新列表 |
| `popup` | bool/object | 否 | 真值时弹窗；对象需含 `title`、`message` |

退出码约定：

| 退出码 | 含义 | 宿主行为 |
|---|---|---|
| `0` | 成功 | 解析 stdout JSON；无 JSON 时只打印 |
| 非 `0` | 失败 | 弹窗展示 stderr（过长则滚动） |

### 7.4 插件清单接口

插件目录必须满足：

1. 位于 `plugins/` 一级子目录；
2. 目录根部有 `manifest.json`；
3. manifest 声明的可执行文件存在（允许省略 `.py`/`.exe` 后缀）；
4. 多按钮时每个按钮有 `label` 与 `executable`。

按钮 `type` 的约定：

| type | 行为 |
|---|---|
| `script` | 启动子进程，传入 JSON 请求 |
| `config` | 用 `notepad.exe` 打开 `executable_path`（当前无插件使用） |

### 7.5 插件安装包接口

- 输入：zip 文件；根目录必须有 `manifest.json`。
- 必填字段：`name`、`version`；可选 `plugin_id`、`description`。
- 安装目标：`<program_dir>/plugins/<plugin_id or name>/`。
- 版本规则：新版本或未安装直接安装；相同/更低版本需用户确认重装。
- 安全校验：zip 成员路径会拒绝绝对路径与 `..`（`load_zip.py:125-128`）；但 `plugin_id` 本身未校验（见 11 节）。

### 7.6 内部关键函数/类

| 符号 | 位置 | 作用 | 输入/输出 |
|---|---|---|---|
| `get_path(relative_path=None, use_program_dir=True)` | `插件调度主程序.py:22-48`、`load_zip.py:10-36`、`common.py:8-34`、`ass转码透明底视频.py:18-44` | 统一路径解析 | 相对路径 → 绝对路径 |
| `parse_dropped_files(data)` | `插件调度主程序.py:68-79` | 解析 TkDND 拖放数据 | 原始字符串 → 路径列表 |
| `scan_plugins(plugins_dir=None)` | `插件调度主程序.py:112-205` | 扫描插件、解析 manifest | 插件目录 → 按钮信息列表 |
| `BuildLayout.build_layout()` | `插件调度主程序.py:208-295` | 组装主窗口布局 | 按钮列表 → PySimpleGUI layout |
| `run_script_plugin(btn_info, window)` | `插件调度主程序.py:298-372` | 启动插件并处理响应 | 按钮信息 → 更新文件列表/弹窗 |
| `move_all_files(src_dir, dst_dir)` | `插件调度主程序.py:375-387` | 导出并处理重名 | 目录 → 目录 |
| `import_plugin_list(zip_path_list)` | `load_zip.py:148-165` | 批量导入插件 | zip 列表 → `{success_list, failed_files}` |
| `SubtitleRuleProcessor.load_rules(force_rebuild=False)` | `build_automaton.py:280-294` | 加载/构建规则与自动机 | 无 → 初始化内部状态 |
| `SubtitleRuleProcessor.process_text(text)` | `build_automaton.py:212-233` | 删除/替换文本 | 原始文本 → 清理文本 |
| `SubtitleRuleProcessor.reset_profanity_count()` | `build_automaton.py:113-115` | 重置单文件计数 | 无 |
| `SubtitleRuleProcessor.get_profanity_count()` | `build_automaton.py:117-119` | 读取单文件计数 | 无 → int |
| `srt_keyword_editor.main(params)` | `srt_keyword_editor.py:63-139` | 关键词插件主流程 | 请求 dict → 写文件 + stdout JSON |
| `subtitle_rule_editor.run()` | `subtitle_rule_editor.py:852-857` | 启动 PyQt5 编辑器 | 无 → GUI |
| `add_char_to_srt(srt_path, char, output_path=None)` | `自动给srt加前缀.py:12-26` | 给 SRT 文本行加前缀 | 文件路径 → 输出文件 |
| `SubtitleProcessor.export_transparent_video(output_video_path, fps=60)` | `ass转码透明底视频.py:109-189` | 调 FFmpeg 生成透明 MOV | ASS 路径 → MOV 文件 |
| `PluginInstaller.check_version_and_install()` | `load_zip.py:84-118` | 比较版本并安装 | 无 → bool（但存在误报，见 11 节） |

### 7.7 协议示例

请求：

```json
{
  "output_path": "E:/tools/ReToolbox/cache/output",
  "temp_path": "E:/tools/ReToolbox/cache/temp",
  "pending_file_lists": ["E:/subs/ep01.srt"],
  "event": "main"
}
```

成功响应（关键词插件）：

```json
{
  "status": "ok",
  "processed": 1,
  "completed_output_lists": ["E:/tools/ReToolbox/cache/output/ep01.srt"],
  "popup": {
    "title": "文明小助手",
    "message": "删词统计:\n1. ep01 抓到 3 个敏感词\n..."
  }
}
```

失败响应（`__init__.py` 统一错误格式）：

```json
{
  "status": false,
  "popup": {
    "title": "返回消息",
    "message": "错误信息"
  }
}
```

---

## 8. 配置与环境

### 8.1 配置文件

| 文件 | 作用 | 读取方 | 写入方 | 注意事项 |
|---|---|---|---|---|
| `软件本体/config.json` | 主程序版本、日期、作者 | `插件调度主程序.py:50-55` | 人工 | 损坏/缺失时使用内嵌默认配置，不写回 |
| `plugins/*/manifest.json` | 插件元数据/按钮 | `scan_plugins`、`PluginInstaller` | 插件作者/安装包 | 无 schema 校验；坏 JSON 会让主程序启动失败 |
| `plugins/srt关键词替换/subtitle_rules.json` | 当前规则 | `SubtitleRuleProcessor._get_json` | 规则编辑器/人工 | 格式错误时会尝试复制默认规则；若仍失败则用内嵌默认并覆盖 |
| `plugins/srt关键词替换/default_subtitle_rules.json` | 默认规则模板 | 规则编辑器、处理器兜底 | 开发者 | 打包后位于只读资源目录 |
| `plugins/srt关键词替换/subtitle_rules.pkl` | 自动机缓存 | `_load_from_cache` | `_save_to_cache` | 仅按 mtime 判断有效性 |
| `plugins/srt关键词替换/plugin_log/` | 插件日志 | 人工 | `setup_logger` | 目录不存在时自动创建 |

### 8.2 环境变量

- 未发现任何 `os.environ` / `os.getenv` / `.env` 读取（全目录 grep 未命中）。
- 运行时行为主要由 `sys.frozen`、`sys.executable`、`sys._MEIPASS` 和当前工作目录/程序目录决定。
- 不需要配置 PATH 来定位 FFmpeg：ASS 插件按固定相对路径查找。

### 8.3 路径与打包环境

| 场景 | 程序目录 | 资源目录 | 说明 |
|---|---|---|---|
| 开发（脚本运行） | `插件调度主程序.py` 所在目录 | 同程序目录 | `sys.frozen` 为假 |
| PyInstaller 单文件运行 | `sys.executable` 所在目录 | `sys._MEIPASS`（临时解压） | 可写数据必须写到 exe 目录，不能写 `_MEIPASS` |
| 插件 exe | 插件 exe 所在目录 | 插件 exe 的 `_MEIPASS` | 规则工作文件、日志应在 exe 旁 |

主程序加载图标时显式使用 `use_program_dir=False`（`插件调度主程序.py:61`），配合 `--add-data "icon.ico;."` 从 `_MEIPASS` 读取；规则编辑器加载默认规则也使用 `False`（`subtitle_rule_editor.py:171`）。其余需要持久化的路径都用 `True`。

### 8.4 日志

- 关键词插件使用 `logging` + `RotatingFileHandler`：单文件 10 MB、保留 5 份（`common.py:70-86`）。
- `plugin_error.log` 始终记录 ERROR；`plugin_info.log` 仅在 manifest 的 `debug=true` 时记录 DEBUG 及以上（`common.py:54-59`、`78-86`）。
- 当前 `srt关键词替换/manifest.json:6` 设置了 `"debug": true`。
- 其他插件主要用 `print(..., file=sys.stderr)`，由主程序收集后显示/记录。
- 主程序的“日志”控件通过 `reroute_stdout=True` 接收自身 stdout（`插件调度主程序.py:228`）。

### 8.5 外部依赖：FFmpeg

- 期望路径：`<插件目录>/ffmpeg/bin/ffmpeg.exe`（Windows）。
- 代码检查：`os.path.exists(self.ffmpeg_path)`，不存在直接抛异常（`ass转码透明底视频.py:69`、`110-111`）。
- 仓库现状：`软件本体/plugins/ass转码透明底视频/ffmpeg/bin/` 存在但为空；git 未跟踪任何 ffmpeg 二进制（`git ls-files`）。
- 版本要求：代码使用 `color`、`subtitles`、`alpha`、`format` 滤镜与 `qtrle` 编码器，需要较完整的 FFmpeg 构建；具体最低版本**未确认**。

### 8.6 启动方式

| 场景 | 命令/操作 | 说明 |
|---|---|---|
| 开发运行主程序 | `python 软件本体/插件调度主程序.py` | 建议使用 `.venv/Scripts/python.exe`；从任意 cwd 启动均可，因为路径基于 `__file__` |
| 打包后运行 | 双击 `Re工具箱 - vX.Y.Z.exe` | 插件需为 `.exe`，否则打包模式无法启动 `.py` |
| 单独调试插件 | 向插件 stdin 传入请求 JSON | 插件按 `event` 分发；无 `event` 默认 `main` |
| 打开规则编辑器 | 主界面点击“修改配置” | 仅关键词插件提供；需要 PyQt5 |

### 8.7 网络与外部服务

- 无网络请求；不会检查更新、不会上传字幕。
- `config.json` 中的 B站/Q群/GitHub/DeepSeek URL 只是静态展示，未被代码请求。

---

## 9. 构建 / 运行 / 测试

### 9.1 开发环境准备

工作区已有一个 Python 3.11.9 的 `.venv`。仓库内没有正式依赖文件；按源码实际 import，最小依赖为：

```bash
# 在 E:/projects/ReToolbox 下
.venv/Scripts/python.exe -m pip install \
  pysimplegui==6.0 \
  tkinterdnd2==0.4.3 \
  pyahocorasick==2.3.1 \
  pyass==0.1.4 \
  packaging==26.1 \
  PyQt5==5.15.11 \
  pyinstaller==6.20.0
```

注意：

- `.venv/old_requirements.txt` 是 UTF-16 编码，列出了大部分依赖，但**没有 PyQt5**；同时包含源码未使用的 `pysub-parser`、`Unidecode`。
- 若只运行主程序 + 前缀/关键词插件，PyQt5 只在打开规则编辑器时需要；若打包关键词插件，PyQt5 必须安装。
- PySimpleGUI 6.0 的实际安装/授权方式**未确认**，新环境请以官方渠道为准。

### 9.2 运行

```bash
# 主程序（开发模式）
cd "E:/projects/ReToolbox"
.venv/Scripts/python.exe "Editing-tools-related-to-SRT-subtitles/软件本体/插件调度主程序.py"
```

插件在开发模式下由主程序用 `sys.executable` 启动，因此主程序必须运行在安装了依赖的 Python 环境中。

### 9.3 构建主程序

仓库给出的命令（`打包exe指令.txt:1`）：

```bash
pyinstaller --onefile --windowed -i "icon.ico" \
  --collect-all tkinterdnd2 \
  --hidden-import=tkdnd \
  --add-data "icon.ico;." \
  插件调度主程序.py \
  --name "Re工具箱 - v1.1.0"
```

注意：

- 命令中的版本名仍是 **v1.1.0**，与当前 `config.json` 的 1.3.0 不一致；实际打包前应更新 `--name`。
- 该命令假定在 `软件本体/` 目录内执行（`icon.ico` 与 `插件调度主程序.py` 为相对路径）。
- `--windowed` 会隐藏控制台；主程序对 `sys.stdin/stdout/stderr` 做了 `None` 保护并重定向到 GUI 日志（`插件调度主程序.py:13-19`、`228`）。

### 9.4 构建插件

仓库没有提供插件打包脚本或 `.spec` 文件。现有发布包显示：

- 关键词插件打包为 `__init__.exe`（与 manifest 的 `executable: "__init__"` 对应）；
- 前缀插件打包为 `自动给srt加前缀.exe`；
- 测试插件打包为 `__init__.exe` 或 `test.exe`（不同版本命名不完全一致）。

因此可以推断插件也是 PyInstaller 单文件打包，但**具体命令、`--add-data` 参数（规则默认文件/FFmpeg）、版本命名规则均未确认**。若要重新打包，需要至少保证：

1. 插件 exe 文件名与 manifest 的 `executable` 匹配（可省略 `.exe`）；
2. 关键词插件的 `default_subtitle_rules.json` 被打进资源目录（`use_program_dir=False` 能读到）；
3. ASS 插件 exe 旁边保留 `ffmpeg/bin/ffmpeg.exe`，或修改路径策略；
4. PyQt5 相关 DLL 被正确收集。

### 9.5 测试现状

> 2026-10-22 更新：已建立 pytest 框架并固化 5 组回归。以下前两条为勘察期结论，保留原记述；当前状态见本节末尾「当前状态」。

- **（勘察期结论，已不成立）没有自动化测试**：未发现 `tests/`、pytest/unittest 用例、CI 配置。
- 存在若干临时/手工测试入口：
  - `软件本体/plugins/srt关键词替换/build_automaton.py:302-313` 的 `test()`：用固定文本验证删除/计数；仅 `__main__` 时执行。
  - `软件本体/plugins/ass转码透明底视频/ass转码透明底视频.py:193-198` 的 `test()`：读取 `test.ass` 并生成 `output.mov`；但 `__main__` 实际调用的是 `main()`（`268-269`），需要手工调用 `test()`。
  - `软件本体/plugins/测试插件/` 提供“测试弹窗”“测试报错”两个按钮；后者会 `raise KeyboardInterrupt`（`测试插件/__init__.py:68-70`），用于验证异常链路。
- 本次勘察未运行上述测试，功能正确性**未验证**。

**当前状态（2026-10-22）**：

- 已建立 `tests/`（pytest，60 项用例，`pytest==9.1.1` 记录在 `requirements-dev.txt`），运行基准 `pytest tests/`，当前 **59 passed / 1 skipped**（SKIP 为环境无法模拟目录不可写）。
- `tests/conftest.py` 通过 `importlib` 按路径加载被测模块以兼容中文目录；`load_zip` 的 `get_path` 与弹窗在 fixture 内 monkeypatch，规则 JSON/pkl 全部限制在 `tmp_path`，因此测试不读写仓库内运行产物。
- 覆盖范围：`test_installer.py`（安装器三态与路径越界）、`test_installer_failures.py`（真实清理/解压失败）、`test_repeat.py`（repeat 语义与真实规则回归）、`test_cache.py`（pkl 缓存校验链）。插件导入、repeat 与主程序缓存的 **GUI/真机手工冒烟**已于 2026-10-22 由作者在真机执行通过（插件导入三态与重装询问、规则编辑器 + 真实 `subtitle_rules.pkl` 命中/失效、主程序连续处理与修改 JSON 后自动重建），`TODO.md`「测试补强」已随之清空。
- 仍无 CI 配置；上述手工入口照旧存在。

### 9.6 建议的冒烟测试清单

| 检查项 | 操作 | 预期 |
|---|---|---|
| 启动 | 开发模式启动主程序 | 窗口出现，底部显示 1.3.0，插件按钮按类别分组 |
| 插件发现 | 查看 `srt加前缀`、`srt关键词替换`、`测试插件`、`ass转码透明底视频` | 四个插件均出现（ass 插件即使无 FFmpeg 也应能被扫描） |
| 拖拽 | 拖入 1 个 SRT + 路径含空格的 SRT | 列表出现两项且路径完整 |
| 前缀 | 点击“srt加前缀”后导出 | 字幕文本前有 `文件名：` |
| 关键词 | 点击“srt关键词替换” | 敏感词被删，弹窗显示统计 |
| 规则编辑器 | 点击“修改配置”，新增一条替换，保存 | JSON 更新；再次处理时生效 |
| 缓存 | 连续执行两个 SRT 插件 | 第二个插件处理的是第一个插件的输出 |
| 导出 | 点击“导出并打开位置” | `output/` 出现文件，资源管理器打开 |
| 插件导入 | `导入插件` 选择发布 zip | 版本确认后安装、按钮出现；仅在真正装上插件时重建窗口（失败/取消重装不重建） |
| ASS | 准备 ffmpeg 后处理 `test.ass` | 生成带透明通道的 `.mov` |

### 9.7 常见故障对照

| 现象 | 可能原因 | 处理 |
|---|---|---|
| `ModuleNotFoundError: ahocorasick` | 未安装 pyahocorasick | 安装 `pyahocorasick` |
| `ModuleNotFoundError: PyQt5` | 依赖清单缺少 PyQt5 | 安装 `PyQt5` |
| `不是, 你 FFmpeg 呢` | `ffmpeg/bin/ffmpeg.exe` 不存在 | 放置 FFmpeg 或修改路径 |
| 打包后点击插件没反应 | 打包模式只接受插件 exe，源码目录里是 `.py` | 打包插件或使用开发模式 |
| 规则修改后不生效 | pkl 缓存未按当前 JSON 失效（哈希/schema 校验异常）或缓存读写失败 | 检查哈希/schema 版本，或删除 pkl、调用 `rebuild_cache(force_rebuild=True)` 强制重建 |
| 导入插件后报错/目录异常 | manifest 的 `plugin_id` 含路径字符，或版本号非法 | 检查 manifest，见 11 节 |
| 面板没有按钮 | manifest 缺少/损坏，或可执行文件不存在 | 查看控制台/日志中的 `警告` |
| ASS 输出失败 | FFmpeg 编码器缺失、字体/字幕路径问题 | 查看 `cache/temp/ffmpeg-*.log` |

---

## 10. 代码规范与约定

### 10.1 命名与组织

| 维度 | 约定/现状 | 依据 |
|---|---|---|
| 文件/目录命名 | 插件目录、脚本大量使用中文名称；主程序文件为中文 | `软件本体/` 目录树 |
| 函数/变量 | `snake_case`（如 `scan_plugins`、`run_script_plugin`、`pending_file_lists`） | 主程序、插件源码 |
| 类名 | `PascalCase`（`PluginInstaller`、`SubtitleRuleProcessor`、`BuildLayout`） | `load_zip.py:38`、`build_automaton.py:56`、`插件调度主程序.py:208` |
| 常量 | 全大写（`FILE_LIST`、`VISION`、`COFFEE_QR_BASE64`） | 主程序 |
| 事件名 | 小写下划线（`main`、`test2`、`subtitle_rule_editor`） | manifest 与 `__init__.py` |
| 私有方法 | 前导下划线（`_get_json`、`_build_automaton`、`_resolve_overlaps`） | `build_automaton.py` |
| 中文注释/文案 | 大量口语化中文提示、错误信息 | 全项目 |

### 10.2 编码与文本

- 源码/JSON 统一 UTF-8；ASS 读取使用 `utf-8-sig`（`ass转码透明底视频.py:82`、`97`）。
- 插件入口普遍显式 `reconfigure(encoding='utf-8')`，避免 Windows 默认 GBK 导致 JSON 中文乱码（`srt关键词替换/__init__.py:8-10`、`自动给srt加前缀.py:7-9`）。
- 输出 JSON 使用 `ensure_ascii=False`，保留中文。
- 主程序在 `--windowed` 下对 `None` 标准流做保护（`插件调度主程序.py:13-19`）。

### 10.3 插件协议约定

- 插件必须从 stdin 读 JSON、向 stdout 写 JSON；日志写 stderr。
- 处理结果必须通过 `completed_output_lists` 返回，否则主程序的文件列表不会更新。
- 需要提示用户时使用 `popup` 对象；不需要时用 `false`。
- 插件不应直接操作主程序的 `FILE_LIST` 或 GUI。
- 插件应自行过滤支持的扩展名；主程序不过滤。

### 10.4 UI/日志风格

- 主程序是单窗口、同步阻塞式交互：点击按钮后界面会等待插件结束（没有进度条/取消）。
- 日志控件用于显示主程序自身 stdout；插件 stderr 通过弹窗展示。
- 错误信息风格口语化、直接（如“一个文件都不传, 处理个蛋啊”），正式产品化时可考虑统一错误码/文案。

### 10.5 Git 约定与任务工作流

#### 仓库范围

- git 仓库位于 `Editing-tools-related-to-SRT-subtitles/`，分支 `main`，
  remote `git@github.com:100210110/Editing-tools-related-to-SRT-subtitles.git`。
- **工作区根目录不是 git 仓库**；但**项目文档随代码入库**：
  `docs/`（含 `AI_CONTEXT.md`、`TODO.md`、`CHANGELOG.md`）已迁入
  `Editing-tools-related-to-SRT-subtitles/docs/`，由 git 跟踪。
- 仓库外的工作区目录——`v1.0.0/`、`v1.1.0/`、`v1.1.0b/`、`v1.2.0/`、`v1.3.0/`、`v1.3.0b/`、
  `发布zip/`、`.venv/`、`打包exe指令.txt`——**不在 git 仓库内**，不参与提交，
  在文档中仍以工作区根为基准引用。
- 当前 HEAD 领先 `origin/main` 1 个提交；没有分支策略、PR 模板、CI 或版本标签。

#### 提交信息风格

- 采用 `feat:` / `fix:` / `docs:` 前缀 + 中文描述，例如：
  - `5ff5463 feat: 窗口size由固定改为自动`
  - `b93b90b feat: 字幕替换规则与自动机更新`
  - `129fca5 fix: 修复在重启刷新后未同步刷新显示列表的错误`
  - `docs: 初始化交接文档（AI_CONTEXT / TODO / CHANGELOG）`
- 一次任务对应一条提交；不混合无关改动，不夹带格式化/重构。

#### 任务前置检查（每次任务第 0 步，必须执行）

每次任务开始、**修改任何文件之前**，AI 必须执行：

```bash
git -C "Editing-tools-related-to-SRT-subtitles" diff --cached --quiet
```

- **返回 0（暂存区为空）**：正常继续任务。
- **返回非 0（暂存区非空）**：**立即中断**，不读取、不修改、不暂存任何文件，
  只输出以下提醒并等待人工处理：

  ```
  ⚠️ 暂存区非空，上次修改尚未提交，为避免混批已中断本次任务。
  请先处理（任选其一）：
  - 人工在 IDE 审查并 git commit
  - git -C "Editing-tools-related-to-SRT-subtitles" reset 撤销暂存
  处理完成后请重新发起本次任务。
  ```

  提醒中附 `git -C "Editing-tools-related-to-SRT-subtitles" status --short` 输出，
  便于人工判断是哪一批改动。

- **例外**：任务本身明确要求"承接上次未提交改动"时，人工须在提示词中显式声明
  `跳过前置检查`，AI 才可继续；否则一律按上述规则中断。

- **未跟踪文件（`??`）不阻塞**；工作区未暂存的已跟踪修改（` M`）同样不阻塞，
  但 AI 应在汇报中提示"工作区存在未暂存修改，本次未触碰"。

#### 每次任务的 Git 工作流（AI 执行，人工验收）

1. **AI 只 `git add`，不 `git commit`、不 `git push`。**
2. **只暂存本次任务涉及的文件**，不带入其他未提交改动；代码与 docs 一起暂存。
   仓库外的 `v1.x/`、`发布zip/`、`.venv/` 不会被 `git add` 到（它们在仓库外）。
3. **AI 在任务汇报中给出建议 commit message**（格式见上），并附
   `git -C "Editing-tools-related-to-SRT-subtitles" status --short` 的暂存结果。
4. **人工在 IDE 中直接审查暂存 diff 并执行 `git commit`。**
   - AI **不在对话框中输出完整 diff**；仅对复杂核心逻辑摘取代码片段或说明改动逻辑。
5. 人工拒绝本次提交时，需告知 AI 回滚代码与 docs 变更（两者同批）。

#### docs 维护约定

- `docs/TODO.md`：只记未完成项；大项全部完成后整节移入 `CHANGELOG.md`，
  编号永久占用、不复用、不重排；「当前最大编号」写在文首。
- `docs/CHANGELOG.md`：只记已完成变更，按时间倒序；与本次代码提交同批记录，
  人工审查时一并核对。
- `docs/AI_CONTEXT.md`：作为静态诊断快照，**仅在结构性变化时更新**；
  修复细节不入本文，进 CHANGELOG。
- docs 随代码走同一次提交，不做独立的 docs 提交（除非本次任务只涉及文档）。

#### AI_CONTEXT §11 修复标注
- §11 条目修复后，在「问题」列描述末尾加 `（已修复，见 CHANGELOG [YYYY-MM-DD]）`
- 不删除、不改写原诊断内容，保留快照性质
- 日期取 CHANGELOG 中对应修复条目的小节日期
- §11 标题下方的说明块末尾补一句：「已修复条目在问题描述末尾括注」

### 10.6 工程规范缺口

- 无 linter/formatter 配置（flake8、ruff、black、prettier 等）。
- 无类型检查配置；少量类型标注（`List[str]`、`Dict[str, dict]`）但不完整。
- 无统一依赖清单、无锁文件、无 `pyproject.toml`。
- `get_path()` 在四个文件中重复实现，默认参数不一致。
- 业务常量（默认规则）在代码与 JSON 中重复维护。

---

## 11. 已知问题与技术债

> 级别为交接评估建议，不代表原作者的优先级。所有问题均来自静态阅读，未做运行时复现。
> 已修复条目在问题描述末尾括注。

| 级别 | 问题 | 位置/证据 | 影响与建议 |
|---|---|---|---|
| 高 | **插件安装路径可被 manifest 的 `plugin_id` 带出 `plugins/`**：`plugin_path = get_path(f'plugins\\{plugin_id}')`，未校验 `..`/绝对路径；安装前直接 `shutil.rmtree(self.plugin_path)`（已修复，见 CHANGELOG [2026-10-22]） | `软件本体/load_zip.py:74-77`、`121-130` | 导入不可信 zip 可能删除/覆盖插件目录之外的路径。建议限制 `plugin_id` 为安全字符集，并用 `os.path.realpath` 校验目标位于 `plugins/` 下 |
| 高 | **安装失败仍返回成功**：`install()` 捕获异常后只弹窗，不返回 False；`check_version_and_install()` 随后无条件 `return True`（已修复，见 CHANGELOG [2026-10-22]） | `软件本体/load_zip.py:117-118`、`121-134`、`157-161` | 主程序会把失败 zip 从列表移除并提示安装成功。建议让 `install()` 返回 bool/抛异常，并据此更新结果 |
| 中 | **`repeat` 规则完全未生效**：编辑器可增删改并保存，但 `_parse_repeat_config()` 是 `pass` 且从未被 `load_rules()` 调用；AC 自动机只加入 delete/replace（已修复，见 CHANGELOG [2026-10-22]） | `软件本体/plugins/srt关键词替换/build_automaton.py:121-123`、`161-173`、`280-289`；`subtitle_rule_editor.py:315-327`、`508-550` | 用户会以为“重复词压缩”已生效。建议实现、或在编辑器中明确标注“未启用/预留”并禁用 |
| 中 | **`regex` 节点空操作** | `软件本体/plugins/srt关键词替换/build_automaton.py:177-179` | 规则中的 regex 配置不会生效，且没有提示。建议实现或从 schema/编辑器中移除 |
| 中 | **pkl 缓存只按 mtime 判断，且被 git 跟踪**（已修复，见 CHANGELOG [2026-10-22]） | `build_automaton.py:339-347`；`git ls-files` 显示 `subtitle_rules.pkl` 入库 | git checkout 后 pkl 的 mtime 往往比 JSON 新，可能加载旧规则；代码升级也不会自动失效。建议使用内容哈希/版本号，移除 pkl 出库，并在启动时校验 |
| 中 | **无正式依赖清单**：仓库没有 `requirements.txt`/`pyproject.toml`；`.venv/old_requirements.txt` 缺少 PyQt5，且包含未使用包 | `.venv/old_requirements.txt`；`subtitle_rule_editor.py:5-11`；`pysub-parser`/`Unidecode` 未被 import | 新环境难以复现，规则编辑器容易因缺 PyQt5 失败。建议整理最小依赖清单并区分 runtime/dev/build |
| 中 | **README 与当前实现不一致**：README 说 `config.json` 是删改词配置、格式错误会被覆盖；实际规则在 `subtitle_rules.json`，且 `config.json` 只用于版本/作者 | `Editing-tools-related-to-SRT-subtitles/README.md:14-20`；`软件本体/plugins/srt关键词替换/build_automaton.py:58-59` | 用户按 README 改错文件，规则不会生效。建议更新 README，补充规则编辑器、导出、导入插件、ASS 插件 |
| 中 | **ASS 插件缺少 FFmpeg**：代码要求 `ffmpeg/bin/ffmpeg.exe`，仓库该目录为空，发布包中也未发现 FFmpeg | `软件本体/plugins/ass转码透明底视频/ass转码透明底视频.py:69`；目录清单 | 源码环境下 ASS 功能不可用。建议文档说明外部依赖，或在发布包中附带并校验版本 |
| 中 | **ASS 插件未出现在现有发布产物** | `v1.x/plugins` 与 `发布zip/` 清单均无该插件 | 功能是否对用户发布、如何分发**未确认**；接手时需确认发布策略 |
| 中 | **主界面在插件运行期间阻塞**：`proc.communicate()` 在 UI 事件循环内同步等待，无超时、无取消、无进度 | `软件本体/插件调度主程序.py:330-337`、`485-587` | ASS 渲染或大批量 SRT 时窗口“无响应”。建议改为线程/进程异步 + 进度回传，或至少加忙碌提示 |
| 中 | **SRT 前缀插件假设固定四行结构**：`range(2, len(lines), 4)`，多行字幕会错位；重复运行会叠加前缀；`processed` 统计的是输入数而非成功数 | `软件本体/plugins/srt加前缀/自动给srt加前缀.py:19-20`、`50-74` | 真实字幕（多行、样式标签、缺空行）可能被破坏。建议按空行分块解析，并记录成功数 |
| 中 | **同名文件在缓存中互相覆盖**：两个插件都写 `cache/output/<basename>`；不同目录的同名 SRT 会覆盖 | `srt_keyword_editor.py:104-108`；`自动给srt加前缀.py:55-61`；`插件调度主程序.py:375-387` | 链式处理方便，但批量处理多目录时可能丢结果。建议保留相对路径或加哈希前缀 |
| 低 | **损坏的 manifest 会让主程序启动崩溃**：`scan_plugins` 直接 `json.load`，无 try/except；`init_program` 也没有捕获 | `软件本体/插件调度主程序.py:130-134`、`438-452` | 一个插件配置写错会阻止整个工具启动。建议逐个 manifest 捕获异常并跳过/提示 |
| 低 | **`scan_plugins()` 重复调用** | `软件本体/插件调度主程序.py:438`、`448` | 多一次扫描，当前无功能影响；可删除一次 |
| 低 | **最长匹配只在同起点时成立**：排序后线性过滤，起点更早的短词可能先占位 | `软件本体/plugins/srt关键词替换/build_automaton.py:175-191` | 某些重叠词删除/替换结果不符合“长词优先”直觉。建议用区间调度/优先队列选择全局最优 |
| 低 | **不同节点的相同 `source` 后者覆盖前者**，编辑器只防单 item 内重复 | `build_automaton.py:133-138`；`subtitle_rule_editor.py:108-115` | 规则冲突不易发现。建议保存时做全局冲突检测 |
| 低 | **打包后“新建”规则文件路径可能指向只读临时目录**：`os.path.dirname(__file__)` | `subtitle_rule_editor.py:214-218` | 单文件 exe 下 `__file__` 位于 `_MEIPASS`，可能无法保存；**未在打包环境验证** |
| 低 | **规则编辑器退出用 `sys.exit`，`__init__.py` 的 `except Exception` 捕获不到 `SystemExit`** | `subtitle_rule_editor.py:852-857`；`srt关键词替换/__init__.py:66-90` | 编辑器关闭后主程序可能收不到 JSON，但不影响退出码 0；建议统一返回/输出协议 |
| 低 | **`test_plugins_list()` 是失效/有缺陷的测试入口**：循环结束后只安装最后一个插件，空列表时 `plugin_zip` 未定义；主程序未使用该函数 | `load_zip.py:137-145` | 容易误用。建议删除或改为正式测试 |
| 低 | **测试插件用 `raise KeyboardInterrupt` 模拟错误** | `软件本体/plugins/测试插件/__init__.py:68-70` | `KeyboardInterrupt` 不是 `Exception`，会走 Python 默认 traceback；仅调试用途 |
| 低 | **仓库卫生**：`cache/temp/ffmpeg-*.log` 与 `subtitle_rules.pkl` 被跟踪；`plugin_log/` 未跟踪且无 `.gitignore` | `git ls-files`、`git status` | 运行产物/缓存入库，日志可能误提交。建议添加 `.gitignore`，清理已跟踪的缓存 |
| 低 | **拖放路径解析在无花括号时按空格拆分** | `软件本体/插件调度主程序.py:68-79` | 某些来源的含空格路径会被拆坏；TkDND 通常会给含空格路径加花括号，风险有限 |
| 低 | **日志语句缺少 f-string**：`logger.info("params: {str(params)}")` | `软件本体/plugins/srt关键词替换/srt_keyword_editor.py:71` | 日志记录了字面量而不是参数，影响排查 |
| 低 | **FFmpeg 以 `CREATE_NEW_CONSOLE` 启动并带 `-report`** | `ass转码透明底视频.py:141`、`156-164` | 可能闪控制台，且在 `cache/temp` 留下 ffmpeg 日志；建议 `CREATE_NO_WINDOW` 并清理日志 |

### 11.1 建议的优先修复顺序

1. **先修安装器安全与正确性**：`plugin_id` 路径校验、`install()` 返回值、`check_version_and_install()` 结果传递。
2. **明确规则能力边界**：`repeat` 已实现；剩余 `regex` 需实现或在 UI/文档中标记为未启用，避免用户误解。
3. **缓存与依赖可复现**：增加 `requirements.txt`，移除 pkl/日志出库，加入 schema/内容哈希。
4. **更新 README**：以 `subtitle_rules.json` 和规则编辑器为准，补全导入/导出/ASS 说明。
5. **改善长任务体验**：插件异步执行、进度/取消、超时；至少避免 UI 假死。
6. **补最小回归测试**：为规则解析、重叠处理、前缀插入、插件协议各写 1-2 个单元测试。

---

## 12. 阅读路线建议

### 12.1 新人/接手者路线

| 阶段 | 阅读对象 | 目标 | 预计 |
|---|---|---|---|
| 0. 建立全局印象 | `Editing-tools-related-to-SRT-subtitles/README.md`、`软件本体/config.json`、第 1-4 节 | 知道工具做什么、工作区哪些是源码/产物 | 10 分钟 |
| 1. 主程序骨架 | `软件本体/插件调度主程序.py:22-48`（路径）、`112-205`（插件扫描）、`298-372`（调度）、`423-590`（初始化/事件循环） | 理解 UI 与插件如何连接 | 30 分钟 |
| 2. 最简插件样板 | `软件本体/plugins/srt加前缀/manifest.json`、`自动给srt加前缀.py:1-79` | 掌握 stdin/stdout JSON 协议 | 10 分钟 |
| 3. 关键词插件（核心） | `plugins/srt关键词替换/__init__.py` → `common.py` → `build_automaton.py:56-298` → `srt_keyword_editor.py:63-139` | 理解规则解析、AC 自动机、缓存、统计 | 60-90 分钟 |
| 4. 规则编辑器（按需） | `plugins/srt关键词替换/subtitle_rule_editor.py:19-153`（对话框）、`156-345`（树）、`482-754`（增删改）、`852-857`（入口） | 理解规则 JSON 的可视化维护 | 45 分钟 |
| 5. ASS 插件 | `plugins/ass转码透明底视频/ass转码透明底视频.py:47-189` | 理解 pyass 与 FFmpeg 滤镜/编码 | 30 分钟 |
| 6. 安装与发布 | `软件本体/load_zip.py`、`打包exe指令.txt`、`发布zip/` 清单 | 理解插件分发、版本比较、打包差异 | 30 分钟 |
| 7. 历史对照（可选） | `v1.1.0b/`、`v1.2.0/`、`v1.3.0/` 中的旧源码/发布包 | 追溯命名/协议演进 | 按需 |

### 12.2 AI 助手接手检查清单

1. **先读协议再改代码**：任何插件改动都必须保持 `stdin JSON → stdout JSON`、日志走 stderr、`completed_output_lists` 更新文件列表。
2. **不要直接修改 pkl**：它只是缓存；改规则后删除 pkl 或强制 `rebuild_cache`，否则可能被 mtime 误判。
3. **区分开发/打包路径**：`sys.frozen` 为真时，插件必须是 exe；写文件用程序目录，不要写 `_MEIPASS`。
4. **任何安装器改动都要校验路径**：`plugin_id`、zip 成员、目标目录三者都要限制在 `plugins/` 下。
5. **改规则 schema 时同步三处**：`subtitle_rules.json`、`default_subtitle_rules.json`、`build_automaton.py` 的 `default_config`，并更新编辑器。
6. **改 UI 前确认线程模型**：当前是同步阻塞；若引入异步，注意 PySimpleGUI 的线程安全与窗口重建逻辑。
7. **先跑冒烟清单再改**：本次未运行 GUI，任何“已修复”的结论都需要实际启动/执行插件验证。
8. **保持中文路径兼容**：项目大量使用中文目录/文件名，涉及 zip 解压、subprocess 参数、FFmpeg 字幕路径时要显式指定 UTF-8。

### 12.3 最小上下文包（时间有限时）

如果只能读 5 个文件，建议按顺序：

1. `软件本体/插件调度主程序.py`（尤其 112-205、298-372、423-590）
2. `软件本体/plugins/srt加前缀/自动给srt加前缀.py`（协议样板）
3. `软件本体/plugins/srt关键词替换/build_automaton.py`（核心算法）
4. `软件本体/plugins/srt关键词替换/srt_keyword_editor.py`（批处理流程）
5. `软件本体/plugins/srt关键词替换/manifest.json`（多按钮/事件约定）

---

## 附录 A：未确认项清单

| 编号 | 未确认项 | 原因/需要如何确认 |
|---|---|---|
| A1 | GUI 实际运行行为、拖拽兼容性、按钮布局 | 本次只做静态阅读，未启动 GUI |
| A2 | ASS 插件端到端输出是否正确（透明通道、时长、字体渲染） | 缺少 FFmpeg，未实际渲染 |
| A3 | 插件 exe 的准确 PyInstaller 命令、`--add-data` 与依赖收集方式 | 仓库无插件打包脚本/`.spec`；仅能从发布包推断 |
| A4 | ASS 插件是否曾发布、通过何种渠道分发 | 现有 `v1.x/` 与 `发布zip/` 均未发现该插件 |
| A5 | FFmpeg 的最低版本要求与推荐构建 | 代码只调用滤镜/编码器，未声明版本 |
| A6 | PySimpleGUI 6.0 的授权/安装限制 | 未查阅官方许可；新环境安装前需确认 |
| A7 | 打包后规则编辑器“新建/保存”的实际路径行为 | 依赖 PyInstaller 单文件模式的 `__file__` 行为，未实测 |
| A8 | `default_subtitle_rules.json` 与 `build_automaton.py` 内嵌默认配置是否逐字一致 | 内容近似，未做 diff 比对 |
| A9 | 旧版 `v1.0.0/v1.1.0b` 源码与当前实现的完整差异 | 仅抽查了目录与部分文件，未逐行 diff |
| A10 | `plugin_log/` 是否应纳入版本管理、日志保留策略 | 当前无 `.gitignore`，需作者确认 |
| A11 | 是否存在未提交到工作区的测试/部署脚本 | 工作区与 git 仅显示现有 31 个跟踪文件；外部环境未知 |
| A12 | “文明小助手”统计口径是否符合业务预期（按匹配次数而非文件数） | 代码明确按匹配次数计数，但业务意图未文档化 |

## 附录 B：本次勘察读取的主要文件

| 文件 | 读取范围 | 用途 |
|---|---|---|
| `软件本体/插件调度主程序.py` | 全文 590 行 | 主程序架构、UI、调度、导入/导出 |
| `软件本体/load_zip.py` | 全文 172 行 | 插件安装、版本比较、路径校验 |
| `软件本体/config.json` | 全文 | 版本/作者信息 |
| `软件本体/plugins/srt加前缀/manifest.json`、`自动给srt加前缀.py` | 全文 | 最简插件协议 |
| `软件本体/plugins/srt关键词替换/manifest.json` | 全文 | 多按钮/事件 |
| `软件本体/plugins/srt关键词替换/__init__.py` | 全文 89 行 | 事件分发、统一错误输出 |
| `软件本体/plugins/srt关键词替换/common.py` | 全文 89 行 | 路径、日志 |
| `软件本体/plugins/srt关键词替换/build_automaton.py` | 全文 368 行 | 规则解析、AC 自动机、缓存 |
| `软件本体/plugins/srt关键词替换/srt_keyword_editor.py` | 全文 146 行 | 批处理主流程、统计 |
| `软件本体/plugins/srt关键词替换/subtitle_rule_editor.py` | 全文 862 行 | PyQt5 规则编辑器 |
| `软件本体/plugins/srt关键词替换/subtitle_rules.json`、`default_subtitle_rules.json` | 结构与统计 | 规则数据模型 |
| `软件本体/plugins/ass转码透明底视频/manifest.json`、`ass转码透明底视频.py` | 全文 268 行 | ASS 处理、FFmpeg 调用 |
| `软件本体/plugins/测试插件/manifest.json`、`__init__.py`、`test.py`、`test_1.py` | 全文 | 协议/异常测试 |
| `Editing-tools-related-to-SRT-subtitles/README.md` | 全文 23 行 | 用户说明与现状对照 |
| `Editing-tools-related-to-SRT-subtitles/LICENSE` | 头部 | 许可证 |
| `打包exe指令.txt` | 全文 | 构建命令 |
| `.venv/pyvenv.cfg`、`.venv/old_requirements.txt` | 全文 | Python/依赖版本 |
| `发布zip/`、`v1.x/` 目录与 zip 清单 | 目录/清单抽查 | 发布产物与版本关系 |
| git 仓库 | `git log`、`git status`、`git ls-files`、`git remote -v` | 版本/提交/跟踪文件 |

## 附录 C：快速命令备忘

```bash
# 进入工作区
cd "E:/projects/ReToolbox"

# 查看仓库状态
git -C "Editing-tools-related-to-SRT-subtitles" status --short
git -C "Editing-tools-related-to-SRT-subtitles" log --oneline -10

# 启动主程序（开发模式）
.venv/Scripts/python.exe "Editing-tools-related-to-SRT-subtitles/软件本体/插件调度主程序.py"

# 查看关键词插件日志
tail -n 50 "Editing-tools-related-to-SRT-subtitles/软件本体/plugins/srt关键词替换/plugin_log/plugin_error.log"

# 强制重建规则缓存（在 Python 中）
# from build_automaton import SubtitleRuleProcessor
# p = SubtitleRuleProcessor(); p.load_rules(force_rebuild=True)

# 清理本地缓存（谨慎；会删除未导出的处理结果）
# rm -rf "Editing-tools-related-to-SRT-subtitles/软件本体/cache/output/"*
```

---

**交接结论**：该项目结构小巧、插件边界清晰，最值得保留的设计是“manifest 驱动 + stdin/stdout JSON + 缓存式链式处理”；最需要优先处理的是插件安装器的路径/返回值安全、`regex` 能力与文档不一致、pkl 缓存失效策略，以及缺失的依赖/测试基础设施。建议接手后先按 9.6 做一次完整冒烟，再按 11.1 的顺序逐步修复。
