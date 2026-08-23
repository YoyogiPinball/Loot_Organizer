# -*- coding: utf-8 -*-
"""
Clean モードの動作テスト

deletion → cleanup → sorting_rules の3ステップが正しく動くことと、
after_sorting や skip_if_exists + rename_pattern の組み合わせを確認する。
"""

from src.core.file_scanner import FileScanner
from src.core.planning_context import PlanningContext
from src.core.preview_generator import FileOperation, PreviewGenerator
from src.handlers.clean_handler import CleanModeHandler
from src.utils.file_executor import execute_file_op
from tests.conftest import make_files, clean_config


def _handler(src_dir, nolog, **kwargs):
    cfg = clean_config(src_dir, **kwargs)
    scanner = FileScanner(str(src_dir), nolog)
    return CleanModeHandler(cfg, scanner, nolog)


# ---------------------------------------------------------------------------
# deletion ステップ
# ---------------------------------------------------------------------------

class TestDeletion:
    def test_removes_files_with_matching_string(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "{zpi$r=1}bad.png", "good.png")

        handler = _handler(src, nolog, deletion={"enabled": True, "strings": ["{zpi$r=1}"], "recursive": False})
        ops = handler.plan_operations()
        delete_ops = [op for op in ops if op.action == "delete"]

        assert len(delete_ops) == 1
        assert delete_ops[0].source.name == "{zpi$r=1}bad.png"

    def test_disabled_deletion_skipped(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "{zpi$r=1}bad.png")

        handler = _handler(src, nolog, deletion={"enabled": False, "strings": ["{zpi$r=1}"], "recursive": False})
        ops = handler.plan_operations()

        assert all(op.action != "delete" for op in ops)

    def test_overlapping_delete_strings_plan_file_once(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "delete_me.png")

        handler = _handler(
            src,
            nolog,
            deletion={
                "enabled": True,
                "strings": ["delete", "me"],
                "recursive": False,
            },
        )
        ops = handler.plan_operations()

        assert len([op for op in ops if op.action == "delete"]) == 1

    def test_execute_actually_deletes(self, tmp_path, nolog):
        src = tmp_path / "src"
        files = make_files(src, "{zpi$r=1}bad.png", "keep.png")

        handler = _handler(src, nolog, deletion={
            "enabled": True,
            "strings": ["{zpi$r=1}"],
            "recursive": False,
            "delete_mode": "permanent",
        })
        ops = handler.plan_operations()
        for op in ops:
            execute_file_op(op)

        assert not files[0].exists()
        assert files[1].exists()

    def test_delete_mode_defaults_to_trash_in_planned_operation(
        self,
        tmp_path,
        nolog,
    ):
        src = tmp_path / "src"
        make_files(src, "delete_me.png")
        handler = _handler(
            src,
            nolog,
            deletion={
                "enabled": True,
                "strings": ["delete_me"],
                "recursive": False,
            },
        )

        operations = handler.plan_operations()

        assert operations[0].delete_mode == "trash"


# ---------------------------------------------------------------------------
# cleanup ステップ
# ---------------------------------------------------------------------------

class TestCleanup:
    def test_removes_emojis_from_filename(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "photo🎨image.png")

        handler = _handler(src, nolog, cleanup={"enabled": True, "recursive": False, "custom_patterns": []})
        ops = handler.plan_operations()
        cleanup_ops = [op for op in ops if op.action == "cleanup"]

        assert len(cleanup_ops) == 1
        assert "🎨" not in cleanup_ops[0].destination.name

    def test_unchanged_file_not_included(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "normal_file.png")

        handler = _handler(src, nolog, cleanup={"enabled": True, "recursive": False, "custom_patterns": []})
        ops = handler.plan_operations()
        cleanup_ops = [op for op in ops if op.action == "cleanup"]

        assert cleanup_ops == []

    def test_custom_pattern_removed(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "file_DRAFT.png")

        handler = _handler(src, nolog, cleanup={
            "enabled": True, "recursive": False,
            "custom_patterns": [r"_DRAFT"],
        })
        ops = handler.plan_operations()
        cleanup_ops = [op for op in ops if op.action == "cleanup"]

        assert len(cleanup_ops) == 1
        assert "DRAFT" not in cleanup_ops[0].destination.name

    def test_duplicate_cleanup_destination_skips_second(self, tmp_path, nolog):
        src = tmp_path / "src"
        first, second = make_files(src, "photo😀.png", "photo😃.png")
        handler = _handler(
            src,
            nolog,
            cleanup={"enabled": True, "recursive": False, "custom_patterns": []},
        )

        operations = handler.plan_operations()

        assert [operation.source for operation in operations] == [first, second]
        assert operations[0].planned_skip_reason is None
        assert operations[1].planned_skip_reason is not None
        result = handler.execute_operations(operations)
        assert result == (1, 0)
        assert result.skipped_count == 1
        assert result.skipped_operations[0].source == second

    def test_duplicate_cleanup_preserves_skipped_source(self, tmp_path, nolog):
        src = tmp_path / "src"
        first, second = make_files(src, "photo😀.png", "photo😃.png")
        handler = _handler(
            src,
            nolog,
            cleanup={"enabled": True, "recursive": False, "custom_patterns": []},
        )

        operations = handler.plan_operations()
        handler.execute_operations(operations)

        assert not first.exists()
        assert second.exists()
        assert (src / "photo.png").exists()


