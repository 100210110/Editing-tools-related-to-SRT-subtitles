"""安装失败回归测试：真实清理失败、真实解压失败、文件占用与权限不足。"""
import os
import stat
from pathlib import Path

import pytest


def _manifest(plugin_id):
    return {"name": plugin_id, "version": "1.0.0", "plugin_id": plugin_id}


def _prepare_installer(installer_env, zip_factory, plugin_id):
    zip_path = zip_factory(manifest=_manifest(plugin_id), name=f"{plugin_id}.zip")
    installer = installer_env.installer(zip_path)
    assert installer.load_zip_json() is True
    return installer


def test_只读文件阻止清理时返回False并保留旧目录(installer_env, zip_factory):
    """目标目录含只读文件时 rmtree 失败，install() 返回 False 且旧目录保留。"""
    plugin_id = "只读清理插件"
    target = installer_env.plugins_root / plugin_id
    target.mkdir()
    locked = target / "locked.txt"
    locked.write_text("keep", encoding="utf-8")
    os.chmod(locked, stat.S_IREAD)
    installer = _prepare_installer(installer_env, zip_factory, plugin_id)

    try:
        result = installer.install()
        if result:
            pytest.skip("当前环境只读文件未阻止 rmtree")
        assert result is False
        assert target.is_dir()
        assert locked.is_file()
        assert installer_env.popups.errors
    finally:
        if locked.exists():
            os.chmod(locked, stat.S_IWRITE)


def test_文件被占用阻止清理时返回False(installer_env, zip_factory):
    """目标文件被打开占用时清理失败，install() 返回 False（其他平台可能跳过）。"""
    plugin_id = "占用清理插件"
    target = installer_env.plugins_root / plugin_id
    target.mkdir()
    held = target / "held.txt"
    held.write_text("keep", encoding="utf-8")
    handle = open(held, "w", encoding="utf-8")
    installer = _prepare_installer(installer_env, zip_factory, plugin_id)

    try:
        result = installer.install()
        if result:
            pytest.skip("当前平台允许删除被占用文件，未复现清理失败")
        assert result is False
        assert target.is_dir()
        assert installer_env.popups.errors
    finally:
        handle.close()


def test_损坏zip在解压前打开失败(installer_env, zip_factory):
    """manifest 读取成功后 zip 被破坏，install() 应返回 False 而不抛异常。"""
    plugin_id = "损坏包插件"
    installer = _prepare_installer(installer_env, zip_factory, plugin_id)
    Path(installer.zip_path).write_bytes(b"not a zip anymore\n")

    assert installer.install() is False
    assert installer_env.popups.errors


def test_真实解压冲突导致失败(installer_env, zip_factory):
    """zip 内文件与目录同名时 extractall 真实失败，install() 返回 False。"""
    plugin_id = "解压冲突插件"
    zip_path = zip_factory(
        manifest=_manifest(plugin_id),
        files={"a": "file", "a/b.txt": "nested"},
        name="解压冲突.zip",
    )
    installer = installer_env.installer(zip_path)
    assert installer.load_zip_json() is True

    assert installer.install() is False
    assert installer_env.popups.errors


def test_权限不足导致失败或跳过(installer_env, zip_factory):
    """plugins 目录不可写时安装失败；若环境无法模拟则明确跳过。"""
    plugin_id = "权限插件"
    zip_path = zip_factory(manifest=_manifest(plugin_id), name="权限.zip")
    installer = installer_env.installer(zip_path)
    assert installer.load_zip_json() is True

    original_mode = stat.S_IMODE(os.stat(installer_env.plugins_root).st_mode)
    os.chmod(installer_env.plugins_root, stat.S_IREAD)
    try:
        result = installer.install()
    finally:
        os.chmod(installer_env.plugins_root, original_mode)

    if result:
        pytest.skip("当前环境无法用普通权限模拟目录不可写")
    assert result is False
    assert installer_env.popups.errors
