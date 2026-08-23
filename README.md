> 最終更新: 2026-08-23（Sun）20:06

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

Python 3.12 以上が必要です。

```bash
# リポジトリをクローン
git clone https://github.com/YoyogiPinball/Loot_Organizer.git
cd Loot_Organizer
```

**Windows:**
```cmd
py -3.12 -m pip install -r requirements.txt
```

**Linux/macOS:**
```bash
python3 -m pip install -r requirements.txt
```

依存関係には、削除対象をゴミ箱へ送るための `Send2Trash` が含まれます。

### 設定

サンプル設定をコピーします。
初回は本番フォルダを指定せず、移動してもよいファイルのコピーだけを入れたテスト用フォルダで試してください。

**Windows:**
```cmd
copy mode\samples\downloads_sort.yaml mode\my_sort.yaml
```

**Linux/macOS:**
```bash
cp mode/samples/downloads_sort.yaml mode/my_sort.yaml
```

テスト用の入力フォルダと振り分け先を作り、動画ファイルなどを数件コピーします。
元ファイルそのものをテスト用フォルダへ移動しないでください。

**Windows:**
```cmd
mkdir "%USERPROFILE%\loot-organizer-test\inbox"
mkdir "%USERPROFILE%\loot-organizer-test\videos"
copy "C:\path\to\sample.mp4" "%USERPROFILE%\loot-organizer-test\inbox\"
```

**Linux/macOS:**
```bash
mkdir -p "$HOME/loot-organizer-test/inbox" "$HOME/loot-organizer-test/videos"
cp /path/to/sample.mp4 "$HOME/loot-organizer-test/inbox/"
```

**Windows:**
```cmd
notepad mode\my_sort.yaml
```

**Linux/macOS:**
```bash
nano mode/my_sort.yaml
```

`settings.target_directory` をテスト用の `inbox` に、試すルールの `dest` をテスト用の振り分け先に変更します。
パス内の `YOUR_USERNAME` は実際のユーザー名に置き換えます。
`dry_run_default: true` はそのままにしてください。

> Clean モードの削除は、既定では `delete_mode: "trash"` によりゴミ箱へ送られます。
> `delete_mode: "permanent"` を指定すると完全削除されるため、テストが終わるまで指定しないでください。

### 実行

**Windows:**
```cmd
run.bat
```

**Linux/macOS:**
```bash
python3 -m src.loot_manager
```

メニューから `my_sort.yaml` を選びます。
**プレビュー**は、これから行う操作の一覧です。
**dry-run** はその一覧を表示しても実際のファイル操作を行わない実行方式です。
一覧が意図どおりなら `dry_run_default: false` に変更し、まずテスト用のコピーだけで実際の移動を確認してから本番用のパスへ変更してください。

---

## 🎯 初回セットアップガイド

どのモードでも、初回は専用のテスト用フォルダにファイルのコピーを数件置き、`dry_run_default: true` で確認します。
Clean モードの `deletion` は既定でゴミ箱へ送りますが、`delete_mode: "permanent"` は完全削除です。

### Sort/Cleanモードの場合（ファイル整理）

**1. サンプル設定をコピー**
```bash
cp mode/samples/downloads_sort.yaml mode/my_sort.yaml
```

**Windows:**
```cmd
copy mode\samples\downloads_sort.yaml mode\my_sort.yaml
```

**2. 設定ファイルを編集**

エディタで `mode/my_sort.yaml` を開きます：

```cmd
notepad mode\my_sort.yaml
```

テスト用の入力フォルダに動画ファイルのコピーを置き、以下のようにテスト用のパスを指定します。
`YOUR_USERNAME` は実際のユーザー名に置き換えてください。
`move_rules` は1ルールにつき1つの `pattern` を指定します。

```yaml
settings:
  target_directory: "C:\\Users\\YOUR_USERNAME\\loot-organizer-test\\inbox"
  dry_run_default: true

move_rules:
  - pattern: "*.mp4"
    dest: "C:\\Users\\YOUR_USERNAME\\loot-organizer-test\\videos"
    description: "MP4動画"

  - pattern: "*.mkv"
    dest: "C:\\Users\\YOUR_USERNAME\\loot-organizer-test\\videos"
    description: "MKV動画"
```

