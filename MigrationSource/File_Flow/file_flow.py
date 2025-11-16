#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FileFlow - ファイル整理自動化ツール

このスクリプトは以下の処理を自動で実行します:
1. 特定文字列を含むファイルの削除
2. ファイル名から絵文字・特殊文字の削除
3. 条件に応じたファイルの振り分け（コピー/移動）

使い方:
    python file_flow.py [オプション]

オプション:
    --execute    : ドライランをスキップして即座に実行
    --no-confirm : 実行前の確認をスキップ
"""

import os
import re
import shutil
import glob
import yaml
import sys
import logging
from datetime import datetime
from pathlib import Path
from colorama import init, Fore, Style

# スクリプトのあるディレクトリに移動（ダブルクリック起動時に重要！）
# これにより、config.yamlやlogsディレクトリが正しく見つかるようになる
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

# coloramaを初期化（Windowsでのカラー表示対応）
# autoreset=Trueで各print文の末尾で自動的に色がリセットされる
init(autoreset=True)


class FileFlow:
    """
    ファイル整理を自動化するメインクラス
    
    設定ファイル（YAML）を読み込み、以下の処理を実行:
    - 不要ファイルの削除
    - ファイル名のクリーンアップ
    - ファイルの振り分け（コピー/移動）
    """
    
    def __init__(self, config_path="config.yaml"):
        """
        FileFlowの初期化
        
        Args:
            config_path (str): 設定ファイルのパス
        """
        self.config = self._load_config(config_path)
        self.dry_run = True  # デフォルトはドライランモード
        self.logger = self._setup_logger()
        
        # 統計情報（処理結果の記録用）
        self.stats = {
            'deleted': 0,      # 削除したファイル数
            'renamed': 0,      # 名前変更したファイル数
            'copied': 0,       # コピーしたファイル数
            'moved': 0,        # 移動したファイル数
            'errors': 0        # エラー数
        }
    
    def _load_config(self, config_path):
        """
        YAML設定ファイルを読み込む
        
        Args:
            config_path (str): 設定ファイルのパス
            
        Returns:
            dict: 設定内容の辞書
            
        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
            yaml.YAMLError: YAML形式が不正な場合
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(Fore.GREEN + f"設定ファイルを読み込みました: {config_path}")
            return config
        except FileNotFoundError:
            print(Fore.RED + f"エラー: 設定ファイルが見つかりません: {config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(Fore.RED + f"エラー: 設定ファイルの形式が不正です: {e}")
            sys.exit(1)
    
    def _setup_logger(self):
        """
        ログ出力の設定
        
        ログファイルは logs/YYYYMMDD.log の形式で保存される（1日1ファイル）
        
        Returns:
            logging.Logger: 設定済みのロガーオブジェクト
        """
        # ログディレクトリの作成
        log_dir = self.config.get('advanced', {}).get('log_directory', 'logs')
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # ログファイル名の生成（日付のみ）
        timestamp = datetime.now().strftime('%Y%m%d')
        log_file = Path(log_dir) / f"{timestamp}.log"
        
        # ロガーの設定
        logger = logging.getLogger('FileFlow')
        logger.setLevel(logging.DEBUG)
        
        # 既存のハンドラをクリア（複数回実行時の重複防止）
        logger.handlers.clear()
        
        # ファイルハンドラ（ログファイルへの追記）
        file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
        file_handler.setLevel(logging.DEBUG)
        
        # フォーマッターの設定
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        
        print(Fore.CYAN + f"📝 ログファイル: {log_file}")
        return logger
    
    def _print_header(self, title):
        """
        セクションヘッダーを見やすく表示（絵文字付き）
        
        Args:
            title (str): ヘッダータイトル
        """
        print(Fore.CYAN + "\n" + "=" * 50)
        print(Fore.CYAN + f"  {title}")
        print(Fore.CYAN + "=" * 50 + "\n")
        self.logger.info(f"--- {title} ---")
    
    def delete_files_with_string(self, directory, search_strings, recurse=True):
        """
        指定された文字列を含むファイルを削除
        
        Args:
            directory (str): 検索対象ディレクトリ
            search_strings (list): 削除対象の文字列リスト
            recurse (bool): サブフォルダも検索するか
            
        Returns:
            list: 削除対象ファイルのパスリスト
        """
        self._print_header("🗑️  ステップ1: 特定文字列を含むファイルの削除")
        
        print(f"📁 対象ディレクトリ: {directory}")
        print(f"🔍 削除対象文字列: {', '.join(search_strings)}")
        print(f"🔄 再帰処理: {'はい' if recurse else 'いいえ'}\n")
        
        files_to_delete = []
        
        # ファイルの検索
        if recurse:
            # サブフォルダを含めて検索
            for root, _, files in os.walk(directory):
                for name in files:
                    # いずれかの文字列が含まれているかチェック
                    if any(search_str in name for search_str in search_strings):
                        files_to_delete.append(os.path.join(root, name))
        else:
            # 指定ディレクトリ直下のみ検索
            for name in os.listdir(directory):
                full_path = os.path.join(directory, name)
                if os.path.isfile(full_path):
                    if any(search_str in name for search_str in search_strings):
                        files_to_delete.append(full_path)
        
        # 結果の表示
        if not files_to_delete:
            print(Fore.YELLOW + "⚠️  削除対象のファイルは見つかりませんでした。")
            self.logger.info("削除対象のファイルなし")
            return files_to_delete
        
        print(Fore.YELLOW + f"📊 削除対象: {len(files_to_delete)} 件のファイル\n")
        
        # 処理実行
        processed_count = 0
        for file_path in files_to_delete:
            file_name = os.path.basename(file_path)
            
            if self.dry_run:
                # ドライランモード: 実際には削除しない
                print(Fore.YELLOW + f"  [ドライラン] 削除予定: {file_name}")
                self.logger.info(f"[DRY-RUN] 削除予定: {file_path}")
                processed_count += 1
            else:
                # 実行モード: 実際に削除
                try:
                    os.remove(file_path)
                    print(Fore.RED + f"  ❌ 削除: {file_name}")
                    self.logger.info(f"削除: {file_path}")
                    self.stats['deleted'] += 1
                    processed_count += 1
                except Exception as e:
                    print(Fore.RED + f"  ⚠️  エラー: '{file_name}' の削除に失敗: {e}")
                    self.logger.error(f"削除失敗: {file_path} - {e}")
                    self.stats['errors'] += 1
        
        print(Fore.GREEN + f"\n✅ 処理完了: {processed_count}/{len(files_to_delete)} 件")
        return files_to_delete
    
    def remove_characters_from_filenames(self, path, recurse=False):
        """
        ファイル名から絵文字や特殊文字を削除
        
        以下の文字を削除:
        - 絵文字（Unicode絵文字範囲）
        - ファイルシステムで使えない文字 (\ / : * ? " < > |)
        - 制御文字
        
        Args:
            path (str): 処理対象ディレクトリ
            recurse (bool): サブフォルダも処理するか
            
        Returns:
            list: 名前変更したファイルのリスト（元の名前、新しい名前）
        """
        self._print_header("✨ ステップ2: ファイル名のクリーンアップ")
        
        print(f"📁 対象パス: {path}")
        print(f"🔄 再帰処理: {'はい' if recurse else 'いいえ'}\n")
        
        # デフォルトのクリーンアップパターン（正規表現）
        patterns = [
            r'[\u2600-\u27BF]',  # 絵文字（基本範囲）
            r'[\uD83C-\uDBFF][\uDC00-\uDFFF]',  # 絵文字（拡張範囲）
            r'[\u200D\uFE0E\uFE0F]',  # ゼロ幅文字
            r'[\\/:\*\?"<>|]',  # ファイルシステムで使えない文字
            r'[\u0000-\u001F\u007F-\u009F\u2000-\u200F\u2028-\u2029\u2060-\u206F\uFEFF\uFFFC-\uFFFD]'  # 制御文字
        ]
        
        # カスタムパターンの追加
        custom_patterns = self.config.get('cleanup', {}).get('custom_patterns', [])
        patterns.extend(custom_patterns)
        
        # パターンを結合してコンパイル
        clean_pattern = re.compile('|'.join(patterns))
        
        # 処理対象ファイルの収集
        files_to_process = []
        if recurse:
            for root, _, files in os.walk(path):
                for name in files:
                    files_to_process.append(os.path.join(root, name))
        else:
            for name in os.listdir(path):
                full_path = os.path.join(path, name)
                if os.path.isfile(full_path):
                    files_to_process.append(full_path)
        
        if not files_to_process:
            print(Fore.YELLOW + f"⚠️  処理対象のファイルが見つかりません: {path}")
            self.logger.warning(f"処理対象ファイルなし: {path}")
            return []
        
        print(Fore.CYAN + f"📊 対象ファイル数: {len(files_to_process)} 件\n")
        
        renamed_files = []
        processed_count = 0
        
        for full_path in files_to_process:
            directory = os.path.dirname(full_path)
            original_filename = os.path.basename(full_path)
            base_name, extension = os.path.splitext(original_filename)
            
            # 特殊文字を削除
            clean_base_name = clean_pattern.sub('', base_name)
            
            # クリーンアップ後のファイル名が空になる場合はスキップ
            if not clean_base_name.strip():
                print(Fore.YELLOW + f"  ⚠️  スキップ: '{original_filename}' (クリーン後のファイル名が空)")
                self.logger.warning(f"スキップ（空のファイル名）: {full_path}")
                continue
            
            # ファイル名に変更があるか確認
            if clean_base_name != base_name:
                new_filename = clean_base_name + extension
                new_full_path = os.path.join(directory, new_filename)
                
                if self.dry_run:
                    # ドライランモード
                    print(Fore.YELLOW + f"  [ドライラン] 名前変更予定: '{original_filename}' -> '{new_filename}'")
                    self.logger.info(f"[DRY-RUN] 名前変更予定: {full_path} -> {new_full_path}")
                    renamed_files.append((original_filename, new_filename))
                    processed_count += 1
                else:
                    # 実行モード
                    try:
                        os.rename(full_path, new_full_path)
                        print(Fore.GREEN + f"  ✏️  名前変更: '{original_filename}' -> '{new_filename}'")
                        self.logger.info(f"名前変更: {full_path} -> {new_full_path}")
                        self.stats['renamed'] += 1
                        renamed_files.append((original_filename, new_filename))
                        processed_count += 1
                    except Exception as e:
                        print(Fore.RED + f"  ⚠️  エラー: '{original_filename}' の名前変更に失敗: {e}")
                        self.logger.error(f"名前変更失敗: {full_path} - {e}")
                        self.stats['errors'] += 1
        
        if not renamed_files:
            print(Fore.YELLOW + "⚠️  名前変更が必要なファイルはありませんでした。")
            self.logger.info("名前変更対象なし")
        else:
            print(Fore.GREEN + f"\n✅ 処理完了: {processed_count} 件のファイル名を変更")
        
        return renamed_files
    
    def process_files(self, source_directory, search_string, destination_directory, action):
        """
        条件に一致するファイルを振り分け（コピー/移動/削除）
        
        Args:
            source_directory (str): 検索元ディレクトリ
            search_string (str): 検索パターン（ワイルドカード使用可）
            destination_directory (str): 振り分け先ディレクトリ
            action (str): 実行する処理 ('copy', 'move', 'delete')
            
        Returns:
            list: 処理したファイルのリスト
        """
        # 検索パスの構築（再帰的に検索）
        search_path = os.path.join(source_directory, '**', search_string)
        files_to_process = [f for f in glob.glob(search_path, recursive=True) if os.path.isfile(f)]
        
        if not files_to_process:
            print(Fore.YELLOW + f"  ⚠️  該当ファイルなし: {search_string}")
            self.logger.info(f"該当ファイルなし: {search_string}")
            return []
        
        print(f"\n  🔍 検索パターン: {search_string}")
        print(f"  📊 該当ファイル: {len(files_to_process)} 件")
        print(f"  ⚙️  処理: {action}")
        if action != 'delete':
            print(f"  📁 宛先: {destination_directory}")
        
        # 宛先ディレクトリの作成（削除処理以外）
        if action != 'delete' and not self.dry_run:
            Path(destination_directory).mkdir(parents=True, exist_ok=True)
        
        processed_files = []
        processed_count = 0
        
        for file_path in files_to_process:
            file_name = os.path.basename(file_path)
            
            try:
                if action.lower() == "copy":
                    if self.dry_run:
                        print(Fore.YELLOW + f"    [ドライラン] コピー予定: '{file_name}'")
                        self.logger.info(f"[DRY-RUN] コピー予定: {file_path} -> {destination_directory}")
                    else:
                        shutil.copy2(file_path, destination_directory)
                        print(Fore.GREEN + f"    📄 コピー: '{file_name}'")
                        self.logger.info(f"コピー: {file_path} -> {destination_directory}")
                        self.stats['copied'] += 1
                    processed_files.append(file_path)
                    processed_count += 1
                    
                elif action.lower() == "move":
                    if self.dry_run:
                        print(Fore.YELLOW + f"    [ドライラン] 移動予定: '{file_name}'")
                        self.logger.info(f"[DRY-RUN] 移動予定: {file_path} -> {destination_directory}")
                    else:
                        shutil.move(file_path, destination_directory)
                        print(Fore.GREEN + f"    📦 移動: '{file_name}'")
                        self.logger.info(f"移動: {file_path} -> {destination_directory}")
                        self.stats['moved'] += 1
                    processed_files.append(file_path)
                    processed_count += 1
                    
                elif action.lower() == "delete":
                    if self.dry_run:
                        print(Fore.YELLOW + f"    [ドライラン] 削除予定: '{file_name}'")
                        self.logger.info(f"[DRY-RUN] 削除予定: {file_path}")
                    else:
                        os.remove(file_path)
                        print(Fore.RED + f"    ❌ 削除: '{file_name}'")
                        self.logger.info(f"削除: {file_path}")
                        self.stats['deleted'] += 1
                    processed_files.append(file_path)
                    processed_count += 1
                    
                else:
                    print(Fore.RED + f"  ⚠️  エラー: 無効な処理 '{action}' (copy/move/delete のいずれかを指定)")
                    self.logger.error(f"無効な処理: {action}")
                    break
                    
            except Exception as e:
                print(Fore.RED + f"  ⚠️  エラー: '{file_name}' の {action} 処理に失敗: {e}")
                self.logger.error(f"{action}失敗: {file_path} - {e}")
                self.stats['errors'] += 1
        
        print(Fore.GREEN + f"  ✅ 処理完了: {processed_count}/{len(files_to_process)} 件")
        return processed_files
    
    def run(self, execute=False, no_confirm=False):
        """
        FileFlowのメイン処理を実行
        
        Args:
            execute (bool): Trueの場合、ドライランをスキップして即座に実行
            no_confirm (bool): Trueの場合、実行前の確認をスキップ
        """
        # 実行モードの設定
        if execute:
            self.dry_run = False
        
        # 開始メッセージ
        mode_text = "実行モード" if not self.dry_run else "ドライランモード"
        print(Fore.MAGENTA + "\n" + "=" * 50)
        print(Fore.MAGENTA + f"  🚀 FileFlow を開始します ({mode_text})")
        print(Fore.MAGENTA + "=" * 50)
        self.logger.info(f"FileFlow開始 ({mode_text})")
        
        target_dir = self.config['target_directory']
        
        # ディレクトリの存在確認
        if not os.path.exists(target_dir):
            print(Fore.RED + f"❌ エラー: 対象ディレクトリが見つかりません: {target_dir}")
            self.logger.error(f"対象ディレクトリが見つかりません: {target_dir}")
            return
        
        # ステップ1: 削除処理
        if self.config.get('deletion', {}).get('enabled', False):
            delete_strings = self.config['deletion']['strings']
            delete_recursive = self.config['deletion'].get('recursive', True)
            self.delete_files_with_string(target_dir, delete_strings, delete_recursive)
        else:
            print(Fore.YELLOW + "\n⚠️  ステップ1: 削除処理はスキップされました（設定で無効化）")
        
        # ステップ2: クリーンアップ処理
        if self.config.get('cleanup', {}).get('enabled', False):
            cleanup_recursive = self.config['cleanup'].get('recursive', True)
            self.remove_characters_from_filenames(target_dir, cleanup_recursive)
        else:
            print(Fore.YELLOW + "\n⚠️  ステップ2: クリーンアップ処理はスキップされました（設定で無効化）")
        
        # ステップ3: 振り分け処理
        sorting_rules = self.config.get('sorting_rules', [])
        if sorting_rules:
            self._print_header("📋 ステップ3: ファイル振り分け")
            
            for i, rule in enumerate(sorting_rules, 1):
                search = rule['search']
                destination = rule['destination']
                action = rule['action']
                
                print(f"\n  ルール {i}/{len(sorting_rules)}:")
                self.process_files(target_dir, search, destination, action)
        else:
            print(Fore.YELLOW + "\n⚠️  ステップ3: 振り分けルールが設定されていません")
        
        # 結果サマリーの表示
        self._print_summary()
        
        # ドライランモードの場合、実行確認
        if self.dry_run:
            confirm_enabled = self.config.get('advanced', {}).get('confirm_before_execution', True)
            if confirm_enabled and not no_confirm:
                print(Fore.CYAN + "\n" + "=" * 50)
                response = input(Fore.YELLOW + "実際に処理を実行しますか？ (y/n): ").strip().lower()
                if response == 'y':
                    print(Fore.GREEN + "\n✅ 実行モードで再実行します...\n")
                    self.dry_run = False
                    self.stats = {'deleted': 0, 'renamed': 0, 'copied': 0, 'moved': 0, 'errors': 0}
                    self.run(execute=True, no_confirm=True)
                else:
                    print(Fore.YELLOW + "\n❌ 処理をキャンセルしました。")
                    self.logger.info("ユーザーによりキャンセル")
    
    def _print_summary(self):
        """処理結果のサマリーを表示"""
        print(Fore.CYAN + "\n" + "=" * 50)
        print(Fore.CYAN + "  📊 処理結果サマリー")
        print(Fore.CYAN + "=" * 50)
        
        if self.dry_run:
            print(Fore.YELLOW + "  ⚙️  モード: ドライラン（実際の処理は行われていません）")
        else:
            print(Fore.GREEN + "  ✅ モード: 実行完了")
            print(f"  🗑️  削除: {self.stats['deleted']} 件")
            print(f"  ✏️  名前変更: {self.stats['renamed']} 件")
            print(f"  📄 コピー: {self.stats['copied']} 件")
            print(f"  📦 移動: {self.stats['moved']} 件")
            
            if self.stats['errors'] > 0:
                print(Fore.RED + f"  ⚠️  エラー: {self.stats['errors']} 件")
            else:
                print(Fore.GREEN + "  ✅ エラー: 0 件")
        
        print(Fore.CYAN + "=" * 50)
        self.logger.info(f"処理完了 - 統計: {self.stats}")


def main():
    """
    エントリーポイント
    コマンドライン引数を処理してFileFlowを実行
    """
    # コマンドライン引数の解析
    execute = '--execute' in sys.argv
    no_confirm = '--no-confirm' in sys.argv
    
    # ヘルプ表示
    if '--help' in sys.argv or '-h' in sys.argv:
        print(__doc__)
        return
    
    try:
        # FileFlowのインスタンス作成と実行
        flow = FileFlow()
        flow.run(execute=execute, no_confirm=no_confirm)
        
        print(Fore.CYAN + "\n✅ 全ての処理が完了しました。")
        
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\n⚠️  処理が中断されました。")
    except Exception as e:
        print(Fore.RED + f"\n❌ 予期しないエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    
    # Enterキーで終了
    input("\nEnterキーを押して終了します...")


if __name__ == "__main__":
    main()
