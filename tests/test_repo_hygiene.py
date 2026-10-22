"""仓库卫生回归测试（TODO #21）。

运行产物（`cache/`、`plugin_log/`、`*.pkl`、`*.log`）不应再进入版本控制。
这里同时守住两件事：`.gitignore` 规则还在，以及索引里确实没有这些文件。
"""
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATTERNS = [
    "*.log",
    "*.pkl",
    "软件本体/cache/output/",
    "软件本体/cache/temp/",
    "软件本体/cache/plugin_backup/",
    "软件本体/output/",
    "软件本体/plugins/*/plugin_log/",
    "__pycache__/",
]

# 典型运行产物：必须被忽略，且不得出现在 git 索引里
RUNTIME_PATHS = [
    "软件本体/cache/temp/ffmpeg-20260501-204631.log",
    "软件本体/cache/output/输出.srt",
    "软件本体/plugins/srt关键词替换/subtitle_rules.pkl",
    "软件本体/plugins/srt关键词替换/plugin_log/plugin_error.log",
    "软件本体/output/导出.srt",
]


def _git(*args, check=True):
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=check,
    )


@pytest.fixture(scope="module")
def git_available():
    result = subprocess.run(
        ["git", "--version"], capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        pytest.skip("当前环境没有可用的 git")
    return True


def test_gitignore_exists_and_covers_runtime_artifacts():
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")

    for pattern in REQUIRED_PATTERNS:
        assert pattern in gitignore, f".gitignore 缺少规则: {pattern}"


def test_runtime_artifacts_are_ignored(git_available):
    for path in RUNTIME_PATHS:
        result = _git("check-ignore", "-q", path, check=False)
        assert result.returncode == 0, f"运行产物未被忽略: {path}"


def test_no_runtime_artifacts_tracked(git_available):
    tracked = _git("ls-files").stdout.splitlines()

    offenders = [
        path
        for path in tracked
        if path.endswith(".pkl")
        or path.endswith(".log")
        or "plugin_log/" in path
        or "/cache/" in path.replace("\\", "/")
    ]
    assert offenders == [], f"以下运行产物仍被版本控制: {offenders}"
