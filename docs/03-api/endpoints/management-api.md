---
document_id: "API-MGMT-001"
title: "データ管理API"
version: "3.0"
date_created: "2025-01-20"
date_updated: "2025-09-30"
status: "active"
category: "api"
document_type: "api-endpoint-specification"
tags: ["data-management", "manga-crud", "user-profile", "system-monitoring", "admin-dashboard", "performance-metrics"]
parent_doc: "API-README-001"
related_docs: ["API-OVERVIEW-001", "API-AUTH-001", "API-GEN-001"]
target_audience: ["api-developer", "backend-developer", "devops-engineer", "admin"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# データ管理API

> **TL;DR**: 作品管理・ユーザー管理・システム監視API。作品CRUD（一覧・詳細・更新・削除）、ユーザープロフィール・利用状況、システムヘルスチェック・ダッシュボード・パフォーマンス監視で構成。管理者向け詳細統計・アラート・設定更新機能。無料30日・有料1年データ保持、7種類エラーコード体系。

[← メインページへ戻る](../README.md) | [← API概要](../api-overview.md)

---

## 概要

作品管理、ユーザー管理、システム監視機能を提供するAPIです。完成した漫画作品の管理、ユーザーアカウント情報、利用状況統計、システムヘルスチェック機能を含みます。

---

## エンドポイント一覧

### 作品管理
| メソッド | エンドポイント | 説明 | 認証 |
|--------|------------|------|------|
| GET | `/api/v1/manga` | 作品一覧取得 | 必須 |
| GET | `/api/v1/manga/{manga_id}` | 作品詳細取得 | 必須 |
| PUT | `/api/v1/manga/{manga_id}` | 作品情報更新 | 必須 |
| DELETE | `/api/v1/manga/{manga_id}` | 作品削除 | 必須 |

### ユーザー管理
| メソッド | エンドポイント | 説明 | 認証 |
|--------|------------|------|------|
| GET | `/api/v1/user/profile` | プロフィール取得 | 必須 |
| GET | `/api/v1/user/usage` | 利用状況取得 | 必須 |

### システム管理
| メソッド | エンドポイント | 説明 | 認証 |
|--------|------------|------|------|
| GET | `/api/v1/health` | ヘルスチェック | 不要 |
| GET | `/api/v1/system/capabilities` | システム機能情報 | 不要 |
| GET | `/api/v1/system/dashboard` | システムダッシュボード | 管理者 |
| GET | `/api/v1/system/performance/summary` | パフォーマンス概要 | 管理者 |

---

## 作品管理API

### GET /api/v1/manga

ユーザーの作品一覧を取得

#### クエリパラメータ

```
?page=1
&limit=20
&sort=created_at|updated_at|title
&order=asc|desc
&status=all|completed|processing|failed
```

#### レスポンス (200 OK)

```json
{
  "items": [
    {
      "manga_id": "uuid",
      "title": "string",
      "status": "completed",
      "pages": 20,
      "style": "anime",
      "created_at": "ISO8601",
      "updated_at": "ISO8601",
      "thumbnail_url": "string",
      "size_bytes": 10485760
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_items": 100,
    "total_pages": 5,
    "has_next": true,
    "has_previous": false
  }
}
```

### GET /api/v1/manga/{manga_id}

特定の作品詳細を取得

#### レスポンス (200 OK)

```json
{
  "manga_id": "uuid",
  "title": "string",
  "status": "completed",
  "metadata": {
    "pages": 20,
    "style": "anime",
    "characters_count": 3,
    "word_count": 5000,
    "processing_time_seconds": 480
  },
  "files": {
    "pdf_url": "string (signed URL)",
    "webp_urls": ["string"],
    "thumbnail_url": "string"
  },
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "expires_at": "ISO8601"
}
```

### PUT /api/v1/manga/{manga_id}

作品情報を更新

#### リクエスト

```json
{
  "title": "string (optional)",
  "description": "string (optional)",
  "tags": ["string"],
  "visibility": "private|public|unlisted"
}
```

#### レスポンス (200 OK)

```json
{
  "manga_id": "uuid",
  "updated_fields": ["title", "tags"],
  "updated_at": "ISO8601"
}
```

### DELETE /api/v1/manga/{manga_id}

作品を削除

#### レスポンス (204 No Content)

```
(No body)
```

---

## ユーザー管理API

### GET /api/v1/user/profile

ユーザープロフィール取得

#### レスポンス (200 OK)

```json
{
  "user_id": "string",
  "email": "string",
  "display_name": "string",
  "account_type": "free|premium",
  "quota": {
    "daily_limit": 3,
    "daily_used": 0,
    "monthly_limit": 90,
    "monthly_used": 15,
    "reset_at": "ISO8601"
  },
  "statistics": {
    "total_manga_created": 10,
    "total_pages_generated": 200,
    "average_processing_time": 450
  },
  "created_at": "ISO8601"
}
```

### GET /api/v1/user/usage

利用状況取得

#### レスポンス (200 OK)

```json
{
  "current_period": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "manga_created": 15,
    "api_calls": 450,
    "storage_used_bytes": 52428800
  },
  "daily_usage": [
    {
      "date": "2025-01-20",
      "manga_created": 1,
      "api_calls": 25,
      "processing_time_seconds": 480,
      "architecture": "monolithic",
      "performance_improvement": "40% faster than microservices"
    }
  ],
  "quota_status": {
    "daily_remaining": 2,
    "monthly_remaining": 75,
    "next_reset": "ISO8601"
  }
}
```

---

## システム管理API

### GET /api/v1/health

ヘルスチェック

#### レスポンス (200 OK)

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "ISO8601",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "storage": "healthy",
    "ai_api": "healthy"
  }
}
```

### GET /api/v1/system/capabilities

システム機能情報

#### レスポンス (200 OK)

```json
{
  "supported_styles": ["realistic", "anime", "cartoon", "sketch", "watercolor"],
  "max_pages": 100,
  "max_text_length": 50000,
  "max_characters": 5,
  "languages": ["ja", "en"],
  "file_formats": ["pdf", "webp"],
  "processing_time_estimate": {
    "per_1000_chars": 96,
    "base_time": 300
  }
}
```

### GET /api/v1/system/dashboard

システムダッシュボード取得（管理者のみ）

#### レスポンス (200 OK)

```json
{
  "system_overview": {
    "uptime_seconds": 86400,
    "cpu_usage": 45.2,
    "memory_usage": 68.5,
    "disk_usage": 12.3,
    "active_connections": 142
  },
  "generation_stats": {
    "total_generations_today": 245,
    "average_processing_time": 450,
    "success_rate": 0.97,
    "queue_length": 5
  },
  "ai_services": {
    "vertex_ai": {
      "status": "healthy",
      "response_time_ms": 850,
      "quota_remaining": 0.85
    }
  }
}
```

### GET /api/v1/system/health

詳細システムヘルスチェック

#### レスポンス (200 OK)

```json
{
  "status": "healthy",
  "components": {
    "api": "healthy",
    "database": "healthy",
    "redis": "healthy",
    "websocket": "healthy"
  },
  "version": "1.0",
  "timestamp": "ISO8601"
}
```

### GET /api/v1/system/performance/summary

パフォーマンス概要

#### レスポンス (200 OK)

```json
{
  "processing_performance": {
    "average_time_per_phase": {
      "phase_1": 12.5,
      "phase_2": 18.3,
      "phase_3": 22.1,
      "phase_4": 8.7,
      "phase_5": 156.2,
      "phase_6": 45.3,
      "phase_7": 32.8
    },
    "total_average_time": 295.9
  },
  "system_resources": {
    "cpu_usage": 45.2,
    "memory_usage": 68.5,
    "concurrent_requests": 12
  }
}
```

### GET /api/v1/system/performance/report

詳細パフォーマンスレポート生成

#### レスポンス (200 OK)

```json
{
  "report_id": "uuid",
  "generated_at": "ISO8601",
  "period": {
    "start": "ISO8601",
    "end": "ISO8601"
  },
  "detailed_metrics": {
    "phase_performance": {
      "phase_1": {
        "total_executions": 1250,
        "average_time": 12.5,
        "success_rate": 0.99,
        "error_rate": 0.01
      }
    },
    "resource_utilization": {
      "peak_cpu": 78.5,
      "peak_memory": 89.2,
      "average_concurrent_requests": 15.3
    }
  }
}
```

### POST /api/v1/system/configuration/update

システム設定更新（管理者のみ）

#### リクエスト

```json
{
  "settings": {
    "phase_timeouts": {
      "phase_5": 250
    },
    "parallel_processing": false
  },
  "apply_immediately": true
}
```

#### レスポンス (200 OK)

```json
{
  "configuration_updated": true,
  "applied_settings": {
    "phase_timeouts": {
      "phase_5": 250
    },
    "parallel_processing": false
  },
  "restart_required": false
}
```

### GET /api/v1/system/alerts

システムアラート取得（管理者のみ）

#### レスポンス (200 OK)

```json
{
  "active_alerts": [
    {
      "alert_id": "uuid",
      "severity": "warning",
      "component": "vertex_ai",
      "message": "API response time elevated",
      "created_at": "ISO8601",
      "acknowledged": false
    }
  ],
  "alert_summary": {
    "critical": 0,
    "warning": 2,
    "info": 5
  }
}
```

### GET /api/v1/system/statistics

システム統計情報（管理者のみ）

#### レスポンス (200 OK)

```json
{
  "usage_stats": {
    "total_manga_generated": 15420,
    "total_users": 2850,
    "average_sessions_per_day": 145,
    "peak_concurrent_users": 89
  },
  "performance_stats": {
    "average_processing_time": 295.9,
    "fastest_generation": 180.2,
    "success_rate_7_days": 0.97
  },
  "resource_stats": {
    "storage_used_gb": 124.5,
    "bandwidth_used_gb": 856.3,
    "ai_api_calls_today": 1240
  }
}
```

---

## 管理エラーコード

| コード | 説明 | HTTPステータス |
|------|------|---------------|
| RES_001 | 作品が見つからない | 404 |
| RES_002 | 作品アクセス権限なし | 403 |
| RES_003 | 作品削除失敗 | 500 |
| RATE_001 | 日次利用制限到達 | 429 |
| RATE_002 | 月次利用制限到達 | 429 |
| SRV_001 | システム内部エラー | 500 |
| SRV_002 | メンテナンス中 | 503 |

---

## データ保持ポリシー

### 作品データ
- **無料ユーザー**: 作成から30日間
- **有料ユーザー**: 作成から1年間
- **削除前通知**: 7日前にメール通知

### ユーザーデータ
- **アカウント情報**: アカウント削除まで永続
- **利用統計**: 2年間保持
- **ログデータ**: 90日間保持

### システムログ
- **アクセスログ**: 30日間
- **エラーログ**: 180日間
- **監査ログ**: 7年間

---

## 関連リンク

- [認証API](auth-api.md)
- [漫画生成API](generation-api.md)
- [データモデル](../schemas/data-models.md)
- [API概要](../api-overview.md)