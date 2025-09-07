#!/usr/bin/env python3
"""
Performance Optimization Runner
データベースインデックス作成とパフォーマンス最適化の実行スクリプト
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database_optimized import optimized_db_manager
from app.core.database_indexes import index_manager
from app.core.async_optimization import async_optimizer
from app.core.config import settings
from app.core.logging import LoggerMixin


class PerformanceOptimizationRunner(LoggerMixin):
    """パフォーマンス最適化実行管理"""
    
    def __init__(self):
        super().__init__()
    
    async def run_all_optimizations(self) -> Dict[str, Any]:
        """全ての最適化を実行"""
        results = {
            "started_at": datetime.utcnow().isoformat(),
            "optimizations": {},
            "summary": {}
        }
        
        try:
            self.logger.info("Starting performance optimization process")
            
            # 1. データベース健全性チェック
            self.logger.info("Checking database health...")
            health_check = await optimized_db_manager.health_check()
            results["optimizations"]["database_health"] = health_check
            
            if health_check["status"] != "healthy":
                raise Exception(f"Database not healthy: {health_check.get('error')}")
            
            # 2. データベースインデックス作成
            self.logger.info("Creating performance indexes...")
            async with optimized_db_manager.get_optimized_session() as db:
                index_results = await index_manager.create_all_indexes(db)
                results["optimizations"]["indexes"] = index_results
            
            # 3. クエリパフォーマンス分析
            self.logger.info("Analyzing query performance...")
            async with optimized_db_manager.get_optimized_session() as db:
                perf_analysis = await index_manager.analyze_query_performance(db)
                results["optimizations"]["query_analysis"] = perf_analysis
            
            # 4. 非同期最適化の初期化
            self.logger.info("Initializing async optimizations...")
            await async_optimizer.start()
            results["optimizations"]["async_optimizer"] = {"status": "initialized"}
            
            # 5. 設定最適化の検証
            self.logger.info("Validating configuration optimizations...")
            config_validation = self._validate_performance_config()
            results["optimizations"]["config_validation"] = config_validation
            
            # サマリー作成
            results["summary"] = {
                "total_indexes_created": len(results["optimizations"]["indexes"].get("created", [])),
                "slow_queries_detected": len(results["optimizations"]["query_analysis"].get("missing_indexes", [])),
                "optimization_status": "completed",
                "recommendations": self._generate_recommendations(results)
            }
            
            self.logger.info("Performance optimization completed successfully")
            
        except Exception as e:
            self.logger.error(f"Performance optimization failed: {e}")
            results["summary"] = {
                "optimization_status": "failed",
                "error": str(e)
            }
        
        finally:
            results["completed_at"] = datetime.utcnow().isoformat()
        
        return results
    
    def _validate_performance_config(self) -> Dict[str, Any]:
        """パフォーマンス設定の検証"""
        validation = {
            "database_pool": {
                "pool_size": settings.database_pool_size,
                "max_overflow": settings.database_max_overflow,
                "status": "ok" if settings.database_pool_size >= 10 else "suboptimal"
            },
            "redis_settings": {
                "max_connections": settings.redis_max_connections,
                "status": "ok" if settings.redis_max_connections >= 10 else "suboptimal"
            },
            "ai_processing": {
                "max_parallel": settings.max_parallel_image_generation,
                "timeout": settings.ai_api_timeout,
                "status": "ok" if settings.max_parallel_image_generation >= 3 else "suboptimal"
            }
        }
        
        return validation
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """最適化結果に基づく推奨事項生成"""
        recommendations = []
        
        # インデックス推奨
        indexes_created = len(results["optimizations"]["indexes"].get("created", []))
        if indexes_created > 0:
            recommendations.append(f"Created {indexes_created} performance indexes - monitor query performance")
        
        # スロークエリ推奨
        missing_indexes = results["optimizations"]["query_analysis"].get("missing_indexes", [])
        if missing_indexes:
            recommendations.append(f"Consider creating {len(missing_indexes)} additional indexes for optimal performance")
        
        # 設定推奨
        config_validation = results["optimizations"]["config_validation"]
        suboptimal_configs = [
            key for key, value in config_validation.items()
            if value.get("status") == "suboptimal"
        ]
        
        if suboptimal_configs:
            recommendations.append(f"Review configuration for: {', '.join(suboptimal_configs)}")
        
        return recommendations
    
    async def run_performance_benchmark(self) -> Dict[str, Any]:
        """パフォーマンスベンチマークの実行"""
        benchmark_results = {
            "started_at": datetime.utcnow().isoformat(),
            "tests": {}
        }
        
        try:
            # データベース接続テスト
            async with optimized_db_manager.get_optimized_session() as db:
                
                # 1. 単純クエリのベンチマーク
                start_time = time.time()
                await db.execute("SELECT 1")
                simple_query_time = time.time() - start_time
                
                benchmark_results["tests"]["simple_query"] = {
                    "duration_ms": simple_query_time * 1000,
                    "status": "fast" if simple_query_time < 0.01 else "slow"
                }
                
                # 2. 接続プール効率テスト
                start_time = time.time()
                tasks = []
                for _ in range(10):
                    tasks.append(db.execute("SELECT 1"))
                
                await asyncio.gather(*tasks)
                pool_test_time = time.time() - start_time
                
                benchmark_results["tests"]["connection_pool"] = {
                    "duration_ms": pool_test_time * 1000,
                    "concurrent_queries": 10,
                    "avg_per_query_ms": (pool_test_time / 10) * 1000
                }
            
            # 3. 非同期処理テスト
            start_time = time.time()
            async_tasks = [asyncio.sleep(0.1) for _ in range(5)]
            await asyncio.gather(*async_tasks)
            async_test_time = time.time() - start_time
            
            benchmark_results["tests"]["async_processing"] = {
                "duration_ms": async_test_time * 1000,
                "expected_min_ms": 100,  # Should be ~100ms, not 500ms
                "efficiency": "good" if async_test_time < 0.15 else "poor"
            }
            
            # ベンチマーク評価
            benchmark_results["overall_score"] = self._calculate_benchmark_score(benchmark_results["tests"])
            
        except Exception as e:
            self.logger.error(f"Performance benchmark failed: {e}")
            benchmark_results["error"] = str(e)
        
        finally:
            benchmark_results["completed_at"] = datetime.utcnow().isoformat()
        
        return benchmark_results
    
    def _calculate_benchmark_score(self, tests: Dict[str, Any]) -> Dict[str, Any]:
        """ベンチマークスコアの計算"""
        scores = []
        
        # 単純クエリスコア
        simple_duration = tests.get("simple_query", {}).get("duration_ms", 1000)
        simple_score = max(0, 100 - (simple_duration * 10))  # 1ms = 90点
        scores.append(simple_score)
        
        # 接続プールスコア
        pool_avg = tests.get("connection_pool", {}).get("avg_per_query_ms", 1000)
        pool_score = max(0, 100 - (pool_avg * 2))  # 1ms = 98点
        scores.append(pool_score)
        
        # 非同期処理スコア
        async_duration = tests.get("async_processing", {}).get("duration_ms", 1000)
        async_score = max(0, 100 - ((async_duration - 100) * 5))  # 100ms基準
        scores.append(async_score)
        
        overall_score = sum(scores) / len(scores) if scores else 0
        
        return {
            "overall_score": round(overall_score, 1),
            "component_scores": {
                "database_query": round(simple_score, 1),
                "connection_pool": round(pool_score, 1),
                "async_processing": round(async_score, 1)
            },
            "grade": self._score_to_grade(overall_score)
        }
    
    def _score_to_grade(self, score: float) -> str:
        """スコアをグレードに変換"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"


