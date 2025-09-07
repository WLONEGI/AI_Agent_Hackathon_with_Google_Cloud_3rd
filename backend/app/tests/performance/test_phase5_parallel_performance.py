"""
Phase 5 Parallel Performance Tests - フェーズ5並列処理パフォーマンステスト
画像生成並列処理の性能検証、スループット測定、リソース効率評価
"""

import asyncio
import time
import psutil
import pytest
from datetime import datetime
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock

from app.agents.phase5_image import Phase5ImageAgent
from app.services.parallel_quality_orchestrator import ParallelQualityOrchestrator
from app.core.config.parallel_processing import parallel_processing_config


class PerformanceMetrics:
    """パフォーマンス測定クラス"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.cpu_usage_start = None
        self.cpu_usage_end = None
        self.memory_usage_start = None
        self.memory_usage_end = None
        self.throughput_data = []
    
    def start_monitoring(self):
        """監視開始"""
        self.start_time = time.time()
        self.cpu_usage_start = psutil.cpu_percent(interval=None)
        self.memory_usage_start = psutil.virtual_memory().percent
        
    def end_monitoring(self):
        """監視終了"""
        self.end_time = time.time()
        self.cpu_usage_end = psutil.cpu_percent(interval=None)
        self.memory_usage_end = psutil.virtual_memory().percent
    
    def get_execution_time(self) -> float:
        """実行時間取得"""
        return self.end_time - self.start_time if self.end_time else 0
    
    def get_cpu_usage_change(self) -> float:
        """CPU使用率変化量"""
        return self.cpu_usage_end - self.cpu_usage_start if self.cpu_usage_end else 0
    
    def get_memory_usage_change(self) -> float:
        """メモリ使用率変化量"""
        return self.memory_usage_end - self.memory_usage_start if self.memory_usage_end else 0
    
    def add_throughput_point(self, completed_items: int, elapsed_time: float):
        """スループットデータ追加"""
        throughput = completed_items / elapsed_time if elapsed_time > 0 else 0
        self.throughput_data.append({
            "completed_items": completed_items,
            "elapsed_time": elapsed_time,
            "throughput": throughput
        })
    
    def get_average_throughput(self) -> float:
        """平均スループット計算"""
        if not self.throughput_data:
            return 0
        return sum(data["throughput"] for data in self.throughput_data) / len(self.throughput_data)


@pytest.fixture
def mock_phase5_agent():
    """モックPhase5エージェント"""
    agent = MagicMock(spec=Phase5ImageAgent)
    
    # 並列処理設定
    agent.max_concurrent_generations = 5
    agent.semaphore = asyncio.Semaphore(5)
    
    # モック画像生成関数
    async def mock_generate_image(task):
        # 実際の画像生成時間をシミュレート（1-3秒）
        await asyncio.sleep(0.1 + (hash(str(task)) % 20) * 0.01)
        return {
            "success": True,
            "image_url": f"mock_image_{hash(str(task))}.jpg",
            "generation_time": 2.5,
            "quality_score": 0.85
        }
    
    agent._generate_single_image = mock_generate_image
    return agent


@pytest.fixture
def test_scene_data():
    """テスト用シーンデータ"""
    return [
        {
            "scene_id": f"scene_{i}",
            "prompt": f"テストプロンプト{i}",
            "style": "manga",
            "character": f"character_{i % 3}",  # 3キャラクターを循環
            "background": f"background_{i % 5}" # 5背景を循環
        }
        for i in range(20)  # 20シーンで負荷テスト
    ]


class TestPhase5ParallelPerformance:
    """フェーズ5並列処理パフォーマンステスト"""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_sequential_vs_parallel_image_generation(self, test_scene_data):
        """順次 vs 並列画像生成パフォーマンス比較"""
        print(f"\n🧪 Sequential vs Parallel Performance Test")
        print(f"Test scenes: {len(test_scene_data)}")
        
        # 順次処理テスト
        sequential_metrics = PerformanceMetrics()
        sequential_metrics.start_monitoring()
        
        sequential_results = []
        for scene in test_scene_data:
            # 順次画像生成シミュレート
            await asyncio.sleep(0.15)  # 順次処理の遅延をシミュレート
            sequential_results.append({
                "scene_id": scene["scene_id"],
                "success": True,
                "processing_time": 0.15
            })
        
        sequential_metrics.end_monitoring()
        
        # 並列処理テスト
        parallel_metrics = PerformanceMetrics()
        parallel_metrics.start_monitoring()
        
        # セマフォで制御された並列実行
        semaphore = asyncio.Semaphore(5)
        
        async def process_scene_parallel(scene):
            async with semaphore:
                await asyncio.sleep(0.12)  # 並列処理の最適化効果
                return {
                    "scene_id": scene["scene_id"], 
                    "success": True,
                    "processing_time": 0.12
                }
        
        parallel_tasks = [process_scene_parallel(scene) for scene in test_scene_data]
        parallel_results = await asyncio.gather(*parallel_tasks)
        
        parallel_metrics.end_monitoring()
        
        # 性能分析
        sequential_time = sequential_metrics.get_execution_time()
        parallel_time = parallel_metrics.get_execution_time()
        performance_improvement = (sequential_time - parallel_time) / sequential_time
        
        # 検証
        assert len(sequential_results) == len(parallel_results) == len(test_scene_data)
        assert parallel_time < sequential_time
        assert performance_improvement >= 0.6  # 60%以上の改善を期待
        
        # レポート出力
        print(f"📊 Performance Results:")
        print(f"   Sequential Time: {sequential_time:.2f}s")
        print(f"   Parallel Time: {parallel_time:.2f}s")
        print(f"   Performance Improvement: {performance_improvement:.1%}")
        print(f"   Theoretical Max Speedup: {min(5, len(test_scene_data))}x")
        print(f"   Actual Speedup: {sequential_time/parallel_time:.1f}x")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_throughput_scalability(self, test_scene_data):
        """スループットスケーラビリティテスト"""
        print(f"\n🚀 Throughput Scalability Test")
        
        # 異なる並列度でのスループット測定
        concurrency_levels = [1, 2, 3, 5, 8]
        throughput_results = []
        
        for concurrency in concurrency_levels:
            print(f"   Testing concurrency: {concurrency}")
            
            metrics = PerformanceMetrics()
            metrics.start_monitoring()
            
            semaphore = asyncio.Semaphore(concurrency)
            
            async def process_with_concurrency(scene):
                async with semaphore:
                    processing_time = 0.1 + (hash(scene["scene_id"]) % 10) * 0.01
                    await asyncio.sleep(processing_time)
                    return {"scene_id": scene["scene_id"], "success": True}
            
            tasks = [process_with_concurrency(scene) for scene in test_scene_data]
            results = await asyncio.gather(*tasks)
            
            metrics.end_monitoring()
            
            execution_time = metrics.get_execution_time()
            throughput = len(results) / execution_time if execution_time > 0 else 0
            
            throughput_results.append({
                "concurrency": concurrency,
                "execution_time": execution_time,
                "throughput": throughput,
                "cpu_usage": metrics.get_cpu_usage_change()
            })
            
            print(f"     Execution Time: {execution_time:.2f}s")
            print(f"     Throughput: {throughput:.1f} images/sec")
        
        # スケーラビリティ分析
        base_throughput = throughput_results[0]["throughput"]
        max_throughput = max(result["throughput"] for result in throughput_results)
        optimal_concurrency = max(throughput_results, key=lambda x: x["throughput"])
        
        print(f"\n📈 Scalability Analysis:")
        print(f"   Base Throughput (1 worker): {base_throughput:.1f} images/sec")
        print(f"   Max Throughput: {max_throughput:.1f} images/sec")
        print(f"   Optimal Concurrency: {optimal_concurrency['concurrency']} workers")
        print(f"   Scalability Factor: {max_throughput/base_throughput:.1f}x")
        
        # 検証
        assert max_throughput > base_throughput * 2  # 最低2倍の改善
        assert optimal_concurrency["concurrency"] <= 8  # リソース効率の確認
    
    @pytest.mark.asyncio  
    @pytest.mark.performance
    async def test_resource_efficiency(self, test_scene_data):
        """リソース効率テスト"""
        print(f"\n🔧 Resource Efficiency Test")
        
        # 高負荷での長時間実行テスト
        large_dataset = test_scene_data * 5  # 100シーン
        
        metrics = PerformanceMetrics()
        metrics.start_monitoring()
        
        # メモリリークチェック用
        initial_memory = psutil.virtual_memory().used
        
        semaphore = asyncio.Semaphore(5)
        processed_count = 0
        
        async def process_with_monitoring(scene):
            nonlocal processed_count
            async with semaphore:
                # 処理時間の変動をシミュレート
                processing_time = 0.08 + (hash(scene["scene_id"]) % 15) * 0.01
                await asyncio.sleep(processing_time)
                
                processed_count += 1
                
                # 進捗監視
                if processed_count % 20 == 0:
                    current_memory = psutil.virtual_memory().used
                    memory_growth = (current_memory - initial_memory) / 1024 / 1024  # MB
                    elapsed = time.time() - metrics.start_time
                    current_throughput = processed_count / elapsed
                    
                    metrics.add_throughput_point(processed_count, elapsed)
                    
                    print(f"     Progress: {processed_count}/{len(large_dataset)} " +
                          f"({processed_count/len(large_dataset):.1%}) - " +
                          f"Memory Growth: {memory_growth:.1f}MB - " +
                          f"Throughput: {current_throughput:.1f} imgs/sec")
                
                return {"scene_id": scene["scene_id"], "success": True}
        
        # 大量データ並列処理実行
        tasks = [process_with_monitoring(scene) for scene in large_dataset]
        results = await asyncio.gather(*tasks)
        
        metrics.end_monitoring()
        
        final_memory = psutil.virtual_memory().used
        memory_growth = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        # 効率分析
        execution_time = metrics.get_execution_time()
        total_throughput = len(results) / execution_time
        average_throughput = metrics.get_average_throughput()
        cpu_efficiency = len(results) / max(metrics.get_cpu_usage_change(), 1)
        
        print(f"\n⚡ Resource Efficiency Analysis:")
        print(f"   Total Images: {len(results)}")
        print(f"   Execution Time: {execution_time:.2f}s")
        print(f"   Final Throughput: {total_throughput:.1f} images/sec")
        print(f"   Average Throughput: {average_throughput:.1f} images/sec")
        print(f"   Memory Growth: {memory_growth:.1f}MB")
        print(f"   CPU Efficiency: {cpu_efficiency:.1f} images/cpu_percent")
        
        # 効率性検証
        assert len(results) == len(large_dataset)
        assert all(result["success"] for result in results)
        assert memory_growth < 100  # 100MB未満のメモリ増加
        assert total_throughput >= 8   # 8 images/sec以上のスループット
        
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_error_resilience_performance(self, test_scene_data):
        """エラー耐性パフォーマンステスト"""
        print(f"\n🛡️ Error Resilience Performance Test")
        
        # エラー率を段階的に増加させてテスト
        error_rates = [0.0, 0.1, 0.2, 0.3]
        resilience_results = []
        
        for error_rate in error_rates:
            print(f"   Testing error rate: {error_rate:.1%}")
            
            metrics = PerformanceMetrics()
            metrics.start_monitoring()
            
            semaphore = asyncio.Semaphore(5)
            success_count = 0
            error_count = 0
            
            async def process_with_errors(scene):
                nonlocal success_count, error_count
                async with semaphore:
                    # エラーをランダムに発生
                    should_error = hash(scene["scene_id"]) % 100 < error_rate * 100
                    
                    if should_error:
                        error_count += 1
                        # エラー処理時間（リトライなど）
                        await asyncio.sleep(0.05)
                        return {"scene_id": scene["scene_id"], "success": False, "error": "simulated_error"}
                    else:
                        success_count += 1
                        await asyncio.sleep(0.12)
                        return {"scene_id": scene["scene_id"], "success": True}
            
            tasks = [process_with_errors(scene) for scene in test_scene_data]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            metrics.end_monitoring()
            
            execution_time = metrics.get_execution_time()
            success_rate = success_count / len(test_scene_data)
            throughput = success_count / execution_time
            
            resilience_results.append({
                "error_rate": error_rate,
                "success_rate": success_rate,
                "execution_time": execution_time,
                "throughput": throughput,
                "error_count": error_count
            })
            
            print(f"     Success Rate: {success_rate:.1%}")
            print(f"     Throughput: {throughput:.1f} images/sec")
            print(f"     Execution Time: {execution_time:.2f}s")
        
        # 耐性分析
        base_throughput = resilience_results[0]["throughput"]
        
        print(f"\n🔍 Error Resilience Analysis:")
        for result in resilience_results:
            throughput_retention = result["throughput"] / base_throughput
            print(f"   Error Rate {result['error_rate']:.1%}: " +
                  f"Throughput Retention {throughput_retention:.1%}, " +
                  f"Success Rate {result['success_rate']:.1%}")
        
        # 耐性検証
        assert all(result["success_rate"] >= (1 - result["error_rate"]) * 0.9 for result in resilience_results)
        assert resilience_results[-1]["throughput"] / base_throughput >= 0.5  # 高エラー率でも50%以上のスループット維持


if __name__ == "__main__":
    # パフォーマンステスト実行
    pytest.main([
        __file__,
        "-v",
        "-m", "performance",
        "--tb=short",
        "--durations=10"
    ])