# -*- coding: utf-8 -*-
"""
ファイル操作用のユーティリティ関数
"""

import os
import re
import logging
from typing import List


def parse_file_size(size_str: str) -> int:
    """
    ファイルサイズ文字列をバイト数に変換

    Args:
        size_str: サイズ文字列（例: "10MB", "1.5GB", "1024"）

    Returns:
        バイト数
    """
    if isinstance(size_str, int):
        return size_str

    size_str = str(size_str).strip().upper()

    # 単位の抽出
    units = {
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3,
        'TB': 1024 ** 4,
    }

    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            number_part = size_str[:-len(unit)].strip()
            try:
                return int(float(number_part) * multiplier)
            except ValueError:
                raise ValueError(f"不正なサイズ形式: {size_str}")

    # 単位なし（バイト数と解釈）
    try:
        return int(size_str)
    except ValueError:
        raise ValueError(f"不正なサイズ形式: {size_str}")


def format_file_size(size_bytes: int) -> str:
    """
    バイト数を人間が読みやすい形式に変換

    Args:
        size_bytes: バイト数

    Returns:
        フォーマット済み文字列（例: "10.5 MB"）
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def clean_filename(filename: str, custom_patterns: List[str] = None) -> str:
    """
    ファイル名から絵文字や特殊文字を除去

    Args:
        filename: 元のファイル名
        custom_patterns: カスタム除去パターン（正規表現）

    Returns:
        クリーンアップ済みファイル名
    """
    # 拡張子を分離
    name_part, ext_part = os.path.splitext(filename)

    # デフォルトパターン: 絵文字、特殊記号の除去
    # 基本的な絵文字範囲（Unicode範囲）
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # 顔文字
        "\U0001F300-\U0001F5FF"  # シンボル＆絵文字
        "\U0001F680-\U0001F6FF"  # 乗り物＆地図シンボル
        "\U0001F1E0-\U0001F1FF"  # 国旗
        "\U00002702-\U000027B0"  # 装飾記号
        "\U0001F200-\U0001F251"  # 囲み文字（修正: U+1F200～、日本語を除外）
        "]+",
        flags=re.UNICODE
    )
    name_part = emoji_pattern.sub('', name_part)

    # カスタムパターンの適用
    if custom_patterns:
        for pattern in custom_patterns:
            try:
                name_part = re.sub(pattern, '', name_part)
            except re.error as e:
                logging.warning(f"不正な正規表現パターン '{pattern}': {e}")

    # 連続する空白を1つに統合
    name_part = re.sub(r'\s+', ' ', name_part)

    # 前後の空白を削除（拡張子の前のスペースも含む）
    name_part = name_part.strip()

    # 空文字列になった場合のフォールバック
    if not name_part:
        name_part = "cleaned_file"

    return name_part + ext_part
