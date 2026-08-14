# -*- coding: utf-8 -*-
"""
Sort モードの動作テスト

move_rules に基づいてファイルが正しく振り分けられることを確認する。
"""

import pytest

from src.core.file_scanner import FileScanner
from src.core.preview_generator import PreviewGenerator
from src.handlers.sort_handler import SortModeHandler
from src.utils.file_executor import execute_file_op
from tests.conftest import make_files, sort_config


def _handler(src_dir, move_rules, nolog, **extra):
    cfg = sort_config(src_dir, move_rules, **extra)
    scanner = FileScanner(str(src_dir), nolog)
    return SortModeHandler(cfg, scanner, nolog)


# ---------------------------------------------------------------------------
# 基本動作
# ---------------------------------------------------------------------------

class TestBasicMove:
    def test_matched_file_becomes_operation(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "photo.jpg")
        dest = tmp_path / "dest"

        handler = _handler(src, [{"pattern": "*.jpg", "dest": str(dest), "description": "jpg"}], nolog)
        ops = handler.plan_operations()

        assert len(ops) == 1
        assert ops[0].source.name == "photo.jpg"
        assert ops[0].action == "move"

    def test_unmatched_file_excluded(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "doc.pdf")
        dest = tmp_path / "dest"

        handler = _handler(src, [{"pattern": "*.jpg", "dest": str(dest), "description": "jpg"}], nolog)
        ops = handler.plan_operations()

        assert ops == []

    def test_disabled_rule_skipped(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "photo.jpg")
        dest = tmp_path / "dest"

        handler = _handler(src, [{"pattern": "*.jpg", "dest": str(dest), "enabled": False, "description": "jpg"}], nolog)
        ops = handler.plan_operations()

        assert ops == []

    def test_first_rule_wins(self, tmp_path, nolog):
        """同じファイルが複数ルールにマッチしても最初のルールだけ適用される"""
        src = tmp_path / "src"
        make_files(src, "photo.jpg")
        dest1 = tmp_path / "d1"
        dest2 = tmp_path / "d2"

        rules = [
            {"pattern": "*.jpg", "dest": str(dest1), "description": "rule1"},
            {"pattern": "photo*", "dest": str(dest2), "description": "rule2"},
        ]
        handler = _handler(src, rules, nolog)
        ops = handler.plan_operations()

        assert len(ops) == 1
        assert str(dest1) in str(ops[0].destination)

    def test_first_rule_still_wins_after_in_place_rename(self, tmp_path, nolog):
        """仮想リネーム後の名前が後続ルールに一致しても同じ実体は再処理しない"""
        src = tmp_path / "src"
        make_files(src, "photo.Exif")
        dest = tmp_path / "dest"

        rules = [
            {
                "pattern": "*.Exif",
                "dest": str(src),
                "rename_pattern": {".Exif": ".jpg"},
                "description": "rename",
            },
            {"pattern": "*.jpg", "dest": str(dest), "description": "later"},
        ]
        handler = _handler(src, rules, nolog)
        ops = handler.plan_operations()

        assert len(ops) == 1
        assert ops[0].destination == src / "photo.jpg"

    def test_execute_actually_moves_file(self, tmp_path, nolog):
        src = tmp_path / "src"
        (src).mkdir()
        f = src / "move_me.txt"
        f.touch()
        dest = tmp_path / "dest"

        handler = _handler(src, [{"pattern": "*.txt", "dest": str(dest), "description": "txt"}], nolog)
        ops = handler.plan_operations()
        for op in ops:
            execute_file_op(op)

        assert not f.exists()
        assert (dest / "move_me.txt").exists()

    def test_dot_named_destination_is_used_as_directory(self, tmp_path, nolog):
        src = tmp_path / "src"
        source = make_files(src, "photo.jpg")[0]
        dest = tmp_path / "output" / "v2.0"

        handler = _handler(
            src,
            [{"pattern": "*.jpg", "dest": str(dest), "description": "jpg"}],
            nolog,
        )
        operations = handler.plan_operations()
        preview = PreviewGenerator(preview_mode="all").generate_preview(
            operations,
            "Sort",
        )

        assert operations[0].destination == dest / source.name
        assert str(dest) in preview

        execute_file_op(operations[0])

        assert not source.exists()
        assert (dest / source.name).exists()


