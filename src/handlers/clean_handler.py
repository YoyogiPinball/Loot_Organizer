# -*- coding: utf-8 -*-
"""
Clean モードの処理ハンドラー
"""

import shutil
from pathlib import Path
from typing import List, Dict, Any, Tuple
from tqdm import tqdm

from ..core.file_scanner import FileScanner
from ..core.logger import LootLogger
from ..core.preview_generator import FileOperation
from ..utils.file_utils import clean_filename


class CleanModeHandler:
    """
    Clean モードの処理を行うクラス

    機能:
    - 3ステップ処理（削除 → クリーンアップ → 振り分け）
    - プレビュー → 確認 → 実行のフロー
    """

    def __init__(
        self,
        config: Dict[str, Any],
        scanner: FileScanner,
        logger: LootLogger
    ):
        """
        初期化

        Args:
            config: 設定辞書
            scanner: ファイルスキャナー
            logger: ロガー
        """
        self.config = config
        self.scanner = scanner
        self.logger = logger

    def plan_operations(self) -> List[FileOperation]:
        """
        実行する操作を計画

        Returns:
            ファイル操作のリスト
        """
        operations = []

        # ステップ1: 削除
        if self.config.get('deletion', {}).get('enabled', False):
            operations.extend(self._plan_deletion())

        # ステップ2: クリーンアップ
        if self.config.get('cleanup', {}).get('enabled', False):
            operations.extend(self._plan_cleanup())

        # ステップ3: 振り分け
        if 'sorting_rules' in self.config:
            operations.extend(self._plan_sorting())

        return operations

    def _plan_deletion(self) -> List[FileOperation]:
        """削除操作を計画"""
        operations = []
        deletion_config = self.config['deletion']
        strings = deletion_config.get('strings', [])
        recursive = deletion_config.get('recursive', True)

        for string in strings:
            pattern = f"*{string}*"
            matched_files = self.scanner.scan_files(
                pattern=pattern,
                recursive=recursive
            )

            for file in matched_files:
                operations.append(FileOperation(
                    source=file,
                    destination=None,
                    action='delete',
                    reason=f"文字列 '{string}' を含む"
                ))

        return operations

    def _plan_cleanup(self) -> List[FileOperation]:
        """クリーンアップ操作を計画"""
        operations = []
        cleanup_config = self.config['cleanup']
        recursive = cleanup_config.get('recursive', True)
        custom_patterns = cleanup_config.get('custom_patterns', [])
        pattern = cleanup_config.get('pattern', '*')  # 検索パターン（デフォルト: 全ファイル）
        target_directories = cleanup_config.get('target_directories')  # 対象ディレクトリ（オプション）

        # target_directoriesが指定されていれば専用のスキャナーを使用
        if target_directories:
            temp_scanner = FileScanner(target_directories, self.logger)
            matched_files = temp_scanner.scan_files(
                pattern=pattern,
                recursive=recursive
            )
        else:
            # 指定がなければ全体のtarget_directoryを使用
            matched_files = self.scanner.scan_files(
                pattern=pattern,
                recursive=recursive
            )

        for file in matched_files:
            # クリーンアップ後のファイル名を計算
            cleaned_name = clean_filename(file.name, custom_patterns)

            # 変更が必要な場合のみ追加
            if cleaned_name != file.name:
                operations.append(FileOperation(
                    source=file,
                    destination=file.parent / cleaned_name,
                    action='cleanup',
                    reason='絵文字・特殊文字の除去'
                ))

        return operations

    def _plan_sorting(self) -> List[FileOperation]:
        """振り分け操作を計画"""
        operations = []
        sorting_rules = self.config.get('sorting_rules', [])

        for rule in sorting_rules:
            search = rule['search']
            destination = Path(rule['destination']) if rule.get('destination') else None
            action = rule['action']
            source_directory = rule.get('source_directory')  # ソースディレクトリ指定（オプション）
            rename_pattern = rule.get('rename_pattern')  # リネームパターン（オプション）
            recursive = rule.get('recursive', False)  # サブフォルダも検索するか（デフォルト: False）

            matched_files = self.scanner.scan_files(
                pattern=search,
                recursive=recursive
            )

            for file in matched_files:
                # source_directoryが指定されている場合、そのディレクトリからのファイルのみ対象
                if source_directory:
                    source_dir_path = Path(source_directory)
                    # ファイルが指定されたディレクトリ配下にあるかチェック
                    try:
                        file.relative_to(source_dir_path)
                    except ValueError:
                        # ディレクトリ配下にない場合はスキップ
                        continue

                # リネームパターンが指定されている場合、destination側のファイル名を変更
                if rename_pattern and destination:
                    new_name = file.name
                    for pattern, replacement in rename_pattern.items():
                        new_name = new_name.replace(pattern, replacement)
                    dest_with_rename = destination / new_name
                else:
                    dest_with_rename = destination

                operations.append(FileOperation(
                    source=file,
                    destination=dest_with_rename if rename_pattern else destination,
                    action=action,
                    reason=f"パターン '{search}'"
                ))

        return operations

    def execute_operations(
        self,
        operations: List[FileOperation],
        dry_run: bool = False
    ) -> Tuple[int, int]:
        """
        操作を実行

        Args:
            operations: ファイル操作のリスト
            dry_run: ドライランモード（実際には実行しない）

        Returns:
            (成功数, 失敗数)
        """
        success_count = 0
        failure_count = 0

        for op in tqdm(operations, desc="処理中", unit="files"):
            try:
                if not dry_run:
                    if op.action == 'delete':
                        op.source.unlink()

                    elif op.action == 'cleanup':
                        op.source.rename(op.destination)

                    elif op.action == 'move':
                        # destinationがファイルパス（親+ファイル名）かディレクトリパスかを判定
                        # rename_pattern使用時はdestinationに新しいファイル名が含まれている
                        if op.destination.suffix:
                            # 拡張子があればファイルパスと判定
                            op.destination.parent.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(op.source), str(op.destination))
                        else:
                            # ディレクトリパスと判定
                            op.destination.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(op.source), str(op.destination / op.source.name))

                    elif op.action == 'copy':
                        # destinationがファイルパス（親+ファイル名）かディレクトリパスかを判定
                        if op.destination.suffix:
                            # 拡張子があればファイルパスと判定
                            op.destination.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(str(op.source), str(op.destination))
                        else:
                            # ディレクトリパスと判定
                            op.destination.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(str(op.source), str(op.destination / op.source.name))

                # ログ記録
                self.logger.info(f"[{op.action}] {op.source} ({op.reason})")
                success_count += 1

            except Exception as e:
                self.logger.error(f"[エラー] {op.source}: {e}")
                failure_count += 1

        return success_count, failure_count
