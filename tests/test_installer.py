"""安装器回归测试：plugin_id 校验、目标路径越界、install/check 三态、混合导入与哨兵目录。"""
import json
import os

import pytest


def _manifest(plugin_id=None, name="测试插件", version="1.0.0", **extra):
    data = {"name": name, "version": version, **extra}
    if plugin_id is not None:
        data["plugin_id"] = plugin_id
    return data


def _new_installer(installer_env, zip_path):
    return installer_env.installer(zip_path)


@pytest.mark.parametrize(
    "plugin_id",
    ["abc", "A1_b-2", "中文插件", "123"],
    ids=["英文", "数字下划线连字符", "中文", "纯数字"],
)
def test_合法plugin_id可以安装(installer_env, zip_factory, plugin_id):
    """合法 plugin_id 应解析到 plugins/ 下并成功解压。"""
    zip_path = zip_factory(manifest=_manifest(plugin_id))
    installer = _new_installer(installer_env, zip_path)

    assert installer.load_zip_json() is True
    assert installer.install() is True
    target = installer_env.plugins_root / plugin_id
    assert (target / "manifest.json").is_file()


@pytest.mark.parametrize(
    "plugin_id",
    [
        "../x",
        "/abs",
        "..\\x",
        "C:\\x",
        "",
        "   ",
        "a/b",
        "a\\b",
        ".",
        "..",
        "bad.plugin",
    ],
    ids=[
        "上级目录",
        "绝对路径",
        "反斜杠越界",
        "盘符路径",
        "空值",
        "纯空格",
        "正斜杠",
        "反斜杠",
        "单点",
        "双点",
        "含点号",
    ],
)
def test_非法plugin_id被拒绝且不安装(installer_env, zip_factory, plugin_id):
    """非法 plugin_id 应在读取 manifest 阶段被拒绝，不产生安装目录。"""
    zip_path = zip_factory(manifest=_manifest(plugin_id))
    installer = _new_installer(installer_env, zip_path)

    assert installer.load_zip_json() is False
    assert installer.plugin_path is None
    assert installer.install() is False
    assert list(installer_env.plugins_root.iterdir()) == []
    assert installer_env.popups.errors


def test_未提供plugin_id时回退到name(installer_env, zip_factory):
    """manifest 缺少 plugin_id 时应使用 name 作为安装目录。"""
    zip_path = zip_factory(manifest=_manifest(plugin_id=None, name="默认目录插件"))
    installer = _new_installer(installer_env, zip_path)

    assert installer.load_zip_json() is True
    assert installer.install() is True
    assert (installer_env.plugins_root / "默认目录插件" / "manifest.json").is_file()


def test_合法plugin_id指向联结外部时拒绝(installer_env, zip_factory, make_junction):
    """plugin_id 合法但 realpath 落到 plugins/ 外时，应拒绝安装且保留外部文件。"""
    outside = installer_env.root / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel.txt"
    sentinel.write_text("keep", encoding="utf-8")
    link = installer_env.plugins_root / "link_plugin"
    make_junction(link, outside)

    try:
        zip_path = zip_factory(manifest=_manifest("link_plugin"))
        installer = _new_installer(installer_env, zip_path)

        assert installer.load_zip_json() is False
        assert installer.plugin_path is None
        assert sentinel.read_text(encoding="utf-8") == "keep"
        assert any("不在 plugins 目录下" in message for message in installer_env.popups.errors)
    finally:
        os.rmdir(link)


def test_非zip文件被拒绝(installer_env, zip_factory):
    """非 zip 文件应在读取阶段失败，install() 也不得报成功。"""
    zip_path = zip_factory(raw=b"not a zip", name="not_a_zip.zip")
    installer = _new_installer(installer_env, zip_path)

    assert installer.load_zip_json() is False
    assert installer.install() is False
    assert installer_env.popups.errors


def test_缺少manifest被拒绝(installer_env, zip_factory):
    """zip 根目录缺少 manifest.json 时应拒绝安装。"""
    zip_path = zip_factory(manifest=None, files={"readme.txt": "x"})
    installer = _new_installer(installer_env, zip_path)

    assert installer.load_zip_json() is False
    assert installer.install() is False


@pytest.mark.parametrize(
    "manifest",
    [
        {"version": "1.0.0"},
        {"name": "缺版本"},
    ],
    ids=["缺name", "缺version"],
)
def test_manifest缺少必填字段被拒绝(installer_env, zip_factory, manifest):
    """manifest 缺少 name 或 version 时应拒绝安装。"""
    zip_path = zip_factory(manifest=manifest)
    installer = _new_installer(installer_env, zip_path)

    assert installer.load_zip_json() is False
    assert installer.install() is False


def test_manifest非法json被拒绝(installer_env, zip_factory):
    """manifest.json 无法解析时应拒绝安装。"""
    zip_path = zip_factory(manifest="{not json")
    installer = _new_installer(installer_env, zip_path)

    assert installer.load_zip_json() is False
    assert installer.install() is False


def test_首次安装返回True(installer_env, zip_factory):
    """未安装过的插件，check_version_and_install() 应返回 True。"""
    zip_path = zip_factory(manifest=_manifest("首次安装"))
    installer = _new_installer(installer_env, zip_path)

    assert installer.load_zip_json() is True
    assert installer.check_version_and_install() is True
    assert (installer_env.plugins_root / "首次安装" / "manifest.json").is_file()


