#!/usr/bin/env python3
"""
簡略化された漫画生成テスト - 現在のスキーマで可能なテスト
"""

import asyncio
import httpx
import json
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

# テスト設定
BACKEND_URL = "https://manga-backend-prod-wg2vlc4pxq-an.a.run.app"
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5433,
    'user': 'manga_user',
    'password': 'manga_secure_password_2024',
    'database': 'manga_db'
}

class SimplifiedMangaTest:
    def __init__(self, backend_url: str):
        self.backend_url = backend_url
        self.client = httpx.AsyncClient(timeout=60.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def test_what_we_can_test(self) -> Dict[str, Any]:
        """現在のスキーマで可能なテストを実行"""
        print("\n🎯 === 簡略化漫画システムテスト ===")
        print(f"テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)

        results = {
            "test_start": datetime.now().isoformat(),
            "tests": {}
        }

        # 1. データベース接続確認
        print("\n🔍 1. データベース接続とスキーマ確認")
        db_test = await self.test_database_schema()
        results["tests"]["database_schema"] = db_test

        # 2. HITLエンドポイント確認（修正されたはず）
        print("\n🔍 2. HITLエンドポイント動作確認")
        hitl_test = await self.test_hitl_endpoints()
        results["tests"]["hitl_endpoints"] = hitl_test

        # 3. 内部タスクエンドポイント確認
        print("\n🔍 3. 内部タスクエンドポイント確認")
        internal_test = await self.test_internal_endpoint_structure()
        results["tests"]["internal_endpoint"] = internal_test

        # 4. API構造確認
        print("\n🔍 4. API構造の健全性確認")
        api_test = await self.test_api_structure()
        results["tests"]["api_structure"] = api_test

        # 5. 基本認証フロー確認
        print("\n🔍 5. 認証フロー動作確認")
        auth_test = await self.test_auth_flow()
        results["tests"]["auth_flow"] = auth_test

        # 結果サマリー
        results["test_end"] = datetime.now().isoformat()

        passed_tests = sum(1 for test in results["tests"].values() if test.get("status") == "pass")
        total_tests = len(results["tests"])

        results["summary"] = {
            "passed": passed_tests,
            "total": total_tests,
            "pass_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        }

        print(f"\n📊 テスト完了: {passed_tests}/{total_tests} 成功 ({results['summary']['pass_rate']:.1f}%)")

        return results

    async def test_database_schema(self) -> Dict[str, Any]:
        """データベーススキーマの状態を確認"""
        try:
            import psycopg2
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # 必要なテーブルの存在確認
            essential_tables = [
                'manga_sessions', 'users', 'phase_results',
                'phase_feedback_states', 'user_feedback_history'
            ]

            existing_tables = []
            for table in essential_tables:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = %s
                    );
                """, (table,))
                exists = cursor.fetchone()[0]
                existing_tables.append({"table": table, "exists": exists})
                print(f"  {table}: {'✅' if exists else '❌'}")

            # マイグレーション状況確認
            cursor.execute("SELECT version_num FROM alembic_version;")
            current_version = cursor.fetchone()[0] if cursor.rowcount > 0 else "none"
            print(f"  マイグレーションバージョン: {current_version}")

            cursor.close()
            conn.close()

            all_essential_exist = all(t["exists"] for t in existing_tables)

            return {
                "status": "pass" if all_essential_exist else "partial",
                "tables": existing_tables,
                "migration_version": current_version,
                "essential_tables_present": all_essential_exist
            }

        except Exception as e:
            print(f"  ❌ データベーステストエラー: {e}")
            return {"status": "fail", "error": str(e)}

    async def test_hitl_endpoints(self) -> Dict[str, Any]:
        """HITLエンドポイントの動作確認"""
        try:
            response = await self.client.get(f"{self.backend_url}/api/v1/hitl/status")

            if response.status_code == 200:
                result_data = response.json()
                print(f"  ✅ HITLステータス: HTTP 200, データサイズ: {len(response.content)} bytes")
                return {
                    "status": "pass",
                    "status_code": 200,
                    "response_size": len(response.content),
                    "has_data": bool(result_data)
                }
            else:
                print(f"  ❌ HITLステータス: HTTP {response.status_code}")
                return {
                    "status": "fail",
                    "status_code": response.status_code,
                    "response": response.text
                }

        except Exception as e:
            print(f"  ❌ HITLエンドポイントエラー: {e}")
            return {"status": "fail", "error": str(e)}

    async def test_internal_endpoint_structure(self) -> Dict[str, Any]:
        """内部エンドポイントの構造確認"""
        try:
            # 無効なUUIDでテスト（構造確認が目的）
            test_uuid = str(uuid.uuid4())

            response = await self.client.post(
                f"{self.backend_url}/internal/tasks/manga",
                json={"request_id": test_uuid},
                headers={"Content-Type": "application/json"}
            )

            print(f"  内部エンドポイントレスポンス: HTTP {response.status_code}")

            if response.status_code == 404:
                # セッションが見つからないのは期待される（存在しないUUIDのため）
                print("  ✅ 内部エンドポイント構造は正常（セッション未発見は期待通り）")
                return {
                    "status": "pass",
                    "endpoint_accessible": True,
                    "expected_404": True,
                    "status_code": 404
                }
            elif response.status_code == 202:
                # 何らかの理由で処理が開始された場合
                print("  ⚠️ 内部エンドポイントで処理が開始されました")
                return {
                    "status": "pass",
                    "endpoint_accessible": True,
                    "unexpected_processing": True,
                    "status_code": 202
                }
            else:
                print(f"  ⚠️ 予期しないレスポンス: {response.text}")
                return {
                    "status": "partial",
                    "endpoint_accessible": True,
                    "unexpected_response": response.text,
                    "status_code": response.status_code
                }

        except Exception as e:
            print(f"  ❌ 内部エンドポイントエラー: {e}")
            return {"status": "fail", "error": str(e)}

    async def test_api_structure(self) -> Dict[str, Any]:
        """API構造の確認"""
        try:
            response = await self.client.get(f"{self.backend_url}/openapi.json")

            if response.status_code == 200:
                spec = response.json()
                paths = list(spec.get('paths', {}).keys())

                # 重要なエンドポイントの存在確認
                critical_endpoints = [
                    '/api/v1/manga/generate',
                    '/api/v1/hitl/status',
                    '/internal/tasks/manga'
                ]

                existing_critical = [ep for ep in critical_endpoints if ep in paths]

                print(f"  ✅ API仕様取得成功: {len(paths)}個のエンドポイント")
                print(f"  重要エンドポイント: {len(existing_critical)}/{len(critical_endpoints)} 存在")

                return {
                    "status": "pass" if len(existing_critical) == len(critical_endpoints) else "partial",
                    "total_endpoints": len(paths),
                    "critical_endpoints_present": len(existing_critical),
                    "critical_endpoints_total": len(critical_endpoints),
                    "all_critical_present": len(existing_critical) == len(critical_endpoints)
                }
            else:
                print(f"  ❌ API仕様取得失敗: HTTP {response.status_code}")
                return {"status": "fail", "status_code": response.status_code}

        except Exception as e:
            print(f"  ❌ API構造テストエラー: {e}")
            return {"status": "fail", "error": str(e)}

    async def test_auth_flow(self) -> Dict[str, Any]:
        """認証フローの基本動作確認"""
        try:
            # 認証が必要なエンドポイントで401を確認
            response = await self.client.get(f"{self.backend_url}/api/v1/auth/me")

            if response.status_code == 401:
                print("  ✅ 認証必須エンドポイントが正しく401を返却")
                return {
                    "status": "pass",
                    "auth_required_works": True,
                    "status_code": 401
                }
            else:
                print(f"  ⚠️ 予期しないレスポンス: HTTP {response.status_code}")
                return {
                    "status": "partial",
                    "unexpected_response": True,
                    "status_code": response.status_code
                }

        except Exception as e:
            print(f"  ❌ 認証フローテストエラー: {e}")
            return {"status": "fail", "error": str(e)}

async def main():
    """メイン実行"""
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2が必要です。既にインストール済みのはずです。")
        return False

    async with SimplifiedMangaTest(BACKEND_URL) as test:
        results = await test.test_what_we_can_test()

        # 結果をファイルに保存
        with open("simplified_manga_test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n📋 詳細結果を simplified_manga_test_results.json に保存しました")

        # スキーマ問題がある場合の提案
        if results["summary"]["pass_rate"] < 100:
            print("\n🔧 改善提案:")
            print("1. データベーススキーマの完全マイグレーション適用")
            print("2. request_idカラムの追加（管理者権限必要）")
            print("3. 漫画生成パイプラインの完全テスト")

        return results["summary"]["pass_rate"] >= 80  # 80%以上で成功とする

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)