**3. 実行**
```cmd
run.bat
```

メニューから `my_sort.yaml` を選択します。
プレビューは予定されている操作の一覧で、dry-run 中は一覧を確認しても実際のファイルは動きません。
一覧に納得したら `dry_run_default: false` に変更し、テスト用のコピーで実行結果を確認してから本番フォルダへ切り替えます。

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

テスト用フォルダにAI画像のコピーを数件置きます。
`mode/my_ai_sorter.yaml` を開いて、そのテスト用パスを指定します。

```yaml
settings:
  source_directories:
    - "C:\\Users\\YOUR_USERNAME\\loot-organizer-test\\ai-input"
  output_directory: "C:\\Users\\YOUR_USERNAME\\loot-organizer-test\\ai-sorted"
  mapping_file: "mode/lora_map.yaml"
  dry_run_default: true
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

目的：Downloadsフォルダ（C:\Users\YOUR_USERNAME\Downloads）を整理
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
- character_alpha → キャラクター_アルファ
- character_beta → キャラクター_ベータ
- style_watercolor → スタイル_水彩
- style_monochrome → スタイル_モノクロ

mode/samples/lora_map_sample.yaml の形式で作成してください。
```

### プロンプト例3: 日付でファイルをアーカイブ

```
Loot OrganizerのSortモード設定で、以下を実現してください：

- 更新日時が2026-01-01より前のファイルを D:\Archive に移動
- ただし "important" が含まれるファイルは除外
- `filters` の日付条件は `date: {before: "2026-01-01"}` と絶対日付で指定

mode/samples/downloads_sort.yaml を参考にしてください。
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
  dry_run_default: true  # 初回は true で結果を確認し、納得したら false に変更

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
  dry_run_default: true  # 初回は true で結果を確認し、納得したら false に変更

steps:
  - config: "mode/rename.yaml"
    label: "1. リネーム"
  - config: "mode/sort.yaml"
    label: "2. 振り分け"
```

各ステップの `confirm_before_execute` と `dry_run_default` は使用せず、Pipeline側の設定を全体へ適用します。実行中に1件でも失敗した場合は、前段の結果に依存する後続操作を中止します。

PNG_Prompt_Sort をステップに含める場合も、そのプリセットの `duplicate_handling` が機能します。`overwrite`（上書き）、`sequential`（連番）、`skip`（スキップ）を指定でき、未指定時の既定値は `skip` です。既定では実ディスク上の既存ファイルを保護しますが、`overwrite` を明示した場合は上書きします。`ask` は Pipeline では使用できず、ファイルを操作する前に設定エラーになります。PNG_Prompt_Sort を単独で実行する場合は従来どおり `ask` を使用でき、確認時に「上書き」を選ぶと既存ファイルを上書きします。

同じ実行内の複数の操作が同じ保存先を指す場合、先に計画された操作だけを実行し、後の操作はスキップして処理を続行します。実ファイルが保存先に既に存在する場合も既定ではスキップします。ただし PNG_Prompt_Sort で `duplicate_handling: overwrite` を明示した場合は上書きします。

### パスの書き方

設定に書くパスは Windows 形式のまま書けます。WSL / Linux から実行した場合は、起動時に自動で変換されます。

| 書き方 | Windows で実行 | WSL / Linux で実行 |
|---|---|---|
| `D:\Videos` | そのまま | `/mnt/d/Videos` に変換 |
| `/mnt/d/Videos` | そのまま | そのまま |
| `\\wsl.localhost\Ubuntu\home\me\x` | そのまま | `/home/me/x` に変換（v2.2.2〜） |
| `\\wsl$\Ubuntu\home\me\x` | そのまま | 同上（v2.2.2〜） |
| `\\server\share\x`（ネットワーク共有） | そのまま | **非対応** |

