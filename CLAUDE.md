# 📁 Loot Organizer

個人用ファイル整理ツール - 2段階ワークフローによるファイル管理システム

## 🎯 プロジェクト概要

Loot Organizerは、ダウンロードフォルダなどに散らばったファイルを効率的に整理するためのCLIツールです。
ユーザーが設定したルール（YAML形式）に基づいて、ファイルの振り分け、クリーンアップ、削除を自動化します。

### 💡 設計思想

- **⚙️ 設定駆動型**: YAML設定ファイルで処理ルールを定義
- **🎮 インタラクティブUI**: ↑↓キーで選択するモダンなCLI
- **🛡️ 非破壊的確認**: 実行前に必ずプレビューを表示し、ユーザー確認を取る
- **🌍 多言語対応**: 日本語/英語（将来実装予定）
- **💾 プリセット管理**: よく使う設定をプリセットとして保存・選択可能

## 🔄 ワークフロー

```
📥 ダウンロードフォルダ（カオス）
    ↓
📤 【Sort モード】大まかに振り分け
    ↓
📁 動画フォルダ、スクショフォルダ etc...
    ↓
🏷️ 【外部ツール: Zippla】ラベリング（r=5, t=V など）
    ↓
✨ 【Clean モード】クリーンアップ＋低レート削除
    ↓
✅ 完成！
```

## 📂 プロジェクト構造

```
Loot_Organizer/
├── src/
│   └── loot_manager.py          # メインスクリプト
├── configs/
│   ├── samples/                 # サンプル設定集（Git管理対象）
│   │   ├── downloads_sort.yaml  # ダウンロード振り分けサンプル
│   │   ├── cleanup_files.yaml   # クリーンアップサンプル
│   │   └── custom_example.yaml  # カスタム例
│   └── *.yaml                   # ユーザーの個人設定（Git除外）
├── MigrationSource/             # 統合前の旧スクリプト（参考用）
│   ├── File_Flow/
│   └── File_organizer/
├── requirements.txt
├── run.bat                      # 起動用バッチファイル
├── .gitignore
├── CLAUDE.md                    # このファイル
└── logs/                        # 実行ログ（Git除外）
```

## ⚙️ コアモード

### 📤 Sort モード
**🎯 目的**: ゴチャついたフォルダから各種フォルダへファイルを振り分け

**📝 処理内容**:
- パターンマッチングによるファイル移動
- 除外設定（特定ファイルをスキップ）
- プレビュー → 確認 → 実行

**📌 ベース**: 旧`File_organizer`スクリプト

**💼 典型的な用途**:
- ダウンロードフォルダ → 動画/画像/ドキュメントフォルダ
- 拡張子ベースの振り分け
- ファイル名パターンベースの振り分け

### ✨ Clean モード
**🎯 目的**: 既に振り分けられたファイルのクリーンアップと整理

**📝 処理内容**:
1. **🗑️ 削除処理**: 特定文字列を含むファイルを削除（例: `{zpi$r=1}`）
2. **🧹 クリーンアップ**: 絵文字・特殊文字の除去（Android互換性向上）
3. **📋 振り分け**: ラベル付きファイルの分類（copy/move/delete）

**📌 ベース**: 旧`File_Flow`スクリプト

**💼 典型的な用途**:
- Zipplaでラベリング後の処理
- 低レートファイル（r=1）の一括削除
- タグ付きファイル（t=V, t=pic等）の振り分け
- ファイル名から絵文字除去

### 🔄 連続実行モード
**🎯 目的**: 複数のプリセットを順番に実行

**📝 処理内容**:
- チェックボックス形式で実行するプリセットを選択
- 選択順に自動実行
- 各ステップでプレビュー・確認

**💼 典型的な用途**:
- ダウンロード振り分け → クリーンアップの一連の流れを自動化

## 📋 設定ファイル構造

### 🏷️ 共通メタ情報
全てのYAML設定ファイルには以下のメタ情報が必要です：

```yaml
meta:
  name: "設定名（メニューに表示）"
  icon: "📤"  # 絵文字アイコン
  mode: "Sort"  # SortまたはClean
  description: "この設定の説明"
```

### 📤 Sort モード設定例

