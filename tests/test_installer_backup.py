"""安装时自动备份将被覆盖的插件文件（TODO #27，真机 T15）。

核心诉求：用户改过的 subtitle_rules.json 之类文件，在升级/重装插件时不能被静默覆盖掉，
而且备份必须在 rmtree 之前完成——备份失败就干脆别装。
"""
import json
import os
from pathlib import Path

import pytest


def _manifest(version="1.0.0", name="测试插件"):
    """带 buttons 的现代 manifest，能通过 validate_package 的可执行文件校验。"""
    return {
        "name": name,
        "version": version,
        "buttons": [{"label": name, "executable": "__init__"}],
    }


def _install_existing(env, plugin_id, manifest, files):
    """在 plugins/<id> 下预置一个"已安装"插件，返回目录路径。"""
    target = env.plugins_root / plugin_id
    target.mkdir(parents=True)
    (target / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
    )
    for name, content in files.items():
        (target / name).write_bytes(
            content if isinstance(content, bytes) else content.encode("utf-8")
        )
    return target


def _backup_root(env):
    return env.root / "cache" / "plugin_backup"


def test_覆盖用户改过的规则文件前先备份(installer_env, zip_factory):
    target = _install_existing(
        installer_env,
        "测试插件",
        _manifest("1.0.0"),
        {"subtitle_rules.json": '{"v": "user"}', "__init__.exe": b"OLD-EXE"},
    )
    zip_path = zip_factory(
        manifest=_manifest("1.1.0"),
        files={"subtitle_rules.json": '{"v": "zip"}', "__init__.exe": b"NEW-EXE"},
    )
    installer = installer_env.installer(zip_path)

    assert installer.load_zip_json() is True
    assert installer.check_version_and_install() is True

    # 装上的是包里那份
    assert (target / "subtitle_rules.json").read_text(encoding="utf-8") == '{"v": "zip"}'
    assert (target / "__init__.exe").read_bytes() == b"NEW-EXE"

    # 用户改过的原件逐字节留在备份里
    assert installer.backup_dir is not None
    backup_dir = Path(installer.backup_dir)
    assert backup_dir.parent == _backup_root(installer_env) / "测试插件"
    assert (backup_dir / "subtitle_rules.json").read_text(encoding="utf-8") == '{"v": "user"}'
    assert (backup_dir / "__init__.exe").read_bytes() == b"OLD-EXE"
    assert "subtitle_rules.json" in installer.backed_up
    # 备份目录在插件目录之外，不会随 rmtree 一起消失
    assert os.path.isdir(backup_dir)


def test_内容完全一致时不产生备份(installer_env, zip_factory):
    manifest = _manifest("1.0.0")
    target = _install_existing(installer_env, "测试插件", manifest, {"__init__.exe": b"MZ"})
    zip_path = zip_factory(manifest=manifest, files={"__init__.exe": b"MZ"})
    installer_env.popups.yes_no_response = "Yes"  # 同版本重装

    installer = installer_env.installer(zip_path)
    assert installer.load_zip_json() is True
    assert installer.check_version_and_install() is True

    assert installer.backup_dir is None
    assert installer.backed_up == []
    assert not _backup_root(installer_env).exists()
    assert (target / "__init__.exe").read_bytes() == b"MZ"


def test_全新安装不产生备份(installer_env, zip_factory):
    zip_path = zip_factory(
        manifest=_manifest("1.0.0", "全新插件"),
        files={"subtitle_rules.json": "{}"},
    )
    installer = installer_env.installer(zip_path)

    assert installer.load_zip_json() is True
    assert installer.check_version_and_install() is True
    assert installer.backup_dir is None
    assert not _backup_root(installer_env).exists()
    assert (installer_env.plugins_root / "全新插件" / "subtitle_rules.json").exists()


