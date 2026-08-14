# -*- coding: utf-8 -*-
"""
file_executor の単体テスト

execute_file_op が move / copy / delete / rename / cleanup の
それぞれのアクションを正しく実行することを確認する。
"""

import pytest

from src.core.preview_generator import FileOperation
from src.utils.file_executor import execute_file_op, resolve_destination


# ---------------------------------------------------------------------------
# resolve_destination
# ---------------------------------------------------------------------------

class TestResolveDestination:
    def test_move_to_directory(self, tmp_path):
        src = tmp_path / "file.txt"
        dest_dir = tmp_path / "out"
        op = FileOperation(source=src, destination=dest_dir, action="move", reason="")
        assert resolve_destination(op) == dest_dir / "file.txt"

    def test_move_to_file_path(self, tmp_path):
        src = tmp_path / "old.txt"
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
    def test_move_to_directory(self, tmp_path):
        src = tmp_path / "src" / "file.txt"
        src.parent.mkdir()
        src.write_text("data")
        dest_dir = tmp_path / "dest"

        op = FileOperation(source=src, destination=dest_dir, action="move", reason="")
        execute_file_op(op)

        assert not src.exists()
        assert (dest_dir / "file.txt").read_text() == "data"

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
        dest_dir = tmp_path / "copy_dest"

        op = FileOperation(source=src, destination=dest_dir, action="copy", reason="")
        execute_file_op(op)

        assert src.exists()
        assert (dest_dir / "file.txt").read_text() == "hello"

    def test_delete(self, tmp_path):
        src = tmp_path / "remove_me.txt"
        src.touch()

        op = FileOperation(source=src, destination=None, action="delete", reason="")
        execute_file_op(op)

        assert not src.exists()

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
        dest = tmp_path / "a" / "b" / "c" / "dest"

        op = FileOperation(source=src, destination=dest, action="move", reason="")
        execute_file_op(op)

        assert (dest / "file.txt").exists()
