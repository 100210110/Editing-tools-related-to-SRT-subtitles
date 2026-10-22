# 变更日志

> 本文件记录**功能级 / 结构级**变更；日常小修小补由 git log 承担。
> 另：**检查 / 收尾类任务即使没有代码变更，也记录结论**，避免日后无法判断是否需要重新检查。
> 分工：本文件只记录**已完成**的变更，未完成的任务统一见 `TODO.md`。
> 格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，按时间倒序，最新在最上面。
> 已完成的事项从 `TODO.md` 迁移至此。

---

## [未发布]

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

- TODO 初始化后完成前两项修复（#1 插件安装路径穿越、#2 安装失败仍报成功）；其余 22 项待办不变。
