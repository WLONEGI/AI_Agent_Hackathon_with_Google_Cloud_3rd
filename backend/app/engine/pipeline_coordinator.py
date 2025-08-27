"""PipelineCoordinator - パイプライン統合コーディネーター

設計書要件:
- 7フェーズ統合処理の調整・監視
- 非同期処理パイプライン管理
- エラーハンドリング・リトライ制御
- パフォーマンス最適化・リソース管理
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, AsyncGenerator, Set
from uuid import UUID
from enum import Enum
from dataclasses import dataclass
import json
from collections import defaultdict
import time

from app.core.logging import LoggerMixin
from app.core.config.settings import get_settings
from .manga_generation_engine import MangaGenerationEngine
from .hitl_manager import HITLManager
from .preview_system import PreviewSystem
from .quality_gate import QualityGateSystem
from .version_manager import VersionManager
from .websocket_manager import WebSocketManager


class CoordinatorStatus(Enum):
    """Coordinator status enumeration."""
    IDLE = "idle"
    ACTIVE = "active"
    OVERLOADED = "overloaded"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class ResourceStatus(Enum):
    """Resource status enumeration."""
    AVAILABLE = "available"
    BUSY = "busy"
    CRITICAL = "critical"
    UNAVAILABLE = "unavailable"


@dataclass
class SystemMetrics:
    """System performance metrics."""
    cpu_usage: float
    memory_usage: float
    active_sessions: int
    queue_size: int
    throughput_per_minute: float
    error_rate: float
    average_response_time: float
    quality_score_average: float
    timestamp: datetime


@dataclass
class ResourcePool:
    """Resource pool management."""
    max_concurrent_sessions: int
    current_sessions: int
    max_phase_workers: int
    current_workers: int
    max_memory_mb: int
    current_memory_mb: int
    max_cpu_percent: float
    current_cpu_percent: float


class PipelineCoordinator(LoggerMixin):
    """パイプライン統合コーディネーター
    
    7フェーズエンジンシステム全体の調整・監視・最適化を担当。
    リソース管理・パフォーマンス最適化・エラーハンドリングを統合。
    """
    
    def __init__(
        self,
        manga_engine: MangaGenerationEngine,
        hitl_manager: HITLManager,
        preview_system: PreviewSystem,
        quality_gate: QualityGateSystem,
        version_manager: VersionManager,
        websocket_manager: WebSocketManager
    ):
        """Initialize PipelineCoordinator.
        
        Args:
            manga_engine: 漫画生成エンジン
            hitl_manager: HITLマネージャー
            preview_system: プレビューシステム
            quality_gate: 品質ゲートシステム
            version_manager: バージョンマネージャー
            websocket_manager: WebSocketマネージャー
        """
        super().__init__()
        self.settings = get_settings()
        
        # Core system components
        self.manga_engine = manga_engine
        self.hitl_manager = hitl_manager
        self.preview_system = preview_system
        self.quality_gate = quality_gate
        self.version_manager = version_manager
        self.websocket_manager = websocket_manager
        
        # Coordinator state
        self.status = CoordinatorStatus.IDLE
        self.startup_time = datetime.utcnow()
        
        # Resource management
        self.resource_pool = ResourcePool(
            max_concurrent_sessions=50,
            current_sessions=0,
            max_phase_workers=20,
            current_workers=0,
            max_memory_mb=8192,
            current_memory_mb=0,
            max_cpu_percent=80.0,
            current_cpu_percent=0.0
        )
        
        # Performance tracking
        self.metrics_history: List[SystemMetrics] = []
        self.performance_targets = {
            "max_response_time": 97.0,  # seconds
            "min_throughput_per_minute": 5.0,
            "max_error_rate": 0.05,  # 5%
            "min_quality_score": 0.70,
            "max_concurrent_sessions": 50
        }
        
        # Session management
        self.active_sessions: Dict[UUID, Dict[str, Any]] = {}
        self.session_queue: asyncio.Queue = asyncio.Queue()
        self.priority_queue: asyncio.Queue = asyncio.Queue()
        
        # Background tasks
        self.background_tasks: List[asyncio.Task] = []
        self.monitoring_enabled = True
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "completed_requests": 0,
            "failed_requests": 0,
            "queue_overflows": 0,
            "resource_throttles": 0,
            "system_recoveries": 0,
            "uptime_seconds": 0,
            "peak_concurrent_sessions": 0,
            "total_processing_time": 0.0
        }
        
        # Error tracking
        self.error_tracking: Dict[str, List[datetime]] = defaultdict(list)
        self.circuit_breakers: Dict[str, bool] = {}
    
    async def initialize(self):
        """Initialize coordinator and start background tasks."""
        try:
            self.logger.info("Initializing PipelineCoordinator...")
            
            # Start background monitoring
            self.background_tasks.append(
                asyncio.create_task(self._system_monitor_loop())
            )
            
            # Start session processor
            self.background_tasks.append(
                asyncio.create_task(self._session_processor())
            )
            
            # Start resource monitor
            self.background_tasks.append(
                asyncio.create_task(self._resource_monitor())
            )
            
            # Start metrics collector
            self.background_tasks.append(
                asyncio.create_task(self._metrics_collector())
            )
            
            # Start health checker
            self.background_tasks.append(
                asyncio.create_task(self._health_checker())
            )
            
            self.status = CoordinatorStatus.ACTIVE
            self.logger.info("PipelineCoordinator initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize coordinator: {e}")
            self.status = CoordinatorStatus.ERROR
            raise
    
    async def shutdown(self):
        """Gracefully shutdown coordinator."""
        self.logger.info("Shutting down PipelineCoordinator...")
        
        self.monitoring_enabled = False
        self.status = CoordinatorStatus.MAINTENANCE
        
        # Cancel background tasks
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # Complete active sessions
        for session_id in list(self.active_sessions.keys()):
            await self._cleanup_session(session_id, "System shutdown")
        
        self.logger.info("PipelineCoordinator shutdown completed")
    
    async def submit_generation_request(
        self,
        user_input: str,
        user_id: UUID,
        session_id: Optional[UUID] = None,
        priority: int = 5,
        quality_level: str = "high",
        enable_hitl: bool = True,
        options: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Submit manga generation request.
        
        Args:
            user_input: ユーザー入力
            user_id: ユーザーID
            session_id: セッションID
            priority: 優先度 (1-10, higher = more priority)
            quality_level: 品質レベル
            enable_hitl: HITL有効化
            options: 追加オプション
            
        Yields:
            リアルタイム進捗更新
        """
        try:
            # Resource availability check
            if not await self._check_resource_availability():
                yield {
                    "type": "resource_unavailable",
                    "message": "System is currently overloaded. Please try again later.",
                    "retry_after": 60,
                    "timestamp": datetime.utcnow().isoformat()
                }
                return
            
            # Update statistics
            self.stats["total_requests"] += 1
            
            # Create session tracking
            session_data = {
                "user_input": user_input,
                "user_id": user_id,
                "session_id": session_id,
                "priority": priority,
                "quality_level": quality_level,
                "enable_hitl": enable_hitl,
                "options": options or {},
                "submitted_at": datetime.utcnow(),
                "status": "queued"
            }
            
            if session_id:
                self.active_sessions[session_id] = session_data
            
            # Queue the request
            if priority >= 8:  # High priority
                await self.priority_queue.put(session_data)
            else:
                await self.session_queue.put(session_data)
            
            yield {
                "type": "request_queued",
                "session_id": str(session_id) if session_id else None,
                "queue_position": self.session_queue.qsize() + self.priority_queue.qsize(),
                "estimated_wait_time": self._estimate_wait_time(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to submit generation request: {e}")
            self.stats["failed_requests"] += 1
            
            yield {
                "type": "submission_error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _session_processor(self):
        """Background session processor."""
        self.logger.info("Session processor started")
        
        while self.monitoring_enabled:
            try:
                # Process priority queue first
                session_data = None
                
                try:
                    session_data = await asyncio.wait_for(
                        self.priority_queue.get(), timeout=0.1
                    )
                except asyncio.TimeoutError:
                    try:
                        session_data = await asyncio.wait_for(
                            self.session_queue.get(), timeout=1.0
                        )
                    except asyncio.TimeoutError:
                        continue
                
                # Process the session
                if session_data:
                    await self._process_session(session_data)
                
            except Exception as e:
                self.logger.error(f"Session processor error: {e}")
                await asyncio.sleep(1)
    
    async def _process_session(self, session_data: Dict[str, Any]):
        """Process individual session."""
        session_id = session_data.get("session_id")
        start_time = time.time()
        
        try:
            # Update resource usage
            self.resource_pool.current_sessions += 1
            self.stats["peak_concurrent_sessions"] = max(
                self.stats["peak_concurrent_sessions"],
                self.resource_pool.current_sessions
            )
            
            # Update session status
            if session_id:
                session_data["status"] = "processing"
                session_data["started_at"] = datetime.utcnow()
            
            # Create generation stream
            generation_stream = self.manga_engine.generate_manga(
                user_input=session_data["user_input"],
                user_id=session_data["user_id"],
                session_id=session_id,
                quality_level=session_data["quality_level"],
                enable_hitl=session_data["enable_hitl"]
            )
            
            # Process generation updates
            async for update in generation_stream:
                # Forward to WebSocket clients
                if session_id:
                    await self.websocket_manager.send_to_session(session_id, update)
                
                # Handle completion
                if update.get("type") == "pipeline_completed":
                    processing_time = time.time() - start_time
                    self.stats["completed_requests"] += 1
                    self.stats["total_processing_time"] += processing_time
                    
                    if session_id:
                        session_data["status"] = "completed"
                        session_data["completed_at"] = datetime.utcnow()
                        session_data["processing_time"] = processing_time
                    
                    self.logger.info(
                        f"Session {session_id} completed in {processing_time:.2f}s"
                    )
                
                # Handle errors
                elif update.get("type") == "error":
                    self.stats["failed_requests"] += 1
                    if session_id:
                        session_data["status"] = "failed"
                        session_data["error"] = update.get("error")
                    
                    await self._track_error(update.get("error", "Unknown error"))
            
        except Exception as e:
            self.logger.error(f"Session processing failed: {e}")
            self.stats["failed_requests"] += 1
            
            if session_id:
                session_data["status"] = "failed"
                session_data["error"] = str(e)
                
                # Send error to WebSocket
                await self.websocket_manager.send_to_session(session_id, {
                    "type": "processing_error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            await self._track_error(str(e))
        
        finally:
            # Update resource usage
            self.resource_pool.current_sessions -= 1
            
            # Cleanup session
            if session_id:
                await self._cleanup_session(session_id)
    
    async def _system_monitor_loop(self):
        """Background system monitoring loop."""
        self.logger.info("System monitor started")
        
        while self.monitoring_enabled:
            try:
                # Collect system metrics
                metrics = await self._collect_system_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only last 1000 metrics (about 16 hours at 1-minute intervals)
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]
                
                # Check performance targets
                await self._check_performance_targets(metrics)
                
                # Adjust system behavior
                await self._adjust_system_behavior(metrics)
                
                # Update uptime
                self.stats["uptime_seconds"] = (
                    datetime.utcnow() - self.startup_time
                ).total_seconds()
                
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                self.logger.error(f"System monitor error: {e}")
                await asyncio.sleep(30)
    
    async def _resource_monitor(self):
        """Monitor and manage system resources."""
        self.logger.info("Resource monitor started")
        
        while self.monitoring_enabled:
            try:
                # Update resource usage
                await self._update_resource_usage()
                
                # Check resource limits
                resource_status = self._check_resource_limits()
                
                if resource_status == ResourceStatus.CRITICAL:
                    self.logger.warning("System resources critical")
                    await self._handle_resource_pressure()
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Resource monitor error: {e}")
                await asyncio.sleep(30)
    
    async def _metrics_collector(self):
        """Collect and aggregate performance metrics."""
        self.logger.info("Metrics collector started")
        
        while self.monitoring_enabled:
            try:
                # Collect component metrics
                engine_metrics = self.manga_engine.get_engine_metrics()
                hitl_metrics = self.hitl_manager.get_feedback_metrics()
                preview_metrics = self.preview_system.get_preview_stats()
                quality_metrics = self.quality_gate.get_quality_stats()
                version_metrics = self.version_manager.get_version_stats()
                websocket_metrics = self.websocket_manager.get_manager_stats()
                
                # Aggregate metrics
                aggregated_metrics = {
                    "coordinator": self.stats,
                    "engine": engine_metrics,
                    "hitl": hitl_metrics,
                    "preview": preview_metrics,
                    "quality": quality_metrics,
                    "version": version_metrics,
                    "websocket": websocket_metrics,
                    "collected_at": datetime.utcnow().isoformat()
                }
                
                # Store metrics (could be sent to monitoring system)
                await self._store_metrics(aggregated_metrics)
                
                await asyncio.sleep(300)  # Collect every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Metrics collector error: {e}")
                await asyncio.sleep(60)
    
    async def _health_checker(self):
        """System health checker."""
        self.logger.info("Health checker started")
        
        while self.monitoring_enabled:
            try:
                # Check component health
                health_status = await self._check_system_health()
                
                # Update coordinator status based on health
                if health_status["overall"] == "healthy":
                    if self.status != CoordinatorStatus.ACTIVE:
                        self.status = CoordinatorStatus.ACTIVE
                        self.logger.info("System health restored")
                
                elif health_status["overall"] == "degraded":
                    if self.status == CoordinatorStatus.ACTIVE:
                        self.status = CoordinatorStatus.OVERLOADED
                        self.logger.warning("System performance degraded")
                
                elif health_status["overall"] == "unhealthy":
                    if self.status != CoordinatorStatus.ERROR:
                        self.status = CoordinatorStatus.ERROR
                        self.logger.error("System health critical")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Health checker error: {e}")
                await asyncio.sleep(60)
    
    async def _check_resource_availability(self) -> bool:
        """Check if resources are available for new request."""
        if self.status == CoordinatorStatus.ERROR:
            return False
        
        if self.resource_pool.current_sessions >= self.resource_pool.max_concurrent_sessions:
            self.stats["queue_overflows"] += 1
            return False
        
        if self.resource_pool.current_cpu_percent > 90.0:
            self.stats["resource_throttles"] += 1
            return False
        
        if self.resource_pool.current_memory_mb > self.resource_pool.max_memory_mb * 0.9:
            self.stats["resource_throttles"] += 1
            return False
        
        return True
    
    def _estimate_wait_time(self) -> int:
        """Estimate wait time in seconds."""
        queue_size = self.session_queue.qsize() + self.priority_queue.qsize()
        
        if queue_size == 0:
            return 0
        
        # Use average processing time from stats
        if self.stats["completed_requests"] > 0:
            avg_time = self.stats["total_processing_time"] / self.stats["completed_requests"]
        else:
            avg_time = self.performance_targets["max_response_time"]
        
        # Account for concurrent processing
        concurrent_factor = max(1, self.resource_pool.max_concurrent_sessions / 4)
        estimated_time = (queue_size / concurrent_factor) * avg_time
        
        return int(estimated_time)
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        # Calculate throughput
        if len(self.metrics_history) >= 2:
            prev_metrics = self.metrics_history[-1]
            time_diff = (datetime.utcnow() - prev_metrics.timestamp).total_seconds() / 60.0
            request_diff = self.stats["completed_requests"]
            throughput = request_diff / time_diff if time_diff > 0 else 0.0
        else:
            throughput = 0.0
        
        # Calculate error rate
        total_requests = self.stats["total_requests"]
        error_rate = (
            self.stats["failed_requests"] / total_requests 
            if total_requests > 0 else 0.0
        )
        
        # Calculate average response time
        if self.stats["completed_requests"] > 0:
            avg_response_time = (
                self.stats["total_processing_time"] / self.stats["completed_requests"]
            )
        else:
            avg_response_time = 0.0
        
        # Get quality score average (placeholder)
        quality_score_average = 0.75  # Would be calculated from actual quality scores
        
        return SystemMetrics(
            cpu_usage=self.resource_pool.current_cpu_percent,
            memory_usage=self.resource_pool.current_memory_mb,
            active_sessions=self.resource_pool.current_sessions,
            queue_size=self.session_queue.qsize() + self.priority_queue.qsize(),
            throughput_per_minute=throughput,
            error_rate=error_rate,
            average_response_time=avg_response_time,
            quality_score_average=quality_score_average,
            timestamp=datetime.utcnow()
        )
    
    async def _check_performance_targets(self, metrics: SystemMetrics):
        """Check if performance targets are being met."""
        issues = []
        
        if metrics.average_response_time > self.performance_targets["max_response_time"]:
            issues.append(f"Response time {metrics.average_response_time:.1f}s exceeds target")
        
        if metrics.throughput_per_minute < self.performance_targets["min_throughput_per_minute"]:
            issues.append(f"Throughput {metrics.throughput_per_minute:.1f}/min below target")
        
        if metrics.error_rate > self.performance_targets["max_error_rate"]:
            issues.append(f"Error rate {metrics.error_rate:.1%} exceeds target")
        
        if metrics.quality_score_average < self.performance_targets["min_quality_score"]:
            issues.append(f"Quality score {metrics.quality_score_average:.2f} below target")
        
        if issues:
            self.logger.warning(f"Performance issues: {'; '.join(issues)}")
    
    async def _adjust_system_behavior(self, metrics: SystemMetrics):
        """Adjust system behavior based on metrics."""
        
        # Reduce concurrent sessions if overloaded
        if metrics.cpu_usage > 85.0 or metrics.memory_usage > self.resource_pool.max_memory_mb * 0.85:
            new_max = max(10, int(self.resource_pool.max_concurrent_sessions * 0.8))
            if new_max != self.resource_pool.max_concurrent_sessions:
                self.resource_pool.max_concurrent_sessions = new_max
                self.logger.info(f"Reduced max concurrent sessions to {new_max}")
        
        # Increase concurrent sessions if resources available
        elif metrics.cpu_usage < 50.0 and metrics.memory_usage < self.resource_pool.max_memory_mb * 0.5:
            new_max = min(50, int(self.resource_pool.max_concurrent_sessions * 1.2))
            if new_max != self.resource_pool.max_concurrent_sessions:
                self.resource_pool.max_concurrent_sessions = new_max
                self.logger.info(f"Increased max concurrent sessions to {new_max}")
    
    async def _update_resource_usage(self):
        """Update current resource usage metrics."""
        # In a real implementation, these would be actual system metrics
        # For now, we'll simulate based on active sessions
        
        base_cpu = 20.0
        base_memory = 1024
        
        session_factor = self.resource_pool.current_sessions / self.resource_pool.max_concurrent_sessions
        
        self.resource_pool.current_cpu_percent = base_cpu + (session_factor * 60.0)
        self.resource_pool.current_memory_mb = base_memory + (session_factor * 6000)
    
    def _check_resource_limits(self) -> ResourceStatus:
        """Check current resource status."""
        cpu_ratio = self.resource_pool.current_cpu_percent / 100.0
        memory_ratio = self.resource_pool.current_memory_mb / self.resource_pool.max_memory_mb
        session_ratio = self.resource_pool.current_sessions / self.resource_pool.max_concurrent_sessions
        
        max_ratio = max(cpu_ratio, memory_ratio, session_ratio)
        
        if max_ratio >= 0.95:
            return ResourceStatus.CRITICAL
        elif max_ratio >= 0.80:
            return ResourceStatus.BUSY
        else:
            return ResourceStatus.AVAILABLE
    
    async def _handle_resource_pressure(self):
        """Handle resource pressure situation."""
        self.logger.warning("Handling resource pressure")
        
        # Pause new session processing temporarily
        original_max = self.resource_pool.max_concurrent_sessions
        self.resource_pool.max_concurrent_sessions = max(1, self.resource_pool.current_sessions)
        
        # Wait for some sessions to complete
        await asyncio.sleep(30)
        
        # Restore capacity gradually
        self.resource_pool.max_concurrent_sessions = min(original_max, self.resource_pool.current_sessions + 5)
        
        self.stats["system_recoveries"] += 1
    
    async def _check_system_health(self) -> Dict[str, str]:
        """Check overall system health."""
        health_checks = {
            "coordinator": "healthy",
            "engine": "healthy",
            "hitl": "healthy",
            "preview": "healthy",
            "quality": "healthy",
            "version": "healthy",
            "websocket": "healthy"
        }
        
        # Check error rates
        if len(self.metrics_history) > 0:
            latest_metrics = self.metrics_history[-1]
            
            if latest_metrics.error_rate > 0.1:  # 10% error rate
                health_checks["engine"] = "unhealthy"
            elif latest_metrics.error_rate > 0.05:  # 5% error rate
                health_checks["engine"] = "degraded"
            
            if latest_metrics.cpu_usage > 90.0:
                health_checks["coordinator"] = "unhealthy"
            elif latest_metrics.cpu_usage > 80.0:
                health_checks["coordinator"] = "degraded"
        
        # Determine overall health
        unhealthy_count = sum(1 for status in health_checks.values() if status == "unhealthy")
        degraded_count = sum(1 for status in health_checks.values() if status == "degraded")
        
        if unhealthy_count > 0:
            health_checks["overall"] = "unhealthy"
        elif degraded_count > 2:
            health_checks["overall"] = "unhealthy"
        elif degraded_count > 0:
            health_checks["overall"] = "degraded"
        else:
            health_checks["overall"] = "healthy"
        
        return health_checks
    
    async def _track_error(self, error_message: str):
        """Track error for circuit breaker logic."""
        now = datetime.utcnow()
        error_key = error_message[:50]  # Use first 50 chars as key
        
        # Add to error history
        self.error_tracking[error_key].append(now)
        
        # Keep only last hour of errors
        hour_ago = now - timedelta(hours=1)
        self.error_tracking[error_key] = [
            timestamp for timestamp in self.error_tracking[error_key]
            if timestamp > hour_ago
        ]
        
        # Check if circuit breaker should be triggered
        if len(self.error_tracking[error_key]) > 10:  # More than 10 errors in an hour
            self.circuit_breakers[error_key] = True
            self.logger.error(f"Circuit breaker activated for: {error_key}")
    
    async def _store_metrics(self, metrics: Dict[str, Any]):
        """Store metrics for monitoring system."""
        # In a real implementation, this would send to monitoring system
        # For now, we'll just log important metrics
        
        coordinator_stats = metrics.get("coordinator", {})
        engine_stats = metrics.get("engine", {})
        
        self.logger.info(
            f"System Metrics - "
            f"Active Sessions: {coordinator_stats.get('peak_concurrent_sessions', 0)}, "
            f"Completed: {coordinator_stats.get('completed_requests', 0)}, "
            f"Failed: {coordinator_stats.get('failed_requests', 0)}, "
            f"Engine Success Rate: {engine_stats.get('success_rate', 0):.1f}%"
        )
    
    async def _cleanup_session(self, session_id: UUID, reason: str = "Completed"):
        """Clean up session resources."""
        if session_id in self.active_sessions:
            session_data = self.active_sessions[session_id]
            session_data["cleanup_reason"] = reason
            session_data["cleaned_up_at"] = datetime.utcnow()
            
            # Keep for a short time for debugging
            await asyncio.sleep(60)
            del self.active_sessions[session_id]
    
    def get_coordinator_status(self) -> Dict[str, Any]:
        """Get coordinator status and metrics."""
        uptime = (datetime.utcnow() - self.startup_time).total_seconds()
        
        return {
            "status": self.status.value,
            "uptime_seconds": uptime,
            "resource_pool": {
                "max_concurrent_sessions": self.resource_pool.max_concurrent_sessions,
                "current_sessions": self.resource_pool.current_sessions,
                "cpu_usage": self.resource_pool.current_cpu_percent,
                "memory_usage_mb": self.resource_pool.current_memory_mb,
                "memory_limit_mb": self.resource_pool.max_memory_mb
            },
            "queue_status": {
                "regular_queue": self.session_queue.qsize(),
                "priority_queue": self.priority_queue.qsize(),
                "total_queue": self.session_queue.qsize() + self.priority_queue.qsize()
            },
            "performance": {
                "total_requests": self.stats["total_requests"],
                "completed_requests": self.stats["completed_requests"],
                "failed_requests": self.stats["failed_requests"],
                "success_rate": (
                    self.stats["completed_requests"] / max(self.stats["total_requests"], 1) * 100
                ),
                "average_processing_time": (
                    self.stats["total_processing_time"] / max(self.stats["completed_requests"], 1)
                ),
                "peak_concurrent_sessions": self.stats["peak_concurrent_sessions"]
            },
            "error_tracking": {
                "active_circuit_breakers": len([k for k, v in self.circuit_breakers.items() if v]),
                "recent_error_types": len(self.error_tracking),
                "queue_overflows": self.stats["queue_overflows"],
                "resource_throttles": self.stats["resource_throttles"],
                "system_recoveries": self.stats["system_recoveries"]
            },
            "background_tasks": {
                "total_tasks": len(self.background_tasks),
                "running_tasks": sum(1 for task in self.background_tasks if not task.done()),
                "monitoring_enabled": self.monitoring_enabled
            }
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get detailed performance report."""
        if not self.metrics_history:
            return {"message": "No metrics available"}
        
        recent_metrics = self.metrics_history[-min(60, len(self.metrics_history)):]  # Last hour
        
        # Calculate averages
        avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
        avg_response_time = sum(m.average_response_time for m in recent_metrics) / len(recent_metrics)
        avg_throughput = sum(m.throughput_per_minute for m in recent_metrics) / len(recent_metrics)
        avg_error_rate = sum(m.error_rate for m in recent_metrics) / len(recent_metrics)
        avg_quality = sum(m.quality_score_average for m in recent_metrics) / len(recent_metrics)
        
        # Performance vs targets
        target_compliance = {
            "response_time": avg_response_time <= self.performance_targets["max_response_time"],
            "throughput": avg_throughput >= self.performance_targets["min_throughput_per_minute"],
            "error_rate": avg_error_rate <= self.performance_targets["max_error_rate"],
            "quality_score": avg_quality >= self.performance_targets["min_quality_score"]
        }
        
        compliance_rate = sum(target_compliance.values()) / len(target_compliance) * 100
        
        return {
            "report_period": "last_hour",
            "metrics_count": len(recent_metrics),
            "averages": {
                "cpu_usage": avg_cpu,
                "memory_usage_mb": avg_memory,
                "response_time_seconds": avg_response_time,
                "throughput_per_minute": avg_throughput,
                "error_rate": avg_error_rate,
                "quality_score": avg_quality
            },
            "performance_targets": self.performance_targets,
            "target_compliance": target_compliance,
            "overall_compliance_rate": compliance_rate,
            "performance_grade": (
                "A" if compliance_rate >= 90 else
                "B" if compliance_rate >= 75 else
                "C" if compliance_rate >= 60 else
                "D"
            ),
            "generated_at": datetime.utcnow().isoformat()
        }