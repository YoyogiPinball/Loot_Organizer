# -*- coding: utf-8 -*-
"""PNG_Prompt_Sort の重複処理と Pipeline 連携の回帰テスト。"""

from pathlib import Path

import pytest
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from src.core.config_loader import PresetMeta
from src.core.planning_context import PlanningContext
from src.core.preview_generator import PreviewGenerator
from src.handlers.pipeline_handler import (
    PipelineAskDuplicateHandlingError,
    PipelineModeHandler,
)
from src.handlers.png_prompt_sort_handler import PngPromptSortModeHandler
from src.loot_manager import LootManager
from tests.conftest import pipeline_config, sort_config, write_yaml


def _write_png(path: Path, color: str = "red") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = PngInfo()
    metadata.add_text("parameters", "portrait <lora:Example Lora:1.0>")
    Image.new("RGB", (2, 2), color=color).save(path, pnginfo=metadata)
    return path


def _write_mapping(path: Path) -> Path:
    return write_yaml(path, {"mappings": {"Example Lora": "portraits"}})


def _png_config(
    source: Path,
    output: Path,
    mapping: Path,
    duplicate: str | None,
) -> dict:
    config = {
        "meta": {
            "name": "test-png",
            "icon": "I",
            "mode": "PNG_Prompt_Sort",
            "description": "test",
        },
        "settings": {
            "source_directories": [str(source)],
            "output_directory": str(output),
            "mapping_file": str(mapping),
            "target_extensions": ["png"],
        },
    }
    if duplicate is not None:
        config["settings"]["duplicate_handling"] = duplicate
    return config


def _handler(tmp_path, nolog, duplicate: str):
    source = tmp_path / "source"
    output = tmp_path / "output"
    mapping = _write_mapping(tmp_path / "lora-map.yaml")
    return (
        PngPromptSortModeHandler(
            _png_config(source, output, mapping, duplicate),
            None,
            nolog,
        ),
        source,
        output / "portraits",
    )


