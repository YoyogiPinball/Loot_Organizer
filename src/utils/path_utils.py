# -*- coding: utf-8 -*-
"""
Path normalization helpers.
"""

import os
import re
from pathlib import Path
from typing import Iterable


_WINDOWS_DRIVE_RE = re.compile(r"^([A-Za-z]):[\\/](.*)$")


def to_path(path_value) -> Path:
    """
    Convert a configured path to pathlib.Path.

    On Linux/WSL, Windows drive paths like ``D:\\foo`` are mapped to
    ``/mnt/d/foo`` so the same YAML can be used from Windows and WSL.
    """
    path_str = str(path_value)
    match = _WINDOWS_DRIVE_RE.match(path_str)
    if os.name != "nt" and match:
        drive, rest = match.groups()
        rest_parts = [part for part in re.split(r"[\\/]+", rest) if part]
        path = Path("/mnt") / drive.lower() / Path(*rest_parts)
    else:
        path = Path(path_str)

    # 保存先が未作成でも扱えるよう、実在確認やシンボリックリンク解決は行わず
    # 相対パスと ``..`` だけを字句的に正規化する。
    return Path(os.path.abspath(os.path.normpath(path)))


def to_paths(path_values) -> list[Path]:
    """Normalize a single path or iterable of paths."""
    if isinstance(path_values, (str, os.PathLike)):
        return [to_path(path_values)]
    if isinstance(path_values, Iterable):
        return [to_path(value) for value in path_values]
    return [to_path(path_values)]
