"""
file_organizer.py
ファイル整理ツール

ダウンロードフォルダ内のファイルを設定に従って自動整理します。
"""

import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from colorama import Fore, Style, init
import yaml
from fnmatch import fnmatch

init(autoreset=True)


class FileOrganizer:
    def __init__(self, config_path="config.yaml"):
        """初期化"""
        self.script_dir = Path(__file__).parent
        self.config_path = self.script_dir / config_path
        self.config = self._load_config()
        self.logger = self._setup_logger() if self.config['settings']['enable_logging'] else None
        self.move_results = defaultdict(list)  # 移動先ごとの結果を保存
        
    def _load_config(self):
        """設定ファイル読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"{Fore.RED}エラー: 設定ファイルが見つかりません: {self.config_path}")
            exit(1)
        except yaml.YAMLError as e:
            print(f"{Fore.RED}エラー: 設定ファイルの読み込みに失敗: {e}")
            exit(1)
    
    def _setup_logger(self):
        """ログ設定（日毎に1ファイル、追記形式）"""
        log_dir = self.script_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # 日付ごとのログファイル
        log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        
        logger = logging.getLogger('FileOrganizer')
        logger.setLevel(logging.INFO)
        
        # 既存のハンドラをクリア（複数回実行時の重複を防ぐ）
        logger.handlers.clear()
        
        # ファイルハンドラ（追記モード）
        fh = logging.FileHandler(log_file, encoding='utf-8', mode='a')
        fh.setLevel(logging.INFO)
        
        # フォーマッターは設定しない（カスタムフォーマットで出力）
        logger.addHandler(fh)
        
        return logger
    
    def _log(self, message):
        """ログ出力"""
        if self.logger:
            self.logger.info(message)
    
    def _is_excluded(self, path):
        """除外対象かチェック"""
        exclusions = self.config.get('exclusions', {})
        name = path.name
        
        # 完全一致チェック
        if name in exclusions.get('exact_names', []):
            return True
        
        # パターンチェック
        for pattern in exclusions.get('patterns', []):
            if fnmatch(name, pattern):
                return True
        
        return False
    
    def scan_targets(self):
        """移動対象をスキャン（downloadsフォルダ直下のファイルのみ）"""
        results = defaultdict(list)
        
        # 基準パスの解決
        base_path = Path(self.config['settings']['base_path'])
        if not base_path.is_absolute():
            base_path = (self.script_dir / base_path).resolve()
        
        if not base_path.exists():
            print(f"{Fore.RED}エラー: 基準パスが存在しません: {base_path}")
            return results
        
        # downloadsフォルダ直下のファイルのみを取得
        try:
            all_items = list(base_path.iterdir())
        except PermissionError:
            print(f"{Fore.RED}エラー: フォルダへのアクセスが拒否されました: {base_path}")
            return results
        
        files = [item for item in all_items if item.is_file()]
        
        # 各ファイルに対してルールを適用（最初にマッチしたルールのみ）
        for file_path in files:
            # 除外チェック
            if self._is_excluded(file_path):
                continue
            
            # ルールを上から順にチェック
            for rule in self.config.get('move_rules', []):
                if not rule.get('enabled', True):
                    continue
                
                # パターンマッチング
                if fnmatch(file_path.name, rule['pattern']):
                    dest = Path(rule['dest'])
                    results[str(dest)].append({
                        'file': file_path,
                        'description': rule['description']
                    })
                    break  # 最初にマッチしたルールで終了
        
        return results
    
    def display_preview(self, scan_results):
        """実行前プレビュー表示"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}📋 移動対象プレビュー")
        print(f"{Fore.CYAN}{'='*60}\n")
        
        if not scan_results:
            print(f"{Fore.LIGHTBLACK_EX}  対象ファイルなし")
            print(f"\n{Fore.CYAN}{'='*60}\n")
            return False
        
        total_files = 0
        
        for dest, items in sorted(scan_results.items()):
            count = len(items)
            total_files += count
            print(f"{Fore.YELLOW}📁 {dest} {Fore.GREEN}({count}件)")
            
            # 最初の5件のみ表示
            for item in items[:5]:
                print(f"  {Fore.GREEN}├─ {item['file'].name}")
            
            if count > 5:
                print(f"  {Fore.LIGHTBLACK_EX}└─ ... 他{count-5}件")
            print()
        
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.WHITE}合計: {Fore.GREEN}{total_files}{Fore.WHITE}件")
        print(f"{Fore.CYAN}{'='*60}\n")
        
        return True
    
    def execute_moves(self, scan_results):
        """実際の移動処理"""
        success_count = 0
        error_count = 0
        errors = []
        
        print(f"\n{Fore.CYAN}🚀 移動処理を開始します...\n")
        
        # ログ: セッション開始
        if self.logger:
            self._log("=" * 80)
            self._log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [実行開始]")
            self._log("=" * 80)
            self._log("")
        
        for dest, items in sorted(scan_results.items()):
            dest_path = Path(dest)
            dest_path.mkdir(parents=True, exist_ok=True)
            
            print(f"{Fore.YELLOW}📁 {dest}")
            
            # ログ: 移動先グループ開始
            if self.logger:
                self._log(f"[{dest} へ移動 - {len(items)}件]")
            
            for item in items:
                file_path = item['file']
                try:
                    dest_file = dest_path / file_path.name
                    shutil.move(str(file_path), str(dest_file))
                    
                    print(f"  {Fore.GREEN}✓ {file_path.name}")
                    
                    # 結果を保存
                    self.move_results[dest].append({
                        'name': file_path.name,
                        'success': True
                    })
                    
                    # ログ
                    if self.logger:
                        self._log(f"  ✓ {file_path.name}")
                    
                    success_count += 1
                    
                except Exception as e:
                    msg = f"{file_path.name}: {str(e)}"
                    print(f"  {Fore.RED}✗ {msg}")
                    
                    # 結果を保存
                    self.move_results[dest].append({
                        'name': file_path.name,
                        'success': False,
                        'error': str(e)
                    })
                    
                    # ログ
                    if self.logger:
                        self._log(f"  ✗ {file_path.name} (エラー: {str(e)})")
                    
                    error_count += 1
                    errors.append(msg)
            
            print()
            
            # ログ: 移動先グループ終了
            if self.logger:
                self._log("")
        
        # ログ: セッション終了
        if self.logger:
            self._log("-" * 80)
            self._log(f"実行結果: 成功 {success_count}件 / 失敗 {error_count}件")
            self._log(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self._log("=" * 80)
            self._log("")  # 空行で次の実行と区切る
        
        return success_count, error_count, errors
    
    def display_result(self, success_count, error_count, errors):
        """実行結果サマリ表示"""
        print(f"\n{Fore.CYAN}{'='*64}")
        print(f"{Fore.CYAN}📊 実行結果サマリ")
        print(f"{Fore.CYAN}{'='*64}\n")
        
        if self.move_results:
            print(f"{Fore.YELLOW}【移動先別の内訳】\n")
            
            for dest, items in sorted(self.move_results.items()):
                success_items = [item for item in items if item['success']]
                count = len(success_items)
                
                if count > 0:
                    print(f"{Fore.YELLOW}📁 {dest} {Fore.GREEN}({count}件)")
                    
                    # 最初の5件表示
                    for i, item in enumerate(success_items[:5]):
                        prefix = "├─" if i < min(4, count-1) else "└─"
                        print(f"  {Fore.GREEN}{prefix} {item['name']}")
                    
                    if count > 5:
                        print(f"  {Fore.LIGHTBLACK_EX}└─ ... 他{count-5}件")
                    print()
        
        print(f"{Fore.WHITE}合計: {Fore.GREEN}{success_count + error_count}{Fore.WHITE}件移動")
        print(f"{Fore.GREEN}成功: {success_count}件 {Fore.WHITE}/ ", end="")
        
        if error_count > 0:
            print(f"{Fore.RED}失敗: {error_count}件")
            
            if errors:
                print(f"\n{Fore.YELLOW}【エラー詳細】")
                for error in errors[:5]:
                    print(f"  {Fore.RED}• {error}")
                if len(errors) > 5:
                    print(f"  {Fore.LIGHTBLACK_EX}... 他{len(errors)-5}件")
        else:
            print(f"{Fore.GREEN}失敗: 0件")
        
        print(f"\n{Fore.CYAN}{'='*64}\n")
    
    def run(self):
        """メイン処理"""
        print(f"{Fore.MAGENTA}🎀 ファイル整理ツール 🎀\n")
        
        # スキャン
        scan_results = self.scan_targets()
        
        # プレビュー表示
        has_targets = self.display_preview(scan_results)
        
        if not has_targets:
            print(f"{Fore.YELLOW}移動対象がありませんでした")
            return
        
        # 確認
        if self.config['settings']['confirm_before_execute']:
            response = input(f"{Fore.YELLOW}この内容で実行しますか? (y/N): {Style.RESET_ALL}").strip().lower()
            
            if response != 'y':
                print(f"{Fore.YELLOW}キャンセルしました")
                return
        
        # 実行
        success_count, error_count, errors = self.execute_moves(scan_results)
        
        # 結果表示
        self.display_result(success_count, error_count, errors)
        
        # Enter待ち
        input(f"{Fore.CYAN}Enterキーを押すと終了します...{Style.RESET_ALL}")


if __name__ == "__main__":
    try:
        organizer = FileOrganizer()
        organizer.run()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}中断されました")
    except Exception as e:
        print(f"\n{Fore.RED}予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        input(f"\n{Fore.CYAN}Enterキーを押すと終了します...{Style.RESET_ALL}")