# ---------------------------------------------------------------------------
# rename_pattern（Sort モードへの追加対応 Bug-2 修正確認）
# ---------------------------------------------------------------------------

class TestRenamePattern:
    def test_removes_prefix_tag(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "{zpi$r=3}image.png")
        dest = tmp_path / "dest"

        handler = _handler(src, [{
            "pattern": "*{zpi$r=3}*",
            "dest": str(dest),
            "rename_pattern": {"{zpi$r=3}": ""},
            "description": "remove tag",
        }], nolog)
        ops = handler.plan_operations()

        assert len(ops) == 1
        assert ops[0].destination.name == "image.png"

    def test_replaces_extension(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "photo.Exif")
        dest = tmp_path / "dest"

        handler = _handler(src, [{
            "pattern": "*.Exif",
            "dest": str(dest),
            "rename_pattern": {".Exif": ".jpg"},
            "description": "exif to jpg",
        }], nolog)
        ops = handler.plan_operations()

        assert len(ops) == 1
        assert ops[0].destination.name == "photo.jpg"

    def test_case_insensitive(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "FILE.EXIF")
        dest = tmp_path / "dest"

        handler = _handler(src, [{
            "pattern": "*.EXIF",
            "dest": str(dest),
            "rename_pattern": {".exif": ".jpg"},
            "description": "case insensitive",
        }], nolog)
        ops = handler.plan_operations()

        assert len(ops) == 1
        assert ops[0].destination.suffix == ".jpg"


# ---------------------------------------------------------------------------
# skip_if_exists（rename_pattern との組み合わせ Bug-2 回帰テスト）
# ---------------------------------------------------------------------------

class TestSkipIfExists:
    def test_skips_when_renamed_dest_exists(self, tmp_path, nolog):
        """rename 後のファイルが既存 → スキップされる"""
        src = tmp_path / "src"
        make_files(src, "{tag}file.png")
        dest = tmp_path / "dest"
        dest.mkdir()
        (dest / "file.png").touch()  # リネーム後の名前で既存

        handler = _handler(src, [{
            "pattern": "*{tag}*",
            "dest": str(dest),
            "rename_pattern": {"{tag}": ""},
            "skip_if_exists": True,
            "description": "test",
        }], nolog)
        ops = handler.plan_operations()

        assert ops == []

    def test_moves_when_renamed_dest_absent(self, tmp_path, nolog):
        """rename 後のファイルが未存在 → 処理される"""
        src = tmp_path / "src"
        make_files(src, "{tag}file.png")
        dest = tmp_path / "dest"
        dest.mkdir()
        # リネーム後ファイルは存在しない

        handler = _handler(src, [{
            "pattern": "*{tag}*",
            "dest": str(dest),
            "rename_pattern": {"{tag}": ""},
            "skip_if_exists": True,
            "description": "test",
        }], nolog)
        ops = handler.plan_operations()

        assert len(ops) == 1

    def test_skips_without_rename_pattern(self, tmp_path, nolog):
        """rename_pattern なし・同名ファイルが dest に存在 → スキップ"""
        src = tmp_path / "src"
        make_files(src, "file.png")
        dest = tmp_path / "dest"
        dest.mkdir()
        (dest / "file.png").touch()

        handler = _handler(src, [{
            "pattern": "*.png",
            "dest": str(dest),
            "skip_if_exists": True,
            "description": "test",
        }], nolog)
        ops = handler.plan_operations()

        assert ops == []


# ---------------------------------------------------------------------------
# rename: random
# ---------------------------------------------------------------------------

class TestRandomRename:
    def test_generates_hex_name_with_correct_extension(self, tmp_path, nolog):
        src = tmp_path / "src"
        make_files(src, "image (1).jpg")
        dest = tmp_path / "dest"

        handler = _handler(src, [{
            "pattern": "image (*).jpg",
            "dest": str(dest),
            "rename": "random",
            "description": "random rename",
        }], nolog)
        ops = handler.plan_operations()

        assert len(ops) == 1
        name = ops[0].destination.name
        stem, ext = ops[0].destination.stem, ops[0].destination.suffix
        assert ext == ".jpg"
        assert len(stem) == 10
        assert stem.isalnum()
