# -*- coding: utf-8 -*-
"""
PNG_Prompt_Sort モードの処理ハンドラー
AI生成画像をメタデータのLoRA情報で振り分け
"""

import os
import re
import yaml
import questionary
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from tqdm import tqdm
from PIL import Image

from ..core.file_scanner import FileScanner
from ..core.preview_generator import FileOperation
from ..utils.file_executor import execute_file_op, operation_log_message
from ..utils.path_utils import to_path
from .base_handler import BaseHandler


class PngPromptSortModeHandler(BaseHandler):
    """
    PNG_Prompt_Sort モードの処理を行うクラス

    機能:
    - 画像ファイルのメタデータ（PNG info等）からLoRA名を抽出
    - マッピングテーブルに基づいて振り分け先を決定
    - 最初にマッチしたLoRAのフォルダに移動
    - 重複ファイル処理オプション（上書き/連番/確認/スキップ）
    """

    MODE = "PNG_Prompt_Sort"
    REQUIRES_SCANNER = False
    REQUIRED_SETTINGS = ("source_directories", "output_directory", "mapping_file")

    def __init__(
        self,
        config: Dict,
        scanner: Optional[FileScanner],
        logger,
        config_loader=None,
        planning_context=None,
    ):
        """
        初期化

        Args:
            config: 設定辞書
            scanner: ファイルスキャナー（PNG_Prompt_Sortでは未使用）
            logger: ロガー
        """
        super().__init__(
            config=config,
            scanner=scanner,
            logger=logger,
            config_loader=config_loader,
            planning_context=planning_context,
        )
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

        mapping_path = to_path(mapping_file)

        # 相対パスの場合はプロジェクトルートからの相対
        if not mapping_path.is_absolute():
            script_dir = Path(__file__).parent.parent.parent  # src/handlers/ の2階層上
            mapping_path = script_dir / mapping_path

        if not mapping_path.exists():
            self.logger.error(f"マッピングファイルが見つかりません: {mapping_path}")
            return None

        try:
            with open(mapping_path, 'r', encoding='utf-8') as f:
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
            metadata_path = image_path
            if self.planning_context is not None:
                metadata_path = self.planning_context.backing_path(image_path)
            with Image.open(metadata_path) as img:
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

    def _get_unique_filename(
        self,
        dest_dir: Path,
        filename: str,
        *,
        planned_state: bool = True,
    ) -> str:
        """
        重複しないファイル名を生成（連番付与）

        Args:
            dest_dir: 保存先ディレクトリ
            filename: 元のファイル名

        Returns:
            重複しないファイル名
        """
        dest_path = dest_dir / filename
        if planned_state:
            destination_exists = self.planning_context.is_file
        else:
            destination_exists = Path.exists

        if not destination_exists(dest_path):
            return filename

        # 拡張子を分離
        name_part, ext_part = os.path.splitext(filename)

        # 連番を付与
        counter = 1
        while True:
            new_filename = f"{name_part}_{counter}{ext_part}"
            new_path = dest_dir / new_filename
            if not destination_exists(new_path):
                return new_filename
            counter += 1

    def _append_planned_operation(
        self,
        operations: List[FileOperation],
        operation: FileOperation,
    ) -> None:
        """重複方針を確定してから仮想状態へ反映する。"""
        duplicate_handling = self.settings.get('duplicate_handling', 'overwrite')
        destination = operation.destination
        operation.skip_if_exists = duplicate_handling == 'skip'

        if destination is not None and self.planning_context.is_file(destination):
            if duplicate_handling == 'skip':
                self.logger.info(
                    f"スキップ: {operation.source} "
                    f"(保存先が既に存在します: {destination})"
                )
                return
            if duplicate_handling == 'sequential':
                unique_filename = self._get_unique_filename(
                    destination.parent,
                    destination.name,
                )
                operation.destination = destination.parent / unique_filename

        operations.append(operation)
        self._record_planned_operations([operation])

    def plan_operations(self) -> List[FileOperation]:
        """
        ファイル操作を計画

        Returns:
            FileOperationのリスト
        """
        self._start_planning()

        if self.lora_map is None:
            self.logger.error("マッピングファイルが読み込まれていないため、処理を中止します")
            return []

        operations = []

        # 入力ディレクトリのリストを取得
        source_dirs = self.settings.get('source_directories', [])
        if isinstance(source_dirs, str):
            source_dirs = [source_dirs]

        # 出力親ディレクトリ
        output_dir = to_path(self.settings['output_directory'])

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
            source_dir = to_path(source_dir_str)

            if not self.planning_context.directory_exists(source_dir):
                self.logger.warning(f"入力ディレクトリが存在しません: {source_dir}")
                continue

            self.logger.info(f"スキャン中: {source_dir}")

            # このディレクトリ用の一時スキャナーを作成
            temp_scanner = FileScanner(
                str(source_dir),
                self.logger,
                planning_context=self.planning_context,
            )

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
                        self._append_planned_operation(operations, FileOperation(
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
                        self._append_planned_operation(operations, FileOperation(
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
                        self._append_planned_operation(operations, FileOperation(
                            source=file_path,
                            destination=dest_folder / file_path.name,
                            action='move',
                            reason=f'未登録LoRA: {loras[0]}'
                        ))
                    else:
                        # 最初のマッチフォルダに移動のみ
                        folder_name, lora_name = matched_folders[0]
                        dest_folder = output_dir / folder_name
                        self._append_planned_operation(operations, FileOperation(
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
        ask の単独実行だけ、従来どおり実行時に選択する。

        Args:
            operations: ファイル操作のリスト
            dry_run: ドライランモード

        Returns:
            (成功数, 失敗数)
        """
        duplicate_handling = self.settings.get('duplicate_handling', 'overwrite')
        if duplicate_handling != 'ask':
            return super().execute_operations(operations, dry_run=dry_run)

        success_count = 0
        failure_count = 0
        skip_count = 0

        for op in tqdm(operations, desc="処理中", unit="files"):
            try:
                if not dry_run:
                    final_dest = op.destination

                    if final_dest.exists():
                        answer = questionary.select(
                            f"ファイルが既に存在します: {final_dest.name}",
                            choices=["上書き", "連番付与", "スキップ"]
                        ).ask()

                        if answer == "連番付与":
                            unique_filename = self._get_unique_filename(
                                op.destination.parent,
                                op.destination.name,
                                planned_state=False,
                            )
                            final_dest = op.destination.parent / unique_filename
                        elif answer != "上書き":
                            self.logger.info(
                                f"スキップ: {op.source.name} (ユーザー選択)"
                            )
                            skip_count += 1
                            continue

                    planned_destination = op.destination
                    op.destination = final_dest
                    try:
                        execute_file_op(op)
                        self.logger.info(operation_log_message(op))
                    finally:
                        op.destination = planned_destination
                    success_count += 1
                else:
                    self.logger.info(operation_log_message(op, dry_run=True))
                    success_count += 1

            except Exception as e:
                self.logger.error(f"移動失敗 ({op.source.name}): {e}")
                failure_count += 1

        if skip_count > 0:
            self.logger.info(f"スキップ: {skip_count}件")

        return success_count, failure_count
