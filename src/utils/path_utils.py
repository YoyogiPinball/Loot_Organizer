# -*- coding: utf-8 -*-
"""
Path normalization helpers.
"""

import os
import re
from pathlib import Path
from typing import Iterable


_WINDOWS_DRIVE_RE = re.compile(r"^([A-Za-z]):[\\/](.*)$")
_WSL_UNC_RE = re.compile(
    r"^[\\/]{2}(?:wsl\.localhost|wsl\$)[\\/]([^\\/]+)(?:[\\/](.*))?$",
    re.IGNORECASE,
)


def to_path(path_value) -> Path:
    """
    Convert a configured path to pathlib.Path.

    On Linux/WSL, Windows drive paths like ``D:\\foo`` are mapped to
    ``/mnt/d/foo`` so the same YAML can be used from Windows and WSL.
    """
    path_str = str(path_value)
    unc_match = _WSL_UNC_RE.match(path_str)
    drive_match = _WINDOWS_DRIVE_RE.match(path_str)
    if os.name != "nt" and unc_match:
        distro, rest = unc_match.groups()
        local_distro = os.environ.get("WSL_DISTRO_NAME")
        # Windows は UNC を大文字小文字の区別なく解決するので、エクスプローラーから
        # コピーしたパスの distro 名が WSL_DISTRO_NAME と綴り違いになることがある。
        # ここで厳密比較すると、正しいパスまで設定エラーとして弾いてしまう。
        if local_distro is None or local_distro.casefold() != distro.casefold():
            local_value = local_distro if local_distro is not None else "未設定"
            raise ValueError(
                "UNC パスには別のディストリビューション名が指定されているため"
                f"変換できません: 指定={distro}, WSL_DISTRO_NAME={local_value}"
            )
        rest_parts = [
            part for part in re.split(r"[\\/]+", rest or "") if part
        ]
        path = Path("/") / Path(*rest_parts)
    elif os.name != "nt" and re.match(r"^[\\/]{2}", path_str):
        raise ValueError(
            "WSL からはネットワーク共有パスを解決できません: "
            f"{path_str}"
        )
    elif os.name == "nt" and re.match(r"^[\\/](?![\\/])", path_str):
        # Windows では先頭の / は「現在のドライブのルート」を指すので、
        # /mnt/d/x のような WSL 形式のパスが黙って C:\mnt\d\x になる。
        # 保存先なら別の場所へ作られ、走査元ならエラーも出ず対象0件で終わる。
        raise ValueError(
            "Windows からは Linux 形式の絶対パスを解決できません: "
            f"{path_str}（D:\\Foo\\Bar のようにドライブ文字で書いてください）"
        )
    elif os.name != "nt" and drive_match:
        drive, rest = drive_match.groups()
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
