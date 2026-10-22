"""规则编辑器退出协议回归测试（TODO #18）。

历史问题：编辑器用 `sys.exit(app.exec_())` 退出，`SystemExit` 继承 `BaseException`，
插件入口的 `except Exception` 接不住，主程序可能收不到 JSON。
现在 `run()` 只返回退出码，由 `__init__.py` 的分发层统一输出 JSON 后再结束。
"""
import ast
import json
import shutil
import subprocess
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = REPO_ROOT / "软件本体" / "plugins" / "srt关键词替换"


# ---------------------------------------------------------------- 单元层


def test_editor_close_outputs_success_json(keyword_plugin_module, monkeypatch, capsys):
    stub = types.ModuleType("subtitle_rule_editor")
    stub.run = lambda: 0
    monkeypatch.setitem(sys.modules, "subtitle_rule_editor", stub)

    keyword_plugin_module.handle_event("subtitle_rule_editor", {})

    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["status"] is True
    assert "字幕替换规则修改完成" in payload["popup"]["message"]


def test_editor_exception_propagates_to_entry(keyword_plugin_module, monkeypatch, capsys):
    """编辑器内部异常要冒泡到入口，由入口统一转成错误 JSON（不能吞掉）。"""
    stub = types.ModuleType("subtitle_rule_editor")

    def boom():
        raise RuntimeError("编辑器炸了")

    stub.run = boom
    monkeypatch.setitem(sys.modules, "subtitle_rule_editor", stub)

    with pytest.raises(RuntimeError):
        keyword_plugin_module.handle_event("subtitle_rule_editor", {})
    capsys.readouterr()


def test_editor_run_returns_exit_code_instead_of_sys_exit(rule_editor_module):
    """`run()` 必须返回退出码，不能自己 sys.exit。"""
    source = (PLUGIN_DIR / "subtitle_rule_editor.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    run_func = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run"
    )
    calls = [
        node
        for node in ast.walk(run_func)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "exit"
    ]
    assert calls == [], "run() 内不应调用 sys.exit，退出码应返回给分发层"
    returns = [node for node in ast.walk(run_func) if isinstance(node, ast.Return)]
    assert returns, "run() 必须返回 Qt 事件循环的退出码"


# ---------------------------------------------------------------- 子进程层


def _prepare_plugin(tmp_path, editor_stub_source):
    shutil.copy2(PLUGIN_DIR / "__init__.py", tmp_path / "__init__.py")
    shutil.copy2(PLUGIN_DIR / "common.py", tmp_path / "common.py")
    (tmp_path / "subtitle_rule_editor.py").write_text(editor_stub_source, encoding="utf-8")
    return tmp_path / "__init__.py"


def _run(entry, payload=None, timeout=60):
    return subprocess.run(
        [sys.executable, str(entry)],
        input=json.dumps(payload) if payload is not None else "",
        capture_output=True,
        encoding="utf-8",
        timeout=timeout,
    )


def test_editor_system_exit_zero_outputs_success_json(tmp_path):
    entry = _prepare_plugin(
        tmp_path,
        "def run():\n    raise SystemExit(0)\n",
    )

    result = _run(entry, {"event": "subtitle_rule_editor"})

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout.strip())
    assert payload["status"] is True


def test_editor_system_exit_nonzero_outputs_failure_json(tmp_path):
    entry = _prepare_plugin(
        tmp_path,
        "def run():\n    raise SystemExit(1)\n",
    )

    result = _run(entry, {"event": "subtitle_rule_editor"})

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout.strip())
    assert payload["status"] is False
    assert "退出码 1" in payload["popup"]["message"]


def test_editor_exception_outputs_failure_json(tmp_path):
    entry = _prepare_plugin(
        tmp_path,
        "def run():\n    raise RuntimeError('编辑器炸了')\n",
    )

    result = _run(entry, {"event": "subtitle_rule_editor"})

    payload = json.loads(result.stdout.strip())
    assert payload["status"] is False
    assert "编辑器炸了" in payload["popup"]["message"]
    assert "Traceback" in result.stderr


def test_empty_stdin_still_reports_json(tmp_path):
    entry = _prepare_plugin(tmp_path, "def run():\n    return 0\n")

    result = _run(entry, None)

    assert result.returncode == 1
    payload = json.loads(result.stdout.strip())
    assert payload["status"] is False
    assert "stdin" in payload["popup"]["message"]
