# -*- coding: utf-8 -*-
"""
設定ファイル読み込みとバリデーション
"""

import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class PresetMeta:
    """プリセットのメタ情報"""
    name: str
    icon: str
    mode: str  # "Sort", "Clean", または "PNG_Prompt_Sort"
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
            raise ValueError(
                f"{config_path}: meta.mode は 'Sort', 'Clean', "
                "または 'PNG_Prompt_Sort' である必要があります"
            )

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
