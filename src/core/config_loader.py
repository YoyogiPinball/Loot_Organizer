# -*- coding: utf-8 -*-
"""
設定ファイル読み込みとバリデーション
"""

import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

from ..utils.path_utils import to_path


@dataclass
class PresetMeta:
    """プリセットのメタ情報"""
    name: str
    icon: str
    mode: str
    description: str
    file_path: str


class ConfigLoader:
    """
    YAML設定ファイルを読み込み、バリデーションを行うクラス

    機能:
    - YAMLファイルのパース
    - 必須フィールドの検証
    - デフォルト値の適用
    - プリセット自動検出
    """

    def __init__(self, mode_dir: str = "mode", valid_modes: List[str] | None = None):
        """
        初期化

        Args:
            mode_dir: 実行モードファイルディレクトリのパス
            valid_modes: 登録済み処理モードの一覧
        """
        self.mode_dir = Path(mode_dir)
        self.valid_modes = set(valid_modes or [])
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
        config_path = to_path(config_path)

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

        # modeの検証（処理モードの詳細検証は各ハンドラが担当）
        if self.valid_modes and meta['mode'] not in self.valid_modes:
            raise ValueError(
                f"{config_path}: meta.mode は {sorted(self.valid_modes)} "
                "のいずれかである必要があります"
            )

        # settingsセクションの検証
        if 'settings' not in config:
            raise ValueError(f"{config_path}: 'settings'セクションが必要です")

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

        return config

    def discover_presets(self) -> List[PresetMeta]:
        """
        mode/ ディレクトリからプリセットを自動検出

        Returns:
            検出されたプリセットのリスト
        """
        presets = []

        if not self.mode_dir.exists():
            self.logger.warning(f"設定ディレクトリが見つかりません: {self.mode_dir}")
            return presets

        # mode/直下のYAMLファイルを検索（samples/内とlora_map*.yamlは除外）
        for yaml_file in self.mode_dir.glob("*.yaml"):
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
