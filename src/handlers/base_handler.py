# -*- coding: utf-8 -*-
"""
Base class for execution mode handlers.
"""

from typing import Any, Dict, List

from tqdm import tqdm

from ..core.file_scanner import FileScanner
from ..core.planning_context import PlanningContext
from ..core.logger import LootLogger
from ..core.preview_generator import FileOperation, SourceFingerprint
from ..utils.file_executor import (
    ExecutionResult,
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
        if not self._external_planning_context or self.planning_context is None:
            self.planning_context = PlanningContext()
        if self.scanner is not None:
            self.scanner.planning_context = self.planning_context
        return self.planning_context

    def _record_planned_operations(
        self,
        operations: List[FileOperation],
        *,
        allow_disk_overwrite: bool = False,
    ) -> List[FileOperation]:
        """Record operations, marking occupied destinations as skipped."""
        if self.planning_context is not None:
            for operation in operations:
                self._record_planned_operation(
                    operation,
                    allow_disk_overwrite=allow_disk_overwrite,
                )
        return operations

    def _record_planned_operation(
        self,
        operation: FileOperation,
        *,
        allow_disk_overwrite: bool = False,
    ) -> None:
        """Record one operation after applying the shared destination checks."""
        if self.planning_context is None:
            return

        destination = operation.destination
        operation.source_identity = self.planning_context.identity(operation.source)
        if operation.action != "delete":
            operation.skip_if_exists = not allow_disk_overwrite

        if operation.planned_skip_reason is not None:
            if operation.planned_skip_category is None:
                operation.planned_skip_category = operation.skip_category
            return

        if destination is not None and self.planning_context.paths_equal(
            operation.source,
            destination,
        ):
            # 同一パスは「保存先が埋まっている」のとは意味が違う。手動対応も要らないので、
            # 件数だけ出す専用の分類にする（protected にすると要対応の一覧に載ってしまう）。
            operation.planned_skip_reason = (
                f"移動元と移動先が同じためスキップしました: {destination}"
            )
            operation.planned_skip_category = "same_path"
            operation.skip_if_exists = True
            return

        if destination is not None:
            reserved = self.planning_context.is_planned_destination(destination)
            occupied = self.planning_context.is_file(destination)
            if reserved or (occupied and not allow_disk_overwrite):
                operation.planned_skip_reason = (
                    f"保存先が既に存在するためスキップしました: {destination}"
                )
                operation.planned_skip_category = operation.skip_category
                operation.skip_if_exists = True
                return

        self.planning_context.apply_operation(operation)

    def _rebuild_planning_state(
        self,
        operations: List[FileOperation],
        initial_planning_state,
        dependency_skipped_renames: List[FileOperation],
    ) -> None:
        """Restore and replay executable operations through destination checks."""
        if self.planning_context is None:
            return

        self.planning_context.restore(initial_planning_state)
        skipped_renames = []
        dependency_skip_ids = {
            id(operation) for operation in dependency_skipped_renames
        }

        for operation in operations:
            for skipped_destination, original_source in skipped_renames:
                if self.planning_context.paths_equal(
                    operation.source,
                    skipped_destination,
                ):
                    operation.source = original_source
                    operation.source_fingerprint = SourceFingerprint.capture(
                        original_source
                    )
                    break

            if operation.planned_skip_reason is not None:
                if id(operation) in dependency_skip_ids:
                    skipped_renames.append((operation.destination, operation.source))
                continue

            self._record_planned_operation(
                operation,
                allow_disk_overwrite=(
                    operation.action != "delete" and not operation.skip_if_exists
                ),
            )

    @staticmethod
    def _skip_cleanup_for_skipped_sorting(
        cleanup_operations: List[FileOperation],
        sorting_operations: List[FileOperation],
    ) -> List[FileOperation]:
        """Skip cleanup when sorting for the same logical source was skipped."""
        skipped_sorting = {
            operation.source_identity: operation
            for operation in sorting_operations
            if operation.planned_skip_reason is not None
        }
        changed_operations = []
        for operation in cleanup_operations:
            sorting_operation = skipped_sorting.get(operation.source_identity)
            if sorting_operation is None or operation.planned_skip_reason is not None:
                continue
            operation.planned_skip_reason = (
                "同じ元ファイルの振り分け操作がスキップされたため、"
                "cleanup もスキップしました"
            )
            operation.planned_skip_category = sorting_operation.skip_category
            operation.skip_if_exists = True
            changed_operations.append(operation)
        return changed_operations

    def _propagate_cleanup_skips(
        self,
        operations: List[FileOperation],
        initial_planning_state,
        cleanup_operations: List[FileOperation],
        sorting_operations: List[FileOperation],
    ) -> List[FileOperation]:
        """Propagate dependency skips and rebuild until the plan is stable."""
        dependency_skipped_cleanup = []
        while True:
            changed_operations = self._skip_cleanup_for_skipped_sorting(
                cleanup_operations,
                sorting_operations,
            )
            if not changed_operations:
                return dependency_skipped_cleanup
            dependency_skipped_cleanup.extend(changed_operations)
            self._rebuild_planning_state(
                operations,
                initial_planning_state,
                dependency_skipped_cleanup,
            )

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
    ) -> ExecutionResult:
        """Execute planned operations."""
        success_count = 0
        failure_count = 0
        skipped_operations = []

        for op in tqdm(operations, desc="処理中", unit="files"):
            try:
                if op.planned_skip_reason is not None:
                    result = execute_file_op(op)
                elif not dry_run:
                    result = execute_file_op(op)
                else:
                    result = None

                if isinstance(result, SkippedFileOperation):
                    skipped_operations.append(result)
                    self.logger.info(skipped_operation_log_message(op, result))
                    continue

                self.logger.info(operation_log_message(op, dry_run=dry_run))
                success_count += 1

            except Exception as e:
                self.logger.error(f"[エラー] {op.source}: {e}")
                failure_count += 1

        return ExecutionResult(success_count, failure_count, skipped_operations)
