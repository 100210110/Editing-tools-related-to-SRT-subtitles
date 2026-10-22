"""拖放路径解析回归测试（TODO #22）。

历史问题：无花括号时直接按空格拆分，`C:\\my subtitle.srt` 会被拆成两段。
现在改为花括号优先分组，无花括号时用“合并后磁盘上确实存在”的保守判据还原带空格路径。
"""
import textwrap

import pytest


def test_braced_path_with_space(main_program_module):
    result = main_program_module.parse_dropped_files("{C:/Users/abc/my subtitle.srt}")
    assert result == ["C:/Users/abc/my subtitle.srt"]


def test_braced_multiple_paths(main_program_module):
    data = "{C:/a b/1.srt} {D:/x/2.srt}"
    assert main_program_module.parse_dropped_files(data) == ["C:/a b/1.srt", "D:/x/2.srt"]


def test_braced_chinese_path_with_space(main_program_module):
    data = "{E:/项目 资料/第一集 字幕.srt} {E:/项目 资料/第二集.srt}"
    assert main_program_module.parse_dropped_files(data) == [
        "E:/项目 资料/第一集 字幕.srt",
        "E:/项目 资料/第二集.srt",
    ]


def test_braced_windows_backslash_path(main_program_module):
    result = main_program_module.parse_dropped_files(r"{C:\Users\abc\my subtitle.srt}")
    assert result == [r"C:\Users\abc\my subtitle.srt"]


def test_unbraced_plain_paths_split_by_space(main_program_module):
    data = "C:/a/1.srt D:/b/2.srt"
    assert main_program_module.parse_dropped_files(data) == ["C:/a/1.srt", "D:/b/2.srt"]


def test_unbraced_real_file_with_space_is_kept_whole(main_program_module, tmp_path):
    target = tmp_path / "my subtitle.srt"
    target.write_text("1\n", encoding="utf-8")

    result = main_program_module.parse_dropped_files(str(target))

    assert result == [str(target)]


def test_unbraced_two_real_files_with_spaces(main_program_module, tmp_path):
    first = tmp_path / "my subtitle.srt"
    second = tmp_path / "another subtitle.srt"
    first.write_text("1\n", encoding="utf-8")
    second.write_text("2\n", encoding="utf-8")

    result = main_program_module.parse_dropped_files(f"{first} {second}")

    assert result == [str(first), str(second)]


def test_mixed_braced_and_unbraced(main_program_module):
    data = "{C:/a b/1.srt} C:/plain/2.srt"
    assert main_program_module.parse_dropped_files(data) == ["C:/a b/1.srt", "C:/plain/2.srt"]


def test_newline_separated_paths(main_program_module):
    data = textwrap.dedent(
        """\
        C:/a/1.srt
        C:/b/2.srt
        """
    )
    assert main_program_module.parse_dropped_files(data) == ["C:/a/1.srt", "C:/b/2.srt"]


def test_empty_and_whitespace_input(main_program_module):
    assert main_program_module.parse_dropped_files("") == []
    assert main_program_module.parse_dropped_files("   \n\t ") == []


def test_unclosed_brace_falls_back(main_program_module, tmp_path):
    """括号没闭合时不能崩，也不应吞掉后续路径。"""
    data = "{C:/a b/1.srt"
    result = main_program_module.parse_dropped_files(data)
    assert result == ["{C:/a", "b/1.srt"]

    target = tmp_path / "a b.srt"
    target.write_text("1\n", encoding="utf-8")
    assert main_program_module.parse_dropped_files(str(target)) == [str(target)]
