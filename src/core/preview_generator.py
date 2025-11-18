# -*- coding: utf-8 -*-
"""
プレビュー表示生成
"""

from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

from ..utils.colors import Colors


@dataclass
class FileOperation:
    """ファイル操作を表すデータクラス"""
    source: Path
    destination: Path | None
    action: str  # "move", "copy", "delete", "cleanup"
    reason: str  # ルールの説明


class PreviewGenerator:
    """
    ファイル操作のプレビュー表示を生成するクラス

    機能:
    - head/tail/both/all モード対応
    - 移動先ごとのグループ化表示
    - 件数サマリー
    """

    def __init__(
        self,
        config: Dict[str, Any] = None,
        preview_mode: str = "head",
        preview_count: int = 5
    ):
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
        preview_lines.append(
            f"{Colors.NEON_CYAN}╔════════════════════════════════════════════╗"
        )
        preview_lines.append(
            f"{Colors.NEON_BLUE}║  📋 処理対象プレビュー                    ║"
        )
        preview_lines.append(
            f"{Colors.NEON_CYAN}╠════════════════════════════════════════════╣{Colors.RESET}"
        )
        preview_lines.append("")

        # クリーンアップ操作がある場合、対象パターンを表示
        if mode == "Clean" and any(op.action == 'cleanup' for op in operations):
            cleanup_info = self._get_cleanup_patterns_description()
            if cleanup_info:
                preview_lines.append(
                    f"{Colors.NEON_YELLOW}🧹 クリーンアップ対象パターン:{Colors.RESET}"
                )
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
                    preview_lines.append(
                        f"{Colors.NEON_RED}  ├─ {op.source.name}{Colors.RESET}"
                    )
                else:
                    preview_lines.append(
                        f"{Colors.NEON_BLUE}  ├─ {op.source.name}{Colors.RESET}"
                    )

            # 省略表示
            omitted = count - len(files_to_show)
            if omitted > 0:
                if group_ops[0].action == 'delete':
                    preview_lines.append(
                        f"{Colors.NEON_RED}  └─ ... 他{omitted}件{Colors.RESET}"
                    )
                else:
                    preview_lines.append(
                        f"{Colors.NEON_BLUE}  └─ ... 他{omitted}件{Colors.RESET}"
                    )

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

    def _generate_png_prompt_sort_preview(
        self,
        operations: List[FileOperation]
    ) -> str:
        """
        PNG_Prompt_Sort専用のプレビュー生成

        Args:
            operations: ファイル操作のリスト

        Returns:
            プレビュー文字列
        """
        preview_lines = []
        preview_lines.append(
            f"{Colors.NEON_CYAN}╔════════════════════════════════════════════╗"
        )
        preview_lines.append(
            f"{Colors.NEON_BLUE}║  📋 処理対象プレビュー                    ║"
        )
        preview_lines.append(
            f"{Colors.NEON_CYAN}╠════════════════════════════════════════════╣{Colors.RESET}"
        )
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
            preview_lines.append(
                f"{Colors.NEON_CYAN}📁 {folder_name}{Colors.RESET} "
                f"{Colors.NEON_YELLOW}({first_reason}){Colors.RESET}"
            )
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
                    preview_lines.append(
                        f"{Colors.NEON_BLUE}   ... 他{omitted}件{Colors.RESET}"
                    )

                preview_lines.append(
                    f"{Colors.NEON_BLUE}   ├─ {op.source.name}{Colors.RESET}"
                )

            preview_lines.append("")

        # サマリー
        preview_lines.append(f"{Colors.CYAN}{'─' * 44}{Colors.RESET}")
        preview_lines.append(f"{Colors.NEON_YELLOW}合計: {total_count}件{Colors.RESET}")
        preview_lines.append("")

        return "\n".join(preview_lines)
