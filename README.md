# 📁 Loot Organizer

A personal file organization tool with a two-step workflow for efficient file management.

個人用ファイル整理ツール - 2段階ワークフローによるファイル管理システム

---

## 🎯 What is Loot Organizer? / Loot Organizerとは？

**English:**
Loot Organizer is a CLI tool that helps you efficiently organize scattered files in your download folder and other directories. It automates file sorting, cleanup, and deletion based on user-defined rules in YAML format.

**日本語:**
Loot Organizerは、ダウンロードフォルダなどに散らばったファイルを効率的に整理するためのCLIツールです。YAML形式で定義したルールに基づいて、ファイルの振り分け、クリーンアップ、削除を自動化します。

---

## ✨ Key Features / 主な機能

- **📤 Sort Mode**: Organize large amounts of messy files (e.g., download folders) into categorized directories
  - **振り分けモード**: 大量のファイルでゴチャついたフォルダ（ダウンロードフォルダなど）を各種フォルダへ整理整頓
- **✨ Clean Mode**: Cleanup file names, delete unwanted files, and re-organize
  - **クリーンアップモード**: ファイル名整理、不要ファイル削除、再振り分け
- **🎨 PNG_Prompt_Sort Mode**: Automatically sort AI-generated images by LoRA metadata in prompts
  - **PNG_Prompt_Sortモード**: AI生成画像をプロンプトのLoRAメタデータで自動振り分け
- **🔄 Batch Mode**: Execute multiple presets sequentially
  - **連続実行モード**: 複数のプリセットを順番に実行
- **🎮 Interactive UI**: Navigate with ↑↓ arrow keys
  - **インタラクティブUI**: ↑↓キーで操作
- **🛡️ Safe Operations**: Always preview before execution
  - **安全な操作**: 実行前に必ずプレビュー表示
- **💾 Preset Management**: Save and reuse your favorite settings
  - **プリセット管理**: よく使う設定を保存・再利用

---

## 🚀 Quick Start / クイックスタート

### 1. Installation / インストール

\`\`\`bash
# Clone the repository
git clone https://github.com/YoyogiPinball/Loot_Organizer.git
cd Loot_Organizer

# Install dependencies
pip install -r requirements.txt
\`\`\`

### 2. Configuration / 設定

Copy a sample configuration and edit it for your environment:

サンプル設定をコピーして、自分の環境に合わせて編集：

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

### 3. Run / 実行

**Windows:**
```cmd
run.bat
```

**Linux/Mac:**
```bash
python src/loot_manager.py
```

---

## 📋 Configuration Guide / 設定ガイド

### Basic Structure / 基本構造

Every YAML configuration file requires the following \`meta\` section:

すべてのYAML設定ファイルには以下の\`meta\`セクションが必要です：

\`\`\`yaml
meta:
  name: "My File Organizer"
  icon: "📤"
  mode: "Sort"  # Sort, Clean, or PNG_Prompt_Sort
  description: "Organize download folder"

settings:
  target_directory: "/path/to/folder"
  enable_logging: true
  confirm_before_execute: true
  dry_run_default: true

  preview:
    mode: "head"  # head / tail / both / all
    count: 5

  logging:
    log_success: true
    log_directory: "logs"
\`\`\`

For complete examples and advanced filtering options, see \`configs/samples/\` directory.

完全な例と高度なフィルタリングオプションについては、\`configs/samples/\`ディレクトリを参照してください。

---

## 💡 Common Use Cases / よくある使い方

### Case 1: Organize Downloads / ダウンロードフォルダの整理

1. Create a configuration file for your downloads folder / ダウンロードフォルダ用の設定ファイルを作成
2. Run the tool and select your preset / ツールを実行してプリセットを選択
3. Preview the changes and confirm / プレビューを確認して実行

### Case 2: Photo Organization / 写真の整理

Filter by resolution, aspect ratio, or date to organize your photos efficiently.

解像度、アスペクト比、日付でフィルタリングして写真を効率的に整理できます。

### Case 3: Video Management / 動画管理

Organize videos by file size, duration, or content tags.

ファイルサイズ、長さ、またはコンテンツタグで動画を整理できます。

### Case 4: Automated Workflow / 自動化ワークフロー

1. Sort files from downloads / ダウンロードから振り分け
2. Use external tool (like Zippla) to label files / 外部ツールでラベリング
3. Use Clean mode to reorganize labeled files / Cleanモードで再整理

### Case 5: AI-Generated Image Organization / AI生成画像の整理

**English:**
Organize AI-generated images (from Stable Diffusion, NovelAI, ComfyUI, etc.) by LoRA names embedded in the metadata.

1. Generate images with Stable Diffusion (or other AI tools)
2. Create a `lora_map.yaml` file mapping LoRA names to folder names
3. Run PNG_Prompt_Sort mode to automatically sort images by LoRA
4. Images with multiple LoRAs are copied to all matching folders

**Example `lora_map.yaml`:**
```yaml
mappings:
  "character_alice": "Characters/Alice"
  "style_anime": "Styles/Anime"
  "pose_sitting": "Poses/Sitting"
