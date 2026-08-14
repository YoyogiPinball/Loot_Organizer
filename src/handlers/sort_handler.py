# -*- coding: utf-8 -*-
"""
Sort モードの処理ハンドラー
"""

import re
import uuid
from typing import List

from ..core.preview_generator import FileOperation
from ..utils.file_utils import clean_filename
from ..utils.path_utils import to_path
from .base_handler import BaseHandler


class SortModeHandler(BaseHandler):
    """
    Sort モードの処理を行うクラス

    機能:
    - ルールベースのファイル振り分け
    - 最初にマッチしたルールのみ適用
    - プレビュー → 確認 → 実行のフロー
    """

    MODE = "Sort"
    REQUIRED_SETTINGS = ("target_directory",)
    REQUIRED_TOP_LEVEL = ("move_rules",)

    @classmethod
    def validate_config(cls, config, config_path=None) -> None:
        """Sortモードの設定を検証"""
        super().validate_config(config, config_path=config_path)
        if not config.get('move_rules'):
            label = str(config_path) if config_path else "設定"
            raise ValueError(f"{label}: Sort モードには 'move_rules' が必要です")

    def _apply_mode_defaults(self) -> None:
        """Sortモードのデフォルト値を適用"""
        if 'exclusions' not in self.config:
            self.config['exclusions'] = {}
        self.config['exclusions'].setdefault('exact_names', [])
        self.config['exclusions'].setdefault('patterns', [])

    @staticmethod
    def _generate_random_name(extension: str) -> str:
        """UUID4 先頭10文字のランダムファイル名を生成"""
        random_str = uuid.uuid4().hex[:10]
        return f"{random_str}{extension}"

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

    def plan_operations(self) -> List[FileOperation]:
        """
        実行する操作を計画

        Returns:
            ファイル操作のリスト
        """
        self._start_planning()
        operations = []
        move_rules = self.config.get('move_rules', [])
        exclusions = self.config.get('exclusions', {})

        # 処理済みの実体を追跡（リネーム後も最初のルールのみ適用）
        processed_files = set()

        for rule in move_rules:
            if not rule.get('enabled', True):
                continue

            pattern = rule['pattern']
            dest = to_path(rule['dest'])
            description = rule.get('description', pattern)
            filters = rule.get('filters', {})
            rename = rule.get('rename')
            rename_pattern = rule.get('rename_pattern')

            # ファイルをスキャン
            matched_files = self.scanner.scan_files(
                pattern=pattern,
                filters=filters,
                exclusions=exclusions,
                recursive=False
            )

            # 未処理のファイルのみ追加
            for file in matched_files:
                file_identity = self.planning_context.backing_path(file)
                if file_identity not in processed_files:
                    # rename: random の場合、ファイル名をランダム文字列に置換
                    if rename == 'random':
                        new_name = self._generate_random_name(file.suffix)
                        dest_path = dest / new_name
                    elif rename_pattern:
                        new_name = self._apply_rename_pattern(file.name, rename_pattern)
                        dest_path = dest / new_name
                    else:
                        dest_path = dest / file.name

                    if rule.get('skip_if_exists', False):
                        if self.planning_context.is_file(dest_path):
                            continue

                    operation = FileOperation(
                        source=file,
                        destination=dest_path,
                        action='move',
                        reason=description
                    )
                    operations.append(operation)
                    self._record_planned_operations([operation])
                    processed_files.add(file_identity)

        return operations
