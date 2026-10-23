"""单条字幕纯重复去重（TODO #28）回归测试。

规则摘要（作者 2026-10-23 定稿）：
- 阈值 ≥ 6 个字（等于即触发），标点当普通字符，只去首尾空白；
- 单元按**最小周期**判定，`呵呵呵呵` 是 `呵`×4，走单字分支；
- 单字循环输出 `哈 哈 哈`（保留 single_keep 个），多字循环输出 `嘿嘿哈哈 嘿嘿哈哈`；
- 严格模式（默认）：整行必须恰好是纯循环，判整行长度；非严格：只替换行内最长循环片段，判片段长度；
- 无论开关如何，导出时每行都去掉首尾空白。
"""
import json

import pytest

LINE_DEDUPE_DEFAULTS = {
    "enabled": True,
    "strict": True,
    "min_chars": 6,
    "single_keep": 3,
    "multi_keep": 2,
}


def make_processor(build_automaton_module, tmp_path, line_dedupe=None, repeat=None):
    """构造处理器；`line_dedupe=None` 表示规则文件里不写这个键（走默认值）。"""
    rules = {
        "delete": {"profanity": [], "others": []},
        "repeat": repeat or [],
        "replace": [],
    }
    if line_dedupe is not None:
        rules["line_dedupe"] = line_dedupe
    json_path = tmp_path / "subtitle_rules.json"
    json_path.write_text(json.dumps(rules, ensure_ascii=False), encoding="utf-8")
    processor = build_automaton_module.SubtitleRuleProcessor()
    processor.json_path = str(json_path)
    processor.cache_path = str(tmp_path / "subtitle_rules.pkl")
    processor.load_rules(force_rebuild=True)
    return processor


# ---------------------------------------------------------------- 阈值与分支


def test_threshold_is_inclusive(build_automaton_module, tmp_path):
    """5 个字不触发，6 个字（等于阈值）触发。"""
    processor = make_processor(build_automaton_module, tmp_path)
    assert processor.process_text("哈" * 5) == "哈" * 5
    assert processor.process_text("哈" * 6) == "哈 哈 哈"


def test_minimal_period_treats_same_char_as_single(build_automaton_module, tmp_path):
    """`呵呵呵呵呵` 的最小周期是 1，按单字循环处理，而不是双字 `呵呵`。"""
    processor = make_processor(build_automaton_module, tmp_path)
    assert processor.process_text("呵" * 7) == "呵 呵 呵"


def test_multi_char_unit_keeps_two(build_automaton_module, tmp_path):
    """周期 ≥2 的循环走多字分支，保留 multi_keep（默认 2）个单元。"""
    processor = make_processor(build_automaton_module, tmp_path)
    assert processor.process_text("嘿嘿哈哈" * 2) == "嘿嘿哈哈 嘿嘿哈哈"


def test_longer_unit_is_supported(build_automaton_module, tmp_path):
    """不设单元长度上限：4 字单元重复也能归一。"""
    processor = make_processor(build_automaton_module, tmp_path)
    assert processor.process_text("不可能吧" * 2) == "不可能吧 不可能吧"


# ---------------------------------------------------------------- 严格 / 非严格


def test_strict_mode_ignores_line_with_extra_chars(build_automaton_module, tmp_path):
    """严格模式下整行不是纯循环就不处理。"""
    processor = make_processor(build_automaton_module, tmp_path)
    assert processor.process_text("哈" * 6 + "草") == "哈" * 6 + "草"


def test_non_strict_mode_replaces_only_fragment(build_automaton_module, tmp_path):
    """非严格模式按「循环片段长度」判断，只替换片段，前后文字保留。"""
    processor = make_processor(
        build_automaton_module, tmp_path, line_dedupe={"strict": False}
    )
    assert processor.process_text("哈" * 6 + "草") == "哈 哈 哈草"
    assert processor.process_text("今天" + "嘿嘿哈哈" * 2 + "好") == "今天嘿嘿哈哈 嘿嘿哈哈好"


def test_non_strict_mode_needs_fragment_long_enough(build_automaton_module, tmp_path):
    """非严格模式同样受阈值约束：片段不到 6 个字不处理。"""
    processor = make_processor(
        build_automaton_module, tmp_path, line_dedupe={"strict": False}
    )
    assert processor.process_text("哈哈哈哈草") == "哈哈哈哈草"


# ---------------------------------------------------------------- 每行去空白


def test_every_line_is_stripped(build_automaton_module, tmp_path):
    """即使开关关闭，导出时每行也去掉首尾空白（含序号行与时间轴行）。"""
    processor = make_processor(build_automaton_module, tmp_path, line_dedupe={"enabled": False})
    text = (
        "  1  \n"
        "00:00:01,000 --> 00:00:03,000\n"
        "  随便一句话  \n"
        "\n"
        "  2  \n"
    )
    assert processor.process_text(text) == (
        "1\n"
        "00:00:01,000 --> 00:00:03,000\n"
        "随便一句话\n"
        "\n"
        "2\n"
    )


