# -*- coding: utf-8 -*-
"""
共通フィクスチャとヘルパー
"""

import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from src.core.logger import LootLogger

# 本番は Windows、開発は WSL。Linux のパス規則（先頭 / の絶対パス・大文字小文字の
# 区別）を前提にしたテストは Windows ネイティブでは成立しないので、そこだけ外す。
# 製品コードの Windows 側の振る舞いは、対になる Windows 用テストで確認する。
posix_only = pytest.mark.skipif(
    os.name == "nt",
    reason="Linux のパス規則を前提にしたテスト（Windows ネイティブでは別テストで確認）",
)


@pytest.fixture
def nolog(tmp_path):
    """ファイル書き込みなしの LootLogger"""
    return LootLogger(log_directory=str(tmp_path / "logs"), enable_logging=False)


# ---------------------------------------------------------------------------
# config dict ヘルパー
# ---------------------------------------------------------------------------

def _base_settings(target_dir) -> dict:
    return {
        "target_directory": str(target_dir),
        "enable_logging": False,
        "confirm_before_execute": False,
        "dry_run_default": True,
        "preview": {"mode": "head", "count": 5},
        "logging": {"log_success": False, "log_directory": "logs"},
    }


def sort_config(target_dir, move_rules: list, **extra) -> dict[str, Any]:
    return {
        "meta": {"name": "test-sort", "icon": "S", "mode": "Sort", "description": "test"},
        "settings": _base_settings(target_dir),
        "move_rules": move_rules,
        **extra,
    }


def clean_config(target_dir, *, deletion=None, cleanup=None, sorting_rules=None, **extra) -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "meta": {"name": "test-clean", "icon": "C", "mode": "Clean", "description": "test"},
        "settings": _base_settings(target_dir),
        **extra,
    }
    if deletion is not None:
        cfg["deletion"] = deletion
    if cleanup is not None:
        cfg["cleanup"] = cleanup
    if sorting_rules is not None:
        cfg["sorting_rules"] = sorting_rules
    # 少なくとも1つのキーが必要
    if not any(k in cfg for k in ("deletion", "cleanup", "sorting_rules")):
        cfg["sorting_rules"] = []
    return cfg


def pipeline_config(steps: list, **extra) -> dict[str, Any]:
    return {
        "meta": {"name": "test-pipeline", "icon": "P", "mode": "Pipeline", "description": "test"},
        "settings": {
            "enable_logging": False,
            "confirm_before_execute": False,
            "dry_run_default": True,
            "preview": {"mode": "head", "count": 5},
            "logging": {"log_success": False, "log_directory": "logs"},
        },
        "steps": steps,
        **extra,
    }


def write_yaml(path: Path, data: dict) -> Path:
    """dict を YAML ファイルとして書き出す"""
    path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# ファイル作成ヘルパー
# ---------------------------------------------------------------------------

def make_files(directory: Path, *names: str) -> list[Path]:
    """空ファイルを作成してパスのリストを返す"""
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in names:
        p = directory / name
        p.touch()
        paths.append(p)
    return paths
