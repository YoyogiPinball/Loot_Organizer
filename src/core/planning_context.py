# -*- coding: utf-8 -*-
"""In-memory file-system state used while planning dependent operations."""

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Hashable, Iterable

from .preview_generator import FileOperation
from ..utils.file_executor import resolve_destination
from ..utils.path_utils import to_path


def _translate_character_class(segment: str, index: int) -> tuple[str, int]:
    """Translate ``segment[index:]`` starting at a ``[``.

    ``fnmatch.translate`` と同じ規則にそろえてある。とくに次の3点は自前で
    書くと取り違えやすい。
      - 否定記号は ``!`` だけ。先頭の ``^`` はリテラル文字として扱う
      - ``[z-a]`` のような逆順の範囲は正規表現ではエラーになるので取り除く
      - ``[]]`` は「``]`` 1文字」を意味する（閉じ括弧の探索は1つ後ろから）
    """
    length = len(segment)
    close = index
    if close < length and segment[close] == '!':
        close += 1
    if close < length and segment[close] == ']':
        close += 1
    while close < length and segment[close] != ']':
        close += 1
    if close >= length:
        return r'\[', index

    body = segment[index:close]
    if '-' not in body:
        body = body.replace('\\', r'\\')
    else:
        # `-` を範囲として使っている箇所と、ただの文字として置かれている箇所を
        # 分けたうえで、逆順になっている範囲を畳む（fnmatch と同じ手順）。
        chunks = []
        start = index
        cursor = index + 2 if segment[index] == '!' else index + 1
        while True:
            cursor = segment.find('-', cursor, close)
            if cursor < 0:
                break
            chunks.append(segment[start:cursor])
            start = cursor + 1
            cursor = cursor + 3
        chunk = segment[start:close]
        if chunk:
            chunks.append(chunk)
        else:
            chunks[-1] += '-'
        for position in range(len(chunks) - 1, 0, -1):
            if chunks[position - 1][-1] > chunks[position][0]:
                chunks[position - 1] = (
                    chunks[position - 1][:-1] + chunks[position][1:]
                )
                del chunks[position]
        body = '-'.join(
            piece.replace('\\', r'\\').replace('-', r'\-') for piece in chunks
        )

    if not body:
        return '(?!)', close + 1
    if body == '!':
        return '[^/]', close + 1
    if body[0] == '!':
        body = '^' + body[1:]
    elif body[0] in ('^', '['):
        body = '\\' + body
    return f'[{body}]', close + 1


def _translate_segment(segment: str) -> str:
    """Translate one glob segment into a regex that never crosses ``/``.

    ``fnmatch.translate`` をそのまま使えないのは、あちらが ``*`` を ``.*`` に
    するため。``.`` はディレクトリ区切りにも当たってしまうので、区切りを
    含まない文字クラス ``[^/]`` に置き換える。
    """
    out = []
    index = 0
    length = len(segment)
    while index < length:
        char = segment[index]
        index += 1
        if char == '*':
            out.append('[^/]*')
        elif char == '?':
            out.append('[^/]')
        elif char == '[':
            translated, index = _translate_character_class(segment, index)
            out.append(translated)
        else:
            out.append(re.escape(char))
    return ''.join(out)


def platform_glob_rules() -> tuple[bool, tuple[str, ...]]:
    """Return how ``Path.glob`` behaves on the platform we are running on.

    戻り値は (大文字小文字を無視するか, ``/`` 以外の区切り文字)。
    Windows で直接動かすと ``Path.glob`` は大小文字を区別せず、``\\`` も
    区切りとして解釈する。WSL から ``/mnt/c`` を触る場合は Linux 側の規則
    （大小文字を区別・区切りは ``/`` のみ）になる。
    """
    case_insensitive = os.path.normcase('A') != 'A'
    separators = tuple(
        separator
        for separator in (os.sep, os.altsep)
        if separator and separator != '/'
    )
    return case_insensitive, separators


