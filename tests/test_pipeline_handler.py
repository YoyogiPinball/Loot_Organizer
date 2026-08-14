# -*- coding: utf-8 -*-
"""
Pipeline モードの動作テスト

複数ステップの操作が正しく結合され、step_label / step_mode が付与されることを確認する。
"""

import pytest

from src.core.planning_context import PlanningConflictError
from src.core.preview_generator import FileOperation
from src.handlers.pipeline_handler import PipelineModeHandler
from src.handlers.registry import build_handler
from tests.conftest import make_files, sort_config, clean_config, pipeline_config, write_yaml


def _pipeline_handler(tmp_path, nolog, steps):
    cfg = pipeline_config(steps)
    from src.core.config_loader import ConfigLoader
    loader = ConfigLoader(mode_dir=str(tmp_path))
    return PipelineModeHandler(cfg, None, nolog, config_loader=loader)


# ---------------------------------------------------------------------------
# 操作の収集
# ---------------------------------------------------------------------------

class TestOperationCollection:
    def test_merges_ops_from_all_steps(self, tmp_path, nolog):
        src1 = tmp_path / "src1"
        src2 = tmp_path / "src2"
        make_files(src1, "a.jpg")
        make_files(src2, "b.png")
        dest = tmp_path / "dest"

        step1_path = write_yaml(tmp_path / "step1.yaml", sort_config(src1, [
            {"pattern": "*.jpg", "dest": str(dest), "description": "jpg"},
        ]))
        step2_path = write_yaml(tmp_path / "step2.yaml", sort_config(src2, [
            {"pattern": "*.png", "dest": str(dest), "description": "png"},
        ]))

        handler = _pipeline_handler(tmp_path, nolog, [
            {"config": str(step1_path), "label": "Step A"},
            {"config": str(step2_path), "label": "Step B"},
        ])
        ops = handler.plan_operations()

        assert len(ops) == 2
        filenames = {op.source.name for op in ops}
        assert filenames == {"a.jpg", "b.png"}

    def test_ops_in_step_order(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "file.txt")
        dest1 = tmp_path / "d1"
        dest2 = tmp_path / "d2"

        step1_path = write_yaml(tmp_path / "step1.yaml", sort_config(src, [
            {"pattern": "*.txt", "dest": str(dest1), "description": "step1"},
        ]))
        # step2 は src に何もないので 0 件になる（順序の確認のみ）
        src2 = tmp_path / "src2"
        src2.mkdir()
        step2_path = write_yaml(tmp_path / "step2.yaml", sort_config(src2, [
            {"pattern": "*.txt", "dest": str(dest2), "description": "step2"},
        ]))

        handler = _pipeline_handler(tmp_path, nolog, [
            {"config": str(step1_path), "label": "First"},
            {"config": str(step2_path), "label": "Second"},
        ])
        ops = handler.plan_operations()

        # step1 の操作が先に来る
        assert ops[0].step_label == "First"

    def test_empty_step_contributes_zero_ops(self, tmp_path, nolog):
        src = tmp_path / "src"
        src.mkdir()  # ファイルなし
        dest = tmp_path / "dest"

        step_path = write_yaml(tmp_path / "step.yaml", sort_config(src, [
            {"pattern": "*.jpg", "dest": str(dest), "description": "nothing"},
        ]))

        handler = _pipeline_handler(tmp_path, nolog, [
            {"config": str(step_path), "label": "Empty"},
        ])
        ops = handler.plan_operations()

        assert ops == []


# ---------------------------------------------------------------------------
# ステップ間の依存
# ---------------------------------------------------------------------------