class TestDuplicateHandling:
    def test_duplicate_source_directories_are_scanned_only_once(
        self,
        tmp_path,
        nolog,
    ):
        handler, source_dir, destination_dir = _handler(
            tmp_path,
            nolog,
            "skip",
        )
        source = _write_png(source_dir / "image.png", "blue")
        existing = _write_png(destination_dir / "image.png", "red")
        handler.settings["source_directories"] = [
            str(source_dir),
            str(source_dir / ".." / source_dir.name),
        ]

        operations = handler.plan_operations()

        assert len(operations) == 1
        assert operations[0].source == source
        assert operations[0].destination == existing

    def test_source_directory_deduplication_uses_planning_path_rules(
        self,
        tmp_path,
        nolog,
        monkeypatch,
    ):
        handler, _source_dir, _destination_dir = _handler(
            tmp_path,
            nolog,
            "skip",
        )
        handler.settings["source_directories"] = [
            r"D:\Images",
            "/mnt/d/images",
        ]
        scanned = []

        class TrackingScanner:
            def __init__(self, target_directory, _logger, planning_context=None):
                scanned.append(Path(target_directory))

            @staticmethod
            def scan_files(**_kwargs):
                return []

        monkeypatch.setattr(PlanningContext, "directory_exists", lambda *_args: True)
        monkeypatch.setattr(
            "src.handlers.png_prompt_sort_handler.FileScanner",
            TrackingScanner,
        )

        assert handler.plan_operations() == []
        assert scanned == [Path("/mnt/d/Images")]

    def test_default_skips_existing_destination(self, tmp_path, nolog):
        handler, source_dir, destination_dir = _handler(tmp_path, nolog, None)
        source = _write_png(source_dir / "image.png", "blue")
        existing = _write_png(destination_dir / "image.png", "red")

        operations = handler.plan_operations()
        preview = PreviewGenerator(preview_mode="all").generate_preview(
            operations,
            "PNG_Prompt_Sort",
        )
        dry_result = handler.execute_operations(operations, dry_run=True)
        execute_result = handler.execute_operations(operations)

        assert operations[0].planned_skip_reason is not None
        assert "[スキップ] image.png" in preview
        assert "保存先が埋まっていたため 1 件をスキップ予定" in preview
        assert dry_result.skipped_count == execute_result.skipped_count == 1
        assert execute_result == (0, 0)
        assert source.exists()
        with Image.open(existing) as image:
            assert image.getpixel((0, 0)) == (255, 0, 0)

    def test_explicit_skip_is_reported_as_configured_skip(self, tmp_path, nolog):
        handler, source_dir, destination_dir = _handler(tmp_path, nolog, "skip")
        source = _write_png(source_dir / "image.png", "blue")
        _write_png(destination_dir / "image.png", "red")

        operations = handler.plan_operations()
        preview = PreviewGenerator(preview_mode="all").generate_preview(
            operations,
            "PNG_Prompt_Sort",
        )
        result = handler.execute_operations(operations)

        assert operations[0].configured_skip_if_exists is True
        assert operations[0].skip_category == "explicit"
        assert "既に存在するため 1 件をスキップ予定" in preview
        assert "保存先が埋まっていたため" not in preview
        assert result.explicit_skipped_count == 1
        assert result.protected_skipped_count == 0
        assert source.is_file()

    def test_overwrite_plans_original_name_and_replaces_existing_file(
        self,
        tmp_path,
        nolog,
    ):
        handler, source_dir, destination_dir = _handler(
            tmp_path,
            nolog,
            "overwrite",
        )
        source = _write_png(source_dir / "image.png", "blue")
        existing = _write_png(destination_dir / "image.png", "red")

        operations = handler.plan_operations()

        assert operations[0].destination == existing
        assert handler.execute_operations(operations) == (1, 0)
        assert not source.exists()
        with Image.open(existing) as image:
            assert image.getpixel((0, 0)) == (0, 0, 255)

    def test_sequential_plans_numbered_name_when_destination_exists(
        self,
        tmp_path,
        nolog,
    ):
        handler, source_dir, destination_dir = _handler(
            tmp_path,
            nolog,
            "sequential",
        )
        _write_png(source_dir / "image.png")
        _write_png(destination_dir / "image.png")

        operations = handler.plan_operations()

        assert operations[0].destination == destination_dir / "image_1.png"

    def test_sequential_sees_destination_planned_earlier_in_same_run(
        self,
        tmp_path,
        nolog,
    ):
        first_source = tmp_path / "source-1"
        second_source = tmp_path / "source-2"
        output = tmp_path / "output"
        mapping = _write_mapping(tmp_path / "lora-map.yaml")
        _write_png(first_source / "image.png", "blue")
        _write_png(second_source / "image.png", "green")
        config = _png_config(first_source, output, mapping, "sequential")
        config["settings"]["source_directories"] = [
            str(first_source),
            str(second_source),
        ]
        handler = PngPromptSortModeHandler(config, None, nolog)

        operations = handler.plan_operations()

        assert [operation.destination.name for operation in operations] == [
            "image.png",
            "image_1.png",
        ]

    def test_ask_still_prompts_during_standalone_execution(
        self,
        tmp_path,
        nolog,
        monkeypatch,
    ):
        handler, source_dir, destination_dir = _handler(tmp_path, nolog, "ask")
        source = _write_png(source_dir / "image.png", "blue")
        existing = _write_png(destination_dir / "image.png", "red")

        class Answer:
            @staticmethod
            def ask():
                return "スキップ"

        monkeypatch.setattr(
            "src.handlers.png_prompt_sort_handler.questionary.select",
            lambda *args, **kwargs: Answer(),
        )

        operations = handler.plan_operations()
        result = handler.execute_operations(operations)

        assert result == (0, 0)
        assert source.exists()
        with Image.open(existing) as image:
            assert image.getpixel((0, 0)) == (255, 0, 0)


