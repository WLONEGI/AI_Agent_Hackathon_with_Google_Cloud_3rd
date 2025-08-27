#!/usr/bin/env python3
"""
AI漫画生成サービス 負荷テストスクリプト

このスクリプトは以下のパフォーマンス検証を行います：
1. 同時10ユーザーでの並行処理テスト
2. APIエンドポイントのレスポンス時間測定
3. WebSocket接続の安定性テスト
4. データベース負荷テスト
5. 品質ゲートシステムの負荷耐性
6. プレビューインタラクティブ機能の負荷耐性
"""

import asyncio
import aiohttp
import websockets
import json
import time
import statistics
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from uuid import uuid4
from dataclasses import dataclass
import concurrent.futures
import psutil
import gc

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# テスト設定
BASE_API_URL = "http://localhost:8000/api/v1"
BASE_WS_URL = "ws://localhost:8000/ws/v1"
TEST_TOKEN = "test-jwt-token"
CONCURRENT_USERS = 10
TEST_DURATION_SECONDS = 300  # 5分間
RAMP_UP_TIME_SECONDS = 30   # 30秒でユーザーを段階的に増加

@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""
    response_times: List[float]
    error_count: int
    success_count: int
    throughput: float
    memory_usage: float
    cpu_usage: float
    
    @property
    def avg_response_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0.0
    
    @property
    def p95_response_time(self) -> float:
        return statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) >= 20 else 0.0
    
    @property
    def p99_response_time(self) -> float:
        return statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) >= 100 else 0.0
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.error_count
        return (self.success_count / total * 100) if total > 0 else 0.0


