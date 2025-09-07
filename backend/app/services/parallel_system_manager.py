"""
Parallel System Manager - 並列システム統合管理
監視、設定、最適化を統合した並列処理システムの中央管理サービス
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from app.core.logging import LoggerMixin
from app.services.performance_monitoring_service import PerformanceMonitoringService
from app.services.parallel_configuration_service import (
    ParallelConfigurationService,
    ConfigurationScope
)
from app.services.parallel_quality_orchestrator import ParallelQualityOrchestrator


class ParallelSystemManager(LoggerMixin):
    """並列システム統合管理サービス"""
    
    def __init__(self):
        super().__init__()
        
        # コンポーネントサービス
        self.monitoring_service = PerformanceMonitoringService()
        self.configuration_service = ParallelConfigurationService()
        self.quality_orchestrator = None  # 必要に応じて初期化
        
        # システム状態
        self.system_health_status = "unknown"
        self.last_health_check = None
        self.system_alerts = []
        
        # 自動最適化設定
        self.auto_optimization_interval = 300  # 5分
        self.optimization_task = None
        self.is_auto_optimizing = False
        
        # 統計
        self.system_stats = {
            "uptime_start": datetime.utcnow(),
            "total_optimizations_applied": 0,
            "total_alerts_triggered": 0,
            "total_configuration_changes": 0
        }
        
        # コールバック設定
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """コールバック設定"""
        # 監視サービスのアラートコールバック
        self.monitoring_service.add_alert_callback(self._handle_performance_alert)
        
        # 設定サービスの変更コールバック
        self.configuration_service.add_change_callback(self._handle_configuration_change)
    
    async def start_system(self):
        """システム開始"""
        try:
            self.logger.info("Starting Parallel System Manager...")
            
            # 監視開始
            await self.monitoring_service.start_monitoring()
            
            # 自動最適化開始
            await self.start_auto_optimization()
            
            # 初期ヘルスチェック
            await self.perform_health_check()
            
            self.logger.info("Parallel System Manager started successfully")
            
        except Exception as e:
            self.logger.error(f"System startup error: {e}")
            raise
    
    async def stop_system(self):
        """システム停止"""
        try:
            self.logger.info("Stopping Parallel System Manager...")
            
            # 自動最適化停止
            await self.stop_auto_optimization()
            
            # 監視停止
            await self.monitoring_service.stop_monitoring()
            
            # 設定保存
            await self.configuration_service.save_configuration_file()
            
            self.logger.info("Parallel System Manager stopped")
            
        except Exception as e:
            self.logger.error(f"System shutdown error: {e}")
    
    async def start_auto_optimization(self):
        """自動最適化開始"""
        if self.is_auto_optimizing:
            self.logger.warning("Auto-optimization is already running")
            return
        
        self.is_auto_optimizing = True
        self.optimization_task = asyncio.create_task(self._auto_optimization_loop())
        
        self.logger.info("Auto-optimization started")
    
    async def stop_auto_optimization(self):
        """自動最適化停止"""
        if not self.is_auto_optimizing:
            return
        
        self.is_auto_optimizing = False
        if self.optimization_task:
            self.optimization_task.cancel()
            try:
                await self.optimization_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Auto-optimization stopped")
    
    async def _auto_optimization_loop(self):
        """自動最適化ループ"""
        try:
            while self.is_auto_optimizing:
                await self._perform_optimization_cycle()
                await asyncio.sleep(self.auto_optimization_interval)
        except asyncio.CancelledError:
            self.logger.info("Auto-optimization loop cancelled")
        except Exception as e:
            self.logger.error(f"Auto-optimization loop error: {e}")
    
    async def _perform_optimization_cycle(self):
        """最適化サイクル実行"""
        try:
            # 現在のパフォーマンスメトリクス取得
            performance_summary = self.monitoring_service.get_performance_summary(hours=1)
            
            # メトリクス抽出
            metrics = self._extract_optimization_metrics(performance_summary)
            
            # 自動最適化適用
            optimizations = await self.configuration_service.apply_auto_optimization(metrics)
            
            if optimizations:
                self.system_stats["total_optimizations_applied"] += len(optimizations)
                
                self.logger.info(
                    f"Applied {len(optimizations)} auto-optimizations",
                    optimizations=optimizations
                )
            
        except Exception as e:
            self.logger.error(f"Optimization cycle error: {e}")
    
    def _extract_optimization_metrics(self, performance_summary: Dict[str, Any]) -> Dict[str, float]:
        """最適化用メトリクス抽出"""
        try:
            system_resources = performance_summary.get("system_resources", {})
            parallel_processing = performance_summary.get("parallel_processing", {})
            
            return {
                "cpu_usage": system_resources.get("cpu", {}).get("average", 0),
                "memory_usage": system_resources.get("memory", {}).get("average", 0),
                "processing_time": parallel_processing.get("processing_time", {}).get("average", 0),
                "throughput": parallel_processing.get("throughput", {}).get("average", 0),
                "queue_length": 0,  # 実際のキュー長を取得する実装が必要
                "cache_hit_rate": 0.5,  # 実際のキャッシュヒット率を取得する実装が必要
                "error_rate": 0  # 実際のエラー率を取得する実装が必要
            }
            
        except Exception as e:
            self.logger.error(f"Metrics extraction error: {e}")
            return {}
    
    async def perform_health_check(self) -> Dict[str, Any]:
        """システムヘルスチェック"""
        try:
            self.logger.info("Performing system health check...")
            
            # 各コンポーネントの状態取得
            monitoring_status = self.monitoring_service.get_current_status()
            configuration_status = self.configuration_service.get_configuration_status()
            
            # パフォーマンス要約取得
            performance_summary = self.monitoring_service.get_performance_summary(hours=1)
            
            # 健康度スコア計算
            health_score = self._calculate_system_health_score(
                monitoring_status, configuration_status, performance_summary
            )
            
            # システム状態判定
            if health_score >= 80:
                self.system_health_status = "excellent"
            elif health_score >= 60:
                self.system_health_status = "good"
            elif health_score >= 40:
                self.system_health_status = "warning"
            else:
                self.system_health_status = "critical"
            
            self.last_health_check = datetime.utcnow()
            
            health_report = {
                "health_status": self.system_health_status,
                "health_score": health_score,
                "last_check": self.last_health_check.isoformat(),
                "monitoring_status": monitoring_status,
                "configuration_status": configuration_status,
                "performance_summary": performance_summary,
                "active_alerts": len(self.system_alerts),
                "system_uptime": (datetime.utcnow() - self.system_stats["uptime_start"]).total_seconds()
            }
            
            self.logger.info(
                f"Health check completed",
                status=self.system_health_status,
                score=health_score
            )
            
            return health_report
            
        except Exception as e:
            self.logger.error(f"Health check error: {e}")
            return {"error": str(e)}
    
    def _calculate_system_health_score(self,
                                     monitoring_status: Dict[str, Any],
                                     configuration_status: Dict[str, Any],
                                     performance_summary: Dict[str, Any]) -> float:
        """システムヘルススコア計算"""
        try:
            score = 100.0
            
            # 監視サービス状態
            if not monitoring_status.get("monitoring_active", False):
                score -= 20
            
            # パフォーマンス指標
            system_resources = performance_summary.get("system_resources", {})
            
            # CPU使用率
            cpu_avg = system_resources.get("cpu", {}).get("average", 0)
            if cpu_avg > 80:
                score -= 15
            elif cpu_avg > 60:
                score -= 5
            
            # メモリ使用率
            memory_avg = system_resources.get("memory", {}).get("average", 0)
            if memory_avg > 85:
                score -= 15
            elif memory_avg > 70:
                score -= 5
            
            # アクティブアラート
            if len(self.system_alerts) > 0:
                score -= min(len(self.system_alerts) * 5, 20)
            
            # 設定の健全性
            config_changes = configuration_status.get("configuration_changes", 0)
            if config_changes > 50:  # 頻繁な設定変更
                score -= 10
            
            return max(score, 0.0)
            
        except Exception:
            return 50.0  # デフォルトスコア
    
    async def _handle_performance_alert(self, alert_info: Dict[str, Any]):
        """パフォーマンスアラート処理"""
        try:
            self.system_alerts.append({
                **alert_info,
                "source": "performance_monitoring"
            })
            
            self.system_stats["total_alerts_triggered"] += 1
            
            # アラート種別に応じた対応
            alert_type = alert_info.get("type")
            
            if alert_type == "high_cpu_usage":
                await self._handle_high_cpu_alert(alert_info)
            elif alert_type == "high_memory_usage":
                await self._handle_high_memory_alert(alert_info)
            elif alert_type == "high_queue_length":
                await self._handle_high_queue_alert(alert_info)
            
            self.logger.warning(
                f"Performance alert handled: {alert_type}",
                alert_data=alert_info
            )
            
        except Exception as e:
            self.logger.error(f"Performance alert handling error: {e}")
    
    async def _handle_high_cpu_alert(self, alert_info: Dict[str, Any]):
        """高CPU使用率アラート処理"""
        # ワーカー数を一時的に削減
        await self.configuration_service.update_configuration(
            "max_concurrent_workers",
            max(1, int(self.configuration_service.current_config.max_concurrent_workers * 0.8)),
            scope=ConfigurationScope.TEMPORARY,
            reason="High CPU usage alert response"
        )
    
    async def _handle_high_memory_alert(self, alert_info: Dict[str, Any]):
        """高メモリ使用率アラート処理"""
        # バッチサイズを一時的に削減
        await self.configuration_service.update_configuration(
            "quality_gate_batch_size",
            max(1, int(self.configuration_service.current_config.quality_gate_batch_size * 0.7)),
            scope=ConfigurationScope.TEMPORARY,
            reason="High memory usage alert response"
        )
    
    async def _handle_high_queue_alert(self, alert_info: Dict[str, Any]):
        """高キュー長アラート処理"""
        # 並列度を一時的に増加（リソースが許す場合）
        current_cpu = alert_info.get("data", {}).get("cpu_percent", 100)
        if current_cpu < 70:
            await self.configuration_service.update_configuration(
                "max_concurrent_workers",
                min(10, int(self.configuration_service.current_config.max_concurrent_workers * 1.2)),
                scope=ConfigurationScope.TEMPORARY,
                reason="High queue length alert response"
            )
    
    async def _handle_configuration_change(self, change):
        """設定変更処理"""
        self.system_stats["total_configuration_changes"] += 1
        
        self.logger.info(
            f"Configuration change detected",
            config_path=change.config_path,
            scope=change.scope.value,
            reason=change.reason
        )
    
    async def create_system_backup(self, backup_name: str) -> Dict[str, Any]:
        """システムバックアップ作成"""
        try:
            # 設定バックアップ
            config_backup_success = await self.configuration_service.create_configuration_backup(
                f"system_backup_{backup_name}"
            )
            
            # パフォーマンスレポート生成
            performance_report = await self.monitoring_service.generate_performance_report(hours=24)
            
            backup_info = {
                "backup_name": backup_name,
                "timestamp": datetime.utcnow().isoformat(),
                "config_backup_success": config_backup_success,
                "performance_report": performance_report,
                "system_stats": self.system_stats.copy(),
                "health_status": self.system_health_status
            }
            
            self.logger.info(f"System backup created: {backup_name}")
            
            return backup_info
            
        except Exception as e:
            self.logger.error(f"System backup error: {e}")
            return {"error": str(e)}
    
    async def get_system_dashboard(self) -> Dict[str, Any]:
        """システムダッシュボード情報取得"""
        try:
            # 最新のヘルスチェック実行（必要に応じて）
            if (not self.last_health_check or 
                datetime.utcnow() - self.last_health_check > timedelta(minutes=5)):
                await self.perform_health_check()
            
            # 現在のステータス取得
            monitoring_status = self.monitoring_service.get_current_status()
            configuration_status = self.configuration_service.get_configuration_status()
            performance_summary = self.monitoring_service.get_performance_summary(hours=1)
            
            dashboard = {
                "system_overview": {
                    "health_status": self.system_health_status,
                    "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
                    "uptime_hours": (datetime.utcnow() - self.system_stats["uptime_start"]).total_seconds() / 3600,
                    "auto_optimization_active": self.is_auto_optimizing
                },
                "monitoring": {
                    "active": monitoring_status.get("monitoring_active", False),
                    "metrics_count": monitoring_status.get("metrics_count", 0),
                    "last_update": monitoring_status.get("last_update")
                },
                "configuration": {
                    "scoped_configs": configuration_status.get("scoped_config_count", 0),
                    "active_ab_tests": configuration_status.get("active_ab_tests", 0),
                    "auto_optimization_enabled": configuration_status.get("auto_optimization_enabled", False)
                },
                "performance": performance_summary,
                "alerts": {
                    "total_active": len(self.system_alerts),
                    "recent_alerts": self.system_alerts[-5:] if self.system_alerts else []
                },
                "statistics": self.system_stats,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return dashboard
            
        except Exception as e:
            self.logger.error(f"Dashboard generation error: {e}")
            return {"error": str(e)}
    
    def clear_old_alerts(self, hours: int = 24):
        """古いアラートのクリア"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            self.system_alerts = [
                alert for alert in self.system_alerts
                if datetime.fromisoformat(alert["timestamp"]) > cutoff_time
            ]
            
            self.logger.info(f"Cleared alerts older than {hours} hours")
            
        except Exception as e:
            self.logger.error(f"Alert cleanup error: {e}")
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """システム統計取得"""
        uptime = datetime.utcnow() - self.system_stats["uptime_start"]
        
        return {
            **self.system_stats,
            "current_uptime_hours": uptime.total_seconds() / 3600,
            "average_optimizations_per_hour": (
                self.system_stats["total_optimizations_applied"] / 
                max(uptime.total_seconds() / 3600, 1)
            ),
            "average_alerts_per_hour": (
                self.system_stats["total_alerts_triggered"] / 
                max(uptime.total_seconds() / 3600, 1)
            )
        }