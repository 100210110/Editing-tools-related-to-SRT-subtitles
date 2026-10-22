"""日志占位符回归测试（TODO #23）。

历史问题：`logger.info("params: {str(params)}")` 少了 f 前缀，日志里记的是字面量，
排查时看不到真实参数。这里用 AST 扫描兜底，避免同类问题再次出现在任何插件源码里。
"""
import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SOFTWARE_DIR = REPO_ROOT / "软件本体"
LOG_METHODS = {"debug", "info", "warning", "warn", "error", "exception", "critical"}


def _iter_python_files():
    return sorted(SOFTWARE_DIR.rglob("*.py"))


def _is_logger_call(node):
    """判断节点是否为 logger.<level>(...) 调用。"""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if not isinstance(func, ast.Attribute) or func.attr not in LOG_METHODS:
        return False
    # 常见写法：logger.xxx(...)、self.logger.xxx(...)
    value = func.value
    return isinstance(value, ast.Name) and value.id == "logger"


def _literal_placeholder_calls():
    """收集“模板是纯字符串字面量、却含有 {} 占位符”的日志调用。"""
    offenders = []
    for path in _iter_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not _is_logger_call(node) or not node.args:
                continue
            first = node.args[0]
            # f-string 会被解析成 JoinedStr；纯字面量里的 {} 不会被渲染
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                if "{" in first.value and "}" in first.value:
                    offenders.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}")
    return offenders


def test_no_unrendered_braces_in_logger_calls():
    offenders = _literal_placeholder_calls()
    assert offenders == [], "以下 logger 调用缺少 f 前缀或应改用 %s 参数：" + ", ".join(offenders)


def test_params_log_uses_percent_style():
    """`main()` 入口的参数日志必须把 params 作为参数传入，而不是写进字面量。"""
    source_path = SOFTWARE_DIR / "plugins" / "srt关键词替换" / "srt_keyword_editor.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))

    found = False
    for node in ast.walk(tree):
        if not _is_logger_call(node) or not node.args:
            continue
        first = node.args[0]
        if not (isinstance(first, ast.Constant) and "params:" in str(first.value)):
            continue
        found = True
        assert len(node.args) >= 2, "params 应当作为日志参数传入"
        assert isinstance(node.args[0].value, str) and "{" not in node.args[0].value
    assert found, "未找到 params 日志语句，测试需要跟随代码更新"
