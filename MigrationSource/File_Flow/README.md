# FileFlow

ファイル整理を自動化するPythonツール

## 概要

FileFlowは、大量のファイルを効率的に整理するためのツールです。以下の処理を自動で実行できます：

1. **特定文字列を含むファイルの削除**
   - 不要なファイルを一括削除

2. **ファイル名のクリーンアップ**
   - 絵文字や特殊文字を削除
   - ファイルシステムで問題を起こす文字を除去

3. **ファイルの振り分け**
   - 条件に応じてファイルをコピー/移動/削除

## 特徴

- ✅ **ドライラン標準**: 実行前にプレビューで確認可能
- ✅ **柔軟な設定**: YAML形式の設定ファイルで簡単カスタマイズ
- ✅ **詳細なログ**: 全処理をログファイルに記録
- ✅ **プログレスバー**: 処理状況を視覚的に表示
- ✅ **カラー出力**: 見やすいコンソール表示

## 動作環境

- Python 3.7以上
- Windows / macOS / Linux

## インストール

### 1. Pythonのインストール

Pythonがインストールされていない場合は、公式サイトからダウンロードしてください：
https://www.python.org/downloads/

### 2. 依存ライブラリのインストール

```bash
pip install -r requirements.txt
```

または、個別にインストール：

```bash
pip install colorama PyYAML tqdm
```

## 使い方

### 基本的な使い方（Windows）

1. `config.yaml`を編集して、処理ルールを設定
2. `run.bat`をダブルクリックで実行
3. ドライラン結果を確認
4. 実行するか選択

### コマンドラインから実行

#### ドライランモード（デフォルト）
```bash
python file_flow.py
```

処理内容をプレビュー表示し、実行前に確認を求めます。

#### 即座に実行
```bash
python file_flow.py --execute
```

確認なしで即座に処理を実行します。

#### 確認をスキップ
```bash
python file_flow.py --no-confirm
```

ドライラン後の確認プロンプトをスキップします。

#### ヘルプ表示
```bash
python file_flow.py --help
```

## 設定ファイル（config.yaml）

設定ファイルの各項目について説明します。

### 基本設定

```yaml
target_directory: "D:\\your\\target\\directory"
```

処理対象のディレクトリを指定します。

### ステップ1: 削除処理

```yaml
deletion:
  enabled: true                # この処理を有効にするか
  strings:                     # 削除対象の文字列リスト
    - "{zpi$r=1}"
    - "不要な文字列"
  recursive: true              # サブフォルダも検索するか
```

ファイル名に指定した文字列が含まれるファイルを削除します。

### ステップ2: クリーンアップ

```yaml
cleanup:
  enabled: true                # この処理を有効にするか
  recursive: true              # サブフォルダも処理するか
  custom_patterns: []          # カスタム正規表現パターン
```

ファイル名から以下を削除します：
- 絵文字
- ファイルシステムで使えない文字（`\ / : * ? " < > |`）
- 制御文字

### ステップ3: 振り分けルール

```yaml
sorting_rules:
  - search: "*t=V*"                           # 検索パターン
    destination: "D:\\sorted\\V"              # 振り分け先
    action: "move"                            # 処理内容（copy/move/delete）
```

#### 処理内容（action）の種類

- `copy`: ファイルをコピー（元のファイルは残る）
- `move`: ファイルを移動（元のファイルは削除される）
- `delete`: ファイルを削除

### 詳細設定

```yaml
advanced:
  confirm_before_execution: true    # 実行前に確認するか
  log_directory: "logs"             # ログファイルの保存先
  show_progress: true               # プログレスバーを表示するか
```

## ログファイル

処理結果は自動的に`logs/`ディレクトリに保存されます。

ファイル名形式: `YYYYMMDD_HHMMSS.log`

例: `20241110_143022.log`

ログには以下の情報が記録されます：
- 処理開始・終了時刻
- 各ファイルの処理結果
- エラー情報

## 使用例

### 例1: 画像ファイルの整理

```yaml
target_directory: "D:\\Downloads"

sorting_rules:
  - search: "*.jpg"
    destination: "D:\\Pictures\\JPG"
    action: "move"
    
  - search: "*.png"
    destination: "D:\\Pictures\\PNG"
    action: "move"
```

### 例2: 特定の文字列を含むファイルの振り分け

```yaml
sorting_rules:
  - search: "*screenshot*"
    destination: "D:\\Screenshots"
    action: "move"
    
  - search: "*backup*"
    destination: "D:\\Backups"
    action: "copy"
```

### 例3: 不要ファイルの一括削除

```yaml
deletion:
  enabled: true
  strings:
    - "Thumbs.db"
    - ".DS_Store"
    - "desktop.ini"
  recursive: true
```

## トラブルシューティング

### エラー: 設定ファイルが見つかりません

`config.yaml`が同じディレクトリに存在するか確認してください。

### エラー: Pythonが見つかりません

Pythonが正しくインストールされ、PATHに追加されているか確認してください。

```bash
python --version
```

### エラー: モジュールが見つかりません

依存ライブラリをインストールしてください：

```bash
pip install -r requirements.txt
```

### 処理が実行されない

ドライランモードで実行されている可能性があります。`--execute`オプションを使用するか、ドライラン後の確認で`yes`を入力してください。

## 注意事項

⚠️ **重要な注意**

- **削除・移動処理は元に戻せません**
- 必ずドライランモードで動作を確認してから実行してください
- 重要なファイルは事前にバックアップを取ることを推奨します
- 設定ファイルのパスは正確に記述してください

## ライセンス

このソフトウェアは個人利用・商用利用ともに自由に使用できます。

## 更新履歴

### v1.0.0 (2024-11-10)
- 初回リリース
- 基本機能の実装
  - ファイル削除
  - ファイル名クリーンアップ
  - ファイル振り分け
- ドライランモード実装
- ログ出力機能
- プログレスバー表示

## 作者

ikoooou

## サポート

問題が発生した場合や改善提案がある場合は、お気軽にご連絡ください。
