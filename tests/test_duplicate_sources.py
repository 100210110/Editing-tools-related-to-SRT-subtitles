"""跨节点重复 source 检测回归测试（TODO #16）。

历史问题：不同节点的相同 `source` 后面覆盖前面，编辑器只防单个 item 内重复，
规则冲突既不容易发现，也没有任何提示。现在：
- 处理端构建映射时检测冲突、写入 `source_conflicts` 并在 stderr 告警；
- 编辑器保存前扫描全局 source，列出冲突并询问是否继续；
- 添加源词时若已被别的替换项占用，先提示再决定。
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


# ---------------------------------------------------------------- 扫描函数


def test_no_duplicates_returns_empty(keyword_common_module):
    rules = {"replace": [{"word": "卡慕", "enabled": True, "source": ["卡布", "卡莫"]}]}

    assert keyword_common_module.find_duplicate_sources(rules) == []


def test_cross_node_duplicate_detected(keyword_common_module):
    rules = {
        "replace": [
            {"word": "卡慕", "enabled": True, "source": ["卡布"]},
            {"word": "米洛", "enabled": True, "source": ["卡布", "米诺"]},
        ]
    }

    result = keyword_common_module.find_duplicate_sources(rules)

    assert result == [{"source": "卡布", "targets": ["卡慕", "米洛"]}]


def test_same_item_duplicate_is_not_a_conflict(keyword_common_module):
    """同一个替换项里写两遍不算跨节点冲突（清单一律去重）。"""
    rules = {"replace": [{"word": "卡慕", "enabled": True, "source": ["卡布", "卡布"]}]}

    assert keyword_common_module.find_duplicate_sources(rules) == []


def test_nested_groups_are_scanned(keyword_common_module):
    rules = {
        "replace": [
            {
                "word": "外层",
                "type": "group",
                "enabled": True,
                "items": [
                    {"word": "A", "enabled": True, "source": ["同源"]},
                    {"word": "B", "enabled": True, "source": ["同源"]},
                ],
            }
        ]
    }

    assert keyword_common_module.find_duplicate_sources(rules) == [
        {"source": "同源", "targets": ["A", "B"]}
    ]


def test_disabled_nodes_are_ignored(keyword_common_module):
    rules = {
        "replace": [
            {"word": "A", "enabled": True, "source": ["同源"]},
            {"word": "B", "enabled": False, "source": ["同源"]},
        ]
    }

    assert keyword_common_module.find_duplicate_sources(rules) == []


# ---------------------------------------------------------------- 处理端


def test_processor_records_conflict_and_warns(build_automaton_module, tmp_path, capsys):
    rules = {
        "delete": {"profanity": [], "others": []},
        "repeat": [],
        "replace": [
            {"word": "卡慕", "enabled": True, "source": ["卡布"]},
            {"word": "米洛", "enabled": True, "source": ["卡布"]},
        ],
    }

    processor = make_processor(build_automaton_module, tmp_path, rules)

    assert processor.source_conflicts == [("卡布", "卡慕", "米洛")]
    assert "卡布" in capsys.readouterr().err
    # 后写入者生效（保持原有语义）
    assert processor.process_text("卡布") == "米洛"


def test_processor_without_conflict_records_nothing(build_automaton_module, tmp_path):
    rules = {
        "delete": {"profanity": [], "others": []},
        "repeat": [],
        "replace": [{"word": "卡慕", "enabled": True, "source": ["卡布"]}],
    }

    processor = make_processor(build_automaton_module, tmp_path, rules)

    assert processor.source_conflicts == []


def test_shipped_rules_have_no_duplicate_sources(keyword_common_module):
    plugin_dir = __import__("pathlib").Path(__file__).resolve().parents[1] / "软件本体" / "plugins" / "srt关键词替换"
    for name in ("subtitle_rules.json", "default_subtitle_rules.json"):
        rules = json.loads((plugin_dir / name).read_text(encoding="utf-8"))
        assert keyword_common_module.find_duplicate_sources(rules) == [], name


# ---------------------------------------------------------------- 编辑器


@pytest.fixture
def silent_messages(rule_editor_module, monkeypatch):
    calls = {"question": [], "information": [], "critical": [], "warning": [], "answer": "No"}

    def question(*args, **kwargs):
        calls["question"].append(args)
        return (
            rule_editor_module.QMessageBox.Yes
            if calls["answer"] == "Yes"
            else rule_editor_module.QMessageBox.No
        )

    monkeypatch.setattr(rule_editor_module.QMessageBox, "question", question)
    for name in ("information", "critical", "warning"):
        monkeypatch.setattr(
            rule_editor_module.QMessageBox, name,
            lambda *a, _n=name, **k: calls[_n].append(a),
        )
    return calls


def test_save_blocks_on_duplicate_sources(rule_editor_module, qt_app, silent_messages, tmp_path):
    editor = rule_editor_module.SubtitleEditor()
    target = tmp_path / "rules.json"
    try:
        editor.data = {
            "delete": {"profanity": [], "others": []},
            "repeat": [],
            "replace": [
                {"word": "卡慕", "enabled": True, "source": ["卡布"]},
                {"word": "米洛", "enabled": True, "source": ["卡布"]},
            ],
        }
        silent_messages["answer"] = "No"

        assert editor.save_to_file(str(target)) is False
        assert not target.exists()
        assert silent_messages["question"], "应弹出冲突确认框"
        message = " ".join(str(part) for part in silent_messages["question"][0])
        assert "卡布" in message
    finally:
        editor.close()


def test_save_proceeds_when_user_confirms(rule_editor_module, qt_app, silent_messages, tmp_path):
    editor = rule_editor_module.SubtitleEditor()
    target = tmp_path / "rules.json"
    try:
        editor.data = {
            "delete": {"profanity": [], "others": []},
            "repeat": [],
            "replace": [
                {"word": "卡慕", "enabled": True, "source": ["卡布"]},
                {"word": "米洛", "enabled": True, "source": ["卡布"]},
            ],
        }
        silent_messages["answer"] = "Yes"

        assert editor.save_to_file(str(target)) is True
        assert target.exists()
    finally:
        editor.close()


def test_collect_sources_maps_source_to_owner(rule_editor_module, qt_app, silent_messages):
    editor = rule_editor_module.SubtitleEditor()
    try:
        editor.data = {
            "delete": {"profanity": [], "others": []},
            "repeat": [],
            "replace": [
                {"word": "外层", "type": "group", "enabled": True,
                 "items": [{"word": "卡慕", "enabled": True, "source": ["卡布", "卡莫"]}]}
            ],
        }

        mapping = editor.collect_sources()

        assert mapping["卡布"] == ["卡慕"]
        assert mapping["卡莫"] == ["卡慕"]
    finally:
        editor.close()
