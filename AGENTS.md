> 最終更新: 2026-08-24（Mon）00:46

# Loot Organizer

YAML のプリセットでファイルを仕分ける個人用 CLI ツール。このファイルはコーディングエージェント向けの案内。

## 実行

```bash
# Windows
run.bat

# Linux / WSL
python3 -m src.loot_manager
# or
./run.sh
```

依存関係: `questionary`, `colorama`, `PyYAML`, `Pillow`, `tqdm`, `Send2Trash`（`requirements.txt` が正本）

## テスト

```bash
.venv/bin/python -m pytest -q
```

現在 136 passed（v2.2.3）。**件数が減る変更は入れない。**

## 開発は WSL、本番実行は Windows

**この2つは別環境で、Python の挙動も違う。片方だけで確かめて結論を出さない。**

- `Path.glob` の大文字小文字: Windows は区別しない。WSL は `/mnt/c`（DrvFs）配下でも区別する
- パス区切り: Windows の `Path.glob` は `\` も区切りとして解釈する。Linux は `/` のみ
- 仮想 glob 側はこの差を `platform_glob_rules()`（`src/core/planning_context.py`。実行中の OS から大小文字と区切りの規則を取る関数）で吸収している

環境差に依存するテストは `os.name` と関連する環境変数を monkeypatch する。実環境依存にしない。

## モード

| モード | 用途 |
|--------|------|
| Sort | YAML ルールに基づいてファイルを仕分け（`rename_pattern` 対応） |
| Clean | 削除 → クリーンアップ → 振り分けの3ステップ処理 |
| PNG_Prompt_Sort | AI 生成画像の PNG メタデータ（LoRA 名等）で分類 |
| Pipeline | 複数プリセットを順番に実行。後段ステップは前段が計画したリネーム・移動を反映した仮想ファイル状態を走査する |

起動後に questionary の対話 UI でモードを選択する。モードの登録は `src/handlers/registry.py`。

## 仮想ファイル状態（Pipeline の中核）

`src/core/planning_context.py` の `PlanningContext` は、**実ファイルを一切触らずに**「この操作が終わった後のファイル配置」をメモリ上に持つ。Pipeline の後段ステップはこの仮想状態を走査するので、前段が「計画しただけ」のリネーム・移動も見える。

計画（plan）と実行（execute）は完全に分かれている。**計画中にディスクへ書き込む変更を入れてはいけない。**

## ファイル操作の安全策

コードレビューを受けて入れた防御。挙動を変えるときは理由を確認してから触る。

| 仕組み | 内容 |
|---|---|
| 保存先が埋まっている場合 | 既定では上書きせずスキップして続行する。判定対象は「実ディスク上の既存ファイル」と「同一実行内で先行操作が予約済みの保存先」の両方。PNG_Prompt_Sort で `duplicate_handling: overwrite` を明示したときだけ上書きする |
| 同一保存先への移動 | 移動元と移動先が同じなら操作を計画しない |
| ルールのフォールスルー防止 | Sort でスキップされたファイルも処理済みとして扱い、後続ルールへ落とさない |
| cleanup の連動スキップ | 同じ source の振り分けがスキップされたら、対になる cleanup（リネーム）もスキップする |
| 保存先パスの統一 | `FileOperation.destination` は delete 以外つねに最終ファイルパス。YAML の `dest` / `destination` は必ずディレクトリとして扱う |
| TOCTOU 検査 | 計画時に source の指紋（size / mtime / dev / ino）を記録し、実行直前に照合する |
| 削除の既定 | `deletion.delete_mode` は既定 `trash`。`permanent` を明示したときだけ `unlink` する |
| パスの正規化 | `to_path`（`src/utils/path_utils.py`）が Windows のドライブ文字と WSL の UNC パスを変換し、`..` と相対パスを字句的に正規化する |
| 仮想ファイルの glob | `matching_virtual_files` は `Path.glob` / `rglob` と同じ規則で照合する |
| 中断時の表示 | Pipeline が途中で落ちたら、止まったステップ名と未実行件数を表示する |

## エラーの出しかた

**「エラーも出さずに対象0件で終わる」を作らない。** 利用者が原因に辿り着けなくなる。設定が解釈できないときは、実際の値を含む日本語の例外で止める。

対話ループ（`src/loot_manager.py` の `LootManager.execute_preset`）は計画時の例外を捕捉してメニューへ戻す。トレースバックはログにだけ残し、画面には型名とメッセージを出す。

## プリセット（mode/）

- `mode/*.yaml` にプリセットを配置。`mode/samples/` にサンプルあり
- `mode/` 直下のファイルが自動検出される（`samples/` と `lora_map*.yaml` は除外）
- **`mode/` 直下の `*.yaml` は `.gitignore` 対象**（利用者の実際の保存先パスを含むため）。エージェントは読まないこと。YAML の例が必要なら `mode/samples/` を見る

Pipeline プリセットの `steps[].config` は起動ディレクトリ（`loot_manager.py` の実行ディレクトリ）からの相対パス。

## バージョン管理

コードを修正・機能追加したら **必ず** `src/__version__.py` のバージョンを更新する。

| 変更種別 | バンプ対象 | 例 |
|---|---|---|
| バグ修正 | patch（末尾） | `1.0.0` → `1.0.1` |
| 機能追加（後方互換あり） | minor（中位） | `1.0.1` → `1.1.0` |
| 破壊的変更・大規模リファクタ | major（先頭） | `1.1.0` → `2.0.0` |

`__commit__` も合わせて更新すること（内容は変更内容の短い日本語説明）。

## プロジェクト構成

```
src/
  __version__.py              # バージョン情報（修正のたびに更新）
  loot_manager.py             # メインエントリポイント・対話ループ
  handlers/
    base_handler.py           # 共通実行ループ。保存先の占有判定もここ
    registry.py               # ハンドラ登録・ファクトリ
    sort_handler.py           # Sort モード
    clean_handler.py          # Clean モード
    pipeline_handler.py       # Pipeline モード
    png_prompt_sort_handler.py
  core/
    config_loader.py          # YAML 読み込み・プリセット自動検出（mode/ 対象）
    file_scanner.py           # ファイルスキャン・フィルタ
    planning_context.py       # 計画中の仮想ファイル状態（実ファイルは触らない）
    preview_generator.py      # FileOperation 型定義・プレビュー生成
    logger.py
  utils/
    file_executor.py          # move/copy/delete/rename の実行を集約
    file_utils.py             # clean_filename 等
    path_utils.py             # Windows パス → WSL パス変換（to_path）
    colors.py
tests/                        # pytest。conftest.py に共通フィクスチャ
mode/                         # プリセット YAML（直下は .gitignore 対象）
  samples/                    # サンプルプリセット（git 管理下）
docs_ToMe/                    # 調査・設計ノート（.gitignore 対象）
```

## 触らないもの

`mode/*.yaml`（samples を除く）、`configs_myrule/`、`docs_ToMe/`、`_Archives/`、`logs/`。
いずれも利用者の実際の保存先パスや個人的な記録を含み、git 管理外。
