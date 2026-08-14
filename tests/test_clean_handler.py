# -*- coding: utf-8 -*-
"""
Clean モードの動作テスト

deletion → cleanup → sorting_rules の3ステップが正しく動くことと、
after_sorting や skip_if_exists + rename_pattern の組み合わせを確認する。
"""

import pytest

from src.core.file_scanner import FileScanner
from src.core.planning_context import PlanningConflictError
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

        handler = _handler(src, nolog, deletion={"enabled": True, "strings": ["{zpi$r=1}"], "recursive": False})
        ops = handler.plan_operations()
        for op in ops:
            execute_file_op(op)

        assert not files[0].exists()
        assert files[1].exists()


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

    def test_duplicate_cleanup_destination_raises_planning_conflict(self, tmp_path, nolog):
        src = tmp_path / "src"
        first, second = make_files(src, "photo😀.png", "photo😃.png")
        handler = _handler(
            src,
            nolog,
            cleanup={"enabled": True, "recursive": False, "custom_patterns": []},
        )

        with pytest.raises(PlanningConflictError) as exc_info:
            handler.plan_operations()

        conflict = exc_info.value
        assert {conflict.first_source, conflict.second_source} == {first, second}
        assert conflict.destination == src / "photo.png"

    def test_planning_conflict_leaves_real_files_unchanged(self, tmp_path, nolog):
        src = tmp_path / "src"
        first, second = make_files(src, "photo😀.png", "photo😃.png")
        handler = _handler(
            src,
            nolog,
            cleanup={"enabled": True, "recursive": False, "custom_patterns": []},
        )

        with pytest.raises(PlanningConflictError):
            handler.plan_operations()

        assert first.exists()
        assert second.exists()
        assert not (src / "photo.png").exists()


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

        assert ops == []

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