YAML では `\` をエスケープして `"D:\\Videos"` と書きます。`/` 区切りで `"D:/Videos"` と書いても構いません。

`\\wsl.localhost\...` と `\\wsl$\...` は、`\` の直後のディストリビューション名が実行中の WSL（環境変数 `WSL_DISTRO_NAME`）と一致する場合だけ変換します。大文字小文字は区別しません。別のディストリビューションを指している場合は、推測して変換せず設定エラーで停止します。他のディストリビューションのファイルシステムは、WSL の中からは同じパスで見えないためです。

Pipeline の `steps[].config`（次に読むプリセットのパス）にも同じ変換が働きます（v2.2.2〜）。

### 保存先と実行時の安全確認

v2.1.0 以降の主な安全策は次のとおりです。

| 安全策 | 動作 |
|---|---|
| 保存先が埋まっている場合 | 既定では、実ファイルまたは同一実行内の予約先が存在すると、その操作をスキップして続行します。PNG_Prompt_Sort で `duplicate_handling: overwrite` を明示した場合は、実ファイルを上書きします |
| 保存先パス | delete 以外は最終ファイルパスとして計画し、設定の `dest` / `destination` はディレクトリとして扱います |
| 実行直前の検査 | source の指紋と保存先の存在を再確認し、計画後に状態が変わっていれば操作しません |
| 削除 | `deletion.delete_mode` の既定値は、復元可能な `trash` です |

`skip_if_exists: true` を明示したルールと、PNG_Prompt_Sort で `duplicate_handling: skip` を明示した設定は、既存ファイルを繰り返し検出することを想定した正常系として件数だけを結果表示します。未指定または `false` のルールで既定の保護が働いた場合は、手動確認が必要なスキップとしてファイル名を表示します。

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

ファイル名パターン、ファイルサイズ、または絶対日付で動画を整理できます。

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

### 問題: 「UNC パスには別のディストリビューション名が指定されているため変換できません」と出る

WSL から実行したとき、設定に書いた `\\wsl.localhost\<名前>\...` の `<名前>` が、いま動いている WSL と違う場合に出ます。

**解決方法:**
- `wsl -l -v` で実行中のディストリビューション名を確認し、設定の綴りを合わせる（大文字小文字は区別しません）
- 別のディストリビューションのファイルを扱いたい場合は、そのディストリビューションから実行する
- WSL 以外の環境（素の Linux 等）では、そもそも UNC ではなく通常のパスを書く

### 問題: 対象ファイルが 0 件のまま何も起きない

**解決方法:**
- パスの綴りを確認する。特にネットワーク共有（`\\server\share\...`）は WSL から実行すると解決できません
- `recursive: true` が必要なのに指定されていないか確認する
- パターンの大文字小文字を確認する。**Windows は区別しませんが、WSL は区別します。** 両方で使う設定なら `*.[jJ][pP][gG]` のように書くか、実際の拡張子に合わせてください

---

## ライセンス

個人利用・商用利用ともに自由に使用可能です。

---

## コントリビューション

IssueやPull Requestを歓迎します！

---

**👤 作成者**: YoyogiPinball

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
- [Quick Start](#quick-start)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Run](#run)
- [🎯 Initial Setup Guide](#-initial-setup-guide)
- [🤖 Using AI to Create YAML Configs](#-using-ai-to-create-yaml-configs)
- [Configuration Guide](#configuration-guide)
- [Common Use Cases](#common-use-cases)
- [For AI Agents](#for-ai-agents)
- [Troubleshooting](#troubleshooting)
- [License](#license)

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

Python 3.12 or later is required.

```bash
# Clone the repository
git clone https://github.com/YoyogiPinball/Loot_Organizer.git
cd Loot_Organizer
```

**Windows:**
```cmd
py -3.12 -m pip install -r requirements.txt
```

**Linux/macOS:**
```bash
python3 -m pip install -r requirements.txt
```

The dependencies include `Send2Trash`, which moves deleted files to the trash.

### Configuration

Copy a sample configuration.
For the first run, use a dedicated test folder containing only copies of files you can safely move; do not point the configuration at a production folder.

**Windows:**
```cmd
copy mode\samples\downloads_sort.yaml mode\my_sort.yaml
```

**Linux/macOS:**
```bash
cp mode/samples/downloads_sort.yaml mode/my_sort.yaml
```

Create a test input folder and destination, then copy in a few files such as a video.
Do not move the originals into the test folder.

**Windows:**
```cmd
mkdir "%USERPROFILE%\loot-organizer-test\inbox"
mkdir "%USERPROFILE%\loot-organizer-test\videos"
copy "C:\path\to\sample.mp4" "%USERPROFILE%\loot-organizer-test\inbox\"
```

**Linux/macOS:**
```bash
mkdir -p "$HOME/loot-organizer-test/inbox" "$HOME/loot-organizer-test/videos"
cp /path/to/sample.mp4 "$HOME/loot-organizer-test/inbox/"
```

**Windows:**
```cmd
notepad mode\my_sort.yaml
```

**Linux/macOS:**
```bash
nano mode/my_sort.yaml
```

Set `settings.target_directory` to the test `inbox`, change the `dest` of the rule you are testing to the test destination, and leave `dry_run_default: true` unchanged.
Replace `YOUR_USERNAME` in paths with your actual user name.

> Clean mode sends deletions to the trash by default with `delete_mode: "trash"`.
> `delete_mode: "permanent"` deletes files permanently, so do not enable it while testing.

### Run

**Windows:**
```cmd
run.bat
```

**Linux/macOS:**
```bash
python3 -m src.loot_manager
```

Select `my_sort.yaml` from the menu.
A **preview** is the list of operations that are about to run.
A **dry-run** displays that list but performs no file operations.
If the list is correct, set `dry_run_default: false`, test the real move using only the copied files, and only then change the paths to production folders.

---

## 🎯 Initial Setup Guide

For every mode, start with a dedicated test folder containing a few copied files and keep `dry_run_default: true` for the first run.
Clean mode sends `deletion` targets to the trash by default, while `delete_mode: "permanent"` deletes them permanently.

### For Sort/Clean Mode (File Organization)

**1. Copy Sample Configuration**
```bash
cp mode/samples/downloads_sort.yaml mode/my_sort.yaml
```

**Windows:**
```cmd
copy mode\samples\downloads_sort.yaml mode\my_sort.yaml
```

**2. Edit Configuration File**

Open `mode/my_sort.yaml` in your editor:

```cmd
notepad mode\my_sort.yaml
```

Put copies of a few video files in the test input folder, then use test-only paths as shown below.
Replace `YOUR_USERNAME` with your actual user name.
Each `move_rules` entry accepts one `pattern`.

```yaml
settings:
  target_directory: "C:\\Users\\YOUR_USERNAME\\loot-organizer-test\\inbox"
  dry_run_default: true

