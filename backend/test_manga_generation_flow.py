#!/usr/bin/env python3
"""
完全な漫画生成フローテスト - セッション作成から完了まで
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

class MangaGenerationFlowTest:
    def __init__(self, backend_url: str):
        self.backend_url = backend_url
        self.client = httpx.AsyncClient(timeout=120.0)
        self.test_session_id: Optional[str] = None
        self.test_request_id: Optional[str] = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def create_test_session_in_db(self) -> str:
        """データベースにテストセッションを直接作成"""
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

        print("📝 データベースにテストセッションを作成中...")

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()

            # Generate UUIDs
            session_id = str(uuid.uuid4())
            request_id = str(uuid.uuid4())
            user_id = str(uuid.uuid4())

            # First create a test user
            cursor.execute("""
                INSERT INTO user_accounts (id, firebase_uid, email, display_name, account_type, provider, is_active, created_at, last_login)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (firebase_uid) DO NOTHING
            """, (
                user_id,
                f"test-user-{int(time.time())}",
                "test@example.com",
                "テストユーザー",
                "individual",
                "google",
                True,
                datetime.utcnow(),
                datetime.utcnow()
            ))

            # Create manga session
            cursor.execute("""
                INSERT INTO manga_sessions (
                    id, user_id, request_id, title, text, status, ai_auto_settings,
                    hitl_enabled, waiting_for_feedback, total_feedback_count,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                session_id,
                user_id,
                request_id,
                "完全テスト漫画",
                "これは完全なシステムテスト用のストーリーです。主人公が冒険に出かけて、様々な困難を乗り越えながら成長していく物語です。最終的に仲間と共に大きな敵を倒し、平和を取り戻します。",
                "pending",
                True,
                False,
                False,
                0,
                datetime.utcnow(),
                datetime.utcnow()
            ))

            cursor.close()
            conn.close()

            self.test_session_id = session_id
            self.test_request_id = request_id

            print(f"✅ テストセッション作成成功:")
            print(f"  セッションID: {session_id}")
            print(f"  リクエストID: {request_id}")

            return request_id

        except Exception as e:
            print(f"❌ セッション作成エラー: {e}")
            raise

    async def trigger_manga_processing(self, request_id: str) -> bool:
        """内部エンドポイントで漫画生成を開始"""
        print("🚀 漫画生成処理を開始中...")

        try:
            payload = {"request_id": request_id}

            response = await self.client.post(
                f"{self.backend_url}/internal/tasks/manga",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            print(f"内部タスク実行結果: HTTP {response.status_code}")

            if response.status_code == 202:
                result = response.json()
                print(f"✅ 処理開始成功: {result}")
                return True
            else:
                print(f"❌ 処理開始失敗: {response.text}")
                return False

        except Exception as e:
            print(f"❌ 処理開始エラー: {e}")
            return False

    async def monitor_session_progress(self, request_id: str, max_wait_minutes: int = 10) -> Dict[str, Any]:
        """セッションの進行状況を監視"""
        print(f"👀 セッション進行状況を監視中 (最大{max_wait_minutes}分)...")

        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        check_interval = 30  # 30秒ごとにチェック

        while time.time() - start_time < max_wait_seconds:
            try:
                # データベースから直接ステータスを確認
                import psycopg2
                conn = psycopg2.connect(**DB_CONFIG)
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT id, status, current_phase, error_message, created_at, updated_at,
                           estimated_completion_time, actual_completion_time
                    FROM manga_sessions
                    WHERE request_id = %s
                """, (request_id,))

                session_data = cursor.fetchone()
                cursor.close()
                conn.close()

                if session_data:
                    session_id, status, current_phase, error_message, created_at, updated_at, est_completion, actual_completion = session_data

                    print(f"📊 ステータス: {status} | フェーズ: {current_phase}")

                    if status == "completed":
                        print("🎉 漫画生成完了！")
                        return {
                            "status": "completed",
                            "session_id": session_id,
                            "final_phase": current_phase,
                            "completion_time": actual_completion,
                            "duration": (actual_completion - created_at).total_seconds() if actual_completion else None
                        }
                    elif status == "failed":
                        print(f"💥 漫画生成失敗: {error_message}")
                        return {
                            "status": "failed",
                            "session_id": session_id,
                            "error": error_message,
                            "failed_phase": current_phase
                        }
                    elif status in ["processing", "pending"]:
                        print(f"⏳ 処理中... (フェーズ {current_phase})")
                        await asyncio.sleep(check_interval)
                        continue
                    else:
                        print(f"⚠️ 不明なステータス: {status}")
                        return {"status": "unknown", "session_status": status}
                else:
                    print("❌ セッションが見つかりません")
                    return {"status": "not_found"}

            except Exception as e:
                print(f"❌ 監視エラー: {e}")
                await asyncio.sleep(check_interval)

        print("⏰ タイムアウト: 指定時間内に完了しませんでした")
        return {"status": "timeout", "waited_minutes": max_wait_minutes}

    async def verify_generation_results(self, session_id: str) -> Dict[str, Any]:
        """生成結果を検証"""
        print("🔍 生成結果を検証中...")

        try:
            import psycopg2
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # フェーズ結果を確認
            cursor.execute("""
                SELECT phase, status, result_data, created_at
                FROM phase_results
                WHERE session_id = %s
                ORDER BY phase
            """, (session_id,))

            phase_results = cursor.fetchall()

            cursor.close()
            conn.close()

            results = {
                "total_phases": len(phase_results),
                "phases": [],
                "all_phases_completed": True
            }

            for phase, status, result_data, created_at in phase_results:
                phase_info = {
                    "phase": phase,
                    "status": status,
                    "has_data": result_data is not None,
                    "created_at": created_at
                }
                results["phases"].append(phase_info)

                if status != "completed":
                    results["all_phases_completed"] = False

                print(f"  フェーズ {phase}: {status} {'✅' if status == 'completed' else '❌'}")

            return results

        except Exception as e:
            print(f"❌ 結果検証エラー: {e}")
            return {"error": str(e)}

    async def cleanup_test_data(self, session_id: str):
        """テストデータのクリーンアップ"""
        print("🧹 テストデータをクリーンアップ中...")

        try:
            import psycopg2
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # 関連データを削除
            cursor.execute("DELETE FROM phase_results WHERE session_id = %s", (session_id,))
            cursor.execute("DELETE FROM manga_sessions WHERE id = %s", (session_id,))

            cursor.close()
            conn.close()
            print("✅ クリーンアップ完了")

        except Exception as e:
            print(f"⚠️ クリーンアップエラー: {e}")

    async def run_complete_test(self) -> Dict[str, Any]:
        """完全な漫画生成フローテストを実行"""
        print("\n🎯 === 完全漫画生成フローテスト開始 ===")
        print(f"テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        test_results = {
            "test_start": datetime.now().isoformat(),
            "backend_url": self.backend_url,
            "stages": {}
        }

        try:
            # 1. セッション作成
            print("\n📝 ステージ 1: テストセッション作成")
            request_id = await self.create_test_session_in_db()
            test_results["stages"]["session_creation"] = {"status": "success", "request_id": request_id}

            # 2. 処理開始
            print("\n🚀 ステージ 2: 漫画生成処理開始")
            processing_started = await self.trigger_manga_processing(request_id)
            test_results["stages"]["processing_start"] = {"status": "success" if processing_started else "failed"}

            if not processing_started:
                test_results["overall_result"] = "failed_at_processing_start"
                return test_results

            # 3. 進行監視
            print("\n👀 ステージ 3: 進行状況監視")
            progress_result = await self.monitor_session_progress(request_id, max_wait_minutes=10)
            test_results["stages"]["progress_monitoring"] = progress_result

            # 4. 結果検証
            if progress_result.get("status") == "completed":
                print("\n🔍 ステージ 4: 結果検証")
                verification_result = await self.verify_generation_results(progress_result["session_id"])
                test_results["stages"]["result_verification"] = verification_result

                if verification_result.get("all_phases_completed"):
                    test_results["overall_result"] = "complete_success"
                    print("🎉 漫画生成完全成功！")
                else:
                    test_results["overall_result"] = "partial_success"
                    print("⚠️ 一部のフェーズで問題がありました")
            else:
                test_results["overall_result"] = f"failed_during_processing_{progress_result.get('status')}"
                print(f"❌ 処理中にエラー: {progress_result.get('status')}")

            # 5. クリーンアップ
            if self.test_session_id:
                await self.cleanup_test_data(self.test_session_id)

        except Exception as e:
            print(f"\n💥 テスト実行中に重大エラー: {e}")
            test_results["overall_result"] = "critical_error"
            test_results["error"] = str(e)

        test_results["test_end"] = datetime.now().isoformat()

        print("\n" + "=" * 60)
        print(f"📊 最終結果: {test_results['overall_result']}")

        return test_results

async def main():
    """メイン実行"""
    try:
        # psycopg2をインストール（必要な場合）
        import psycopg2
    except ImportError:
        print("❌ psycopg2が必要です。インストールしてください: pip install psycopg2-binary")
        return False

    async with MangaGenerationFlowTest(BACKEND_URL) as test:
        results = await test.run_complete_test()

        # 結果をファイルに保存
        with open("manga_generation_flow_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n📋 詳細結果を manga_generation_flow_results.json に保存しました")

        return results["overall_result"] == "complete_success"

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)