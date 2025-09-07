"""
Performance Monitoring Service - パフォーマンス監視サービス
並列処理のリアルタイム監視、メトリクス収集、アラート機能
"""

import asyncio
import psutil
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, asdict
import logging

from app.core.logging import LoggerMixin


@dataclass
class PerformanceMetric:
    """パフォーマンスメトリクス"""
    timestamp: datetime
    metric_type: str
    value: float
    unit: str
    metadata: Dict[str, Any] = None


@dataclass
class SystemResourceSnapshot:
    """システムリソーススナップショット"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    network_sent_mb: float
    network_recv_mb: float


@dataclass
class ParallelProcessingStats:
    """並列処理統計"""
    timestamp: datetime
    active_workers: int
    queued_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_processing_time: float
    throughput_per_second: float


class PerformanceMonitoringService(LoggerMixin):
    """パフォーマンス監視サービス"""
    
    def __init__(self, 
                 monitoring_interval: int = 30,
                 metric_retention_hours: int = 24,
                 alert_thresholds: Dict[str, float] = None):
        super().__init__()
        
        # 監視設定
        self.monitoring_interval = monitoring_interval
        self.metric_retention_hours = metric_retention_hours
        self.is_monitoring = False
        self.monitoring_task = None
        
        # メトリクス保存
        self.performance_metrics: deque = deque(maxlen=10000)
        self.resource_snapshots: deque = deque(maxlen=1000)
        self.parallel_stats: deque = deque(maxlen=1000)
        
        # アラート設定
        self.alert_thresholds = alert_thresholds or {
            "cpu_usage": 80.0,         # CPU使用率 80%
            "memory_usage": 85.0,      # メモリ使用率 85%
            "processing_time": 30.0,   # 処理時間 30秒
            "error_rate": 0.1,         # エラー率 10%
            "queue_length": 100        # キュー長 100
        }
        
        # アラートコールバック
        self.alert_callbacks: List[Callable] = []
        
        # 統計計算用
        self.last_network_stats = psutil.net_io_counters()
        self.performance_baseline = None
    
    async def start_monitoring(self):
        """監視開始"""
        if self.is_monitoring:
            self.logger.warning("Performance monitoring is already running")
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        self.logger.info(
            "Performance monitoring started",
            interval=self.monitoring_interval,
            retention_hours=self.metric_retention_hours
        )
    
    async def stop_monitoring(self):
        """監視停止"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Performance monitoring stopped")
    
    async def _monitoring_loop(self):
        """監視ループ"""
        try:
            while self.is_monitoring:
                await self._collect_metrics()
                await asyncio.sleep(self.monitoring_interval)
        except asyncio.CancelledError:
            self.logger.info("Monitoring loop cancelled")
        except Exception as e:
            self.logger.error(f"Monitoring loop error: {e}")
    
    async def _collect_metrics(self):
        """メトリクス収集"""
        try:
            # システムリソース収集
            await self._collect_system_resources()
            
            # 古いメトリクス削除
            await self._cleanup_old_metrics()
            
            # アラートチェック
            await self._check_alerts()
            
        except Exception as e:
            self.logger.error(f"Metrics collection error: {e}")
    
    async def _collect_system_resources(self):
        """システムリソース収集"""
        try:
            # CPU・メモリ使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # ディスク使用率
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # ネットワーク統計
            network_stats = psutil.net_io_counters()
            network_sent_mb = (network_stats.bytes_sent - self.last_network_stats.bytes_sent) / 1024 / 1024
            network_recv_mb = (network_stats.bytes_recv - self.last_network_stats.bytes_recv) / 1024 / 1024
            self.last_network_stats = network_stats
            
            # スナップショット作成
            snapshot = SystemResourceSnapshot(
                timestamp=datetime.utcnow(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / 1024 / 1024,
                disk_usage_percent=disk_percent,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb
            )
            
            self.resource_snapshots.append(snapshot)
            
            # 個別メトリクス記録
            self._record_metric("system.cpu_usage", cpu_percent, "%")
            self._record_metric("system.memory_usage", memory.percent, "%")
            self._record_metric("system.disk_usage", disk_percent, "%")
            
        except Exception as e:
            self.logger.error(f"System resource collection error: {e}")
    
    def record_parallel_processing_stats(self,
                                       active_workers: int,
                                       queued_tasks: int,
                                       completed_tasks: int,
                                       failed_tasks: int,
                                       processing_times: List[float]):
        """並列処理統計記録"""
        try:
            # 平均処理時間計算
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            # スループット計算（過去1分間）
            recent_stats = [s for s in self.parallel_stats 
                          if s.timestamp > datetime.utcnow() - timedelta(minutes=1)]
            
            if recent_stats:
                total_completed = sum(s.completed_tasks for s in recent_stats)
                throughput = total_completed / 60.0  # per second
            else:
                throughput = 0
            
            # 統計記録
            stats = ParallelProcessingStats(
                timestamp=datetime.utcnow(),
                active_workers=active_workers,
                queued_tasks=queued_tasks,
                completed_tasks=completed_tasks,
                failed_tasks=failed_tasks,
                average_processing_time=avg_processing_time,
                throughput_per_second=throughput
            )
            
            self.parallel_stats.append(stats)
            
            # 個別メトリクス記録
            self._record_metric("parallel.active_workers", active_workers, "count")
            self._record_metric("parallel.queued_tasks", queued_tasks, "count")
            self._record_metric("parallel.processing_time", avg_processing_time, "seconds")
            self._record_metric("parallel.throughput", throughput, "per_second")
            
            # エラー率計算
            total_tasks = completed_tasks + failed_tasks
            error_rate = failed_tasks / total_tasks if total_tasks > 0 else 0
            self._record_metric("parallel.error_rate", error_rate, "ratio")
            
        except Exception as e:
            self.logger.error(f"Parallel processing stats recording error: {e}")
    
    def _record_metric(self, metric_type: str, value: float, unit: str, metadata: Dict[str, Any] = None):
        """メトリクス記録"""
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            metric_type=metric_type,
            value=value,
            unit=unit,
            metadata=metadata or {}
        )
        self.performance_metrics.append(metric)
    
    async def _cleanup_old_metrics(self):
        """古いメトリクス削除"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=self.metric_retention_hours)
            
            # パフォーマンスメトリクス削除
            self.performance_metrics = deque([
                m for m in self.performance_metrics 
                if m.timestamp > cutoff_time
            ], maxlen=10000)
            
            # リソーススナップショット削除
            self.resource_snapshots = deque([
                s for s in self.resource_snapshots
                if s.timestamp > cutoff_time
            ], maxlen=1000)
            
            # 並列処理統計削除
            self.parallel_stats = deque([
                s for s in self.parallel_stats
                if s.timestamp > cutoff_time
            ], maxlen=1000)
            
        except Exception as e:
            self.logger.error(f"Metrics cleanup error: {e}")
    
    async def _check_alerts(self):
        """アラートチェック"""
        try:
            if not self.resource_snapshots:
                return
            
            latest_snapshot = self.resource_snapshots[-1]
            
            # CPU使用率アラート
            if latest_snapshot.cpu_percent > self.alert_thresholds["cpu_usage"]:
                await self._trigger_alert(
                    "high_cpu_usage",
                    f"CPU usage {latest_snapshot.cpu_percent:.1f}% exceeds threshold {self.alert_thresholds['cpu_usage']}%",
                    {"cpu_percent": latest_snapshot.cpu_percent}
                )
            
            # メモリ使用率アラート
            if latest_snapshot.memory_percent > self.alert_thresholds["memory_usage"]:
                await self._trigger_alert(
                    "high_memory_usage",
                    f"Memory usage {latest_snapshot.memory_percent:.1f}% exceeds threshold {self.alert_thresholds['memory_usage']}%",
                    {"memory_percent": latest_snapshot.memory_percent}
                )
            
            # 並列処理統計チェック
            if self.parallel_stats:
                latest_parallel_stats = self.parallel_stats[-1]
                
                # キュー長アラート
                if latest_parallel_stats.queued_tasks > self.alert_thresholds["queue_length"]:
                    await self._trigger_alert(
                        "high_queue_length",
                        f"Queue length {latest_parallel_stats.queued_tasks} exceeds threshold {self.alert_thresholds['queue_length']}",
                        {"queued_tasks": latest_parallel_stats.queued_tasks}
                    )
                
                # 処理時間アラート
                if latest_parallel_stats.average_processing_time > self.alert_thresholds["processing_time"]:
                    await self._trigger_alert(
                        "slow_processing",
                        f"Average processing time {latest_parallel_stats.average_processing_time:.2f}s exceeds threshold {self.alert_thresholds['processing_time']}s",
                        {"processing_time": latest_parallel_stats.average_processing_time}
                    )
            
        except Exception as e:
            self.logger.error(f"Alert check error: {e}")
    
    async def _trigger_alert(self, alert_type: str, message: str, data: Dict[str, Any]):
        """アラート発火"""
        alert_info = {
            "type": alert_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        self.logger.warning(f"ALERT: {message}", **data)
        
        # アラートコールバック実行
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert_info)
                else:
                    callback(alert_info)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")
    
    def add_alert_callback(self, callback: Callable):
        """アラートコールバック追加"""
        self.alert_callbacks.append(callback)
    
    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """パフォーマンスサマリー取得"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # 最近のメトリクス取得
            recent_metrics = [m for m in self.performance_metrics if m.timestamp > cutoff_time]
            recent_snapshots = [s for s in self.resource_snapshots if s.timestamp > cutoff_time]
            recent_parallel_stats = [s for s in self.parallel_stats if s.timestamp > cutoff_time]
            
            # CPU統計
            cpu_values = [s.cpu_percent for s in recent_snapshots]
            cpu_stats = self._calculate_stats(cpu_values, "CPU Usage (%)")
            
            # メモリ統計
            memory_values = [s.memory_percent for s in recent_snapshots]
            memory_stats = self._calculate_stats(memory_values, "Memory Usage (%)")
            
            # 並列処理統計
            processing_times = [s.average_processing_time for s in recent_parallel_stats]
            processing_stats = self._calculate_stats(processing_times, "Processing Time (s)")
            
            throughput_values = [s.throughput_per_second for s in recent_parallel_stats]
            throughput_stats = self._calculate_stats(throughput_values, "Throughput (per sec)")
            
            return {
                "summary_period_hours": hours,
                "data_points": len(recent_snapshots),
                "system_resources": {
                    "cpu": cpu_stats,
                    "memory": memory_stats
                },
                "parallel_processing": {
                    "processing_time": processing_stats,
                    "throughput": throughput_stats
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Performance summary generation error: {e}")
            return {}
    
    def _calculate_stats(self, values: List[float], name: str) -> Dict[str, Any]:
        """統計計算"""
        if not values:
            return {"name": name, "count": 0}
        
        return {
            "name": name,
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "average": sum(values) / len(values),
            "median": sorted(values)[len(values) // 2]
        }
    
    def get_current_status(self) -> Dict[str, Any]:
        """現在のステータス取得"""
        try:
            latest_snapshot = self.resource_snapshots[-1] if self.resource_snapshots else None
            latest_parallel_stats = self.parallel_stats[-1] if self.parallel_stats else None
            
            status = {
                "monitoring_active": self.is_monitoring,
                "last_update": latest_snapshot.timestamp.isoformat() if latest_snapshot else None,
                "system_resources": asdict(latest_snapshot) if latest_snapshot else None,
                "parallel_processing": asdict(latest_parallel_stats) if latest_parallel_stats else None,
                "alert_thresholds": self.alert_thresholds,
                "metrics_count": len(self.performance_metrics)
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Current status error: {e}")
            return {"error": str(e)}
    
    async def generate_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """パフォーマンスレポート生成"""
        try:
            summary = self.get_performance_summary(hours)
            
            # トレンド分析
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            recent_snapshots = [s for s in self.resource_snapshots if s.timestamp > cutoff_time]
            
            # パフォーマンストレンド
            trends = self._analyze_trends(recent_snapshots)
            
            # 推奨事項生成
            recommendations = self._generate_recommendations(summary, trends)
            
            report = {
                "report_period": f"{hours} hours",
                "generated_at": datetime.utcnow().isoformat(),
                "summary": summary,
                "trends": trends,
                "recommendations": recommendations,
                "system_health_score": self._calculate_health_score(summary)
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Performance report generation error: {e}")
            return {"error": str(e)}
    
    def _analyze_trends(self, snapshots: List[SystemResourceSnapshot]) -> Dict[str, str]:
        """トレンド分析"""
        if len(snapshots) < 2:
            return {"status": "insufficient_data"}
        
        # CPU使用率トレンド
        cpu_values = [s.cpu_percent for s in snapshots]
        cpu_trend = "increasing" if cpu_values[-1] > cpu_values[0] else "decreasing"
        
        # メモリ使用率トレンド
        memory_values = [s.memory_percent for s in snapshots]
        memory_trend = "increasing" if memory_values[-1] > memory_values[0] else "decreasing"
        
        return {
            "cpu_trend": cpu_trend,
            "memory_trend": memory_trend,
            "data_points": len(snapshots)
        }
    
    def _generate_recommendations(self, summary: Dict[str, Any], trends: Dict[str, str]) -> List[str]:
        """推奨事項生成"""
        recommendations = []
        
        try:
            # CPU使用率チェック
            if summary.get("system_resources", {}).get("cpu", {}).get("average", 0) > 70:
                recommendations.append("CPU使用率が高いため、並列度を調整することを検討してください")
            
            # メモリ使用率チェック
            if summary.get("system_resources", {}).get("memory", {}).get("average", 0) > 80:
                recommendations.append("メモリ使用率が高いため、キャッシュサイズの最適化を検討してください")
            
            # 処理時間チェック
            if summary.get("parallel_processing", {}).get("processing_time", {}).get("average", 0) > 20:
                recommendations.append("処理時間が長いため、バッチサイズの最適化を検討してください")
            
            # トレンドベースの推奨
            if trends.get("cpu_trend") == "increasing":
                recommendations.append("CPU使用率が増加傾向にあります。リソース監視を強化してください")
            
            if not recommendations:
                recommendations.append("システムは良好に動作しています")
                
        except Exception as e:
            recommendations.append(f"推奨事項生成エラー: {e}")
        
        return recommendations
    
    def _calculate_health_score(self, summary: Dict[str, Any]) -> float:
        """システムヘルススコア計算"""
        try:
            score = 100.0
            
            # CPU使用率影響
            cpu_avg = summary.get("system_resources", {}).get("cpu", {}).get("average", 0)
            if cpu_avg > 80:
                score -= 20
            elif cpu_avg > 60:
                score -= 10
            
            # メモリ使用率影響
            memory_avg = summary.get("system_resources", {}).get("memory", {}).get("average", 0)
            if memory_avg > 85:
                score -= 20
            elif memory_avg > 70:
                score -= 10
            
            # 処理時間影響
            processing_avg = summary.get("parallel_processing", {}).get("processing_time", {}).get("average", 0)
            if processing_avg > 30:
                score -= 15
            elif processing_avg > 20:
                score -= 5
            
            return max(score, 0.0)
            
        except Exception:
            return 50.0  # デフォルトスコア