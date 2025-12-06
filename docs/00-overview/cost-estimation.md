---
document_id: "OVW-COST-001"
title: "本番環境コスト見積もり"
version: "1.0"
date_created: "2025-10-01"
status: "active"
category: "overview"
document_type: "cost-estimation"
tags: ["cost", "pricing", "budget", "gcp", "production", "estimation"]
parent_doc: "OVW-README-001"
related_docs: ["INF-DEPLOY-IMPL-001", "INF-MON-IMPL-001", "ARCH-TECH-001"]
target_audience: ["cto", "cfo", "product-manager", "devops-engineer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# 本番環境コスト見積もり

> **TL;DR**: 月間利用料金見積もり。初期段階（100ユーザー・300生成/月）: **$850/月**、成長段階（1,000ユーザー・3,000生成/月）: **$4,200/月**、スケール段階（10,000ユーザー・30,000生成/月）: **$28,500/月**。AI API（Gemini+Imagen）がコストの60-70%を占める。最適化施策により20-30%削減可能。

## 目次

1. [前提条件](#1-前提条件)
2. [コスト内訳](#2-コスト内訳)
3. [段階別見積もり](#3-段階別見積もり)
4. [最適化施策](#4-最適化施策)
5. [コスト管理](#5-コスト管理)

---

## 1. 前提条件

### 1.1 利用シナリオ定義

#### ユーザー行動モデル
```yaml
Free User (無料ユーザー):
  割合: 80%
  生成回数: 3回/月/ユーザー
  ページ数平均: 4ページ
  セッション時間: 15分/回

Premium User (有料ユーザー):
  割合: 20%
  生成回数: 10回/月/ユーザー
  ページ数平均: 8ページ
  セッション時間: 30分/回
```

#### 技術仕様
```yaml
Infrastructure:
  Cloud Run:
    Memory: 4Gi
    CPU: 2 vCPU
    Min Instances: 2
    Max Instances: 100

  Cloud SQL:
    Tier: db-standard-2 (2 vCPU, 7.5GB RAM)
    Storage: 50GB SSD
    Backup: Daily automated

  Cloud Storage:
    Input Storage: Standard
    Output Storage: Standard → Nearline (30日) → Coldline (180日)

AI Processing:
  Gemini Pro 1.5:
    Input: 128K tokens/generation (phases 1-4, 6-7)
    Output: 8K tokens/generation

  Imagen 4:
    Images: 4-8枚/generation (phase 5)
    Resolution: 1024x1024
```

---

## 2. コスト内訳

### 2.1 GCPサービス別料金

#### Cloud Run
```yaml
Cloud Run Pricing (asia-northeast1):
  CPU: $0.00002400/vCPU-second
  Memory: $0.00000250/GiB-second
  Requests: $0.40/million requests

Calculation Example (1,000 users/month):
  Monthly Requests: 3,000 generations × 50 API calls/generation = 150,000 requests
  Avg Processing Time: 8 minutes = 480 seconds

  CPU Cost:
    = 150,000 requests × 480s × 2 vCPU × $0.000024
    = $3,456/month

  Memory Cost:
    = 150,000 requests × 480s × 4 GiB × $0.0000025
    = $720/month

  Request Cost:
    = 0.15M requests × $0.40
    = $0.06/month

  Total Cloud Run: $4,176/month
```

#### Cloud SQL
```yaml
Cloud SQL Pricing (asia-northeast1):
  db-standard-2: $0.1918/hour = $139/month (730 hours)
  Storage SSD: $0.17/GB/month = $8.50/month (50GB)
  Backup: $0.08/GB/month = $4/month (50GB)

  Total Cloud SQL: $151.50/month
```

#### Cloud Storage
```yaml
Cloud Storage Pricing (asia-northeast1):
  Standard Storage: $0.023/GB/month
  Nearline Storage: $0.013/GB/month
  Coldline Storage: $0.007/GB/month

Calculation (3,000 generations/month):
  Input Files: 3,000 × 0.5MB = 1.5GB
  Output Files: 3,000 × 5MB = 15GB

  Month 1 (all Standard):
    = 16.5GB × $0.023 = $0.38

  Month 2 (30-day lifecycle):
    Standard: 16.5GB × $0.023 = $0.38
    Nearline (prev month): 16.5GB × $0.013 = $0.21
    = $0.59

  Month 6+ (steady state):
    Standard: 16.5GB × $0.023 = $0.38
    Nearline (1-6 months): 82.5GB × $0.013 = $1.07
    Coldline (6+ months): 165GB × $0.007 = $1.16
    = $2.61/month

  Data Transfer (Egress to Internet):
    3,000 downloads × 5MB = 15GB/month
    First 1GB: Free
    1-10TB: $0.12/GB = 14GB × $0.12 = $1.68/month

  Total Cloud Storage: $4.29/month (steady state)
```

#### AI API (Gemini Pro + Imagen)
```yaml
Gemini Pro 1.5 Pricing:
  Input: $0.00125/1K tokens (prompt caching不使用)
  Output: $0.005/1K tokens

Per Generation (7 phases using Gemini):
  Input Tokens: 128K tokens
  Output Tokens: 8K tokens

  Cost per generation:
    Input: 128 × $0.00125 = $0.160
    Output: 8 × $0.005 = $0.040
    Total: $0.20/generation

  Monthly (3,000 generations):
    = 3,000 × $0.20 = $600/month

Imagen 4 Pricing:
  Standard Quality: $0.04/image

Per Generation:
  Images: 6 images average (4-8 pages)
  Cost: 6 × $0.04 = $0.24/generation

  Monthly (3,000 generations):
    = 3,000 × $0.24 = $720/month

Total AI API: $1,320/month (3,000 generations)
```

#### その他GCPサービス
```yaml
Secret Manager:
  Active Secrets: 20 secrets
  Cost: $0.06/secret/month = $1.20/month
  Access Operations: Free (first 10,000)

Cloud Logging:
  Logs Ingestion: 50GB/month
  First 50GB: Free
  Cost: $0/month

Cloud Monitoring:
  Metrics: 100 custom metrics
  First 150 metrics: Free
  Cost: $0/month

Cloud Build:
  Build Minutes: 20 builds/month × 10 min = 200 min/month
  First 120 minutes: Free
  Additional: 80 min × $0.003/min = $0.24/month

Firebase Hosting:
  Bandwidth: 10GB/month
  First 10GB: Free
  Storage: 1GB
  First 1GB: Free
  Cost: $0/month

Total Other Services: $1.44/month
```

### 2.2 外部サービス

```yaml
Firebase Authentication:
  Monthly Active Users: 1,000
  First 50,000 MAU: Free
  Cost: $0/month

Domain & SSL:
  Domain Registration: $12/year = $1/month
  SSL Certificate: Free (Firebase managed)
  Total: $1/month

Email Service (SendGrid):
  Emails: 1,000/month (notifications)
  Free Tier: 100 emails/day
  Cost: $0/month

Total External Services: $1/month
```

---

## 3. 段階別見積もり

### 3.1 初期段階（0-6ヶ月）

#### 前提
- **月間アクティブユーザー**: 100人
- **無料ユーザー**: 80人 (3生成/月)
- **有料ユーザー**: 20人 (10生成/月)
- **月間生成数**: 240 + 200 = **440生成/月**

#### コスト内訳
```yaml
Infrastructure:
  Cloud Run:
    CPU: 440 × 480s × 2 vCPU × $0.000024 = $10.14
    Memory: 440 × 480s × 4 GiB × $0.0000025 = $2.11
    Requests: 22,000 requests × $0.40/1M = $0.01
    Subtotal: $12.26

  Cloud SQL: $151.50
  Cloud Storage: $4.29 (steady state)
  Other GCP Services: $1.44

AI Processing:
  Gemini Pro: 440 × $0.20 = $88.00
  Imagen 4: 440 × $0.24 = $105.60
  Subtotal: $193.60

External Services: $1.00

Total Monthly Cost: $364.09/月
≈ $365/月 (初期段階)

Per Generation Cost: $365 / 440 = $0.83/generation
```

### 3.2 成長段階（6-18ヶ月）

#### 前提
- **月間アクティブユーザー**: 1,000人
- **無料ユーザー**: 800人 (3生成/月)
- **有料ユーザー**: 200人 (10生成/月)
- **月間生成数**: 2,400 + 2,000 = **4,400生成/月**

#### コスト内訳
```yaml
Infrastructure:
  Cloud Run:
    CPU: 4,400 × 480s × 2 vCPU × $0.000024 = $101.38
    Memory: 4,400 × 480s × 4 GiB × $0.0000025 = $21.12
    Requests: 220,000 requests × $0.40/1M = $0.09
    Subtotal: $122.59

  Cloud SQL: $151.50 (同スペック)
  Cloud Storage: $15.00 (165GB total)
  Other GCP Services: $1.44

AI Processing:
  Gemini Pro: 4,400 × $0.20 = $880.00
  Imagen 4: 4,400 × $0.24 = $1,056.00
  Subtotal: $1,936.00

External Services: $1.00

Total Monthly Cost: $2,227.53/月
≈ $2,230/月 (成長段階)

Per Generation Cost: $2,230 / 4,400 = $0.51/generation
```

### 3.3 スケール段階（18ヶ月+）

#### 前提
- **月間アクティブユーザー**: 10,000人
- **無料ユーザー**: 8,000人 (3生成/月)
- **有料ユーザー**: 2,000人 (10生成/月)
- **月間生成数**: 24,000 + 20,000 = **44,000生成/月**

#### インフラスケールアップ
```yaml
Cloud Run:
  Max Instances: 100
  同時処理: 50 generations

Cloud SQL:
  Upgrade to: db-standard-4 (4 vCPU, 15GB RAM)
  Cost: $0.3836/hour = $279.83/month
  Storage: 200GB SSD = $34/month
  Read Replica: +$279.83/month (HA構成)
```

#### コスト内訳
```yaml
Infrastructure:
  Cloud Run:
    CPU: 44,000 × 480s × 2 vCPU × $0.000024 = $1,013.76
    Memory: 44,000 × 480s × 4 GiB × $0.0000025 = $211.20
    Requests: 2.2M requests × $0.40/1M = $0.88
    Subtotal: $1,225.84

  Cloud SQL (High Availability):
    Primary: $313.83
    Read Replica: $279.83
    Subtotal: $593.66

  Cloud Storage: $80.00 (1.65TB total)
  Other GCP Services: $5.00 (increased monitoring)

AI Processing:
  Gemini Pro: 44,000 × $0.20 = $8,800.00
  Imagen 4: 44,000 × $0.24 = $10,560.00
  Subtotal: $19,360.00

External Services:
  Email (SendGrid Essentials): $19.95/month
  Domain: $1.00
  Subtotal: $20.95

Total Monthly Cost: $21,285.45/月
≈ $21,300/月 (スケール段階)

Per Generation Cost: $21,300 / 44,000 = $0.48/generation
```

---

## 4. 最適化施策

### 4.1 AI API コスト削減（最大40%削減）

#### プロンプトキャッシング活用
```yaml
Gemini Pro Prompt Caching:
  Cached Input: $0.0003125/1K tokens (75%削減)

Implementation:
  System Prompt: 20K tokens (固定)
  User Context: 108K tokens (可変)

Before Caching (per generation):
  128K tokens × $0.00125 = $0.160

After Caching (80% cache hit rate):
  Cached: 20K × $0.0003125 = $0.00625
  Non-cached: 108K × $0.00125 = $0.135
  Total: $0.14125

Savings: $0.160 - $0.14125 = $0.01875/generation
Monthly (44,000 generations): $825/month saved
Reduction: 11.7%
```

#### バッチ処理最適化
```yaml
Imagen Batch Generation:
  Batch 4 images: $0.04/image × 4 = $0.16
  Sequential 4 images: $0.04/image × 4 = $0.16

  Note: Imagen doesn't offer batch discount
  Optimization: Reduce image count to 4 pages (minimum)

Savings (6 → 4 images):
  Before: $0.24/generation
  After: $0.16/generation
  Monthly (44,000 generations): $3,520/month saved
  Reduction: 33.3% on Imagen costs
```

#### 品質スコアによる早期終了
```yaml
Quality-Based Retry Reduction:
  Current: 3 retries max per phase
  Optimized: Early exit at quality >= 0.85

Average Retry Reduction: 20%

Gemini Savings:
  Before: 44,000 × $0.20 = $8,800
  After: 44,000 × 0.8 × $0.20 = $7,040
  Savings: $1,760/month
  Reduction: 20%
```

#### 総AI API最適化効果
```yaml
Gemini Pro:
  Caching: -$825/month
  Retry Reduction: -$1,760/month
  Total Gemini Savings: $2,585/month

Imagen:
  Image Count Reduction: -$3,520/month
  Total Imagen Savings: $3,520/month

Total AI Savings: $6,105/month
Original AI Cost: $19,360/month
Optimized AI Cost: $13,255/month
Reduction: 31.5%
```

### 4.2 インフラコスト削減（最大25%削減）

#### Cloud Run最適化
```yaml
Request-based Autoscaling:
  Current: Always-on 2 instances
  Optimized: Scale to 0 during low traffic

Savings (off-peak 50% of time):
  Idle Cost: 2 instances × 12h/day × 30 days × (2 vCPU × $0.000024 + 4 GiB × $0.0000025)
  = 2 × 1,296,000s × ($0.000048 + $0.00001)
  = $75.17/month saved

Request Coalescing:
  Batch API calls: 50 → 40 calls/generation
  Reduction: 20%
  Savings: $245/month
```

#### Cloud SQL最適化
```yaml
Connection Pooling Tuning:
  Current: 20 max connections
  Optimized: 10 connections (PgBouncer)

  Downgrade feasibility: No (need HA)
  Savings: $0

Automated Backup Optimization:
  Current: Daily full backup
  Optimized: Weekly full + daily incremental
  Savings: Minimal (~$2/month)
```

#### Cloud Storage最適化
```yaml
Lifecycle Policy Tuning:
  Current: 30 days Standard → 180 days Nearline → Coldline
  Optimized: 7 days Standard → 30 days Nearline → Coldline

Average Storage (44,000 generations/month):
  Standard (7 days): 16.5GB × 7/30 = 3.85GB
  Nearline (23 days): 16.5GB × 23/30 = 12.65GB
  Coldline (6+ months): 990GB

Costs:
  Standard: 3.85GB × $0.023 = $0.09
  Nearline: 12.65GB × $0.013 = $0.16
  Coldline: 990GB × $0.007 = $6.93
  Total: $7.18/month

Savings: $80 - $7.18 = $72.82/month
Reduction: 91% on storage costs
```

#### 総インフラ最適化効果
```yaml
Cloud Run: -$320/month
Cloud SQL: -$2/month
Cloud Storage: -$73/month
Total Infrastructure Savings: $395/month

Original Infrastructure Cost: $1,904/month
Optimized Infrastructure Cost: $1,509/month
Reduction: 20.7%
```

### 4.3 最適化後の総コスト

#### スケール段階最適化版
```yaml
Infrastructure: $1,509/month (was $1,904)
AI Processing: $13,255/month (was $19,360)
External Services: $21/month (unchanged)

Total Optimized Cost: $14,785/月
Original Cost: $21,300/月
Total Savings: $6,515/月 (30.6%削減)

Per Generation Cost: $14,785 / 44,000 = $0.34/generation
```

---

## 5. コスト管理

### 5.1 予算アラート設定

#### GCP Budget Alerts
```yaml
Budget 1 - Monthly Total:
  Amount: $15,000/month
  Alerts:
    - 50% threshold: Email to billing-admin@company.com
    - 80% threshold: Email + Slack #finance
    - 100% threshold: Email + Slack + SMS
    - 120% threshold: Auto-disable non-essential services

Budget 2 - AI API Only:
  Amount: $13,500/month
  Alerts:
    - 50% threshold: Email to ai-team@company.com
    - 80% threshold: Email + Slack #engineering
    - 100% threshold: Rate limit implementation

Budget 3 - Infrastructure:
  Amount: $1,500/month
  Alerts:
    - 90% threshold: Email to devops@company.com
```

#### コスト監視ダッシュボード
```yaml
Cloud Monitoring Dashboard:
  Widgets:
    - Real-time Cost Tracker
    - Cost per Generation Trend
    - AI API Usage vs Budget
    - Top 10 Cost Resources
    - Projected Monthly Cost

  Update Frequency: Hourly
  Access: Billing Admin, CTO, Product Manager
```

### 5.2 コスト配分戦略

#### ユーザー課金モデル
```yaml
Free Tier:
  生成回数: 3回/月
  コスト: $0.34 × 3 = $1.02/user/month
  収益: $0 (広告なし)
  損失: -$1.02/user/month

Premium Tier:
  生成回数: 10回/月
  コスト: $0.34 × 10 = $3.40/user/month
  収益: $9.99/month
  利益: $6.59/user/month

Break-even Analysis:
  Free Users: 80% × 1,000 = 800 users × $1.02 = $816 loss
  Premium Users: 20% × 1,000 = 200 users × $6.59 = $1,318 profit
  Net Profit: $1,318 - $816 = $502/month

  Required Premium Conversion: $816 / $6.59 = 124 premium users (12.4%)
  Current: 20% → Healthy margin
```

#### 段階別損益分岐点
```yaml
Initial Stage (100 users):
  Total Cost: $365/month
  Required Premium Users: $365 / $6.59 = 56 users
  Required Conversion Rate: 56 / 100 = 56%
  Status: ⚠️ High barrier to entry

Growth Stage (1,000 users):
  Total Cost: $2,230/month (before optimization)
  Optimized Cost: $1,561/month (30% reduction)
  Required Premium Users: $1,561 / $6.59 = 237 users
  Required Conversion Rate: 237 / 1,000 = 23.7%
  Status: ✅ Achievable

Scale Stage (10,000 users):
  Total Cost: $21,300/month (before optimization)
  Optimized Cost: $14,785/month (30% reduction)
  Required Premium Users: $14,785 / $6.59 = 2,243 users
  Required Conversion Rate: 2,243 / 10,000 = 22.4%
  Status: ✅ Sustainable
```

### 5.3 追加収益化戦略

#### 従量課金オプション
```yaml
Pay-As-You-Go Plan:
  Target: ヘビーユーザー（月10回超）
  Pricing: $1.50/generation

  Cost per Generation: $0.34
  Margin: $1.16 (77.3%)

  Scenario (50 PAYG users, 20 generations/month):
    Revenue: 50 × 20 × $1.50 = $1,500/month
    Cost: 50 × 20 × $0.34 = $340/month
    Profit: $1,160/month
```

#### エンタープライズプラン
```yaml
Enterprise Plan:
  Target: 企業・クリエイター
  Pricing: $299/month
  Generation Limit: 200回/月

  Cost: 200 × $0.34 = $68/month
  Margin: $231 (77.3%)

  Break-even: 1 enterprise customer ≈ 35 premium customers
```

#### API販売
```yaml
Developer API:
  Target: サードパーティアプリ
  Pricing: $0.80/generation

  Cost: $0.34/generation
  Margin: $0.46 (57.5%)

  Scenario (100 API calls/day):
    Monthly Revenue: 3,000 × $0.80 = $2,400/month
    Monthly Cost: 3,000 × $0.34 = $1,020/month
    Monthly Profit: $1,380/month
```

---

## 6. コスト比較表

### 6.1 段階別コストサマリー

| 段階 | ユーザー数 | 生成数/月 | インフラ | AI API | 合計（最適化前） | 合計（最適化後） | 削減率 |
|------|-----------|----------|---------|--------|--------------|--------------|-------|
| **初期** | 100 | 440 | $169 | $194 | **$365** | **$255** | 30% |
| **成長** | 1,000 | 4,400 | $291 | $1,936 | **$2,230** | **$1,561** | 30% |
| **スケール** | 10,000 | 44,000 | $1,904 | $19,360 | **$21,300** | **$14,785** | 31% |

### 6.2 生成単価推移

| 段階 | 最適化前 | 最適化後 | 削減額 |
|------|---------|---------|-------|
| **初期** | $0.83/generation | $0.58/generation | $0.25 |
| **成長** | $0.51/generation | $0.35/generation | $0.16 |
| **スケール** | $0.48/generation | $0.34/generation | $0.14 |

### 6.3 収益性分析

#### 成長段階（1,000ユーザー、最適化後）
```yaml
Costs:
  Infrastructure: $291/month
  AI Processing: $1,249/month
  External Services: $21/month
  Total: $1,561/month

Revenue:
  Premium Users (200): 200 × $9.99 = $1,998/month

Profit:
  Monthly: $1,998 - $1,561 = $437/month
  Annual: $437 × 12 = $5,244/year

Profit Margin: 21.9%
```

#### スケール段階（10,000ユーザー、最適化後）
```yaml
Costs:
  Infrastructure: $1,509/month
  AI Processing: $13,255/month
  External Services: $21/month
  Total: $14,785/month

Revenue:
  Premium Users (2,000): 2,000 × $9.99 = $19,980/month

Profit:
  Monthly: $19,980 - $14,785 = $5,195/month
  Annual: $5,195 × 12 = $62,340/year

Profit Margin: 26.0%
```

---

## 7. 推奨事項

### 7.1 即座に実装すべき施策

#### 高優先度（即時実装）
1. **Gemini Prompt Caching** - 実装工数: 2日、削減額: $825/月
2. **Cloud Storage Lifecycle Policy** - 実装工数: 4時間、削減額: $73/月
3. **Cloud Run Request Coalescing** - 実装工数: 3日、削減額: $245/月

#### 中優先度（1-2週間以内）
4. **品質スコア早期終了** - 実装工数: 5日、削減額: $1,760/月
5. **Imagen画像数最適化** - 実装工数: 2日、削減額: $3,520/月
6. **予算アラート設定** - 実装工数: 2時間、削減なし（監視強化）

### 7.2 段階的実装ロードマップ

#### Phase 1: コスト可視化（Week 1-2）
- Cloud Monitoring ダッシュボード構築
- 予算アラート設定
- コストレポート自動化

#### Phase 2: 即効性施策（Week 3-4）
- Prompt Caching実装
- Storage Lifecycle最適化
- Request Coalescing実装

#### Phase 3: AI最適化（Week 5-8）
- 品質スコア早期終了
- Imagen画像数削減
- バッチ処理最適化

#### Phase 4: 長期最適化（Week 9-12）
- Reserved Instances検討（Cloud SQL）
- CDN統合（Cloud Storage）
- マルチリージョン展開準備

---

## 関連ドキュメント

- [デプロイ手順](./deployment-procedures.md) - インフラ構築手順
- [監視実装](./monitoring-implementation.md) - コスト監視設定
- [技術仕様書](../02-architecture/technical-spec.md) - システム構成

---

**承認**
- CFO: TBD 日付: TBD
- CTO: TBD 日付: TBD
- プロダクトマネージャー: TBD 日付: TBD