@lru_cache(maxsize=256)
def _compile_glob(
    pattern: str,
    recursive: bool,
    case_insensitive: bool = False,
    separators: tuple[str, ...] = (),
) -> re.Pattern:
    """Build the regex that ``Path.glob``/``Path.rglob`` would match with.

    ``rglob(pattern)`` は ``glob('**/' + pattern)`` と同義なので、
    recursive のときだけ先頭に ``**`` を足す。
    """
    original_pattern = pattern
    for separator in separators:
        pattern = pattern.replace(separator, '/')

    if pattern.startswith('/') or re.match(r'^[A-Za-z]:/', pattern):
        raise ValueError(
            "絶対パスの検索パターンは指定できません: "
            f"{original_pattern}"
        )

    # 末尾の `/` はディレクトリ限定の指定。ここが持つのはファイルだけ。
    directory_only = pattern.endswith('/')

    # 空セグメント（`a//b`）とカレント指定（`./a`）は glob 側でも無視される。
    raw_segments = [
        segment
        for segment in pattern.split('/')
        if segment and segment != '.'
    ]
    if recursive:
        raw_segments.insert(0, '**')

    # Path は各走査位置からパターンを字句どおりに評価する。rglob では先頭に
    # `**/` が付くため、`../` はその再帰セグメントと相殺される。
    segments = []
    for segment in raw_segments:
        if segment == '..' and segments and segments[-1] != '..':
            segments.pop()
        else:
            segments.append(segment)

    expression = ''
    for position, segment in enumerate(segments):
        last = position == len(segments) - 1
        if segment == '**':
            # 0 個以上のディレクトリ階層。ただし末尾の ** は glob では
            # ディレクトリだけに当たるので、ファイルには当たらなくする。
            expression += '(?!)' if last else '(?:[^/]+/)*'
        elif last and directory_only:
            expression += '(?!)'
        else:
            expression += _translate_segment(segment) + '/'

    expression = expression.removesuffix('/')
    flags = re.IGNORECASE if case_insensitive else 0
    return re.compile(f'(?s:{expression})\\Z', flags)


class PlanningConflictError(Exception):
    """Raised when multiple planned operations share one destination."""

    def __init__(
        self,
        first_source: Path,
        second_source: Path,
        destination: Path,
    ):
        self.first_source = Path(first_source)
        self.second_source = Path(second_source)
        self.destination = Path(destination)
        super().__init__(
            f"移動先が衝突しています: {self.first_source} / "
            f"{self.second_source} -> {self.destination}"
        )


