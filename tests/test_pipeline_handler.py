# -*- coding: utf-8 -*-
"""
Pipeline モードの動作テスト

複数ステップの操作が正しく結合され、step_label / step_mode が付与されることを確認する。
"""

import pytest

from src.core.preview_generator import FileOperation, PreviewGenerator
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
        src1 = tmp_path / "src1"
        src2 = tmp_path / "src2"
        make_files(src1, "a.txt", "b.txt")
        make_files(src2, "c.txt", "d.txt")
        dest1 = tmp_path / "d1"
        dest2 = tmp_path / "d2"

        step1_path = write_yaml(tmp_path / "step1.yaml", sort_config(src1, [
            {"pattern": "*.txt", "dest": str(dest1), "description": "step1"},
        ]))
        step2_path = write_yaml(tmp_path / "step2.yaml", sort_config(src2, [
            {"pattern": "*.txt", "dest": str(dest2), "description": "step2"},
        ]))

        handler = _pipeline_handler(tmp_path, nolog, [
            {"config": str(step1_path), "label": "First"},
            {"config": str(step2_path), "label": "Second"},
        ])
        ops = handler.plan_operations()

        assert [op.step_label for op in ops] == [
            "First",
            "First",
            "Second",
            "Second",
        ]

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
        assert ops[0].source_fingerprint is not None
        assert ops[1].source_fingerprint is None
        assert ops[2].source_fingerprint is None
        assert len(ops) == 3

        success, failure = handler.execute_operations(ops)
        assert (success, failure) == (3, 0)
        assert (final / "photo.jpg").exists()

    def test_filters_use_original_file_for_virtual_path(self, tmp_path, nolog):
        src = tmp_path / "src"
        file_path = make_files(src, "payload.bin")[0]
        file_path.write_bytes(b"1234")
        make_files(src, "empty.bin")
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
            {"config": str(stage_path), "label": "Stage"},
            {"config": str(filtered_path), "label": "Filtered"},
        ])
        ops = handler.plan_operations()

        # 後段は仮想パス（staging/ 配下。まだディスクには無い）を走査し、
        # サイズフィルタは元ファイル（src/ 配下の実体）を見る。
        # source が staging/ でなければ、そもそも仮想走査が働いていない。
        assert [op.source for op in ops if op.step_label == "Filtered"] == [
            staging / "payload.bin"
        ]

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

        assert len(ops) == 2
        assert ops[0].step_label == "First"
        assert ops[1].step_label == "Second"
        assert ops[1].planned_skip_reason is not None

    def test_skipped_sorting_in_prior_step_also_skips_later_cleanup(
        self,
        tmp_path,
        nolog,
    ):
        """別プリセットでも同じ論理 source の cleanup だけを実行しない。"""
        src = tmp_path / "src"
        original = make_files(src, "photo_DRAFT.png")[0]
        cleaned = src / "photo.png"
        blocked = tmp_path / "blocked"
        make_files(blocked, original.name)
        sorting_path = write_yaml(
            tmp_path / "sorting.yaml",
            clean_config(src, sorting_rules=[{
                "search": "*.png",
                "destination": str(blocked),
                "action": "copy",
            }]),
        )
        cleanup_path = write_yaml(
            tmp_path / "cleanup.yaml",
            clean_config(src, cleanup={
                "enabled": True,
                "recursive": False,
                "custom_patterns": [r"_DRAFT"],
            }),
        )
        handler = _pipeline_handler(tmp_path, nolog, [
            {"config": str(sorting_path), "label": "Sorting"},
            {"config": str(cleanup_path), "label": "Cleanup"},
        ])

        operations = handler.plan_operations()
        preview = PreviewGenerator(handler.config).generate_preview(
            operations,
            mode="Pipeline",
        )
        result = handler.execute_operations(operations)

        assert [operation.action for operation in operations] == [
            "copy",
            "cleanup",
        ]
        assert preview.count("[スキップ]") == 2
        assert all(
            operation.planned_skip_reason is not None
            for operation in operations
        )
        assert result == (0, 0)
        assert result.skipped_count == 2
        assert original.exists()
        assert not cleaned.exists()

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

        assert len(ops) == 2
        assert ops[0].planned_skip_reason is None
        assert ops[1].planned_skip_reason is not None

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

    def test_conflicting_destinations_skip_second_and_pipeline_completes(
        self,
        tmp_path,
        nolog,
    ):
        src1 = tmp_path / "src1"
        src2 = tmp_path / "src2"
        first = make_files(src1, "same.txt")[0]
        second, later = make_files(src2, "same.txt", "later.txt")
        dest = tmp_path / "dest"

        first_path = write_yaml(tmp_path / "first.yaml", sort_config(src1, [
            {"pattern": "*.txt", "dest": str(dest), "description": "first"},
        ]))
        second_path = write_yaml(tmp_path / "second.yaml", sort_config(src2, [
            {"pattern": "same.txt", "dest": str(dest), "description": "second"},
            {"pattern": "later.txt", "dest": str(dest), "description": "later"},
        ]))
        handler = _pipeline_handler(tmp_path, nolog, [
            {"config": str(first_path), "label": "First"},
            {"config": str(second_path), "label": "Second"},
        ])

        operations = handler.plan_operations()
        dry_result = handler.execute_operations(operations, dry_run=True)
        execute_result = handler.execute_operations(operations)

        assert len(operations) == 3
        assert operations[0].source == first
        assert operations[1].source == second
        assert operations[1].planned_skip_reason is not None
        assert operations[2].source == later
        assert dry_result.skipped_count == 1
        assert execute_result.skipped_count == 1
        assert execute_result == (2, 0)
        assert execute_result.skipped_operations[0].source == second
        assert execute_result.skipped_operations[0].destination == dest / "same.txt"
        assert (dest / "same.txt").exists()
        assert (dest / "later.txt").exists()
        assert second.exists()
        assert not later.exists()


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

    def test_abort_reports_which_step_stopped_and_what_was_not_run(
        self, tmp_path, nolog, monkeypatch
    ):
        """中断時に「どこで止まり、何件が未実行か」を結果から取り出せる。"""
        handler = _pipeline_handler(tmp_path, nolog, [
            {"config": "unused.yaml"},
        ])

        def fail_on_second(op):
            if op.source.name == "two":
                raise OSError("boom")
            return op.destination

        monkeypatch.setattr(
            "src.handlers.pipeline_handler.execute_file_op",
            fail_on_second,
            raising=False,
        )

        def _op(name, label):
            operation = FileOperation(
                tmp_path / name, tmp_path / "out" / name, "move", name
            )
            operation.step_label = label
            return operation

        ops = [
            _op("one", "1. 前段"),
            _op("two", "2. 落ちる段"),
            _op("three", "3. 後段"),
            _op("four", "3. 後段"),
        ]

        result = handler.execute_operations(ops)

        assert (result.success_count, result.failure_count) == (1, 1)
        assert result.aborted is True
        assert result.aborted_step == "2. 落ちる段"
        assert result.not_attempted_count == 2
        assert result.not_attempted_by_step() == [("3. 後段", 2)]
        # 成功・失敗・スキップ・未実行の合計が計画件数に一致する。
        assert (
            result.success_count
            + result.failure_count
            + result.skipped_count
            + result.not_attempted_count
        ) == len(ops)

    def test_completed_run_reports_nothing_left_unattempted(
        self, tmp_path, nolog, monkeypatch
    ):
        handler = _pipeline_handler(tmp_path, nolog, [
            {"config": "unused.yaml"},
        ])
        monkeypatch.setattr(
            "src.handlers.pipeline_handler.execute_file_op",
            lambda op: op.destination,
            raising=False,
        )
        ops = [
            FileOperation(tmp_path / "one", tmp_path / "out" / "one", "move", "one"),
        ]

        result = handler.execute_operations(ops)

        assert result.aborted is False
        assert result.not_attempted == ()
        assert result.aborted_step is None


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
    def test_rejects_missing_steps_key(self, tmp_path, nolog):
        cfg = pipeline_config([])
        del cfg["steps"]
        with pytest.raises(ValueError, match="steps"):
            PipelineModeHandler.validate_config(cfg)

    def test_rejects_empty_steps(self, tmp_path, nolog):
        cfg = pipeline_config([])
        with pytest.raises(ValueError, match="steps"):
            PipelineModeHandler.validate_config(cfg)

    def test_rejects_non_list_steps(self, tmp_path, nolog):
        cfg = pipeline_config([])
        cfg["steps"] = ({"config": "step.yaml"},)
        with pytest.raises(ValueError, match="steps"):
            PipelineModeHandler.validate_config(cfg)

    def test_rejects_step_without_config_key(self, tmp_path, nolog):
        cfg = pipeline_config([{"label": "no config key"}])
        with pytest.raises(ValueError):
            PipelineModeHandler.validate_config(cfg)


class TestAbortReportingEdgeCase:
    def test_failure_on_the_last_operation_still_reports_the_step(
        self, tmp_path, nolog, monkeypatch
    ):
        """最後の操作で落ちたら未実行は 0 件だが、中断であることは残す。"""
        handler = _pipeline_handler(tmp_path, nolog, [
            {"config": "unused.yaml"},
        ])
        monkeypatch.setattr(
            "src.handlers.pipeline_handler.execute_file_op",
            lambda op: (_ for _ in ()).throw(OSError("boom")),
            raising=False,
        )
        operation = FileOperation(
            tmp_path / "one", tmp_path / "out" / "one", "move", "one"
        )
        operation.step_label = "最終段"

        result = handler.execute_operations([operation])

        assert result.not_attempted_count == 0
        assert result.aborted_step == "最終段"
        assert result.aborted is True
