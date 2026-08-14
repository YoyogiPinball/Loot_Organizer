# -*- coding: utf-8 -*-
"""
Base class for execution mode handlers.
"""

from typing import Any, Dict, List, Tuple

from tqdm import tqdm

from ..core.file_scanner import FileScanner
from ..core.planning_context import PlanningContext
from ..core.logger import LootLogger
from ..core.preview_generator import FileOperation
from ..utils.file_executor import (
    SkippedFileOperation,
    execute_file_op,
    operation_log_message,
    skipped_operation_log_message,
)


class BaseHandler:
    """
    Common handler behavior.

    Subclasses decide what operations should happen. This base class owns the
    shared execution loop so move/copy/delete/rename behavior stays consistent.
    """

    MODE = ""
    REQUIRES_SCANNER = True
    REQUIRED_SETTINGS: tuple[str, ...] = ()
    REQUIRED_TOP_LEVEL: tuple[str, ...] = ()

    def __init__(
        self,
        config: Dict[str, Any],
        scanner: FileScanner | None,
        logger: LootLogger,
        config_loader=None,
        planning_context: PlanningContext | None = None,
    ):
        self.config = config
        self.scanner = scanner
        self.logger = logger
        self.config_loader = config_loader
        self.planning_context = planning_context
        self._external_planning_context = planning_context is not None
        if self.scanner is not None and planning_context is not None:
            self.scanner.planning_context = planning_context
        self._apply_mode_defaults()

    def _start_planning(self) -> PlanningContext:
        """Prepare a fresh local context, or reuse a Pipeline-owned context."""
        if not self._external_planning_context:
            self.planning_context = PlanningContext()
        if self.scanner is not None:
            self.scanner.planning_context = self.planning_context
        return self.planning_context

    def _record_planned_operations(
        self,
        operations: List[FileOperation],
    ) -> List[FileOperation]:
        """Apply operations to the in-memory state and return them unchanged."""
        if self.planning_context is not None:
            self.planning_context.apply_operations(operations)
        return operations

    @classmethod
    def validate_config(cls, config: Dict[str, Any], config_path=None) -> None:
        """Validate fields required by this mode."""
        label = str(config_path) if config_path else "設定"
        settings = config.get("settings", {})

        for field in cls.REQUIRED_SETTINGS:
            if field not in settings:
                raise ValueError(f"{label}: settings.{field} が必要です")

        for field in cls.REQUIRED_TOP_LEVEL:
            if field not in config:
                raise ValueError(f"{label}: {cls.MODE} モードには '{field}' が必要です")

    def _apply_mode_defaults(self) -> None:
        """Apply mode-specific defaults. Subclasses may override."""

    def plan_operations(self) -> List[FileOperation]:
        """Plan file operations for this mode."""
        raise NotImplementedError

    def execute_operations(
        self,
        operations: List[FileOperation],
        dry_run: bool = False
    ) -> Tuple[int, int]:
        """Execute planned operations."""
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

        return success_count, failure_count