async def main():
    """メイン実行関数"""
    runner = PerformanceOptimizationRunner()
    
    print("🚀 Starting Performance Optimization...")
    print("=" * 50)
    
    # 最適化実行
    optimization_results = await runner.run_all_optimizations()
    
    # 結果表示
    print("\n📊 Optimization Results:")
    print("-" * 30)
    
    summary = optimization_results.get("summary", {})
    print(f"Status: {summary.get('optimization_status', 'unknown')}")
    print(f"Indexes Created: {summary.get('total_indexes_created', 0)}")
    print(f"Slow Queries: {summary.get('slow_queries_detected', 0)}")
    
    # 推奨事項
    recommendations = summary.get("recommendations", [])
    if recommendations:
        print("\n💡 Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    
    # ベンチマーク実行
    print("\n🏃 Running Performance Benchmark...")
    benchmark_results = await runner.run_performance_benchmark()
    
    # ベンチマーク結果表示
    if "overall_score" in benchmark_results:
        score_info = benchmark_results["overall_score"]
        print(f"\n📈 Performance Score: {score_info['overall_score']}/100 (Grade: {score_info['grade']})")
        
        print("\nComponent Scores:")
        for component, score in score_info["component_scores"].items():
            print(f"  {component}: {score}/100")
    
    # クリーンアップ
    await async_optimizer.cleanup()
    print("\n✅ Performance optimization completed!")


if __name__ == "__main__":
    # Import guard for datetime
    from datetime import datetime
    
    asyncio.run(main())