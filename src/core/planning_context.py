# -*- coding: utf-8 -*-
"""In-memory file-system state used while planning dependent operations."""

from pathlib import Path
from typing import Hashable, Iterable

from .preview_generator import FileOperation
from ..utils.file_executor import resolve_destination
from ..utils.path_utils import to_path


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

        for path_key, path in self._virtual_paths.items():
            try:
                relative_key = path_key.relative_to(directory_key)
            except ValueError:
                continue

            relative = Path(*path.parts[-len(relative_key.parts):])
            if not recursive and relative.parent != Path('.'):
                continue
            if relative.match(pattern):
                matched.append(path)

        return matched

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
