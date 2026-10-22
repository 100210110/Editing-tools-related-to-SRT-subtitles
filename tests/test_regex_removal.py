"""regex 规则类型移除回归测试（TODO #4）。

`regex` 从早期起就是个空分支（`_process_node` 里 `pass`），写了不生效也没有提示。
现在把它从 schema/编辑器/默认规则中移除：处理端遇到未知类型会告警，编辑器加载与保存
都会剔除 `type: "regex"` 节点。
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = REPO_ROOT / "软件本体" / "plugins" / "srt关键词替换"
BUILD_AUTOMATON_PATH = PLUGIN_DIR / "build_automaton.py"
RULE_JSONS = [
    PLUGIN_DIR / "subtitle_rules.json",
    PLUGIN_DIR / "default_subtitle_rules.json",
]


@pytest.fixture(scope="module")
def strip_regex_nodes(rule_editor_module):
    return rule_editor_module.strip_regex_nodes


# ---------------------------------------------------------------- 编辑器迁移


def test_strip_removes_toplevel_regex_node(strip_regex_nodes):
    data = {
        "replace": [
            {"word": "正则组", "type": "regex", "pattern": "a.*b"},
            {"word": "正常组", "type": "group", "items": []},
        ]
    }

    removed = strip_regex_nodes(data)

    assert removed == 1
    assert [node["word"] for node in data["replace"]] == ["正常组"]


def test_strip_removes_nested_regex_node(strip_regex_nodes):
    data = {
        "replace": [
            {
                "word": "外层",
                "type": "group",
                "items": [
                    {"word": "卡慕", "enabled": True, "source": ["卡布"]},
                    {"word": "正则", "type": "regex", "pattern": "x"},
                ],
            }
        ]
    }

    removed = strip_regex_nodes(data)

    assert removed == 1
    items = data["replace"][0]["items"]
    assert [node["word"] for node in items] == ["卡慕"]


def test_strip_counts_multiple_and_keeps_other_types(strip_regex_nodes):
    data = {
        "delete": {"profanity": ["傻逼"], "others": []},
        "repeat": [{"word": "哈", "enabled": True, "max_times": 2}],
        "replace": [
            {"word": "A", "type": "regex"},
            {"word": "B", "type": "group", "items": [{"word": "C", "type": "regex"}]},
            {"word": "D", "enabled": True, "source": ["d"]},
        ],
    }

    removed = strip_regex_nodes(data)

    assert removed == 2
    assert len(data["replace"]) == 2
    assert data["replace"][0]["items"] == []
    assert data["delete"]["profanity"] == ["傻逼"]
    assert data["repeat"][0]["word"] == "哈"


def test_strip_is_noop_without_regex(strip_regex_nodes):
    data = json.loads((PLUGIN_DIR / "default_subtitle_rules.json").read_text(encoding="utf-8"))

    assert strip_regex_nodes(data) == 0


def test_shipped_rule_files_have_no_regex_nodes():
    for path in RULE_JSONS:
        text = path.read_text(encoding="utf-8")
        assert '"regex"' not in text, f"{path.name} 仍然包含 regex 节点"


# ---------------------------------------------------------------- 处理端


def test_unknown_type_is_warned_not_silently_ignored(build_automaton_module, tmp_path, capsys):
    rules = {
        "delete": {"profanity": [], "others": []},
        "repeat": [],
        "replace": [
            {"word": "遗留正则", "type": "regex", "pattern": "a.*b"},
            {"word": "卡慕", "enabled": True, "source": ["卡布"]},
        ],
    }
    json_path = tmp_path / "subtitle_rules.json"
    json_path.write_text(json.dumps(rules, ensure_ascii=False), encoding="utf-8")

    processor = build_automaton_module.SubtitleRuleProcessor()
    processor.json_path = str(json_path)
    processor.cache_path = str(tmp_path / "subtitle_rules.pkl")
    processor.load_rules(force_rebuild=True)

    stderr = capsys.readouterr().err
    assert "未知规则节点类型" in stderr
    assert "regex" in stderr
    # 正常节点仍然生效
    assert processor.process_text("卡布来了") == "卡慕来了"
