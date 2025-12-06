---
document_id: "INF-MON-IMPL-001"
title: "監視システム実装仕様"
version: "1.0"
date_created: "2025-10-01"
status: "active"
category: "infrastructure"
document_type: "implementation-spec"
tags: ["monitoring", "logging", "alerting", "cloud-monitoring", "cloud-logging", "implementation", "gcp", "observability"]
parent_doc: "INF-MON-001"
related_docs: ["INF-DEP-PROC-001", "INF-OVERVIEW-001", "API-IMPL-001"]
target_audience: ["backend-developer", "sre-engineer", "devops-engineer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# 監視システム実装仕様

> **TL;DR**: Cloud Monitoring/Logging完全実装ガイド。Python構造化ログ実装、カスタムメトリクス収集、アラートポリシー自動作成、ダッシュボード設定を網羅。gcloudコマンド・Terraform・Pythonコード例で本番レディ監視システムを構築。

## 目次

1. [Cloud Logging実装](#1-cloud-logging実装)
2. [Cloud Monitoring実装](#2-cloud-monitoring実装)
3. [カスタムメトリクス実装](#3-カスタムメトリクス実装)
4. [アラートポリシー実装](#4-アラートポリシー実装)
5. [ダッシュボード実装](#5-ダッシュボード実装)
6. [初期セットアップ手順](#6-初期セットアップ手順)

---

## 1. Cloud Logging実装

### 1.1 構造化ログ実装

#### Python構造化ログ設定

```python
# backend/app/core/logging_config.py
import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
from google.cloud import logging as cloud_logging
import structlog

# リクエストコンテキスト用ContextVar
request_id_ctx: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_ctx: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
trace_id_ctx: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)


def configure_structured_logging():
    """構造化ログの設定"""

    # Cloud Loggingクライアント初期化
    if settings.ENVIRONMENT == "production":
        client = cloud_logging.Client()
        client.setup_logging()

    # Structlog設定
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            add_timestamp,
            add_request_context,
            add_service_metadata,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def add_timestamp(logger, method_name, event_dict):
    """ISO 8601タイムスタンプ追加"""
    event_dict["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return event_dict


def add_request_context(logger, method_name, event_dict):
    """リクエストコンテキスト追加"""
    event_dict["request_id"] = request_id_ctx.get()
    event_dict["user_id"] = user_id_ctx.get()
    event_dict["trace_id"] = trace_id_ctx.get()
    return event_dict


def add_service_metadata(logger, method_name, event_dict):
    """サービスメタデータ追加"""
    event_dict["service"] = "manga-service"
    event_dict["version"] = settings.APP_VERSION
    event_dict["environment"] = settings.ENVIRONMENT
    return event_dict


# グローバルロガー取得
def get_logger(name: str):
    """構造化ロガー取得"""
    return structlog.get_logger(name)
```

#### FastAPI統合

```python
# backend/app/middleware/logging_middleware.py
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging_config import get_logger, request_id_ctx, user_id_ctx, trace_id_ctx

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """リクエストログミドルウェア"""

    async def dispatch(self, request: Request, call_next):
        # リクエストID生成
        request_id = str(uuid.uuid4())
        request_id_ctx.set(request_id)

        # Cloud Trace ID取得（存在する場合）
        trace_header = request.headers.get("X-Cloud-Trace-Context")
        if trace_header:
            trace_id = trace_header.split("/")[0]
            trace_id_ctx.set(trace_id)

        # ユーザーID取得（認証済みの場合）
        if hasattr(request.state, "user"):
            user_id_ctx.set(request.state.user.uid)

        # リクエスト開始ログ
        logger.info(
            "request_started",
            method=request.method,
            endpoint=str(request.url.path),
            query_params=dict(request.query_params),
            user_agent=request.headers.get("user-agent"),
            source_ip=request.client.host
        )

        # リクエスト処理
        import time
        start_time = time.time()

        try:
            response = await call_next(request)
            processing_time = (time.time() - start_time) * 1000  # ms

            # リクエスト完了ログ
            logger.info(
                "request_completed",
                method=request.method,
                endpoint=str(request.url.path),
                status_code=response.status_code,
                response_time=processing_time
            )

            # レスポンスヘッダーにリクエストID追加
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            processing_time = (time.time() - start_time) * 1000

            # エラーログ
            logger.error(
                "request_failed",
                method=request.method,
                endpoint=str(request.url.path),
                response_time=processing_time,
                error=str(exc),
                error_type=type(exc).__name__
            )
            raise
```

#### 漫画生成フェーズログ

```python
# backend/app/services/phase_logger.py
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class PhaseLogger:
    """フェーズ処理ログ専用クラス"""

    @staticmethod
    def log_phase_start(session_id: str, phase: int, context: dict):
        """フェーズ開始ログ"""
        logger.info(
            "phase_started",
            event_type="manga_generation",
            session_id=session_id,
            phase=phase,
            genre=context.get("genre"),
            style=context.get("style")
        )

    @staticmethod
    def log_phase_progress(session_id: str, phase: int, progress: float, message: str):
        """フェーズ進捗ログ"""
        logger.info(
            "phase_progress",
            event_type="manga_generation",
            session_id=session_id,
            phase=phase,
            progress=progress,
            message=message
        )

    @staticmethod
    def log_phase_complete(
        session_id: str,
        phase: int,
        quality_score: float,
        processing_time: float,
        retry_count: int
    ):
        """フェーズ完了ログ"""
        logger.info(
            "phase_completed",
            event_type="manga_generation",
            session_id=session_id,
            phase=phase,
            quality_score=quality_score,
            processing_time=processing_time,
            retry_count=retry_count,
            success=True
        )

    @staticmethod
    def log_phase_error(
        session_id: str,
        phase: int,
        error: Exception,
        retry_count: int,
        processing_time: float
    ):
        """フェーズエラーログ"""
        logger.error(
            "phase_failed",
            event_type="manga_generation",
            session_id=session_id,
            phase=phase,
            error=str(error),
            error_type=type(error).__name__,
            retry_count=retry_count,
            processing_time=processing_time,
            success=False
        )

    @staticmethod
    def log_hitl_feedback(session_id: str, phase: int, feedback: dict):
        """HITLフィードバックログ"""
        logger.info(
            "hitl_feedback",
            event_type="user_interaction",
            session_id=session_id,
            phase=phase,
            action=feedback.get("action"),  # skip or modify
            has_modification=bool(feedback.get("modification"))
        )
```

#### セキュリティイベントログ

```python
# backend/app/core/security_logger.py
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class SecurityLogger:
    """セキュリティイベントログ専用クラス"""

    @staticmethod
    def log_authentication(
        user_id: str,
        event_type: str,
        result: str,
        source_ip: str,
        user_agent: str,
        reason: str = None
    ):
        """認証イベントログ"""
        logger.info(
            "security_event",
            event_type=event_type,  # login, logout, token_refresh
            security_category="authentication",
            user_id=user_id,
            result=result,  # SUCCESS, FAILURE, BLOCKED
            source_ip=source_ip,
            user_agent=user_agent,
            reason=reason
        )

    @staticmethod
    def log_authorization(
        user_id: str,
        resource: str,
        action: str,
        result: str,
        reason: str = None
    ):
        """認可イベントログ"""
        logger.info(
            "security_event",
            event_type="authorization",
            security_category="authorization",
            user_id=user_id,
            resource=resource,
            action=action,
            result=result,  # GRANTED, DENIED
            reason=reason
        )

    @staticmethod
    def log_rate_limit(
        user_id: str,
        endpoint: str,
        limit: int,
        current_count: int,
        source_ip: str
    ):
        """レート制限イベントログ"""
        logger.warning(
            "security_event",
            event_type="rate_limit_exceeded",
            security_category="rate_limiting",
            user_id=user_id,
            endpoint=endpoint,
            limit=limit,
            current_count=current_count,
            source_ip=source_ip
        )

    @staticmethod
    def log_suspicious_activity(
        user_id: str,
        activity_type: str,
        details: dict,
        source_ip: str
    ):
        """疑わしいアクティビティログ"""
        logger.warning(
            "security_event",
            event_type="suspicious_activity",
            security_category="threat_detection",
            user_id=user_id,
            activity_type=activity_type,
            details=details,
            source_ip=source_ip
        )
```

### 1.2 ログシンク設定

#### gcloudコマンドでログシンク作成

```bash
#!/bin/bash
# scripts/setup-log-sinks.sh

PROJECT_ID="your-project-id"
REGION="asia-northeast1"

# 1. アプリケーションログシンク（Cloud Logging）
gcloud logging sinks create application-logs \
  storage.googleapis.com/manga-logs-application \
  --log-filter='resource.type="cloud_run_revision"
    AND severity >= INFO' \
  --project=${PROJECT_ID}

# 2. セキュリティログシンク（BigQuery）
gcloud logging sinks create security-logs-bigquery \
  bigquery.googleapis.com/projects/${PROJECT_ID}/datasets/security_logs \
  --log-filter='jsonPayload.security_category EXISTS
    AND resource.type="cloud_run_revision"' \
  --project=${PROJECT_ID}

# 3. エラーログシンク（Cloud Storage + Cloud Logging）
gcloud logging sinks create error-logs \
  storage.googleapis.com/manga-logs-errors \
  --log-filter='severity >= ERROR
    AND resource.type="cloud_run_revision"' \
  --project=${PROJECT_ID}

# 4. パフォーマンスログシンク（BigQuery）
gcloud logging sinks create performance-logs-bigquery \
  bigquery.googleapis.com/projects/${PROJECT_ID}/datasets/performance_logs \
  --log-filter='jsonPayload.response_time > 1000
    AND resource.type="cloud_run_revision"' \
  --project=${PROJECT_ID}

# 5. Slackクリティカルアラートシンク
gcloud logging sinks create slack-critical-alerts \
  pubsub.googleapis.com/projects/${PROJECT_ID}/topics/critical-alerts \
  --log-filter='severity = CRITICAL
    AND resource.type="cloud_run_revision"' \
  --project=${PROJECT_ID}

echo "ログシンク作成完了"
```

#### Terraformでログシンク設定

```hcl
# terraform/logging.tf

# Application Logs Sink
resource "google_logging_project_sink" "application_logs" {
  name        = "application-logs"
  destination = "storage.googleapis.com/${google_storage_bucket.application_logs.name}"

  filter = <<-EOT
    resource.type="cloud_run_revision"
    AND severity >= INFO
  EOT

  unique_writer_identity = true
}

resource "google_storage_bucket" "application_logs" {
  name          = "${var.project_id}-logs-application"
  location      = var.region
  force_destroy = false

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

# Security Logs Sink (BigQuery)
resource "google_logging_project_sink" "security_logs" {
  name        = "security-logs-bigquery"
  destination = "bigquery.googleapis.com/projects/${var.project_id}/datasets/${google_bigquery_dataset.security_logs.dataset_id}"

  filter = <<-EOT
    jsonPayload.security_category EXISTS
    AND resource.type="cloud_run_revision"
  EOT

  unique_writer_identity = true
}

resource "google_bigquery_dataset" "security_logs" {
  dataset_id                 = "security_logs"
  location                   = var.region
  default_table_expiration_ms = 31536000000  # 1 year
}

# Error Logs Sink
resource "google_logging_project_sink" "error_logs" {
  name        = "error-logs"
  destination = "storage.googleapis.com/${google_storage_bucket.error_logs.name}"

  filter = <<-EOT
    severity >= ERROR
    AND resource.type="cloud_run_revision"
  EOT

  unique_writer_identity = true
}

resource "google_storage_bucket" "error_logs" {
  name          = "${var.project_id}-logs-errors"
  location      = var.region
  force_destroy = false

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

# Performance Logs Sink (BigQuery)
resource "google_logging_project_sink" "performance_logs" {
  name        = "performance-logs-bigquery"
  destination = "bigquery.googleapis.com/projects/${var.project_id}/datasets/${google_bigquery_dataset.performance_logs.dataset_id}"

  filter = <<-EOT
    jsonPayload.response_time > 1000
    AND resource.type="cloud_run_revision"
  EOT

  unique_writer_identity = true
}

resource "google_bigquery_dataset" "performance_logs" {
  dataset_id                 = "performance_logs"
  location                   = var.region
  default_table_expiration_ms = 15552000000  # 6 months
}
```

---

## 2. Cloud Monitoring実装

### 2.1 メトリクスクライアント実装

```python
# backend/app/core/metrics_client.py
from google.cloud import monitoring_v3
from google.api import metric_pb2 as ga_metric
from google.api import label_pb2 as ga_label
import time
from typing import Dict, Any, Optional
from app.core.config import settings

class MetricsClient:
    """Cloud Monitoringメトリクスクライアント"""

    def __init__(self):
        self.project_id = settings.GCP_PROJECT_ID
        self.client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{self.project_id}"

        # メトリクス記述子を作成（初回のみ）
        self._ensure_metric_descriptors()

    def _ensure_metric_descriptors(self):
        """カスタムメトリクス記述子を作成"""
        descriptors = [
            {
                "type": "custom.googleapis.com/manga/generation/processing_time",
                "metric_kind": ga_metric.MetricDescriptor.MetricKind.GAUGE,
                "value_type": ga_metric.MetricDescriptor.ValueType.DOUBLE,
                "unit": "s",
                "description": "漫画生成フェーズ処理時間",
                "display_name": "Manga Generation Processing Time",
                "labels": [
                    ga_label.LabelDescriptor(
                        key="phase",
                        value_type=ga_label.LabelDescriptor.ValueType.STRING,
                        description="Processing phase number"
                    ),
                    ga_label.LabelDescriptor(
                        key="session_id",
                        value_type=ga_label.LabelDescriptor.ValueType.STRING,
                        description="Generation session ID"
                    )
                ]
            },
            {
                "type": "custom.googleapis.com/manga/generation/quality_score",
                "metric_kind": ga_metric.MetricDescriptor.MetricKind.GAUGE,
                "value_type": ga_metric.MetricDescriptor.ValueType.DOUBLE,
                "unit": "1",
                "description": "AI生成品質スコア",
                "display_name": "Manga Generation Quality Score",
                "labels": [
                    ga_label.LabelDescriptor(
                        key="phase",
                        value_type=ga_label.LabelDescriptor.ValueType.STRING
                    )
                ]
            },
            {
                "type": "custom.googleapis.com/manga/generation/success_rate",
                "metric_kind": ga_metric.MetricDescriptor.MetricKind.GAUGE,
                "value_type": ga_metric.MetricDescriptor.ValueType.DOUBLE,
                "unit": "%",
                "description": "漫画生成成功率",
                "display_name": "Manga Generation Success Rate",
                "labels": [
                    ga_label.LabelDescriptor(
                        key="phase",
                        value_type=ga_label.LabelDescriptor.ValueType.STRING
                    )
                ]
            },
            {
                "type": "custom.googleapis.com/manga/user/active_count",
                "metric_kind": ga_metric.MetricDescriptor.MetricKind.GAUGE,
                "value_type": ga_metric.MetricDescriptor.ValueType.INT64,
                "unit": "1",
                "description": "アクティブユーザー数",
                "display_name": "Active User Count",
                "labels": [
                    ga_label.LabelDescriptor(
                        key="account_type",
                        value_type=ga_label.LabelDescriptor.ValueType.STRING
                    )
                ]
            },
            {
                "type": "custom.googleapis.com/manga/user/session_duration",
                "metric_kind": ga_metric.MetricDescriptor.MetricKind.GAUGE,
                "value_type": ga_metric.MetricDescriptor.ValueType.DOUBLE,
                "unit": "s",
                "description": "ユーザーセッション継続時間",
                "display_name": "User Session Duration",
                "labels": []
            },
            {
                "type": "custom.googleapis.com/manga/business/generation_count",
                "metric_kind": ga_metric.MetricDescriptor.MetricKind.CUMULATIVE,
                "value_type": ga_metric.MetricDescriptor.ValueType.INT64,
                "unit": "1",
                "description": "漫画生成総数",
                "display_name": "Total Generation Count",
                "labels": [
                    ga_label.LabelDescriptor(
                        key="account_type",
                        value_type=ga_label.LabelDescriptor.ValueType.STRING
                    )
                ]
            },
            {
                "type": "custom.googleapis.com/manga/business/cost_per_generation",
                "metric_kind": ga_metric.MetricDescriptor.MetricKind.GAUGE,
                "value_type": ga_metric.MetricDescriptor.ValueType.DOUBLE,
                "unit": "USD",
                "description": "1世代あたりのコスト",
                "display_name": "Cost Per Generation",
                "labels": []
            }
        ]

        for descriptor_config in descriptors:
            try:
                descriptor = ga_metric.MetricDescriptor(
                    type=descriptor_config["type"],
                    metric_kind=descriptor_config["metric_kind"],
                    value_type=descriptor_config["value_type"],
                    unit=descriptor_config["unit"],
                    description=descriptor_config["description"],
                    display_name=descriptor_config["display_name"],
                    labels=descriptor_config.get("labels", [])
                )
                self.client.create_metric_descriptor(
                    name=self.project_name,
                    metric_descriptor=descriptor
                )
            except Exception as e:
                # 既に存在する場合はスキップ
                if "already exists" not in str(e).lower():
                    print(f"メトリクス記述子作成エラー: {e}")

    def write_metric(
        self,
        metric_type: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        resource_type: str = "cloud_run_revision"
    ):
        """メトリクスを書き込み"""
        series = monitoring_v3.TimeSeries()
        series.metric.type = metric_type
        series.resource.type = resource_type

        # ラベル設定
        if labels:
            for key, val in labels.items():
                series.metric.labels[key] = str(val)

        # タイムスタンプと値
        now = time.time()
        seconds = int(now)
        nanos = int((now - seconds) * 10 ** 9)

        interval = monitoring_v3.TimeInterval(
            {"end_time": {"seconds": seconds, "nanos": nanos}}
        )

        point = monitoring_v3.Point(
            {
                "interval": interval,
                "value": {"double_value": float(value)}
            }
        )
        series.points = [point]

        # メトリクス送信
        try:
            self.client.create_time_series(
                name=self.project_name,
                time_series=[series]
            )
        except Exception as e:
            print(f"メトリクス書き込みエラー: {e}")


# グローバルメトリクスクライアント
metrics_client = MetricsClient()
```

---

## 3. カスタムメトリクス実装

### 3.1 漫画生成メトリクス

```python
# backend/app/services/generation_metrics.py
from app.core.metrics_client import metrics_client
from app.core.logging_config import get_logger
from typing import Dict, Any

logger = get_logger(__name__)


class GenerationMetrics:
    """漫画生成メトリクス収集クラス"""

    @staticmethod
    def record_phase_metrics(
        session_id: str,
        phase: int,
        processing_time: float,
        quality_score: float,
        success: bool,
        retry_count: int = 0
    ):
        """フェーズメトリクスを記録"""

        # 処理時間
        metrics_client.write_metric(
            metric_type="custom.googleapis.com/manga/generation/processing_time",
            value=processing_time,
            labels={"phase": str(phase), "session_id": session_id}
        )

        # 品質スコア
        metrics_client.write_metric(
            metric_type="custom.googleapis.com/manga/generation/quality_score",
            value=quality_score,
            labels={"phase": str(phase)}
        )

        # 成功率（0 or 100）
        success_rate = 100.0 if success else 0.0
        metrics_client.write_metric(
            metric_type="custom.googleapis.com/manga/generation/success_rate",
            value=success_rate,
            labels={"phase": str(phase)}
        )

        logger.info(
            "generation_metrics_recorded",
            session_id=session_id,
            phase=phase,
            processing_time=processing_time,
            quality_score=quality_score,
            success=success,
            retry_count=retry_count
        )

    @staticmethod
    def record_generation_complete(
        session_id: str,
        total_time: float,
        account_type: str,
        phase_count: int = 7
    ):
        """生成完了メトリクスを記録"""

        # 生成数カウント
        metrics_client.write_metric(
            metric_type="custom.googleapis.com/manga/business/generation_count",
            value=1.0,
            labels={"account_type": account_type}
        )

        logger.info(
            "generation_complete_metrics",
            session_id=session_id,
            total_time=total_time,
            account_type=account_type,
            phase_count=phase_count
        )
```

### 3.2 ユーザー行動メトリクス

```python
# backend/app/services/user_metrics.py
from app.core.metrics_client import metrics_client
from app.core.logging_config import get_logger
from datetime import datetime

logger = get_logger(__name__)


class UserMetrics:
    """ユーザー行動メトリクス収集クラス"""

    @staticmethod
    def record_active_user(user_id: str, account_type: str):
        """アクティブユーザー記録"""
        metrics_client.write_metric(
            metric_type="custom.googleapis.com/manga/user/active_count",
            value=1.0,
            labels={"account_type": account_type}
        )

    @staticmethod
    def record_session_end(user_id: str, session_duration: float):
        """セッション終了記録"""
        metrics_client.write_metric(
            metric_type="custom.googleapis.com/manga/user/session_duration",
            value=session_duration,
            labels={}
        )

        logger.info(
            "session_ended",
            user_id=user_id,
            session_duration=session_duration
        )

    @staticmethod
    def record_user_action(user_id: str, action: str, metadata: dict = None):
        """ユーザーアクション記録"""
        logger.info(
            "user_action",
            event_type="user_interaction",
            user_id=user_id,
            action=action,
            metadata=metadata or {}
        )
```

### 3.3 ビジネスメトリクス

```python
# backend/app/services/business_metrics.py
from app.core.metrics_client import metrics_client
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class BusinessMetrics:
    """ビジネスメトリクス収集クラス"""

    @staticmethod
    def record_cost_per_generation(
        session_id: str,
        gemini_cost: float,
        imagen_cost: float,
        infrastructure_cost: float
    ):
        """1生成あたりのコスト記録"""
        total_cost = gemini_cost + imagen_cost + infrastructure_cost

        metrics_client.write_metric(
            metric_type="custom.googleapis.com/manga/business/cost_per_generation",
            value=total_cost,
            labels={}
        )

        logger.info(
            "generation_cost_recorded",
            session_id=session_id,
            gemini_cost=gemini_cost,
            imagen_cost=imagen_cost,
            infrastructure_cost=infrastructure_cost,
            total_cost=total_cost
        )

    @staticmethod
    def record_subscription_conversion(user_id: str, from_plan: str, to_plan: str):
        """サブスクリプション変換記録"""
        logger.info(
            "subscription_conversion",
            event_type="business",
            user_id=user_id,
            from_plan=from_plan,
            to_plan=to_plan,
            conversion_direction="upgrade" if to_plan == "premium" else "downgrade"
        )
```

---

## 4. アラートポリシー実装

### 4.1 アラートポリシー作成スクリプト

```bash
#!/bin/bash
# scripts/setup-alert-policies.sh

PROJECT_ID="your-project-id"
NOTIFICATION_CHANNEL_SLACK="projects/${PROJECT_ID}/notificationChannels/YOUR_SLACK_CHANNEL_ID"
NOTIFICATION_CHANNEL_EMAIL="projects/${PROJECT_ID}/notificationChannels/YOUR_EMAIL_CHANNEL_ID"

# 1. サービス可用性アラート（Critical）
gcloud alpha monitoring policies create \
  --display-name="[Critical] Service Availability" \
  --condition-display-name="Service availability < 99.5%" \
  --condition-threshold-value=99.5 \
  --condition-threshold-duration=300s \
  --condition-threshold-filter='
    metric.type="run.googleapis.com/request_count"
    AND resource.type="cloud_run_revision"' \
  --notification-channels=${NOTIFICATION_CHANNEL_SLACK},${NOTIFICATION_CHANNEL_EMAIL} \
  --alert-strategy-auto-close=1800s \
  --project=${PROJECT_ID}

# 2. データベース接続エラーアラート（Critical）
gcloud alpha monitoring policies create \
  --display-name="[Critical] Database Connection Errors" \
  --condition-display-name="DB connection error rate > 10%" \
  --condition-threshold-value=0.10 \
  --condition-threshold-duration=120s \
  --condition-threshold-filter='
    metric.type="cloudsql.googleapis.com/database/network/connections"
    AND resource.type="cloudsql_database"' \
  --notification-channels=${NOTIFICATION_CHANNEL_SLACK},${NOTIFICATION_CHANNEL_EMAIL} \
  --project=${PROJECT_ID}

# 3. 高レイテンシアラート（High）
gcloud alpha monitoring policies create \
  --display-name="[High] High Latency" \
  --condition-display-name="P95 response time > 5s" \
  --condition-threshold-value=5000 \
  --condition-threshold-duration=600s \
  --condition-threshold-filter='
    metric.type="run.googleapis.com/request_latencies"
    AND resource.type="cloud_run_revision"' \
  --notification-channels=${NOTIFICATION_CHANNEL_SLACK} \
  --project=${PROJECT_ID}

# 4. 高エラー率アラート（High）
gcloud alpha monitoring policies create \
  --display-name="[High] High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=300s \
  --condition-threshold-filter='
    metric.type="run.googleapis.com/request_count"
    AND metric.label.response_code_class="5xx"
    AND resource.type="cloud_run_revision"' \
  --notification-channels=${NOTIFICATION_CHANNEL_SLACK},${NOTIFICATION_CHANNEL_EMAIL} \
  --project=${PROJECT_ID}

# 5. CPU使用率アラート（Medium）
gcloud alpha monitoring policies create \
  --display-name="[Medium] CPU Exhaustion" \
  --condition-display-name="CPU utilization > 85%" \
  --condition-threshold-value=0.85 \
  --condition-threshold-duration=900s \
  --condition-threshold-filter='
    metric.type="run.googleapis.com/container/cpu/utilizations"
    AND resource.type="cloud_run_revision"' \
  --notification-channels=${NOTIFICATION_CHANNEL_SLACK} \
  --project=${PROJECT_ID}

# 6. メモリ使用率アラート（Medium）
gcloud alpha monitoring policies create \
  --display-name="[Medium] Memory Exhaustion" \
  --condition-display-name="Memory utilization > 90%" \
  --condition-threshold-value=0.90 \
  --condition-threshold-duration=600s \
  --condition-threshold-filter='
    metric.type="run.googleapis.com/container/memory/utilizations"
    AND resource.type="cloud_run_revision"' \
  --notification-channels=${NOTIFICATION_CHANNEL_SLACK} \
  --project=${PROJECT_ID}

# 7. AI生成失敗アラート（High）
gcloud alpha monitoring policies create \
  --display-name="[High] AI Generation Failure Spike" \
  --condition-display-name="Generation failure rate > 20%" \
  --condition-threshold-value=20.0 \
  --condition-threshold-duration=1800s \
  --condition-threshold-filter='
    metric.type="custom.googleapis.com/manga/generation/success_rate"
    AND resource.type="cloud_run_revision"' \
  --notification-channels=${NOTIFICATION_CHANNEL_SLACK},${NOTIFICATION_CHANNEL_EMAIL} \
  --project=${PROJECT_ID}

echo "アラートポリシー作成完了"
```

### 4.2 Terraformアラートポリシー

```hcl
# terraform/monitoring_alerts.tf

# Notification Channels
resource "google_monitoring_notification_channel" "slack" {
  display_name = "Slack Critical Alerts"
  type         = "slack"

  labels = {
    channel_name = "#alerts-critical"
  }

  sensitive_labels {
    auth_token = var.slack_webhook_url
  }
}

resource "google_monitoring_notification_channel" "email" {
  display_name = "Email Alerts"
  type         = "email"

  labels = {
    email_address = "alerts@company.com"
  }
}

# Critical: Service Availability
resource "google_monitoring_alert_policy" "service_availability" {
  display_name = "[Critical] Service Availability"
  combiner     = "OR"

  conditions {
    display_name = "Service availability < 99.5%"

    condition_threshold {
      filter          = "metric.type=\"run.googleapis.com/request_count\" AND resource.type=\"cloud_run_revision\""
      duration        = "300s"
      comparison      = "COMPARISON_LT"
      threshold_value = 0.995

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = [
    google_monitoring_notification_channel.slack.id,
    google_monitoring_notification_channel.email.id
  ]

  alert_strategy {
    auto_close = "1800s"
  }
}

# High: High Latency
resource "google_monitoring_alert_policy" "high_latency" {
  display_name = "[High] High Latency"
  combiner     = "OR"

  conditions {
    display_name = "P95 response time > 5s"

    condition_threshold {
      filter          = "metric.type=\"run.googleapis.com/request_latencies\" AND resource.type=\"cloud_run_revision\""
      duration        = "600s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5000

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_PERCENTILE_95"
      }
    }
  }

  notification_channels = [
    google_monitoring_notification_channel.slack.id
  ]
}

# High: High Error Rate
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "[High] High Error Rate"
  combiner     = "OR"

  conditions {
    display_name = "Error rate > 5%"

    condition_threshold {
      filter          = "metric.type=\"run.googleapis.com/request_count\" AND metric.label.response_code_class=\"5xx\" AND resource.type=\"cloud_run_revision\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = [
    google_monitoring_notification_channel.slack.id,
    google_monitoring_notification_channel.email.id
  ]
}

# Medium: CPU Exhaustion
resource "google_monitoring_alert_policy" "cpu_exhaustion" {
  display_name = "[Medium] CPU Exhaustion"
  combiner     = "OR"

  conditions {
    display_name = "CPU utilization > 85%"

    condition_threshold {
      filter          = "metric.type=\"run.googleapis.com/container/cpu/utilizations\" AND resource.type=\"cloud_run_revision\""
      duration        = "900s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.85

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = [
    google_monitoring_notification_channel.slack.id
  ]
}

# High: AI Generation Failure Spike
resource "google_monitoring_alert_policy" "generation_failure" {
  display_name = "[High] AI Generation Failure Spike"
  combiner     = "OR"

  conditions {
    display_name = "Generation failure rate > 20%"

    condition_threshold {
      filter          = "metric.type=\"custom.googleapis.com/manga/generation/success_rate\" AND resource.type=\"cloud_run_revision\""
      duration        = "1800s"
      comparison      = "COMPARISON_LT"
      threshold_value = 80.0

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = [
    google_monitoring_notification_channel.slack.id,
    google_monitoring_notification_channel.email.id
  ]
}
```

---

## 5. ダッシュボード実装

### 5.1 Operationsダッシュボード

```json
// dashboards/operations-dashboard.json
{
  "displayName": "Manga Service - Operations Dashboard",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Request Rate (req/s)",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_RATE"
                    }
                  }
                }
              }
            ],
            "timeshiftDuration": "0s",
            "yAxis": {
              "label": "Requests/sec",
              "scale": "LINEAR"
            }
          }
        }
      },
      {
        "xPos": 6,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Response Time (P50, P95, P99)",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"run.googleapis.com/request_latencies\" resource.type=\"cloud_run_revision\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_DELTA",
                      "crossSeriesReducer": "REDUCE_PERCENTILE_50"
                    }
                  }
                },
                "plotType": "LINE",
                "targetAxis": "Y1"
              },
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"run.googleapis.com/request_latencies\" resource.type=\"cloud_run_revision\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_DELTA",
                      "crossSeriesReducer": "REDUCE_PERCENTILE_95"
                    }
                  }
                },
                "plotType": "LINE",
                "targetAxis": "Y1"
              },
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"run.googleapis.com/request_latencies\" resource.type=\"cloud_run_revision\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_DELTA",
                      "crossSeriesReducer": "REDUCE_PERCENTILE_99"
                    }
                  }
                },
                "plotType": "LINE",
                "targetAxis": "Y1"
              }
            ],
            "yAxis": {
              "label": "Latency (ms)",
              "scale": "LINEAR"
            }
          }
        }
      },
      {
        "yPos": 4,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Error Rate (%)",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\" metric.label.response_code_class=\"5xx\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_RATE"
                    }
                  }
                }
              }
            ],
            "yAxis": {
              "label": "Error Rate",
              "scale": "LINEAR"
            },
            "thresholds": [
              {
                "value": 0.05,
                "color": "RED",
                "direction": "ABOVE"
              }
            ]
          }
        }
      },
      {
        "xPos": 6,
        "yPos": 4,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "CPU Utilization (%)",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"run.googleapis.com/container/cpu/utilizations\" resource.type=\"cloud_run_revision\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_MEAN"
                    }
                  }
                }
              }
            ],
            "yAxis": {
              "label": "CPU %",
              "scale": "LINEAR"
            },
            "thresholds": [
              {
                "value": 0.85,
                "color": "YELLOW",
                "direction": "ABOVE"
              },
              {
                "value": 0.95,
                "color": "RED",
                "direction": "ABOVE"
              }
            ]
          }
        }
      },
      {
        "yPos": 8,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Memory Utilization (%)",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"run.googleapis.com/container/memory/utilizations\" resource.type=\"cloud_run_revision\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_MEAN"
                    }
                  }
                }
              }
            ],
            "yAxis": {
              "label": "Memory %",
              "scale": "LINEAR"
            },
            "thresholds": [
              {
                "value": 0.90,
                "color": "YELLOW",
                "direction": "ABOVE"
              },
              {
                "value": 0.95,
                "color": "RED",
                "direction": "ABOVE"
              }
            ]
          }
        }
      },
      {
        "xPos": 6,
        "yPos": 8,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Database Connections",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"cloudsql.googleapis.com/database/network/connections\" resource.type=\"cloudsql_database\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_MEAN"
                    }
                  }
                }
              }
            ],
            "yAxis": {
              "label": "Connections",
              "scale": "LINEAR"
            }
          }
        }
      }
    ]
  }
}
```

### 5.2 Businessダッシュボード

```json
// dashboards/business-dashboard.json
{
  "displayName": "Manga Service - Business Dashboard",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 4,
        "height": 3,
        "widget": {
          "title": "Active Users (Last 24h)",
          "scorecard": {
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "metric.type=\"custom.googleapis.com/manga/user/active_count\" resource.type=\"cloud_run_revision\"",
                "aggregation": {
                  "alignmentPeriod": "86400s",
                  "perSeriesAligner": "ALIGN_SUM"
                }
              }
            }
          }
        }
      },
      {
        "xPos": 4,
        "width": 4,
        "height": 3,
        "widget": {
          "title": "Total Generations (Last 24h)",
          "scorecard": {
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "metric.type=\"custom.googleapis.com/manga/business/generation_count\" resource.type=\"cloud_run_revision\"",
                "aggregation": {
                  "alignmentPeriod": "86400s",
                  "perSeriesAligner": "ALIGN_SUM"
                }
              }
            }
          }
        }
      },
      {
        "xPos": 8,
        "width": 4,
        "height": 3,
        "widget": {
          "title": "Avg Session Duration (min)",
          "scorecard": {
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "metric.type=\"custom.googleapis.com/manga/user/session_duration\" resource.type=\"cloud_run_revision\"",
                "aggregation": {
                  "alignmentPeriod": "3600s",
                  "perSeriesAligner": "ALIGN_MEAN"
                }
              }
            }
          }
        }
      },
      {
        "yPos": 3,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Generation Success Rate by Phase",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"custom.googleapis.com/manga/generation/success_rate\" resource.type=\"cloud_run_revision\"",
                    "aggregation": {
                      "alignmentPeriod": "300s",
                      "perSeriesAligner": "ALIGN_MEAN",
                      "groupByFields": ["metric.label.phase"]
                    }
                  }
                }
              }
            ],
            "yAxis": {
              "label": "Success Rate (%)",
              "scale": "LINEAR"
            },
            "thresholds": [
              {
                "value": 70.0,
                "color": "RED",
                "direction": "BELOW"
              },
              {
                "value": 85.0,
                "color": "YELLOW",
                "direction": "BELOW"
              }
            ]
          }
        }
      },
      {
        "xPos": 6,
        "yPos": 3,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Quality Score Distribution",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"custom.googleapis.com/manga/generation/quality_score\" resource.type=\"cloud_run_revision\"",
                    "aggregation": {
                      "alignmentPeriod": "300s",
                      "perSeriesAligner": "ALIGN_MEAN",
                      "groupByFields": ["metric.label.phase"]
                    }
                  }
                }
              }
            ],
            "yAxis": {
              "label": "Quality Score",
              "scale": "LINEAR"
            }
          }
        }
      },
      {
        "yPos": 7,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Processing Time by Phase (seconds)",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"custom.googleapis.com/manga/generation/processing_time\" resource.type=\"cloud_run_revision\"",
                    "aggregation": {
                      "alignmentPeriod": "300s",
                      "perSeriesAligner": "ALIGN_MEAN",
                      "groupByFields": ["metric.label.phase"]
                    }
                  }
                }
              }
            ],
            "yAxis": {
              "label": "Time (s)",
              "scale": "LINEAR"
            }
          }
        }
      },
      {
        "xPos": 6,
        "yPos": 7,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Cost Per Generation (USD)",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"custom.googleapis.com/manga/business/cost_per_generation\" resource.type=\"cloud_run_revision\"",
                    "aggregation": {
                      "alignmentPeriod": "3600s",
                      "perSeriesAligner": "ALIGN_MEAN"
                    }
                  }
                }
              }
            ],
            "yAxis": {
              "label": "Cost (USD)",
              "scale": "LINEAR"
            },
            "thresholds": [
              {
                "value": 1.0,
                "color": "RED",
                "direction": "ABOVE"
              },
              {
                "value": 0.5,
                "color": "YELLOW",
                "direction": "ABOVE"
              }
            ]
          }
        }
      }
    ]
  }
}
```

---

## 6. 初期セットアップ手順

### 6.1 完全セットアップスクリプト

```bash
#!/bin/bash
# scripts/setup-monitoring-complete.sh

set -e

PROJECT_ID="${GCP_PROJECT_ID}"
REGION="asia-northeast1"

echo "=== 監視システムセットアップ開始 ==="

# 1. APIを有効化
echo "Step 1: GCP APIの有効化..."
gcloud services enable \
  monitoring.googleapis.com \
  logging.googleapis.com \
  cloudtrace.googleapis.com \
  clouderrorreporting.googleapis.com \
  --project=${PROJECT_ID}

# 2. サービスアカウント作成
echo "Step 2: 監視用サービスアカウント作成..."
gcloud iam service-accounts create monitoring-sa \
  --display-name="Monitoring Service Account" \
  --project=${PROJECT_ID}

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:monitoring-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/monitoring.metricWriter"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:monitoring-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"

# 3. ログバケット作成
echo "Step 3: Cloud Storageログバケット作成..."
gsutil mb -p ${PROJECT_ID} -l ${REGION} gs://${PROJECT_ID}-logs-application/ || true
gsutil mb -p ${PROJECT_ID} -l ${REGION} gs://${PROJECT_ID}-logs-errors/ || true

# ライフサイクルルール設定
echo '{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 30}
      }
    ]
  }
}' > /tmp/application-logs-lifecycle.json

gsutil lifecycle set /tmp/application-logs-lifecycle.json gs://${PROJECT_ID}-logs-application/

echo '{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}
      }
    ]
  }
}' > /tmp/error-logs-lifecycle.json

gsutil lifecycle set /tmp/error-logs-lifecycle.json gs://${PROJECT_ID}-logs-errors/

# 4. BigQueryデータセット作成
echo "Step 4: BigQueryデータセット作成..."
bq mk --dataset \
  --location=${REGION} \
  --default_table_expiration=31536000 \
  ${PROJECT_ID}:security_logs

bq mk --dataset \
  --location=${REGION} \
  --default_table_expiration=15552000 \
  ${PROJECT_ID}:performance_logs

# 5. ログシンク作成
echo "Step 5: ログシンク作成..."
bash scripts/setup-log-sinks.sh

# 6. 通知チャネル作成
echo "Step 6: 通知チャネル作成..."
# Slack通知チャネル（要Webhook URL）
if [ -n "${SLACK_WEBHOOK_URL}" ]; then
  gcloud alpha monitoring channels create \
    --display-name="Slack Critical Alerts" \
    --type=slack \
    --channel-labels=channel_name="#alerts-critical" \
    --user-labels=url="${SLACK_WEBHOOK_URL}" \
    --project=${PROJECT_ID}
fi

# Email通知チャネル
gcloud alpha monitoring channels create \
  --display-name="Email Alerts" \
  --type=email \
  --channel-labels=email_address="alerts@company.com" \
  --project=${PROJECT_ID}

# 7. アラートポリシー作成
echo "Step 7: アラートポリシー作成..."
bash scripts/setup-alert-policies.sh

# 8. ダッシュボード作成
echo "Step 8: ダッシュボード作成..."
gcloud monitoring dashboards create \
  --config-from-file=dashboards/operations-dashboard.json \
  --project=${PROJECT_ID}

gcloud monitoring dashboards create \
  --config-from-file=dashboards/business-dashboard.json \
  --project=${PROJECT_ID}

# 9. Cloud Runサービスに監視設定適用
echo "Step 9: Cloud Runサービス監視設定..."
gcloud run services update manga-service-prod \
  --region=${REGION} \
  --service-account=monitoring-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID}" \
  --project=${PROJECT_ID}

echo "=== 監視システムセットアップ完了 ==="
echo ""
echo "次のステップ:"
echo "1. Cloud Consoleで監視ダッシュボードを確認"
echo "   https://console.cloud.google.com/monitoring/dashboards?project=${PROJECT_ID}"
echo "2. アラートポリシーを確認"
echo "   https://console.cloud.google.com/monitoring/alerting/policies?project=${PROJECT_ID}"
echo "3. ログを確認"
echo "   https://console.cloud.google.com/logs/query?project=${PROJECT_ID}"
```

### 6.2 Terraformでの完全セットアップ

```hcl
# terraform/monitoring_complete.tf

# Enable APIs
resource "google_project_service" "monitoring" {
  service = "monitoring.googleapis.com"
}

resource "google_project_service" "logging" {
  service = "logging.googleapis.com"
}

# Service Account
resource "google_service_account" "monitoring" {
  account_id   = "monitoring-sa"
  display_name = "Monitoring Service Account"
}

resource "google_project_iam_member" "monitoring_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.monitoring.email}"
}

resource "google_project_iam_member" "monitoring_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.monitoring.email}"
}

# Storage Buckets for Logs
resource "google_storage_bucket" "application_logs" {
  name          = "${var.project_id}-logs-application"
  location      = var.region
  force_destroy = false

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket" "error_logs" {
  name          = "${var.project_id}-logs-errors"
  location      = var.region
  force_destroy = false

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

# BigQuery Datasets
resource "google_bigquery_dataset" "security_logs" {
  dataset_id                 = "security_logs"
  location                   = var.region
  default_table_expiration_ms = 31536000000  # 1 year
}

resource "google_bigquery_dataset" "performance_logs" {
  dataset_id                 = "performance_logs"
  location                   = var.region
  default_table_expiration_ms = 15552000000  # 6 months
}

# Log Sinks (from logging.tf)
# Alert Policies (from monitoring_alerts.tf)
# Dashboards (apply JSON files via gcloud)

# Output monitoring URLs
output "monitoring_dashboard_url" {
  value = "https://console.cloud.google.com/monitoring/dashboards?project=${var.project_id}"
}

output "logging_url" {
  value = "https://console.cloud.google.com/logs/query?project=${var.project_id}"
}

output "alert_policies_url" {
  value = "https://console.cloud.google.com/monitoring/alerting/policies?project=${var.project_id}"
}
```

---

## 実装チェックリスト

### バックエンド実装
- [ ] `backend/app/core/logging_config.py` - 構造化ログ設定
- [ ] `backend/app/middleware/logging_middleware.py` - リクエストログミドルウェア
- [ ] `backend/app/services/phase_logger.py` - フェーズログ実装
- [ ] `backend/app/core/security_logger.py` - セキュリティログ実装
- [ ] `backend/app/core/metrics_client.py` - メトリクスクライアント
- [ ] `backend/app/services/generation_metrics.py` - 生成メトリクス
- [ ] `backend/app/services/user_metrics.py` - ユーザーメトリクス
- [ ] `backend/app/services/business_metrics.py` - ビジネスメトリクス

### インフラ設定
- [ ] `scripts/setup-log-sinks.sh` - ログシンク設定スクリプト
- [ ] `scripts/setup-alert-policies.sh` - アラートポリシー作成スクリプト
- [ ] `scripts/setup-monitoring-complete.sh` - 完全セットアップスクリプト
- [ ] `terraform/logging.tf` - Terraformログ設定
- [ ] `terraform/monitoring_alerts.tf` - Terraformアラート設定
- [ ] `terraform/monitoring_complete.tf` - Terraform完全設定

### ダッシュボード
- [ ] `dashboards/operations-dashboard.json` - Operationsダッシュボード
- [ ] `dashboards/business-dashboard.json` - Businessダッシュボード
- [ ] `dashboards/security-dashboard.json` - Securityダッシュボード（作成推奨）

### 環境変数
- [ ] `GCP_PROJECT_ID` - GCPプロジェクトID
- [ ] `SLACK_WEBHOOK_URL` - Slack Webhook URL
- [ ] `APP_VERSION` - アプリケーションバージョン
- [ ] `ENVIRONMENT` - 環境名（development/staging/production）

---

## 関連ドキュメント

- [監視・ログ・アラート設計](./monitoring.md) - 高レベル設計
- [デプロイメント手順](./deployment-procedures.md) - デプロイ実装
- [インフラ概要](./infrastructure-overview.md) - インフラ設計
- [エラーハンドリング仕様](../02-architecture/error-handling-spec.md) - エラー処理

---

**実装承認**
- バックエンド開発者: TBD 日付: TBD
- SREエンジニア: TBD 日付: TBD
- DevOpsエンジニア: TBD 日付: TBD
