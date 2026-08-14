# -*- coding: utf-8 -*-
"""LootManager の対話フローに関する回帰テスト。"""

from src.core.config_loader import PresetMeta
from src.loot_manager import LootManager
from tests.conftest import clean_config, make_files, write_yaml


def test_planning_conflict_is_displayed_and_returns_without_file_changes(
    tmp_path,
    monkeypatch,
    capsys,
):
    src = tmp_path / "src"
    first, second = make_files(src, "photo😀.png", "photo😃.png")
    config_path = write_yaml(
        tmp_path / "conflict.yaml",
        clean_config(
            src,
            cleanup={"enabled": True, "recursive": False, "custom_patterns": []},
        ),
    )
    preset = PresetMeta(
        name="conflict",
        icon="C",
        mode="Clean",
        description="test",
        file_path=str(config_path),
    )
    monkeypatch.setattr("builtins.input", lambda _prompt: "")

    LootManager().execute_preset(preset)

    output = capsys.readouterr().out
    assert "[エラー] 移動先が衝突しています" in output
    assert str(first) in output
    assert str(second) in output
    assert str(src / "photo.png") in output
    assert "YAML のルールを見直してください。" in output
    assert first.exists()
    assert second.exists()
    assert not (src / "photo.png").exists()
