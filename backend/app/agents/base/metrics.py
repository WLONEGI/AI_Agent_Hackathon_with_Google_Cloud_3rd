"""Agent metrics collection and reporting."""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
import asyncio

from app.core.logging import LoggerMixin


@dataclass
class ExecutionMetric:
    """Individual execution metric."""
    timestamp: datetime
    execution_time: float
    success: bool
    error_message: Optional[str] = None
    quality_score: Optional[float] = None


@dataclass
class MetricsSummary:
    """Summary of agent metrics."""
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    average_execution_time: float
    min_execution_time: float
    max_execution_time: float
    average_quality_score: Optional[float]
    last_24h_executions: int
    trend: str  # "improving", "stable", "degrading"


class AgentMetrics(LoggerMixin):
    """Manages metrics collection and analysis for agents."""
    
    def __init__(
        self,
        phase_number: int,
        phase_name: str,
        max_history: int = 1000
    ):
        """Initialize metrics collector.
        
        Args:
            phase_number: Phase number
            phase_name: Phase name
            max_history: Maximum number of metrics to retain
        """
        super().__init__()
        
        self.phase_number = phase_number
        self.phase_name = phase_name
        self.max_history = max_history
        
        # Metrics storage
        self.executions: deque = deque(maxlen=max_history)
        self.quality_scores: deque = deque(maxlen=max_history)
        
        # Counters
        self.total_processed = 0
        self.total_failures = 0
        self.total_execution_time = 0.0
        
        # Performance thresholds
        self.performance_thresholds = {
            "execution_time_warning": 30.0,  # seconds
            "execution_time_critical": 60.0,  # seconds
            "success_rate_warning": 0.8,     # 80%
            "success_rate_critical": 0.6,    # 60%
            "quality_score_warning": 0.7,    # 70%
            "quality_score_critical": 0.5    # 50%
        }
        
        self.logger.debug(
            f"AgentMetrics initialized for {phase_name}",
            phase_number=phase_number,
            max_history=max_history
        )
    
    async def record_success(
        self,
        execution_time: float,
        quality_score: Optional[float] = None
    ) -> None:
        """Record successful execution.
        
        Args:
            execution_time: Execution time in seconds
            quality_score: Optional quality score (0.0 to 1.0)
        """
        metric = ExecutionMetric(
            timestamp=datetime.utcnow(),
            execution_time=execution_time,
            success=True,
            quality_score=quality_score
        )
        
        self.executions.append(metric)
        
        if quality_score is not None:
            self.quality_scores.append(quality_score)
        
        # Update counters
        self.total_processed += 1
        self.total_execution_time += execution_time
        
        # Check thresholds
        await self._check_performance_thresholds(metric)
        
        self.logger.debug(
            f"Recorded success for {self.phase_name}",
            execution_time=execution_time,
            quality_score=quality_score
        )
    
    async def record_failure(
        self,
        execution_time: float,
        error_message: str
    ) -> None:
        """Record failed execution.
        
        Args:
            execution_time: Execution time before failure
            error_message: Error message
        """
        metric = ExecutionMetric(
            timestamp=datetime.utcnow(),
            execution_time=execution_time,
            success=False,
            error_message=error_message
        )
        
        self.executions.append(metric)
        
        # Update counters
        self.total_processed += 1
        self.total_failures += 1
        self.total_execution_time += execution_time
        
        # Check thresholds
        await self._check_performance_thresholds(metric)
        
        self.logger.warning(
            f"Recorded failure for {self.phase_name}",
            execution_time=execution_time,
            error_message=error_message
        )
    
    async def get_summary(
        self,
        time_window: Optional[timedelta] = None
    ) -> MetricsSummary:
        """Get metrics summary.
        
        Args:
            time_window: Optional time window for filtering metrics
            
        Returns:
            MetricsSummary with aggregated metrics
        """
        if time_window:
            cutoff_time = datetime.utcnow() - time_window
            relevant_executions = [
                e for e in self.executions 
                if e.timestamp >= cutoff_time
            ]
        else:
            relevant_executions = list(self.executions)
        
        if not relevant_executions:
            return MetricsSummary(
                total_executions=0,
                successful_executions=0,
                failed_executions=0,
                success_rate=0.0,
                average_execution_time=0.0,
                min_execution_time=0.0,
                max_execution_time=0.0,
                average_quality_score=None,
                last_24h_executions=0,
                trend="stable"
            )
        
        # Calculate basic metrics
        total_executions = len(relevant_executions)
        successful_executions = sum(1 for e in relevant_executions if e.success)
        failed_executions = total_executions - successful_executions
        success_rate = successful_executions / total_executions if total_executions > 0 else 0.0
        
        # Execution times
        execution_times = [e.execution_time for e in relevant_executions]
        average_execution_time = sum(execution_times) / len(execution_times)
        min_execution_time = min(execution_times)
        max_execution_time = max(execution_times)
        
        # Quality scores
        quality_scores = [
            e.quality_score for e in relevant_executions 
            if e.quality_score is not None
        ]
        average_quality_score = (
            sum(quality_scores) / len(quality_scores) 
            if quality_scores else None
        )
        
        # Last 24 hours
        last_24h_cutoff = datetime.utcnow() - timedelta(hours=24)
        last_24h_executions = sum(
            1 for e in self.executions 
            if e.timestamp >= last_24h_cutoff
        )
        
        # Trend analysis
        trend = await self._analyze_trend(relevant_executions)
        
        return MetricsSummary(
            total_executions=total_executions,
            successful_executions=successful_executions,
            failed_executions=failed_executions,
            success_rate=success_rate,
            average_execution_time=average_execution_time,
            min_execution_time=min_execution_time,
            max_execution_time=max_execution_time,
            average_quality_score=average_quality_score,
            last_24h_executions=last_24h_executions,
            trend=trend
        )
    
    async def get_performance_health(self) -> Dict[str, Any]:
        """Get performance health status.
        
        Returns:
            Dictionary with health indicators
        """
        summary = await self.get_summary(timedelta(hours=1))  # Last hour
        
        health = {
            "phase_number": self.phase_number,
            "phase_name": self.phase_name,
            "overall_health": "healthy",
            "issues": [],
            "metrics": {
                "success_rate": summary.success_rate,
                "average_execution_time": summary.average_execution_time,
                "average_quality_score": summary.average_quality_score,
                "total_executions": summary.total_executions
            }
        }
        
        # Check success rate
        if summary.success_rate < self.performance_thresholds["success_rate_critical"]:
            health["overall_health"] = "critical"
            health["issues"].append({
                "type": "success_rate",
                "severity": "critical",
                "message": f"Success rate ({summary.success_rate:.2%}) below critical threshold"
            })
        elif summary.success_rate < self.performance_thresholds["success_rate_warning"]:
            health["overall_health"] = "warning" if health["overall_health"] == "healthy" else health["overall_health"]
            health["issues"].append({
                "type": "success_rate",
                "severity": "warning",
                "message": f"Success rate ({summary.success_rate:.2%}) below warning threshold"
            })
        
        # Check execution time
        if summary.average_execution_time > self.performance_thresholds["execution_time_critical"]:
            health["overall_health"] = "critical"
            health["issues"].append({
                "type": "execution_time",
                "severity": "critical",
                "message": f"Execution time ({summary.average_execution_time:.1f}s) above critical threshold"
            })
        elif summary.average_execution_time > self.performance_thresholds["execution_time_warning"]:
            health["overall_health"] = "warning" if health["overall_health"] == "healthy" else health["overall_health"]
            health["issues"].append({
                "type": "execution_time",
                "severity": "warning",
                "message": f"Execution time ({summary.average_execution_time:.1f}s) above warning threshold"
            })
        
        # Check quality score
        if summary.average_quality_score is not None:
            if summary.average_quality_score < self.performance_thresholds["quality_score_critical"]:
                health["overall_health"] = "critical"
                health["issues"].append({
                    "type": "quality_score",
                    "severity": "critical",
                    "message": f"Quality score ({summary.average_quality_score:.2f}) below critical threshold"
                })
            elif summary.average_quality_score < self.performance_thresholds["quality_score_warning"]:
                health["overall_health"] = "warning" if health["overall_health"] == "healthy" else health["overall_health"]
                health["issues"].append({
                    "type": "quality_score",
                    "severity": "warning",
                    "message": f"Quality score ({summary.average_quality_score:.2f}) below warning threshold"
                })
        
        return health
    
    async def _check_performance_thresholds(self, metric: ExecutionMetric) -> None:
        """Check if metric crosses performance thresholds."""
        
        # Check execution time
        if metric.execution_time > self.performance_thresholds["execution_time_critical"]:
            self.logger.error(
                f"{self.phase_name} execution time critical",
                execution_time=metric.execution_time,
                threshold=self.performance_thresholds["execution_time_critical"]
            )
        elif metric.execution_time > self.performance_thresholds["execution_time_warning"]:
            self.logger.warning(
                f"{self.phase_name} execution time warning",
                execution_time=metric.execution_time,
                threshold=self.performance_thresholds["execution_time_warning"]
            )
        
        # Check quality score
        if metric.quality_score is not None:
            if metric.quality_score < self.performance_thresholds["quality_score_critical"]:
                self.logger.error(
                    f"{self.phase_name} quality score critical",
                    quality_score=metric.quality_score,
                    threshold=self.performance_thresholds["quality_score_critical"]
                )
            elif metric.quality_score < self.performance_thresholds["quality_score_warning"]:
                self.logger.warning(
                    f"{self.phase_name} quality score warning",
                    quality_score=metric.quality_score,
                    threshold=self.performance_thresholds["quality_score_warning"]
                )
    
    async def _analyze_trend(self, executions: List[ExecutionMetric]) -> str:
        """Analyze performance trend.
        
        Args:
            executions: List of execution metrics
            
        Returns:
            Trend description: "improving", "stable", or "degrading"
        """
        if len(executions) < 10:
            return "stable"
        
        # Split into recent and older halves
        mid_point = len(executions) // 2
        older_half = executions[:mid_point]
        recent_half = executions[mid_point:]
        
        # Compare success rates
        older_success_rate = sum(1 for e in older_half if e.success) / len(older_half)
        recent_success_rate = sum(1 for e in recent_half if e.success) / len(recent_half)
        
        success_rate_delta = recent_success_rate - older_success_rate
        
        # Compare execution times (lower is better, so flip the logic)
        older_avg_time = sum(e.execution_time for e in older_half) / len(older_half)
        recent_avg_time = sum(e.execution_time for e in recent_half) / len(recent_half)
        
        time_improvement = older_avg_time - recent_avg_time  # Positive if improving
        
        # Determine trend
        if success_rate_delta > 0.05 or time_improvement > 2.0:
            return "improving"
        elif success_rate_delta < -0.05 or time_improvement < -2.0:
            return "degrading"
        else:
            return "stable"
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.executions.clear()
        self.quality_scores.clear()
        self.total_processed = 0
        self.total_failures = 0
        self.total_execution_time = 0.0
        
        self.logger.info(f"Metrics reset for {self.phase_name}")
    
    def get_raw_data(self) -> Dict[str, Any]:
        """Get raw metrics data for external analysis."""
        return {
            "phase_number": self.phase_number,
            "phase_name": self.phase_name,
            "executions": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "execution_time": e.execution_time,
                    "success": e.success,
                    "error_message": e.error_message,
                    "quality_score": e.quality_score
                }
                for e in self.executions
            ],
            "counters": {
                "total_processed": self.total_processed,
                "total_failures": self.total_failures,
                "total_execution_time": self.total_execution_time
            },
            "thresholds": self.performance_thresholds
        }