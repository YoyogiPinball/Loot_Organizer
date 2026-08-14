> 最終更新: 2026-03-12（Thu）21:32

# Loot Organizer

## 実行

```bash
# Windows
run.bat

# Linux / WSL
python3 -m src.loot_manager
# or
./run.sh
```

依存関係: `questionary`, `colorama`, `PyYAML`, `Pillow`, `tqdm`

## モード

| モード | 用途 |
|--------|------|
| Sort | YAML ルールに基づいてファイルを仕分け |
| Clean | ファイル名のクリーンアップ |
| PNG_Prompt_Sort | AI 生成画像の PNG メタデータ（LoRA 名等）で分類 |

起動後に questionary の対話 UI でモードを選択する。

## 設定ファイル（configs/）

- `configs/*.yaml` にプリセットを配置。`configs/samples/` にサンプルあり
- プリセットの作成・編集は Codex に依頼する運用

## バージョン管理

コードを修正・機能追加したら **必ず** `src/__version__.py` のバージョンを更新する。

| 変更種別 | バンプ対象 | 例 |
|---|---|---|
| バグ修正 | patch（末尾） | `1.0.0` → `1.0.1` |
| 機能追加（後方互換あり） | minor（中位） | `1.0.1` → `1.1.0` |
| 破壊的変更・大規模リファクタ | major（先頭） | `1.1.0` → `2.0.0` |

`__commit__` も合わせて更新すること（内容はコミットハッシュ or 変更内容の短い説明）。

## プロジェクト構成

```
src/
  __version__.py          # バージョン情報（修正のたびに更新）
  loot_manager.py         # メインエントリポイント
  handlers/
    clean_handler.py      # Clean モード
    sort_handler.py       # Sort モード
    png_prompt_sort_handler.py
  core/
    file_scanner.py       # ファイルスキャン・フィルタ
    config_loader.py      # YAML設定ロード
    preview_generator.py  # プレビュー生成
  utils/
    file_utils.py         # ファイル名クリーンアップ等
configs/                  # プリセットYAML（*.yaml）
docs_ToMe/                # 調査・設計ノート（.gitignore対象）
```
