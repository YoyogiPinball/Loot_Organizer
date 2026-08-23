# -*- coding: utf-8 -*-
"""
file_executor の単体テスト

execute_file_op が move / copy / delete / rename / cleanup の
それぞれのアクションを正しく実行することを確認する。
"""

import pytest

from src.core.preview_generator import FileOperation, PreviewGenerator
from src.utils.file_executor import (
    SkippedFileOperation,
    SourceChangedError,
    execute_file_op,
    operation_log_message,
    resolve_destination,
)


# ---------------------------------------------------------------------------
# resolve_destination
# ---------------------------------------------------------------------------

class TestResolveDestination:
    def test_move_returns_final_destination_as_is(self, tmp_path):
        src = tmp_path / "file.txt"
        dest_file = tmp_path / "out" / "new.txt"
        op = FileOperation(source=src, destination=dest_file, action="move", reason="")
        assert resolve_destination(op) == dest_file

    def test_delete_returns_none(self, tmp_path):
        op = FileOperation(source=tmp_path / "x", destination=None, action="delete", reason="")
        assert resolve_destination(op) is None

    def test_cleanup_returns_destination_as_is(self, tmp_path):
        src = tmp_path / "a.txt"
        dest = tmp_path / "b.txt"
        op = FileOperation(source=src, destination=dest, action="cleanup", reason="")
        assert resolve_destination(op) == dest


# ---------------------------------------------------------------------------
# execute_file_op
# ---------------------------------------------------------------------------

class TestExecuteFileOp:
    def test_move_to_final_file_path(self, tmp_path):
        src = tmp_path / "src" / "file.txt"
        src.parent.mkdir()
        src.write_text("data")
        dest = tmp_path / "dest" / src.name

        op = FileOperation(source=src, destination=dest, action="move", reason="")
        execute_file_op(op)

        assert not src.exists()
        assert dest.read_text() == "data"

    def test_move_to_file_path(self, tmp_path):
        src = tmp_path / "original.png"
        src.touch()
        dest = tmp_path / "out" / "renamed.png"

        op = FileOperation(source=src, destination=dest, action="move", reason="")
        execute_file_op(op)

        assert not src.exists()
        assert dest.exists()

    def test_copy_keeps_source(self, tmp_path):
        src = tmp_path / "file.txt"
        src.write_text("hello")
        dest = tmp_path / "copy_dest" / src.name

        op = FileOperation(source=src, destination=dest, action="copy", reason="")
        execute_file_op(op)

        assert src.exists()
        assert dest.read_text() == "hello"

    def test_delete_defaults_to_trash(self, tmp_path, monkeypatch):
        src = tmp_path / "remove_me.txt"
        src.touch()
        trashed = []
        monkeypatch.setattr(
            "src.utils.file_executor.send2trash",
            lambda path: trashed.append(path),
        )

        op = FileOperation(source=src, destination=None, action="delete", reason="")
        execute_file_op(op)

        assert trashed == [str(src)]
        assert src.exists()

    def test_delete_permanent_calls_unlink_only_when_explicit(
        self,
        tmp_path,
        monkeypatch,
    ):
        src = tmp_path / "remove_me.txt"
        src.touch()
        calls = []
        original_unlink = type(src).unlink

        def record_unlink(path, *args, **kwargs):
            calls.append(path)
            return original_unlink(path, *args, **kwargs)

        monkeypatch.setattr(type(src), "unlink", record_unlink)
        monkeypatch.setattr(
            "src.utils.file_executor.send2trash",
            lambda path: pytest.fail("permanent では send2trash を呼ばない"),
        )

        op = FileOperation(
            source=src,
            destination=None,
            action="delete",
            reason="",
            delete_mode="permanent",
        )
        execute_file_op(op)

        assert calls == [src]
        assert not src.exists()

    def test_trash_failure_does_not_fall_back_to_unlink(
        self,
        tmp_path,
        monkeypatch,
    ):
        src = tmp_path / "remove_me.txt"
        src.touch()
        unlink_calls = []

        def fail_trash(path):
            raise OSError("trash unavailable")

        monkeypatch.setattr("src.utils.file_executor.send2trash", fail_trash)
        monkeypatch.setattr(
            type(src),
            "unlink",
            lambda path, *args, **kwargs: unlink_calls.append(path),
        )

        op = FileOperation(source=src, destination=None, action="delete", reason="")
        with pytest.raises(OSError, match="trash unavailable"):
            execute_file_op(op)

        assert unlink_calls == []
        assert src.exists()

    def test_rename_in_place(self, tmp_path):
        src = tmp_path / "old.txt"
        src.touch()
        new = tmp_path / "new.txt"

        op = FileOperation(source=src, destination=new, action="rename", reason="")
        execute_file_op(op)

        assert not src.exists()
        assert new.exists()

    def test_cleanup_in_place(self, tmp_path):
        src = tmp_path / "dirty file.txt"
        src.touch()
        clean = tmp_path / "clean.txt"

        op = FileOperation(source=src, destination=clean, action="cleanup", reason="")
        execute_file_op(op)

        assert not src.exists()
        assert clean.exists()

    def test_move_creates_parent_dirs(self, tmp_path):
        src = tmp_path / "file.txt"
        src.touch()
        dest = tmp_path / "a" / "b" / "c" / "file.txt"

        op = FileOperation(source=src, destination=dest, action="move", reason="")
        execute_file_op(op)

        assert dest.exists()


