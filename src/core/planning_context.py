# -*- coding: utf-8 -*-
"""In-memory file-system state used while planning dependent operations."""

from pathlib import Path
from typing import Iterable

from .preview_generator import FileOperation
from ..utils.file_executor import resolve_destination


class PlanningContext:
    """
    Track the paths that will exist after each planned operation.

    The real file system is never changed during planning.  A virtual path maps
    back to the real file that supplies its metadata, allowing later pipeline
    steps to scan renamed, moved, or copied files before execution starts.
    """

    def __init__(self):
        self._virtual_files: dict[Path, Path] = {}
        self._removed_files: set[Path] = set()

    def is_file(self, path: Path) -> bool:
        """Return whether ``path`` exists in the planned state."""
        path = Path(path)
        if path in self._virtual_files:
            return True
        if path in self._removed_files:
            return False
        return path.is_file()

    def directory_exists(self, directory: Path) -> bool:
        """Return whether a real or planned directory is available."""
        directory = Path(directory)
        if directory.is_dir():
            return True
        return any(directory == path.parent or directory in path.parents
                   for path in self._virtual_files)

    def backing_path(self, path: Path) -> Path:
        """Return the real file used to read metadata for a planned path."""
        path = Path(path)
        return self._virtual_files.get(path, path)

    def active_disk_files(self, files: Iterable[Path]) -> list[Path]:
        """Remove files hidden by earlier planned move/delete operations."""
        return [Path(path) for path in files if self.is_file(Path(path))]

    def matching_virtual_files(
        self,
        directory: Path,
        pattern: str,
        recursive: bool,
    ) -> list[Path]:
        """Return virtual files matching the same rules as glob/rglob."""
        directory = Path(directory)
        matched = []

        for path in self._virtual_files:
            try:
                relative = path.relative_to(directory)
            except ValueError:
                continue

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
        source = Path(operation.source)
        backing = self.backing_path(source)
        destination = resolve_destination(operation)

        if operation.action == 'delete':
            self._remove(source)
            return

        if destination is None:
            raise ValueError(
                f"{operation.action} には destination が必要です: {source}"
            )

        destination = Path(destination)
        if operation.action == 'copy':
            self._add(destination, backing)
            return

        if operation.action in {'move', 'cleanup', 'rename'}:
            self._remove(source)
            self._add(destination, backing)
            return

        raise ValueError(f"未対応のファイル操作です: {operation.action}")

    def _remove(self, path: Path) -> None:
        self._virtual_files.pop(path, None)
        self._removed_files.add(path)

    def _add(self, path: Path, backing: Path) -> None:
        self._removed_files.discard(path)
        self._virtual_files[path] = backing