class TestDependentSteps:
    def test_later_steps_see_files_created_by_earlier_steps(self, tmp_path, nolog):
        downloads = tmp_path / "downloads"
        make_files(downloads, "photo.Exif")
        staging = tmp_path / "staging"
        final = tmp_path / "final"

        rename_path = write_yaml(tmp_path / "rename.yaml", clean_config(
            downloads,
            sorting_rules=[{
                "search": "*.Exif",
                "destination": str(downloads),
                "action": "move",
                "rename_pattern": {".Exif": ".jpg"},
            }],
        ))
        stage_path = write_yaml(tmp_path / "stage.yaml", sort_config(downloads, [
            {"pattern": "*.jpg", "dest": str(staging), "description": "stage"},
        ]))
        final_path = write_yaml(tmp_path / "final.yaml", sort_config(staging, [
            {"pattern": "*.jpg", "dest": str(final), "description": "final"},
        ]))

        handler = _pipeline_handler(tmp_path, nolog, [
            {"config": str(rename_path), "label": "Rename"},
            {"config": str(stage_path), "label": "Stage"},
            {"config": str(final_path), "label": "Final"},
        ])

        ops = handler.plan_operations()

        assert [op.source for op in ops] == [
            downloads / "photo.Exif",
            downloads / "photo.jpg",
            staging / "photo.jpg",
        ]
        assert len(ops) == 3

        success, failure = handler.execute_operations(ops)
        assert (success, failure) == (3, 0)
        assert (final / "photo.jpg").exists()

    def test_filters_use_original_file_for_virtual_path(self, tmp_path, nolog):
        src = tmp_path / "src"
        file_path = make_files(src, "payload.bin")[0]
        file_path.write_bytes(b"1234")
        staging = tmp_path / "staging"
        final = tmp_path / "final"

        stage_path = write_yaml(tmp_path / "stage.yaml", sort_config(src, [
            {"pattern": "*.bin", "dest": str(staging), "description": "stage"},
        ]))
        filtered_path = write_yaml(tmp_path / "filtered.yaml", sort_config(staging, [
            {
                "pattern": "*.bin",
                "dest": str(final),
                "description": "non-empty",
                "filters": {"size": {"min": 1}},
            },
        ]))

        handler = _pipeline_handler(tmp_path, nolog, [
            {"config": str(stage_path)},
            {"config": str(filtered_path)},
        ])
        ops = handler.plan_operations()

        assert len(ops) == 2
        assert ops[1].source == staging / "payload.bin"

    def test_sort_processes_both_source_and_copy_created_by_clean(
        self,
        tmp_path,
        nolog,
    ):
        src = tmp_path / "src"
        original = make_files(src, "{tag}photo.png")[0]
        copied = tmp_path / "copied"
        final = tmp_path / "final"

        copy_path = write_yaml(tmp_path / "copy.yaml", clean_config(
            src,
            sorting_rules=[{
                "search": "*.png",
                "destination": str(copied),
                "action": "copy",
                "rename_pattern": {"{tag}": ""},
            }],
        ))
        sort_cfg = sort_config(src, [{
            "pattern": "*.png",
            "dest": str(final),
            "description": "sort originals and copies",
        }])
        sort_cfg["settings"]["target_directory"] = [str(src), str(copied)]
        sort_path = write_yaml(tmp_path / "sort.yaml", sort_cfg)

        handler = _pipeline_handler(tmp_path, nolog, [
            {"config": str(copy_path), "label": "Copy"},
            {"config": str(sort_path), "label": "Sort"},
        ])

        operations = handler.plan_operations()

        assert len(operations) == 3
        assert operations[0].action == "copy"
        assert operations[0].source == original
        assert operations[0].destination == copied / "photo.png"
        assert {operation.source for operation in operations[1:]} == {
            original,
            copied / "photo.png",
        }
        assert {operation.destination for operation in operations[1:]} == {
            final / "{tag}photo.png",
            final / "photo.png",
        }

    def test_skip_if_exists_sees_planned_destination(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "file.txt")
        dest = tmp_path / "dest"

        first_path = write_yaml(tmp_path / "first.yaml", clean_config(src, sorting_rules=[
            {"search": "*.txt", "destination": str(dest), "action": "copy"},
        ]))
        second_path = write_yaml(tmp_path / "second.yaml", clean_config(src, sorting_rules=[
            {
                "search": "*.txt",
                "destination": str(dest),
                "action": "copy",
                "skip_if_exists": True,
            },
        ]))

        handler = _pipeline_handler(tmp_path, nolog, [
            {"config": str(first_path), "label": "First"},
            {"config": str(second_path), "label": "Second"},
        ])
        ops = handler.plan_operations()

        assert len(ops) == 1
        assert ops[0].step_label == "First"

    def test_skip_if_exists_sees_earlier_file_in_same_step(self, tmp_path, nolog):
        src1 = tmp_path / "src1"
        src2 = tmp_path / "src2"
        make_files(src1, "same.txt")
        make_files(src2, "same.txt")
        dest = tmp_path / "dest"

        config = sort_config(src1, [{
            "pattern": "*.txt",
            "dest": str(dest),
            "description": "deduplicate",
            "skip_if_exists": True,
        }])
        config["settings"]["target_directory"] = [str(src1), str(src2)]
        step_path = write_yaml(tmp_path / "same-step.yaml", config)

        handler = _pipeline_handler(tmp_path, nolog, [
            {"config": str(step_path), "label": "One step"},
        ])
        ops = handler.plan_operations()

        assert len(ops) == 1

    def test_dry_run_keeps_real_files_unchanged(self, tmp_path, nolog):
        src = tmp_path / "src"
        original = make_files(src, "file.txt")[0]
        dest = tmp_path / "dest"
        step_path = write_yaml(tmp_path / "move.yaml", sort_config(src, [
            {"pattern": "*.txt", "dest": str(dest), "description": "move"},
        ]))

        handler = _pipeline_handler(tmp_path, nolog, [
            {"config": str(step_path)},
        ])
        ops = handler.plan_operations()
        success, failure = handler.execute_operations(ops, dry_run=True)

        assert (success, failure) == (1, 0)
        assert original.exists()
        assert not dest.exists()

    def test_conflicting_destinations_across_steps_abort_before_execution(
        self,
        tmp_path,
        nolog,
    ):
        src1 = tmp_path / "src1"
        src2 = tmp_path / "src2"
        first = make_files(src1, "same.txt")[0]
        second = make_files(src2, "same.txt")[0]
        dest = tmp_path / "dest"

        first_path = write_yaml(tmp_path / "first.yaml", sort_config(src1, [
            {"pattern": "*.txt", "dest": str(dest), "description": "first"},
        ]))
        second_path = write_yaml(tmp_path / "second.yaml", sort_config(src2, [
            {"pattern": "*.txt", "dest": str(dest), "description": "second"},
        ]))
        handler = _pipeline_handler(tmp_path, nolog, [
            {"config": str(first_path), "label": "First"},
            {"config": str(second_path), "label": "Second"},
        ])

        with pytest.raises(PlanningConflictError) as exc_info:
            handler.plan_operations()

        conflict = exc_info.value
        assert conflict.first_source == first
        assert conflict.second_source == second
        assert conflict.destination == dest / "same.txt"
        assert first.exists()
        assert second.exists()
        assert not dest.exists()