def test_同版本重装同样备份(installer_env, zip_factory):
    _install_existing(
        installer_env,
        "测试插件",
        _manifest("1.0.0"),
        {"subtitle_rules.json": '{"v": "user"}'},
    )
    zip_path = zip_factory(
        manifest=_manifest("1.0.0"),
        files={"subtitle_rules.json": '{"v": "zip"}'},
    )
    installer_env.popups.yes_no_response = "Yes"

    installer = installer_env.installer(zip_path)
    assert installer.load_zip_json() is True
    assert installer.check_version_and_install() is True
    assert installer.backup_dir is not None
    assert (Path(installer.backup_dir) / "subtitle_rules.json").read_text(
        encoding="utf-8"
    ) == '{"v": "user"}'


def test_备份失败时不删除旧插件(installer_env, zip_factory, monkeypatch):
    """备份失败必须中止安装：宁可装不上，也不能旧文件删了、新文件没解出来。"""
    target = _install_existing(
        installer_env,
        "测试插件",
        _manifest("1.0.0"),
        {"subtitle_rules.json": '{"v": "user"}', "__init__.exe": b"OLD-EXE"},
    )
    zip_path = zip_factory(
        manifest=_manifest("1.1.0"),
        files={"subtitle_rules.json": '{"v": "zip"}', "__init__.exe": b"NEW-EXE"},
    )

    def boom(*args, **kwargs):
        raise OSError("磁盘已满")

    monkeypatch.setattr(installer_env.module.shutil, "copy2", boom)
    installer = installer_env.installer(zip_path)
    assert installer.load_zip_json() is True

    assert installer.check_version_and_install() is False
    assert installer_env.popups.errors
    assert "磁盘已满" in installer_env.popups.errors[-1]
    # 旧插件一个字节都不能动
    assert (target / "subtitle_rules.json").read_text(encoding="utf-8") == '{"v": "user"}'
    assert (target / "__init__.exe").read_bytes() == b"OLD-EXE"


def test_不安全路径的包不会删掉旧插件(installer_env, zip_factory):
    """成员路径校验提前到 rmtree 之前：坏包连备份机会都不该有。"""
    target = _install_existing(
        installer_env,
        "测试插件",
        _manifest("1.0.0"),
        {"subtitle_rules.json": '{"v": "user"}', "__init__.exe": b"OLD-EXE"},
    )
    zip_path = zip_factory(
        manifest=_manifest("1.1.0"),
        files={"../evil.txt": b"x", "__init__.exe": b"NEW-EXE"},
    )
    installer = installer_env.installer(zip_path)
    assert installer.load_zip_json() is True

    assert installer.check_version_and_install() is False
    assert installer_env.popups.errors
    assert "不安全路径" in installer_env.popups.errors[-1]
    assert (target / "__init__.exe").read_bytes() == b"OLD-EXE"
    assert (target / "subtitle_rules.json").read_text(encoding="utf-8") == '{"v": "user"}'


def test_批量导入返回备份信息(installer_env, zip_factory):
    _install_existing(
        installer_env,
        "测试插件",
        _manifest("1.0.0"),
        {"subtitle_rules.json": '{"v": "user"}'},
    )
    zip_path = zip_factory(
        manifest=_manifest("1.1.0"),
        files={"subtitle_rules.json": '{"v": "zip"}'},
    )

    result = installer_env.module.import_plugin_list([str(zip_path)])

    assert result["success_list"] == [str(zip_path)]
    assert result["failed_files"] == []
    info = result["backups"][str(zip_path)]
    assert info["name"] == "测试插件"
    assert "subtitle_rules.json" in info["files"]
    assert os.path.isdir(info["dir"])


def test_无覆盖时批量导入不返回备份(installer_env, zip_factory):
    zip_path = zip_factory(manifest=_manifest("1.0.0", "全新插件"))
    result = installer_env.module.import_plugin_list([str(zip_path)])

    assert result["success_list"] == [str(zip_path)]
    assert result["backups"] == {}
