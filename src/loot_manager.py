#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Loot Organizer - ファイル整理ツール
個人用ファイル整理ツール - 2段階ワークフローによるファイル管理システム

Author: YoyogiPinball
License: Free to use for personal and commercial purposes
"""

import sys

# サードパーティライブラリ
try:
    import questionary
    from colorama import init
except ImportError as e:
    # coloramaがインポートできない場合もあるので直接ANSIコードを使用
    print(f"\033[91m必要なライブラリがインストールされていません: {e}\033[0m")
    print(f"\033[93mpip install -r requirements.txt を実行してください\033[0m")
    sys.exit(1)

# 自作モジュール
from src.utils.colors import Colors
from src.core.config_loader import ConfigLoader, PresetMeta
from src.core.logger import LootLogger
from src.core.file_scanner import FileScanner
from src.core.preview_generator import PreviewGenerator
from src.handlers.sort_handler import SortModeHandler
from src.handlers.clean_handler import CleanModeHandler
from src.handlers.png_prompt_sort_handler import PngPromptSortModeHandler

# Windows環境でのUTF-8出力対応
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# colorama初期化（Windows対応）
init(autoreset=True)


# =====================================
# LootManager - メイン管理クラス
# =====================================

class LootManager:
    """
    Loot Organizerのメイン管理クラス

    機能:
    - プリセット選択メニュー
    - モード別処理の実行
    - プレビュー → 確認 → 実行のフロー制御
    """

    def __init__(self):
        """初期化"""
        self.config_loader = ConfigLoader()

    def run(self):
        """メインループ"""
        while True:
            # プリセット検出
            presets = self.config_loader.discover_presets()

            if not presets:
                print(f"{Colors.NEON_RED}エラー: configs/ フォルダにプリセットが見つかりません{Colors.RESET}")
                print(f"{Colors.NEON_YELLOW}configs/samples/ から設定ファイルをコピーして configs/ に配置してください{Colors.RESET}")
                return

            # メニュー選択
            choices = [
                f"{preset.icon} {preset.name} [{preset.mode}]"
                for preset in presets
            ]
            choices.append("❌ 終了")

            print(f"\n{Colors.NEON_CYAN}{'─' * 44}{Colors.RESET}")
            print(f"{Colors.NEON_YELLOW}📋 メニュー選択{Colors.RESET}")
            print(f"{Colors.NEON_CYAN}{'─' * 44}{Colors.RESET}")

            selected = questionary.select(
                "実行するプリセットを選択:",
                choices=choices
            ).ask()

            print(f"{Colors.NEON_CYAN}{'─' * 44}{Colors.RESET}\n")

            if not selected or selected == "❌ 終了":
                print(f"{Colors.NEON_CYAN}終了します{Colors.RESET}")
                break

            # 選択されたプリセットを実行
            preset_index = choices.index(selected)
            if preset_index < len(presets):
                self.execute_preset(presets[preset_index])

    def execute_preset(self, preset: PresetMeta):
        """
        プリセットを実行

        Args:
            preset: プリセットメタ情報
        """
        print()
        print(f"{Colors.NEON_CYAN}{'=' * 44}")
        print(f"{Colors.NEON_BLUE}{preset.icon} {preset.name}")
        print(f"{Colors.NEON_CYAN}{'=' * 44}{Colors.RESET}")
        print()

        # 設定ロード
        try:
            config = self.config_loader.load_config(preset.file_path)
        except Exception as e:
            print(f"{Colors.NEON_RED}エラー: 設定ファイルの読み込みに失敗: {e}{Colors.RESET}")
            input(f"{Colors.NEON_CYAN}Enterキーで続行...{Colors.RESET}")
            return

        settings = config['settings']

        # ロガー初期化
        logger = LootLogger(
            log_directory=settings['logging']['log_directory'],
            enable_logging=settings.get('enable_logging', True)
        )

        # モード別処理
        if preset.mode == "Sort" or preset.mode == "Clean":
            # Sort/Cleanモードはtarget_directoryを使用
            try:
                scanner = FileScanner(settings['target_directory'], logger)
            except FileNotFoundError as e:
                print(f"{Colors.NEON_RED}エラー: {e}{Colors.RESET}")
                input(f"{Colors.NEON_CYAN}Enterキーで続行...{Colors.RESET}")
                return

            if preset.mode == "Sort":
                handler = SortModeHandler(config, scanner, logger)
            else:  # Clean
                handler = CleanModeHandler(config, scanner, logger)

        elif preset.mode == "PNG_Prompt_Sort":
            # PNG_Prompt_Sortモードはsource_directoriesを使用（ハンドラ内で処理）
            scanner = None  # PNG_Prompt_Sortモードではscannerは使用しない
            handler = PngPromptSortModeHandler(config, scanner, logger)

        else:
            print(f"{Colors.NEON_RED}エラー: 不明なモード '{preset.mode}'{Colors.RESET}")
            input(f"{Colors.NEON_CYAN}Enterキーで続行...{Colors.RESET}")
            return

        # 操作を計画
        operations = handler.plan_operations()

        if not operations:
            print(f"{Colors.NEON_YELLOW}処理対象のファイルがありません{Colors.RESET}")
            input(f"{Colors.NEON_CYAN}Enterキーで続行...{Colors.RESET}")
            return

        # プレビュー表示
        preview_gen = PreviewGenerator(
            config=config,
            preview_mode=settings['preview']['mode'],
            preview_count=settings['preview']['count']
        )
        preview = preview_gen.generate_preview(operations, preset.mode)
        print(preview)

        # 実行確認
        if settings.get('confirm_before_execute', True):
            print(f"{Colors.NEON_CYAN}{'─' * 44}{Colors.RESET}")
            print(f"{Colors.NEON_YELLOW}⚡ 実行確認{Colors.RESET}")
            print(f"{Colors.NEON_CYAN}{'─' * 44}{Colors.RESET}")

            execute = questionary.confirm(
                "この内容で実行しますか?",
                default=False
            ).ask()

            print(f"{Colors.NEON_CYAN}{'─' * 44}{Colors.RESET}\n")

            if not execute:
                print(f"{Colors.NEON_YELLOW}キャンセルしました{Colors.RESET}")
                input(f"{Colors.NEON_CYAN}Enterキーで続行...{Colors.RESET}")
                return

        # 実行
        dry_run = settings.get('dry_run_default', True)
        if dry_run:
            print(f"{Colors.NEON_YELLOW}[ドライランモード] 実際にはファイル操作を行いません{Colors.RESET}")

        success, failure = handler.execute_operations(operations, dry_run=dry_run)

        # 結果サマリー
        print()
        print(f"{Colors.NEON_GREEN}完了: {success}件成功{Colors.RESET}")
        if failure > 0:
            print(f"{Colors.NEON_RED}失敗: {failure}件{Colors.RESET}")

        input(f"{Colors.NEON_CYAN}Enterキーで続行...{Colors.RESET}")


# =====================================
# メイン処理
# =====================================

def main():
    """メインエントリポイント"""
    print(f"{Colors.NEON_CYAN}╔════════════════════════════════════════════╗")
    print(f"{Colors.NEON_BLUE}║  📁 Loot Organizer                        ║")
    print(f"{Colors.NEON_CYAN}╚════════════════════════════════════════════╝{Colors.RESET}")
    print()

    manager = LootManager()
    manager.run()


if __name__ == "__main__":
    main()
