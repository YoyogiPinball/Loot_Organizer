@echo off
REM Loot Organizer起動スクリプト
REM UTF-8出力を有効化（絵文字表示対応）
chcp 65001 > nul

REM カレントディレクトリをスクリプトの場所に変更
cd /d "%~dp0"

REM Pythonスクリプトを実行
python src/loot_manager.py

REM 終了時に一時停止（エラー確認用）
pause
