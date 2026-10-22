"""srt加前缀 插件回归测试：块解析、幂等判断与计数语义（TODO #11）。"""
import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_PATH = REPO_ROOT / "软件本体" / "plugins" / "srt加前缀" / "自动给srt加前缀.py"


@pytest.fixture(scope="module")
def prefix_module():
    """按文件路径加载插件模块。

    模块在 import 期就会把 sys.stdin/stdout/stderr 换成 UTF-8 包装器，
    因此先塞入带 buffer 的占位流，加载完再还原，避免污染 pytest 的捕获对象。
    """
    saved = (sys.stdin, sys.stdout, sys.stderr)
    sys.stdin = io.TextIOWrapper(io.BytesIO())
    sys.stdout = io.TextIOWrapper(io.BytesIO())
    sys.stderr = io.TextIOWrapper(io.BytesIO())
    try:
        spec = importlib.util.spec_from_file_location(
            "retoolbox_srt_prefix_under_test", PLUGIN_PATH
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    finally:
        sys.stdin, sys.stdout, sys.stderr = saved
    return module


def write_source(path, text, encoding="utf-8"):
    """按字节写入，避免 Windows 换行转换干扰行尾断言。"""
    path.write_bytes(text.encode(encoding))
    return path


def read_text(path):
    return path.read_text(encoding="utf-8")


def block(index, start, end, text):
    return f"{index}\n{start} --> {end}\n{text}"


TIMELINE = "00:00:01,000 --> 00:00:03,000"


# ---------------------------------------------------------------- 块解析


def test_single_block_gets_prefix(tmp_path, prefix_module):
    src = write_source(tmp_path / "ep01.srt", block(1, "00:00:01,000", "00:00:03,000", "你好") + "\n")
    out = tmp_path / "cache" / "ep01.srt"

    count, prefixed = prefix_module.add_char_to_srt(src, "ep01：", out)

    assert (count, prefixed) == (1, True)
    assert read_text(out) == block(1, "00:00:01,000", "00:00:03,000", "ep01：你好") + "\n"


def test_multiple_blocks_all_prefixed(tmp_path, prefix_module):
    text = (
        block(1, "00:00:01,000", "00:00:03,000", "第一句")
        + "\n\n"
        + block(2, "00:00:04,000", "00:00:06,000", "第二句")
        + "\n"
    )
    src = write_source(tmp_path / "ep02.srt", text)
    out = tmp_path / "cache" / "ep02.srt"

    count, prefixed = prefix_module.add_char_to_srt(src, "ep02：", out)

    assert (count, prefixed) == (2, True)
    assert read_text(out) == (
        block(1, "00:00:01,000", "00:00:03,000", "ep02：第一句")
        + "\n\n"
        + block(2, "00:00:04,000", "00:00:06,000", "ep02：第二句")
        + "\n"
    )


def test_multiline_text_only_first_line_prefixed(tmp_path, prefix_module):
    src = write_source(
        tmp_path / "ep03.srt",
        block(1, "00:00:01,000", "00:00:03,000", "第一行\n第二行") + "\n",
    )
    out = tmp_path / "cache" / "ep03.srt"

    prefix_module.add_char_to_srt(src, "ep03：", out)

    assert read_text(out) == block(1, "00:00:01,000", "00:00:03,000", "ep03：第一行\n第二行") + "\n"


def test_missing_index_line_still_recognized(tmp_path, prefix_module):
    src = write_source(tmp_path / "ep04.srt", f"{TIMELINE}\n你好\n")
    out = tmp_path / "cache" / "ep04.srt"

    count, prefixed = prefix_module.add_char_to_srt(src, "ep04：", out)

    assert (count, prefixed) == (1, True)
    assert read_text(out) == f"{TIMELINE}\nep04：你好\n"


def test_dot_millisecond_separator(tmp_path, prefix_module):
    src = write_source(
        tmp_path / "ep05.srt",
        "1\n00:00:01.000 --> 00:00:03.000\n你好\n",
    )
    out = tmp_path / "cache" / "ep05.srt"

    count, prefixed = prefix_module.add_char_to_srt(src, "ep05：", out)

    assert (count, prefixed) == (1, True)
    assert read_text(out) == "1\n00:00:01.000 --> 00:00:03.000\nep05：你好\n"


def test_crlf_input_is_accepted(tmp_path, prefix_module):
    src = write_source(
        tmp_path / "ep06.srt",
        "1\r\n00:00:01,000 --> 00:00:03,000\r\n你好\r\n\r\n2\r\n00:00:04,000 --> 00:00:06,000\r\n再见\r\n",
    )
    out = tmp_path / "cache" / "ep06.srt"

    count, prefixed = prefix_module.add_char_to_srt(src, "ep06：", out)

    assert (count, prefixed) == (2, True)
    assert read_text(out) == (
        "1\n00:00:01,000 --> 00:00:03,000\nep06：你好\n\n"
        "2\n00:00:04,000 --> 00:00:06,000\nep06：再见\n"
    )


def test_bom_read_but_not_written(tmp_path, prefix_module):
    src = write_source(
        tmp_path / "ep07.srt",
        "\ufeff1\n00:00:01,000 --> 00:00:03,000\n你好\n",
    )
    out = tmp_path / "cache" / "ep07.srt"

    count, prefixed = prefix_module.add_char_to_srt(src, "ep07：", out)

    assert (count, prefixed) == (1, True)
    raw = out.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert read_text(out) == "1\n00:00:01,000 --> 00:00:03,000\nep07：你好\n"


def test_consecutive_blank_lines_collapse_to_one_separator(tmp_path, prefix_module):
    text = (
        block(1, "00:00:01,000", "00:00:03,000", "第一句")
        + "\n\n\n\n"
        + block(2, "00:00:04,000", "00:00:06,000", "第二句")
        + "\n"
    )
    src = write_source(tmp_path / "ep08.srt", text)
    out = tmp_path / "cache" / "ep08.srt"

    count, _ = prefix_module.add_char_to_srt(src, "ep08：", out)

    assert count == 2
    assert read_text(out) == (
        block(1, "00:00:01,000", "00:00:03,000", "ep08：第一句")
        + "\n\n"
        + block(2, "00:00:04,000", "00:00:06,000", "ep08：第二句")
        + "\n"
    )


def test_missing_trailing_blank_line(tmp_path, prefix_module):
    src = write_source(
        tmp_path / "ep09.srt",
        block(1, "00:00:01,000", "00:00:03,000", "你好"),
    )
    out = tmp_path / "cache" / "ep09.srt"

    count, prefixed = prefix_module.add_char_to_srt(src, "ep09：", out)

    assert (count, prefixed) == (1, True)
    assert read_text(out) == block(1, "00:00:01,000", "00:00:03,000", "ep09：你好") + "\n"


def test_block_without_timeline_is_preserved_verbatim(tmp_path, prefix_module):
    text = (
        "WEBVTT\n\n"
        + block(1, "00:00:01,000", "00:00:03,000", "你好")
        + "\n"
    )
    src = write_source(tmp_path / "ep10.srt", text)
    out = tmp_path / "cache" / "ep10.srt"

    count, prefixed = prefix_module.add_char_to_srt(src, "ep10：", out)

    assert (count, prefixed) == (1, True)
    assert read_text(out) == (
        "WEBVTT\n\n" + block(1, "00:00:01,000", "00:00:03,000", "ep10：你好") + "\n"
    )


# ---------------------------------------------------------------- 幂等判断


def test_idempotent_skips_when_prefix_matches_filename(tmp_path, prefix_module):
    original = block(1, "00:00:01,000", "00:00:03,000", "ep11：你好") + "\n"
    src = write_source(tmp_path / "ep11.srt", original)
    out = tmp_path / "cache" / "ep11.srt"

    count, prefixed = prefix_module.add_char_to_srt(src, "ep11：", out)

    assert (count, prefixed) == (1, False)
    assert read_text(out) == original
    assert read_text(out).count("ep11：") == 1


def test_idempotent_does_not_skip_other_prefix(tmp_path, prefix_module):
    src = write_source(
        tmp_path / "ep12.srt",
        block(1, "00:00:01,000", "00:00:03,000", "主持人：你好") + "\n",
    )
    out = tmp_path / "cache" / "ep12.srt"

    count, prefixed = prefix_module.add_char_to_srt(src, "ep12：", out)

    assert (count, prefixed) == (1, True)
    assert read_text(out) == block(1, "00:00:01,000", "00:00:03,000", "ep12：主持人：你好") + "\n"


def test_idempotent_judged_by_first_text_line_only(tmp_path, prefix_module):
    src = write_source(
        tmp_path / "ep13.srt",
        block(1, "00:00:01,000", "00:00:03,000", "ep13：第一行\n第二行") + "\n",
    )
    out = tmp_path / "cache" / "ep13.srt"

    count, prefixed = prefix_module.add_char_to_srt(src, "ep13：", out)

    assert (count, prefixed) == (1, False)
    assert read_text(out) == block(1, "00:00:01,000", "00:00:03,000", "ep13：第一行\n第二行") + "\n"


def test_mixed_blocks_only_unprefixed_get_prefix(tmp_path, prefix_module):
    text = (
        block(1, "00:00:01,000", "00:00:03,000", "ep14：已经有了")
        + "\n\n"
        + block(2, "00:00:04,000", "00:00:06,000", "还没有")
        + "\n"
    )
    src = write_source(tmp_path / "ep14.srt", text)
    out = tmp_path / "cache" / "ep14.srt"

    count, prefixed = prefix_module.add_char_to_srt(src, "ep14：", out)

    assert (count, prefixed) == (2, True)
    assert read_text(out) == (
        block(1, "00:00:01,000", "00:00:03,000", "ep14：已经有了")
        + "\n\n"
        + block(2, "00:00:04,000", "00:00:06,000", "ep14：还没有")
        + "\n"
    )


# ---------------------------------------------------------------- 失败分类


def test_empty_file_raises(tmp_path, prefix_module):
    src = write_source(tmp_path / "ep15.srt", "")

    with pytest.raises(prefix_module.SrtFormatError):
        prefix_module.add_char_to_srt(src, "ep15：", tmp_path / "cache" / "ep15.srt")


def test_whitespace_only_file_raises(tmp_path, prefix_module):
    src = write_source(tmp_path / "ep16.srt", "  \n\n\t\n")

    with pytest.raises(prefix_module.SrtFormatError):
        prefix_module.add_char_to_srt(src, "ep16：", tmp_path / "cache" / "ep16.srt")


def test_file_without_timeline_raises(tmp_path, prefix_module):
    src = write_source(tmp_path / "ep17.srt", "1\n这不是字幕\n2\n也不是\n")

    with pytest.raises(prefix_module.SrtFormatError):
        prefix_module.add_char_to_srt(src, "ep17：", tmp_path / "cache" / "ep17.srt")


# ---------------------------------------------------------------- main 端到端


@pytest.fixture
def run_main(prefix_module, monkeypatch):
    def _run(payload):
        monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload, ensure_ascii=False)))
        stdout = io.StringIO()
        stderr = io.StringIO()
        monkeypatch.setattr(sys, "stdout", stdout)
        monkeypatch.setattr(sys, "stderr", stderr)
        with pytest.raises(SystemExit) as excinfo:
            prefix_module.main()
        assert excinfo.value.code == 0
        return json.loads(stdout.getvalue()), stderr.getvalue()

    return _run


