# -*- coding: utf-8 -*-
"""
ファイルのスキャンとフィルタリング
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from PIL import Image

from ..utils.file_utils import parse_file_size


class FileScanner:
    """
    ファイルのスキャンとフィルタリングを行うクラス

    機能:
    - パターンマッチング（ワイルドカード）
    - ファイルサイズフィルタ
    - 日付フィルタ
    - 画像解像度フィルタ
    - アスペクト比フィルタ
    - 除外パターン
    """

    def __init__(self, target_directory, logger: 'LootLogger' = None):
        """
        初期化

        Args:
            target_directory: スキャン対象ディレクトリ（文字列またはリスト）
            logger: ロガー
        """
        self.logger = logger

        # 文字列でもリストでも受け取れるように正規化
        if isinstance(target_directory, list):
            self.target_directories = [Path(d) for d in target_directory]
        else:
            self.target_directories = [Path(target_directory)]

        # 存在チェック & 警告
        self.valid_dirs = []
        self.skipped_dirs = []

        for directory in self.target_directories:
            if directory.exists():
                self.valid_dirs.append(directory)
            else:
                self.skipped_dirs.append(str(directory))
                if self.logger:
                    self.logger.warning(f"ディレクトリが存在しません（スキップします）: {directory}")

        # 1つも有効なディレクトリがない場合はエラー
        if not self.valid_dirs:
            dirs_str = ", ".join(str(d) for d in self.target_directories)
            raise FileNotFoundError(f"有効なディレクトリが見つかりません: {dirs_str}")

    def scan_files(
        self,
        pattern: str,
        filters: Dict[str, Any] = None,
        exclusions: Dict[str, List[str]] = None,
        recursive: bool = False
    ) -> List[Path]:
        """
        ファイルをスキャンしてフィルタリング

        Args:
            pattern: ファイル名パターン（ワイルドカード可）
            filters: フィルタ条件（size, date, resolution, aspect_ratio）
            exclusions: 除外条件（exact_names, patterns）
            recursive: サブディレクトリも検索するか

        Returns:
            マッチしたファイルのリスト
        """
        filters = filters or {}
        exclusions = exclusions or {'exact_names': [], 'patterns': []}

        # 複数ディレクトリをまとめてスキャン
        all_matched_files = []
        for target_dir in self.valid_dirs:
            # パターンマッチングでファイル取得
            if recursive:
                matched_files = list(target_dir.rglob(pattern))
            else:
                matched_files = list(target_dir.glob(pattern))

            # ディレクトリを除外（ファイルのみ）
            matched_files = [f for f in matched_files if f.is_file()]
            all_matched_files.extend(matched_files)

        # 除外パターンの適用
        all_matched_files = self._apply_exclusions(all_matched_files, exclusions)

        # フィルタの適用
        if filters:
            all_matched_files = self._apply_filters(all_matched_files, filters)

        return all_matched_files

    def _apply_exclusions(
        self,
        files: List[Path],
        exclusions: Dict[str, List[str]]
    ) -> List[Path]:
        """
        除外パターンを適用

        Args:
            files: ファイルリスト
            exclusions: 除外条件

        Returns:
            除外後のファイルリスト
        """
        exact_names = exclusions.get('exact_names', [])
        patterns = exclusions.get('patterns', [])

        filtered_files = []
        for file in files:
            # 完全一致での除外
            if file.name in exact_names:
                continue

            # パターンでの除外
            excluded = False
            for pattern in patterns:
                if file.match(pattern):
                    excluded = True
                    break

            if not excluded:
                filtered_files.append(file)

        return filtered_files

    def _apply_filters(
        self,
        files: List[Path],
        filters: Dict[str, Any]
    ) -> List[Path]:
        """
        フィルタを適用

        Args:
            files: ファイルリスト
            filters: フィルタ条件

        Returns:
            フィルタ後のファイルリスト
        """
        filtered_files = []

        for file in files:
            # 全てのフィルタをパスする必要がある（AND条件）
            if self._check_file_filters(file, filters):
                filtered_files.append(file)

        return filtered_files

    def _check_file_filters(self, file: Path, filters: Dict[str, Any]) -> bool:
        """
        ファイルが全フィルタ条件を満たすか確認

        Args:
            file: ファイルパス
            filters: フィルタ条件

        Returns:
            全条件を満たす場合True
        """
        # サイズフィルタ
        if 'size' in filters:
            if not self._check_size_filter(file, filters['size']):
                return False

        # 日付フィルタ
        if 'date' in filters:
            if not self._check_date_filter(file, filters['date']):
                return False

        # 解像度フィルタ
        if 'resolution' in filters:
            if not self._check_resolution_filter(file, filters['resolution']):
                return False

        # アスペクト比フィルタ
        if 'aspect_ratio' in filters:
            if not self._check_aspect_ratio_filter(file, filters['aspect_ratio']):
                return False

        return True

    def _check_size_filter(self, file: Path, size_filter: Dict[str, Any]) -> bool:
        """
        サイズフィルタのチェック

        Args:
            file: ファイルパス
            size_filter: サイズフィルタ条件（min, max）

        Returns:
            条件を満たす場合True
        """
        file_size = file.stat().st_size

        if 'min' in size_filter:
            min_size = parse_file_size(size_filter['min'])
            if file_size < min_size:
                return False

        if 'max' in size_filter:
            max_size = parse_file_size(size_filter['max'])
            if file_size > max_size:
                return False

        return True

    def _check_date_filter(self, file: Path, date_filter: Dict[str, str]) -> bool:
        """
        日付フィルタのチェック

        Args:
            file: ファイルパス
            date_filter: 日付フィルタ条件（after, before）

        Returns:
            条件を満たす場合True
        """
        file_mtime = datetime.fromtimestamp(file.stat().st_mtime)

        if 'after' in date_filter:
            after_date = datetime.strptime(date_filter['after'], '%Y-%m-%d')
            if file_mtime < after_date:
                return False

        if 'before' in date_filter:
            before_date = datetime.strptime(date_filter['before'], '%Y-%m-%d')
            if file_mtime >= before_date:
                return False

        return True

    def _check_resolution_filter(
        self,
        file: Path,
        resolution_filter: Dict[str, int]
    ) -> bool:
        """
        解像度フィルタのチェック（画像ファイルのみ）

        Args:
            file: ファイルパス
            resolution_filter: 解像度フィルタ条件（min_width, max_width, min_height, max_height）

        Returns:
            条件を満たす場合True（画像でない場合はスキップ）
        """
        try:
            with Image.open(file) as img:
                width, height = img.size

                if 'min_width' in resolution_filter:
                    if width < resolution_filter['min_width']:
                        return False

                if 'max_width' in resolution_filter:
                    if width > resolution_filter['max_width']:
                        return False

                if 'min_height' in resolution_filter:
                    if height < resolution_filter['min_height']:
                        return False

                if 'max_height' in resolution_filter:
                    if height > resolution_filter['max_height']:
                        return False

                return True

        except Exception as e:
            # 画像として開けない場合はスキップ（ログに記録）
            if self.logger:
                self.logger.warning(
                    f"{file.name}: 画像として開けませんでした（解像度フィルタをスキップ） - {e}"
                )
            return False

    def _check_aspect_ratio_filter(
        self,
        file: Path,
        aspect_filter: Dict[str, float]
    ) -> bool:
        """
        アスペクト比フィルタのチェック（画像ファイルのみ）

        Args:
            file: ファイルパス
            aspect_filter: アスペクト比フィルタ条件
                          （vertical_min, horizontal_max, square_tolerance）

        Returns:
            条件を満たす場合True（画像でない場合はスキップ）
        """
        try:
            with Image.open(file) as img:
                width, height = img.size
                aspect_ratio = height / width  # 縦/横

                # 縦長チェック（vertical_min: 縦横比の最小値）
                if 'vertical_min' in aspect_filter:
                    if aspect_ratio < aspect_filter['vertical_min']:
                        return False

                # 横長チェック（horizontal_max: 縦横比の最大値）
                if 'horizontal_max' in aspect_filter:
                    if aspect_ratio > aspect_filter['horizontal_max']:
                        return False

                # 正方形チェック（square_tolerance: 1.0からの許容範囲）
                if 'square_tolerance' in aspect_filter:
                    tolerance = aspect_filter['square_tolerance']
                    if not (1.0 - tolerance <= aspect_ratio <= 1.0 + tolerance):
                        return False

                return True

        except Exception as e:
            # 画像として開けない場合はスキップ（ログに記録）
            if self.logger:
                self.logger.warning(
                    f"{file.name}: 画像として開けませんでした（アスペクト比フィルタをスキップ） - {e}"
                )
            return False