move_rules:
  - pattern: "*.mp4"
    dest: "C:\\Users\\YOUR_USERNAME\\loot-organizer-test\\videos"
    description: "MP4 videos"

  - pattern: "*.mkv"
    dest: "C:\\Users\\YOUR_USERNAME\\loot-organizer-test\\videos"
    description: "MKV videos"
```

**3. Run**
```cmd
run.bat
```

Select `my_sort.yaml` from the menu.
The preview lists the planned operations; during a dry-run, the files do not move.
After the list looks correct, set `dry_run_default: false`, verify the result with the copied test files, and only then switch to production folders.

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

Put copies of a few AI-generated images in a test folder.
Open `mode/my_ai_sorter.yaml` and point it to test-only paths:

```yaml
settings:
  source_directories:
    - "C:\\Users\\YOUR_USERNAME\\loot-organizer-test\\ai-input"
  output_directory: "C:\\Users\\YOUR_USERNAME\\loot-organizer-test\\ai-sorted"
  mapping_file: "mode/lora_map.yaml"
  dry_run_default: true
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

Purpose: Organize Downloads folder (C:\Users\YOUR_USERNAME\Downloads)
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
- character_alpha → Characters_Alpha
- character_beta → Characters_Beta
- style_watercolor → Styles_Watercolor
- style_monochrome → Styles_Monochrome

Use the format from mode/samples/lora_map_sample.yaml.
```

### Example Prompt 3: Archive Files by Date

```
Create a Loot Organizer Sort mode configuration to:

- Move files last modified before 2026-01-01 to D:\Archive
- But exclude files containing "important"
- Express the `filters` date condition as the absolute value `date: {before: "2026-01-01"}`

Use mode/samples/downloads_sort.yaml as reference.
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
  dry_run_default: true  # Keep true for the first run; set false after reviewing the result

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
  dry_run_default: true  # Keep true for the first run; set false after reviewing the result

