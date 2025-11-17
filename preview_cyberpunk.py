#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cyberpunk 2077風カラーリング プレビュー - 全パターン対応
A案: クラシックサイバーパンク
B案: Night City風
C案: Corpo風

レベル1: カラースキームのみ
レベル2: カラー + ネオンボーダー
レベル3: グリッチエフェクト + ASCIIアート
"""

import random
from colorama import init, Fore, Back, Style

# colorama初期化
init(autoreset=True)


# ==========================================
# A案: クラシックサイバーパンク
# ==========================================
class ClassicCyberpunk:
    """A案: クラシックサイバーパンク（定番カラー）"""
    # ネオンカラー
    NEON_CYAN = Fore.CYAN + Style.BRIGHT
    NEON_MAGENTA = Fore.MAGENTA + Style.BRIGHT
    NEON_YELLOW = Fore.YELLOW + Style.BRIGHT
    NEON_GREEN = Fore.GREEN + Style.BRIGHT
    NEON_RED = Fore.RED + Style.BRIGHT

    # 通常カラー
    CYAN = Fore.CYAN
    MAGENTA = Fore.MAGENTA
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    RED = Fore.RED

    # 背景
    BG_BLACK = Back.BLACK

    # リセット
    RESET = Style.RESET_ALL


# ==========================================
# B案: Night City風
# ==========================================
class NightCity:
    """B案: Night City風（マゼンタ×シアン×イエロー）"""
    # ネオンカラー
    NEON_CYAN = Fore.CYAN + Style.BRIGHT
    NEON_MAGENTA = Fore.MAGENTA + Style.BRIGHT
    NEON_YELLOW = Fore.YELLOW + Style.BRIGHT
    NEON_GREEN = Fore.GREEN + Style.BRIGHT
    NEON_RED = Fore.RED + Style.BRIGHT

    # 通常カラー
    CYAN = Fore.CYAN
    BLUE = Fore.BLUE
    RED = Fore.RED

    # 背景
    BG_BLACK = Back.BLACK

    # リセット
    RESET = Style.RESET_ALL


# ==========================================
# C案: Corpo風
# ==========================================
class Corpo:
    """C案: Corpo風（企業テーマ - シアン×ブルー）"""
    # ネオンカラー
    NEON_CYAN = Fore.CYAN + Style.BRIGHT
    NEON_BLUE = Fore.BLUE + Style.BRIGHT
    NEON_YELLOW = Fore.YELLOW + Style.BRIGHT
    NEON_WHITE = Fore.WHITE + Style.BRIGHT
    NEON_RED = Fore.RED + Style.BRIGHT

    # 通常カラー
    CYAN = Fore.CYAN
    BLUE = Fore.BLUE
    WHITE = Fore.WHITE
    YELLOW = Fore.YELLOW
    RED = Fore.RED

    # 背景
    BG_BLACK = Back.BLACK
    BG_BLUE = Back.BLUE

    # リセット
    RESET = Style.RESET_ALL


# ==========================================
# レベル1: カラースキームのみ
# ==========================================
def show_level1_menu(colors, theme_name):
    """レベル1: シンプルなカラー適用"""
    print(f"\n{colors.CYAN}╔{'═' * 46}╗")
    print(f"║  📁 Loot Organizer                          ║")
    print(f"╠{'═' * 46}╣{colors.RESET}")
    print(f"{colors.CYAN}║{' ' * 46}║")
    print(f"{colors.CYAN}║  ▶ 📤 ダウンロード振り分け [Sort]{' ' * 11}{colors.CYAN}║")
    print(f"{colors.CYAN}║    ✨ ファイルクリーンアップ [Clean]{' ' * 8}{colors.CYAN}║")
    print(f"{colors.CYAN}║{' ' * 46}║")
    print(f"{colors.CYAN}╚{'═' * 46}╝{colors.RESET}\n")


def show_level1_success(colors):
    """レベル1: 成功メッセージ"""
    print(f"{colors.GREEN}✓ 完了: 23件成功{colors.RESET}")
    print(f"{colors.CYAN}━{'━' * 44}{colors.RESET}\n")


def show_level1_error(colors):
    """レベル1: エラーメッセージ"""
    print(f"{colors.RED}✗ エラー: ファイルが見つかりません{colors.RESET}")
    print(f"{colors.RED}>> C:\\invalid\\path\\file.txt{colors.RESET}\n")


# ==========================================
# レベル2: ネオンボーダー
# ==========================================
def show_level2_menu(colors, theme_name):
    """レベル2: ネオンボーダー + グラデーション"""
    if theme_name == "A案":
        header_color = colors.NEON_MAGENTA
        border_color = colors.NEON_CYAN
        accent_color = colors.NEON_YELLOW
    elif theme_name == "B案":
        header_color = colors.NEON_MAGENTA
        border_color = colors.CYAN
        accent_color = colors.NEON_YELLOW
    else:  # C案
        header_color = colors.NEON_CYAN
        border_color = colors.BLUE
        accent_color = colors.NEON_YELLOW

    print(f"\n{header_color}╔{'═' * 46}╗")
    print(f"║ {colors.NEON_CYAN}🌆 LOOT ORGANIZER v2077{' ' * 21}{header_color}║")
    print(f"║ {accent_color}▓▒░ {theme_name} THEME ░▒▓{' ' * (30 - len(theme_name))}{header_color}║")
    print(f"{border_color}╠{'═' * 46}╣{colors.RESET}")
    print(f"{border_color}║{' ' * 46}║")
    print(f"{border_color}║  {colors.NEON_MAGENTA if theme_name != 'C案' else colors.NEON_BLUE}▶ {colors.RESET}📤 ダウンロード振り分け [Sort]{' ' * 11}{border_color}║")
    print(f"{border_color}║    ✨ ファイルクリーンアップ [Clean]{' ' * 8}{border_color}║")
    print(f"{border_color}║    🔄 連続実行モード{' ' * 24}{border_color}║")
    print(f"{border_color}║{' ' * 46}║")
    print(f"{header_color}╚{'═' * 46}╝{colors.RESET}\n")


def show_level2_success(colors, theme_name):
    """レベル2: 成功メッセージ"""
    if theme_name == "B案":
        accent = colors.NEON_YELLOW
    else:
        accent = colors.NEON_GREEN

    print(f"{colors.NEON_CYAN}╔{'═' * 46}╗")
    print(f"║ {accent}⚡ 処理完了 - UPLOAD SUCCESSFUL{' ' * 14}{colors.NEON_CYAN}║")
    print(f"╠{'═' * 46}╣{colors.RESET}")
    print(f"{colors.CYAN}║  {colors.NEON_GREEN}⚡ 完了: 23件成功{' ' * 30}{colors.CYAN}║")
    print(f"{colors.CYAN}╚{'═' * 46}╝{colors.RESET}\n")


def show_level2_error(colors, theme_name):
    """レベル2: エラーメッセージ"""
    print(f"{colors.NEON_RED}╔{'═' * 46}╗")
    print(f"║ {colors.NEON_RED}{colors.BG_BLACK}🔥 ERROR - SYSTEM MALFUNCTION{' ' * 16}{colors.RESET}{colors.NEON_RED}║")
    print(f"╠{'═' * 46}╣{colors.RESET}")
    print(f"{colors.RED}║  🔥 エラー: ファイルが見つかりません{' ' * 8}{colors.RED}║")
    print(f"║  >> C:\\invalid\\path\\file.txt{' ' * 17}{colors.RED}║")
    print(f"╚{'═' * 46}╝{colors.RESET}\n")


# ==========================================
# レベル3: グリッチエフェクト
# ==========================================
def glitch_text(text, colors):
    """グリッチエフェクト: ランダムカラー"""
    color_list = [colors.NEON_CYAN, colors.NEON_MAGENTA, colors.NEON_YELLOW]
    return ''.join(random.choice(color_list) + c for c in text) + colors.RESET


def show_level3_menu(colors, theme_name):
    """レベル3: グリッチエフェクト + ASCIIアート"""
    if theme_name == "A案":
        header_color = colors.NEON_MAGENTA
        border_color = colors.NEON_CYAN
    elif theme_name == "B案":
        header_color = colors.NEON_MAGENTA
        border_color = colors.CYAN
    else:  # C案
        header_color = colors.NEON_CYAN
        border_color = colors.BLUE

    # ASCIIアート風タイトル
    print(f"\n{colors.NEON_CYAN}{'▄' * 48}")
    print(f"{colors.NEON_MAGENTA}{'█' * 48}")
    print(f"{colors.NEON_YELLOW}  ██╗      ██████╗  ██████╗ ████████╗")
    print(f"  ██║     ██╔═══██╗██╔═══██╗╚══██╔══╝")
    print(f"  ██║     ██║   ██║██║   ██║   ██║   ")
    print(f"  ██║     ██║   ██║██║   ██║   ██║   ")
    print(f"  ███████╗╚██████╔╝╚██████╔╝   ██║   ")
    print(f"  ╚══════╝ ╚═════╝  ╚═════╝    ╚═╝   ")
    print(f"{colors.NEON_MAGENTA}{'█' * 48}")
    print(f"{colors.NEON_CYAN}{'▀' * 48}{colors.RESET}")

    print(f"\n{header_color}╔{'═' * 46}╗")
    print(f"║ {glitch_text('ORGANIZER v2077', colors)}{' ' * 30}{header_color}║")
    print(f"{border_color}╠{'═' * 46}╣{colors.RESET}")
    print(f"{border_color}║  ▶ 📤 ダウンロード振り分け{' ' * 20}{border_color}║")
    print(f"{border_color}║    ✨ ファイルクリーンアップ{' ' * 18}{border_color}║")
    print(f"{border_color}╚{'═' * 46}╝{colors.RESET}\n")


def show_level3_success(colors, theme_name):
    """レベル3: グリッチ風成功メッセージ"""
    print(f"{colors.NEON_GREEN}{'▓' * 48}")
    print(f"{glitch_text('>>> UPLOAD SUCCESSFUL <<<', colors)}")
    print(f"{colors.NEON_GREEN}⚡ 完了: 23件{colors.RESET}")
    print(f"{colors.NEON_GREEN}{'▓' * 48}{colors.RESET}\n")


def show_level3_error(colors, theme_name):
    """レベル3: グリッチ風エラーメッセージ"""
    print(f"{colors.NEON_RED}{colors.BG_BLACK}{'█' * 48}")
    print(f"{glitch_text('!!! SYSTEM ERROR !!!', colors)}")
    print(f"{colors.NEON_RED}🔥 MALFUNCTION DETECTED{colors.RESET}")
    print(f"{colors.NEON_RED}{colors.BG_BLACK}{'█' * 48}{colors.RESET}\n")


# ==========================================
# メイン処理
# ==========================================
def show_pattern(theme_name, colors, level):
    """指定されたパターンを表示"""
    print("\n" + "=" * 50)
    print(f"【{theme_name} - レベル{level}】")
    print("=" * 50)

    if level == 1:
        print("\n--- メインメニュー ---")
        show_level1_menu(colors, theme_name)
        print("\n--- 成功メッセージ ---")
        show_level1_success(colors)
        print("\n--- エラーメッセージ ---")
        show_level1_error(colors)

    elif level == 2:
        print("\n--- メインメニュー ---")
        show_level2_menu(colors, theme_name)
        print("\n--- 成功メッセージ ---")
        show_level2_success(colors, theme_name)
        print("\n--- エラーメッセージ ---")
        show_level2_error(colors, theme_name)

    elif level == 3:
        print("\n--- メインメニュー ---")
        show_level3_menu(colors, theme_name)
        print("\n--- 成功メッセージ ---")
        show_level3_success(colors, theme_name)
        print("\n--- エラーメッセージ ---")
        show_level3_error(colors, theme_name)


def main():
    """メイン処理"""
    themes = {
        "A": ("A案: クラシックサイバーパンク", ClassicCyberpunk),
        "B": ("B案: Night City風", NightCity),
        "C": ("C案: Corpo風", Corpo)
    }

    print("\n" + "=" * 50)
    print("🌃 Cyberpunk 2077風カラーリング プレビュー")
    print("=" * 50)
    print("\n【テーマ選択】")
    print("A: クラシックサイバーパンク（定番カラー）")
    print("B: Night City風（マゼンタ×シアン×イエロー）")
    print("C: Corpo風（企業テーマ - シアン×ブルー）")
    print("ALL: 全パターン表示")
    print("Q: 終了")

    choice = input("\n選択 (A/B/C/ALL/Q): ").strip().upper()

    if choice == "Q":
        print("終了します")
        return

    if choice == "ALL":
        # 全パターン表示
        for theme_key, (theme_name, theme_colors) in themes.items():
            for level in [1, 2, 3]:
                show_pattern(theme_name, theme_colors, level)
                input("\n[Enter]キーで次へ...")

    elif choice in themes:
        theme_name, theme_colors = themes[choice]

        print("\n【レベル選択】")
        print("1: カラースキームのみ（シンプル）")
        print("2: カラー + ネオンボーダー（推奨）")
        print("3: グリッチエフェクト + ASCIIアート（派手）")
        print("ALL: 全レベル表示")

        level_choice = input("\n選択 (1/2/3/ALL): ").strip()

        if level_choice == "ALL":
            for level in [1, 2, 3]:
                show_pattern(theme_name, theme_colors, level)
                input("\n[Enter]キーで次へ...")
        elif level_choice in ["1", "2", "3"]:
            show_pattern(theme_name, theme_colors, int(level_choice))
        else:
            print("無効な選択です")

    else:
        print("無効な選択です")

    print("\n" + "=" * 50)
    print("プレビュー終了")
    print("=" * 50)


if __name__ == "__main__":
    main()
