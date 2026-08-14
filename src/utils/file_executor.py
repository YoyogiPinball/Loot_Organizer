# -*- coding: utf-8 -*-
"""
Shared file operation executor.
"""

import shutil
from dataclasses import dataclass
from pathlib import Path

from send2trash import send2trash

from ..core.preview_generator import FileOperation, SourceFingerprint


class SourceChangedError(Exception):
    """計画後に source の状態が変化したときに送出する。"""

    def __init__(self, source: Path, detail: str = "指紋が一致しません"):
        self.source = Path(source)
        self.detail = detail
        super().__init__(
            f"{self.source}: 計画時から変更されているため操作しません（{detail}）"
        )


@dataclass(frozen=True)
class SkippedFileOperation:
    """失敗として扱わない実行時スキップ。"""

    reason: str


def resolve_destination(op: FileOperation) -> Path | None:
    """Return the final destination path stored in the operation."""
    if op.action == "delete":
        return None

    if op.destination is None:
        raise ValueError(f"{op.action} には destination が必要です: {op.source}")

    return op.destination


def _verify_source_fingerprint(op: FileOperation) -> None:
    """指紋がある操作だけ、現在の source と比較する。"""
    planned = op.source_fingerprint
    if planned is None:
        return

    try:
        current = SourceFingerprint.capture(Path(op.source))
    except OSError as exc:
        raise SourceChangedError(op.source, f"現在の状態を取得できません: {exc}") from exc

    if current is None:
        raise SourceChangedError(op.source, "ファイルが見つかりません")
    if current != planned:
        raise SourceChangedError(op.source)


def execute_file_op(op: FileOperation) -> Path | None | SkippedFileOperation:
    """
    Execute one file operation and return its final destination when applicable.
    """
    _verify_source_fingerprint(op)
    destination = resolve_destination(op)

    if op.action == "delete":
        if op.delete_mode == "trash":
            send2trash(str(op.source))
        elif op.delete_mode == "permanent":
            op.source.unlink()
        else:
            raise ValueError(
                f"delete_mode は trash または permanent を指定してください: "
                f"{op.delete_mode}"
            )
        return None

    if destination is None:
        raise ValueError(f"{op.action} には destination が必要です: {op.source}")

    if op.skip_if_exists and destination.exists():
        return SkippedFileOperation(
            f"実行直前に保存先が存在したためスキップしました: {destination}"
        )

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
        action = "ゴミ箱" if op.delete_mode == "trash" else "完全削除"
        return f"{prefix}[{action}] {op.source} ({op.reason})"
    return f"{prefix}[{op.action}] {op.source} -> {destination} ({op.reason})"


def skipped_operation_log_message(
    op: FileOperation,
    skipped: SkippedFileOperation,
) -> str:
    """実行時スキップの日本語ログを作る。"""
    return f"[スキップ] {op.source}: {skipped.reason}"