```yaml
meta:
  name: "ダウンロード振り分け"
  icon: "📤"
  mode: "Sort"
  description: "ダウンロードフォルダから各種フォルダへ振り分け"

settings:
  target_directory: "C:\\Users\\username\\Downloads"
  enable_logging: true
  confirm_before_execute: true
  log_directory: "logs"

# 移動ルール（上から順に優先、最初にマッチしたルールを適用）
move_rules:
  - pattern: "*.mp4"
    dest: "D:\\Videos"
    description: "動画ファイル"
    enabled: true

  - pattern: "*screenshot*"
    dest: "C:\\Pictures\\Screenshots"
    description: "スクリーンショット"
    enabled: true

# 除外パターン（移動しないファイル）
exclusions:
  exact_names:
    - "desktop.ini"
    - "Thumbs.db"
  patterns:
    - "*.tmp"
    - "*.bak"
```

### ✨ Clean モード設定例

```yaml
meta:
  name: "ファイルクリーンアップ"
  icon: "✨"
  mode: "Clean"
  description: "絵文字除去・低レート削除・振り分け"

settings:
  target_directory: "D:\\SortedFiles"
  enable_logging: true
  confirm_before_execute: true
  log_directory: "logs"

# ステップ1: 削除処理
deletion:
  enabled: true
  strings:
    - "{zpi$r=1}"  # 低レートファイル
  recursive: true

# ステップ2: クリーンアップ
cleanup:
  enabled: true
  recursive: true
  custom_patterns: []  # 追加の正規表現パターン

# ステップ3: 振り分けルール
sorting_rules:
  - search: "*r=5*"
    destination: "D:\\HighRated"
    action: "copy"  # copy/move/delete

  - search: "*t=V*"
    destination: "D:\\Videos\\Tagged"
    action: "move"
```

## 🎨 UI/UX設計

### 📋 メインメニュー

```
╔════════════════════════════════════════════╗
║  📁 Loot Organizer                        ║
╠════════════════════════════════════════════╣
║                                            ║
║  ▶ 📤 ダウンロード振り分け [Sort]         ║
║    ✨ ファイルクリーンアップ [Clean]      ║
║    🔄 連続実行モード                      ║
║    ❌ 終了                                ║
║                                            ║
╠════════════════════════════════════════════╣
║  ↑↓: 選択 | Enter: 決定                   ║
╚════════════════════════════════════════════╝
```

### 👀 プレビュー表示（Sort モード例）

```
╔════════════════════════════════════════════╗
║  📋 移動対象プレビュー                    ║
╠════════════════════════════════════════════╣
║                                            ║
║  📁 D:\Videos (15件)                      ║
║    ├─ video001.mp4                        ║
║    ├─ video002.mp4                        ║
║    └─ ... 他13件                          ║
║                                            ║
║  📁 C:\Pictures\Screenshots (8件)         ║
║    ├─ screenshot_01.png                   ║
║    └─ ... 他7件                           ║
║                                            ║
║  合計: 23件                               ║
╠════════════════════════════════════════════╣
║  この内容で実行しますか? (y/N):          ║
╚════════════════════════════════════════════╝
```

### 🎨 カラー出力規則

- **🔵 Cyan**: ヘッダー、タイトル
- **🟢 Green**: 成功メッセージ、処理完了
- **🟡 Yellow**: 警告、プレビュー、確認プロンプト
- **🔴 Red**: エラーメッセージ
- **⚪ White背景+Black文字**: 選択中の項目（ハイライト）

## 🛠️ 技術スタック

- **💻 言語**: Python 3.7+
- **📦 主要ライブラリ**:
  - `questionary`: インタラクティブCLI（↑↓選択）
  - `colorama`: クロスプラットフォームカラー出力
  - `pyyaml`: YAML設定ファイル読み込み
  - `pathlib`: パス操作

## 📝 開発ガイドライン

### 📖 コーディング規約

1. **💬 コメントは多めに**: 1年後に見ても理解できるように
2. **🇯🇵 日本語コメント推奨**: 個人プロジェクトのため
3. **📚 関数のdocstring**: 必ず記載（目的、引数、戻り値）
4. **🛡️ エラーハンドリング**: 想定される例外は全てキャッチ
5. **📊 ログ出力**: 重要な処理は必ずログに記録

