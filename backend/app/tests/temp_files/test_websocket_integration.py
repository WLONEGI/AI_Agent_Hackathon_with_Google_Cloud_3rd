#!/usr/bin/env python3
"""
WebSocket統合テストスクリプト - リアルタイム品質更新の動作確認

このスクリプトは以下の機能をテストします：
1. WebSocket接続の確立
2. 品質ゲート更新のリアルタイム配信
3. プレビュー変更の即座反映
4. エラーハンドリング
5. 接続の安定性
"""

import asyncio
import websockets
import json
import logging
import time
from typing import Dict, Any, List
from datetime import datetime
from uuid import uuid4

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# テスト設定
BASE_WS_URL = "ws://localhost:8000/ws/v1"
TEST_TOKEN = "test-jwt-token"  # 実際のテストでは有効なJWTトークンを使用
SESSION_ID = str(uuid4())
USER_ID = str(uuid4())

class WebSocketTester:
    """WebSocket統合テストクラス"""
    
    def __init__(self):
        self.connections = {}
        self.received_messages = []
        self.test_results = {
            "connection_test": False,
            "quality_update_test": False,
            "preview_update_test": False,
            "error_handling_test": False,
            "performance_test": False
        }
        
    async def run_all_tests(self):
        """全テストの実行"""
        logger.info("=== WebSocket統合テスト開始 ===")
        
        try:
            # 1. 接続テスト
            await self.test_connection()
            
            # 2. 品質更新テスト
            await self.test_quality_updates()
            
            # 3. プレビュー更新テスト  
            await self.test_preview_updates()
            
            # 4. エラーハンドリングテスト
            await self.test_error_handling()
            
            # 5. パフォーマンステスト
            await self.test_performance()
            
        except Exception as e:
            logger.error(f"テスト実行中にエラー: {e}")
        finally:
            await self.cleanup()
            
        # 結果表示
        self.print_test_results()
    
    async def test_connection(self):
        """WebSocket接続テスト"""
        logger.info("--- 接続テスト開始 ---")
        
        try:
            # メインセッション接続
            main_ws = await websockets.connect(
                f"{BASE_WS_URL}/sessions/{SESSION_ID}",
                extra_headers={"Authorization": f"Bearer {TEST_TOKEN}"}
            )
            self.connections["main"] = main_ws
            
            # 認証メッセージ送信
            auth_message = {
                "type": "authenticate",
                "token": TEST_TOKEN
            }
            await main_ws.send(json.dumps(auth_message))
            
            # レスポンス待機
            response = await asyncio.wait_for(main_ws.recv(), timeout=5.0)
            response_data = json.loads(response)
            
            if response_data.get("type") == "authenticated":
                logger.info("✅ メインセッション接続成功")
                self.test_results["connection_test"] = True
            else:
                logger.error("❌ 認証失敗")
                
        except Exception as e:
            logger.error(f"❌ 接続テスト失敗: {e}")
    
    async def test_quality_updates(self):
        """品質ゲート更新のリアルタイムテスト"""
        logger.info("--- 品質更新テスト開始 ---")
        
        if "main" not in self.connections:
            logger.error("❌ メインセッション接続が必要")
            return
            
        try:
            main_ws = self.connections["main"]
            
            # 品質ゲート失敗シミュレーション
            quality_alert_message = {
                "type": "quality_alert",
                "level": "critical",
                "phase": 4,
                "quality_score": 0.45,
                "message": "フェーズ4の品質が閾値を下回りました",
                "threshold": 0.7,
                "retry_count": 1,
                "max_retries": 3,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # メッセージ送信
            await main_ws.send(json.dumps(quality_alert_message))
            
            # 応答待機
            response = await asyncio.wait_for(main_ws.recv(), timeout=5.0)
            response_data = json.loads(response)
            
            if response_data.get("type") == "quality_alert":
                logger.info("✅ 品質アラートの受信成功")
                
                # 品質ゲート再試行シミュレーション
                retry_message = {
                    "type": "quality_gate_retry",
                    "phase": 4,
                    "retry_attempt": 2,
                    "estimated_time": 15
                }
                
                await main_ws.send(json.dumps(retry_message))
                
                # 改善後の品質スコアシミュレーション
                await asyncio.sleep(1)
                quality_improved_message = {
                    "type": "quality_alert",
                    "level": "info",
                    "phase": 4,
                    "quality_score": 0.78,
                    "message": "フェーズ4の品質が改善されました",
                    "status": "passed"
                }
                
                await main_ws.send(json.dumps(quality_improved_message))
                
                logger.info("✅ 品質改善の通知送信成功")
                self.test_results["quality_update_test"] = True
                
        except Exception as e:
            logger.error(f"❌ 品質更新テスト失敗: {e}")
    
    async def test_preview_updates(self):
        """プレビュー更新のリアルタイムテスト"""
        logger.info("--- プレビュー更新テスト開始 ---")
        
        if "main" not in self.connections:
            logger.error("❌ メインセッション接続が必要")
            return
            
        try:
            main_ws = self.connections["main"]
            
            # プレビュー変更通知
            preview_change_message = {
                "type": "preview_change",
                "phase": 3,
                "version_id": str(uuid4()),
                "change_type": "text_edit",
                "element_id": "plot.main_conflict",
                "change_data": {
                    "previous_value": "古い設定",
                    "new_value": "新しい設定",
                    "change_description": "主人公の対立構造を変更"
                },
                "preview_url": f"/preview/{SESSION_ID}/phase/3/v2",
                "quality_impact": 0.05,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await main_ws.send(json.dumps(preview_change_message))
            
            # プレビュー準備完了通知
            await asyncio.sleep(0.5)
            preview_ready_message = {
                "type": "preview_ready",
                "phase": 3,
                "preview_url": f"/preview/{SESSION_ID}/phase/3/v2",
                "thumbnail_url": f"/preview/{SESSION_ID}/phase/3/v2/thumb",
                "generation_time_ms": 1250,
                "cache_status": "fresh"
            }
            
            await main_ws.send(json.dumps(preview_ready_message))
            
            # レスポンス確認
            response = await asyncio.wait_for(main_ws.recv(), timeout=5.0)
            response_data = json.loads(response)
            
            if "preview" in response_data.get("type", ""):
                logger.info("✅ プレビュー更新の受信成功")
                self.test_results["preview_update_test"] = True
                
        except Exception as e:
            logger.error(f"❌ プレビュー更新テスト失敗: {e}")
    
    async def test_error_handling(self):
        """エラーハンドリングテスト"""
        logger.info("--- エラーハンドリングテスト開始 ---")
        
        if "main" not in self.connections:
            logger.error("❌ メインセッション接続が必要")
            return
            
        try:
            main_ws = self.connections["main"]
            
            # 無効なメッセージ送信
            invalid_message = {
                "type": "invalid_message_type",
                "data": "invalid_data"
            }
            
            await main_ws.send(json.dumps(invalid_message))
            
            # エラーレスポンス待機
            response = await asyncio.wait_for(main_ws.recv(), timeout=5.0)
            response_data = json.loads(response)
            
            if response_data.get("type") == "error":
                logger.info("✅ エラーハンドリング成功")
                self.test_results["error_handling_test"] = True
            else:
                logger.error("❌ エラーレスポンスが期待されましたが、受信できませんでした")
                
        except Exception as e:
            logger.error(f"❌ エラーハンドリングテスト失敗: {e}")
    
    async def test_performance(self):
        """パフォーマンステスト"""
        logger.info("--- パフォーマンステスト開始 ---")
        
        if "main" not in self.connections:
            logger.error("❌ メインセッション接続が必要") 
            return
            
        try:
            main_ws = self.connections["main"]
            
            # 複数メッセージの連続送信
            message_count = 10
            start_time = time.time()
            
            for i in range(message_count):
                ping_message = {
                    "type": "ping",
                    "sequence": i,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await main_ws.send(json.dumps(ping_message))
                
                # レスポンス待機
                response = await asyncio.wait_for(main_ws.recv(), timeout=2.0)
                response_data = json.loads(response)
                
                if response_data.get("type") != "pong":
                    logger.warning(f"Ping {i}: 期待外のレスポンス")
            
            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / message_count
            
            logger.info(f"✅ パフォーマンステスト完了:")
            logger.info(f"   総時間: {total_time:.2f}秒")
            logger.info(f"   平均応答時間: {avg_time*1000:.2f}ms")
            
            if avg_time < 0.1:  # 100ms未満
                self.test_results["performance_test"] = True
                logger.info("✅ パフォーマンス基準をクリア")
            else:
                logger.warning("⚠️ パフォーマンス基準を満たしていません")
                
        except Exception as e:
            logger.error(f"❌ パフォーマンステスト失敗: {e}")
    
    async def cleanup(self):
        """テスト後のクリーンアップ"""
        logger.info("--- クリーンアップ開始 ---")
        
        for name, ws in self.connections.items():
            try:
                await ws.close()
                logger.info(f"✅ {name}接続をクローズ")
            except Exception as e:
                logger.warning(f"⚠️ {name}接続のクローズ中にエラー: {e}")
        
        self.connections.clear()
    
    def print_test_results(self):
        """テスト結果の表示"""
        logger.info("=== テスト結果 ===")
        
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        
        for test_name, result in self.test_results.items():
            status = "✅ 成功" if result else "❌ 失敗"
            logger.info(f"{test_name}: {status}")
        
        logger.info(f"")
        logger.info(f"総テスト数: {total_tests}")
        logger.info(f"成功: {passed_tests}")
        logger.info(f"失敗: {total_tests - passed_tests}")
        logger.info(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            logger.info("🎉 全テストが成功しました！")
        else:
            logger.warning("⚠️ 一部のテストが失敗しました。")


class LoadTester:
    """負荷テスト用クラス"""
    
    def __init__(self, concurrent_users=10):
        self.concurrent_users = concurrent_users
        self.results = []
        
    async def run_load_test(self):
        """負荷テストの実行"""
        logger.info(f"=== 負荷テスト開始 ({self.concurrent_users}同時ユーザー) ===")
        
        # 並行ユーザーセッション作成
        tasks = []
        for i in range(self.concurrent_users):
            user_session_id = str(uuid4())
            task = asyncio.create_task(
                self.simulate_user_session(i, user_session_id)
            )
            tasks.append(task)
        
        # 全ユーザーセッション実行
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # 結果分析
        successful_sessions = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
        failed_sessions = self.concurrent_users - successful_sessions
        total_time = end_time - start_time
        
        logger.info(f"=== 負荷テスト結果 ===")
        logger.info(f"同時ユーザー数: {self.concurrent_users}")
        logger.info(f"成功セッション: {successful_sessions}")
        logger.info(f"失敗セッション: {failed_sessions}")
        logger.info(f"総実行時間: {total_time:.2f}秒")
        logger.info(f"成功率: {(successful_sessions/self.concurrent_users)*100:.1f}%")
        
        return {
            "concurrent_users": self.concurrent_users,
            "successful_sessions": successful_sessions,
            "failed_sessions": failed_sessions,
            "total_time": total_time,
            "success_rate": (successful_sessions/self.concurrent_users)*100
        }
    
    async def simulate_user_session(self, user_index: int, session_id: str):
        """個別ユーザーセッションのシミュレーション"""
        try:
            # WebSocket接続
            ws = await websockets.connect(
                f"{BASE_WS_URL}/sessions/{session_id}",
                timeout=10
            )
            
            # 認証
            auth_message = {
                "type": "authenticate", 
                "token": TEST_TOKEN
            }
            await ws.send(json.dumps(auth_message))
            
            # 認証レスポンス待機
            response = await asyncio.wait_for(ws.recv(), timeout=5.0)
            auth_response = json.loads(response)
            
            if auth_response.get("type") != "authenticated":
                return {"success": False, "error": "authentication_failed"}
            
            # シミュレーションメッセージ送信
            for phase in range(1, 8):
                progress_message = {
                    "type": "progress_update",
                    "phase": phase,
                    "progress": phase * 14.3  # 7フェーズで約100%
                }
                await ws.send(json.dumps(progress_message))
                await asyncio.sleep(0.1)  # 短い待機
                
                # 品質アラート（ランダム）
                if phase == 4 and user_index % 3 == 0:  # 3分の1のユーザーで品質アラート
                    quality_message = {
                        "type": "quality_alert",
                        "level": "warning",
                        "phase": phase,
                        "quality_score": 0.65,
                        "threshold": 0.7
                    }
                    await ws.send(json.dumps(quality_message))
            
            # クリーンアップ
            await ws.close()
            
            return {
                "success": True,
                "user_index": user_index,
                "session_id": session_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "user_index": user_index,
                "error": str(e)
            }


async def main():
    """メイン実行関数"""
    
    # 基本統合テスト
    tester = WebSocketTester()
    await tester.run_all_tests()
    
    # 負荷テスト（オプション）
    print("\n" + "="*50)
    run_load_test = input("負荷テストを実行しますか？ (y/N): ").lower() == 'y'
    
    if run_load_test:
        load_tester = LoadTester(concurrent_users=10)
        await load_tester.run_load_test()
    
    logger.info("=== 全テスト完了 ===")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("テストが中断されました")
    except Exception as e:
        logger.error(f"テスト実行エラー: {e}")