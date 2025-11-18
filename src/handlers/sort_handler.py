# -*- coding: utf-8 -*-
"""
Sort モードの処理ハンドラー
"""

import shutil
from pathlib import Path
from typing import List, Dict, Any, Tuple
from tqdm import tqdm

from ..core.file_scanner import FileScanner
from ..core.logger import LootLogger
from ..core.preview_generator import FileOperation


class SortModeHandler:
    """
    Sort モードの処理を行うクラス

    機能:
    - ルールベースのファイル振り分け
    - 最初にマッチしたルールのみ適用
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
        move_rules = self.config.get('move_rules', [])
        exclusions = self.config.get('exclusions', {})

        # 処理済みファイルを追跡（最初のルールのみ適用）
        processed_files = set()

        for rule in move_rules:
            if not rule.get('enabled', True):
                continue

            pattern = rule['pattern']
            dest = Path(rule['dest'])
            description = rule.get('description', pattern)
            filters = rule.get('filters', {})

            # ファイルをスキャン
            matched_files = self.scanner.scan_files(
                pattern=pattern,
                filters=filters,
                exclusions=exclusions,
                recursive=False
            )

            # 未処理のファイルのみ追加
            for file in matched_files:
                if file not in processed_files:
                    operations.append(FileOperation(
                        source=file,
                        destination=dest,
                        action='move',
                        reason=description
                    ))
                    processed_files.add(file)

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
                    # 移動先ディレクトリを作成
                    op.destination.mkdir(parents=True, exist_ok=True)

                    # ファイル移動
                    shutil.move(str(op.source), str(op.destination / op.source.name))

                # ログ記録
                self.logger.info(
                    f"[移動] {op.source} → {op.destination / op.source.name} ({op.reason})"
                )
                success_count += 1

            except Exception as e:
                self.logger.error(f"[エラー] {op.source}: {e}")
                failure_count += 1

        return success_count, failure_count