### 🛡️ 非破壊的操作の原則

**⚠️ 重要**: ファイル操作は必ず以下のフローを守ること：

```
1. 🔍 処理対象をスキャン
2. 👀 プレビュー表示
3. ✋ ユーザー確認
4. ⚡ 実行
5. 📊 結果サマリー表示
```

### 🔍 プリセット自動検出

`configs/`フォルダ内のYAMLファイルは起動時に自動検出され、メニューに表示されます。

**📌 検出ルール**:
- `configs/samples/`内のファイルはサンプル（メニューには表示しない）
- `configs/`直下の`*.yaml`ファイルを実行可能プリセットとして認識
- `meta`セクションが無いYAMLは無視

### 📝 ログ管理

- **📄 ファイル名**: `logs/YYYY-MM-DD.log`（日付ごとに1ファイル）
- **📋 フォーマット**: `YYYY-MM-DD HH:MM:SS [レベル] メッセージ`
- **➕ 追記モード**: 同日の複数実行を1ファイルに記録

## 💡 よくある使い方

### 📤 ケース1: ダウンロードフォルダの整理

1. `configs/downloads_sort.yaml`を自分の環境に合わせて編集
2. `run.bat`をダブルクリック
3. 「📤 ダウンロード振り分け」を選択
4. プレビュー確認 → 実行

### ✨ ケース2: Zippla後のクリーンアップ

1. Zipplaでファイルにラベル付け（r=5, t=V など）
2. `run.bat`をダブルクリック
3. 「✨ ファイルクリーンアップ」を選択
4. プレビュー確認 → 実行

### 🔄 ケース3: フル自動化ワークフロー

1. `run.bat`をダブルクリック
2. 「🔄 連続実行モード」を選択
3. 実行したいプリセットをチェック（Space）
4. Enter → 順番に自動実行

## 🔧 トラブルシューティング

### ❓ プリセットがメニューに表示されない

- `meta`セクションが正しく記載されているか確認
- YAMLの文法エラーがないか確認（インデント等）
- ファイルが`configs/`直下にあるか確認（`configs/samples/`内は除外）

### ❓ ファイルが移動/削除されない

- ドライランモードになっていないか確認
- 確認プロンプトで`y`を入力したか確認
- ログファイルでエラーを確認

### ❓ 絵文字が文字化けする

- Windowsの場合: コマンドプロンプトではなくWindows Terminalを使用
- フォントを絵文字対応フォント（Cascadia Code等）に変更

## 🚀 今後の拡張予定

- [ ] 🌍 多言語対応（日本語/英語）

---

## 📝 開発ログ

### 2025-11-16 セッション1: プロジェクト設計と基盤構築

#### 完了したこと
1. **プロジェクト設計の確定**
   - ディレクトリ構造: `src/`, `configs/samples/` 方式
   - モード: Sort（振り分け）、Clean（クリーンアップ）の2モード
   - 連続実行モード: チェックボックス形式で複数プリセットを順次実行

2. **設定ファイル仕様の決定**
   - AND条件のみ（OR条件はルールを分けて記述）
   - 拡張機能: ファイルサイズ、画像解像度、アスペクト比、日付フィルタリング
   - プレビュー表示: head/tail/both/all の4モード、件数指定可能
   - ドライランをデフォルトでON

3. **インフラファイルの作成**
   - `.gitignore`: CLAUDE.md除外、ユーザー設定除外、サンプルは含める
   - `requirements.txt`: questionary, colorama, PyYAML, Pillow, tqdm
   - `README.md`: 日英併記、ユーザー向け＋AIエージェント向けドキュメント

#### 決定事項
- **複数条件**: AND方式のみ（シンプル、実用的）
- **アスペクト比**: vertical_min=1.2, horizontal_max=0.8, square_tolerance=0.05
- **プレビュー**: head（先頭5件）、tail、both（先頭＋末尾）、all
- **エラーハンドリング**: 連続実行時は都度確認（案B）
- **ファイルサイズ単位**: KB/MB/GB（文字列）をサポート
- **README作成**: 実装前に作成完了

---

## 🎯 Next Steps（次回作業）