def test_main_mixed_input_counts(tmp_path, run_main):
    needs_prefix = write_source(
        tmp_path / "a.srt", block(1, "00:00:01,000", "00:00:03,000", "待处理") + "\n"
    )
    not_srt = write_source(tmp_path / "b.txt", "随便什么内容")
    empty = write_source(tmp_path / "c.srt", "")
    already = write_source(
        tmp_path / "d.srt", block(1, "00:00:01,000", "00:00:03,000", "d：已完成") + "\n"
    )
    no_timeline = write_source(tmp_path / "e.srt", "只有文本，没有时间轴\n")
    cache_dir = tmp_path / "cache" / "output"

    result, stderr = run_main(
        {
            "output_path": str(cache_dir),
            "pending_file_lists": [
                str(needs_prefix),
                str(not_srt),
                str(empty),
                str(already),
                str(no_timeline),
            ],
        }
    )

    assert result["total"] == 5
    assert result["processed"] == 2
    assert result["skipped"] == 2
    assert result["failed"] == 2
    assert result["status"] == "ok"
    assert result["popup"] is False

    completed = [Path(p) for p in result["completed_output_lists"]]
    assert completed == [cache_dir / "a.srt", cache_dir / "d.srt"]
    assert all(path.exists() for path in completed)

    assert read_text(cache_dir / "a.srt") == block(
        1, "00:00:01,000", "00:00:03,000", "a：待处理"
    ) + "\n"
    assert read_text(cache_dir / "d.srt") == block(
        1, "00:00:01,000", "00:00:03,000", "d：已完成"
    ) + "\n"
    assert not (cache_dir / "c.srt").exists()
    assert not (cache_dir / "e.srt").exists()
    assert "跳过非 SRT 文件" in stderr


