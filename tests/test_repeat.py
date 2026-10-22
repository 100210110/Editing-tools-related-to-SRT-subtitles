"""repeat 规则回归测试：压缩、分隔、优先级、词次数口径及与 delete/replace 的顺序。"""
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = REPO_ROOT / "软件本体" / "plugins" / "srt关键词替换"


def _rules(repeat=None, delete=None, replace=None):
    return {
        "delete": delete or {"profanity": [], "others": []},
        "repeat": repeat or [],
        "replace": replace or [],
    }


def _repeat_rule(
    word,
    max_times=2,
    enabled=True,
    interval_enabled=False,
    min_consecutive=3,
    separator=" ",
):
    return {
        "word": word,
        "enabled": enabled,
        "max_times": max_times,
        "interval": {
            "enabled": interval_enabled,
            "min_consecutive": min_consecutive,
            "separator": separator,
        },
    }


@pytest.fixture
def load_processor(tmp_rules_dir):
    def _load(rules):
        tmp_rules_dir.write(rules)
        processor = tmp_rules_dir.processor()
        processor.load_rules()
        return processor

    return _load


def _count_builds(processor):
    calls = {"n": 0}
    original = processor._build_automaton

    def wrapped():
        calls["n"] += 1
        return original()

    processor._build_automaton = wrapped
    return calls


@pytest.mark.parametrize(
    "interval_enabled,min_consecutive,text,expected",
    [
        (True, 4, "哈哈哈", "哈哈"),
        (True, 3, "哈哈哈", "哈 哈"),
        (False, 3, "哈哈哈", "哈哈"),
    ],
    ids=["达标但不加分隔", "原始次数达门槛加分隔", "间隔关闭仍压缩"],
)
def test_压缩与分隔独立触发(load_processor, interval_enabled, min_consecutive, text, expected):
    """max_times 控制压缩，interval 只控制分隔；两者互不影响。"""
    processor = load_processor(
        _rules(
            repeat=[
                _repeat_rule(
                    "哈",
                    max_times=2,
                    interval_enabled=interval_enabled,
                    min_consecutive=min_consecutive,
                )
            ]
        )
    )

    assert processor.process_text(text) == expected


def test_原始次数门槛不按压缩后次数计算(load_processor):
    """原始 3 次达到 min_consecutive=3，即使压缩后只剩 2 个也应插入分隔符。"""
    processor = load_processor(
        _rules(
            repeat=[
                _repeat_rule(
                    "哈",
                    max_times=2,
                    interval_enabled=True,
                    min_consecutive=3,
                )
            ]
        )
    )

    assert processor.process_text("哈哈哈") == "哈 哈"


def test_外层禁用时整条规则跳过(load_processor):
    """enabled=false 的 repeat 规则不识别、不压缩、不加分隔符。"""
    processor = load_processor(
        _rules(repeat=[_repeat_rule("哈", enabled=False, interval_enabled=True)])
    )

    assert processor.repeat_rule_map == {}
    assert processor.repeat_automaton is None
    assert processor.process_text("哈哈哈哈") == "哈哈哈哈"


def test_多规则max_times小者优先(load_processor):
    """同起点命中多条规则时，max_times 更小的规则优先，即使词更短。"""
    processor = load_processor(
        _rules(
            repeat=[
                _repeat_rule("哈", max_times=2),
                _repeat_rule("哈哈", max_times=3),
            ]
        )
    )

    assert processor.process_text("哈哈哈哈哈哈") == "哈哈"


def test_多规则同max_times时长词优先(load_processor):
    """max_times 相同时，较长的重复词优先。"""
    processor = load_processor(
        _rules(
            repeat=[
                _repeat_rule("哈", max_times=3),
                _repeat_rule("哈哈", max_times=3),
            ]
        )
    )

    assert processor.process_text("哈哈哈哈") == "哈哈哈哈"


def test_重复次数按词出现次数计算(load_processor):
    """“哈哈”在“哈哈哈哈”中恰好出现 2 次，max_times=2 时不应压缩。"""
    processor = load_processor(_rules(repeat=[_repeat_rule("哈哈", max_times=2)]))

    assert processor.process_text("哈哈哈哈") == "哈哈哈哈"
    assert processor.process_text("哈哈哈哈哈哈") == "哈哈哈哈"


@pytest.mark.parametrize(
    "text",
    ["哈 哈 哈", "哈，哈，哈", "哈-哈", "哈\n哈"],
    ids=["空格", "中文逗号", "连字符", "换行"],
)
def test_带空格或标点不识别为重复(load_processor, text):
    """只识别无空格、无标点的连续同词重复。"""
    processor = load_processor(_rules(repeat=[_repeat_rule("哈", max_times=2)]))

    assert processor.process_text(text) == text


def test_删除替换先于重复且敏感词计数不变(load_processor):
    """delete/replace 先执行，repeat 后执行；repeat 不改变敏感词删除计数。"""
    processor = load_processor(
        _rules(
            delete={"profanity": ["傻逼"], "others": []},
            replace=[
                {
                    "word": "卡慕",
                    "type": "correction",
                    "enabled": True,
                    "source": ["卡布"],
                }
            ],
            repeat=[_repeat_rule("哈", max_times=3)],
        )
    )

    processor.reset_profanity_count()
    assert processor.process_text("傻逼卡布哈哈哈哈") == "卡慕哈哈哈"
    assert processor.get_profanity_count() == 1

    processor.reset_profanity_count()
    assert processor.process_text("傻逼哈哈哈哈") == "哈哈哈"
    assert processor.get_profanity_count() == 1


def test_缓存命中和失效路径下repeat状态一致(tmp_rules_dir):
    """分别走缓存命中与 JSON 变更失效重建路径，repeat 规则均应可用。"""
    base_rules = _rules(repeat=[_repeat_rule("哈", max_times=2)])
    tmp_rules_dir.write(base_rules)

    first = tmp_rules_dir.processor()
    first.load_rules()
    assert first.process_text("哈哈哈") == "哈哈"

    hit = tmp_rules_dir.processor()
    hit_calls = _count_builds(hit)
    hit.load_rules()
    assert hit_calls["n"] == 0
    assert sorted(hit.repeat_rule_map) == ["哈"]
    assert hit.process_text("哈哈哈") == "哈哈"

    changed_rules = _rules(
        repeat=[_repeat_rule("哈", max_times=2)],
        delete={"profanity": [], "others": ["测试词"]},
    )
    tmp_rules_dir.write(changed_rules)
    rebuilt = tmp_rules_dir.processor()
    rebuild_calls = _count_builds(rebuilt)
    rebuilt.load_rules()
    assert rebuild_calls["n"] == 1
    assert rebuilt.process_text("测试词哈哈哈") == "哈哈"


@pytest.mark.parametrize(
    "rules_file",
    ["subtitle_rules.json", "default_subtitle_rules.json"],
)
def test_真实规则文件中的repeat示例(load_processor, rules_file):
    """真实规则文件中的 repeat 示例应保持当前语义。"""
    with open(PLUGIN_DIR / rules_file, encoding="utf-8") as f:
        real_rules = json.load(f)
    assert real_rules.get("repeat"), f"{rules_file} 缺少 repeat 示例"

    processor = load_processor(real_rules)

    assert processor.process_text("完了完了完了") == "完了 完了"
    assert processor.process_text("哈哈哈哈") == "哈哈哈"