def test_解压失败返回False(installer_env, zip_factory):
    """zip 含越界成员时 install() 失败，且不得写出 plugins/ 外的文件。"""
    zip_path = zip_factory(
        manifest=_manifest("越界成员插件"),
        files={"../evil.txt": "should not exist"},
    )
    installer = _new_installer(installer_env, zip_path)

    assert installer.load_zip_json() is True
    assert installer.check_version_and_install() is False
    assert not (installer_env.root / "evil.txt").exists()
    assert installer_env.popups.errors


def test_同版本取消返回None(installer_env, zip_factory):
    """同版本重装选择取消时返回 None，且不覆盖已安装内容。"""
    target = installer_env.plugins_root / "同版本插件"
    target.mkdir()
    (target / "manifest.json").write_text(
        json.dumps({"name": "同版本插件", "version": "1.0.0", "marker": "old"}, ensure_ascii=False),
        encoding="utf-8",
    )
    zip_path = zip_factory(manifest=_manifest("同版本插件", marker="new"))
    installer = _new_installer(installer_env, zip_path)

    assert installer.load_zip_json() is True
    installer_env.popups.yes_no_response = "No"
    assert installer.check_version_and_install() is None

    installed = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    assert installed["marker"] == "old"
    assert installer_env.popups.yes_no_messages


def test_低版本取消返回None(installer_env, zip_factory):
    """已安装版本更高时选择取消，返回 None 且保留旧版本。"""
    target = installer_env.plugins_root / "低版本插件"
    target.mkdir()
    (target / "manifest.json").write_text(
        json.dumps({"name": "低版本插件", "version": "2.0.0", "marker": "old"}, ensure_ascii=False),
        encoding="utf-8",
    )
    zip_path = zip_factory(manifest=_manifest("低版本插件", version="1.0.0", marker="new"))
    installer = _new_installer(installer_env, zip_path)

    assert installer.load_zip_json() is True
    installer_env.popups.yes_no_response = "No"
    assert installer.check_version_and_install() is None

    installed = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    assert installed["version"] == "2.0.0"
    assert installed["marker"] == "old"


def test_同版本确认重装返回True(installer_env, zip_factory):
    """同版本重装选择确认时应覆盖旧内容并返回 True。"""
    target = installer_env.plugins_root / "重装插件"
    target.mkdir()
    (target / "manifest.json").write_text(
        json.dumps({"name": "重装插件", "version": "1.0.0", "marker": "old"}, ensure_ascii=False),
        encoding="utf-8",
    )
    zip_path = zip_factory(manifest=_manifest("重装插件", marker="new"))
    installer = _new_installer(installer_env, zip_path)

    assert installer.load_zip_json() is True
    installer_env.popups.yes_no_response = "Yes"
    assert installer.check_version_and_install() is True

    installed = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    assert installed["marker"] == "new"


def test_混合导入结果分组正确(installer_env, zip_factory):
    """成功、失败与取消应分别归入三条列表。"""
    success_zip = zip_factory(manifest=_manifest("ok_plugin"), name="ok.zip")
    bad_id_zip = zip_factory(manifest=_manifest("../evil"), name="bad_id.zip")
    missing_manifest_zip = zip_factory(manifest=None, name="missing_manifest.zip")
    unsafe_zip = zip_factory(
        manifest=_manifest("unsafe_plugin"),
        files={"../evil.txt": "x"},
        name="unsafe.zip",
    )

    cancel_target = installer_env.plugins_root / "cancel_plugin"
    cancel_target.mkdir()
    (cancel_target / "manifest.json").write_text(
        json.dumps({"name": "cancel_plugin", "version": "1.0.0"}, ensure_ascii=False),
        encoding="utf-8",
    )
    cancel_zip = zip_factory(manifest=_manifest("cancel_plugin"), name="cancel.zip")

    installer_env.popups.yes_no_response = "No"
    result = installer_env.module.import_plugin_list(
        [success_zip, bad_id_zip, missing_manifest_zip, unsafe_zip, cancel_zip]
    )

    assert result["success_list"] == [success_zip]
    assert result["failed_files"] == [bad_id_zip, missing_manifest_zip, unsafe_zip]
    assert result["skipped_files"] == [cancel_zip]
    assert (installer_env.plugins_root / "ok_plugin" / "manifest.json").is_file()


def test_越界拒绝不删除现有目录与外部哨兵(installer_env, zip_factory):
    """非法 plugin_id 被拒绝时，已有插件目录和 plugins/ 外文件都不得被删除。"""
    safe_dir = installer_env.plugins_root / "safe_plugin"
    safe_dir.mkdir()
    sentinel = safe_dir / "sentinel.txt"
    sentinel.write_text("keep", encoding="utf-8")
    outside = installer_env.root / "outside_sentinel.txt"
    outside.write_text("keep", encoding="utf-8")

    for plugin_id in ("../safe_plugin", "../outside_sentinel.txt"):
        zip_path = zip_factory(manifest=_manifest(plugin_id))
        installer = _new_installer(installer_env, zip_path)
        assert installer.load_zip_json() is False
        assert installer.install() is False

    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert outside.read_text(encoding="utf-8") == "keep"
    assert safe_dir.is_dir()
