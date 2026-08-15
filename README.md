> 最終更新: 2026-08-15（Sat）10:26

# 📁 Loot Organizer

個人用ファイル整理ツール - 2段階ワークフローによるファイル管理システム

[English](#english) | 日本語

---

## 目次

- [Loot Organizerとは？](#loot-organizerとは)
- [主な機能](#主な機能)
- [クイックスタート](#クイックスタート)
  - [インストール](#インストール)
  - [設定](#設定)
  - [実行](#実行)
- [🎯 初回セットアップガイド](#-初回セットアップガイド)
- [🤖 YAML設定をAIで簡単に作成](#-yaml設定をaiで簡単に作成)
- [設定ガイド](#設定ガイド)
- [よくある使い方](#よくある使い方)
- [AIエージェント向け](#aiエージェント向け)
- [トラブルシューティング](#トラブルシューティング)
- [ライセンス](#ライセンス)

---

## Loot Organizerとは？

Loot Organizerは、ダウンロードフォルダなどに散らばったファイルを効率的に整理するためのCLIツールです。YAML形式で定義したルールに基づいて、ファイルの振り分け、クリーンアップ、削除を自動化します。

**特に、AI生成画像（Stable Diffusion / NovelAI / ComfyUI等）を、PNG画像に埋め込まれたプロンプト情報から自動的に読み取り、使用されているLoRA名を検出して自動振り分けする機能が強力です。**

---

## 主な機能

- **📤 振り分けモード（Sort）**: 大量のファイルでゴチャついたフォルダ（ダウンロードフォルダなど）を各種フォルダへ整理整頓
- **✨ クリーンアップモード（Clean）**: ファイル名整理、不要ファイル削除、再振り分け
  - **source_directory**: 特定のディレクトリからのファイルのみ対象
  - **rename_pattern**: 移動/コピー時にファイル名から文字列を削除/置換
  - **recursive**: サブフォルダも再帰的に検索
  - **cleanup pattern & target_directories**: 特定のパターン・ディレクトリのみをクリーンアップ
- **🎨 PNG_Prompt_Sortモード**:
  - **PNG画像に埋め込まれたプロンプトを自動解析**
  - **使用LoRAを検出して自動振り分け** (Stable Diffusion / NovelAI / ComfyUI 対応)
  - 数千枚の画像も一瞬で整理可能
  - マッピングファイルで柔軟にフォルダ振り分け設定
- **🔄 連続実行モード**: 複数のプリセットを順番に実行
- **🎮 インタラクティブUI**: ↑↓キーで操作
- **🛡️ 安全な操作**: 実行前に必ずプレビュー表示
- **💾 プリセット管理**: よく使う設定を保存・再利用
- **📊 バージョン表示**: 起動時にバージョン番号とコミットハッシュを表示

---

## クイックスタート

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/YoyogiPinball/Loot_Organizer.git
cd Loot_Organizer

# 依存関係をインストール
pip install -r requirements.txt
```

依存関係には、削除対象をゴミ箱へ送るための `Send2Trash` が含まれます。

### 設定

サンプル設定をコピーして、自分の環境に合わせて編集します：

```bash
# サンプルをコピー
cp mode/samples/downloads_sort.yaml mode/my_sort.yaml
```

**Windows:**
```cmd
notepad mode\my_sort.yaml
```

**Linux/Mac:**
```bash
nano mode/my_sort.yaml
```

### 実行

**Windows:**
```cmd
run.bat
```

**Linux/Mac:**
```bash
python -m src.loot_manager
```

---

## 🎯 初回セットアップガイド

### Sort/Cleanモードの場合（ファイル整理）

**1. サンプル設定をコピー**
```bash
cp mode/samples/downloads_sort.yaml mode/my_organizer.yaml
```

**Windows:**
```cmd
copy mode\samples\downloads_sort.yaml mode\my_organizer.yaml
```

**2. 設定ファイルを編集**

エディタで `mode/my_organizer.yaml` を開きます：

```cmd
notepad mode\my_organizer.yaml
```

以下の項目を自分の環境に合わせて変更：

```yaml
settings:
  target_directory: "C:\\Users\\YOUR_NAME\\Downloads"  # 整理したいフォルダ

move_rules:
  - name: "Videos"
    destination: "D:\\Videos"  # 移動先フォルダ
    patterns:
      - "*.mp4"
      - "*.mkv"
```

**3. 実行**
```cmd
run.bat
```

メニューから設定ファイルを選択して実行！

---

### AI画像整理モードの場合（Stable Diffusion等）

**1. サンプル設定をコピー**
```bash
cp mode/samples/ai_image_sort.yaml mode/my_ai_sorter.yaml
cp mode/samples/lora_map_sample.yaml mode/lora_map.yaml
```

**Windows:**
```cmd
copy mode\samples\ai_image_sort.yaml mode\my_ai_sorter.yaml
copy mode\samples\lora_map_sample.yaml mode\lora_map.yaml
```

**2. マッピングファイルを編集**

`mode/lora_map.yaml` を開いて、自分の使っているLoRA名を登録：

```yaml
mappings:
  "your_lora_name": "振り分け先フォルダ名"
  "character_alice": "キャラクター＿アリス"
  "style_anime": "スタイル＿アニメ"
```

**3. 設定ファイルを編集**

`mode/my_ai_sorter.yaml` を開いて、パスを変更：

```yaml
settings:
  source_directories:
    - "D:\\StableDiffusion\\outputs"  # AI画像が保存されているフォルダ
  output_directory: "D:\\AI_Images\\Sorted"  # 振り分け先の親フォルダ
  mapping_file: "mode/lora_map.yaml"
```

**4. 実行**
```cmd
run.bat
```

---

## 🤖 YAML設定をAIで簡単に作成

YAML設定ファイルの編集が難しい？**AIエージェント（Claude、ChatGPT等）を使えば簡単に作成できます！**

### プロンプト例1: ダウンロードフォルダ整理

```
Loot Organizerの設定ファイルを作成してください。

目的：Downloadsフォルダ（C:\Users\YourName\Downloads）を整理
振り分け先：
- 動画（*.mp4, *.mkv） → D:\Videos
- 画像（*.jpg, *.png） → D:\Pictures
- ドキュメント（*.pdf, *.docx） → D:\Documents
- 10MB以上のファイル → D:\LargeFiles

mode/samples/downloads_sort.yaml を参考にして作成してください。
```

### プロンプト例2: AI画像整理

```
Loot Organizerの lora_map.yaml を作成してください。

以下のLoRA名をフォルダに振り分けたいです：
- pikachu → ピカチュウ
- eevee → イーブイ
- anime_style_v2 → アニメスタイル
- realistic_face → リアル顔

mode/samples/lora_map_sample.yaml の形式で作成してください。
```

### プロンプト例3: 古いファイル削除

```
Loot Organizerの設定で、以下を実現してください：

- 30日以上前のファイルを削除
- ただし "important" が含まれるファイルは除外
- ファイル名に絵文字が含まれるものはクリーンアップ

mode/samples/cleanup_files.yaml を参考にしてください。
```

**コツ：**
- サンプルファイル（`mode/samples/`）を見せて「これを参考に作って」と頼む
- 具体的な条件（パス、拡張子、サイズ等）を明示する
- 分からない項目は「おすすめ設定を教えて」と聞く

---

## 設定ガイド

### 基本構造

すべてのYAML設定ファイルには以下の`meta`セクションが必要です：

```yaml
meta:
  name: "My File Organizer"
  icon: "📤"
  mode: "Sort"  # Sort, Clean, または PNG_Prompt_Sort
  description: "ダウンロードフォルダを整理"

settings:
  target_directory: "/path/to/folder"
  enable_logging: true
  confirm_before_execute: true
  dry_run_default: false

  preview:
    mode: "both"  # head / tail / both / all
    count: 5

  logging:
    log_success: true
    log_directory: "logs"
```

### Pipeline モード

複数のプリセットを、1回のプレビューと確認で順番に実行できます。後段のステップは、前段で予定されたリネーム・移動・コピー・削除を反映した仮想ファイル状態を検索します。プレビュー中や dry-run 中に実ファイルは変更されません。

```yaml
meta:
  name: "ワンストップ処理"
  icon: "🚀"
  mode: "Pipeline"
  description: "リネーム後に振り分けとクリーンアップを実行"

settings:
  confirm_before_execute: true
  dry_run_default: false

steps:
  - config: "mode/rename.yaml"
    label: "1. リネーム"
  - config: "mode/sort.yaml"
    label: "2. 振り分け"
```

各ステップの `confirm_before_execute` と `dry_run_default` は使用せず、Pipeline側の設定を全体へ適用します。実行中に1件でも失敗した場合は、前段の結果に依存する後続操作を中止します。

PNG_Prompt_Sort をステップに含める場合も、そのプリセットの `duplicate_handling` が機能します。`overwrite`（上書き）、`sequential`（連番）、`skip`（スキップ）を指定できます。`ask` は Pipeline では使用できず、ファイルを操作する前に設定エラーになります。PNG_Prompt_Sort を単独で実行する場合は、従来どおり `ask` を使用できます。

同じ実行内の複数のファイルが同じ保存先を指すと、計画段階でエラーになり、ファイル操作を開始せずに停止します。エラーには衝突した両方のファイル名が表示されます。以前は無警告で上書きされていたため、保存先が重なる既存のプリセットは停止する可能性があります。

### 保存先と実行時の安全確認

Sort の `dest` と Clean の `destination` は、ドットを含む名前でも常にディレクトリとして扱われます。たとえば `dest: "D:\\Output\\v2.0"` はファイル名ではなくディレクトリを表し、元のファイル名がその後ろに追加されます。

計画後のプレビュー確認中に対象ファイルが別のプロセスによって変更、置換、または削除された場合、そのファイルは操作されずにエラーになります。

### Clean モードの高度な機能

Clean モードでは、以下の高度なオプションが使用できます：

#### deletion の削除方式

```yaml
deletion:
  enabled: true
  delete_mode: "trash"
  strings:
    - ".tmp"
```

| 設定項目 | 値 | 既定値 | 説明 |
|---|---|---|---|
| `deletion.delete_mode` | `trash` / `permanent` | `trash` | `trash` は復元可能なゴミ箱へ移動し、`permanent` は完全に削除します。 |

既定の削除方式は、以前の完全削除からゴミ箱への移動に変わりました。Windows から直接実行した場合は Windows のゴミ箱へ移動します。WSL から実行した場合は Windows のゴミ箱ではなく、対象ドライブ直下の `.Trash-1000/` フォルダーへ移動します。

#### sorting_rules の拡張オプション

```yaml
sorting_rules:
  - search: "*r=3*"
    source_directory: "D:\\Source\\Folder"  # 特定のディレクトリからのみ対象
    destination: "D:\\Destination\\Folder"
    action: "copy"  # または "move"
    recursive: true  # サブフォルダも検索
    rename_pattern:  # ファイル名から文字列を削除/置換
      "{zpi$r=3}": ""  # {zpi$r=3} を削除
      "old_text": "new_text"  # 置換も可能
```

#### cleanup の拡張オプション

```yaml
cleanup:
  enabled: true
  after_sorting: true  # 🔥 NEW: sorting_rules の後に cleanup を実行（デフォルト: false）
  recursive: true
  pattern: "*{zpi$}*"  # 特定のパターンを含むファイルのみ対象
  target_directories:  # 特定のディレクトリのみ対象
    - "D:\\Folder1"
    - "D:\\Folder2"
  custom_patterns:  # ファイル名から削除する正規表現パターン
    - "\\{zpi\\$r=3\\}"
```

##### `after_sorting` オプション（実行順序の制御）

デフォルトでは、Clean モードは以下の順序で実行されます：

```
1. deletion（削除）
2. cleanup（クリーンアップ）
3. sorting_rules（振り分け）
```

しかし、`after_sorting: true` を設定すると：

```
1. deletion（削除）
2. sorting_rules（振り分け）← 先に実行
3. cleanup（クリーンアップ）← 後で実行
```

**ユースケース：**
- 元ファイルをコピー後、元ファイルの名前も変更したい場合
- 例：`{tag}` 付きファイルを別フォルダにコピー → 元ファイルから `{tag}` を削除

**実例：**

```yaml
# r=3 タグ付きファイルを ai_r5 フォルダーにコピーして、元ファイルもクリーンアップ

cleanup:
  enabled: true
  after_sorting: true  # sorting_rules の後に実行
  pattern: "*{zpi$r=3}*"
  custom_patterns:
    - "\\{zpi\\$r=3\\}"

sorting_rules:
  - search: "*{zpi$r=3}*"
    destination: "D:\\AI_Storage_PNG\\ai_r5"
    action: "copy"  # コピー（元ファイルは残る）
    rename_pattern:
      "{zpi$r=3}": ""  # コピー先ではタグを削除

# 実行結果:
# 1. 元ファイル（{zpi$r=3} 付き）を ai_r5 にコピー（タグなし）
# 2. 元ファイルからもタグを削除
# 3. 次回実行時は、元ファイルにタグがないので処理対象外 ✅
```

完全な例と高度なフィルタリングオプションについては、`mode/samples/`ディレクトリを参照してください。

---

## よくある使い方

### ケース1: ダウンロードフォルダの整理

1. ダウンロードフォルダ用の設定ファイルを作成
2. ツールを実行してプリセットを選択
3. プレビューを確認して実行

### ケース2: 写真の整理

解像度、アスペクト比、日付でフィルタリングして写真を効率的に整理できます。

### ケース3: 動画管理

ファイルサイズ、長さ、またはコンテンツタグで動画を整理できます。

### ケース4: 自動化ワークフロー

1. ダウンロードから振り分け
2. 外部ツール（Zippla等）でラベリング
3. Cleanモードで再整理

### ケース5: AI生成画像の自動整理（PNG画像からプロンプトを読み取り）

Stable Diffusion、NovelAI、ComfyUI等で生成したAI画像は、PNG形式のメタデータにプロンプト情報が埋め込まれています。
Loot Organizerは、この**PNG画像に埋め込まれたプロンプト情報を自動的に読み取り**、使用されている**LoRA名を検出**して、設定したフォルダに自動振り分けします。

#### 仕組み

1. **PNG画像のメタデータからプロンプトを読み取り**
2. プロンプト内の `<lora:名前:重み>` 形式のLoRAを検出
3. マッピングファイルでLoRA名とフォルダ名を照合
4. 最初にマッチしたLoRAのフォルダに自動移動
5. 数千枚でも一瞬で処理完了

#### 手順

1. Stable Diffusion等で画像を生成
2. LoRA名→フォルダ名のマッピングファイル `lora_map.yaml` を作成
3. PNG_Prompt_Sortモードを実行して自動振り分け
4. 最初にマッチしたLoRAのフォルダに移動

#### マッピングファイル例

```yaml
mappings:
  "character_alice": "キャラクター＿アリス"
  "style_anime": "スタイル＿アニメ"
  "pose_sitting": "ポーズ＿座り"
```

#### 特徴

- PNG, JPG, JPEG, WebP 形式に対応
- `<lora:名前:重み>` 形式のLoRAを検出
- 複数の入力フォルダに対応
- 重複ファイル処理方法を選択可能（上書き/連番/確認/スキップ）

---

## AIエージェント向け

### ユーザーの設定作成支援方法

ユーザーが設定ファイルの作成を依頼した場合、以下の手順に従ってください：

1. **目的を確認**
   - どのフォルダを整理したいか？
   - 最終的な構造は？

2. **ファイルタイプを確認**
   - どのタイプのファイル？（動画、画像、ドキュメント等）
   - 特定のファイルパターンはあるか？

3. **条件を確認**
   - サイズ要件は？
   - 日付要件は？
   - 画像解像度の要件は？

4. **YAMLを生成**
   - `meta`セクションから開始
   - `settings`セクションを追加
   - 適切なルールを追加（Sortモードは`move_rules`、Cleanモードは`sorting_rules`）
   - 必要に応じて`exclusions`を追加

5. **設定を説明**
   - 各ルールをわかりやすく説明
   - マッチするファイルの例を示す
   - 潜在的な問題を警告

### 対話例

```
ユーザー: 「ダウンロードフォルダを整理したい」

AI: 「設定ファイルの作成をお手伝いしますね！いくつか質問させてください：

1. ダウンロードフォルダの場所は？
2. どのタイプのファイルを整理したいですか？（動画、画像、ドキュメント等）
3. それぞれどこに移動させたいですか？
4. 除外したいファイルはありますか？

これらに答えていただければ、すぐに使える設定ファイルを生成します」
```

---

## トラブルシューティング

### 問題: プリセットがメニューに表示されない

**解決方法:**
- YAMLファイルが`mode/`直下にあることを確認（`mode/samples/`ではない）
- `meta`セクションが存在し、正しくフォーマットされているか確認
- YAMLの構文エラーをチェック（インデント等）

### 問題: ファイルが移動されない

**解決方法:**
- ドライランモードが有効になっていないか確認
- 確認プロンプトで'y'を入力したか確認
- ログファイルでエラーを確認

### 問題: 絵文字が文字化けする

**解決方法:**
- Windows: コマンドプロンプトではなくWindows Terminalを使用
- 絵文字対応フォント（Cascadia Code等）を使用

---

## ライセンス

個人利用・商用利用ともに自由に使用可能です。

---

## コントリビューション

IssueやPull Requestを歓迎します！

---

**👤 作成者**: YoyogiPinball
**📅 最終更新**: 2026-08-15

---
---

<a name="english"></a>

# 📁 Loot Organizer

A personal file organization tool with a two-step workflow for efficient file management.

English | [日本語](#-loot-organizer)

---

## Table of Contents

- [What is Loot Organizer?](#what-is-loot-organizer)
- [Key Features](#key-features)
- [Quick Start](#quick-start-1)
  - [Installation](#installation-1)
  - [Configuration](#configuration-1)
  - [Run](#run-1)
- [🎯 Initial Setup Guide](#-initial-setup-guide)
- [🤖 Using AI to Create YAML Configs](#-using-ai-to-create-yaml-configs)
- [Configuration Guide](#configuration-guide-1)
- [Common Use Cases](#common-use-cases)
- [For AI Agents](#for-ai-agents)
- [Troubleshooting](#troubleshooting-1)
- [License](#license-1)

---

## What is Loot Organizer?

Loot Organizer is a CLI tool that helps you efficiently organize scattered files in your download folder and other directories. It automates file sorting, cleanup, and deletion based on user-defined rules in YAML format.

**Especially powerful for AI-generated images (Stable Diffusion / NovelAI / ComfyUI, etc.), it automatically reads prompt information embedded in PNG images, detects used LoRA names, and sorts them into folders.**

---

## Key Features

- **📤 Sort Mode**: Organize large amounts of messy files (e.g., download folders) into categorized directories
- **✨ Clean Mode**: Cleanup file names, delete unwanted files, and re-organize
  - **source_directory**: Target files only from specific directories
  - **rename_pattern**: Remove/replace strings from filenames during move/copy
  - **recursive**: Recursively search subfolders
  - **cleanup pattern & target_directories**: Cleanup only specific patterns/directories
- **🎨 PNG_Prompt_Sort Mode**:
  - **Automatically analyzes prompts embedded in PNG images**
  - **Detects used LoRAs and auto-sorts** (supports Stable Diffusion / NovelAI / ComfyUI)
  - Process thousands of images instantly
  - Flexible folder mapping via configuration files
- **🔄 Batch Mode**: Execute multiple presets sequentially
- **🎮 Interactive UI**: Navigate with ↑↓ arrow keys
- **🛡️ Safe Operations**: Always preview before execution
- **💾 Preset Management**: Save and reuse your favorite settings
- **📊 Version Display**: Shows version number and commit hash at startup

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/YoyogiPinball/Loot_Organizer.git
cd Loot_Organizer

# Install dependencies
pip install -r requirements.txt
```

The dependencies include `Send2Trash`, which moves deleted files to the trash.

### Configuration

Copy a sample configuration and edit it for your environment:

```bash
# Copy sample
cp mode/samples/downloads_sort.yaml mode/my_sort.yaml
```

**Windows:**
```cmd
notepad mode\my_sort.yaml
```

**Linux/Mac:**
```bash
nano mode/my_sort.yaml
```

### Run

**Windows:**
```cmd
run.bat
```

**Linux/Mac:**
```bash
python -m src.loot_manager
```

---

## 🎯 Initial Setup Guide

### For Sort/Clean Mode (File Organization)

**1. Copy Sample Configuration**
```bash
cp mode/samples/downloads_sort.yaml mode/my_organizer.yaml
```

**Windows:**
```cmd
copy mode\samples\downloads_sort.yaml mode\my_organizer.yaml
```

**2. Edit Configuration File**

Open `mode/my_organizer.yaml` in your editor:

```cmd
notepad mode\my_organizer.yaml
```

Customize these settings for your environment:

```yaml
settings:
  target_directory: "C:\\Users\\YOUR_NAME\\Downloads"  # Folder to organize

move_rules:
  - name: "Videos"
    destination: "D:\\Videos"  # Destination folder
    patterns:
      - "*.mp4"
      - "*.mkv"
```

**3. Run**
```cmd
run.bat
```

Select your configuration from the menu and execute!

---

### For AI Image Organization Mode (Stable Diffusion, etc.)

**1. Copy Sample Configuration**
```bash
cp mode/samples/ai_image_sort.yaml mode/my_ai_sorter.yaml
cp mode/samples/lora_map_sample.yaml mode/lora_map.yaml
```

**Windows:**
```cmd
copy mode\samples\ai_image_sort.yaml mode\my_ai_sorter.yaml
copy mode\samples\lora_map_sample.yaml mode\lora_map.yaml
```

**2. Edit Mapping File**

Open `mode/lora_map.yaml` and register your LoRA names:

```yaml
mappings:
  "your_lora_name": "Destination_Folder_Name"
  "character_alice": "Characters_Alice"
  "style_anime": "Styles_Anime"
```

**3. Edit Configuration File**

Open `mode/my_ai_sorter.yaml` and update paths:

```yaml
settings:
  source_directories:
    - "D:\\StableDiffusion\\outputs"  # Folder where AI images are saved
  output_directory: "D:\\AI_Images\\Sorted"  # Parent folder for sorted files
  mapping_file: "mode/lora_map.yaml"
```

**4. Run**
```cmd
run.bat
```

---

## 🤖 Using AI to Create YAML Configs

Finding YAML configuration difficult? **Use AI agents (Claude, ChatGPT, etc.) to easily create config files!**

### Example Prompt 1: Organize Downloads Folder

```
Create a Loot Organizer configuration file.

Purpose: Organize Downloads folder (C:\Users\YourName\Downloads)
Destinations:
- Videos (*.mp4, *.mkv) → D:\Videos
- Images (*.jpg, *.png) → D:\Pictures
- Documents (*.pdf, *.docx) → D:\Documents
- Files over 10MB → D:\LargeFiles

Use mode/samples/downloads_sort.yaml as reference.
```

### Example Prompt 2: AI Image Organization

```
Create a lora_map.yaml file for Loot Organizer.

I want to organize the following LoRA names into folders:
- pikachu → Pikachu
- eevee → Eevee
- anime_style_v2 → Anime_Styles
- realistic_face → Realistic_Faces

Use the format from mode/samples/lora_map_sample.yaml.
```

### Example Prompt 3: Delete Old Files

```
Create a Loot Organizer configuration to:

- Delete files older than 30 days
- But exclude files containing "important"
- Cleanup filenames containing emojis

Use mode/samples/cleanup_files.yaml as reference.
```

**Tips:**
- Show sample files (`mode/samples/`) and ask "create based on this"
- Be specific about conditions (paths, extensions, sizes, etc.)
- Ask "what's the recommended setting?" for unclear options

---

## Configuration Guide

### Basic Structure

Every YAML configuration file requires the following `meta` section:

```yaml
meta:
  name: "My File Organizer"
  icon: "📤"
  mode: "Sort"  # Sort, Clean, or PNG_Prompt_Sort
  description: "Organize download folder"

settings:
  target_directory: "/path/to/folder"
  enable_logging: true
  confirm_before_execute: true
  dry_run_default: false

  preview:
    mode: "both"  # head / tail / both / all
    count: 5

  logging:
    log_success: true
    log_directory: "logs"
```

### Pipeline Mode

Pipeline runs multiple presets in order with one preview and confirmation. Later steps scan a virtual file state that includes renames, moves, copies, and deletions planned by earlier steps. Preview and dry-run never modify real files.

```yaml
meta:
  name: "One-stop workflow"
  icon: "🚀"
  mode: "Pipeline"
  description: "Rename, sort, then clean files"

settings:
  confirm_before_execute: true
  dry_run_default: false

steps:
  - config: "mode/rename.yaml"
    label: "1. Rename"
  - config: "mode/sort.yaml"
    label: "2. Sort"
```

Step-level `confirm_before_execute` and `dry_run_default` values are ignored; the Pipeline settings apply to the whole run. If an operation fails, later operations stop because they may depend on the failed result.

When a Pipeline includes a PNG_Prompt_Sort step, that preset's `duplicate_handling` setting is honored. You can use `overwrite`, `sequential`, or `skip`. `ask` is not available in Pipeline and causes a configuration error before any file operation starts. Standalone PNG_Prompt_Sort runs can continue to use `ask` as before.

If multiple files in the same run point to the same destination, planning fails and stops before any file operation starts. The error shows both conflicting filenames. Because previous versions overwrote such files without warning, existing presets with overlapping destinations may now stop.

### Destinations and Execution-Time Safety

Sort `dest` and Clean `destination` values are always treated as directories, even when their names contain dots. For example, `dest: "D:\\Output\\v2.0"` identifies a directory rather than a filename, and the source filename is appended to it.

If another process modifies, replaces, or deletes a target file while you are reviewing the plan, Loot Organizer reports an error and does not operate on that file.

### Advanced Features in Clean Mode

Clean mode supports the following advanced options:

#### deletion Mode

```yaml
deletion:
  enabled: true
  delete_mode: "trash"
  strings:
    - ".tmp"
```

| Setting | Values | Default | Description |
|---|---|---|---|
| `deletion.delete_mode` | `trash` / `permanent` | `trash` | `trash` moves files to recoverable trash; `permanent` deletes them permanently. |

The default changed from permanent deletion to moving files to the trash. When run directly on Windows, files go to the Windows Recycle Bin. When run from WSL, files go to the `.Trash-1000/` folder at the root of the target drive instead of the Windows Recycle Bin.

#### sorting_rules Extended Options

```yaml
sorting_rules:
  - search: "*r=3*"
    source_directory: "D:\\Source\\Folder"  # Target only specific directory
    destination: "D:\\Destination\\Folder"
    action: "copy"  # or "move"
    recursive: true  # Search subfolders
    rename_pattern:  # Remove/replace strings from filenames
      "{zpi$r=3}": ""  # Remove {zpi$r=3}
      "old_text": "new_text"  # Replacement also supported
```

#### cleanup Extended Options

```yaml
cleanup:
  enabled: true
  after_sorting: true  # 🔥 NEW: Execute cleanup after sorting_rules (default: false)
  recursive: true
  pattern: "*{zpi$}*"  # Target only files matching pattern
  target_directories:  # Target only specific directories
    - "D:\\Folder1"
    - "D:\\Folder2"
  custom_patterns:  # Regex patterns to remove from filenames
    - "\\{zpi\\$r=3\\}"
```

##### `after_sorting` Option (Execution Order Control)

By default, Clean mode executes in this order:

```
1. deletion
2. cleanup
3. sorting_rules
```

However, with `after_sorting: true`:

```
1. deletion
2. sorting_rules  ← Executed first
3. cleanup        ← Executed after
```

**Use Cases:**
- Copy files first, then rename the originals
- Example: Copy `{tag}` files to another folder → Remove `{tag}` from originals

**Example:**

```yaml
# Copy r=3 tagged files to ai_r5 folder, then cleanup originals

cleanup:
  enabled: true
  after_sorting: true  # Execute after sorting_rules
  pattern: "*{zpi$r=3}*"
  custom_patterns:
    - "\\{zpi\\$r=3\\}"

sorting_rules:
  - search: "*{zpi$r=3}*"
    destination: "D:\\AI_Storage_PNG\\ai_r5"
    action: "copy"  # Copy (originals remain)
    rename_pattern:
      "{zpi$r=3}": ""  # Remove tag in destination

# Results:
# 1. Copy original files ({zpi$r=3} included) to ai_r5 (tag removed)
# 2. Remove tag from original files
# 3. Next run: No files match (originals have no tag) ✅
```

For complete examples and advanced filtering options, see `mode/samples/` directory.

---

## Common Use Cases

### Case 1: Organize Downloads

1. Create a configuration file for your downloads folder
2. Run the tool and select your preset
3. Preview the changes and confirm

### Case 2: Photo Organization

Filter by resolution, aspect ratio, or date to organize your photos efficiently.

### Case 3: Video Management

Organize videos by file size, duration, or content tags.

### Case 4: Automated Workflow

1. Sort files from downloads
2. Use external tool (like Zippla) to label files
3. Use Clean mode to reorganize labeled files

### Case 5: AI-Generated Image Auto-Organization (Reading Prompts from PNG)

AI-generated images from Stable Diffusion, NovelAI, ComfyUI, etc. have prompt information embedded in PNG metadata.
Loot Organizer **automatically reads the prompt information embedded in PNG images**, **detects LoRA names** used, and automatically sorts them into configured folders.

#### How It Works

1. **Reads prompts from PNG image metadata**
2. Detects LoRAs in the format: `<lora:name:weight>`
3. Matches LoRA names with folder names in mapping file
4. Automatically moves to the first matching LoRA folder
5. Processes thousands of images instantly

#### Steps

1. Generate images with Stable Diffusion (or other AI tools)
2. Create a `lora_map.yaml` file mapping LoRA names to folder names
3. Run PNG_Prompt_Sort mode to automatically sort images by LoRA
4. Images are moved to the first matching LoRA folder

#### Example `lora_map.yaml`

```yaml
mappings:
  "character_alice": "Characters_Alice"
  "style_anime": "Styles_Anime"
  "pose_sitting": "Poses_Sitting"
```

#### Features

- Supports PNG, JPG, JPEG, WebP formats
- Detects LoRA in format: `<lora:name:weight>`
- Handles multiple input directories
- Configurable duplicate file handling (overwrite/sequential/ask/skip)

---

## For AI Agents

### How to Help Users Create Configurations

When a user asks you to help create a configuration file, follow these steps:

1. **Ask about their goal**
   - What folders do they want to organize?
   - What is the final structure they want?

2. **Ask about file types**
   - What types of files? (videos, images, documents, etc.)
   - Any specific file patterns? (screenshots, downloads, etc.)

3. **Ask about conditions**
   - Size requirements?
   - Date requirements?
   - Image resolution requirements?

4. **Generate the YAML**
   - Start with the `meta` section
   - Add `settings` section
   - Add appropriate rules (`move_rules` for Sort, `sorting_rules` for Clean)
   - Add `exclusions` if needed

5. **Explain the configuration**
   - Explain each rule in simple terms
   - Show examples of files that would match
   - Warn about potential issues

### Example Dialogue

```
User: "I want to organize my download folder."

AI: "I'll help you create a configuration! Let me ask a few questions:

1. Where is your download folder located?
2. What types of files do you want to organize? (videos, images, documents, etc.)
3. Where do you want each type to go?
4. Are there any files you want to exclude or ignore?

Once you answer these, I'll generate a ready-to-use configuration file for you."
```

---

## Troubleshooting

### Problem: Preset not showing in menu

**Solution:**
- Check that the YAML file is in `mode/` (not `mode/samples/`)
- Verify the `meta` section exists and is correctly formatted
- Check for YAML syntax errors (indentation, etc.)

### Problem: Files are not being moved

**Solution:**
- Check if dry run mode is enabled
- Verify you entered 'y' at the confirmation prompt
- Check the log file for errors

### Problem: Emojis are garbled

**Solution:**
- Windows: Use Windows Terminal instead of Command Prompt
- Use an emoji-compatible font (Cascadia Code, etc.)

---

## License

Free to use for personal and commercial purposes.

---

## Contributing

Issues and pull requests are welcome!

---

**👤 Author**: YoyogiPinball
**📅 Last Updated**: 2026-08-15
