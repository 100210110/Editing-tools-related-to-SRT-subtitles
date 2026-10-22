"""安装前包完整性校验：损坏的插件包不得覆盖已安装的正常插件（TODO #26，真机 T11）。"""
import json

import pytest


def _multi_manifest(buttons, name="多按钮插件", version="1.0.0"):
    return {"name": name, "version": version, "buttons": buttons}


def _install_existing(env, plugin_id, manifest, files):
    """在 plugins/<id> 下预置一个"已安装"插件，返回目录路径。"""
    target = env.plugins_root / plugin_id
    target.mkdir(parents=True)
    (target / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
    )
    for name, content in files.items():
        path = target / name
        path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
    return target


def test_多按钮插件缺exe时拒绝安装(installer_env, zip_factory):
    """第二个按钮指向包内不存在的文件时，整包拒绝，且不创建插件目录。"""
    manifest = _multi_manifest(
        [
            {"label": "主功能", "executable": "__init__"},
            {"label": "第二功能", "executable": "missing"},
        ]
    )
    zip_path = zip_factory(manifest=manifest)
    installer = installer_env.installer(zip_path)

    assert installer.load_zip_json() is True
    assert installer.validate_package() is False
    assert installer_env.popups.errors
    assert "missing" in installer_env.popups.errors[-1]
    assert not (installer_env.plugins_root / "多按钮插件").exists()


def test_坏包不得删除已安装的正常插件(installer_env, zip_factory):
    """核心回归：导入损坏的同名插件包时，已安装的正常插件必须原样保留。"""
    old_manifest = _multi_manifest(
        [{"label": "主功能", "executable": "__init__"}], version="1.0.0"
    )
    target = _install_existing(
        installer_env, "多按钮插件", old_manifest, {"__init__.exe": b"OLD-EXE"}
    )

    bad_manifest = _multi_manifest(
        [
            {"label": "主功能", "executable": "__init__"},
            {"label": "第二功能", "executable": "missing"},
        ],
        version="1.0.0",
    )
    zip_path = zip_factory(manifest=bad_manifest)
    installer = installer_env.installer(zip_path)

    assert installer.load_zip_json() is True
    assert installer.check_version_and_install() is False

    # 旧插件一个字节都不能动
    assert (target / "__init__.exe").read_bytes() == b"OLD-EXE"
    installed = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    assert installed["version"] == "1.0.0"
    assert len(installed["buttons"]) == 1


def test_旧式单按钮缺executable被拒绝(installer_env, zip_factory):
    """manifest 既没有 buttons 也没有 executable 时拒绝安装。"""
    zip_path = zip_factory(manifest={"name": "缺可执行文件", "version": "1.0.0"})
    installer = installer_env.installer(zip_path)

    assert installer.load_zip_json() is True
    assert installer.validate_package() is False
    assert "executable" in installer_env.popups.errors[-1]


def test_buttons为空被拒绝(installer_env, zip_factory):
    zip_path = zip_factory(manifest=_multi_manifest([], name="空按钮插件"))
    installer = installer_env.installer(zip_path)

    assert installer.load_zip_json() is True
    assert installer.validate_package() is False


def test_按钮缺label被拒绝(installer_env, zip_factory):
    """与主程序 _build_buttons 一致：多按钮格式缺 label 视为非法。"""
    zip_path = zip_factory(
        manifest=_multi_manifest([{"executable": "__init__"}], name="缺label插件")
    )
    installer = installer_env.installer(zip_path)

    assert installer.load_zip_json() is True
    assert installer.validate_package() is False


def test_exe位于子目录时被拒绝(installer_env, zip_factory):
    """manifest 写顶层文件名、但包内放在子目录时，解压后主程序找不到，应提前拒绝。"""
    zip_path = zip_factory(
        manifest=_multi_manifest(
            [{"label": "主功能", "executable": "only_in_sub"}], name="子目录插件"
        ),
        files={"sub/only_in_sub.exe": b"MZ"},
    )
    installer = installer_env.installer(zip_path)

    assert installer.load_zip_json() is True
    assert installer.validate_package() is False