# ---------------------------------------------------------------------------
# sorting_rules ステップ
# ---------------------------------------------------------------------------

class TestSortingRules:
    def test_move_matching_file(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "target.png")
        dest = tmp_path / "dest"

        handler = _handler(src, nolog, sorting_rules=[{
            "search": "*.png", "destination": str(dest), "action": "move",
        }])
        ops = handler.plan_operations()
        move_ops = [op for op in ops if op.action == "move"]

        assert len(move_ops) == 1
        assert move_ops[0].source.name == "target.png"

    def test_copy_keeps_source(self, tmp_path, nolog):
        src = tmp_path / "src"
        f = make_files(src, "target.png")[0]
        dest = tmp_path / "dest"

        handler = _handler(src, nolog, sorting_rules=[{
            "search": "*.png", "destination": str(dest), "action": "copy",
        }])
        ops = handler.plan_operations()
        for op in ops:
            execute_file_op(op)

        assert f.exists()
        assert (dest / "target.png").exists()

    def test_rename_pattern_applied(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "{zpi$r=3}image.png")
        dest = tmp_path / "dest"

        handler = _handler(src, nolog, sorting_rules=[{
            "search": "*{zpi$r=3}*",
            "destination": str(dest),
            "action": "move",
            "rename_pattern": {"{zpi$r=3}": ""},
        }])
        ops = handler.plan_operations()

        assert len(ops) == 1
        assert ops[0].destination.name == "image.png"

    def test_skip_if_exists_with_rename_pattern(self, tmp_path, nolog):
        """Bug-1 回帰: rename 後のファイルが既存なら skip する"""
        src = tmp_path / "src"
        make_files(src, "{tag}file.png")
        dest = tmp_path / "dest"
        dest.mkdir()
        (dest / "file.png").touch()

        handler = _handler(src, nolog, sorting_rules=[{
            "search": "*{tag}*",
            "destination": str(dest),
            "action": "copy",
            "rename_pattern": {"{tag}": ""},
            "skip_if_exists": True,
        }])
        ops = handler.plan_operations()

        assert len(ops) == 1
        assert ops[0].planned_skip_reason is not None

    def test_skip_if_exists_moves_when_absent(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "{tag}file.png")
        dest = tmp_path / "dest"
        dest.mkdir()

        handler = _handler(src, nolog, sorting_rules=[{
            "search": "*{tag}*",
            "destination": str(dest),
            "action": "copy",
            "rename_pattern": {"{tag}": ""},
            "skip_if_exists": True,
        }])
        ops = handler.plan_operations()

        assert len(ops) == 1
        assert ops[0].skip_if_exists is True

    def test_skipped_copy_also_skips_cleanup_for_same_source(
        self,
        tmp_path,
        nolog,
    ):
        """copy が成立しない限り、対象外化するタグを元ファイルから消さない。"""
        src = tmp_path / "src"
        tagged = make_files(src, "image{zpi$r=3}.png")[0]
        copy_dest = tmp_path / "ai_r5"
        copied = make_files(copy_dest, "image.png")[0]
        cleaned = src / "image.png"
        handler = _handler(
            src,
            nolog,
            sorting_rules=[{
                "search": "*{zpi$r=3}*",
                "destination": str(copy_dest),
                "action": "copy",
                "rename_pattern": {"{zpi$r=3}": ""},
                "skip_if_exists": True,
            }],
            cleanup={
                "enabled": True,
                "recursive": False,
                "pattern": "*{zpi$r=3}*",
                "custom_patterns": [r"\{zpi\$r=3\}"],
                "after_sorting": True,
            },
        )

        operations = handler.plan_operations()
        result = handler.execute_operations(operations)

        assert [(op.action, op.source, op.destination) for op in operations] == [
            ("copy", tagged, copied),
            ("cleanup", tagged, cleaned),
        ]
        assert all(op.planned_skip_reason is not None for op in operations)
        assert result == (0, 0)
        assert result.skipped_count == 2
        assert tagged.exists()
        assert copied.exists()
        assert not cleaned.exists()

    def test_skip_counts_distinguish_explicit_and_protective_rules(
        self,
        tmp_path,
        nolog,
    ):
        src = tmp_path / "src"
        explicit, protected = make_files(src, "explicit.txt", "protected.txt")
        dest = tmp_path / "dest"
        make_files(dest, explicit.name, protected.name)
        handler = _handler(
            src,
            nolog,
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

        operations = handler.plan_operations()
        result = handler.execute_operations(operations)

        assert operations[0].configured_skip_if_exists is True
        assert operations[1].configured_skip_if_exists is None
        assert result.skipped_count == 2
        assert result.explicit_skipped_count == 1
        assert result.protected_skipped_count == 1

    def test_same_source_and_destination_skips_sorting_and_cleanup(
        self,
        tmp_path,
        nolog,
    ):
        """振り分けが同一パスの no-op なら、cleanup だけを実行しない。"""
        src = tmp_path / "src"
        original = make_files(src, "photo_DRAFT.png")[0]
        cleaned = src / "photo.png"
        handler = _handler(
            src,
            nolog,
            sorting_rules=[{
                "search": "*.png",
                "destination": str(src),
                "action": "move",
            }],
            cleanup={
                "enabled": True,
                "recursive": False,
                "custom_patterns": [r"_DRAFT"],
                "after_sorting": True,
            },
        )

        operations = handler.plan_operations()
        preview = PreviewGenerator(handler.config).generate_preview(
            operations,
            mode="Clean",
        )
        result = handler.execute_operations(operations)

        assert [operation.action for operation in operations] == [
            "move",
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


# ---------------------------------------------------------------------------
# ステップ順序
# ---------------------------------------------------------------------------

class TestStepOrder:
    def test_deletion_before_sorting(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "delete_me.png", "keep.png")
        dest = tmp_path / "dest"

        handler = _handler(src, nolog,
            deletion={"enabled": True, "strings": ["delete_me"], "recursive": False},
            sorting_rules=[{"search": "*.png", "destination": str(dest), "action": "move"}],
        )
        ops = handler.plan_operations()
        actions = [op.action for op in ops]

        assert actions.index("delete") < actions.index("move")

    def test_after_sorting_true_puts_cleanup_last(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "photo🎨.png")
        dest = tmp_path / "dest"

        handler = _handler(src, nolog,
            cleanup={"enabled": True, "recursive": False, "custom_patterns": [], "after_sorting": True},
            # copy は元ファイルが残るので、その後の cleanup が有効
            sorting_rules=[{"search": "*.png", "destination": str(dest), "action": "copy"}],
        )
        ops = handler.plan_operations()
        actions = [op.action for op in ops]

        assert actions.index("copy") < actions.index("cleanup")

    def test_after_sorting_false_puts_cleanup_before_sorting(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "photo🎨.png")
        dest = tmp_path / "dest"

        handler = _handler(src, nolog,
            cleanup={"enabled": True, "recursive": False, "custom_patterns": [], "after_sorting": False},
            sorting_rules=[{"search": "*.png", "destination": str(dest), "action": "move"}],
        )
        ops = handler.plan_operations()
        actions = [op.action for op in ops]

        assert actions.index("cleanup") < actions.index("move")

    def test_cleanup_then_sort_uses_cleaned_source_path(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "photo_DRAFT.png")
        dest = tmp_path / "dest"

        handler = _handler(
            src,
            nolog,
            cleanup={
                "enabled": True,
                "recursive": False,
                "custom_patterns": [r"_DRAFT"],
                "after_sorting": False,
            },
            sorting_rules=[{
                "search": "*.png",
                "destination": str(dest),
                "action": "move",
            }],
        )
        ops = handler.plan_operations()

        assert ops[0].source == src / "photo_DRAFT.png"
        assert ops[0].destination == src / "photo.png"
        assert ops[1].source == src / "photo.png"

        for op in ops:
            execute_file_op(op)
        assert (dest / "photo.png").exists()

    def test_cleanup_before_sorting_is_also_skipped_when_copy_is_skipped(
        self,
        tmp_path,
        nolog,
    ):
        """after_sorting の値によらず、同じ論理sourceの依存を守る。"""
        src = tmp_path / "src"
        tagged = make_files(src, "photo_DRAFT.png")[0]
        dest = tmp_path / "dest"
        existing = make_files(dest, "photo.png")[0]
        handler = _handler(
            src,
            nolog,
            cleanup={
                "enabled": True,
                "recursive": False,
                "custom_patterns": [r"_DRAFT"],
                "after_sorting": False,
            },
            sorting_rules=[{
                "search": "*.png",
                "destination": str(dest),
                "action": "copy",
                "skip_if_exists": True,
            }],
        )

        operations = handler.plan_operations()
        result = handler.execute_operations(operations)

        assert [op.action for op in operations] == ["cleanup", "copy"]
        assert all(op.planned_skip_reason is not None for op in operations)
        assert result == (0, 0)
        assert tagged.exists()
        assert existing.exists()
        assert not (src / "photo.png").exists()

    def test_rebuild_rechecks_disk_destination_occupied_after_cleanup_skip(
        self,
        tmp_path,
        nolog,
    ):
        """巻き戻しで復活した実ファイルを、後続操作が上書き予定にしない。"""
        src = tmp_path / "src"
        original, replacement = make_files(
            src,
            "photo_DRAFT.png",
            "{replacement}photo_DRAFT.png",
        )
        blocked = tmp_path / "blocked"
        make_files(blocked, "photo.png")
        handler = _handler(
            src,
            nolog,
            cleanup={
                "enabled": True,
                "recursive": False,
                "pattern": "photo_DRAFT.png",
                "custom_patterns": [r"_DRAFT"],
                "after_sorting": False,
            },
            sorting_rules=[
                {
                    "search": "photo.png",
                    "destination": str(blocked),
                    "action": "copy",
                },
                {
                    "search": "{replacement}*",
                    "destination": str(src),
                    "action": "move",
                    "rename_pattern": {"{replacement}": ""},
                },
            ],
        )

        operations = handler.plan_operations()
        result = handler.execute_operations(operations)

        assert [operation.action for operation in operations] == [
            "cleanup",
            "copy",
            "move",
        ]
        assert all(
            operation.planned_skip_reason is not None
            for operation in operations
        )
        assert result == (0, 0)
        assert result.skipped_count == 3
        assert original.exists()
        assert replacement.exists()

    def test_rebuild_turns_restored_planned_destination_conflict_into_skip(
        self,
        tmp_path,
        nolog,
    ):
        """巻き戻しで復活した予約先との衝突は例外ではなく skip にする。"""
        context = PlanningContext()
        reserved_source, later_source = make_files(
            tmp_path / "sources",
            "reserved.txt",
            "later.txt",
        )
        destination = tmp_path / "work" / "destination.txt"
        context.apply_operation(FileOperation(
            reserved_source,
            destination,
            "copy",
            "prior step",
        ))
        initial_planning_state = context.snapshot()
        skipped_cleanup = FileOperation(
            destination,
            tmp_path / "work" / "cleaned.txt",
            "cleanup",
            "cleanup",
        )
        context.apply_operation(skipped_cleanup)
        skipped_cleanup.planned_skip_reason = "dependency skip"
        skipped_cleanup.planned_skip_category = "protected"
        later_operation = FileOperation(
            later_source,
            destination,
            "move",
            "later",
        )
        handler = CleanModeHandler(
            clean_config(tmp_path, sorting_rules=[]),
            None,
            nolog,
            planning_context=context,
        )
        handler._record_planned_operations([later_operation])

        handler._rebuild_planning_state(
            [skipped_cleanup, later_operation],
            initial_planning_state,
            [skipped_cleanup],
        )

        assert later_operation.planned_skip_reason is not None

    def test_rebuild_preserves_explicit_disk_overwrite(self, tmp_path, nolog):
        destination = make_files(tmp_path / "work", "destination.txt")[0]
        source = make_files(tmp_path / "sources", "source.txt")[0]
        context = PlanningContext()
        initial_planning_state = context.snapshot()
        overwrite = FileOperation(source, destination, "copy", "overwrite")
        handler = CleanModeHandler(
            clean_config(tmp_path, sorting_rules=[]),
            None,
            nolog,
            planning_context=context,
        )
        handler._record_planned_operations(
            [overwrite],
            allow_disk_overwrite=True,
        )

        handler._rebuild_planning_state(
            [overwrite],
            initial_planning_state,
            [],
        )

        assert overwrite.planned_skip_reason is None
        assert overwrite.skip_if_exists is False


class TestSamePathSkipDisplay:
    """同一パスのスキップは、手動対応が要る「保存先の埋まり」と分けて表示する。"""

    def test_same_path_skip_is_not_reported_as_occupied_destination(
        self,
        tmp_path,
        nolog,
    ):
        src = tmp_path / "src"
        make_files(src, "photo.png")
        handler = _handler(
            src,
            nolog,
            sorting_rules=[{
                "search": "*.png",
                "destination": str(src),
                "action": "move",
            }],
        )

        operations = handler.plan_operations()
        preview = PreviewGenerator(handler.config).generate_preview(
            operations,
            mode="Clean",
        )
        result = handler.execute_operations(operations)

        assert [op.skip_category for op in operations] == ["same_path"]
        assert result.same_path_skipped_count == 1
        # 手動対応の一覧（保存先が埋まっていた分）には載せない。
        assert result.protected_skipped_count == 0
        assert "移動元と移動先が同じため 1 件をスキップ予定" in preview
        assert "保存先が埋まっていたため" not in preview
