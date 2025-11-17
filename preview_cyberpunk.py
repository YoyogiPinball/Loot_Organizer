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
# B案: Night City風（Cyberpunk 2077 UI準拠）
# ==========================================
class NightCity:
    """B案: Cyberpunk 2077 UI準拠（イエロー中心×シアンアクセント）"""
    # メインカラー（CP2077準拠）
    NEON_YELLOW = Fore.YELLOW + Style.BRIGHT      # 主役カラー（選択、ハイライト）
    NEON_CYAN = Fore.CYAN + Style.BRIGHT          # セカンダリカラー（情報表示）
    NEON_WHITE = Fore.WHITE + Style.BRIGHT        # テキスト
    NEON_RED = Fore.RED + Style.BRIGHT            # エラー、警告
    NEON_GREEN = Fore.GREEN + Style.BRIGHT        # 成功
    NEON_MAGENTA = Fore.MAGENTA + Style.BRIGHT    # 控えめアクセント
    NEON_BLUE = Fore.BLUE + Style.BRIGHT

    # 通常カラー
    CYAN = Fore.CYAN
    YELLOW = Fore.YELLOW
    WHITE = Fore.WHITE
    RED = Fore.RED
    GREEN = Fore.GREEN
    MAGENTA = Fore.MAGENTA
    BLUE = Fore.BLUE

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
    """レベル2: ネオンボーダー（Cyberpunk 2077風 - 1行1色）"""
    if theme_name == "A案":
        header_color = colors.NEON_MAGENTA
        text_color = colors.NEON_CYAN
        item_color = colors.NEON_YELLOW
    elif theme_name == "B案":  # Cyberpunk 2077準拠
        header_color = colors.NEON_YELLOW      # イエローを主役に
        text_color = colors.NEON_CYAN          # シアンで情報表示
        item_color = colors.NEON_YELLOW        # 選択項目はイエロー
    else:  # C案
        header_color = colors.NEON_CYAN
        text_color = colors.NEON_BLUE
        item_color = colors.NEON_YELLOW

    print(f"\n{header_color}╔{'═' * 46}╗{colors.RESET}")
    print(f"{text_color}║  🌆 LOOT ORGANIZER v2077                    ║{colors.RESET}")
    print(f"{header_color}║  ▓▒░ {theme_name} THEME ░▒▓{' ' * (30 - len(theme_name))}║{colors.RESET}")
    print(f"{header_color}╠{'═' * 46}╣{colors.RESET}")
    print(f"{colors.CYAN}║                                              ║{colors.RESET}")
    print(f"{item_color}║  ▶ 📤 ダウンロード振り分け [Sort]           ║{colors.RESET}")
    print(f"{colors.CYAN}║    ✨ ファイルクリーンアップ [Clean]        ║{colors.RESET}")
    print(f"{colors.CYAN}║    🔄 連続実行モード                        ║{colors.RESET}")
    print(f"{colors.CYAN}║                                              ║{colors.RESET}")
    print(f"{header_color}╚{'═' * 46}╝{colors.RESET}\n")


def show_level2_success(colors, theme_name):
    """レベル2: 成功メッセージ（Cyberpunk 2077風 - 1行1色）"""
    if theme_name == "B案":  # Cyberpunk 2077準拠
        border_color = colors.NEON_YELLOW
        accent = colors.NEON_YELLOW
        success_color = colors.NEON_CYAN
    else:
        border_color = colors.NEON_CYAN
        accent = colors.NEON_GREEN
        success_color = colors.NEON_GREEN

    print(f"{border_color}╔{'═' * 46}╗{colors.RESET}")
    print(f"{accent}║  ⚡ 処理完了 - UPLOAD SUCCESSFUL              ║{colors.RESET}")
    print(f"{border_color}╠{'═' * 46}╣{colors.RESET}")
    print(f"{success_color}║  ⚡ 完了: 23件成功                            ║{colors.RESET}")
    print(f"{colors.CYAN}║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━║{colors.RESET}")
    print(f"{colors.CYAN}║  📊 ログ: logs/2025-11-17.log                ║{colors.RESET}")
    print(f"{border_color}╚{'═' * 46}╝{colors.RESET}\n")