def test_main_all_success(tmp_path, run_main):
    first = write_source(
        tmp_path / "ep01.srt", block(1, "00:00:01,000", "00:00:03,000", "第一句") + "\n"
    )
    second = write_source(
        tmp_path / "ep02.srt",
        block(1, "00:00:01,000", "00:00:03,000", "第一行\n第二行") + "\n",
    )
    cache_dir = tmp_path / "cache" / "output"

    result, _ = run_main(
        {"output_path": str(cache_dir), "pending_file_lists": [str(first), str(second)]}
    )

    assert (result["total"], result["processed"], result["skipped"], result["failed"]) == (2, 2, 0, 0)
    assert len(result["completed_output_lists"]) == 2


def test_main_all_failed(tmp_path, run_main):
    empty = write_source(tmp_path / "ep01.srt", "")
    no_timeline = write_source(tmp_path / "ep02.srt", "没有时间轴\n")
    cache_dir = tmp_path / "cache" / "output"

    result, stderr = run_main(
        {"output_path": str(cache_dir), "pending_file_lists": [str(empty), str(no_timeline)]}
    )

    assert (result["total"], result["processed"], result["skipped"], result["failed"]) == (2, 0, 0, 2)
    assert result["completed_output_lists"] == []
    assert cache_dir.is_dir()
    assert list(cache_dir.iterdir()) == []
    assert "无有效字幕块" in stderr


def test_main_idempotent_copy_lands_in_cache(tmp_path, run_main):
    original = block(1, "00:00:01,000", "00:00:03,000", "ep03：已经带前缀") + "\n"
    already = write_source(tmp_path / "ep03.srt", original)
    cache_dir = tmp_path / "cache" / "output"

    result, _ = run_main(
        {"output_path": str(cache_dir), "pending_file_lists": [str(already)]}
    )

    assert (result["total"], result["processed"], result["skipped"], result["failed"]) == (1, 1, 1, 0)
    written = cache_dir / "ep03.srt"
    assert written.exists()
    assert read_text(written) == original
    assert read_text(written).count("ep03：") == 1


def test_main_only_non_srt_files(tmp_path, run_main):
    text_file = write_source(tmp_path / "notes.txt", "普通文本")
    cache_dir = tmp_path / "cache" / "output"

    result, _ = run_main(
        {"output_path": str(cache_dir), "pending_file_lists": [str(text_file)]}
    )

    assert (result["total"], result["processed"], result["skipped"], result["failed"]) == (1, 0, 1, 0)
    assert result["completed_output_lists"] == []
    assert list(cache_dir.iterdir()) == []