```

**Features:**
- Supports PNG, JPG, JPEG, WebP formats
- Detects LoRA in format: `<lora:name:weight>`
- Handles multiple input directories
- Auto-renames duplicates with sequential numbers

**日本語:**
Stable Diffusion、NovelAI、ComfyUI等で生成したAI画像を、メタデータに埋め込まれたLoRA名で整理します。

1. Stable Diffusion等で画像を生成
2. LoRA名→フォルダ名のマッピングファイル `lora_map.yaml` を作成
3. PNG_Prompt_Sortモードを実行して自動振り分け
4. 複数LoRAを含む画像は該当する全フォルダにコピーされます

**マッピングファイル例:**
```yaml
mappings:
  "character_alice": "キャラクター/アリス"
  "style_anime": "スタイル/アニメ"
  "pose_sitting": "ポーズ/座り"
```

**特徴:**
- PNG, JPG, JPEG, WebP 形式に対応
- `<lora:名前:重み>` 形式のLoRAを検出
- 複数の入力フォルダに対応
- 重複ファイルは連番で自動リネーム

---

## 🤖 For AI Agents / AIエージェント向け

### How to Help Users Create Configurations / ユーザーの設定作成支援方法

When a user asks you to help create a configuration file, follow these steps:

ユーザーが設定ファイルの作成を依頼した場合、以下の手順に従ってください：

1. **Ask about their goal** / 目的を確認
   - What folders do they want to organize?
   - What is the final structure they want?

2. **Ask about file types** / ファイルタイプを確認
   - What types of files? (videos, images, documents, etc.)
   - Any specific file patterns? (screenshots, downloads, etc.)

3. **Ask about conditions** / 条件を確認
   - Size requirements?
   - Date requirements?
   - Image resolution requirements?

4. **Generate the YAML** / YAMLを生成
   - Start with the \`meta\` section
   - Add \`settings\` section
   - Add appropriate rules (\`move_rules\` for Sort, \`sorting_rules\` for Clean)
   - Add \`exclusions\` if needed

5. **Explain the configuration** / 設定を説明
   - Explain each rule in simple terms
   - Show examples of files that would match
   - Warn about potential issues

### Example Dialogue / 対話例

\`\`\`
User: "I want to organize my download folder."

AI: "I'll help you create a configuration! Let me ask a few questions:

1. Where is your download folder located?
2. What types of files do you want to organize? (videos, images, documents, etc.)
3. Where do you want each type to go?
4. Are there any files you want to exclude or ignore?

Once you answer these, I'll generate a ready-to-use configuration file for you."
\`\`\`

## 🔧 Troubleshooting / トラブルシューティング

### Problem: Preset not showing in menu

**解決方法:**
- Check that the YAML file is in \`configs/\` (not \`configs/samples/\`)
- Verify the \`meta\` section exists and is correctly formatted
- Check for YAML syntax errors (indentation, etc.)

### Problem: Files are not being moved

**解決方法:**
- Check if dry run mode is enabled
- Verify you entered 'y' at the confirmation prompt
- Check the log file for errors

### Problem: Emojis are garbled

**解決方法:**
- Windows: Use Windows Terminal instead of Command Prompt
- Use an emoji-compatible font (Cascadia Code, etc.)

---

## 📜 License / ライセンス

Free to use for personal and commercial purposes.

個人利用・商用利用ともに自由に使用可能です。

---

## 🙏 Contributing / コントリビューション

Issues and pull requests are welcome!

IssueやPull Requestを歓迎します！

---

**👤 Author / 作成者**: YoyogiPinball
**📅 Last Updated / 最終更新**: 2025-11-16
