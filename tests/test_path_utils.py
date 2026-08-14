# -*- coding: utf-8 -*-
"""パス正規化ヘルパーの回帰テスト。"""

from pathlib import Path

from src.utils.path_utils import to_path


def test_to_path_resolves_relative_path_and_parent_segments(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert to_path("input/../output/file.txt") == tmp_path / "output" / "file.txt"


def test_to_path_normalizes_parent_segments_in_wsl_drive_path():
    assert to_path(r"D:\Images\..\Loot\file.txt") == Path(
        "/mnt/d/Loot/file.txt"
    )
