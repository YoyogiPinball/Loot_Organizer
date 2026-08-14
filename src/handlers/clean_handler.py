# -*- coding: utf-8 -*-
"""
Clean モードの処理ハンドラー
"""

import re
from typing import List

from ..core.file_scanner import FileScanner
from ..core.preview_generator import FileOperation
from ..utils.file_utils import clean_filename
from ..utils.path_utils import to_path
from .base_handler import BaseHandler


class CleanModeHandler(BaseHandler):
    """
    Clean モードの処理を行うクラス

    機能:
    - 3ステップ処理（削除 → クリーンアップ → 振り分け）
    - プレビュー → 確認 → 実行のフロー

    拡張機能:
    - source_directory: 特定のディレクトリからのファイルのみ対象
    - rename_pattern: 移動/コピー時にファイル名から文字列を削除/置換
    - recursive: サブフォルダも再帰的に検索
    - cleanup の pattern と target_directories: 特定のパターン・ディレクトリのみをクリーンアップ
    - cleanup の after_sorting: True の場合、sorting_rules の後に cleanup を実行（デフォルト: False）
    """

    MODE = "Clean"
    REQUIRED_SETTINGS = ("target_directory",)

    @classmethod
    def validate_config(cls, config, config_path=None) -> None:
        """Cleanモードの設定を検証"""
        super().validate_config(config, config_path=config_path)
        has_operations = any(
            key in config for key in ['deletion', 'cleanup', 'sorting_rules']
        )
        if not has_operations:
            label = str(config_path) if config_path else "設定"
            raise ValueError(
                f"{label}: Clean モードには 'deletion', 'cleanup', "
                "'sorting_rules' のいずれかが必要です"
            )

    def _apply_mode_defaults(self) -> None:
        """Cleanモードのデフォルト値を適用"""
        if 'deletion' in self.config:
            self.config['deletion'].setdefault('enabled', False)
            self.config['deletion'].setdefault('recursive', True)
            self.config['deletion'].setdefault('strings', [])
            self.config['deletion'].setdefault('delete_mode', 'trash')

        if 'cleanup' in self.config:
            self.config['cleanup'].setdefault('enabled', False)
            self.config['cleanup'].setdefault('recursive', True)
            self.config['cleanup'].setdefault('custom_patterns', [])

        if 'sorting_rules' not in self.config:
            self.config['sorting_rules'] = []

    def plan_operations(self) -> List[FileOperation]:
        """
        実行する操作を計画

        Returns:
            ファイル操作のリスト
        """
        self._start_planning()
        operations = []

        # ステップ1: 削除
        if self.config.get('deletion', {}).get('enabled', False):
            deletion_ops = self._plan_deletion()
            operations.extend(self._record_planned_operations(deletion_ops))

        # cleanup を sorting の後に実行するかチェック
        cleanup_config = self.config.get('cleanup', {})
        cleanup_enabled = cleanup_config.get('enabled', False)
        cleanup_after_sorting = cleanup_config.get('after_sorting', False)

        # ステップ2: クリーンアップ（after_sorting が false の場合、デフォルト動作）
        if cleanup_enabled and not cleanup_after_sorting:
            cleanup_ops = self._plan_cleanup()
            operations.extend(self._record_planned_operations(cleanup_ops))

        # ステップ3: 振り分け
        if 'sorting_rules' in self.config:
            sorting_ops = self._plan_sorting()
            operations.extend(sorting_ops)

        # ステップ4: クリーンアップ（after_sorting が true の場合）
        if cleanup_enabled and cleanup_after_sorting:
            cleanup_ops = self._plan_cleanup()
            operations.extend(self._record_planned_operations(cleanup_ops))

        return operations

    def _plan_deletion(self) -> List[FileOperation]:
        """削除操作を計画"""
        operations = []
        deletion_config = self.config['deletion']
        delete_mode = deletion_config.get('delete_mode', 'trash')
        if delete_mode not in {'trash', 'permanent'}:
            raise ValueError(
                "deletion.delete_mode は trash または permanent を指定してください"
            )
        strings = deletion_config.get('strings', [])
        recursive = deletion_config.get('recursive', True)
        planned_files = set()

        for string in strings:
            pattern = f"*{string}*"
            matched_files = self.scanner.scan_files(
                pattern=pattern,
                recursive=recursive
            )

            for file in matched_files:
                if file in planned_files:
                    continue
                operations.append(FileOperation(
                    source=file,
                    destination=None,
                    action='delete',
                    reason=f"文字列 '{string}' を含む",
                    delete_mode=delete_mode,
                ))
                planned_files.add(file)

        return operations

    def _plan_cleanup(self) -> List[FileOperation]:
        """
        クリーンアップ操作を計画

        対応オプション:
        - pattern: 特定のパターンを含むファイルのみ対象（デフォルト: '*'）
        - target_directories: 特定のディレクトリのみ対象（未指定時は全体のtarget_directory）
        - recursive: サブフォルダも検索（デフォルト: True）
        - custom_patterns: ファイル名から削除する正規表現パターン
        - after_sorting: True の場合、sorting_rules の後に実行（デフォルト: False）

        Returns:
            ファイル操作のリスト
        """
        operations = []
        cleanup_config = self.config['cleanup']
        recursive = cleanup_config.get('recursive', True)
        custom_patterns = cleanup_config.get('custom_patterns', [])
        pattern = cleanup_config.get('pattern', '*')  # 検索パターン（デフォルト: 全ファイル）
        target_directories = cleanup_config.get('target_directories')  # 対象ディレクトリ（オプション）

        # target_directoriesが指定されていれば専用のスキャナーを使用
        if target_directories:
            temp_scanner = FileScanner(
                target_directories,
                self.logger,
                planning_context=self.planning_context,
            )
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
        """
        振り分け操作を計画

        対応オプション:
        - search: 検索パターン（ワイルドカード可）
        - source_directory: 特定のディレクトリからのファイルのみ対象（オプション）
        - destination: 移動先ディレクトリ
        - action: 操作種類（move, copy, delete）
        - recursive: サブフォルダも検索（デフォルト: False）
        - rename_pattern: 移動/コピー時にファイル名から文字列を削除/置換（オプション）

        Returns:
            ファイル操作のリスト
        """
        operations = []
        sorting_rules = self.config.get('sorting_rules', [])

        for rule in sorting_rules:
            search = rule['search']
            for file in self._match_sorting_files(rule):
                destination = self._build_sort_destination(file, rule)

                # rename_pattern 適用後のファイル名で存在チェックする
                if rule.get('skip_if_exists', False) and destination:
                    if self._destination_exists(destination):
                        continue

                operation = FileOperation(
                    source=file,
                    destination=destination,
                    action=rule['action'],
                    reason=f"パターン '{search}'",
                    skip_if_exists=rule.get('skip_if_exists', False),
                )
                operations.append(operation)
                self._record_planned_operations([operation])

        return operations

    def _match_sorting_files(self, rule) -> List:
        """sorting_rule に一致するファイルを返す"""
        matched_files = self.scanner.scan_files(
            pattern=rule['search'],
            filters=rule.get('filters', {}),
            recursive=rule.get('recursive', False)
        )

        source_directory = rule.get('source_directory')
        if not source_directory:
            return matched_files

        source_dir_path = to_path(source_directory)
        filtered_files = []
        for file in matched_files:
            try:
                file.relative_to(source_dir_path)
            except ValueError:
                continue
            filtered_files.append(file)

        return filtered_files

    def _build_sort_destination(self, file, rule):
        """sorting_rule から最終 destination を組み立てる"""
        if not rule.get('destination'):
            return None

        destination = to_path(rule['destination'])
        rename_pattern = rule.get('rename_pattern')
        if not rename_pattern:
            return destination / file.name

        new_name = self._apply_rename_pattern(file.name, rename_pattern)
        return destination / new_name

    @staticmethod
    def _apply_rename_pattern(filename: str, rename_pattern: dict[str, str]) -> str:
        """rename_patternをファイル名に適用"""
        new_name = filename
        for pattern, replacement in rename_pattern.items():
            new_name = re.sub(
                re.escape(pattern),
                replacement,
                new_name,
                flags=re.IGNORECASE
            )
        return clean_filename(new_name)

    def _destination_exists(self, destination) -> bool:
        """最終 destination にファイルが存在するか確認する"""
        return self.planning_context.is_file(destination)
