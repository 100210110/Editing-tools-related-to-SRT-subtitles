"""共享测试设施：加载中文路径源码、隔离临时目录、构造插件 zip、重定向规则缓存。"""
import hashlib
import importlib.util
import io
import json
import os
import pickle
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SOFTWARE_DIR = REPO_ROOT / "软件本体"
BUILD_AUTOMATON_PATH = SOFTWARE_DIR / "plugins" / "srt关键词替换" / "build_automaton.py"
LOAD_ZIP_PATH = SOFTWARE_DIR / "load_zip.py"
MAIN_PROGRAM_PATH = SOFTWARE_DIR / "插件调度主程序.py"

_DEFAULT_MANIFEST = object()


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载模块: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def load_zip_module():
    return _load_module("retoolbox_load_zip_under_test", LOAD_ZIP_PATH)


@pytest.fixture(scope="session")
def build_automaton_module():
    return _load_module("retoolbox_build_automaton_under_test", BUILD_AUTOMATON_PATH)


@pytest.fixture(scope="session")
def main_program_module():
    """加载主程序模块（`插件调度主程序.py`）。

    模块在 import 期会把 sys.stdin/stdout/stderr 换成 UTF-8 包装器，并 `from load_zip import ...`，
    所以先塞入带 buffer 的占位流、临时把 `软件本体/` 加进 sys.path，加载完再全部还原。
    """
    saved_streams = (sys.stdin, sys.stdout, sys.stderr)
    saved_path = list(sys.path)
    sys.stdin = io.TextIOWrapper(io.BytesIO())
    sys.stdout = io.TextIOWrapper(io.BytesIO())
    sys.stderr = io.TextIOWrapper(io.BytesIO())
    sys.path.insert(0, str(SOFTWARE_DIR))
    try:
        module = _load_module("retoolbox_main_program_under_test", MAIN_PROGRAM_PATH)
    finally:
        sys.stdin, sys.stdout, sys.stderr = saved_streams
        sys.path[:] = saved_path
    return module


class PopupStub:
    """替代 PySimpleGUI 弹窗，记录调用并返回可控结果。"""

    def __init__(self):
        self.errors = []
        self.yes_no_messages = []
        self.yes_no_response = "No"
        self.ok_cancel_messages = []
        self.ok_cancel_response = "Cancel"

    def popup_error(self, message, **kwargs):
        self.errors.append(str(message))

    def popup_yes_no(self, message, **kwargs):
        self.yes_no_messages.append(str(message))
        return self.yes_no_response

    def popup_ok_cancel(self, message, **kwargs):
        self.ok_cancel_messages.append(str(message))
        return self.ok_cancel_response


class InstallerEnv:
    def __init__(self, module, root, plugins_root, popups):
        self.module = module
        self.root = root
        self.plugins_root = plugins_root
        self.popups = popups

    def installer(self, zip_path):
        return self.module.PluginInstaller(str(zip_path))


@pytest.fixture
def installer_env(tmp_path, monkeypatch, load_zip_module):
    """把 load_zip 的 plugins 根目录重定向到 tmp_path，并拦截所有弹窗。"""
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()

    def fake_get_path(relative_path=None, use_program_dir=True):
        if relative_path is None:
            return str(tmp_path)
        return str(tmp_path / relative_path)

    monkeypatch.setattr(load_zip_module, "get_path", fake_get_path)
    popups = PopupStub()
    monkeypatch.setattr(load_zip_module.sg, "popup_error", popups.popup_error)
    monkeypatch.setattr(load_zip_module.sg, "popup_yes_no", popups.popup_yes_no)
    monkeypatch.setattr(load_zip_module.sg, "popup_ok_cancel", popups.popup_ok_cancel)
    return InstallerEnv(load_zip_module, tmp_path, plugins_root, popups)


@pytest.fixture
def tmp_plugin_dir(installer_env):
    return installer_env.plugins_root


class ZipFactory:
    def __init__(self, root):
        self.root = root
        self.counter = 0

    def __call__(self, manifest=_DEFAULT_MANIFEST, files=None, name=None, raw=None):
        self.counter += 1
        path = self.root / (name or f"plugin_{self.counter}.zip")
        if raw is not None:
            path.write_bytes(raw)
            return path
        if manifest is _DEFAULT_MANIFEST:
            manifest = {"name": "测试插件", "version": "1.0.0"}
        # 默认附带占位可执行文件，让 manifest 声明的 executable 能在包内解析到（validate_package）
        members = {"__init__.exe": b"MZ"}
        members.update(files or {})
        with zipfile.ZipFile(path, "w") as zf:
            if manifest is not None:
                if isinstance(manifest, str):
                    zf.writestr("manifest.json", manifest)
                else:
                    zf.writestr(
                        "manifest.json",
                        json.dumps(manifest, ensure_ascii=False),
                    )
            for member, content in members.items():
                zf.writestr(member, content)
        return path


@pytest.fixture
def zip_factory(tmp_path):
    return ZipFactory(tmp_path)


class RulesWorkspace:
    """把规则 JSON 与 pkl 缓存限制在临时目录内。"""

    def __init__(self, module, root):
        self.module = module
        self.root = root
        self.json_path = root / "subtitle_rules.json"
        self.cache_path = root / "subtitle_rules.pkl"

    def write(self, rules, indent=4):
        self.json_path.write_text(
            json.dumps(rules, ensure_ascii=False, indent=indent),
            encoding="utf-8",
        )

    def write_text(self, text):
        self.json_path.write_text(text, encoding="utf-8")

    def processor(self):
        processor = self.module.SubtitleRuleProcessor()
        processor.json_path = str(self.json_path)
        processor.cache_path = str(self.cache_path)
        return processor

    def payload(self):
        with open(self.cache_path, "rb") as f:
            return pickle.load(f)

    def write_payload(self, payload):
        with open(self.cache_path, "wb") as f:
            pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)

    def expected_hash(self):
        content = self.json_path.read_text(encoding="utf-8")
        normalized = json.dumps(json.loads(content), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@pytest.fixture
def tmp_rules_dir(tmp_path, build_automaton_module):
    root = tmp_path / "rules"
    root.mkdir()
    return RulesWorkspace(build_automaton_module, root)


@pytest.fixture
def make_junction():
    """创建 Windows 目录联接；不可用或无权限时跳过测试。"""

    def _make(link, target):
        if os.name != "nt":
            pytest.skip("目录联接仅用于 Windows 环境")
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pytest.skip(f"当前环境无法创建目录联接: {result.stdout}{result.stderr}")
        return link

    return _make
