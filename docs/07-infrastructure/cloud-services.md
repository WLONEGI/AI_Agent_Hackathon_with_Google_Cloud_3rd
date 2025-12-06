---
document_id: "INF-CLD-001"
title: "クラウドサービス統合設計"
version: "2.0"
date_created: "2025-09-27"
date_updated: "2025-09-30"
status: "active"
category: "infrastructure"
document_type: "cloud-services-design"
tags: ["gcp", "aws", "vertex-ai", "cloud-run", "cloud-sql", "cloud-storage", "iam", "multi-cloud", "cost-optimization"]
parent_doc: "INF-README-001"
related_docs: ["INF-OVERVIEW-001", "INF-DEP-001", "INF-MON-001", "INF-OPT-001"]
target_audience: ["cloud-architect", "devops-engineer", "backend-developer", "cost-optimizer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# クラウドサービス統合設計

> **TL;DR**: GCP/AWSマルチクラウド統合設計。GCP主軸（Vertex AI・Cloud Run・Cloud SQL・Cloud Storage・IAM・Secret Manager）、AWSハイブリッド戦略、Firebase統合、外部APIサービス統合で構成。コスト最適化（30-40%削減目標）、自動スケーリング、セキュリティ設計。月額予算管理・アラート体系完備。

## ナビゲーション
- [← 親文書に戻る](./09.インフラ設計書.md)
- [← 監視・ログ設計](./monitoring.md)
- [← デプロイメント設計](./deployment.md)
- [← インフラ概要](./infrastructure-overview.md)

---

## 目次

- [1. Google Cloud Platform サービス](#1-google-cloud-platform-サービス)
  - [1.1 AI/ML サービス](#11-aiml-サービス)
  - [1.2 コンピュートサービス](#12-コンピュートサービス)
  - [1.3 データサービス](#13-データサービス)
  - [1.4 セキュリティサービス](#14-セキュリティサービス)
- [2. AWS サービス統合](#2-aws-サービス統合)
  - [2.1 ハイブリッドクラウド戦略](#21-ハイブリッドクラウド戦略)
  - [2.2 AWS AI サービス](#22-aws-ai-サービス)
  - [2.3 マルチクラウド管理](#23-マルチクラウド管理)
- [3. 外部API統合](#3-外部api統合)
  - [3.1 Google AI APIs](#31-google-ai-apis)
  - [3.2 Firebase サービス](#32-firebase-サービス)
  - [3.3 サードパーティサービス](#33-サードパーティサービス)
- [4. コスト最適化戦略](#4-コスト最適化戦略)
  - [4.1 リソース管理](#41-リソース管理)
  - [4.2 コスト監視](#42-コスト監視)
  - [4.3 自動スケーリング](#43-自動スケーリング)

---

## 1. Google Cloud Platform サービス

### 1.1 AI/ML サービス

#### Vertex AI 統合設計
```yaml
Vertex AI Configuration:
  Core Services:
    Gemini Pro:
      Model: gemini-1.5-pro
      Use Cases:
        - テキスト解析・物語構造分析
        - シーン分割・キャラクター抽出
        - セリフ配置・品質スコア算出
      Rate Limits:
        - 60 requests/minute
        - 1M tokens/minute
      Cost Optimization:
        - 入力トークン数制限 (max 8K tokens)
        - バッチ処理で効率化
        
    Imagen 4:
      Model: imagen-4.0
      Use Cases:
        - キャラクタービジュアル生成
        - シーン画像生成
        - スタイル一貫性維持
      Configuration:
        - Resolution: 1024x1024 (standard)
        - Quality: Standard (cost-optimized)
        - Safety filters: Enabled
      Rate Limits:
        - 60 images/minute
        - Quality queue priority
      Cost Management:
        - 生成数制限ユーザー当たり
        - キャッシュ機構で重複生成防止
        
  Regional Configuration:
    Primary Region: asia-northeast1 (Tokyo)
    Backup Region: us-central1
    
  Authentication:
    Service Account: vertex-ai-service@PROJECT_ID.iam.gserviceaccount.com
    Roles:
      - roles/aiplatform.user
      - roles/storage.objectAdmin
      
  Quotas & Limits:
    Project Level:
      - Gemini Pro: 1000 requests/day
      - Imagen: 500 generations/day
    User Level:
      - Free tier: 10 generations/day
      - Premium: 100 generations/day
```

#### AI サービス統合戦略
```yaml
AI Integration Architecture:
  Request Flow:
    1. Client Request:
       - Input validation & sanitization
       - Rate limiting check
       - Authentication verification
       
    2. AI Service Routing:
       - Text analysis: Gemini Pro
       - Image generation: Imagen 4
       - Quality assessment: Custom models
       
    3. Response Processing:
       - Result caching (Redis)
       - Quality score calculation
       - User feedback integration
       
    4. Error Handling:
       - Retry logic (exponential backoff)
       - Fallback mechanisms
       - Quota management
       
  Performance Optimization:
    Caching Strategy:
      - Similar prompts: 24-hour cache
      - Generated images: 7-day cache
      - Quality scores: 30-day cache
      
    Batch Processing:
      - Multiple phases in single request
      - Parallel API calls where possible
      - Request deduplication
      
  Quality Assurance:
    Content Filtering:
      - Input: Inappropriate content detection
      - Output: Quality threshold enforcement
      - Safety: Copyright infringement check
      
    Monitoring:
      - API response times
      - Success/failure rates
      - Cost per request
      - Quality score trends
```

### 1.2 コンピュートサービス

#### Cloud Run 最適化設定
```yaml
Cloud Run Optimization:
  Service Configuration:
    Environment: gen2
    CPU: 1-4 (auto-scaling based on load)
    Memory: 2-8Gi (auto-scaling based on load)
    Request Timeout: 900s (15 minutes for long AI processes)
    Concurrency: 50-100 (optimized for I/O bound work)
    
  Auto-scaling Rules:
    Min Instances: 1 (warm startup)
    Max Instances: 100 (cost control)
    Scale-up Threshold: CPU > 70% OR Memory > 80%
    Scale-down Delay: 300s (5 minutes cooldown)
    
  Resource Allocation by Service:
    api-gateway:
      CPU: 1
      Memory: 2Gi
      Concurrency: 100
      
    text-analysis:
      CPU: 2
      Memory: 4Gi
      Concurrency: 20
      
    image-generation:
      CPU: 4
      Memory: 8Gi
      Concurrency: 5
      
    quality-assessment:
      CPU: 2
      Memory: 4Gi
      Concurrency: 30
      
  Cost Optimization:
    CPU Allocation:
      - Development: 1 CPU (minimum cost)
      - Staging: 2 CPU (performance testing)
      - Production: Auto-scaling 1-4 CPU
      
    Memory Allocation:
      - Conservative: 2Gi baseline
      - AI processing: 4-8Gi as needed
      - Cache optimization: Redis integration
      
    Traffic Management:
      - Cold start optimization
      - Request routing optimization
      - Load balancer efficiency
```

### 1.3 データサービス

#### Cloud SQL 高可用性設計
```yaml
Cloud SQL Configuration:
  Primary Instance:
    Instance Type: db-standard-2
    Storage: 200GB SSD
    Backup Configuration:
      Automated Backup: Daily at 3 AM JST
      Point-in-time Recovery: 7 days
      Backup Retention: 30 days
      
  High Availability:
    Regional Persistence: Enabled
    Failover Replica: asia-northeast1-b
    Automatic Failover: Enabled
    
  Performance Optimization:
    Connection Pooling:
      Max Connections: 100
      Connection Pool Size: 20
      Idle Connection Timeout: 300s
      
    Query Optimization:
      Slow Query Log: Enabled
      Query Insights: Enabled
      Performance Schema: Enabled
      
  Security Configuration:
    SSL/TLS: Required
    Private IP: 10.0.2.5
    Authorized Networks: VPC only
    
  Monitoring & Alerting:
    Key Metrics:
      - Connection count (alert > 80)
      - CPU utilization (alert > 80%)
      - Memory utilization (alert > 85%)
      - Disk utilization (alert > 90%)
      - Query performance (alert slow queries > 1s)
```

#### Cloud Storage 最適化戦略
```yaml
Cloud Storage Optimization:
  Bucket Strategy:
    manga-input-data:
      Storage Class: Standard
      Location: asia-northeast1
      Lifecycle: 90 days → Delete
      Access: Private
      
    manga-output-images:
      Storage Class: Standard
      Location: asia-northeast1
      Lifecycle: 
        - 30 days → Nearline
        - 365 days → Coldline
      Access: Signed URLs
      CDN: Cloud CDN enabled
      
    manga-temp-data:
      Storage Class: Standard
      Location: asia-northeast1
      Lifecycle: 7 days → Delete
      Access: Private
      
  Performance Optimization:
    Upload Strategy:
      - Resumable uploads for large files
      - Parallel uploads for multiple files
      - Compression for text data
      
    Download Strategy:
      - Signed URLs with 1-hour expiry
      - Cloud CDN for global distribution
      - Range requests for large files
      
  Cost Management:
    Storage Class Selection:
      - Hot data: Standard (frequent access)
      - Warm data: Nearline (monthly access)
      - Cold data: Coldline (yearly access)
      - Archive data: Archive (rare access)
      
    Transfer Optimization:
      - Regional storage to minimize egress
      - Compression to reduce bandwidth
      - Efficient file formats (WebP for images)
```

### 1.4 セキュリティサービス

#### Identity and Access Management (IAM)
```yaml
IAM Security Strategy:
  Service Account Design:
    manga-api-service:
      Description: "Main API service account"
      Roles:
        - roles/cloudsql.client
        - roles/storage.objectAdmin
        - roles/secretmanager.secretAccessor
        - roles/cloudtasks.enqueuer
        
    manga-ai-service:
      Description: "AI processing service account"
      Roles:
        - roles/aiplatform.user
        - roles/storage.objectViewer
        - roles/monitoring.metricWriter
        
    manga-deployment:
      Description: "CI/CD deployment service account"
      Roles:
        - roles/run.developer
        - roles/storage.admin
        - roles/cloudbuild.builds.editor
        
  User Access Control:
    Developers:
      - roles/editor (development project)
      - roles/viewer (production project)
      
    DevOps:
      - roles/owner (development project)
      - roles/editor (production project)
      
    Support:
      - roles/viewer (all projects)
      - Custom role: Support access (limited operations)
      
  Security Policies:
    Organization Policies:
      - Compute VM external IP access: Denied
      - Cloud SQL external IP access: Denied
      - Storage public access: Denied
      
    Conditional Access:
      - IP address restrictions for admin access
      - Time-based access controls
      - Device-based access controls
```

#### Secret Manager 統合
```yaml
Secret Manager Configuration:
  Secret Categories:
    Database Secrets:
      manga-db-password:
        Description: "PostgreSQL root password"
        Rotation: Manual (quarterly)
        Access: manga-api-service
        
      manga-db-url:
        Description: "Database connection string"
        Rotation: As needed
        Access: manga-api-service
        
    API Keys:
      vertex-ai-key:
        Description: "Vertex AI service account key"
        Rotation: Automatic (90 days)
        Access: manga-ai-service
        
      firebase-config:
        Description: "Firebase configuration"
        Rotation: Manual (yearly)
        Access: manga-api-service
        
    Application Secrets:
      jwt-secret:
        Description: "JWT signing key"
        Rotation: Automatic (30 days)
        Access: manga-api-service
        
      encryption-key:
        Description: "Data encryption key"
        Rotation: Automatic (90 days)
        Access: manga-api-service
        
  Access Control:
    Principle of Least Privilege:
      - Service-specific access only
      - Version-specific access
      - Time-limited access tokens
      
    Audit and Monitoring:
      - All secret access logged
      - Unusual access patterns alerted
      - Regular access review
```

---

## 2. AWS サービス統合

### 2.1 ハイブリッドクラウド戦略

#### マルチクラウド考慮事項
```yaml
Multi-Cloud Strategy:
  Primary Cloud: Google Cloud Platform
    Rationale:
      - Superior AI/ML services (Vertex AI)
      - Integrated development ecosystem
      - Cost-effective for startup
      - Strong container orchestration
      
  Secondary Cloud: AWS (Future consideration)
    Use Cases:
      - Disaster recovery
      - Global expansion
      - Service-specific advantages
      - Compliance requirements
      
  Integration Points:
    Data Synchronization:
      - Cross-cloud backup strategy
      - Data replication for DR
      - Archive storage in AWS S3 Glacier
      
    Service Redundancy:
      - DNS failover (Route 53 → Cloud DNS)
      - CDN redundancy (CloudFront + Cloud CDN)
      - Monitoring redundancy (CloudWatch + Cloud Monitoring)
      
  Implementation Timeline:
    Phase 1 (Current): GCP-only
    Phase 2 (6 months): AWS backup/DR
    Phase 3 (12 months): Multi-cloud load distribution
    Phase 4 (18 months): Full multi-cloud optimization
```

### 2.2 AWS AI サービス

#### AWS AI サービス比較
```yaml
AWS AI Services Evaluation:
  Amazon Bedrock:
    Advantages:
      - Multiple foundation models available
      - Claude, Llama, Titan models
      - Competitive pricing
      - Good text generation capabilities
      
    Disadvantages:
      - Limited image generation compared to Imagen
      - Different API structure (migration cost)
      - Regional availability limitations
      
    Use Case Fit: 7/10
    
  Amazon Rekognition:
    Advantages:
      - Excellent image analysis
      - Content moderation capabilities
      - Copyright detection features
      
    Use Cases:
      - Image quality assessment
      - Content safety filtering
      - Copyright infringement detection
      
    Integration Priority: Medium
    
  Amazon Polly:
    Advantages:
      - High-quality text-to-speech
      - Multiple language support
      - Character voice generation
      
    Use Cases:
      - Accessibility features
      - Audio manga generation
      - Character voice synthesis
      
    Integration Priority: Low
    
  Hybrid AI Strategy:
    Current: GCP Vertex AI (primary)
    Future:
      - AWS Rekognition for content moderation
      - AWS Bedrock for text diversity
      - Cross-cloud AI redundancy
```

### 2.3 マルチクラウド管理

#### 統合管理プラットフォーム
```yaml
Multi-Cloud Management:
  Infrastructure as Code:
    Terraform Configuration:
      - Provider: google, aws
      - State: Remote (GCS + S3 backup)
      - Modules: Shared infrastructure patterns
      
    Terraform Structure:
      /terraform
        /modules
          /gcp-foundation
          /aws-foundation
          /monitoring
        /environments
          /development
          /staging
          /production
        /shared
          /variables.tf
          /outputs.tf
          
  Monitoring Integration:
    Unified Dashboard:
      - Grafana for cross-cloud metrics
      - Prometheus for data collection
      - AlertManager for unified alerting
      
    Data Flow:
      GCP Monitoring → Prometheus → Grafana
      AWS CloudWatch → Prometheus → Grafana
      
  Cost Management:
    Cross-Cloud Cost Tracking:
      - GCP: Cloud Billing API
      - AWS: Cost Explorer API
      - Unified reporting dashboard
      
    Budget Controls:
      - Shared budget policies
      - Cross-cloud cost allocation
      - Resource optimization recommendations
      
  Security and Compliance:
    Identity Federation:
      - Google Workspace SSO
      - AWS IAM Identity Center
      - Consistent access policies
      
    Audit and Compliance:
      - Unified audit logs
      - Cross-cloud security scanning
      - Compliance reporting automation
```

---

## 3. 外部API統合

### 3.1 Google AI APIs

#### API 統合アーキテクチャ
```yaml
Google AI API Integration:
  Vertex AI API:
    Base URL: https://asia-northeast1-aiplatform.googleapis.com
    Authentication: Service Account JSON key
    
    Endpoints:
      Text Generation:
        endpoint: /v1/projects/{project}/locations/{location}/publishers/google/models/gemini-1.5-pro:generateContent
        method: POST
        rate_limit: 60 requests/minute
        
      Image Generation:
        endpoint: /v1/projects/{project}/locations/{location}/publishers/google/models/imagen-4.0:predict
        method: POST
        rate_limit: 60 requests/minute
        
  Error Handling:
    Retry Strategy:
      - Exponential backoff: 1s, 2s, 4s, 8s
      - Max retries: 3
      - Jitter: ±50% random variance
      
    Error Types:
      400 Bad Request: Input validation error
      401 Unauthorized: Authentication failure
      403 Forbidden: Quota exceeded
      429 Too Many Requests: Rate limit exceeded
      500 Internal Server Error: Service unavailable
      
  Response Caching:
    Cache Strategy:
      - Redis cache for similar requests
      - TTL: 24 hours for text, 7 days for images
      - Cache key: Hash of input parameters
      
  Performance Optimization:
    Request Batching:
      - Multiple text analysis in single request
      - Parallel image generation where possible
      - Request deduplication
      
    Connection Pooling:
      - HTTP/2 connection reuse
      - Keep-alive connections
      - Connection pool size: 20
```

### 3.2 Firebase サービス

#### Firebase 統合設計
```yaml
Firebase Integration:
  Authentication:
    Providers:
      - Google OAuth 2.0
      - Email/Password
      - Anonymous (disabled for security)
      
    Configuration:
      Session Duration: 7 days
      Password Policy:
        Min Length: 8 characters
        Require: Uppercase, lowercase, number
        
  Hosting:
    Configuration:
      Public Directory: out
      SPA: true
      Rewrites:
        - source: "/api/**"
          run:
            serviceId: manga-generation-service
            region: asia-northeast1
        - source: "**"
          destination: "/index.html"
          
    Performance:
      CDN: Enabled globally
      Compression: Gzip/Brotli
      Cache Headers:
        Static Assets: 1 year
        HTML: 5 minutes
        API: No cache
        
  Firestore (Optional):
    Use Cases:
      - User preferences
      - Chat session data
      - Temporary HITL data
      
    Configuration:
      Region: asia-northeast1
      Security Rules: Authenticated users only
      
  Cloud Functions (Optional):
    Use Cases:
      - Webhook processing
      - Background cleanup
      - Analytics processing
      
    Configuration:
      Runtime: Node.js 18
      Memory: 256MB
      Timeout: 60s
```

### 3.3 サードパーティサービス

#### サードパーティサービス統合
```yaml
Third-Party Service Integration:
  Payment Processing:
    Stripe:
      Use Cases:
        - Subscription billing
        - One-time payments
        - Usage-based billing
        
      Configuration:
        Currency: JPY, USD
        Webhooks: Payment status updates
        Security: PCI DSS compliance
        
  Analytics:
    Google Analytics 4:
      Events:
        - User registration
        - Manga generation start/complete
        - Subscription conversions
        
      Custom Dimensions:
        - User tier (free/premium)
        - Generation style preferences
        - Success/failure reasons
        
  Email Service:
    SendGrid:
      Use Cases:
        - Transactional emails
        - Marketing campaigns
        - System notifications
        
      Templates:
        - Welcome email
        - Generation complete
        - Subscription confirmations
        
  Monitoring:
    Datadog (Optional):
      Use Cases:
        - Advanced APM
        - Custom dashboards
        - Alert integration
        
      Configuration:
        - APM tracing
        - Log aggregation
        - Custom metrics
        
  Communication:
    Slack:
      Webhooks:
        - Critical alerts
        - Deployment notifications
        - Error summaries
        
      Channels:
        - #alerts-critical
        - #deployments
        - #general-monitoring
```

---

## 4. コスト最適化戦略

### 4.1 リソース管理

#### リソース最適化戦略
```yaml
Resource Optimization:
  Compute Optimization:
    Cloud Run:
      Strategies:
        - Right-sizing: CPU/Memory based on actual usage
        - Auto-scaling: Min 1, Max 100 instances
        - Cold start optimization: Keep 1 warm instance
        - Request timeout optimization: 15 minutes max
        
      Cost Savings:
        - Estimated 30% reduction vs. always-on GKE
        - Pay-per-request model
        - No cluster management overhead
        
  Storage Optimization:
    Cloud Storage:
      Lifecycle Policies:
        - Standard: 0-30 days
        - Nearline: 31-90 days
        - Coldline: 91-365 days
        - Archive: 365+ days
        
      Cost Savings:
        - Up to 60% for long-term storage
        - Automatic tier transitions
        - Reduced retrieval costs
        
  Database Optimization:
    Cloud SQL:
      Strategies:
        - Right-sizing: Start with db-standard-1
        - Connection pooling: Reduce connection overhead
        - Query optimization: Regular performance reviews
        - Backup optimization: 30-day retention
        
      Cost Monitoring:
        - Daily cost tracking
        - Usage pattern analysis
        - Performance vs. cost optimization
        
  Network Optimization:
    Traffic Management:
      - Regional traffic prioritization
      - CDN for static content
      - Compression for data transfer
      - Direct VPC Egress (saves $20-40/month)
```

### 4.2 コスト監視

#### コスト監視システム
```yaml
Cost Monitoring:
  Budget Controls:
    Monthly Budgets:
      Development: $100
      Staging: $200
      Production: $1,000
      
    Alert Thresholds:
      50%: Email notification
      80%: Slack alert + Email
      95%: SMS alert + Escalation
      100%: Automatic resource limitations
      
  Cost Attribution:
    Service-Level Tracking:
      - Cloud Run services
      - Database instances
      - Storage buckets
      - AI API usage
      
    Tag-Based Allocation:
      Environment: dev/staging/prod
      Service: api/ai/storage
      Feature: generation/auth/analytics
      
  Cost Optimization Dashboard:
    Metrics:
      - Daily spend trend
      - Cost per user
      - Cost per generation
      - Resource utilization efficiency
      
    Recommendations:
      - Underutilized resources
      - Optimization opportunities
      - Tier upgrade/downgrade suggestions
      
  Automated Cost Management:
    Policies:
      - Auto-shutdown dev environments after hours
      - Resource scaling based on usage patterns
      - Automated cleanup of temporary resources
      
    Implementation:
      - Cloud Scheduler for automated tasks
      - Cloud Functions for policy enforcement
      - BigQuery for cost analysis
```

### 4.3 自動スケーリング

#### スケーリング最適化
```yaml
Auto-Scaling Optimization:
  Application-Level Scaling:
    Cloud Run:
      Triggers:
        - CPU utilization > 70%
        - Memory utilization > 80%
        - Request queue depth > 10
        
      Policies:
        - Scale up: Add instances gradually
        - Scale down: 5-minute cooldown
        - Max instances: Environment-specific limits
        
  Database Scaling:
    Cloud SQL:
      Automatic Storage Increase:
        - Threshold: 90% disk usage
        - Increment: 25% or 10GB minimum
        - Max size: 1TB
        
      Read Replicas:
        - Trigger: Read load > 80%
        - Location: Same region
        - Auto-promotion: On master failure
        
  AI Service Scaling:
    Vertex AI:
      Quota Management:
        - Dynamic quota requests
        - Load balancing across regions
        - Fallback to alternative models
        
      Rate Limiting:
        - Client-side: Token bucket algorithm
        - Server-side: Exponential backoff
        - Queue management: Redis-based
        
  Cost-Aware Scaling:
    Scaling Policies:
      Business Hours:
        - Higher resource allocation
        - Faster scaling triggers
        - Performance-first approach
        
      Off Hours:
        - Lower resource allocation
        - Cost-optimized scaling
        - Longer scale-down delays
        
  Predictive Scaling:
    Machine Learning:
      - Historical usage pattern analysis
      - Seasonal trend prediction
      - Pre-scaling for anticipated load
      
    Implementation:
      - BigQuery ML for pattern analysis
      - Cloud Functions for automated scaling
      - Cloud Scheduler for predictive triggers
```

---

## 相互参照

### 関連設計書
- [インフラ概要](./infrastructure-overview.md) - ベースインフラ設計
- [デプロイメント設計](./deployment.md) - CI/CDシステム
- [監視・ログ設計](./monitoring.md) - 監視システム
- [セキュリティ設計](../08-security/README.md) - セキュリティ設計

### クラウドサービス選択基準
1. **コスト効率**: スタートアップに適した価格モデル
2. **機能性**: AI/MLサービスの質と範囲
3. **スケーラビリティ**: 成長に合わせた柔軟な拡張
4. **管理性**: 運用負荷の最小化
5. **統合性**: サービス間の連携と一貫性

### 最適化アプローチ
1. **段階的導入**: コア機能から始めて漸進的に拡張
2. **コスト監視**: 常時コストを監視し、最適化を継続
3. **自動化**: 手動作業を減らし、効率を向上
4. **パフォーマンス監視**: サービス品質を維持しながら最適化

---

**文書承認**
- クラウドアーキテクト: TBD 日付: TBD
- コストオプティマイザー: TBD 日付: TBD
- インフラエンジニア: TBD 日付: TBD