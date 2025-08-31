#!/usr/bin/env python3
"""
Backend Compliance Test Runner

設計書準拠性テストの実行スクリプト
- 全ての準拠性テストを実行
- HTML/JSON レポート生成
- CI/CD 統合対応
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from app.tests.reports.compliance_reporter import ComplianceReporter
except ImportError:
    print("⚠️  ComplianceReporter が見つかりません。テストレポート生成をスキップします。")
    ComplianceReporter = None


class ComplianceTestRunner:
    """準拠性テスト実行クラス"""
    
    def __init__(self, output_dir: Path = None):
        """初期化
        
        Args:
            output_dir: テスト結果出力ディレクトリ
        """
        self.project_root = project_root
        self.output_dir = output_dir or (project_root / "test_results")
        self.output_dir.mkdir(exist_ok=True)
        
        # テストコマンド設定
        self.test_commands = {
            "compliance": [
                "python", "-m", "pytest", 
                "app/tests/compliance/",
                "-v", "--tb=short",
                f"--junitxml={self.output_dir}/compliance-results.xml"
            ],
            "contracts": [
                "python", "-m", "pytest",
                "app/tests/contracts/", 
                "-v", "--tb=short",
                f"--junitxml={self.output_dir}/contracts-results.xml"
            ],
            "all": [
                "python", "-m", "pytest",
                "app/tests/",
                "-v", "--tb=short", 
                f"--junitxml={self.output_dir}/all-results.xml"
            ]
        }
    
    def run_tests(self, test_suite: str = "all") -> Dict[str, Any]:
        """テスト実行
        
        Args:
            test_suite: 実行するテストスイート ("compliance", "contracts", "all")
            
        Returns:
            テスト結果辞書
        """
        print(f"🚀 準拠性テスト実行開始: {test_suite}")
        print(f"📁 出力ディレクトリ: {self.output_dir}")
        
        if test_suite not in self.test_commands:
            raise ValueError(f"未知のテストスイート: {test_suite}")
        
        command = self.test_commands[test_suite]
        
        # 環境変数設定
        env = os.environ.copy()
        env['PYTHONPATH'] = str(self.project_root)
        
        try:
            # pytest実行
            start_time = datetime.now()
            result = subprocess.run(
                command,
                cwd=self.project_root,
                env=env,
                capture_output=True,
                text=True,
                timeout=600  # 10分タイムアウト
            )
            end_time = datetime.now()
            
            # 実行時間計算
            duration = (end_time - start_time).total_seconds()
            
            # 結果構築
            test_result = {
                "suite": test_suite,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "return_code": result.returncode,
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(command)
            }
            
            # 結果出力
            if result.returncode == 0:
                print(f"✅ テスト成功 ({duration:.2f}秒)")
            else:
                print(f"❌ テスト失敗 (終了コード: {result.returncode}, {duration:.2f}秒)")
                
            if result.stdout:
                print("📄 標準出力:")
                print(result.stdout)
                
            if result.stderr:
                print("⚠️  標準エラー:")
                print(result.stderr)
                
            return test_result
            
        except subprocess.TimeoutExpired:
            print("❌ テスト実行がタイムアウトしました")
            return {
                "suite": test_suite,
                "success": False,
                "error": "timeout",
                "duration_seconds": 600
            }
        except Exception as e:
            print(f"❌ テスト実行中にエラーが発生しました: {e}")
            return {
                "suite": test_suite,
                "success": False,
                "error": str(e),
                "duration_seconds": 0
            }
    
    def generate_compliance_report(self) -> bool:
        """準拠性レポート生成
        
        Returns:
            レポート生成成功フラグ
        """
        if ComplianceReporter is None:
            print("⚠️  ComplianceReporter が利用できません。レポート生成をスキップします。")
            return False
            
        try:
            print("📊 準拠性レポート生成中...")
            
            reporter = ComplianceReporter()
            report = reporter.generate_report()
            
            # HTMLレポート保存
            html_path = self.output_dir / "compliance_report.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(report.html_report)
            
            # JSONレポート保存
            json_path = self.output_dir / "compliance_report.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(report.json_report, f, indent=2, ensure_ascii=False)
            
            print(f"📋 HTMLレポート: {html_path}")
            print(f"📋 JSONレポート: {json_path}")
            print(f"📈 総合準拠度: {report.overall_compliance:.1f}%")
            
            return True
            
        except Exception as e:
            print(f"❌ レポート生成エラー: {e}")
            return False
    
    def save_test_summary(self, test_results: List[Dict[str, Any]]):
        """テスト実行サマリー保存
        
        Args:
            test_results: テスト結果のリスト
        """
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_suites": len(test_results),
            "successful_suites": sum(1 for r in test_results if r.get("success", False)),
            "total_duration": sum(r.get("duration_seconds", 0) for r in test_results),
            "results": test_results
        }
        
        summary_path = self.output_dir / "test_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"📊 テストサマリー: {summary_path}")
        
        # GitHub Actions 用の出力
        if os.environ.get('GITHUB_ACTIONS'):
            success_rate = (summary["successful_suites"] / summary["total_suites"] * 100) if summary["total_suites"] > 0 else 0
            print(f"::set-output name=success_rate::{success_rate:.1f}")
            print(f"::set-output name=total_duration::{summary['total_duration']:.2f}")


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="Backend Compliance Test Runner")
    parser.add_argument(
        "--suite", 
        choices=["compliance", "contracts", "all"],
        default="all",
        help="実行するテストスイート"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="テスト結果出力ディレクトリ"
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="レポート生成のみ実行"
    )
    
    args = parser.parse_args()
    
    # テストランナー初期化
    runner = ComplianceTestRunner(output_dir=args.output_dir)
    
    if args.report_only:
        # レポート生成のみ
        success = runner.generate_compliance_report()
        sys.exit(0 if success else 1)
    
    # テスト実行
    results = []
    
    if args.suite == "all":
        # 全てのスイートを個別実行
        for suite in ["compliance", "contracts"]:
            result = runner.run_tests(suite)
            results.append(result)
    else:
        # 指定されたスイートのみ実行
        result = runner.run_tests(args.suite)
        results.append(result)
    
    # サマリー保存
    runner.save_test_summary(results)
    
    # 準拠性レポート生成
    runner.generate_compliance_report()
    
    # 全体結果判定
    all_success = all(r.get("success", False) for r in results)
    
    if all_success:
        print("🎉 全テストが成功しました！")
        sys.exit(0)
    else:
        print("❌ 一部のテストが失敗しました。")
        sys.exit(1)


if __name__ == "__main__":
    main()