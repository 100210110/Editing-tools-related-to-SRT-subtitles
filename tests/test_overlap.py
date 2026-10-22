"""重叠匹配选择策略回归测试（TODO #15）。

历史问题：`_resolve_overlaps()` 按 (start 升序, end 降序) 排序后线性过滤，
只有"同起点"时才是长词优先；起点更早的短词会先占位，把后面更长的词挤掉。
现改为按 (长度降序, 起点升序) 的区间调度，"长词优先"对任意起点组合都成立。
"""
import json

import pytest


def make_processor(build_automaton_module, tmp_path, rules):
    json_path = tmp_path / "subtitle_rules.json"
    json_path.write_text(json.dumps(rules, ensure_ascii=False), encoding="utf-8")
    processor = build_automaton_module.SubtitleRuleProcessor()
    processor.json_path = str(json_path)
    processor.cache_path = str(tmp_path / "subtitle_rules.pkl")
    processor.load_rules(force_rebuild=True)
    return processor


def rules_with(delete=(), replace=()):
    return {
        "delete": {"profanity": [], "others": list(delete)},
        "repeat": [],
        "replace": [
            {"word": correct, "enabled": True, "source": [source]} for source, correct in replace
        ],
    }


# ---------------------------------------------------------------- 端到端


def test_later_longer_word_beats_earlier_short_word(build_automaton_module, tmp_path):
    """`abcdef` 中 `ab`(0-2) 与 `bcde`(1-5) 重叠：更长且起点更晚的 `bcde` 应当胜出。"""
    processor = make_processor(
        build_automaton_module, tmp_path, rules_with(delete=["ab"], replace=[("bcde", "X")])
    )

    assert processor.process_text("abcdef") == "aXf"


def test_contained_word_is_dropped(build_automaton_module, tmp_path):
    """`b` 完全落在 `abc` 内部，短词应被丢弃。"""
    processor = make_processor(
        build_automaton_module, tmp_path, rules_with(delete=["abc", "b"])
    )

    assert processor.process_text("abc") == ""


def test_same_start_prefers_longer(build_automaton_module, tmp_path):
    processor = make_processor(
        build_automaton_module, tmp_path, rules_with(delete=["ab"], replace=[("abcd", "Z")])
    )

    assert processor.process_text("abcd") == "Z"


def test_non_overlapping_matches_both_applied(build_automaton_module, tmp_path):
    processor = make_processor(
        build_automaton_module, tmp_path, rules_with(delete=["ab"], replace=[("ef", "Z")])
    )

    assert processor.process_text("abcdef") == "cdZ"


def test_equal_length_overlap_prefers_earlier_start(build_automaton_module, tmp_path):
    """等长且重叠时按起点升序取第一个，保证结果确定。"""
    processor = make_processor(
        build_automaton_module, tmp_path, rules_with(delete=["ab"], replace=[("bc", "X")])
    )

    assert processor.process_text("abc") == "c"


def test_long_word_priority_is_order_independent(build_automaton_module):
    """`_resolve_overlaps` 的结果不应取决于匹配到达顺序（自动机遍历顺序可能变化）。"""
    processor = build_automaton_module.SubtitleRuleProcessor()
    matches = [
        (0, 2, ("delete", "ab")),
        (1, 5, ("replace", "bcde", "X")),
        (5, 7, ("delete", "fg")),
    ]

    forward = processor._resolve_overlaps(list(matches))
    backward = processor._resolve_overlaps(list(reversed(matches)))

    assert forward == backward
    assert [(start, end) for start, end, _ in forward] == [(1, 5), (5, 7)]


def test_profanity_count_follows_selected_matches(build_automaton_module, tmp_path):
    """被挤掉的重叠短词不计入敏感词次数。"""
    rules = {
        "delete": {"profanity": ["ab"], "others": []},
        "repeat": [],
        "replace": [{"word": "X", "enabled": True, "source": ["bcde"]}],
    }
    processor = make_processor(build_automaton_module, tmp_path, rules)

    processor.reset_profanity_count()
    assert processor.process_text("abcdef") == "aXf"
    assert processor.get_profanity_count() == 0