class TestPipelineDuplicateHandling:
    def test_skip_does_not_overwrite_existing_file(self, tmp_path, nolog):
        source = tmp_path / "source"
        output = tmp_path / "output"
        mapping = _write_mapping(tmp_path / "lora-map.yaml")
        original = _write_png(source / "image.png", "blue")
        existing = _write_png(output / "portraits" / "image.png", "red")
        png_path = write_yaml(
            tmp_path / "png-skip.yaml",
            _png_config(source, output, mapping, "skip"),
        )
        handler = PipelineModeHandler(
            pipeline_config([{"config": str(png_path), "label": "PNG skip"}]),
            None,
            nolog,
        )

        operations = handler.plan_operations()
        result = handler.execute_operations(operations)

        assert len(operations) == 1
        assert operations[0].planned_skip_reason is not None
        assert result == (0, 0)
        assert result.skipped_count == 1
        assert original.exists()
        with Image.open(existing) as image:
            assert image.getpixel((0, 0)) == (255, 0, 0)

    def test_sequential_destination_is_visible_to_later_step(
        self,
        tmp_path,
        nolog,
    ):
        source = tmp_path / "source"
        output = tmp_path / "output"
        lora_output = output / "portraits"
        final = tmp_path / "final"
        mapping = _write_mapping(tmp_path / "lora-map.yaml")
        _write_png(source / "image.png", "blue")
        _write_png(lora_output / "image.png", "red")
        png_path = write_yaml(
            tmp_path / "png-sequential.yaml",
            _png_config(source, output, mapping, "sequential"),
        )
        sort_path = write_yaml(
            tmp_path / "sort-numbered.yaml",
            sort_config(lora_output, [{
                "pattern": "*_1.png",
                "dest": str(final),
                "description": "numbered PNG",
            }]),
        )
        handler = PipelineModeHandler(
            pipeline_config([
                {"config": str(png_path), "label": "PNG sequential"},
                {"config": str(sort_path), "label": "Later sort"},
            ]),
            None,
            nolog,
        )

        operations = handler.plan_operations()

        assert [operation.destination for operation in operations] == [
            lora_output / "image_1.png",
            final / "image_1.png",
        ]
        assert operations[1].source == lora_output / "image_1.png"
        assert handler.execute_operations(operations) == (2, 0)
        assert (final / "image_1.png").exists()

    def test_ask_is_rejected_before_planning_with_step_and_config_in_message(
        self,
        tmp_path,
        nolog,
    ):
        source = tmp_path / "source"
        output = tmp_path / "output"
        mapping = _write_mapping(tmp_path / "lora-map.yaml")
        original = _write_png(source / "image.png")
        png_path = write_yaml(
            tmp_path / "png-ask.yaml",
            _png_config(source, output, mapping, "ask"),
        )
        handler = PipelineModeHandler(
            pipeline_config([{
                "config": str(png_path),
                "label": "確認が必要な PNG",
            }]),
            None,
            nolog,
        )

        with pytest.raises(PipelineAskDuplicateHandlingError) as exc_info:
            handler.plan_operations()

        message = str(exc_info.value)
        assert "確認が必要な PNG" in message
        assert str(png_path) in message
        assert "duplicate_handling: ask" in message
        assert original.exists()
        assert not output.exists()

    def test_ask_error_is_displayed_in_japanese_by_cli(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        source = tmp_path / "source"
        output = tmp_path / "output"
        mapping = _write_mapping(tmp_path / "lora-map.yaml")
        original = _write_png(source / "image.png")
        png_path = write_yaml(
            tmp_path / "png-ask.yaml",
            _png_config(source, output, mapping, "ask"),
        )
        pipeline_path = write_yaml(
            tmp_path / "pipeline.yaml",
            pipeline_config([{
                "config": str(png_path),
                "label": "個別確認 PNG",
            }]),
        )
        preset = PresetMeta(
            name="pipeline",
            icon="P",
            mode="Pipeline",
            description="test",
            file_path=str(pipeline_path),
        )
        monkeypatch.setattr("builtins.input", lambda _prompt: "")

        LootManager().execute_preset(preset)

        output_text = capsys.readouterr().out
        assert "[エラー]" in output_text
        assert "個別確認 PNG" in output_text
        assert str(png_path) in output_text
        assert "duplicate_handling: ask" in output_text
        assert original.exists()
        assert not output.exists()
