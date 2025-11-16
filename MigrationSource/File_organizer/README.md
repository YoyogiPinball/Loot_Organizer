# File Organizer

ダウンロードフォルダ内のファイルを自動整理するツールです。

## 必要なパッケージ

```bash
pip install colorama pyyaml
```

## 使い方

1. `config.yaml`を編集して、移動ルールを設定
2. `file_organizer起動.bat`をダブルクリック

または

```bash
python file_organizer.py
```

## 設定ファイル (config.yaml)

### 基本設定

- `enable_logging`: ログ出力のON/OFF
- `confirm_before_execute`: 実行前に確認するか
- `base_path`: 作業対象の基準パス（通常は`../downloads`）

### 移動ルール

**重要:** ルールは**上から順に評価**され、**最初にマッチしたルールが適用**されます。

```yaml
move_rules:
  - pattern: "*screenshot*"      # ワイルドカードでパターン指定
    dest: "C:\\path\\to\\dest"   # 移動先パス
    description: "説明"           # ルールの説明
    enabled: true                # このルールを有効にするか
```

#### パターンの例
- `*screenshot*` - "screenshot"を含む全てのファイル
- `*.mp4` - 拡張子が.mp4の全てのファイル
- `test_*.txt` - "test_"で始まる.txtファイル

### 除外パターン

移動させたくないファイルを指定できます。

```yaml
exclusions:
  exact_names:    # 完全一致で除外
    - "desktop.ini"
    - "Thumbs.db"
  patterns:       # パターンで除外
    - "*.tmp"
    - "*.bak"
```

## 動作仕様

- **対象**: downloadsフォルダ直下のファイルのみ（フォルダは無視）
- **マッチング**: 上から順に評価、最初にマッチしたルールを適用
- **ログ**: 日付ごとに1ファイル（`logs/YYYY-MM-DD.log`）、追記形式

## 実行例

```
📊 実行結果サマリ
================================================================

【移動先別の内訳】

📁 C:\Users\kingc\Pictures\Greenshot (5件)
  ├─ screenshot_001.png
  ├─ screenshot_002.png
  ├─ Twitch_clip.mp4
  ├─ ss_2024_memo.txt
  └─ ss_2025_draft.png

📁 D:\ikoooou\Develop\vid (3件)
  ├─ movie_01.mp4
  ├─ movie_02.mp4
  └─ video_test.mp4

合計: 8件移動
成功: 8件 / 失敗: 0件

================================================================
Enterキーを押すと終了します...
```

## 注意事項

- 移動先に同名ファイルがある場合は上書きされます
- 移動先フォルダは自動作成されます
- バックアップは取っていないので、重要なファイルは事前にコピーを推奨