class LoadTester:
    """負荷テスト実行クラス"""
    
    def __init__(self):
        self.results = {}
        self.active_users = 0
        self.start_time = None
        self.system_metrics = []
        
    async def run_comprehensive_load_test(self):
        """包括的な負荷テストの実行"""
        logger.info("=== AI漫画生成サービス 負荷テスト開始 ===")
        logger.info(f"同時ユーザー数: {CONCURRENT_USERS}")
        logger.info(f"テスト時間: {TEST_DURATION_SECONDS}秒")
        logger.info(f"ランプアップ時間: {RAMP_UP_TIME_SECONDS}秒")
        
        self.start_time = time.time()
        
        # システムメトリクス監視タスク
        monitor_task = asyncio.create_task(self.monitor_system_resources())
        
        try:
            # 並行テスト実行
            test_tasks = [
                self.test_api_endpoints_load(),
                self.test_websocket_connections_load(),
                self.test_quality_gates_load(),
                self.test_preview_interactive_load(),
                self.test_database_load()
            ]
            
            # すべてのテストを並行実行
            results = await asyncio.gather(*test_tasks, return_exceptions=True)
            
            # 結果の処理
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"テスト{i}でエラー: {result}")
                else:
                    self.results[f"test_{i}"] = result
                    
        except Exception as e:
            logger.error(f"負荷テスト実行中にエラー: {e}")
        finally:
            # システムメトリクス監視停止
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
            
        # 結果分析と表示
        await self.analyze_and_report_results()
    
    async def test_api_endpoints_load(self) -> Dict[str, Any]:
        """API エンドポイント負荷テスト"""
        logger.info("--- API エンドポイント負荷テスト開始 ---")
        
        endpoints = [
            {"method": "GET", "path": "/info", "name": "api_info"},
            {"method": "GET", "path": "/health", "name": "health_check"},
            {"method": "POST", "path": "/manga/generate", "name": "manga_generate", 
             "data": {"input_text": "テスト用マンガ生成", "hitl_enabled": False}},
            {"method": "GET", "path": "/quality/health", "name": "quality_health"}
        ]
        
        metrics = {endpoint["name"]: PerformanceMetrics([], 0, 0, 0.0, 0.0, 0.0) 
                  for endpoint in endpoints}
        
        # ユーザーシミュレーションタスク
        async def simulate_user(user_id: int):
            async with aiohttp.ClientSession() as session:
                user_start_time = time.time()
                requests_made = 0
                
                while time.time() - user_start_time < TEST_DURATION_SECONDS:
                    for endpoint in endpoints:
                        try:
                            request_start = time.time()
                            
                            # リクエスト実行
                            if endpoint["method"] == "GET":
                                async with session.get(
                                    f"{BASE_API_URL}{endpoint['path']}",
                                    headers={"Authorization": f"Bearer {TEST_TOKEN}"},
                                    timeout=aiohttp.ClientTimeout(total=30)
                                ) as response:
                                    await response.text()
                                    status_ok = response.status < 400
                            else:  # POST
                                async with session.post(
                                    f"{BASE_API_URL}{endpoint['path']}",
                                    json=endpoint.get("data", {}),
                                    headers={"Authorization": f"Bearer {TEST_TOKEN}"},
                                    timeout=aiohttp.ClientTimeout(total=30)
                                ) as response:
                                    await response.text()
                                    status_ok = response.status < 400
                            
                            request_time = time.time() - request_start
                            
                            # メトリクス更新
                            endpoint_metrics = metrics[endpoint["name"]]
                            endpoint_metrics.response_times.append(request_time)
                            
                            if status_ok:
                                endpoint_metrics.success_count += 1
                            else:
                                endpoint_metrics.error_count += 1
                                
                            requests_made += 1
                            
                        except Exception as e:
                            metrics[endpoint["name"]].error_count += 1
                            logger.debug(f"User {user_id} request error: {e}")
                        
                        # 短い待機
                        await asyncio.sleep(0.1)
                    
                    # リクエスト間隔
                    await asyncio.sleep(1.0)
                
                logger.debug(f"User {user_id} completed {requests_made} requests")
        
        # 段階的ユーザー起動
        user_tasks = []
        for i in range(CONCURRENT_USERS):
            # ランプアップ遅延
            await asyncio.sleep(RAMP_UP_TIME_SECONDS / CONCURRENT_USERS)
            task = asyncio.create_task(simulate_user(i))
            user_tasks.append(task)
            self.active_users += 1
            logger.info(f"API負荷テスト: ユーザー{i+1}開始 (総{self.active_users}ユーザー)")
        
        # すべてのユーザータスク完了待機
        await asyncio.gather(*user_tasks, return_exceptions=True)
        
        # スループット計算
        total_time = TEST_DURATION_SECONDS
        for endpoint_name, metric in metrics.items():
            total_requests = metric.success_count + metric.error_count
            metric.throughput = total_requests / total_time if total_time > 0 else 0
        
        logger.info("✅ API エンドポイント負荷テスト完了")
        return {"api_endpoints": metrics}
    
    async def test_websocket_connections_load(self) -> Dict[str, Any]:
        """WebSocket接続負荷テスト"""
        logger.info("--- WebSocket接続負荷テスト開始 ---")
        
        connection_metrics = PerformanceMetrics([], 0, 0, 0.0, 0.0, 0.0)
        message_metrics = PerformanceMetrics([], 0, 0, 0.0, 0.0, 0.0)
        
        # WebSocketユーザーシミュレーション
        async def simulate_websocket_user(user_id: int):
            session_id = str(uuid4())
            connection_start = time.time()
            messages_sent = 0
            
            try:
                # WebSocket接続
                async with websockets.connect(
                    f"{BASE_WS_URL}/sessions/{session_id}",
                    extra_headers={"Authorization": f"Bearer {TEST_TOKEN}"},
                    timeout=10
                ) as websocket:
                    
                    connection_time = time.time() - connection_start
                    connection_metrics.response_times.append(connection_time)
                    connection_metrics.success_count += 1
                    
                    # 認証
                    await websocket.send(json.dumps({
                        "type": "authenticate",
                        "token": TEST_TOKEN
                    }))
                    
                    auth_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    auth_data = json.loads(auth_response)
                    
                    if auth_data.get("type") != "authenticated":
                        connection_metrics.error_count += 1
                        return
                    
                    # メッセージ送受信テスト
                    user_start_time = time.time()
                    while time.time() - user_start_time < TEST_DURATION_SECONDS:
                        try:
                            message_start = time.time()
                            
                            # Pingメッセージ送信
                            ping_message = {
                                "type": "ping",
                                "user_id": user_id,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            
                            await websocket.send(json.dumps(ping_message))
                            
                            # Pongレスポンス待機
                            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            response_data = json.loads(response)
                            
                            message_time = time.time() - message_start
                            message_metrics.response_times.append(message_time)
                            
                            if response_data.get("type") == "pong":
                                message_metrics.success_count += 1
                            else:
                                message_metrics.error_count += 1
                            
                            messages_sent += 1
                            
                        except Exception as e:
                            message_metrics.error_count += 1
                            logger.debug(f"WebSocket user {user_id} message error: {e}")
                        
                        # メッセージ間隔
                        await asyncio.sleep(2.0)
                    
            except Exception as e:
                connection_metrics.error_count += 1
                logger.debug(f"WebSocket user {user_id} connection error: {e}")
            
            logger.debug(f"WebSocket user {user_id} sent {messages_sent} messages")
        
        # 段階的WebSocketユーザー起動
        ws_tasks = []
        for i in range(CONCURRENT_USERS):
            await asyncio.sleep(RAMP_UP_TIME_SECONDS / CONCURRENT_USERS)
            task = asyncio.create_task(simulate_websocket_user(i))
            ws_tasks.append(task)
            logger.info(f"WebSocket負荷テスト: ユーザー{i+1}接続開始")
        
        # すべてのWebSocketタスク完了待機
        await asyncio.gather(*ws_tasks, return_exceptions=True)
        
        logger.info("✅ WebSocket接続負荷テスト完了")
        return {
            "websocket_connections": connection_metrics,
            "websocket_messages": message_metrics
        }
    
    async def test_quality_gates_load(self) -> Dict[str, Any]:
        """品質ゲート負荷テスト"""
        logger.info("--- 品質ゲート負荷テスト開始 ---")
        
        quality_metrics = PerformanceMetrics([], 0, 0, 0.0, 0.0, 0.0)
        
        # 品質ゲートAPIテスト
        async def test_quality_endpoints(session: aiohttp.ClientSession):
            test_session_id = str(uuid4())
            
            endpoints = [
                f"/manga/{test_session_id}/quality-gate",
                "/quality/metrics", 
                "/quality/health"
            ]
            
            for endpoint in endpoints:
                try:
                    request_start = time.time()
                    
                    async with session.get(
                        f"{BASE_API_URL}{endpoint}",
                        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as response:
                        await response.text()
                        
                        request_time = time.time() - request_start
                        quality_metrics.response_times.append(request_time)
                        
                        if response.status < 400:
                            quality_metrics.success_count += 1
                        else:
                            quality_metrics.error_count += 1
                            
                except Exception as e:
                    quality_metrics.error_count += 1
                    logger.debug(f"Quality gate test error: {e}")
        
        # 並行品質ゲートテスト
        async with aiohttp.ClientSession() as session:
            quality_tasks = []
            for _ in range(CONCURRENT_USERS * 3):  # より多くのリクエスト
                task = asyncio.create_task(test_quality_endpoints(session))
                quality_tasks.append(task)
            
            await asyncio.gather(*quality_tasks, return_exceptions=True)
        
        logger.info("✅ 品質ゲート負荷テスト完了")
        return {"quality_gates": quality_metrics}
    
    async def test_preview_interactive_load(self) -> Dict[str, Any]:
        """プレビューインタラクティブ負荷テスト"""
        logger.info("--- プレビューインタラクティブ負荷テスト開始 ---")
        
        preview_metrics = PerformanceMetrics([], 0, 0, 0.0, 0.0, 0.0)
        
        # プレビューAPIテスト
        async def test_preview_endpoints(session: aiohttp.ClientSession):
            test_session_id = str(uuid4())
            
            endpoints = [
                f"/manga/{test_session_id}/preview/1",
                f"/manga/{test_session_id}/preview/2",
                f"/manga/{test_session_id}/preview/3"
            ]
            
            for endpoint in endpoints:
                try:
                    request_start = time.time()
                    
                    async with session.get(
                        f"{BASE_API_URL}{endpoint}",
                        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
                        timeout=aiohttp.ClientTimeout(total=20)
                    ) as response:
                        await response.text()
                        
                        request_time = time.time() - request_start
                        preview_metrics.response_times.append(request_time)
                        
                        if response.status < 400:
                            preview_metrics.success_count += 1
                        else:
                            preview_metrics.error_count += 1
                            
                except Exception as e:
                    preview_metrics.error_count += 1
                    logger.debug(f"Preview interactive test error: {e}")
        
        # 並行プレビューテスト
        async with aiohttp.ClientSession() as session:
            preview_tasks = []
            for _ in range(CONCURRENT_USERS * 2):
                task = asyncio.create_task(test_preview_endpoints(session))
                preview_tasks.append(task)
            
            await asyncio.gather(*preview_tasks, return_exceptions=True)
        
        logger.info("✅ プレビューインタラクティブ負荷テスト完了")
        return {"preview_interactive": preview_metrics}
    
    async def test_database_load(self) -> Dict[str, Any]:
        """データベース負荷テスト（間接的）"""
        logger.info("--- データベース負荷テスト開始 ---")
        
        db_metrics = PerformanceMetrics([], 0, 0, 0.0, 0.0, 0.0)
        
        # データベースを多用するAPIエンドポイントのテスト
        async def database_intensive_requests(session: aiohttp.ClientSession):
            for _ in range(5):  # 各ユーザーが5回実行
                try:
                    request_start = time.time()
                    
                    # セッション作成（データベース書き込み）
                    create_data = {
                        "input_text": f"負荷テスト用マンガ生成 {uuid4()}",
                        "hitl_enabled": False,
                        "quality_level": "high"
                    }
                    
                    async with session.post(
                        f"{BASE_API_URL}/manga/generate",
                        json=create_data,
                        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        await response.text()
                        
                        request_time = time.time() - request_start
                        db_metrics.response_times.append(request_time)
                        
                        if response.status < 400:
                            db_metrics.success_count += 1
                        else:
                            db_metrics.error_count += 1
                            
                except Exception as e:
                    db_metrics.error_count += 1
                    logger.debug(f"Database load test error: {e}")
                
                await asyncio.sleep(1.0)  # リクエスト間隔
        
        # 並行データベーステスト
        async with aiohttp.ClientSession() as session:
            db_tasks = []
            for i in range(CONCURRENT_USERS):
                task = asyncio.create_task(database_intensive_requests(session))
                db_tasks.append(task)
            
            await asyncio.gather(*db_tasks, return_exceptions=True)
        
        logger.info("✅ データベース負荷テスト完了")
        return {"database_load": db_metrics}
    
    async def monitor_system_resources(self):
        """システムリソース監視"""
        while True:
            try:
                # CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # メモリ使用率
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                
                # ディスクI/O
                disk_io = psutil.disk_io_counters()
                
                metric = {
                    "timestamp": datetime.utcnow(),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_read_mb_s": (disk_io.read_bytes if disk_io else 0) / (1024**2),
                    "disk_write_mb_s": (disk_io.write_bytes if disk_io else 0) / (1024**2)
                }
                
                self.system_metrics.append(metric)
                
                await asyncio.sleep(5)  # 5秒間隔で監視
                
            except Exception as e:
                logger.debug(f"System monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def analyze_and_report_results(self):
        """結果分析とレポート生成"""
        logger.info("=== 負荷テスト結果分析 ===")
        
        total_duration = time.time() - self.start_time
        
        # 総合統計
        logger.info(f"テスト実行時間: {total_duration:.2f}秒")
        logger.info(f"同時ユーザー数: {CONCURRENT_USERS}")
        
        # 各テストの結果表示
        for test_name, test_result in self.results.items():
            logger.info(f"\n--- {test_name} 結果 ---")
            
            if isinstance(test_result, dict):
                for category_name, metrics in test_result.items():
                    if isinstance(metrics, PerformanceMetrics):
                        logger.info(f"\n{category_name}:")
                        logger.info(f"  成功率: {metrics.success_rate:.1f}%")
                        logger.info(f"  平均応答時間: {metrics.avg_response_time*1000:.2f}ms")
                        if metrics.response_times:
                            logger.info(f"  P95応答時間: {metrics.p95_response_time*1000:.2f}ms")
                            logger.info(f"  P99応答時間: {metrics.p99_response_time*1000:.2f}ms")
                        logger.info(f"  スループット: {metrics.throughput:.2f} req/s")
                        logger.info(f"  成功数: {metrics.success_count}")
                        logger.info(f"  エラー数: {metrics.error_count}")
        
        # システムリソース分析
        if self.system_metrics:
            logger.info(f"\n--- システムリソース使用状況 ---")
            
            avg_cpu = statistics.mean([m["cpu_percent"] for m in self.system_metrics])
            max_cpu = max([m["cpu_percent"] for m in self.system_metrics])
            
            avg_memory = statistics.mean([m["memory_percent"] for m in self.system_metrics])
            max_memory = max([m["memory_percent"] for m in self.system_metrics])
            
            logger.info(f"  平均CPU使用率: {avg_cpu:.1f}%")
            logger.info(f"  最大CPU使用率: {max_cpu:.1f}%")
            logger.info(f"  平均メモリ使用率: {avg_memory:.1f}%")
            logger.info(f"  最大メモリ使用率: {max_memory:.1f}%")
        
        # パフォーマンス判定
        self.evaluate_performance()
        
        # 詳細レポートファイル出力
        await self.generate_detailed_report()
    
    def evaluate_performance(self):
        """パフォーマンス評価"""
        logger.info(f"\n=== パフォーマンス評価 ===")
        
        # 評価基準
        criteria = {
            "api_response_time": 1000,  # 1秒以内
            "websocket_connection_time": 2000,  # 2秒以内
            "success_rate": 95,  # 95%以上
            "throughput_per_user": 1,  # 1 req/s/user以上
            "system_cpu": 80,  # 80%以下
            "system_memory": 80  # 80%以下
        }
        
        passed_criteria = 0
        total_criteria = len(criteria)
        
        for test_name, test_result in self.results.items():
            if isinstance(test_result, dict):
                for category_name, metrics in test_result.items():
                    if isinstance(metrics, PerformanceMetrics):
                        # 成功率チェック
                        if metrics.success_rate >= criteria["success_rate"]:
                            passed_criteria += 1
                            logger.info(f"✅ {category_name} 成功率: {metrics.success_rate:.1f}% (基準: {criteria['success_rate']}%)")
                        else:
                            logger.warning(f"❌ {category_name} 成功率: {metrics.success_rate:.1f}% (基準: {criteria['success_rate']}%)")
                        
                        # 応答時間チェック
                        avg_ms = metrics.avg_response_time * 1000
                        if avg_ms <= criteria["api_response_time"]:
                            logger.info(f"✅ {category_name} 平均応答時間: {avg_ms:.2f}ms (基準: {criteria['api_response_time']}ms)")
                        else:
                            logger.warning(f"❌ {category_name} 平均応答時間: {avg_ms:.2f}ms (基準: {criteria['api_response_time']}ms)")
        
        # システムリソースチェック
        if self.system_metrics:
            avg_cpu = statistics.mean([m["cpu_percent"] for m in self.system_metrics])
            avg_memory = statistics.mean([m["memory_percent"] for m in self.system_metrics])
            
            if avg_cpu <= criteria["system_cpu"]:
                passed_criteria += 1
                logger.info(f"✅ 平均CPU使用率: {avg_cpu:.1f}% (基準: {criteria['system_cpu']}%)")
            else:
                logger.warning(f"❌ 平均CPU使用率: {avg_cpu:.1f}% (基準: {criteria['system_cpu']}%)")
            
            if avg_memory <= criteria["system_memory"]:
                passed_criteria += 1
                logger.info(f"✅ 平均メモリ使用率: {avg_memory:.1f}% (基準: {criteria['system_memory']}%)")
            else:
                logger.warning(f"❌ 平均メモリ使用率: {avg_memory:.1f}% (基準: {criteria['system_memory']}%)")
        
        # 総合評価
        performance_score = (passed_criteria / total_criteria) * 100
        logger.info(f"\n🎯 総合パフォーマンススコア: {performance_score:.1f}%")
        
        if performance_score >= 80:
            logger.info("🎉 優秀 - システムは高負荷条件下でも良好に動作しています")
        elif performance_score >= 60:
            logger.info("✅ 良好 - システムは許容可能なパフォーマンスを示しています")
        elif performance_score >= 40:
            logger.warning("⚠️ 改善必要 - いくつかのパフォーマンス問題があります")
        else:
            logger.error("❌ 要対応 - 重大なパフォーマンス問題があります")
    
    async def generate_detailed_report(self):
        """詳細レポートファイル生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"load_test_report_{timestamp}.json"
        
        report_data = {
            "test_config": {
                "concurrent_users": CONCURRENT_USERS,
                "test_duration_seconds": TEST_DURATION_SECONDS,
                "ramp_up_time_seconds": RAMP_UP_TIME_SECONDS,
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "end_time": datetime.now().isoformat()
            },
            "results": {},
            "system_metrics": self.system_metrics
        }
        
        # メトリクスデータの変換
        for test_name, test_result in self.results.items():
            if isinstance(test_result, dict):
                report_data["results"][test_name] = {}
                for category_name, metrics in test_result.items():
                    if isinstance(metrics, PerformanceMetrics):
                        report_data["results"][test_name][category_name] = {
                            "success_count": metrics.success_count,
                            "error_count": metrics.error_count,
                            "success_rate": metrics.success_rate,
                            "avg_response_time_ms": metrics.avg_response_time * 1000,
                            "p95_response_time_ms": metrics.p95_response_time * 1000,
                            "p99_response_time_ms": metrics.p99_response_time * 1000,
                            "throughput": metrics.throughput
                        }
        
        # ファイル出力
        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"✅ 詳細レポートを出力: {report_filename}")
        except Exception as e:
            logger.error(f"❌ レポート出力エラー: {e}")


async def main():
    """メイン実行関数"""
    logger.info("AI漫画生成サービス 負荷テストツール")
    logger.info("=" * 50)
    
    # メモリクリーンアップ
    gc.collect()
    
    # 負荷テスト実行
    load_tester = LoadTester()
    await load_tester.run_comprehensive_load_test()
    
    logger.info("=== 負荷テスト完了 ===")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("負荷テストが中断されました")
    except Exception as e:
        logger.error(f"負荷テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()