class TestTimeOfCheckToTimeOfUse:
    def test_source_replacement_is_rejected_before_move(self, tmp_path):
        src = tmp_path / "source.txt"
        src.write_text("planned", encoding="utf-8")
        dest = tmp_path / "dest" / "source.txt"
        op = FileOperation(src, dest, "move", "TOCTOU test")

        replacement = tmp_path / "replacement.txt"
        replacement.write_text("different contents", encoding="utf-8")
        replacement.replace(src)

        with pytest.raises(SourceChangedError, match="計画時から変更"):
            execute_file_op(op)

        assert src.read_text(encoding="utf-8") == "different contents"
        assert not dest.exists()

    def test_operation_without_fingerprint_accepts_later_created_source(
        self,
        tmp_path,
    ):
        virtual_source = tmp_path / "staging" / "future.txt"
        destination = tmp_path / "final" / "future.txt"
        op = FileOperation(virtual_source, destination, "move", "Pipeline dependency")
        assert op.source_fingerprint is None

        virtual_source.parent.mkdir()
        virtual_source.write_text("created by earlier step", encoding="utf-8")

        execute_file_op(op)

        assert destination.read_text(encoding="utf-8") == "created by earlier step"

    def test_skip_if_exists_rechecks_destination_at_execution(self, tmp_path):
        src = tmp_path / "source.txt"
        src.write_text("source", encoding="utf-8")
        destination = tmp_path / "dest" / "source.txt"
        op = FileOperation(
            src,
            destination,
            "move",
            "skip test",
            skip_if_exists=True,
        )
        destination.parent.mkdir()
        destination.write_text("created after planning", encoding="utf-8")

        result = execute_file_op(op)

        assert isinstance(result, SkippedFileOperation)
        assert "実行直前" in result.reason
        assert src.exists()
        assert destination.read_text(encoding="utf-8") == "created after planning"

    @pytest.mark.parametrize("action", ["move", "copy", "rename"])
    def test_existing_destination_is_skipped_by_default(self, tmp_path, action):
        source = tmp_path / f"source-{action}.txt"
        destination = tmp_path / f"destination-{action}.txt"
        source.write_text("source", encoding="utf-8")
        destination.write_text("preserved", encoding="utf-8")
        operation = FileOperation(source, destination, action, "duplicate")

        result = execute_file_op(operation)

        assert isinstance(result, SkippedFileOperation)
        assert source.read_text(encoding="utf-8") == "source"
        assert destination.read_text(encoding="utf-8") == "preserved"


class TestDeleteDisplay:
    def test_log_distinguishes_trash_and_permanent_delete(self, tmp_path):
        trash = FileOperation(tmp_path / "trash.txt", None, "delete", "old")
        permanent = FileOperation(
            tmp_path / "permanent.txt",
            None,
            "delete",
            "secret",
            delete_mode="permanent",
        )

        assert "ゴミ箱" in operation_log_message(trash)
        assert "完全削除" in operation_log_message(permanent)

    def test_preview_distinguishes_trash_and_permanent_delete(self, tmp_path):
        operations = [
            FileOperation(tmp_path / "trash.txt", None, "delete", "old"),
            FileOperation(
                tmp_path / "permanent.txt",
                None,
                "delete",
                "secret",
                delete_mode="permanent",
            ),
        ]

        preview = PreviewGenerator(preview_mode="all").generate_preview(
            operations,
            "Clean",
        )

        assert "ゴミ箱へ移動" in preview
        assert "完全削除" in preview
