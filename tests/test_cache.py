"""pkl 缓存校验回归测试：冷启动、命中、内容/格式变化、schema/哈希失效与强制重建。"""


def _rules(extra_delete=None):
    return {
        "delete": {
            "profanity": ["傻逼"],
            "others": list(extra_delete or []),
        },
        "repeat": [
            {
                "word": "哈",
                "enabled": True,
                "max_times": 2,
                "interval": {
                    "enabled": False,
                    "min_consecutive": 3,
                    "separator": " ",
                },
            }
        ],
        "replace": [
            {
                "word": "卡慕",
                "type": "correction",
                "enabled": True,
                "source": ["卡布"],
            }
        ],
    }


def _count_builds(processor):
    calls = {"n": 0}
    original = processor._build_automaton

    def wrapped():
        calls["n"] += 1
        return original()

    processor._build_automaton = wrapped
    return calls


def test_冷启动重建并写入哈希与schema(tmp_rules_dir):
    """pkl 不存在时应重建，并写入 json_content_hash 与 schema_version。"""
    tmp_rules_dir.write(_rules())
    processor = tmp_rules_dir.processor()
    calls = _count_builds(processor)

    assert not tmp_rules_dir.cache_path.exists()
    processor.load_rules()

    assert calls["n"] == 1
    assert tmp_rules_dir.cache_path.exists()
    payload = tmp_rules_dir.payload()
    assert payload["schema_version"] == tmp_rules_dir.module.CACHE_SCHEMA_VERSION
    assert payload["json_content_hash"] == tmp_rules_dir.expected_hash()
    assert payload["repeat_automaton"] is not None
    assert sorted(payload["repeat_rule_map"]) == ["哈"]

    processor.reset_profanity_count()
    assert processor.process_text("傻逼卡布哈哈哈") == "卡慕哈哈"
    assert processor.get_profanity_count() == 1


def test_连续加载第二次命中(tmp_rules_dir):
    """相同 JSON 连续加载两次，第二次应命中缓存而不重建。"""
    tmp_rules_dir.write(_rules())
    first = tmp_rules_dir.processor()
    first.load_rules()

    second = tmp_rules_dir.processor()
    calls = _count_builds(second)
    second.load_rules()

    assert calls["n"] == 0
    second.reset_profanity_count()
    assert second.process_text("傻逼卡布哈哈哈") == "卡慕哈哈"
    assert second.get_profanity_count() == 1


def test_json内容变化触发重建(tmp_rules_dir):
    """增删改规则内容应使缓存失效，并应用新规则。"""
    tmp_rules_dir.write(_rules())
    first = tmp_rules_dir.processor()
    first.load_rules()

    tmp_rules_dir.write(_rules(extra_delete=["测试词"]))
    second = tmp_rules_dir.processor()
    calls = _count_builds(second)
    second.load_rules()

    assert calls["n"] == 1
    assert second.process_text("测试词哈") == "哈"
    assert tmp_rules_dir.payload()["json_content_hash"] == tmp_rules_dir.expected_hash()


def test_json仅格式化仍命中缓存(tmp_rules_dir):
    """键顺序与缩进变化不改变内容哈希，缓存应继续命中。"""
    tmp_rules_dir.write(_rules())
    first = tmp_rules_dir.processor()
    first.load_rules()

    original = _rules()
    reordered = {
        "replace": original["replace"],
        "repeat": original["repeat"],
        "delete": original["delete"],
    }
    tmp_rules_dir.write(reordered, indent=2)

    second = tmp_rules_dir.processor()
    calls = _count_builds(second)
    second.load_rules()

    assert calls["n"] == 0
    assert second.process_text("傻逼卡布哈哈哈") == "卡慕哈哈"


def test_schema版本不匹配触发重建(tmp_rules_dir):
    """载荷 schema_version 与常量不一致时应失效重建。"""
    tmp_rules_dir.write(_rules())
    first = tmp_rules_dir.processor()
    first.load_rules()

    payload = tmp_rules_dir.payload()
    payload["schema_version"] = 1
    tmp_rules_dir.write_payload(payload)

    second = tmp_rules_dir.processor()
    calls = _count_builds(second)
    second.load_rules()

    assert calls["n"] == 1
    assert second.process_text("傻逼卡布哈哈哈") == "卡慕哈哈"
    assert tmp_rules_dir.payload()["schema_version"] == tmp_rules_dir.module.CACHE_SCHEMA_VERSION


