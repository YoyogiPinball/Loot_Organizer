# -*- coding: utf-8 -*-
"""
Pipeline モードの処理ハンドラー
"""

from typing import List, Tuple

from tqdm import tqdm

from ..core.planning_context import PlanningContext
from ..core.preview_generator import FileOperation
from ..utils.file_executor import (
    SkippedFileOperation,
    execute_file_op,
    operation_log_message,
    skipped_operation_log_message,
)
from .base_handler import BaseHandler


class PipelineAskDuplicateHandlingError(ValueError):
    """Pipeline 内の PNG ステップが ask を要求したときの設定エラー。"""

    def __init__(self, step_label: str, config_path):
        self.step_label = step_label
        self.config_path = config_path
        super().__init__(
            f"Pipeline のステップ「{step_label}」の設定ファイル "
            f"{config_path} では duplicate_handling: ask を使用できません"
        )


class PipelineModeHandler(BaseHandler):
    """
    複数の実行モード YAML を順番に計画し、まとめて実行するモード。
    """

    MODE = "Pipeline"
    REQUIRES_SCANNER = False
    REQUIRED_TOP_LEVEL = ("steps",)

    @classmethod
    def validate_config(cls, config, config_path=None) -> None:
        """Pipelineモードの設定を検証"""
        super().validate_config(config, config_path=config_path)
        label = str(config_path) if config_path else "設定"
        steps = config.get('steps')
        if not isinstance(steps, list) or not steps:
            raise ValueError(f"{label}: Pipeline モードには 'steps' が必要です")

        for index, step in enumerate(steps, 1):
            if not isinstance(step, dict) or not step.get('config'):
                raise ValueError(f"{label}: steps[{index}] に config が必要です")

    def plan_operations(self) -> List[FileOperation]:
        """各ステップの操作をまとめて計画"""
        from .registry import build_handler
        from ..core.config_loader import ConfigLoader

        loader = self.config_loader or ConfigLoader()
        prepared_steps = []
        for index, step in enumerate(self.config.get('steps', []), 1):
            step_config_path = step['config']
            step_label = step.get('label') or f"{index}. {step_config_path}"
            sub_config = loader.load_config(step_config_path)
            if (
                sub_config.get("meta", {}).get("mode") == "PNG_Prompt_Sort"
                and sub_config.get("settings", {}).get(
                    "duplicate_handling",
                    "overwrite",
                ) == "ask"
            ):
                raise PipelineAskDuplicateHandlingError(
                    step_label,
                    step_config_path,
                )
            prepared_steps.append(
                (step_config_path, step_label, sub_config)
            )

        if not self._external_planning_context:
            self.planning_context = PlanningContext()
        operations = []
        self.skipped_dirs = []

        for step_config_path, step_label, sub_config in prepared_steps:
            sub_handler = build_handler(
                config=sub_config,
                logger=self.logger,
                config_loader=loader,
                config_path=step_config_path,
                planning_context=self.planning_context,
            )

            step_ops = sub_handler.plan_operations()
            for op in step_ops:
                op.reason = f"[{step_label}] {op.reason}"
                op.step_label = step_label
                op.step_mode = sub_config['meta']['mode']
            operations.extend(step_ops)

            scanner = getattr(sub_handler, 'scanner', None)
            if scanner and getattr(scanner, 'skipped_dirs', None):
                self.skipped_dirs.extend(scanner.skipped_dirs)

            if getattr(sub_handler, 'skipped_dirs', None):
                self.skipped_dirs.extend(sub_handler.skipped_dirs)

        return operations

    def execute_operations(
        self,
        operations: List[FileOperation],
        dry_run: bool = False,
    ) -> Tuple[int, int]:
        """Execute in order and stop when a dependency may have failed."""
        success_count = 0
        failure_count = 0

        for op in tqdm(operations, desc="処理中", unit="files"):
            try:
                if not dry_run:
                    result = execute_file_op(op)
                    if isinstance(result, SkippedFileOperation):
                        self.logger.info(skipped_operation_log_message(op, result))
                        continue

                self.logger.info(operation_log_message(op, dry_run=dry_run))
                success_count += 1

            except Exception as e:
                self.logger.error(f"[エラー] {op.source}: {e}")
                failure_count += 1
                self.logger.error(
                    "Pipeline の整合性を保つため、後続処理を中止します"
                )
                break

        return success_count, failure_count
