"""
Comprehensive Health Monitoring System
Phase 4: Real-time monitoring, alerting, and performance tracking
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.manga_session import MangaSession, MangaSessionStatus
from app.core.db import session_scope
from app.services.circuit_breaker import circuit_breaker_manager
from app.services.state_reconciler import StateReconciler

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """System health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthMetric:
    """Individual health metric data"""
    name: str
    value: float
    status: HealthStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None


@dataclass
class SystemHealthReport:
    """Comprehensive system health report"""
    overall_status: HealthStatus
    score: float  # 0-100, where 100 is perfect health
    metrics: List[HealthMetric]
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)


class HealthMonitor:
    """
    Comprehensive system health monitoring service

    Tracks performance metrics, identifies issues, and provides recommendations
    """

    def __init__(self):
        self.metric_history: Dict[str, List[HealthMetric]] = {}
        self.alert_thresholds = {
            "active_sessions_ratio": {"warning": 0.8, "critical": 0.95},
            "failed_sessions_ratio": {"warning": 0.1, "critical": 0.25},
            "average_processing_time": {"warning": 300, "critical": 600},  # seconds
            "stale_sessions_count": {"warning": 5, "critical": 15},
            "circuit_breakers_open": {"warning": 1, "critical": 3}
        }

    async def get_system_health(self) -> SystemHealthReport:
        """
        Generate comprehensive system health report

        Returns:
            Complete health assessment with metrics and recommendations
        """
        logger.info("🏥 Generating system health report")

        metrics = []
        recommendations = []

        try:
            # Database health metrics
            db_metrics = await self._check_database_health()
            metrics.extend(db_metrics)

            # Session management metrics
            session_metrics = await self._check_session_health()
            metrics.extend(session_metrics)

            # Circuit breaker metrics
            circuit_metrics = await self._check_circuit_breaker_health()
            metrics.extend(circuit_metrics)

            # System performance metrics
            perf_metrics = await self._check_performance_metrics()
            metrics.extend(perf_metrics)

            # State consistency metrics
            consistency_metrics = await self._check_state_consistency()
            metrics.extend(consistency_metrics)

            # Calculate overall health score and status
            overall_status, score = self._calculate_overall_health(metrics)

            # Generate recommendations
            recommendations = self._generate_recommendations(metrics)

            # Store metrics for historical analysis
            await self._store_metric_history(metrics)

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            metrics.append(HealthMetric(
                name="health_check_error",
                value=1,
                status=HealthStatus.CRITICAL,
                message=f"Health monitoring system failure: {e}"
            ))
            overall_status = HealthStatus.CRITICAL
            score = 0
            recommendations = ["Health monitoring system needs immediate attention"]

        report = SystemHealthReport(
            overall_status=overall_status,
            score=score,
            metrics=metrics,
            recommendations=recommendations
        )

        logger.info(f"✅ Health report generated: {overall_status.value} (score: {score:.1f})")
        return report

    async def _check_database_health(self) -> List[HealthMetric]:
        """Check database connectivity and performance"""
        metrics = []

        try:
            start_time = datetime.utcnow()
            async with session_scope() as db_session:
                # Test basic connectivity
                await db_session.execute(select(1))

                # Check response time
                response_time = (datetime.utcnow() - start_time).total_seconds()
                metrics.append(HealthMetric(
                    name="database_response_time",
                    value=response_time,
                    status=HealthStatus.HEALTHY if response_time < 1.0 else HealthStatus.WARNING,
                    message=f"Database response time: {response_time:.3f}s"
                ))

        except Exception as e:
            metrics.append(HealthMetric(
                name="database_connectivity",
                value=0,
                status=HealthStatus.CRITICAL,
                message=f"Database connection failed: {e}"
            ))

        return metrics

    async def _check_session_health(self) -> List[HealthMetric]:
        """Check session management health metrics"""
        metrics = []

        try:
            async with session_scope() as db_session:
                # Count sessions by status
                result = await db_session.execute(
                    select(
                        MangaSession.status,
                        func.count(MangaSession.id).label('count')
                    ).group_by(MangaSession.status)
                )
                status_counts = dict(result.fetchall())

                total_sessions = sum(status_counts.values())
                if total_sessions > 0:
                    # Calculate ratios
                    failed_ratio = status_counts.get(MangaSessionStatus.FAILED.value, 0) / total_sessions
                    running_ratio = status_counts.get(MangaSessionStatus.RUNNING.value, 0) / total_sessions

                    # Failed sessions ratio
                    failed_status = self._evaluate_threshold("failed_sessions_ratio", failed_ratio)
                    metrics.append(HealthMetric(
                        name="failed_sessions_ratio",
                        value=failed_ratio,
                        status=failed_status,
                        message=f"Failed sessions: {failed_ratio:.1%} of total"
                    ))

                    # Active sessions load
                    active_status = self._evaluate_threshold("active_sessions_ratio", running_ratio)
                    metrics.append(HealthMetric(
                        name="active_sessions_ratio",
                        value=running_ratio,
                        status=active_status,
                        message=f"Active sessions: {running_ratio:.1%} of total"
                    ))

                # Check for stale sessions
                reconciliation_stats = await StateReconciler.reconcile_all_sessions()
                stale_count = (
                    reconciliation_stats.get("stale_running_fixed", 0) +
                    reconciliation_stats.get("stale_queued_fixed", 0) +
                    reconciliation_stats.get("stale_processing_fixed", 0)
                )

                stale_status = self._evaluate_threshold("stale_sessions_count", stale_count)
                metrics.append(HealthMetric(
                    name="stale_sessions_count",
                    value=stale_count,
                    status=stale_status,
                    message=f"Stale sessions detected and fixed: {stale_count}"
                ))

        except Exception as e:
            metrics.append(HealthMetric(
                name="session_health_check",
                value=0,
                status=HealthStatus.CRITICAL,
                message=f"Session health check failed: {e}"
            ))

        return metrics

    async def _check_circuit_breaker_health(self) -> List[HealthMetric]:
        """Check circuit breaker status"""
        metrics = []

        try:
            breaker_health = await circuit_breaker_manager.health_check()
            open_breakers = breaker_health["open_breakers"]

            status = self._evaluate_threshold("circuit_breakers_open", open_breakers)
            metrics.append(HealthMetric(
                name="circuit_breakers_open",
                value=open_breakers,
                status=status,
                message=f"Open circuit breakers: {open_breakers}/{breaker_health['total_breakers']}"
            ))

            metrics.append(HealthMetric(
                name="circuit_breaker_health_percentage",
                value=breaker_health["healthy_percentage"],
                status=HealthStatus.HEALTHY if breaker_health["healthy_percentage"] > 80 else HealthStatus.WARNING,
                message=f"Circuit breaker health: {breaker_health['healthy_percentage']:.1f}%"
            ))

        except Exception as e:
            metrics.append(HealthMetric(
                name="circuit_breaker_check",
                value=0,
                status=HealthStatus.CRITICAL,
                message=f"Circuit breaker health check failed: {e}"
            ))

        return metrics

    async def _check_performance_metrics(self) -> List[HealthMetric]:
        """Check system performance metrics"""
        metrics = []

        try:
            async with session_scope() as db_session:
                # Check average processing time for recent completed sessions
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                result = await db_session.execute(
                    select(
                        func.avg(
                            func.extract('epoch', MangaSession.updated_at - MangaSession.created_at)
                        ).label('avg_processing_time')
                    ).where(
                        and_(
                            MangaSession.status == MangaSessionStatus.COMPLETED.value,
                            MangaSession.updated_at > cutoff_time
                        )
                    )
                )
                avg_time = result.scalar() or 0

                status = self._evaluate_threshold("average_processing_time", avg_time)
                metrics.append(HealthMetric(
                    name="average_processing_time",
                    value=avg_time,
                    status=status,
                    message=f"Average processing time (24h): {avg_time:.1f}s"
                ))

        except Exception as e:
            metrics.append(HealthMetric(
                name="performance_check",
                value=0,
                status=HealthStatus.CRITICAL,
                message=f"Performance metrics check failed: {e}"
            ))

        return metrics

    async def _check_state_consistency(self) -> List[HealthMetric]:
        """Check system state consistency"""
        metrics = []

        try:
            # Run state reconciliation and check results
            reconciliation_stats = await StateReconciler.reconcile_all_sessions()

            # Total inconsistencies found
            total_issues = (
                reconciliation_stats.get("stale_running_fixed", 0) +
                reconciliation_stats.get("stale_queued_fixed", 0) +
                reconciliation_stats.get("stale_processing_fixed", 0) +
                reconciliation_stats.get("errors", 0)
            )

            status = HealthStatus.HEALTHY if total_issues == 0 else HealthStatus.WARNING if total_issues < 5 else HealthStatus.CRITICAL
            metrics.append(HealthMetric(
                name="state_consistency_issues",
                value=total_issues,
                status=status,
                message=f"State consistency issues found and resolved: {total_issues}"
            ))

        except Exception as e:
            metrics.append(HealthMetric(
                name="state_consistency_check",
                value=0,
                status=HealthStatus.CRITICAL,
                message=f"State consistency check failed: {e}"
            ))

        return metrics

    def _evaluate_threshold(self, metric_name: str, value: float) -> HealthStatus:
        """Evaluate a metric value against defined thresholds"""
        thresholds = self.alert_thresholds.get(metric_name, {})

        if "critical" in thresholds and value >= thresholds["critical"]:
            return HealthStatus.CRITICAL
        elif "warning" in thresholds and value >= thresholds["warning"]:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY

    def _calculate_overall_health(self, metrics: List[HealthMetric]) -> tuple[HealthStatus, float]:
        """Calculate overall system health status and score"""
        if not metrics:
            return HealthStatus.UNKNOWN, 0

        # Count metrics by status
        status_counts = {status: 0 for status in HealthStatus}
        for metric in metrics:
            status_counts[metric.status] += 1

        total_metrics = len(metrics)

        # Calculate score (0-100)
        score = (
            (status_counts[HealthStatus.HEALTHY] * 100) +
            (status_counts[HealthStatus.WARNING] * 60) +
            (status_counts[HealthStatus.CRITICAL] * 0) +
            (status_counts[HealthStatus.UNKNOWN] * 50)
        ) / total_metrics

        # Determine overall status
        if status_counts[HealthStatus.CRITICAL] > 0:
            overall_status = HealthStatus.CRITICAL
        elif status_counts[HealthStatus.WARNING] > 0:
            overall_status = HealthStatus.WARNING
        elif status_counts[HealthStatus.UNKNOWN] > total_metrics * 0.5:
            overall_status = HealthStatus.UNKNOWN
        else:
            overall_status = HealthStatus.HEALTHY

        return overall_status, score

    def _generate_recommendations(self, metrics: List[HealthMetric]) -> List[str]:
        """Generate actionable recommendations based on metrics"""
        recommendations = []

        for metric in metrics:
            if metric.status == HealthStatus.CRITICAL:
                if "database" in metric.name:
                    recommendations.append(f"🚨 CRITICAL: Database issues detected - {metric.message}")
                elif "failed_sessions" in metric.name:
                    recommendations.append(f"🚨 CRITICAL: High failure rate - investigate error patterns")
                elif "circuit_breaker" in metric.name:
                    recommendations.append(f"🚨 CRITICAL: External services failing - check service health")
                elif "stale_sessions" in metric.name:
                    recommendations.append(f"🚨 CRITICAL: Many stale sessions - check processing pipeline")

            elif metric.status == HealthStatus.WARNING:
                if "active_sessions" in metric.name:
                    recommendations.append(f"⚠️ WARNING: High system load - consider scaling")
                elif "processing_time" in metric.name:
                    recommendations.append(f"⚠️ WARNING: Slow processing - optimize pipeline performance")

        if not recommendations:
            recommendations.append("✅ System appears healthy - continue monitoring")

        return recommendations

    async def _store_metric_history(self, metrics: List[HealthMetric]) -> None:
        """Store metrics for historical analysis"""
        for metric in metrics:
            if metric.name not in self.metric_history:
                self.metric_history[metric.name] = []

            history = self.metric_history[metric.name]
            history.append(metric)

            # Keep only last 100 entries per metric
            if len(history) > 100:
                history.pop(0)


# Global health monitor instance
health_monitor = HealthMonitor()


async def start_health_monitoring(interval_minutes: int = 5):
    """Start background health monitoring"""
    logger.info(f"🏥 Starting health monitoring (every {interval_minutes} minutes)")

    while True:
        try:
            await asyncio.sleep(interval_minutes * 60)
            report = await health_monitor.get_system_health()

            # Log critical issues immediately
            if report.overall_status == HealthStatus.CRITICAL:
                logger.error(f"🚨 CRITICAL SYSTEM HEALTH: {report.score:.1f}/100")
                for rec in report.recommendations:
                    logger.error(rec)

        except Exception as e:
            logger.error(f"Health monitoring iteration failed: {e}")
            # Continue monitoring even if one iteration fails