"""缓存哈希前缀回归测试（TODO #12）。

历史问题：两个插件都写 `cache/output/<basename>`，不同目录的同名 SRT 会互相覆盖，
批量处理多目录时可能只剩一份结果、链式处理还会丢中间产物。
现在输出名统一为 `<12位路径哈希>__<原文件名>`，导出时由主程序剥掉前缀。
"""
import json
import sys

import pytest


def _write_srt(path, text="你好"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"1\n00:00:01,000 --> 00:00:03,000\n{text}\n", encoding="utf-8")
    return path


class _StubProcessor:
    """顶替 SubtitleRuleProcessor：只验证输出命名，不做规则处理。"""

    def load_rules(self):
        pass

    def reset_profanity_count(self):
        pass

    def process_text(self, text):
        return text

    def get_profanity_count(self):
        return 0


# ---------------------------------------------------------------- 命名规则


def test_same_basename_in_different_dirs_gets_different_prefix(keyword_common_module):
    first = keyword_common_module.cache_output_name("C:/a/ep01.srt")
    second = keyword_common_module.cache_output_name("C:/b/ep01.srt")

    assert first != second
    assert first.endswith("__ep01.srt")
    assert second.endswith("__ep01.srt")
    assert len(first.split("__")[0]) == 12


def test_prefix_is_stable_and_idempotent(keyword_common_module):
    name = keyword_common_module.cache_output_name("C:/a/ep01.srt")

    assert keyword_common_module.cache_output_name("C:/a/ep01.srt") == name
    # 已经带前缀的中间产物沿用原名，不叠加第二层
    assert keyword_common_module.cache_output_name(name) == name


def test_strip_restores_original_name(keyword_common_module):
    name = keyword_common_module.cache_output_name("C:/a/ep01.srt")

    assert keyword_common_module.strip_cache_prefix(name) == "ep01.srt"
    assert keyword_common_module.strip_cache_prefix("ep01.srt") == "ep01.srt"
    # 不是 12 位十六进制的“前缀”不能误剥
    assert keyword_common_module.strip_cache_prefix("zzz__ep01.srt") == "zzz__ep01.srt"


def test_both_plugins_share_the_same_convention(keyword_common_module, prefix_plugin_module, tmp_path):
    source = str(tmp_path / "ep01.srt")

    assert prefix_plugin_module.cache_output_name(source) == keyword_common_module.cache_output_name(source)
    assert prefix_plugin_module.strip_cache_prefix("0123456789ab__ep01.srt") == "ep01.srt"


# ---------------------------------------------------------------- 插件端到端


def test_keyword_plugin_keeps_both_same_name_outputs(keyword_processor_module, monkeypatch, tmp_path, capsys):
    first = _write_srt(tmp_path / "dir1" / "ep01.srt", "第一条")
    second = _write_srt(tmp_path / "dir2" / "ep01.srt", "第二条")
    cache_dir = tmp_path / "cache"

    monkeypatch.setattr(keyword_processor_module, "SubtitleRuleProcessor", _StubProcessor)
    keyword_processor_module.main(
        {"output_path": str(cache_dir), "pending_file_lists": [str(first), str(second)]}
    )

    outputs = sorted(p.name for p in cache_dir.iterdir())
    assert len(outputs) == 2, outputs
    assert all(name.endswith("__ep01.srt") for name in outputs)
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["processed"] == 2
    assert len(payload["completed_output_lists"]) == 2


def test_keyword_plugin_stats_use_original_name(keyword_processor_module, monkeypatch, tmp_path, capsys):
    source = _write_srt(tmp_path / "dir1" / "ep01.srt")
    cache_dir = tmp_path / "cache"

    monkeypatch.setattr(keyword_processor_module, "SubtitleRuleProcessor", _StubProcessor)
    keyword_processor_module.main({"output_path": str(cache_dir), "pending_file_lists": [str(source)]})

    payload = json.loads(capsys.readouterr().out.strip())
    message = payload["popup"]["message"]
    # 统计里显示原始文件名，不显示 12 位哈希
    assert "ep01" in message
    assert "__" not in message


def test_prefix_plugin_keeps_both_same_name_outputs(prefix_plugin_module, monkeypatch, tmp_path):
    first = _write_srt(tmp_path / "dir1" / "ep01.srt", "第一条")
    second = _write_srt(tmp_path / "dir2" / "ep01.srt", "第二条")
    cache_dir = tmp_path / "cache"

    monkeypatch.setattr(
        sys,
        "stdin",
        __import__("io").StringIO(
            json.dumps({"output_path": str(cache_dir), "pending_file_lists": [str(first), str(second)]},
                       ensure_ascii=False)
        ),
    )
    with pytest.raises(SystemExit):
        prefix_plugin_module.main()

    outputs = sorted(cache_dir.iterdir())
    assert len(outputs) == 2
    assert all(path.name.endswith("__ep01.srt") for path in outputs)
    # 说话人前缀用原始文件名，不带哈希
    assert all("ep01：第一条" in path.read_text(encoding="utf-8") or
               "ep01：第二条" in path.read_text(encoding="utf-8") for path in outputs)


def test_prefix_plugin_chained_input_keeps_original_speaker(prefix_plugin_module, monkeypatch, tmp_path):
    """链式处理时输入已带哈希前缀，说话人名仍应取 `ep01`。"""
    source = _write_srt(tmp_path / "0123456789ab__ep01.srt", "第一条")
    cache_dir = tmp_path / "cache"

    monkeypatch.setattr(
        sys,
        "stdin",
        __import__("io").StringIO(
            json.dumps({"output_path": str(cache_dir), "pending_file_lists": [str(source)]},
                       ensure_ascii=False)
        ),
    )
    with pytest.raises(SystemExit):
        prefix_plugin_module.main()

    outputs = list(cache_dir.iterdir())
    assert [path.name for path in outputs] == ["0123456789ab__ep01.srt"]
    assert "ep01：第一条" in outputs[0].read_text(encoding="utf-8")


# ---------------------------------------------------------------- 导出映射


def test_move_all_files_strips_prefix_and_dedups(main_program_module, tmp_path):
    cache_dir = tmp_path / "cache"
    out_dir = tmp_path / "out"
    cache_dir.mkdir()
    (cache_dir / "0123456789ab__ep01.srt").write_text("一", encoding="utf-8")
    (cache_dir / "abcdefabcdef__ep01.srt").write_text("二", encoding="utf-8")
    (cache_dir / "plain.srt").write_text("三", encoding="utf-8")

    main_program_module.move_all_files(str(cache_dir), str(out_dir))

    names = sorted(path.name for path in out_dir.iterdir())
    assert names == ["ep01.srt", "ep01_1.srt", "plain.srt"]
    assert list(cache_dir.iterdir()) == []
