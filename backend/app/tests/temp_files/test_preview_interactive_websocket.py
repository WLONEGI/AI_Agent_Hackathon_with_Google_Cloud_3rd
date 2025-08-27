#!/usr/bin/env python3
"""
プレビューインタラクティブ WebSocket統合テストスクリプト

このスクリプトは以下の機能をテストします：
1. プレビュー変更のリアルタイム通知
2. バージョン管理とブランチング
3. インタラクティブ要素の変更
4. プレビューキャッシュの更新
5. 複数ユーザーによる同時編集
"""

import asyncio
import websockets
import json
import logging
import time
from typing import Dict, Any, List, Optional
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
TEST_TOKEN = "test-jwt-token"
BASE_SESSION_ID = str(uuid4())

class PreviewInteractiveWebSocketTester:
    """プレビューインタラクティブ WebSocket テストクラス"""
    
    def __init__(self):
        self.connections = {}
        self.test_session_id = BASE_SESSION_ID
        self.test_results = {
            "element_change_notification": False,
            "version_branching": False,
            "cache_invalidation": False,
            "multi_user_collaboration": False,
            "preview_regeneration": False,
            "error_recovery": False
        }
        
    async def run_all_tests(self):
        """全プレビューインタラクティブテストの実行"""
        logger.info("=== プレビューインタラクティブ WebSocket統合テスト開始 ===")
        
        try:
            # 接続確立
            await self.setup_connections()
            
            # 1. 要素変更通知テスト
            await self.test_element_change_notification()
            
            # 2. バージョンブランチングテスト
            await self.test_version_branching()
            
            # 3. キャッシュ無効化テスト
            await self.test_cache_invalidation()
            
            # 4. マルチユーザー協調テスト
            await self.test_multi_user_collaboration()
            
            # 5. プレビュー再生成テスト
            await self.test_preview_regeneration()
            
            # 6. エラー回復テスト
            await self.test_error_recovery()
            
        except Exception as e:
            logger.error(f"テスト実行中にエラー: {e}")
        finally:
            await self.cleanup()
            
        # 結果表示
        self.print_test_results()
    
    async def setup_connections(self):
        """WebSocket接続の確立"""
        logger.info("--- 接続確立 ---")
        
        try:
            # メイン編集者接続
            main_editor_ws = await websockets.connect(
                f"{BASE_WS_URL}/sessions/{self.test_session_id}",
                extra_headers={"Authorization": f"Bearer {TEST_TOKEN}"}
            )
            
            # 認証
            await main_editor_ws.send(json.dumps({
                "type": "authenticate",
                "token": TEST_TOKEN
            }))
            
            auth_response = await asyncio.wait_for(main_editor_ws.recv(), timeout=5.0)
            auth_data = json.loads(auth_response)
            
            if auth_data.get("type") == "authenticated":
                self.connections["main_editor"] = main_editor_ws
                logger.info("✅ メイン編集者接続成功")
                
                # 観察者接続（別のユーザー）
                observer_session_id = str(uuid4())
                observer_ws = await websockets.connect(
                    f"{BASE_WS_URL}/sessions/{observer_session_id}",
                    extra_headers={"Authorization": f"Bearer {TEST_TOKEN}"}
                )
                
                await observer_ws.send(json.dumps({
                    "type": "authenticate",
                    "token": TEST_TOKEN
                }))
                
                obs_response = await asyncio.wait_for(observer_ws.recv(), timeout=5.0)
                obs_data = json.loads(obs_response)
                
                if obs_data.get("type") == "authenticated":
                    self.connections["observer"] = observer_ws
                    logger.info("✅ 観察者接続成功")
                else:
                    logger.error("❌ 観察者認証失敗")
            else:
                logger.error("❌ メイン編集者認証失敗")
                
        except Exception as e:
            logger.error(f"❌ 接続確立失敗: {e}")
    
    async def test_element_change_notification(self):
        """要素変更通知テスト"""
        logger.info("--- 要素変更通知テスト開始 ---")
        
        if "main_editor" not in self.connections:
            logger.error("❌ メイン編集者接続が必要")
            return
            
        try:
            main_ws = self.connections["main_editor"]
            
            # インタラクティブ要素の変更をシミュレーション
            element_change = {
                "type": "interactive_element_change",
                "session_id": self.test_session_id,
                "phase": 2,
                "change_id": str(uuid4()),
                "element_id": "character.main_protagonist.name",
                "change_type": "text_edit",
                "change_data": {
                    "previous_value": "田中太郎",
                    "new_value": "佐藤花子",
                    "metadata": {
                        "user_initiated": True,
                        "edit_position": {"start": 0, "end": 4}
                    }
                },
                "apply_immediately": True,
                "create_branch": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 変更送信
            await main_ws.send(json.dumps(element_change))
            
            # 変更確認通知を待機
            response = await asyncio.wait_for(main_ws.recv(), timeout=5.0)
            response_data = json.loads(response)
            
            if response_data.get("type") == "element_change_applied":
                logger.info("✅ 要素変更通知の受信成功")
                
                # プレビュー更新通知の確認
                preview_response = await asyncio.wait_for(main_ws.recv(), timeout=5.0)
                preview_data = json.loads(preview_response)
                
                if preview_data.get("type") == "preview_updated":
                    logger.info("✅ プレビュー更新通知の受信成功")
                    self.test_results["element_change_notification"] = True
                else:
                    logger.error("❌ プレビュー更新通知が受信されませんでした")
            else:
                logger.error("❌ 要素変更確認が受信されませんでした")
                
        except Exception as e:
            logger.error(f"❌ 要素変更通知テスト失敗: {e}")
    
    async def test_version_branching(self):
        """バージョンブランチングテスト"""
        logger.info("--- バージョンブランチングテスト開始 ---")
        
        if "main_editor" not in self.connections:
            logger.error("❌ メイン編集者接続が必要")
            return
            
        try:
            main_ws = self.connections["main_editor"]
            
            # ブランチ作成を伴う変更
            branch_change = {
                "type": "interactive_element_change",
                "session_id": self.test_session_id,
                "phase": 3,
                "change_id": str(uuid4()),
                "element_id": "plot.main_conflict",
                "change_type": "content_replacement",
                "change_data": {
                    "previous_value": "従来の対立構造",
                    "new_value": "革新的な対立構造",
                    "metadata": {
                        "major_change": True,
                        "experimental": True
                    }
                },
                "apply_immediately": False,
                "create_branch": True,
                "branch_name": "実験的プロット変更",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # ブランチ作成変更送信
            await main_ws.send(json.dumps(branch_change))
            
            # ブランチ作成確認通知を待機
            response = await asyncio.wait_for(main_ws.recv(), timeout=5.0)
            response_data = json.loads(response)
            
            if response_data.get("type") == "branch_created":
                branch_id = response_data.get("branch_id")
                logger.info(f"✅ ブランチ作成成功: {branch_id}")
                
                # ブランチ切り替え通知
                switch_message = {
                    "type": "switch_branch",
                    "session_id": self.test_session_id,
                    "branch_id": branch_id,
                    "phase": 3
                }
                
                await main_ws.send(json.dumps(switch_message))
                
                # 切り替え確認
                switch_response = await asyncio.wait_for(main_ws.recv(), timeout=5.0)
                switch_data = json.loads(switch_response)
                
                if switch_data.get("type") == "branch_switched":
                    logger.info("✅ ブランチ切り替え成功")
                    self.test_results["version_branching"] = True
                else:
                    logger.error("❌ ブランチ切り替えが失敗")
            else:
                logger.error("❌ ブランチ作成が失敗")
                
        except Exception as e:
            logger.error(f"❌ バージョンブランチングテスト失敗: {e}")
    
    async def test_cache_invalidation(self):
        """キャッシュ無効化テスト"""
        logger.info("--- キャッシュ無効化テスト開始 ---")
        
        if "main_editor" not in self.connections:
            logger.error("❌ メイン編集者接続が必要")
            return
            
        try:
            main_ws = self.connections["main_editor"]
            
            # キャッシュ影響のある変更
            cache_affecting_change = {
                "type": "interactive_element_change",
                "session_id": self.test_session_id,
                "phase": 5,
                "change_id": str(uuid4()),
                "element_id": "scene.background_setting",
                "change_type": "style_change",
                "change_data": {
                    "previous_value": {"theme": "modern", "color_palette": "bright"},
                    "new_value": {"theme": "vintage", "color_palette": "sepia"},
                    "metadata": {
                        "affects_rendering": True,
                        "cache_invalidation_required": True
                    }
                },
                "quality_level": 4,
                "apply_immediately": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 変更送信
            await main_ws.send(json.dumps(cache_affecting_change))
            
            # キャッシュ無効化通知を待機
            response = await asyncio.wait_for(main_ws.recv(), timeout=5.0)
            response_data = json.loads(response)
            
            if response_data.get("type") == "cache_invalidated":
                logger.info("✅ キャッシュ無効化通知受信成功")
                
                # 再生成開始通知
                regen_response = await asyncio.wait_for(main_ws.recv(), timeout=10.0)
                regen_data = json.loads(regen_response)
                
                if regen_data.get("type") == "preview_regeneration_started":
                    logger.info("✅ プレビュー再生成開始通知受信")
                    
                    # 再生成完了通知
                    complete_response = await asyncio.wait_for(main_ws.recv(), timeout=15.0)
                    complete_data = json.loads(complete_response)
                    
                    if complete_data.get("type") == "preview_regeneration_completed":
                        logger.info("✅ プレビュー再生成完了通知受信")
                        self.test_results["cache_invalidation"] = True
                    else:
                        logger.error("❌ プレビュー再生成完了通知が受信されませんでした")
                else:
                    logger.error("❌ プレビュー再生成開始通知が受信されませんでした")
            else:
                logger.error("❌ キャッシュ無効化通知が受信されませんでした")
                
        except Exception as e:
            logger.error(f"❌ キャッシュ無効化テスト失敗: {e}")
    
    async def test_multi_user_collaboration(self):
        """マルチユーザー協調テスト"""
        logger.info("--- マルチユーザー協調テスト開始 ---")
        
        if "main_editor" not in self.connections or "observer" not in self.connections:
            logger.error("❌ 複数の接続が必要")
            return
            
        try:
            main_ws = self.connections["main_editor"]
            observer_ws = self.connections["observer"]
            
            # メイン編集者が変更を行う
            collaborative_change = {
                "type": "interactive_element_change",
                "session_id": self.test_session_id,
                "phase": 6,
                "change_id": str(uuid4()),
                "element_id": "dialogue.scene_12.line_5",
                "change_type": "text_edit",
                "change_data": {
                    "previous_value": "こんにちは",
                    "new_value": "おはよう",
                    "metadata": {
                        "collaborative_edit": True,
                        "editor_id": "main_editor"
                    }
                },
                "apply_immediately": True,
                "notify_collaborators": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # メイン編集者が変更送信
            await main_ws.send(json.dumps(collaborative_change))
            
            # 両方の接続で通知を確認
            main_response_task = asyncio.create_task(
                asyncio.wait_for(main_ws.recv(), timeout=5.0)
            )
            observer_response_task = asyncio.create_task(
                asyncio.wait_for(observer_ws.recv(), timeout=5.0)
            )
            
            # 両方のレスポンスを待機
            main_response, observer_response = await asyncio.gather(
                main_response_task, observer_response_task,
                return_exceptions=True
            )
            
            main_success = False
            observer_success = False
            
            # メイン編集者のレスポンス確認
            if not isinstance(main_response, Exception):
                main_data = json.loads(main_response)
                if main_data.get("type") == "element_change_applied":
                    main_success = True
                    logger.info("✅ メイン編集者の変更確認成功")
            
            # 観察者のレスポンス確認
            if not isinstance(observer_response, Exception):
                observer_data = json.loads(observer_response)
                if observer_data.get("type") == "collaborative_change_notification":
                    observer_success = True
                    logger.info("✅ 観察者の協調変更通知受信成功")
            
            if main_success and observer_success:
                self.test_results["multi_user_collaboration"] = True
                logger.info("✅ マルチユーザー協調テスト成功")
            else:
                logger.error("❌ マルチユーザー協調テストが部分的に失敗")
                
        except Exception as e:
            logger.error(f"❌ マルチユーザー協調テスト失敗: {e}")
    
    async def test_preview_regeneration(self):
        """プレビュー再生成テスト"""
        logger.info("--- プレビュー再生成テスト開始 ---")
        
        if "main_editor" not in self.connections:
            logger.error("❌ メイン編集者接続が必要")
            return
            
        try:
            main_ws = self.connections["main_editor"]
            
            # 再生成を要求する変更
            regeneration_change = {
                "type": "request_preview_regeneration",
                "session_id": self.test_session_id,
                "phase": 4,
                "quality_level": 5,  # 高品質で再生成
                "reason": "manual_refresh",
                "regeneration_scope": ["layout", "styling", "content"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 再生成要求送信
            await main_ws.send(json.dumps(regeneration_change))
            
            # 再生成開始通知
            start_response = await asyncio.wait_for(main_ws.recv(), timeout=5.0)
            start_data = json.loads(start_response)
            
            if start_data.get("type") == "preview_regeneration_started":
                estimated_time = start_data.get("estimated_time_seconds", 10)
                logger.info(f"✅ プレビュー再生成開始 (推定時間: {estimated_time}秒)")
                
                # 進捗更新の確認
                progress_response = await asyncio.wait_for(main_ws.recv(), timeout=10.0)
                progress_data = json.loads(progress_response)
                
                if progress_data.get("type") == "regeneration_progress":
                    progress = progress_data.get("progress", 0)
                    logger.info(f"✅ 再生成進捗更新: {progress}%")
                    
                    # 完了通知
                    completion_response = await asyncio.wait_for(main_ws.recv(), timeout=15.0)
                    completion_data = json.loads(completion_response)
                    
                    if completion_data.get("type") == "preview_regeneration_completed":
                        new_preview_url = completion_data.get("preview_url")
                        generation_time = completion_data.get("generation_time_ms")
                        logger.info(f"✅ プレビュー再生成完了: {generation_time}ms")
                        logger.info(f"   新しいプレビューURL: {new_preview_url}")
                        self.test_results["preview_regeneration"] = True
                    else:
                        logger.error("❌ プレビュー再生成完了通知が受信されませんでした")
                else:
                    logger.error("❌ 再生成進捗更新が受信されませんでした")
            else:
                logger.error("❌ プレビュー再生成開始通知が受信されませんでした")
                
        except Exception as e:
            logger.error(f"❌ プレビュー再生成テスト失敗: {e}")
    
    async def test_error_recovery(self):
        """エラー回復テスト"""
        logger.info("--- エラー回復テスト開始 ---")
        
        if "main_editor" not in self.connections:
            logger.error("❌ メイン編集者接続が必要")
            return
            
        try:
            main_ws = self.connections["main_editor"]
            
            # 無効な変更データでエラーを発生させる
            invalid_change = {
                "type": "interactive_element_change",
                "session_id": self.test_session_id,
                "phase": 99,  # 無効なフェーズ
                "change_id": str(uuid4()),
                "element_id": "invalid.element.id",
                "change_type": "invalid_change_type",
                "change_data": {
                    "invalid_data": "this should cause an error"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 無効な変更送信
            await main_ws.send(json.dumps(invalid_change))
            
            # エラーレスポンスを待機
            error_response = await asyncio.wait_for(main_ws.recv(), timeout=5.0)
            error_data = json.loads(error_response)
            
            if error_data.get("type") == "error":
                error_code = error_data.get("code")
                logger.info(f"✅ エラーレスポンス受信: {error_code}")
                
                # エラー後の回復確認
                recovery_message = {
                    "type": "ping",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await main_ws.send(json.dumps(recovery_message))
                
                # 正常なレスポンス確認
                recovery_response = await asyncio.wait_for(main_ws.recv(), timeout=5.0)
                recovery_data = json.loads(recovery_response)
                
                if recovery_data.get("type") == "pong":
                    logger.info("✅ エラー後の接続回復確認成功")
                    self.test_results["error_recovery"] = True
                else:
                    logger.error("❌ エラー後の接続が回復しませんでした")
            else:
                logger.error("❌ エラーレスポンスが受信されませんでした")
                
        except Exception as e:
            logger.error(f"❌ エラー回復テスト失敗: {e}")
    
    async def cleanup(self):
        """テスト後のクリーンアップ"""
        logger.info("--- プレビューインタラクティブテスト クリーンアップ ---")
        
        for name, ws in self.connections.items():
            try:
                await ws.close()
                logger.info(f"✅ {name}接続をクローズ")
            except Exception as e:
                logger.warning(f"⚠️ {name}接続のクローズ中にエラー: {e}")
        
        self.connections.clear()
    
    def print_test_results(self):
        """テスト結果の表示"""
        logger.info("=== プレビューインタラクティブWebSocketテスト結果 ===")
        
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        
        test_descriptions = {
            "element_change_notification": "要素変更通知",
            "version_branching": "バージョンブランチング",
            "cache_invalidation": "キャッシュ無効化",
            "multi_user_collaboration": "マルチユーザー協調",
            "preview_regeneration": "プレビュー再生成",
            "error_recovery": "エラー回復"
        }
        
        for test_name, result in self.test_results.items():
            status = "✅ 成功" if result else "❌ 失敗"
            description = test_descriptions.get(test_name, test_name)
            logger.info(f"{description}: {status}")
        
        logger.info(f"")
        logger.info(f"総テスト数: {total_tests}")
        logger.info(f"成功: {passed_tests}")
        logger.info(f"失敗: {total_tests - passed_tests}")
        logger.info(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            logger.info("🎉 全プレビューインタラクティブテストが成功しました！")
        else:
            logger.warning("⚠️ 一部のプレビューインタラクティブテストが失敗しました。")


async def main():
    """メイン実行関数"""
    tester = PreviewInteractiveWebSocketTester()
    await tester.run_all_tests()
    
    logger.info("=== プレビューインタラクティブWebSocketテスト完了 ===")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("テストが中断されました")
    except Exception as e:
        logger.error(f"テスト実行エラー: {e}")