class PlanningContext:
    """
    Track the paths that will exist after each planned operation.

    The real file system is never changed during planning.  A virtual path maps
    back to the real file that supplies its metadata, allowing later pipeline
    steps to scan renamed, moved, or copied files before execution starts.
    """

    def __init__(self):
        # 辞書・集合のキーは _path_key で比較用に正規化する。I/O や表示で
        # 大文字小文字を保持できるよう、仮想パス本体は別に保存する。
        self._virtual_files: dict[Path, Path] = {}
        self._virtual_paths: dict[Path, Path] = {}
        self._identities: dict[Path, Hashable] = {}
        self._removed_files: set[Path] = set()
        self._planned_destinations: dict[Path, Path] = {}

    @staticmethod
    def _normalize(path: Path) -> Path:
        """Return an absolute, lexically normalized I/O path."""
        return to_path(path)

    @classmethod
    def _path_key(cls, path: Path) -> Path:
        """Return a comparison key without changing native Linux case rules."""
        normalized = cls._normalize(path)
        parts = normalized.parts
        if (
            len(parts) >= 3
            and parts[0] == '/'
            and parts[1] == 'mnt'
            and len(parts[2]) == 1
            and parts[2].isascii()
            and parts[2].isalpha()
        ):
            return Path(str(normalized).casefold())
        return normalized

    def is_file(self, path: Path) -> bool:
        """Return whether ``path`` exists in the planned state."""
        path = self._normalize(path)
        key = self._path_key(path)
        if key in self._virtual_files:
            return True
        if key in self._removed_files:
            return False
        return path.is_file()

    @classmethod
    def paths_equal(cls, first: Path, second: Path) -> bool:
        """Compare paths using the same normalization as planning-state keys."""
        return cls._path_key(first) == cls._path_key(second)

    def is_planned_destination(self, path: Path) -> bool:
        """Return whether an earlier operation currently reserves ``path``."""
        return self._path_key(path) in self._planned_destinations

    def snapshot(self) -> tuple[dict, dict, dict, set, dict]:
        """Return a shallow copy of the virtual state for dependency replanning."""
        return (
            self._virtual_files.copy(),
            self._virtual_paths.copy(),
            self._identities.copy(),
            self._removed_files.copy(),
            self._planned_destinations.copy(),
        )

    def restore(self, snapshot: tuple[dict, dict, dict, set, dict]) -> None:
        """Restore a state previously returned by :meth:`snapshot`."""
        (
            self._virtual_files,
            self._virtual_paths,
            self._identities,
            self._removed_files,
            self._planned_destinations,
        ) = snapshot

    def directory_exists(self, directory: Path) -> bool:
        """Return whether a real or planned directory is available."""
        directory = self._normalize(directory)
        if directory.is_dir():
            return True
        directory_key = self._path_key(directory)
        return any(
            directory_key == path_key.parent or directory_key in path_key.parents
            for path_key in self._virtual_files
        )

    def backing_path(self, path: Path) -> Path:
        """Return the real file used to read metadata for a planned path."""
        path = self._normalize(path)
        return self._virtual_files.get(self._path_key(path), path)

    def identity(self, path: Path) -> Hashable:
        """Return the logical file identity used for first-match handling."""
        path = self._normalize(path)
        key = self._path_key(path)
        return self._identities.get(key, key)

    def active_disk_files(self, files: Iterable[Path]) -> list[Path]:
        """Remove files hidden by earlier planned move/delete operations."""
        active = []
        seen = set()
        for path in files:
            normalized = self._normalize(path)
            key = self._path_key(normalized)
            if key in seen or not self.is_file(normalized):
                continue
            seen.add(key)
            active.append(normalized)
        return active

    def matching_virtual_files(
        self,
        directory: Path,
        pattern: str,
        recursive: bool,
    ) -> list[Path]:
        """Return virtual files matching the same rules as glob/rglob."""
        directory = self._normalize(directory)
        directory_key = self._path_key(directory)
        matched = []

        case_insensitive, separators = platform_glob_rules()
        matcher = _compile_glob(pattern, recursive, case_insensitive, separators)

        for path_key, path in self._virtual_paths.items():
            try:
                relative_key = path_key.relative_to(directory_key)
            except ValueError:
                continue

            # 走査対象ディレクトリ自身と同じパスならファイルではない。
            # ここで弾かないと parts[-0:] がパス全体になって切り出しが壊れる。
            if not relative_key.parts:
                continue

            relative = Path(*path.parts[-len(relative_key.parts):])
            if recursive and self._has_symlinked_parent(directory, relative):
                continue
            if matcher.match(relative.as_posix()):
                matched.append(path)

        return matched

    @staticmethod
    def _has_symlinked_parent(directory: Path, relative_path: Path) -> bool:
        """Return whether an intermediate component is a directory symlink."""
        current = directory
        for part in relative_path.parts[:-1]:
            current = current / part
            if current.is_symlink():
                return True
        return False

    def apply_operations(self, operations: Iterable[FileOperation]) -> None:
        """Advance the planned state by applying operations in order."""
        for operation in operations:
            self.apply_operation(operation)

    def apply_operation(self, operation: FileOperation) -> None:
        """Advance the planned state by one operation without disk writes."""
        displayed_source = Path(operation.source)
        source = self._normalize(displayed_source)
        backing = self.backing_path(source)
        identity = self.identity(source)
        destination = resolve_destination(operation)

        if operation.action == 'delete':
            self._remove(source)
            return

        if destination is None:
            raise ValueError(
                f"{operation.action} には destination が必要です: {source}"
            )

        displayed_destination = Path(destination)
        destination = self._normalize(displayed_destination)
        destination_key = self._path_key(destination)
        first_source = self._planned_destinations.get(destination_key)
        if first_source is not None:
            raise PlanningConflictError(
                first_source,
                displayed_source,
                displayed_destination,
            )

        if operation.action == 'copy':
            self._add(destination, backing, displayed_source, object())
            return

        if operation.action in {'move', 'cleanup', 'rename'}:
            self._remove(source)
            self._add(destination, backing, displayed_source, identity)
            return

        raise ValueError(f"未対応のファイル操作です: {operation.action}")

    def _remove(self, path: Path) -> None:
        path = self._normalize(path)
        key = self._path_key(path)
        self._virtual_files.pop(key, None)
        self._virtual_paths.pop(key, None)
        self._identities.pop(key, None)
        self._planned_destinations.pop(key, None)
        self._removed_files.add(key)

    def _add(
        self,
        path: Path,
        backing: Path,
        source: Path,
        identity: Hashable,
    ) -> None:
        path = self._normalize(path)
        key = self._path_key(path)
        self._removed_files.discard(key)
        self._virtual_files[key] = self._normalize(backing)
        self._virtual_paths[key] = path
        self._identities[key] = identity
        self._planned_destinations[key] = Path(source)
