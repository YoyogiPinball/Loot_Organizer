# -*- coding: utf-8 -*-
"""
Shared file operation executor.
"""

import shutil
from pathlib import Path

from ..core.preview_generator import FileOperation


def resolve_destination(op: FileOperation) -> Path | None:
    """Return the final destination path stored in the operation."""
    if op.action == "delete":
        return None

    if op.destination is None:
        raise ValueError(f"{op.action} には destination が必要です: {op.source}")

    return op.destination


def execute_file_op(op: FileOperation) -> Path | None:
    """
    Execute one file operation and return its final destination when applicable.
    """
    destination = resolve_destination(op)

    if op.action == "delete":
        op.source.unlink()
        return None

    if destination is None:
        raise ValueError(f"{op.action} には destination が必要です: {op.source}")

    destination.parent.mkdir(parents=True, exist_ok=True)

    if op.action == "move":
        shutil.move(str(op.source), str(destination))
    elif op.action == "copy":
        shutil.copy2(str(op.source), str(destination))
    elif op.action in {"cleanup", "rename"}:
        op.source.rename(destination)
    else:
        raise ValueError(f"未対応のファイル操作です: {op.action}")

    return destination


def operation_log_message(op: FileOperation, dry_run: bool = False) -> str:
    """Build a compact log message for a file operation."""
    prefix = "[DRY-RUN] " if dry_run else ""
    destination = resolve_destination(op)
    if destination is None:
        return f"{prefix}[delete] {op.source} ({op.reason})"
    return f"{prefix}[{op.action}] {op.source} -> {destination} ({op.reason})"