### 優先度: 高 ⭐⭐⭐

#### 1. サンプル設定ファイルの作成
**作成するファイル:**
- `configs/samples/downloads_sort.yaml` - ダウンロード振り分けサンプル
- `configs/samples/cleanup_files.yaml` - クリーンアップサンプル
- `configs/samples/photo_organize.yaml` - 写真整理サンプル（高度な例）
- `configs/samples/migration_organizer.yaml` - **既存file_organizer移行用**
- `configs/samples/migration_flow.yaml` - **既存file_flow移行用**

**各ファイルの要件:**
- 先頭に詳細なコメント（どこに何を書くか、使い方）
- 実用的なデフォルト値
- 拡張機能の使用例を含める

#### 2. 既存スクリプトからの移行サポート

**移行モードの方針:**
```yaml
# configs/samples/migration_organizer.yaml
# ========================================
# 🔄 file_organizer からの移行用設定
# ========================================
# 使い方:
# 1. このファイルを configs/my_organizer.yaml にコピー
# 2. 旧 file_organizer/config.yaml の設定値をコピー
# 3. すぐに使用開始できます

meta:
  name: "file_organizer互換モード"
  icon: "🔄"
  mode: "Sort"
  description: "既存のfile_organizerと同じ動作"

settings:
  # 旧設定の base_path → target_directory
  target_directory: "C:\\Users\\username\\Downloads"

  # 以下、既存設定と同じ
  enable_logging: true
  confirm_before_execute: true

  # 新機能（省略可）
  dry_run_default: true
  preview:
    mode: "head"
    count: 5

# 旧 move_rules をそのまま使用可能
move_rules:
  # 旧設定からそのままコピーペースト可能
  - pattern: "*screenshot*"
    dest: "C:\\Pictures\\Screenshots"
    description: "スクリーンショット"
    enabled: true
```

**移行チェックリスト機能:**
- 起動時に旧スクリプトのconfig.yamlを検出
- 「移行モードで起動しますか？」と提案
- 自動で設定を変換してプレビュー表示

### 優先度: 高 ⭐⭐⭐

#### 3. loot_manager.py の実装

**実装する主要クラス:**
- `LootManager`: メインクラス
- `SortModeHandler`: Sortモード処理
- `CleanModeHandler`: Cleanモード処理
- `ConfigLoader`: YAML読み込み＋バリデーション
- `FileScanner`: ファイルスキャン＋フィルタリング
- `PreviewGenerator`: プレビュー表示生成
- `Logger`: ログ管理

**実装順序:**
1. ConfigLoader（設定読み込み）
2. FileScanner（ファイル検索・フィルタリング）
3. PreviewGenerator（プレビュー表示）
4. SortModeHandler（Sort処理）
5. CleanModeHandler（Clean処理）
6. LootManager（メイン・メニュー・連続実行）

### 優先度: 中 ⭐⭐

#### 4. run.bat の作成
```batch
@echo off
chcp 65001 > nul
cd /d "%~dp0"
python src/loot_manager.py
pause
```

#### 5. テストデータ作成スクリプト
```python
# create_test_data.py
# テスト用のダミーファイル・フォルダを自動生成
```

### 優先度: 低 ⭐

#### 6. 動作テスト
- 実装完了後に実施

---

## 📌 重要な注意事項（次回作業時）

1. **既存スクリプトとの互換性**
   - file_organizer/config.yaml の設定項目をすべてサポート
   - file_flow/config.yaml の設定項目をすべてサポート
   - 移行が「コピペで完了」するレベルを目指す

2. **非破壊的操作の徹底**
   - 必ずドライラン → プレビュー → 確認 → 実行の順
   - エラー時は処理を止めて確認

3. **コメントは多めに**
   - 1年後に見ても分かるように
   - サンプルyamlには特に詳しく

---

## 🔖 次回セッション開始時の確認事項

1. CLAUDE.mdを読み込んで設計を再確認
2. 既存のMigrationSource/内のスクリプトを再確認
3. 上記Next Stepsから着手

---

## 📜 ライセンス

個人利用・商用利用ともに自由に使用可能です。

---

**👤 作成者**: ikoooou
**📅 最終更新**: 2025-11-16
