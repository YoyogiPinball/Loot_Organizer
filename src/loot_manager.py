#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Loot Organizer - ファイル整理ツール
個人用ファイル整理ツール - 2段階ワークフローによるファイル管理システム

Author: YoyogiPinball
License: Free to use for personal and commercial purposes
"""

import os
import sys
import yaml
import shutil
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

# サードパーティライブラリ
try:
    import questionary
    from colorama import init, Fore, Back, Style
    from PIL import Image
    from tqdm import tqdm
except ImportError as e:
    # coloramaがインポートできない場合もあるので直接ANSIコードを使用
    print(f"\033[91m必要なライブラリがインストールされていません: {e}\033[0m")
    print(f"\033[93mpip install -r requirements.txt を実行してください\033[0m")
    sys.exit(1)

# Windows環境でのUTF-8出力対応
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# colorama初期化（Windows対応）
init(autoreset=True)

# =====================================
# カラーテーマ: Corpo風（cyberpunk風）
# =====================================
# C案レベル3: シアン×ブルー×イエローの洗練されたサイバーパンク
class Colors:
    """カラーパレット - Corpo風"""
    # ネオンカラー
    NEON_CYAN = Fore.CYAN + Style.BRIGHT        # ボーダー、フレーム
    NEON_BLUE = Fore.BLUE + Style.BRIGHT        # タイトル、ヘッダー
    NEON_YELLOW = Fore.YELLOW + Style.BRIGHT    # 選択項目、ハイライト
    NEON_GREEN = Fore.GREEN + Style.BRIGHT      # 成功メッセージ
    NEON_RED = Fore.RED + Style.BRIGHT          # エラーメッセージ

    # 通常カラー
    CYAN = Fore.CYAN
    YELLOW = Fore.YELLOW

    # リセット
    RESET = Style.RESET_ALL


# =====================================
# データクラス
# =====================================

@dataclass
class PresetMeta:
    """プリセットのメタ情報"""
    name: str
    icon: str
    mode: str  # "Sort" or "Clean"
    description: str
    file_path: str


@dataclass
class FileOperation:
    """ファイル操作を表すデータクラス"""
    source: Path
    destination: Optional[Path]
    action: str  # "move", "copy", "delete"
    reason: str  # ルールの説明


# =====================================
# ConfigLoader - 設定ファイル読み込みとバリデーション
# =====================================

class ConfigLoader:
    """
    YAML設定ファイルを読み込み、バリデーションを行うクラス

    機能:
    - YAMLファイルのパース
    - 必須フィールドの検証
    - デフォルト値の適用
    - プリセット自動検出
    """

    def __init__(self, configs_dir: str = "configs"):
        """
        初期化

        Args:
            configs_dir: 設定ファイルディレクトリのパス
        """
        self.configs_dir = Path(configs_dir)
        self.logger = logging.getLogger(__name__)

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        設定ファイルを読み込む

        Args:
            config_path: 設定ファイルのパス

        Returns:
            設定内容の辞書

        Raises:
            FileNotFoundError: ファイルが存在しない
            yaml.YAMLError: YAML形式が不正
            ValueError: 必須フィールドが不足
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"YAML形式が不正です: {e}")

        # バリデーション
        self._validate_config(config, config_path)

        # デフォルト値の適用
        config = self._apply_defaults(config)

        return config

    def _validate_config(self, config: Dict[str, Any], config_path: Path):
        """
        設定ファイルのバリデーション

        Args:
            config: 設定内容
            config_path: 設定ファイルのパス

        Raises:
            ValueError: バリデーションエラー
        """
        # metaセクションの検証
        if 'meta' not in config:
            raise ValueError(f"{config_path}: 'meta'セクションが必要です")

        meta = config['meta']
        required_meta_fields = ['name', 'icon', 'mode', 'description']
        for field in required_meta_fields:
            if field not in meta:
                raise ValueError(f"{config_path}: meta.{field} が必要です")

        # modeの検証
        if meta['mode'] not in ['Sort', 'Clean', 'PNG_Prompt_Sort']:
            raise ValueError(f"{config_path}: meta.mode は 'Sort', 'Clean', または 'PNG_Prompt_Sort' である必要があります")

        # settingsセクションの検証
        if 'settings' not in config:
            raise ValueError(f"{config_path}: 'settings'セクションが必要です")

        settings = config['settings']

        # モード別の必須フィールド検証
        if meta['mode'] in ['Sort', 'Clean']:
            if 'target_directory' not in settings:
                raise ValueError(f"{config_path}: settings.target_directory が必要です")
        elif meta['mode'] == 'PNG_Prompt_Sort':
            if 'source_directories' not in settings:
                raise ValueError(f"{config_path}: settings.source_directories が必要です")
            if 'output_directory' not in settings:
                raise ValueError(f"{config_path}: settings.output_directory が必要です")
            if 'mapping_file' not in settings:
                raise ValueError(f"{config_path}: settings.mapping_file が必要です")

        # モード別の検証
        if meta['mode'] == 'Sort':
            if 'move_rules' not in config or not config['move_rules']:
                raise ValueError(f"{config_path}: Sort モードには 'move_rules' が必要です")

        elif meta['mode'] == 'Clean':
            # Cleanモードは deletion, cleanup, sorting_rules のいずれかが必要
            has_operations = any(key in config for key in ['deletion', 'cleanup', 'sorting_rules'])
            if not has_operations:
                raise ValueError(
                    f"{config_path}: Clean モードには 'deletion', 'cleanup', "
                    "'sorting_rules' のいずれかが必要です"
                )

    def _apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        デフォルト値を適用

        Args:
            config: 設定内容

        Returns:
            デフォルト値適用済みの設定
        """
        # settingsのデフォルト値
        settings = config['settings']
        settings.setdefault('enable_logging', True)
        settings.setdefault('confirm_before_execute', True)
        settings.setdefault('dry_run_default', True)

        # previewのデフォルト値
        if 'preview' not in settings:
            settings['preview'] = {}
        settings['preview'].setdefault('mode', 'head')
        settings['preview'].setdefault('count', 5)

        # loggingのデフォルト値
        if 'logging' not in settings:
            settings['logging'] = {}
        settings['logging'].setdefault('log_success', True)
        settings['logging'].setdefault('log_directory', 'logs')

        # Sortモードのデフォルト値
        if config['meta']['mode'] == 'Sort':
            if 'exclusions' not in config:
                config['exclusions'] = {}
            config['exclusions'].setdefault('exact_names', [])
            config['exclusions'].setdefault('patterns', [])

        # Cleanモードのデフォルト値
        elif config['meta']['mode'] == 'Clean':
            if 'deletion' in config:
                config['deletion'].setdefault('enabled', False)
                config['deletion'].setdefault('recursive', True)
                config['deletion'].setdefault('strings', [])

            if 'cleanup' in config:
                config['cleanup'].setdefault('enabled', False)
                config['cleanup'].setdefault('recursive', True)
                config['cleanup'].setdefault('custom_patterns', [])

            if 'sorting_rules' not in config:
                config['sorting_rules'] = []

        return config

    def discover_presets(self) -> List[PresetMeta]:
        """
        configs/ ディレクトリからプリセットを自動検出

        Returns:
            検出されたプリセットのリスト
        """
        presets = []

        if not self.configs_dir.exists():
            self.logger.warning(f"設定ディレクトリが見つかりません: {self.configs_dir}")
            return presets

        # configs/直下のYAMLファイルを検索（samples/内とlora_map*.yamlは除外）
        for yaml_file in self.configs_dir.glob("*.yaml"):
            # lora_map*.yamlはマッピングファイルなのでスキップ
            if yaml_file.name.startswith('lora_map'):
                continue

            try:
                config = self.load_config(yaml_file)
                meta = config['meta']

                preset = PresetMeta(
                    name=meta['name'],
                    icon=meta['icon'],
                    mode=meta['mode'],
                    description=meta['description'],
                    file_path=str(yaml_file)
                )
                presets.append(preset)

            except Exception as e:
                self.logger.warning(f"{yaml_file} の読み込みに失敗: {e}")
                continue

        return presets