def test_py扩展名可解析到exe成员(installer_env, zip_factory):
    """executable 写成 .py 但包内是 .exe 时允许安装（与运行时解析同源）。"""
    zip_path = zip_factory(
        manifest=_multi_manifest(
            [{"label": "加前缀", "executable": "自动给srt加前缀.py"}], name="扩展名插件"
        ),
        files={"自动给srt加前缀.exe": b"MZ"},
    )
    installer = installer_env.installer(zip_path)

    assert installer.load_zip_json() is True
    assert installer.validate_package() is True


def test_完整多按钮包可正常安装(installer_env, zip_factory):
    manifest = _multi_manifest(
        [
            {"label": "测试弹窗", "executable": "__init__", "event": "test"},
            {"label": "测试报错", "executable": "__init__", "event": "test2"},
        ],
        name="完整插件",
    )
    zip_path = zip_factory(manifest=manifest)
    installer = installer_env.installer(zip_path)

    assert installer.load_zip_json() is True
    assert installer.check_version_and_install() is True
    target = installer_env.plugins_root / "完整插件"
    assert (target / "manifest.json").is_file()
    assert (target / "__init__.exe").is_file()


def test_完整包可覆盖旧插件(installer_env, zip_factory):
    """校验通过后仍按原逻辑覆盖，确认没有误伤正常升级。"""
    old_manifest = _multi_manifest(
        [{"label": "主功能", "executable": "__init__"}], version="1.0.0"
    )
    target = _install_existing(
        installer_env, "升级插件", old_manifest, {"__init__.exe": b"OLD-EXE"}
    )

    new_manifest = _multi_manifest(
        [
            {"label": "主功能", "executable": "__init__"},
            {"label": "新功能", "executable": "__init__"},
        ],
        name="升级插件",
        version="1.1.0",
    )
    zip_path = zip_factory(manifest=new_manifest, files={"__init__.exe": b"NEW-EXE"})
    installer = installer_env.installer(zip_path)

    assert installer.load_zip_json() is True
    assert installer.check_version_and_install() is True
    assert (target / "__init__.exe").read_bytes() == b"NEW-EXE"
    installed = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    assert installed["version"] == "1.1.0"


def test_坏包归入失败列表(installer_env, zip_factory):
    """import_plugin_list 应把校验失败的包计入 failed_files，不影响同批正常包。"""
    good_zip = zip_factory(
        manifest=_multi_manifest([{"label": "主功能", "executable": "__init__"}], name="ok_plugin"),
        name="ok.zip",
    )
    bad_zip = zip_factory(
        manifest=_multi_manifest(
            [{"label": "主功能", "executable": "missing"}], name="bad_plugin"
        ),
        name="bad.zip",
    )

    result = installer_env.module.import_plugin_list([bad_zip, good_zip])

    assert result["failed_files"] == [bad_zip]
    assert result["success_list"] == [good_zip]
    assert result["skipped_files"] == []
    assert (installer_env.plugins_root / "ok_plugin" / "__init__.exe").is_file()


def test_批量导入坏包不单独弹窗但记录原因(installer_env, zip_factory):
    """批量导入时失败原因交给调用方汇总提示，避免“校验失败”和“未导入”连弹两次。"""
    bad_zip = zip_factory(
        manifest=_multi_manifest(
            [
                {"label": "主功能", "executable": "__init__"},
                {"label": "坏按钮", "executable": "missing"},
            ],
            name="bad_plugin",
        ),
        name="bad.zip",
    )

    result = installer_env.module.import_plugin_list([bad_zip])

    assert result["failed_files"] == [bad_zip]
    reason = result["failed_reasons"][bad_zip]
    assert "坏按钮" in reason and "missing" in reason
    assert "\n" not in reason  # 单行，便于在汇总弹窗里缩进展示
    assert installer_env.popups.errors == []


def test_单独调用时校验失败仍弹窗(installer_env, zip_factory):
    """不经过 import_plugin_list 的调用方（如手工调试）仍能直接看到失败原因。"""
    zip_path = zip_factory(
        manifest=_multi_manifest([{"label": "坏按钮", "executable": "missing"}], name="坏插件")
    )
    installer = installer_env.installer(zip_path)

    assert installer.load_zip_json() is True
    assert installer.check_version_and_install() is False
    assert installer.rejection_reason
    assert "missing" in installer_env.popups.errors[-1]