def show_level2_error(colors, theme_name):
    """レベル2: エラーメッセージ（1行1色）"""
    print(f"{colors.NEON_RED}╔{'═' * 46}╗{colors.RESET}")
    print(f"{colors.NEON_RED}║  🔥 ERROR - SYSTEM MALFUNCTION               ║{colors.RESET}")
    print(f"{colors.NEON_RED}╠{'═' * 46}╣{colors.RESET}")
    print(f"{colors.RED}║  エラー: ファイルが見つかりません            ║{colors.RESET}")
    print(f"{colors.RED}║  >> C:\\invalid\\path\\file.txt                 ║{colors.RESET}")
    print(f"{colors.NEON_RED}╚{'═' * 46}╝{colors.RESET}\n")


# ==========================================
# レベル3: ASCIIアート + ネオン強調（グリッチなし）
# ==========================================
def show_level3_menu(colors, theme_name):
    """レベル3: ASCIIアート + メッセージ（Cyberpunk 2077風 - グリッチなし）"""
    if theme_name == "A案":
        art_color = colors.NEON_MAGENTA
        header_color = colors.NEON_CYAN
        item_color = colors.NEON_YELLOW
    elif theme_name == "B案":  # Cyberpunk 2077準拠
        art_color = colors.NEON_YELLOW         # ASCIIアートをイエローで
        header_color = colors.NEON_YELLOW      # ボーダーもイエロー
        item_color = colors.NEON_YELLOW        # 選択項目もイエロー
    else:  # C案
        art_color = colors.NEON_CYAN
        header_color = colors.NEON_BLUE
        item_color = colors.NEON_YELLOW

    # ASCIIアート風タイトル（統一カラー - 見やすい）
    print(f"\n{art_color}{'▄' * 48}{colors.RESET}")
    print(f"{art_color}{'█' * 48}{colors.RESET}")
    print(f"{art_color}  ██╗      ██████╗  ██████╗ ████████╗{colors.RESET}")
    print(f"{art_color}  ██║     ██╔═══██╗██╔═══██╗╚══██╔══╝{colors.RESET}")
    print(f"{art_color}  ██║     ██║   ██║██║   ██║   ██║   {colors.RESET}")
    print(f"{art_color}  ██║     ██║   ██║██║   ██║   ██║   {colors.RESET}")
    print(f"{art_color}  ███████╗╚██████╔╝╚██████╔╝   ██║   {colors.RESET}")
    print(f"{art_color}  ╚══════╝ ╚═════╝  ╚═════╝    ╚═╝   {colors.RESET}")
    print(f"{art_color}{'█' * 48}{colors.RESET}")
    print(f"{art_color}{'▀' * 48}{colors.RESET}")

    # メニュー部分（読みやすく1行1色）
    print(f"\n{header_color}╔{'═' * 46}╗{colors.RESET}")
    print(f"{header_color}║  ORGANIZER v2077 - {theme_name}{' ' * (24 - len(theme_name))}║{colors.RESET}")
    print(f"{header_color}╠{'═' * 46}╣{colors.RESET}")
    print(f"{item_color}║  ▶ 📤 ダウンロード振り分け                   ║{colors.RESET}")
    print(f"{colors.CYAN}║    ✨ ファイルクリーンアップ                 ║{colors.RESET}")
    print(f"{colors.CYAN}║    🔄 連続実行モード                         ║{colors.RESET}")
    print(f"{header_color}╚{'═' * 46}╝{colors.RESET}\n")


def show_level3_success(colors, theme_name):
    """レベル3: 成功メッセージ（Cyberpunk 2077風 - 1行1色）"""
    if theme_name == "B案":  # Cyberpunk 2077準拠
        border_color = colors.NEON_YELLOW
        success_color = colors.NEON_CYAN
    else:
        border_color = colors.NEON_GREEN
        success_color = colors.NEON_YELLOW

    print(f"{border_color}{'▓' * 48}{colors.RESET}")
    print(f"{success_color}>>> UPLOAD SUCCESSFUL <<<{colors.RESET}")
    print(f"{border_color}⚡ 完了: 23件{colors.RESET}")
    print(f"{border_color}{'▓' * 48}{colors.RESET}\n")


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
        "B": ("B案: Cyberpunk 2077 UI", NightCity),
        "C": ("C案: Corpo風", Corpo)
    }

    print("\n" + "=" * 50)
    print("🌃 Cyberpunk 2077風カラーリング プレビュー")
    print("=" * 50)
    print("\n【テーマ選択】")
    print("A: クラシックサイバーパンク（定番カラー）")
    print("B: Cyberpunk 2077 UI（イエロー中心×シアンアクセント）")
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
