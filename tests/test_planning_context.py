# -*- coding: utf-8 -*-
"""計画中の仮想ファイル状態に関する回帰テスト。"""

import os
from pathlib import Path

import pytest

from tests.conftest import posix_only
from src.core.file_scanner import FileScanner
from src.core.planning_context import PlanningContext, _compile_glob
from src.core.preview_generator import FileOperation


def _operation(source: Path, destination: Path, action: str = "move"):
    return FileOperation(source, destination, action, "test")


@posix_only
def test_wsl_drive_paths_with_different_case_share_one_virtual_file():
    context = PlanningContext()
    backing = Path("/real/Original.dat")
    displayed_path = Path("/mnt/c/Users/Alice/Loot/a.txt")
    alternate_case = Path("/mnt/c/users/alice/loot/a.txt")

    assert context.paths_equal(displayed_path, alternate_case)

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


@posix_only
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


@posix_only
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


def _seed_tree(context, root, relative_paths):
    """仮想側と実側に同じ構成を作り、仮想パスを root 配下に登録する。"""
    source_dir = root.parent / f"{root.name}_seed"
    source_dir.mkdir(exist_ok=True)
    for index, relative in enumerate(relative_paths):
        real = root / relative
        real.parent.mkdir(parents=True, exist_ok=True)
        real.write_text("x", encoding="utf-8")

        seed = source_dir / f"seed{index}"
        seed.write_text("x", encoding="utf-8")
        context.apply_operation(_operation(seed, root / relative))


def _real_glob(root, pattern, recursive):
    found = root.rglob(pattern) if recursive else root.glob(pattern)
    return sorted(path.relative_to(root).as_posix() for path in found if path.is_file())


def _virtual_glob(context, root, pattern, recursive):
    return sorted(
        Path(path).relative_to(root).as_posix()
        for path in context.matching_virtual_files(root, pattern, recursive)
    )


@posix_only
def test_virtual_glob_matches_real_glob_for_patterns_with_separators(tmp_path):
    """パターンに `/` や `**` を含むとき、仮想側と実側の結果が一致する。

    修正前は次の3通りでズレていた。
      - `sub/*.jpg`（非再帰）: 仮想側が 0 件
      - `**/*.jpg`（非再帰）: 仮想側が 0 件
      - `**/*.jpg`（再帰）: 仮想側が直下の a.jpg を取りこぼす
    """
    root = tmp_path / "tree"
    root.mkdir()
    context = PlanningContext()
    _seed_tree(
        context,
        root,
        [
            "a.jpg",
            "A.JPG",
            "sub/b.jpg",
            "sub/deep/c.jpg",
            "note.txt",
            ".hidden.jpg",
            "x]y.txt",
            "a-b.txt",
        ],
    )

    patterns = [
        "*.jpg",
        "*.JPG",
        "*.[jJ]pg",
        "sub/*.jpg",
        "sub/*",
        "sub/**/*.jpg",
        "**/*.jpg",
        "**",
        "*",
        "?.jpg",
        "*.*",
        "*.[!t]*",
        "[a-z].jpg",
        # 区切りの揺れと文字クラスの端。glob 側と同じ扱いになるか。
        "./*.jpg",
        "sub//*.jpg",
        ".*",
        "[]]*",
        "[[]*",
        "[a-]*",
        "*[.]jpg",
        # fnmatch と同じ扱いになるか（Codex の反証で判明した3件）。
        "[^a]*",      # 先頭の ^ は否定ではなくリテラル
        "[z-a]*",     # 逆順の範囲。正規表現に素通しすると re.error になる
        "sub/",       # 末尾の / はディレクトリ限定
    ]
    for pattern in patterns:
        for recursive in (False, True):
            assert _virtual_glob(context, root, pattern, recursive) == _real_glob(
                root, pattern, recursive
            ), f"pattern={pattern!r} recursive={recursive}"


def test_virtual_glob_ignores_the_scanned_directory_itself(tmp_path):
    """走査対象ディレクトリと同じパスの仮想エントリで相対パスが壊れない。"""
    root = tmp_path / "tree"
    root.mkdir()
    context = PlanningContext()
    context.apply_operation(_operation(tmp_path / "seed.txt", root))

    assert context.matching_virtual_files(root, "*", recursive=False) == []
    assert context.matching_virtual_files(root, "*", recursive=True) == []


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlink 非対応環境")
def test_recursive_virtual_scan_does_not_follow_directory_symlink(
    tmp_path,
    nolog,
):
    """実 rglob と同様、リンク経由の仮想パスを重複して返さない。"""
    root = tmp_path / "tree"
    target = root / "target"
    target.mkdir(parents=True)
    real_file = target / "a.jpg"
    real_file.write_text("real", encoding="utf-8")
    link = root / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"directory symlink を作成できません: {exc}")

    seed = tmp_path / "seed.dat"
    seed.write_text("seed", encoding="utf-8")
    context = PlanningContext()
    context.apply_operation(_operation(seed, link / "a.jpg", "copy"))
    scanner = FileScanner(root, nolog, planning_context=context)

    assert scanner.scan_files("*.jpg", recursive=True) == [real_file]


def test_windows_glob_rules_ignore_case_and_accept_backslashes():
    """Windows で直接動かしたときの Path.glob の規則にそろっているか。

    Windows の `Path.glob` は大文字小文字を区別せず、`\\` も区切りとして扱う。
    Linux 上では実 glob と突き合わせられないので、規則そのものを固定する。
    """
    matcher = _compile_glob("sub\\*.JPG", False, True, ("\\",))

    assert matcher.match("sub/a.jpg")
    assert matcher.match("SUB/A.JPG")
    assert not matcher.match("a.jpg")
    assert not matcher.match("sub/deep/a.jpg")


def test_posix_glob_rules_stay_case_sensitive():
    """WSL から /mnt/c を触る場合は Linux 側の規則（大小文字を区別）になる。"""
    matcher = _compile_glob("*.JPG", False, False, ())

    assert matcher.match("a.JPG")
    assert not matcher.match("a.jpg")


def test_absolute_virtual_glob_pattern_raises_japanese_config_error():
    pattern = "/tmp/*.jpg"

    with pytest.raises(ValueError) as exc_info:
        _compile_glob(pattern, False, False, ())

    message = str(exc_info.value)
    assert "絶対パスの検索パターンは指定できません" in message
    assert pattern in message


@pytest.mark.parametrize(
    ("pattern", "recursive", "expected"),
    [
        ("../*.jpg", False, []),
        ("../*.jpg", True, ["a.jpg"]),
        ("sub/../*.jpg", False, ["a.jpg"]),
        ("sub/../*.jpg", True, ["a.jpg"]),
    ],
)
def test_virtual_glob_parent_segments_match_pathlib_behavior(
    tmp_path,
    pattern,
    recursive,
    expected,
):
    root = tmp_path / "tree"
    root.mkdir()
    (root / "sub").mkdir()
    context = PlanningContext()
    _seed_tree(context, root, ["a.jpg"])

    real_paths = root.rglob(pattern) if recursive else root.glob(pattern)
    assert sorted(path.name for path in real_paths if path.is_file()) == expected
    assert _virtual_glob(context, root, pattern, recursive) == expected
