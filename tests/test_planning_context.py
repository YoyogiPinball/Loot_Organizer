# -*- coding: utf-8 -*-
"""計画中の仮想ファイル状態に関する回帰テスト。"""

from pathlib import Path

from src.core.planning_context import PlanningContext
from src.core.preview_generator import FileOperation


def _operation(source: Path, destination: Path, action: str = "move"):
    return FileOperation(source, destination, action, "test")


def test_wsl_drive_paths_with_different_case_share_one_virtual_file():
    context = PlanningContext()
    backing = Path("/real/Original.dat")
    displayed_path = Path("/mnt/c/Users/Alice/Loot/a.txt")
    alternate_case = Path("/mnt/c/users/alice/loot/a.txt")

    context.apply_operation(_operation(backing, displayed_path, "copy"))

    assert context.is_file(alternate_case)
    assert context.backing_path(alternate_case) == backing
    assert context.identity(alternate_case) == context.identity(displayed_path)
    assert context.directory_exists(Path("/mnt/c/users/alice/loot"))
    assert context.matching_virtual_files(
        Path("/mnt/c/users/alice/loot"),
        "*.txt",
        recursive=False,
    ) == [displayed_path]

    context.apply_operation(_operation(alternate_case, alternate_case, "delete"))

    assert not context.is_file(displayed_path)
    assert context.matching_virtual_files(
        Path("/mnt/c/Users/Alice/Loot"),
        "*.txt",
        recursive=False,
    ) == []


def test_native_linux_paths_with_different_case_remain_distinct():
    context = PlanningContext()
    upper = Path("/home/user/Foo/a.txt")
    lower = Path("/home/user/foo/a.txt")

    context.apply_operation(_operation(Path("/real/upper"), upper, "copy"))
    context.apply_operation(_operation(Path("/real/lower"), lower, "copy"))

    assert context.identity(upper) != context.identity(lower)
    assert context.backing_path(upper) == Path("/real/upper")
    assert context.backing_path(lower) == Path("/real/lower")


def test_parent_segments_are_normalized_at_planning_context_boundaries(tmp_path):
    context = PlanningContext()
    source = tmp_path / "source.txt"
    source.touch()
    destination_with_parent = tmp_path / "stage" / ".." / "dest" / "file.txt"
    normalized_destination = tmp_path / "dest" / "file.txt"

    context.apply_operation(_operation(source, destination_with_parent))

    assert not context.is_file(tmp_path / "other" / ".." / "source.txt")
    assert context.is_file(normalized_destination)
    assert context.directory_exists(tmp_path / "unused" / ".." / "dest")
    assert context.backing_path(normalized_destination) == source
    assert context.active_disk_files([tmp_path / "other" / ".." / "source.txt"]) == []
    assert context.matching_virtual_files(
        tmp_path / "unused" / ".." / "dest",
        "*.txt",
        recursive=False,
    ) == [normalized_destination]


def test_released_planned_destination_can_be_used_again():
    context = PlanningContext()
    first = Path("/source/A.txt")
    second = Path("/source/B.txt")
    staging = Path("/stage/X.txt")
    final = Path("/final/Y.txt")

    context.apply_operation(_operation(first, staging))
    context.apply_operation(_operation(staging, final))
    context.apply_operation(_operation(second, staging))

    assert context.backing_path(final) == first
    assert context.backing_path(staging) == second
