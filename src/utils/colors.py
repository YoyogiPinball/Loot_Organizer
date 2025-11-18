# -*- coding: utf-8 -*-
"""
カラーテーマ定義
Cyberpunk 2077風のカラースキーム
"""

from colorama import Fore, Style


class Colors:
    """カラーパレット - Corpo風（Cyberpunk風）"""

    # ネオンカラー
    NEON_CYAN = Fore.CYAN + Style.BRIGHT        # ボーダー、フレーム
    NEON_BLUE = Fore.BLUE + Style.BRIGHT        # タイトル、ヘッダー
    NEON_YELLOW = Fore.YELLOW + Style.BRIGHT    # 選択項目、ハイライト
    NEON_GREEN = Fore.GREEN + Style.BRIGHT      # 成功メッセージ
    NEON_RED = Fore.RED + Style.BRIGHT          # エラーメッセージ

    # 通常カラー
    CYAN = Fore.CYAN
    YELLOW = Fore.YELLOW

    # リセット
    RESET = Style.RESET_ALL
