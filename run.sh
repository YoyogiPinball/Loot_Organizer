#!/bin/bash
# Loot Organizer起動スクリプト (Linux/Mac用)

# カレントディレクトリをスクリプトの場所に変更
cd "$(dirname "$0")"

# Pythonスクリプトを実行（モジュールとして）
python3 -m src.loot_manager

# 終了時に一時停止（エラー確認用）
read -p "Press Enter to continue..."