def test_structural_lines_are_not_deduped(build_automaton_module, tmp_path):
    """纯数字序号行与时间轴行不参与去重，避免误伤。"""
    processor = make_processor(build_automaton_module, tmp_path)
    assert processor.process_text("1111111") == "1111111"
    timecode = "00:00:00,000 --> 00:00:00,000"
    assert processor.process_text(timecode) == timecode


# ---------------------------------------------------------------- 与 repeat 的先后


def test_repeat_runs_before_line_dedupe(build_automaton_module, tmp_path):
    """repeat 先把 20 个「哈」压成 3 个，长度不足阈值，去重不再介入。"""
    processor = make_processor(
        build_automaton_module,
        tmp_path,
        repeat=[
            {
                "word": "哈",
                "enabled": True,
                "max_times": 3,
                "interval": {"enabled": False, "min_consecutive": 3, "separator": " "},
            }
        ],
    )
    assert processor.process_text("哈" * 20) == "哈哈哈"


# ---------------------------------------------------------------- 配置解析


def test_missing_key_uses_defaults(build_automaton_module, tmp_path):
    processor = make_processor(build_automaton_module, tmp_path)
    assert processor.line_dedupe_rule == LINE_DEDUPE_DEFAULTS


def test_invalid_values_fall_back(build_automaton_module, tmp_path):
    """类型不对或小于下限的字段回落到默认，合法字段保留。"""
    processor = make_processor(
        build_automaton_module,
        tmp_path,
        line_dedupe={
            "enabled": "yes",  # 不是 bool
            "strict": False,   # 合法
            "min_chars": 1,    # 小于下限 2
            "single_keep": 5,  # 合法
            "multi_keep": True  # bool 不能当数字
        },
    )
    assert processor.line_dedupe_rule == {
        "enabled": True,
        "strict": False,
        "min_chars": 6,
        "single_keep": 5,
        "multi_keep": 2,
    }


def test_custom_threshold_is_honoured(build_automaton_module, tmp_path):
    processor = make_processor(build_automaton_module, tmp_path, line_dedupe={"min_chars": 3})
    assert processor.process_text("呵呵呵") == "呵 呵 呵"


# ---------------------------------------------------------------- 缓存


def test_cache_schema_version_bumped(build_automaton_module):
    """行为依赖新配置，schema 必须递增，否则旧 pkl 不会重算。"""
    assert build_automaton_module.CACHE_SCHEMA_VERSION >= 3


def test_cache_roundtrip_keeps_line_dedupe(build_automaton_module, tmp_path):
    """缓存命中时也要恢复 line_dedupe 配置，行为与重建一致。"""
    first = make_processor(build_automaton_module, tmp_path, line_dedupe={"min_chars": 3})
    assert first.process_text("呵呵呵") == "呵 呵 呵"

    second = build_automaton_module.SubtitleRuleProcessor()
    second.json_path = first.json_path
    second.cache_path = first.cache_path
    second.load_rules()  # 不强制重建，走缓存
    assert second.line_dedupe_rule["min_chars"] == 3
    assert second.process_text("呵呵呵") == "呵 呵 呵"


# ---------------------------------------------------------------- 出厂规则


@pytest.mark.parametrize(
    "filename", ["subtitle_rules.json", "default_subtitle_rules.json"]
)
def test_factory_rules_contain_line_dedupe(filename):
    """两个出厂规则文件都要带默认配置，避免用户打开编辑器时看到空值。"""
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[1]
        / "软件本体" / "plugins" / "srt关键词替换" / filename
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["line_dedupe"] == LINE_DEDUPE_DEFAULTS


# ---------------------------------------------------------------- 编辑器侧


def test_editor_ensure_fills_defaults(rule_editor_module):
    data = {"delete": {}, "repeat": [], "replace": []}
    rule = rule_editor_module.ensure_line_dedupe(data)
    assert rule == LINE_DEDUPE_DEFAULTS
    assert data["line_dedupe"] == LINE_DEDUPE_DEFAULTS


def test_editor_ensure_keeps_valid_values(rule_editor_module):
    data = {"line_dedupe": {"enabled": False, "strict": False, "min_chars": 9}}
    rule = rule_editor_module.ensure_line_dedupe(data)
    assert rule == {
        "enabled": False,
        "strict": False,
        "min_chars": 9,
        "single_keep": 3,
        "multi_keep": 2,
    }


def test_editor_dialog_roundtrip(rule_editor_module, qt_app):
    dialog = rule_editor_module.LineDedupeDialog(
        {"enabled": False, "strict": False, "min_chars": 4, "single_keep": 2, "multi_keep": 5}
    )
    assert dialog.get_data() == {
        "enabled": False,
        "strict": False,
        "min_chars": 4,
        "single_keep": 2,
        "multi_keep": 5,
    }
