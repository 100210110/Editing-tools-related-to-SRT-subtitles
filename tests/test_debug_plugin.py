"""调试插件异常链路回归测试（TODO #20）。

历史问题：`测试插件` 用 `raise KeyboardInterrupt` 模拟错误。`KeyboardInterrupt`
继承自 `BaseException`，`__init__.py` 的 `except Exception` 接不住，于是既不输出
统一错误 JSON，也走 Python 默认 traceback。现在改为 `RuntimeError`，这里用真实子进程
（stdin/stdout 协议）验证“错误 JSON + stderr traceback + 退出码 0”三条。

测试把插件源码复制到临时目录，并把 `test_1`（会弹 PySimpleGUI 窗口）替换成空实现，
避免子进程在无人值守环境下卡在弹窗上。
"""
import ast
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = REPO_ROOT / "软件本体" / "plugins" / "测试插件"


def _prepare_plugin(tmp_path):
    """复制插件入口到临时目录，并用空实现顶替会弹窗的 test_1。"""
    entry = tmp_path / "__init__.py"
    shutil.copy2(PLUGIN_DIR / "__init__.py", entry)
    (tmp_path / "test_1.py").write_text(
        "def run(params=None):\n    return None\n", encoding="utf-8"
    )
    return entry


def _run_plugin(entry, payload, timeout=60):
    return subprocess.run(
        [sys.executable, str(entry)],
        input=json.dumps(payload),
        capture_output=True,
        encoding="utf-8",
        timeout=timeout,
    )


def test_debug_plugin_returns_error_json(tmp_path):
    entry = _prepare_plugin(tmp_path)

    result = _run_plugin(entry, {"event": "test2"})

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] is False
    assert "测试插件故意抛出的异常" in payload["popup"]["message"]


def test_debug_plugin_writes_traceback_to_stderr(tmp_path):
    entry = _prepare_plugin(tmp_path)

    result = _run_plugin(entry, {"event": "test2"})

    assert "Traceback" in result.stderr
    assert "RuntimeError" in result.stderr
    # 只输出一份 JSON，不能因为异常再打一份成功载荷
    assert result.stdout.strip().count("\n") == 0


def test_no_keyboard_interrupt_in_debug_plugin():
    """禁止再退回 KeyboardInterrupt（BaseException 不会被 except Exception 接住）。"""
    source = (PLUGIN_DIR / "__init__.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and node.exc is not None:
            exc = node.exc
            name = exc.func.id if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name) else None
            assert name != "KeyboardInterrupt", "调试插件不应抛 KeyboardInterrupt"
