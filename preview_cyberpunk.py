#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cyberpunk 2077風カラーリング プレビュー - 全パターン対応
A案: クラシックサイバーパンク
B案: Night City風
C案: Corpo風

レベル1: カラースキームのみ
レベル2: カラー + ネオンボーダー
レベル3: ASCIIアート + ネオン強調
"""

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
    NEON_BLUE = Fore.BLUE + Style.BRIGHT

    # 通常カラー
    CYAN = Fore.CYAN
    MAGENTA = Fore.MAGENTA
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    RED = Fore.RED
    BLUE = Fore.BLUE

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
    NEON_BLUE = Fore.BLUE + Style.BRIGHT

    # 通常カラー
    CYAN = Fore.CYAN
    BLUE = Fore.BLUE
    RED = Fore.RED
    MAGENTA = Fore.MAGENTA
    YELLOW = Fore.YELLOW
    GREEN = Fore.GREEN

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
    NEON_MAGENTA = Fore.MAGENTA + Style.BRIGHT
    NEON_GREEN = Fore.GREEN + Style.BRIGHT

    # 通常カラー
    CYAN = Fore.CYAN
    BLUE = Fore.BLUE
    WHITE = Fore.WHITE
    YELLOW = Fore.YELLOW
    RED = Fore.RED
    MAGENTA = Fore.MAGENTA
    GREEN = Fore.GREEN

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
    """レベル2: ネオンボーダー（1行1色）"""
    if theme_name == "A案":
        header_color = colors.NEON_MAGENTA
        text_color = colors.NEON_CYAN
        item_color = colors.NEON_YELLOW
    elif theme_name == "B案":
        header_color = colors.NEON_MAGENTA
        text_color = colors.NEON_CYAN
        item_color = colors.NEON_YELLOW
    else:  # C案
        header_color = colors.NEON_CYAN
        text_color = colors.NEON_BLUE
        item_color = colors.NEON_YELLOW

    print(f"\n{header_color}╔{'═' * 46}╗{colors.RESET}")
    print(f"{text_color}║  🌆 LOOT ORGANIZER v2077                    ║{colors.RESET}")
    print(f"{item_color}║  ▓▒░ {theme_name} THEME ░▒▓{' ' * (30 - len(theme_name))}║{colors.RESET}")
    print(f"{header_color}╠{'═' * 46}╣{colors.RESET}")
    print(f"{colors.CYAN}║                                              ║{colors.RESET}")
    print(f"{item_color}║  ▶ 📤 ダウンロード振り分け [Sort]           ║{colors.RESET}")
    print(f"{colors.CYAN}║    ✨ ファイルクリーンアップ [Clean]        ║{colors.RESET}")
    print(f"{colors.CYAN}║    🔄 連続実行モード                        ║{colors.RESET}")
    print(f"{colors.CYAN}║                                              ║{colors.RESET}")
    print(f"{header_color}╚{'═' * 46}╝{colors.RESET}\n")


def show_level2_success(colors, theme_name):
    """レベル2: 成功メッセージ（1行1色）"""
    if theme_name == "B案":
        accent = colors.NEON_YELLOW
    else:
        accent = colors.NEON_GREEN

    print(f"{colors.NEON_CYAN}╔{'═' * 46}╗{colors.RESET}")
    print(f"{accent}║  ⚡ 処理完了 - UPLOAD SUCCESSFUL              ║{colors.RESET}")
    print(f"{colors.NEON_CYAN}╠{'═' * 46}╣{colors.RESET}")
    print(f"{colors.NEON_GREEN}║  ⚡ 完了: 23件成功                            ║{colors.RESET}")
    print(f"{colors.CYAN}║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━║{colors.RESET}")
    print(f"{colors.CYAN}║  📊 ログ: logs/2025-11-17.log                ║{colors.RESET}")
    print(f"{colors.NEON_CYAN}╚{'═' * 46}╝{colors.RESET}\n")


def show_level2_error(colors, theme_name):
    """レベル2: エラーメッセージ（1行1色）"""
    print(f"{colors.NEON_RED}╔{'═' * 46}╗{colors.RESET}")
    print(f"{colors.NEON_RED}║  🔥 ERROR - SYSTEM MALFUNCTION               ║{colors.RESET}")
    print(f"{colors.NEON_RED}╠{'═' * 46}╣{colors.RESET}")
    print(f"{colors.RED}║  エラー: ファイルが見つかりません            ║{colors.RESET}")
    print(f"{colors.RED}║  >> C:\\invalid\\path\\file.txt                 ║{colors.RESET}")
    print(f"{colors.NEON_RED}╚{'═' * 46}╝{colors.RESET}\n")


# ==========================================
# レベル3: ASCIIアート（グリッチ） + ネオン強調
# ==========================================
def glitch_text(text, colors, chunk_size=4):
    """グリッチエフェクト: 装飾用（数文字単位でカラー変更 - Cyberpunk 2077風）"""
    import random
    color_list = [colors.NEON_CYAN, colors.NEON_MAGENTA, colors.NEON_YELLOW]
    result = []
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i+chunk_size]
        color = random.choice(color_list)
        result.append(color + chunk)
    return ''.join(result) + colors.RESET


def show_level3_menu(colors, theme_name):
    """レベル3: ASCIIアート（グリッチエフェクト） + メッセージ（1行1色）"""
    if theme_name == "A案":
        header_color = colors.NEON_CYAN
        item_color = colors.NEON_YELLOW
    elif theme_name == "B案":
        header_color = colors.NEON_MAGENTA
        item_color = colors.NEON_CYAN
    else:  # C案
        header_color = colors.NEON_BLUE
        item_color = colors.NEON_YELLOW

    # ASCIIアート風タイトル（グリッチエフェクト）
    art_line1 = "▄" * 48
    art_line2 = "█" * 48
    art_line3 = "  ██╗      ██████╗  ██████╗ ████████╗"
    art_line4 = "  ██║     ██╔═══██╗██╔═══██╗╚══██╔══╝"
    art_line5 = "  ██║     ██║   ██║██║   ██║   ██║   "
    art_line6 = "  ██║     ██║   ██║██║   ██║   ██║   "
    art_line7 = "  ███████╗╚██████╔╝╚██████╔╝   ██║   "
    art_line8 = "  ╚══════╝ ╚═════╝  ╚═════╝    ╚═╝   "
    art_line9 = "█" * 48
    art_line10 = "▀" * 48

    print(f"\n{glitch_text(art_line1, colors)}")
    print(f"{glitch_text(art_line2, colors)}")
    print(f"{glitch_text(art_line3, colors)}")
    print(f"{glitch_text(art_line4, colors)}")
    print(f"{glitch_text(art_line5, colors)}")
    print(f"{glitch_text(art_line6, colors)}")
    print(f"{glitch_text(art_line7, colors)}")
    print(f"{glitch_text(art_line8, colors)}")
    print(f"{glitch_text(art_line9, colors)}")
    print(f"{glitch_text(art_line10, colors)}")

    # メニュー部分（読みやすく1行1色）
    print(f"\n{header_color}╔{'═' * 46}╗{colors.RESET}")
    print(f"{header_color}║  ORGANIZER v2077 - {theme_name}{' ' * (24 - len(theme_name))}║{colors.RESET}")
    print(f"{header_color}╠{'═' * 46}╣{colors.RESET}")
    print(f"{item_color}║  ▶ 📤 ダウンロード振り分け                   ║{colors.RESET}")
    print(f"{colors.CYAN}║    ✨ ファイルクリーンアップ                 ║{colors.RESET}")
    print(f"{colors.CYAN}║    🔄 連続実行モード                         ║{colors.RESET}")
    print(f"{header_color}╚{'═' * 46}╝{colors.RESET}\n")


def show_level3_success(colors, theme_name):
    """レベル3: 成功メッセージ（1行1色）"""
    print(f"{colors.NEON_GREEN}{'▓' * 48}{colors.RESET}")
    print(f"{colors.NEON_YELLOW}>>> UPLOAD SUCCESSFUL <<<{colors.RESET}")
    print(f"{colors.NEON_GREEN}⚡ 完了: 23件{colors.RESET}")
    print(f"{colors.NEON_GREEN}{'▓' * 48}{colors.RESET}\n")


def show_level3_error(colors, theme_name):
    """レベル3: エラーメッセージ（1行1色）"""
    print(f"{colors.NEON_RED}{'█' * 48}{colors.RESET}")
    print(f"{colors.NEON_YELLOW}!!! SYSTEM ERROR !!!{colors.RESET}")
    print(f"{colors.NEON_RED}🔥 MALFUNCTION DETECTED{colors.RESET}")
    print(f"{colors.NEON_RED}{'█' * 48}{colors.RESET}\n")


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