# =====================================
# Logger設定
# =====================================

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


# =====================================
# ユーティリティ関数
# =====================================

def parse_file_size(size_str: str) -> int:
    """
    ファイルサイズ文字列をバイト数に変換

    Args:
        size_str: サイズ文字列（例: "10MB", "1.5GB", "1024"）

    Returns:
        バイト数
    """
    if isinstance(size_str, int):
        return size_str

    size_str = str(size_str).strip().upper()

    # 単位の抽出
    units = {
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3,
        'TB': 1024 ** 4,
    }

    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            number_part = size_str[:-len(unit)].strip()
            try:
                return int(float(number_part) * multiplier)
            except ValueError:
                raise ValueError(f"不正なサイズ形式: {size_str}")

    # 単位なし（バイト数と解釈）
    try:
        return int(size_str)
    except ValueError:
        raise ValueError(f"不正なサイズ形式: {size_str}")


def format_file_size(size_bytes: int) -> str:
    """
    バイト数を人間が読みやすい形式に変換

    Args:
        size_bytes: バイト数

    Returns:
        フォーマット済み文字列（例: "10.5 MB"）
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def clean_filename(filename: str, custom_patterns: List[str] = None) -> str:
    """
    ファイル名から絵文字や特殊文字を除去

    Args:
        filename: 元のファイル名
        custom_patterns: カスタム除去パターン（正規表現）

    Returns:
        クリーンアップ済みファイル名
    """
    # 拡張子を分離
    name_part, ext_part = os.path.splitext(filename)

    # デフォルトパターン: 絵文字、特殊記号の除去
    # 基本的な絵文字範囲（Unicode範囲）
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # 顔文字
        "\U0001F300-\U0001F5FF"  # シンボル＆絵文字
        "\U0001F680-\U0001F6FF"  # 乗り物＆地図シンボル
        "\U0001F1E0-\U0001F1FF"  # 国旗
        "\U00002702-\U000027B0"  # 装飾記号
        "\U000024C2-\U0001F251"  # 囲み文字
        "]+",
        flags=re.UNICODE
    )
    name_part = emoji_pattern.sub('', name_part)

    # カスタムパターンの適用
    if custom_patterns:
        for pattern in custom_patterns:
            try:
                name_part = re.sub(pattern, '', name_part)
            except re.error as e:
                logging.warning(f"不正な正規表現パターン '{pattern}': {e}")

    # 連続する空白を1つに、前後の空白を削除
    name_part = re.sub(r'\s+', ' ', name_part).strip()

    # 空文字列になった場合のフォールバック
    if not name_part:
        name_part = "cleaned_file"

    return name_part + ext_part


# =====================================
# FileScanner - ファイルスキャンとフィルタリング
# =====================================

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

    def __init__(self, target_directory: str, logger: LootLogger = None):
        """
        初期化

        Args:
            target_directory: スキャン対象ディレクトリ
            logger: ロガー
        """
        self.target_directory = Path(target_directory)
        self.logger = logger

        if not self.target_directory.exists():
            raise FileNotFoundError(f"ディレクトリが見つかりません: {target_directory}")

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

        # パターンマッチングでファイル取得
        if recursive:
            matched_files = list(self.target_directory.rglob(pattern))
        else:
            matched_files = list(self.target_directory.glob(pattern))

        # ディレクトリを除外（ファイルのみ）
        matched_files = [f for f in matched_files if f.is_file()]

        # 除外パターンの適用
        matched_files = self._apply_exclusions(matched_files, exclusions)

        # フィルタの適用
        if filters:
            matched_files = self._apply_filters(matched_files, filters)

        return matched_files

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


# =====================================
# PreviewGenerator - プレビュー表示生成
# =====================================

class PreviewGenerator:
    """
    ファイル操作のプレビュー表示を生成するクラス

    機能:
    - head/tail/both/all モード対応
    - 移動先ごとのグループ化表示
    - 件数サマリー
    """

    def __init__(self, config: Dict[str, Any] = None, preview_mode: str = "head", preview_count: int = 5):
        """
        初期化

        Args:
            config: 設定辞書（クリーンアップパターン表示用）
            preview_mode: プレビューモード（head/tail/both/all）
            preview_count: 表示件数（head/tail/bothの場合）
        """
        self.config = config or {}
        self.preview_mode = preview_mode
        self.preview_count = preview_count

    def generate_preview(
        self,
        operations: List[FileOperation],
        mode: str = "Sort"
    ) -> str:
        """
        プレビュー文字列を生成

        Args:
            operations: ファイル操作のリスト
            mode: モード（"Sort", "Clean", または "PNG_Prompt_Sort"）

        Returns:
            プレビュー文字列
        """
        if not operations:
            return f"{Colors.NEON_YELLOW}処理対象のファイルがありません{Colors.RESET}"

        # PNG_Prompt_Sort専用プレビュー
        if mode == "PNG_Prompt_Sort":
            return self._generate_png_prompt_sort_preview(operations)

        # 操作をグループ化（destination別、またはaction別）
        grouped = self._group_operations(operations, mode)

        # プレビュー生成
        preview_lines = []
        preview_lines.append(f"{Colors.NEON_CYAN}╔════════════════════════════════════════════╗")
        preview_lines.append(f"{Colors.NEON_BLUE}║  📋 処理対象プレビュー                    ║")
        preview_lines.append(f"{Colors.NEON_CYAN}╠════════════════════════════════════════════╣{Colors.RESET}")
        preview_lines.append("")

        # クリーンアップ操作がある場合、対象パターンを表示
        if mode == "Clean" and any(op.action == 'cleanup' for op in operations):
            cleanup_info = self._get_cleanup_patterns_description()
            if cleanup_info:
                preview_lines.append(f"{Colors.NEON_YELLOW}🧹 クリーンアップ対象パターン:{Colors.RESET}")
                for line in cleanup_info:
                    preview_lines.append(f"{Colors.NEON_CYAN}  {line}{Colors.RESET}")
                preview_lines.append("")
                preview_lines.append(f"{Colors.CYAN}{'─' * 44}{Colors.RESET}")
                preview_lines.append("")

        total_count = 0

        for group_key, group_ops in grouped.items():
            count = len(group_ops)
            total_count += count

            # グループヘッダー
            if mode == "Sort":
                action_icon = "📁"
                header = f"{action_icon} {group_key} ({count}件)"
            else:  # Clean
                action_icon = self._get_action_icon(group_ops[0].action)
                header = f"{action_icon} {group_key} ({count}件)"

            preview_lines.append(f"{Colors.NEON_CYAN}{header}{Colors.RESET}")

            # ファイルリスト表示
            files_to_show = self._select_files_to_show(group_ops)

            for op in files_to_show:
                # 削除アクションは赤色で強調表示、その他は青色
                if op.action == 'delete':
                    preview_lines.append(f"{Colors.NEON_RED}  ├─ {op.source.name}{Colors.RESET}")
                else:
                    preview_lines.append(f"{Colors.NEON_BLUE}  ├─ {op.source.name}{Colors.RESET}")

            # 省略表示
            omitted = count - len(files_to_show)
            if omitted > 0:
                if group_ops[0].action == 'delete':
                    preview_lines.append(f"{Colors.NEON_RED}  └─ ... 他{omitted}件{Colors.RESET}")
                else:
                    preview_lines.append(f"{Colors.NEON_BLUE}  └─ ... 他{omitted}件{Colors.RESET}")

            preview_lines.append("")

        # サマリー
        preview_lines.append(f"{Colors.CYAN}{'─' * 44}{Colors.RESET}")
        preview_lines.append(f"{Colors.NEON_YELLOW}合計: {total_count}件{Colors.RESET}")
        preview_lines.append("")

        return "\n".join(preview_lines)

    def _group_operations(
        self,
        operations: List[FileOperation],
        mode: str = "Sort"
    ) -> Dict[str, List[FileOperation]]:
        """
        操作をグループ化

        Args:
            operations: ファイル操作のリスト
            mode: モード

        Returns:
            グループ化された操作（key: destination or action）
        """
        grouped = {}

        for op in operations:
            # グループキーの決定
            if op.action == "delete":
                key = f"削除（{op.reason}）"
            elif op.action == "cleanup":
                key = f"クリーンアップ（{op.reason}）"
            elif op.destination:
                key = str(op.destination)
            else:
                key = op.action

            if key not in grouped:
                grouped[key] = []

            grouped[key].append(op)

        return grouped

    def _select_files_to_show(
        self,
        operations: List[FileOperation]
    ) -> List[FileOperation]:
        """
        表示するファイルを選択（preview_modeに基づく）

        Args:
            operations: ファイル操作のリスト

        Returns:
            表示対象のファイル操作リスト
        """
        # 削除アクションは常に全件表示（重要な操作のため）
        if operations and operations[0].action == 'delete':
            return operations

        if self.preview_mode == "all":
            return operations

        count = len(operations)

        if self.preview_mode == "head":
            return operations[:self.preview_count]

        elif self.preview_mode == "tail":
            return operations[-self.preview_count:]

        elif self.preview_mode == "both":
            if count <= self.preview_count * 2:
                return operations
            else:
                return operations[:self.preview_count] + operations[-self.preview_count:]

        return operations

    def _get_action_icon(self, action: str) -> str:
        """
        アクションに対応するアイコンを取得

        Args:
            action: アクション名

        Returns:
            絵文字アイコン
        """
        icons = {
            'move': '📦',
            'copy': '📋',
            'delete': '🗑️',
            'cleanup': '✨'
        }
        return icons.get(action, '📄')

    def _get_cleanup_patterns_description(self) -> List[str]:
        """
        クリーンアップで除去される文字パターンの説明を生成

        Returns:
            パターン説明のリスト
        """
        descriptions = []

        # デフォルトパターンの説明
        descriptions.append("📌 デフォルト除去パターン:")
        descriptions.append("  ├─ 絵文字（顔文字、シンボル、乗り物、国旗など）")
        descriptions.append("  ├─ 装飾記号（U+2702～U+27B0）")
        descriptions.append("  ├─ 囲み文字（U+24C2～U+1F251）")
        descriptions.append("  └─ 連続する空白 → 単一スペース化")

        # カスタムパターンがあれば表示
        if 'cleanup' in self.config:
            custom_patterns = self.config['cleanup'].get('custom_patterns', [])
            if custom_patterns:
                descriptions.append("")
                descriptions.append("📌 カスタム除去パターン (正規表現):")
                for i, pattern in enumerate(custom_patterns, 1):
                    descriptions.append(f"  [{i}] {pattern}")

        return descriptions

    def _generate_png_prompt_sort_preview(self, operations: List[FileOperation]) -> str:
        """
        PNG_Prompt_Sort専用のプレビュー生成

        Args:
            operations: ファイル操作のリスト

        Returns:
            プレビュー文字列
        """
        preview_lines = []
        preview_lines.append(f"{Colors.NEON_CYAN}╔════════════════════════════════════════════╗")
        preview_lines.append(f"{Colors.NEON_BLUE}║  📋 処理対象プレビュー                    ║")
        preview_lines.append(f"{Colors.NEON_CYAN}╠════════════════════════════════════════════╣{Colors.RESET}")
        preview_lines.append("")

        # 移動先フォルダでグループ化
        grouped = {}
        for op in operations:
            folder_path = op.destination.parent
            folder_name = folder_path.name

            if folder_name not in grouped:
                grouped[folder_name] = []
            grouped[folder_name].append(op)

        total_count = 0

        for folder_name, ops in grouped.items():
            count = len(ops)
            total_count += count

            # フォルダヘッダー（LoRAワード表示）
            # 最初のoperationからLoRAワードを取得
            first_reason = ops[0].reason
            preview_lines.append(f"{Colors.NEON_CYAN}📁 {folder_name}{Colors.RESET} {Colors.NEON_YELLOW}({first_reason}){Colors.RESET}")
            preview_lines.append(f"{Colors.CYAN}   {count}件{Colors.RESET}")

            # 先頭3件と終端3件を表示
            if count <= 6:
                # 6件以下は全件表示
                files_to_show = ops
            else:
                # 先頭3件 + 終端3件
                files_to_show = ops[:3] + ops[-3:]

            for i, op in enumerate(files_to_show):
                # 省略記号の挿入
                if count > 6 and i == 3:
                    omitted = count - 6
                    preview_lines.append(f"{Colors.NEON_BLUE}   ... 他{omitted}件{Colors.RESET}")

                preview_lines.append(f"{Colors.NEON_BLUE}   ├─ {op.source.name}{Colors.RESET}")

            preview_lines.append("")

        # サマリー
        preview_lines.append(f"{Colors.CYAN}{'─' * 44}{Colors.RESET}")
        preview_lines.append(f"{Colors.NEON_YELLOW}合計: {total_count}件{Colors.RESET}")
        preview_lines.append("")

        return "\n".join(preview_lines)


# =====================================
# SortModeHandler - Sort モードの処理
# =====================================

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


# =====================================
# CleanModeHandler - Clean モードの処理
# =====================================

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

        # 全ファイルをスキャン
        matched_files = self.scanner.scan_files(
            pattern="*",
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

            matched_files = self.scanner.scan_files(
                pattern=search,
                recursive=False
            )

            for file in matched_files:
                operations.append(FileOperation(
                    source=file,
                    destination=destination,
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
                        op.destination.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(op.source), str(op.destination / op.source.name))

                    elif op.action == 'copy':
                        op.destination.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(str(op.source), str(op.destination / op.source.name))

                # ログ記録
                self.logger.info(f"[{op.action}] {op.source} ({op.reason})")
                success_count += 1

            except Exception as e:
                self.logger.error(f"[エラー] {op.source}: {e}")
                failure_count += 1

        return success_count, failure_count


# =====================================
# PngPromptSortModeHandler - PNG_Prompt_Sort モードの処理
# =====================================

class PngPromptSortModeHandler:
    """
    PNG_Prompt_Sort モードの処理を行うクラス

    機能:
    - 画像ファイルのメタデータ（PNG info等）からLoRa名を抽出
    - マッピングテーブルに基づいて振り分け先を決定
    - 複数LoRa検出時は全フォルダにコピー
    - ファイル名重複時は連番を付与
    """

    def __init__(self, config: Dict[str, Any], scanner: 'FileScanner', logger: 'LootLogger'):
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
        self.settings = config['settings']

        # マッピングファイル読み込み
        self.lora_map = self._load_lora_map()

        # メタデータ設定
        self.metadata_config = config.get('metadata', {})
        self.metadata_fields = self.metadata_config.get('fields', ['parameters', 'Comment', 'Description', 'prompt'])
        self.lora_pattern = re.compile(self.metadata_config.get('lora_pattern', r"<lora:([^:]+):[^>]+>"), re.IGNORECASE)

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
            script_dir = Path(__file__).parent.parent  # srcの親 = プロジェクトルート
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
        メタデータからLoRa名を抽出

        Args:
            metadata: メタデータ文字列

        Returns:
            検出されたLoRa名のリスト
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
        target_extensions = self.settings.get('target_extensions', ['png', 'jpg', 'jpeg', 'webp'])

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

                    # LoRa検出
                    loras = self._find_loras(metadata)

                    if not loras:
                        # LoRa未検出
                        dest_folder = output_dir / no_lora_folder
                        operations.append(FileOperation(
                            source=file_path,
                            destination=dest_folder / file_path.name,
                            action='move',
                            reason='LoRa未検出'
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
                            reason=f'未登録LoRa: {loras[0]}'
                        ))
                    else:
                        # 最初のマッチフォルダに移動のみ
                        folder_name, lora_name = matched_folders[0]
                        dest_folder = output_dir / folder_name
                        operations.append(FileOperation(
                            source=file_path,
                            destination=dest_folder / file_path.name,
                            action='move',
                            reason=f'LoRa: {lora_name}'
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

        # 操作実行
        for op in tqdm(operations, desc="処理中", unit="files"):
            try:
                if not dry_run:
                    # 保存先ディレクトリ作成
                    op.destination.parent.mkdir(parents=True, exist_ok=True)

                    # 重複チェック＆連番付与
                    unique_filename = self._get_unique_filename(op.destination.parent, op.destination.name)
                    final_dest = op.destination.parent / unique_filename

                    # 移動実行
                    shutil.move(op.source, final_dest)
                    self.logger.info(f"移動: {op.source.name} -> {op.destination.parent.name}/{unique_filename}")
                    success_count += 1
                else:
                    self.logger.info(f"[DRY-RUN] 移動: {op.source.name} -> {op.destination.parent.name}")
                    success_count += 1

            except Exception as e:
                self.logger.error(f"移動失敗 ({op.source.name}): {e}")
                failure_count += 1

        return success_count, failure_count


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
