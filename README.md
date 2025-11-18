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

---

## 主な機能

- **📤 振り分けモード（Sort）**: 大量のファイルでゴチャついたフォルダ（ダウンロードフォルダなど）を各種フォルダへ整理整頓
- **✨ クリーンアップモード（Clean）**: ファイル名整理、不要ファイル削除、再振り分け
- **🎨 PNG_Prompt_Sortモード**: AI生成画像をプロンプトのLoRAメタデータで自動振り分け
- **🔄 連続実行モード**: 複数のプリセットを順番に実行
- **🎮 インタラクティブUI**: ↑↓キーで操作
- **🛡️ 安全な操作**: 実行前に必ずプレビュー表示
- **💾 プリセット管理**: よく使う設定を保存・再利用

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

### 設定

サンプル設定をコピーして、自分の環境に合わせて編集します：

```bash
# サンプルをコピー
cp configs/samples/downloads_sort.yaml configs/my_sort.yaml
```

**Windows:**
```cmd
notepad configs\my_sort.yaml
```

**Linux/Mac:**
```bash
nano configs/my_sort.yaml
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
cp configs/samples/downloads_sort.yaml configs/my_organizer.yaml
```

**Windows:**
```cmd
copy configs\samples\downloads_sort.yaml configs\my_organizer.yaml
```

**2. 設定ファイルを編集**

エディタで `configs/my_organizer.yaml` を開きます：

```cmd
notepad configs\my_organizer.yaml
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
cp configs/samples/ai_image_sort.yaml configs/my_ai_sorter.yaml
cp configs/samples/lora_map_sample.yaml configs/lora_map.yaml
```

**Windows:**
```cmd
copy configs\samples\ai_image_sort.yaml configs\my_ai_sorter.yaml
copy configs\samples\lora_map_sample.yaml configs\lora_map.yaml
```

**2. マッピングファイルを編集**

`configs/lora_map.yaml` を開いて、自分の使っているLoRA名を登録：

```yaml
mappings:
  "your_lora_name": "振り分け先フォルダ名"
  "character_alice": "キャラクター＿アリス"
  "style_anime": "スタイル＿アニメ"
```

**3. 設定ファイルを編集**

`configs/my_ai_sorter.yaml` を開いて、パスを変更：

```yaml
settings:
  source_directories:
    - "D:\\StableDiffusion\\outputs"  # AI画像が保存されているフォルダ
  output_directory: "D:\\AI_Images\\Sorted"  # 振り分け先の親フォルダ
  mapping_file: "configs/lora_map.yaml"
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

configs/samples/downloads_sort.yaml を参考にして作成してください。
```

### プロンプト例2: AI画像整理

```
Loot Organizerの lora_map.yaml を作成してください。

以下のLoRA名をフォルダに振り分けたいです：
- pikachu → ピカチュウ
- eevee → イーブイ
- anime_style_v2 → アニメスタイル
- realistic_face → リアル顔

configs/samples/lora_map_sample.yaml の形式で作成してください。
```

### プロンプト例3: 古いファイル削除

```
Loot Organizerの設定で、以下を実現してください：

- 30日以上前のファイルを削除
- ただし "important" が含まれるファイルは除外
- ファイル名に絵文字が含まれるものはクリーンアップ

configs/samples/cleanup_files.yaml を参考にしてください。
```

**コツ：**
- サンプルファイル（`configs/samples/`）を見せて「これを参考に作って」と頼む
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

完全な例と高度なフィルタリングオプションについては、`configs/samples/`ディレクトリを参照してください。

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

### ケース5: AI生成画像の整理

Stable Diffusion、NovelAI、ComfyUI等で生成したAI画像を、メタデータに埋め込まれたLoRA名で整理します。

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
- YAMLファイルが`configs/`直下にあることを確認（`configs/samples/`ではない）
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
**📅 最終更新**: 2025-11-18

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

---

## Key Features

- **📤 Sort Mode**: Organize large amounts of messy files (e.g., download folders) into categorized directories
- **✨ Clean Mode**: Cleanup file names, delete unwanted files, and re-organize
- **🎨 PNG_Prompt_Sort Mode**: Automatically sort AI-generated images by LoRA metadata in prompts
- **🔄 Batch Mode**: Execute multiple presets sequentially
- **🎮 Interactive UI**: Navigate with ↑↓ arrow keys
- **🛡️ Safe Operations**: Always preview before execution
- **💾 Preset Management**: Save and reuse your favorite settings

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

### Configuration

Copy a sample configuration and edit it for your environment:

```bash
# Copy sample
cp configs/samples/downloads_sort.yaml configs/my_sort.yaml
```

**Windows:**
```cmd
notepad configs\my_sort.yaml
```

**Linux/Mac:**
```bash
nano configs/my_sort.yaml
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
cp configs/samples/downloads_sort.yaml configs/my_organizer.yaml
```

**Windows:**
```cmd
copy configs\samples\downloads_sort.yaml configs\my_organizer.yaml
```

**2. Edit Configuration File**

Open `configs/my_organizer.yaml` in your editor:

```cmd
notepad configs\my_organizer.yaml
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
cp configs/samples/ai_image_sort.yaml configs/my_ai_sorter.yaml
cp configs/samples/lora_map_sample.yaml configs/lora_map.yaml
```

**Windows:**
```cmd
copy configs\samples\ai_image_sort.yaml configs\my_ai_sorter.yaml
copy configs\samples\lora_map_sample.yaml configs\lora_map.yaml
```

**2. Edit Mapping File**

Open `configs/lora_map.yaml` and register your LoRA names:

```yaml
mappings:
  "your_lora_name": "Destination_Folder_Name"
  "character_alice": "Characters_Alice"
  "style_anime": "Styles_Anime"
```

**3. Edit Configuration File**

Open `configs/my_ai_sorter.yaml` and update paths:

```yaml
settings:
  source_directories:
    - "D:\\StableDiffusion\\outputs"  # Folder where AI images are saved
  output_directory: "D:\\AI_Images\\Sorted"  # Parent folder for sorted files
  mapping_file: "configs/lora_map.yaml"
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

Use configs/samples/downloads_sort.yaml as reference.
```

### Example Prompt 2: AI Image Organization

```
Create a lora_map.yaml file for Loot Organizer.

I want to organize the following LoRA names into folders:
- pikachu → Pikachu
- eevee → Eevee
- anime_style_v2 → Anime_Styles
- realistic_face → Realistic_Faces

Use the format from configs/samples/lora_map_sample.yaml.
```

### Example Prompt 3: Delete Old Files

```
Create a Loot Organizer configuration to:

- Delete files older than 30 days
- But exclude files containing "important"
- Cleanup filenames containing emojis

Use configs/samples/cleanup_files.yaml as reference.
```

**Tips:**
- Show sample files (`configs/samples/`) and ask "create based on this"
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

For complete examples and advanced filtering options, see `configs/samples/` directory.

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

### Case 5: AI-Generated Image Organization

Organize AI-generated images (from Stable Diffusion, NovelAI, ComfyUI, etc.) by LoRA names embedded in the metadata.

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
- Check that the YAML file is in `configs/` (not `configs/samples/`)
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
**📅 Last Updated**: 2025-11-18
