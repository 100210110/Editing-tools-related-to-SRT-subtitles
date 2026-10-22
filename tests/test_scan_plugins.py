"""插件扫描回归测试：损坏 manifest 的容错、跳过与汇总告警（TODO #13）。"""
import importlib.util
import io
import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SOFTWARE_DIR = REPO_ROOT / "软件本体"
MAIN_PATH = SOFTWARE_DIR / "插件调度主程序.py"


class FakeSG(types.ModuleType):
    """够用的 PySimpleGUI 替身：未定义的属性一律返回 MagicMock，弹窗另行覆盖。"""

    WIN_CLOSED = "__WIN_CLOSED__"
    SELECT_MODE_EXTENDED = "extended"

    def __init__(self):
        super().__init__("PySimpleGUI")

    def __getattr__(self, name):
        return MagicMock(name=name)


@pytest.fixture(scope="module")
def app_module():
    """按路径加载主程序模块。

    主程序在 import 期会 import PySimpleGUI / tkinterdnd2，并把 sys.std* 换成 UTF-8 包装器，
    因此这里先顶上桩模块、塞入带 buffer 的占位流，加载完再把 sys 状态还原。
    """
    saved_streams = (sys.stdin, sys.stdout, sys.stderr)
    saved_modules = {
        name: sys.modules.get(name) for name in ("PySimpleGUI", "tkinterdnd2")
    }
    saved_path = list(sys.path)

    sg_stub = FakeSG()
    dnd_stub = types.ModuleType("tkinterdnd2")
    dnd_stub.DND_FILES = "DND_Files"
    dnd_stub.TkinterDnD = types.SimpleNamespace(Tk=lambda *a, **k: MagicMock())

    sys.modules["PySimpleGUI"] = sg_stub
    sys.modules["tkinterdnd2"] = dnd_stub
    sys.path.insert(0, str(SOFTWARE_DIR))
    sys.stdin = io.TextIOWrapper(io.BytesIO())
    sys.stdout = io.TextIOWrapper(io.BytesIO())
    sys.stderr = io.TextIOWrapper(io.BytesIO())
    try:
        spec = importlib.util.spec_from_file_location(
            "retoolbox_main_under_test", MAIN_PATH
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    finally:
        sys.stdin, sys.stdout, sys.stderr = saved_streams
        sys.path[:] = saved_path
        for name, mod in saved_modules.items():
            if mod is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = mod
    return module


def make_plugin(plugins_dir, folder, manifest, files=None):
    """在 plugins_dir 下建一个插件目录；manifest 传字符串则原样写入。"""
    plugin_dir = plugins_dir / folder
    plugin_dir.mkdir(parents=True, exist_ok=True)
    if manifest is not None:
        text = manifest if isinstance(manifest, str) else json.dumps(manifest, ensure_ascii=False)
        (plugin_dir / "manifest.json").write_text(text, encoding="utf-8")
    for name in files or []:
        (plugin_dir / name).write_text("# stub", encoding="utf-8")
    return plugin_dir


OLD_FORMAT = {"name": "旧式插件", "executable": "main.py", "description": "单按钮"}
BUTTON_FORMAT = {
    "name": "多按钮插件",
    "category": "字幕处理",
    "buttons": [
        {"label": "跑一下", "executable": "run.py"},
        {"label": "改配置", "executable": "edit", "event": "config"},   # 省略扩展名
    ],
}


@pytest.fixture
def plugins_dir(tmp_path):
    root = tmp_path / "plugins"
    root.mkdir()
    return root


# ---------------------------------------------------------------- manifest 解析


def test_load_manifest_accepts_old_format(tmp_path, app_module):
    plugin_dir = make_plugin(tmp_path, "old", OLD_FORMAT, files=["main.py"])

    info, error = app_module._load_manifest(plugin_dir / "manifest.json")

    assert error is None
    assert info["name"] == "旧式插件"


def test_load_manifest_accepts_buttons_format(tmp_path, app_module):
    plugin_dir = make_plugin(tmp_path, "multi", BUTTON_FORMAT, files=["run.py", "edit.py"])

    info, error = app_module._load_manifest(plugin_dir / "manifest.json")

    assert error is None
    assert len(info["buttons"]) == 2


def test_load_manifest_reports_json_syntax_error(tmp_path, app_module):
    plugin_dir = make_plugin(tmp_path, "broken", '{"name": "半截",,}')

    info, error = app_module._load_manifest(plugin_dir / "manifest.json")

    assert info is None
    assert "不是合法 JSON" in error


def test_load_manifest_requires_name(tmp_path, app_module):
    plugin_dir = make_plugin(tmp_path, "noname", json.dumps({"executable": "main.py"}))

    info, error = app_module._load_manifest(plugin_dir / "manifest.json")

    assert info is None
    assert "name" in error


def test_load_manifest_requires_executable_or_buttons(tmp_path, app_module):
    plugin_dir = make_plugin(tmp_path, "empty", {"name": "空壳", "version": "1.0.0"})

    info, error = app_module._load_manifest(plugin_dir / "manifest.json")

    assert info is None
    assert "executable" in error


def test_load_manifest_rejects_non_object(tmp_path, app_module):
    plugin_dir = make_plugin(tmp_path, "list", json.dumps([1, 2, 3]))

    info, error = app_module._load_manifest(plugin_dir / "manifest.json")

    assert info is None
    assert "不是对象" in error


def test_load_manifest_rejects_buttons_not_list(tmp_path, app_module):
    plugin_dir = make_plugin(tmp_path, "badbuttons", {"name": "x", "buttons": {"a": 1}})

    info, error = app_module._load_manifest(plugin_dir / "manifest.json")

    assert info is None
    assert "不是数组" in error


# ---------------------------------------------------------------- 可执行文件解析


def test_resolve_executable_appends_py_extension(tmp_path, app_module):
    plugin_dir = make_plugin(tmp_path, "ext", BUTTON_FORMAT, files=["run.py", "edit.py"])

    assert app_module._resolve_executable(plugin_dir, "edit") == str(plugin_dir / "edit.py")
    assert app_module._resolve_executable(plugin_dir, "run.py") == str(plugin_dir / "run.py")
    assert app_module._resolve_executable(plugin_dir, "missing") is None


# ---------------------------------------------------------------- scan_plugins


def test_scan_plugins_passes_through_all_buttons(plugins_dir, app_module):
    make_plugin(plugins_dir, "old", OLD_FORMAT, files=["main.py"])
    make_plugin(plugins_dir, "multi", BUTTON_FORMAT, files=["run.py", "edit.py"])

    buttons, failures = app_module.scan_plugins(str(plugins_dir))

    assert failures == []
    assert {btn["key"] for btn in buttons} == {
        "BTN_old_旧式插件",
        "BTN_multi_跑一下",
        "BTN_multi_改配置",
    }
    by_key = {btn["key"]: btn for btn in buttons}
    assert by_key["BTN_multi_改配置"]["event"] == "config"
    assert by_key["BTN_multi_改配置"]["executable_path"].endswith("edit.py")
    assert by_key["BTN_old_旧式插件"]["type"] == "script"


def test_scan_plugins_skips_broken_json_and_keeps_others(plugins_dir, app_module):
    make_plugin(plugins_dir, "good", OLD_FORMAT, files=["main.py"])
    make_plugin(plugins_dir, "broken", "{ 这不是 JSON")

    buttons, failures = app_module.scan_plugins(str(plugins_dir))

    assert [btn["label"] for btn in buttons] == ["旧式插件"]
    assert len(failures) == 1
    folder, reason = failures[0]
    assert folder == "broken"
    assert "不是合法 JSON" in reason


def test_scan_plugins_reports_missing_executable(plugins_dir, app_module):
    make_plugin(plugins_dir, "ghost", {"name": "缺文件", "executable": "nope.py"})

    buttons, failures = app_module.scan_plugins(str(plugins_dir))

    assert buttons == []
    assert len(failures) == 1
    assert failures[0][0] == "ghost"
    assert "可执行文件不存在" in failures[0][1]


def test_scan_plugins_reports_missing_button_executable(plugins_dir, app_module):
    manifest = {
        "name": "半边坏",
        "buttons": [
            {"label": "正常", "executable": "ok.py"},
            {"label": "缺失", "executable": "gone.py"},
        ],
    }
    make_plugin(plugins_dir, "half", manifest, files=["ok.py"])

    buttons, failures = app_module.scan_plugins(str(plugins_dir))

    # 打包不完整时整个插件跳过，避免只留一半按钮造成误判
    assert buttons == []
    assert len(failures) == 1
    assert "「缺失」" in failures[0][1]


def test_scan_plugins_mixed_reports_each_failure(plugins_dir, app_module):
    make_plugin(plugins_dir, "ok_old", OLD_FORMAT, files=["main.py"])
    make_plugin(plugins_dir, "ok_multi", BUTTON_FORMAT, files=["run.py", "edit.py"])
    make_plugin(plugins_dir, "bad_json", "not json at all")
    make_plugin(plugins_dir, "no_name", {"executable": "a.py"})
    make_plugin(plugins_dir, "ghost", {"name": "幽灵", "executable": "ghost.py"})

    buttons, failures = app_module.scan_plugins(str(plugins_dir))

    assert len(buttons) == 3
    assert sorted(folder for folder, _ in failures) == ["bad_json", "ghost", "no_name"]


def test_scan_plugins_ignores_folder_without_manifest(plugins_dir, app_module):
    (plugins_dir / "not_a_plugin").mkdir()
    make_plugin(plugins_dir, "good", OLD_FORMAT, files=["main.py"])

    buttons, failures = app_module.scan_plugins(str(plugins_dir))

    assert len(buttons) == 1
    assert failures == []


def test_scan_plugins_missing_directory_is_empty(tmp_path, app_module):
    buttons, failures = app_module.scan_plugins(str(tmp_path / "no_such_dir"))

    assert buttons == []
    assert failures == []


# ---------------------------------------------------------------- 告警


def test_warn_broken_plugins_pops_up_once(app_module, monkeypatch, capsys):
    shown = []
    monkeypatch.setattr(app_module.sg, "popup", lambda *a, **k: shown.append((a, k)))

    app_module.warn_broken_plugins(
        [("broken", "manifest.json 不是合法 JSON"), ("ghost", "可执行文件不存在（x.py）")]
    )

    assert len(shown) == 1, "多个损坏插件只能弹一次窗"
    message = shown[0][0][0]
    assert "2 个插件无法加载" in message
    assert "broken" in message and "ghost" in message
    assert "不是合法 JSON" in message

    log = capsys.readouterr().out
    assert log.count("插件加载失败，已跳过") == 2