def test_json内容哈希不匹配触发重建(tmp_rules_dir):
    """载荷 json_content_hash 与当前 JSON 不一致时应失效重建。"""
    tmp_rules_dir.write(_rules())
    first = tmp_rules_dir.processor()
    first.load_rules()

    payload = tmp_rules_dir.payload()
    payload["json_content_hash"] = "0" * 64
    tmp_rules_dir.write_payload(payload)

    second = tmp_rules_dir.processor()
    calls = _count_builds(second)
    second.load_rules()

    assert calls["n"] == 1
    assert tmp_rules_dir.payload()["json_content_hash"] == tmp_rules_dir.expected_hash()


def test_损坏pkl自动重建不崩溃(tmp_rules_dir):
    """pkl 写入随机字节时应捕获异常并自动重建。"""
    tmp_rules_dir.write(_rules())
    tmp_rules_dir.cache_path.write_bytes(b"not a pickle\x00\xff")
    processor = tmp_rules_dir.processor()
    calls = _count_builds(processor)

    processor.load_rules()

    assert calls["n"] == 1
    assert processor.process_text("傻逼卡布哈哈哈") == "卡慕哈哈"
    assert tmp_rules_dir.payload()["schema_version"] == tmp_rules_dir.module.CACHE_SCHEMA_VERSION


def test_旧载荷缺少新字段自动重建(tmp_rules_dir):
    """旧 pkl 缺少哈希/schema 字段时应失效重建。"""
    tmp_rules_dir.write(_rules())
    first = tmp_rules_dir.processor()
    first.load_rules()

    payload = tmp_rules_dir.payload()
    payload.pop("schema_version", None)
    payload.pop("json_content_hash", None)
    tmp_rules_dir.write_payload(payload)

    second = tmp_rules_dir.processor()
    calls = _count_builds(second)
    second.load_rules()

    assert calls["n"] == 1
    assert second.process_text("傻逼卡布哈哈哈") == "卡慕哈哈"
    assert "schema_version" in tmp_rules_dir.payload()


def test_force_rebuild强制重建并更新哈希(tmp_rules_dir):
    """JSON 变化后调用 force_rebuild=True 应跳过缓存并写回新哈希。"""
    tmp_rules_dir.write(_rules())
    processor = tmp_rules_dir.processor()
    processor.load_rules()

    tmp_rules_dir.write(_rules(extra_delete=["强制词"]))
    calls = _count_builds(processor)
    processor.load_rules(force_rebuild=True)

    assert calls["n"] == 1
    assert processor.process_text("强制词哈") == "哈"
    assert tmp_rules_dir.payload()["json_content_hash"] == tmp_rules_dir.expected_hash()


def test_命中与重建路径repeat状态均恢复(tmp_rules_dir):
    """缓存命中与失效重建后，repeat_rule_map 与 repeat 行为都应一致。"""
    tmp_rules_dir.write(_rules())
    first = tmp_rules_dir.processor()
    first.load_rules()
    assert first.process_text("哈哈哈") == "哈哈"

    hit = tmp_rules_dir.processor()
    hit_calls = _count_builds(hit)
    hit.load_rules()
    assert hit_calls["n"] == 0
    assert sorted(hit.repeat_rule_map) == ["哈"]
    assert hit.process_text("哈哈哈") == "哈哈"

    tmp_rules_dir.write(_rules(extra_delete=["测试词"]))
    rebuilt = tmp_rules_dir.processor()
    rebuild_calls = _count_builds(rebuilt)
    rebuilt.load_rules()
    assert rebuild_calls["n"] == 1
    assert sorted(rebuilt.repeat_rule_map) == ["哈"]
    assert rebuilt.process_text("哈哈哈") == "哈哈"
