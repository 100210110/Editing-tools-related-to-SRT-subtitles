"""规则编辑器"新建"落盘路径回归测试（TODO #17）。

历史问题：`new_file()` 用 `os.path.dirname(__file__)` 拼工作文件路径。单文件 exe 下
`__file__` 位于 PyInstaller 的 `_MEIPASS` 临时目录（只读、每次启动重建），
"新建 → 保存"会写进临时目录或直接失败。现在统一走 `get_path(use_program_dir=True)`。
"""
import os
import sys

import pytest


def test_default_working_path_uses_plugin_dir(rule_editor_module):
    path = rule_editor_module.default_working_path()

    assert path.endswith("subtitle_rules.json")
    assert os.path.dirname(path) == rule_editor_module.get_path(use_program_dir=True)


def test_default_working_path_follows_executable_when_frozen(rule_editor_module, tmp_path, monkeypatch):
    """打包后必须指向 exe 所在目录，不能是只读的 _MEIPASS。"""
    program_dir = tmp_path / "program"
    meipass_dir = tmp_path / "meipass"
    program_dir.mkdir()
    meipass_dir.mkdir()

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(program_dir / "ReToolbox.exe"), raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(meipass_dir), raising=False)

    path = rule_editor_module.default_working_path()

    assert path == str(program_dir / "subtitle_rules.json")
    assert str(meipass_dir) not in path


def test_new_file_targets_program_dir(rule_editor_module, qt_app, tmp_path, monkeypatch):
    """“新建”设置的工作文件必须是程序目录下的规则文件。"""
    messages = []
    monkeypatch.setattr(
        rule_editor_module.QMessageBox, "information", lambda *a, **k: messages.append(a)
    )
    monkeypatch.setattr(
        rule_editor_module.QMessageBox, "critical", lambda *a, **k: messages.append(a)
    )

    editor = rule_editor_module.SubtitleEditor()
    try:
        editor.new_file()
        assert editor.current_file == rule_editor_module.default_working_path()
        assert editor.current_file.endswith("subtitle_rules.json")
        assert messages, "新建后应给出提示"
    finally:
        editor.close()


def test_save_failure_suggests_save_as(rule_editor_module, qt_app, tmp_path, monkeypatch):
    """目标不可写时（这里用目录路径触发 OSError），提示要引导用户改用“另存为”。"""
    critical_messages = []
    monkeypatch.setattr(
        rule_editor_module.QMessageBox, "information", lambda *a, **k: None
    )
    monkeypatch.setattr(
        rule_editor_module.QMessageBox, "critical", lambda *a, **k: critical_messages.append(a)
    )

    editor = rule_editor_module.SubtitleEditor()
    try:
        result = editor.save_to_file(str(tmp_path))  # 把目录当文件写，必然 OSError
        assert result is False
        assert critical_messages, "保存失败必须弹错误提示"
        text = " ".join(str(part) for part in critical_messages[0])
        assert "另存为" in text
    finally:
        editor.close()


def test_save_success_writes_json(rule_editor_module, qt_app, tmp_path, monkeypatch):
    monkeypatch.setattr(rule_editor_module.QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(rule_editor_module.QMessageBox, "critical", lambda *a, **k: None)

    editor = rule_editor_module.SubtitleEditor()
    target = tmp_path / "subtitle_rules.json"
    try:
        assert editor.save_to_file(str(target)) is True
        assert target.exists()
        assert '"delete"' in target.read_text(encoding="utf-8")
    finally:
        editor.close()
