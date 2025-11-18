# -*- coding: utf-8 -*-
"""
PNG_Prompt_Sort モードの処理ハンドラー
AI生成画像をメタデータのLoRA情報で振り分け
"""

import os
import re
import shutil
import yaml
import questionary
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from tqdm import tqdm
from PIL import Image

from ..core.file_scanner import FileScanner
from ..core.logger import LootLogger
from ..core.preview_generator import FileOperation


class PngPromptSortModeHandler:
    """
    PNG_Prompt_Sort モードの処理を行うクラス

    機能:
    - 画像ファイルのメタデータ（PNG info等）からLoRA名を抽出
    - マッピングテーブルに基づいて振り分け先を決定
    - 最初にマッチしたLoRAのフォルダに移動
    - 重複ファイル処理オプション（上書き/連番/確認/スキップ）
    """

    def __init__(
        self,
        config: Dict[str, Any],
        scanner: Optional[FileScanner],
        logger: LootLogger
    ):
        """
        初期化

        Args:
            config: 設定辞書
            scanner: ファイルスキャナー（PNG_Prompt_Sortでは未使用）
            logger: ロガー
        """
        self.config = config
        self.scanner = scanner
        self.logger = logger
        self.settings = config['settings']

        # マッピングファイル読み込み
        self.lora_map = self._load_lora_map()

        # メタデータ設定
        self.metadata_config = config.get('metadata', {})
        self.metadata_fields = self.metadata_config.get(
            'fields',
            ['parameters', 'Comment', 'Description', 'prompt']
        )
        self.lora_pattern = re.compile(
            self.metadata_config.get('lora_pattern', r"<lora:([^:]+):[^>]+>"),
            re.IGNORECASE
        )

    def _load_lora_map(self) -> Optional[Dict[str, str]]:
        """
        lora_map.yamlを読み込む

        Returns:
            {lora名(小文字・空白除去): フォルダ名} の辞書、失敗時はNone
        """
        mapping_file = self.settings.get('mapping_file')
        if not mapping_file:
            self.logger.error("設定エラー: mapping_file が指定されていません")
            return None

        # 相対パスの場合はプロジェクトルートからの相対
        if not os.path.isabs(mapping_file):
            script_dir = Path(__file__).parent.parent.parent  # src/handlers/ の2階層上
            mapping_file = script_dir / mapping_file
        else:
            mapping_file = Path(mapping_file)

        if not mapping_file.exists():
            self.logger.error(f"マッピングファイルが見つかりません: {mapping_file}")
            return None

        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            mappings = data.get('mappings', {})
            # 大文字小文字・空白を無視した辞書を作成
            normalized_map = {}
            for lora_name, folder_name in mappings.items():
                # 空白除去＆小文字化
                key = re.sub(r'\s', '', lora_name).lower()
                normalized_map[key] = folder_name

            self.logger.info(f"マッピングファイルを読み込みました: {len(normalized_map)}件")
            return normalized_map

        except Exception as e:
            self.logger.error(f"マッピングファイルの読み込みに失敗: {e}")
            return None

    def _extract_metadata(self, image_path: Path) -> Optional[str]:
        """
        画像ファイルからメタデータを抽出

        Args:
            image_path: 画像ファイルのパス

        Returns:
            メタデータ文字列、失敗時はNone
        """
        try:
            with Image.open(image_path) as img:
                # 複数フィールドを順番に確認
                for field in self.metadata_fields:
                    if field in img.info:
                        metadata = img.info[field]
                        # bytes型の場合はデコード
                        if isinstance(metadata, bytes):
                            metadata = metadata.decode('utf-8', errors='ignore')
                        return metadata
                return None
        except Exception as e:
            self.logger.warning(f"メタデータ読み取り失敗 ({image_path.name}): {e}")
            return None

    def _find_loras(self, metadata: str) -> List[str]:
        """
        メタデータからLoRA名を抽出

        Args:
            metadata: メタデータ文字列

        Returns:
            検出されたLoRA名のリスト
        """
        matches = self.lora_pattern.findall(metadata)
        return matches

    def _get_unique_filename(self, dest_dir: Path, filename: str) -> str:
        """
        重複しないファイル名を生成（連番付与）

        Args:
            dest_dir: 保存先ディレクトリ
            filename: 元のファイル名

        Returns:
            重複しないファイル名
        """
        dest_path = dest_dir / filename
        if not dest_path.exists():
            return filename

        # 拡張子を分離
        name_part, ext_part = os.path.splitext(filename)

        # 連番を付与
        counter = 1
        while True:
            new_filename = f"{name_part}_{counter}{ext_part}"
            new_path = dest_dir / new_filename
            if not new_path.exists():
                return new_filename
            counter += 1

    def plan_operations(self) -> List[FileOperation]:
        """
        ファイル操作を計画

        Returns:
            FileOperationのリスト
        """
        if self.lora_map is None:
            self.logger.error("マッピングファイルが読み込まれていないため、処理を中止します")
            return []

        operations = []

        # 入力ディレクトリのリストを取得
        source_dirs = self.settings.get('source_directories', [])
        if isinstance(source_dirs, str):
            source_dirs = [source_dirs]

        # 出力親ディレクトリ
        output_dir = Path(self.settings['output_directory'])

        # 特殊フォルダ名
        unknown_folder = self.settings.get('unknown_lora_folder', '__unknown_lora')
        no_lora_folder = self.settings.get('no_lora_folder', '__no_lora_found')
        error_folder = self.settings.get('metadata_error_folder', '__metadata_error')

        # 対象拡張子
        target_extensions = self.settings.get(
            'target_extensions',
            ['png', 'jpg', 'jpeg', 'webp']
        )

        # 各入力ディレクトリを処理
        for source_dir_str in source_dirs:
            source_dir = Path(source_dir_str)

            if not source_dir.exists():
                self.logger.warning(f"入力ディレクトリが存在しません: {source_dir}")
                continue

            self.logger.info(f"スキャン中: {source_dir}")

            # このディレクトリ用の一時スキャナーを作成
            temp_scanner = FileScanner(str(source_dir), self.logger)

            # 拡張子ごとにスキャン
            for ext in target_extensions:
                pattern = f"*.{ext}"
                matched_files = temp_scanner.scan_files(pattern=pattern, recursive=False)

                for file_path in matched_files:
                    # メタデータ抽出
                    metadata = self._extract_metadata(file_path)

                    if metadata is None:
                        # メタデータ読み取り失敗
                        dest_folder = output_dir / error_folder
                        operations.append(FileOperation(
                            source=file_path,
                            destination=dest_folder / file_path.name,
                            action='move',
                            reason='メタデータ読み取り失敗'
                        ))
                        continue

                    # LoRA検出
                    loras = self._find_loras(metadata)

                    if not loras:
                        # LoRA未検出
                        dest_folder = output_dir / no_lora_folder
                        operations.append(FileOperation(
                            source=file_path,
                            destination=dest_folder / file_path.name,
                            action='move',
                            reason='LoRA未検出'
                        ))
                        continue

                    # マッピング照合
                    matched_folders = []
                    for lora_name in loras:
                        # 正規化
                        normalized_lora = re.sub(r'\s', '', lora_name).lower()

                        if normalized_lora in self.lora_map:
                            folder_name = self.lora_map[normalized_lora]
                            matched_folders.append((folder_name, lora_name))

                    if not matched_folders:
                        # マッピングにない
                        dest_folder = output_dir / unknown_folder
                        operations.append(FileOperation(
                            source=file_path,
                            destination=dest_folder / file_path.name,
                            action='move',
                            reason=f'未登録LoRA: {loras[0]}'
                        ))
                    else:
                        # 最初のマッチフォルダに移動のみ
                        folder_name, lora_name = matched_folders[0]
                        dest_folder = output_dir / folder_name
                        operations.append(FileOperation(
                            source=file_path,
                            destination=dest_folder / file_path.name,
                            action='move',
                            reason=f'LoRA: {lora_name}'
                        ))

        return operations

    def execute_operations(
        self,
        operations: List[FileOperation],
        dry_run: bool = False
    ) -> Tuple[int, int]:
        """
        操作を実行（移動のみ）

        Args:
            operations: ファイル操作のリスト
            dry_run: ドライランモード

        Returns:
            (成功数, 失敗数)
        """
        success_count = 0
        failure_count = 0
        skip_count = 0

        # 重複処理方法を取得
        duplicate_handling = self.settings.get('duplicate_handling', 'overwrite')

        # 操作実行
        for op in tqdm(operations, desc="処理中", unit="files"):
            try:
                if not dry_run:
                    # 保存先ディレクトリ作成
                    op.destination.parent.mkdir(parents=True, exist_ok=True)

                    # 重複チェック＆処理
                    final_dest = op.destination.parent / op.destination.name

                    if final_dest.exists():
                        if duplicate_handling == 'overwrite':
                            # 上書き：そのまま移動（既存ファイルが置き換えられる）
                            pass
                        elif duplicate_handling == 'sequential':
                            # 連番付与
                            unique_filename = self._get_unique_filename(
                                op.destination.parent,
                                op.destination.name
                            )
                            final_dest = op.destination.parent / unique_filename
                        elif duplicate_handling == 'ask':
                            # 毎回尋ねる
                            answer = questionary.select(
                                f"ファイルが既に存在します: {final_dest.name}",
                                choices=[
                                    "上書き",
                                    "連番付与",
                                    "スキップ"
                                ]
                            ).ask()

                            if answer == "上書き":
                                pass
                            elif answer == "連番付与":
                                unique_filename = self._get_unique_filename(
                                    op.destination.parent,
                                    op.destination.name
                                )
                                final_dest = op.destination.parent / unique_filename
                            else:  # スキップ
                                self.logger.info(
                                    f"スキップ: {op.source.name} (ユーザー選択)"
                                )
                                skip_count += 1
                                continue
                        elif duplicate_handling == 'skip':
                            # スキップ
                            self.logger.info(f"スキップ: {op.source.name} (重複ファイル)")
                            skip_count += 1
                            continue

                    # 移動実行
                    shutil.move(op.source, final_dest)
                    self.logger.info(
                        f"移動: {op.source.name} -> "
                        f"{op.destination.parent.name}/{final_dest.name}"
                    )
                    success_count += 1
                else:
                    self.logger.info(
                        f"[DRY-RUN] 移動: {op.source.name} -> "
                        f"{op.destination.parent.name}"
                    )
                    success_count += 1

            except Exception as e:
                self.logger.error(f"移動失敗 ({op.source.name}): {e}")
                failure_count += 1

        if skip_count > 0:
            self.logger.info(f"スキップ: {skip_count}件")

        return success_count, failure_count