steps:
  - config: "mode/rename.yaml"
    label: "1. Rename"
  - config: "mode/sort.yaml"
    label: "2. Sort"
```

Step-level `confirm_before_execute` and `dry_run_default` values are ignored; the Pipeline settings apply to the whole run. If an operation fails, later operations stop because they may depend on the failed result.

When a Pipeline includes a PNG_Prompt_Sort step, that preset's `duplicate_handling` setting is honored. You can use `overwrite`, `sequential`, or `skip`; the default is `skip` when omitted. Existing files on disk are protected by default, but explicitly setting `overwrite` replaces them. `ask` is not available in Pipeline and causes a configuration error before any file operation starts. Standalone PNG_Prompt_Sort runs can continue to use `ask`; choosing “Overwrite” at the prompt replaces the existing file.

If multiple operations in the same run point to the same destination, only the first planned operation runs; later operations are skipped and processing continues. When a real file already occupies the destination, the operation is also skipped by default. PNG_Prompt_Sort is the exception: explicitly setting `duplicate_handling: overwrite` replaces the real file.

### Writing Paths

Paths in your configuration can stay in Windows form. When you run from WSL / Linux, they are converted automatically at startup.

| Written as | Run on Windows | Run on WSL / Linux |
|---|---|---|
| `D:\Videos` | as-is | converted to `/mnt/d/Videos` |
| `/mnt/d/Videos` | as-is | as-is |
| `\\wsl.localhost\Ubuntu\home\me\x` | as-is | converted to `/home/me/x` (v2.2.2+) |
| `\\wsl$\Ubuntu\home\me\x` | as-is | same as above (v2.2.2+) |
| `\\server\share\x` (network share) | as-is | **not supported** |

In YAML, escape backslashes as `"D:\\Videos"`, or use forward slashes: `"D:/Videos"`.

`\\wsl.localhost\...` and `\\wsl$\...` are converted only when the distribution name matches the running WSL distribution (environment variable `WSL_DISTRO_NAME`). The comparison ignores case. If it names a different distribution, the tool stops with a configuration error rather than guessing — another distribution's filesystem is not reachable at the same path from inside WSL.

The same conversion applies to `steps[].config` in Pipeline mode (v2.2.2+).

### Destinations and Execution-Time Safety

The main safety measures in v2.1.0 and later are:

| Safety measure | Behavior |
|---|---|
| Occupied destination | By default, an operation is skipped if a real file or an earlier in-run reservation exists. PNG_Prompt_Sort overwrites a real file when `duplicate_handling: overwrite` is explicitly set |
| Destination paths | Every non-delete operation plans a final file path; configured `dest` / `destination` values are treated as directories |
| Pre-execution checks | Source fingerprints and destination existence are checked again, and changed state is not operated on |
| Deletion | `deletion.delete_mode` defaults to recoverable `trash` |

Rules with `skip_if_exists: true` and PNG_Prompt_Sort settings with an explicit `duplicate_handling: skip` treat repeated existing files as an expected condition and show only a count in the result. When default protection applies to an omitted or `false` rule setting, those skips include filenames for manual review.

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

Organize videos by filename pattern, file size, or an absolute date.

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

### Problem: "UNC パスには別のディストリビューション名が指定されているため変換できません"

Raised when running from WSL if the `<name>` in a configured `\\wsl.localhost\<name>\...` path does not match the running WSL distribution.

**Solution:**
- Run `wsl -l -v` to see the running distribution name and match the spelling (case is ignored)
- To work with another distribution's files, run the tool from that distribution
- Outside WSL (plain Linux, etc.), use ordinary paths rather than UNC

### Problem: Nothing happens — zero files matched

**Solution:**
- Check the path. Network shares (`\\server\share\...`) cannot be resolved when running from WSL
- Check whether the rule needs `recursive: true`
- Check the case of your pattern. **Windows is case-insensitive; WSL is case-sensitive.** For a config used on both, write `*.[jJ][pP][gG]` or match the actual extension

---

## License

Free to use for personal and commercial purposes.

---

## Contributing

Issues and pull requests are welcome!

---

**👤 Author**: YoyogiPinball
