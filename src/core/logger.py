# -*- coding: utf-8 -*-
"""
ログ管理クラス
"""

import logging
from pathlib import Path
from datetime import datetime


class LootLogger:
    """
    ログ管理クラス

    機能:
    - 日付ごとのログファイル作成
    - ファイル操作の記録
    - コンソール出力との連携
    """

    def __init__(self, log_directory: str, enable_logging: bool = True):
        """
        初期化

        Args:
            log_directory: ログ保存ディレクトリ
            enable_logging: ログ記録の有効/無効
        """
        self.log_directory = Path(log_directory)
        self.enable_logging = enable_logging

        if self.enable_logging:
            self._setup_logger()

    def _setup_logger(self):
        """ロガーのセットアップ"""
        # ログディレクトリ作成
        self.log_directory.mkdir(parents=True, exist_ok=True)

        # ログファイル名（日付ベース）
        log_filename = f"{datetime.now().strftime('%Y-%m-%d')}.log"
        log_filepath = self.log_directory / log_filename

        # ロガー設定
        self.logger = logging.getLogger('LootOrganizer')
        self.logger.setLevel(logging.INFO)

        # 既存のハンドラをクリア（重複回避）
        self.logger.handlers.clear()

        # ファイルハンドラ
        file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # フォーマッター
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

    def info(self, message: str):
        """INFOレベルログ"""
        if self.enable_logging:
            self.logger.info(message)

    def warning(self, message: str):
        """WARNINGレベルログ"""
        if self.enable_logging:
            self.logger.warning(message)

    def error(self, message: str):
        """ERRORレベルログ"""
        if self.enable_logging:
            self.logger.error(message)
