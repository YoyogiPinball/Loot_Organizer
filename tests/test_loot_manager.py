# -*- coding: utf-8 -*-
"""LootManager の対話フローに関する回帰テスト。"""

import pytest

from src.core.config_loader import PresetMeta
from src.loot_manager import LootManager
from tests.conftest import (
    clean_config,
    make_files,
    pipeline_config,
    sort_config,
    write_yaml,
)


def test_skip_summaries_are_separated_after_execution(
    tmp_path,
    monkeypatch,
    capsys,
):
    src = tmp_path / "src"
    explicit, protected = make_files(src, "explicit.txt", "protected.txt")
    dest = tmp_path / "dest"
    make_files(dest, explicit.name, protected.name)
    config = clean_config(
        src,
        sorting_rules=[
            {
                "search": explicit.name,
                "destination": str(dest),
                "action": "copy",
                "skip_if_exists": True,
            },
            {
                "search": protected.name,
                "destination": str(dest),
                "action": "copy",
            },
        ],
    )
    config["settings"]["dry_run_default"] = False
    config_path = write_yaml(tmp_path / "conflict.yaml", config)
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
    result_summary = output.split("完了:", 1)[1]
    assert "0件成功" in result_summary
    assert "既に存在するため 1 件をスキップしました" in result_summary
    assert "保存先が埋まっていたため 1 件をスキップしました" in result_summary
    assert explicit.name not in result_summary
    assert protected.name in result_summary
    assert explicit.exists()
    assert protected.exists()
    assert "内訳: 計画 2件 = 成功 0 / 失敗 0 / スキップ 2 / 未実行 0" in result_summary


def test_aborted_pipeline_shows_how_far_it_got(tmp_path, monkeypatch, capsys):
    """Pipeline が途中で落ちたとき、止まった位置と未実行件数が画面に出る。"""
    src = tmp_path / "src"
    first, second, third = make_files(src, "1_ok.txt", "2_boom.txt", "3_after.txt")
    dest = tmp_path / "dest"

    step_one = write_yaml(
        tmp_path / "step1.yaml",
        sort_config(src, [{"pattern": first.name, "dest": str(dest), "description": "ok"}]),
    )
    step_two = write_yaml(
        tmp_path / "step2.yaml",
        sort_config(src, [{"pattern": second.name, "dest": str(dest), "description": "boom"}]),
    )
    step_three = write_yaml(
        tmp_path / "step3.yaml",
        sort_config(src, [{"pattern": third.name, "dest": str(dest), "description": "after"}]),
    )
    config = pipeline_config([
        {"config": str(step_one), "label": "1. 通る段"},
        {"config": str(step_two), "label": "2. 落ちる段"},
        {"config": str(step_three), "label": "3. 後段"},
    ])
    config["settings"]["dry_run_default"] = False
    config_path = write_yaml(tmp_path / "pipeline.yaml", config)
    preset = PresetMeta(
        name="pipeline",
        icon="P",
        mode="Pipeline",
        description="test",
        file_path=str(config_path),
    )

    def fail_on_second(op):
        if op.source.name == second.name:
            raise OSError("boom")
        return op.destination

    monkeypatch.setattr(
        "src.handlers.pipeline_handler.execute_file_op",
        fail_on_second,
        raising=False,
    )
    monkeypatch.setattr("builtins.input", lambda _prompt: "")

    LootManager().execute_preset(preset)

    output = capsys.readouterr().out
    result_summary = output.split("完了:", 1)[1]
    assert "中断: ステップ「2. 落ちる段」でエラーが起きたため" in result_summary
    assert "残り 1 件は実行していません" in result_summary
    assert "- 3. 後段: 1件 未実行" in result_summary
    assert "内訳: 計画 3件 = 成功 1 / 失敗 1 / スキップ 0 / 未実行 1" in result_summary
    # 未実行のファイルは元の場所に残っている。
    assert third.exists()


def test_plan_error_is_displayed_logged_and_returns_to_menu(
    tmp_path,
    monkeypatch,
    capsys,
):
    config_path = write_yaml(tmp_path / "pipeline.yaml", pipeline_config([]))
    preset = PresetMeta(
        name="壊れたプリセット",
        icon="P",
        mode="Pipeline",
        description="test",
        file_path=str(config_path),
    )
    logged = []
    prompts = []

    class SpyLogger:
        def error(self, message):
            logged.append(message)

    class ExplodingHandler:
        @staticmethod
        def plan_operations():
            raise ValueError("steps[2].config が見つかりません")

    monkeypatch.setattr("src.loot_manager.LootLogger", lambda **_kwargs: SpyLogger())
    monkeypatch.setattr(
        "src.loot_manager.build_handler",
        lambda **_kwargs: ExplodingHandler(),
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda prompt: prompts.append(prompt) or "",
    )

    LootManager().execute_preset(preset)

    output = capsys.readouterr().out
    assert "壊れたプリセット" in output
    assert "ValueError" in output
    assert "steps[2].config が見つかりません" in output
    assert "Traceback (most recent call last)" not in output
    assert len(prompts) == 1
    assert "Enterキーで続行..." in prompts[0]
    assert len(logged) == 1
    assert "Traceback (most recent call last)" in logged[0]
    assert "ValueError: steps[2].config が見つかりません" in logged[0]


@pytest.mark.parametrize("base_exception", [KeyboardInterrupt, SystemExit])
def test_plan_base_exceptions_are_not_caught(
    tmp_path,
    monkeypatch,
    base_exception,
):
    config_path = write_yaml(tmp_path / "pipeline.yaml", pipeline_config([]))
    preset = PresetMeta(
        name="interrupt",
        icon="P",
        mode="Pipeline",
        description="test",
        file_path=str(config_path),
    )

    class ExplodingHandler:
        @staticmethod
        def plan_operations():
            raise base_exception()

    monkeypatch.setattr(
        "src.loot_manager.build_handler",
        lambda **_kwargs: ExplodingHandler(),
    )

    with pytest.raises(base_exception):
        LootManager().execute_preset(preset)