class TestPipelineExecution:
    def test_stops_after_first_failure(self, tmp_path, nolog, monkeypatch):
        handler = _pipeline_handler(tmp_path, nolog, [
            {"config": "unused.yaml"},
        ])
        calls = []

        def fail_first(op):
            calls.append(op)
            raise OSError("boom")

        monkeypatch.setattr(
            "src.handlers.pipeline_handler.execute_file_op",
            fail_first,
            raising=False,
        )
        ops = [
            FileOperation(tmp_path / "one", tmp_path / "out" / "one", "move", "one"),
            FileOperation(tmp_path / "two", tmp_path / "out" / "two", "move", "two"),
        ]

        success, failure = handler.execute_operations(ops)

        assert (success, failure) == (0, 1)
        assert calls == [ops[0]]


# ---------------------------------------------------------------------------
# step_label / step_mode の付与
# ---------------------------------------------------------------------------

class TestMetadataOnOps:
    def test_step_label_added_to_reason(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "file.jpg")
        dest = tmp_path / "dest"

        step_path = write_yaml(tmp_path / "step.yaml", sort_config(src, [
            {"pattern": "*.jpg", "dest": str(dest), "description": "jpg"},
        ]))

        handler = _pipeline_handler(tmp_path, nolog, [
            {"config": str(step_path), "label": "My Label"},
        ])
        ops = handler.plan_operations()

        assert "My Label" in ops[0].reason

    def test_step_mode_reflects_sub_config_mode(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "tagged.png")
        dest = tmp_path / "dest"

        step_path = write_yaml(tmp_path / "step.yaml", clean_config(src, sorting_rules=[
            {"search": "*.png", "destination": str(dest), "action": "move"},
        ]))

        handler = _pipeline_handler(tmp_path, nolog, [
            {"config": str(step_path), "label": "Clean step"},
        ])
        ops = handler.plan_operations()

        assert ops[0].step_mode == "Clean"

    def test_default_label_uses_config_path(self, tmp_path, nolog):
        """label 未指定時は config パスがラベル代わりになる"""
        src = tmp_path / "src"
        make_files(src, "file.jpg")
        dest = tmp_path / "dest"

        step_path = write_yaml(tmp_path / "mystep.yaml", sort_config(src, [
            {"pattern": "*.jpg", "dest": str(dest), "description": "jpg"},
        ]))

        handler = _pipeline_handler(tmp_path, nolog, [
            {"config": str(step_path)},  # label なし
        ])
        ops = handler.plan_operations()

        assert "mystep.yaml" in ops[0].reason


# ---------------------------------------------------------------------------
# validate_config
# ---------------------------------------------------------------------------

class TestValidation:
    def test_rejects_missing_steps(self, tmp_path, nolog):
        cfg = pipeline_config([])
        with pytest.raises(ValueError, match="steps"):
            PipelineModeHandler.validate_config(cfg)

    def test_rejects_step_without_config_key(self, tmp_path, nolog):
        cfg = pipeline_config([{"label": "no config key"}])
        with pytest.raises(ValueError):
            PipelineModeHandler.validate_config(cfg)
