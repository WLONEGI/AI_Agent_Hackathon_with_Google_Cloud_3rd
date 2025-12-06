---
document_id: "SEC-AUTH-001"
title: "認証・認可設計"
version: "3.0"
date_created: "2025-01-20"
date_updated: "2025-09-30"
status: "active"
category: "security"
document_type: "authentication-authorization-design"
tags: ["authentication", "authorization", "firebase-auth", "jwt", "rbac", "api-security", "hitl-security", "websocket-security"]
parent_doc: "SEC-README-001"
related_docs: ["SEC-OVERVIEW-001", "API-AUTH-001", "INF-CLD-001"]
target_audience: ["security-engineer", "backend-developer", "api-developer", "devops-engineer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# 認証・認可設計

> **TL;DR**: Firebase Authentication基盤の包括的セキュリティ設計。JWT認証（標準クレーム+カスタムクレーム）、3階層RBAC（free/premium/admin）、最小権限原則、API認証（Secret Manager統合・キーローテーション）で構成。HITLセキュリティ（XSS対策・SQLインジェクション防止・メッセージ長2000文字制限・24時間プレビュー有効期限）、WebSocketセキュリティ（JWT認証・最大5接続/ユーザー・10メッセージ/秒レート制限・10KBサイズ制限・AES暗号化）完備。

## 🔐 Firebase Authentication設計

### 認証戦略
本システムではFirebase Authenticationを中核とした認証戦略を採用し、以下の設計原則に基づく：

**認証プロバイダー戦略**
- 信頼性の高い認証プロバイダー（Google OAuth、メール認証）の採用
- 匿名認証の無効化による不正利用防止
- Multi-Factor Authentication（MFA）の段階的導入計画

**セキュリティポリシー設計**
- 強力なパスワードポリシーの適用（最小8文字、複合文字種必須）
- 一般的なパスワードの事前ブロック機能
- セッション管理：適切な有効期限設定による安全性とユーザビリティの両立
- レート制限：ブルートフォース攻撃対策の実装

### JWT トークン設計方針
セキュアなトークンベース認証の実装において以下を考慮：

**標準クレーム戦略**
- Firebase標準仕様準拠によるInteroperability確保
- 適切な有効期限設定によるセキュリティバランス
- トークン検証の確実な実装

**カスタムクレーム設計**
- ユーザーロール管理：階層的権限モデルの実装
- API使用量制御：サービス品質保証のための制限機能
- セッション管理：不正使用検出のためのメタデータ保持

## 👥 ロールベースアクセス制御

### ユーザーロール定義
```yaml
User Roles:
  free:
    permissions:
      - manga:generate:daily_limit_1
      - manga:view:own
      - manga:download:own
    api_quota: 1/day

  premium:
    permissions:
      - manga:generate:unlimited
      - manga:view:own
      - manga:download:own
      - manga:edit:own
      - manga:share:public
    api_quota: 100/day

  admin:
    permissions:
      - manga:*
      - user:manage
      - system:monitor
      - content:moderate
    api_quota: unlimited
```

### アクセス制御設計原則

**権限管理アーキテクチャ**
- ロールベースアクセス制御（RBAC）による階層的権限管理
- 最小権限の原則：必要最小限の権限のみ付与
- 権限の粒度設計：リソース・アクション単位での細かな制御
- ワイルドカード機能：管理者権限の効率的な実装

**認可機構設計**
- JWT トークンベースの分散認可
- デコレーターパターンによる透明な権限チェック
- リアルタイム権限検証：リクエスト毎の確実な認証
- 使用量制限：フリーユーザーの日次制限機能

**セキュリティ考慮事項**
- トークン検証の確実な実施
- 権限昇格攻撃の防止
- 認証失敗時の適切なエラーハンドリング
- 監査ログとの連携による不正アクセス検出

## 🔑 API認証

### 外部API認証戦略

**Google AI API セキュリティアーキテクチャ**
- Secret Manager統合による機密情報の安全な管理
- API キーローテーション戦略の実装
- レート制限による適切な使用量管理
- リクエスト検証によるデータ整合性確保

**セキュリティ設計原則**
- 最小権限でのAPI呼び出し権限設定
- トークン・キーの定期的な更新メカニズム
- API呼び出し時の透明性とトレーサビリティ確保
- 異常なAPI使用パターンの検出と対応

**監視とガバナンス**
- API使用状況の継続的な監視
- 不正なAPI利用の早期検出機能
- コスト管理との連携によるリソース最適化
- セキュリティインシデント時の迅速な対応体制

## 🎭 HITLセキュリティ

### HITL (Human-in-the-Loop) セキュリティ設計戦略

**インタラクティブセキュリティアーキテクチャ**
- フィードバックシステムのセキュリティ統合管理
- チャットメッセージのリアルタイム検証・サニタイズ
- プレビューバージョンの適切なアクセス制御
- フェーズベースワークフローのセキュリティ保証

**所有権・アクセス制御設計**
- リクエストIDによる厳格な所有権確認
- 7段階のフェーズ管理による適切なワークフロー制御
- 24時間の有効期限によるプレビューアクセス管理
- 30分のフィードバックタイムアウトによる効率性確保

**メッセージセキュリティ対策**
- XSS攻撃対策：HTMLエスケープによる安全性確保
- SQLインジェクション対策：パラメータ化による保護
- 悪意のあるスクリプト検出：パターンマッチングによる防御
- メッセージ長制限：DoS攻撃防止（最大2000文字）

**セキュリティパターン検出**
- JavaScript実行攻撃の検出と遮断
- イベントハンドラー悪用の防止
- データURIスキーム攻撃の対策
- VBScript注入攻撃の検出

### WebSocketセキュリティ戦略

**リアルタイム通信セキュリティアーキテクチャ**
- JWT認証による安全なWebSocket接続確立
- 接続管理：ユーザー当たり最大5接続制限によるリソース保護
- 分散レート制限：1秒間に10メッセージまでの制御
- 接続状態の適切な管理と監視

**WebSocket認証・認可設計**
- JWT トークンベースの接続時認証
- ユーザー存在確認による不正接続の防止
- 有効期限チェックによるセッション管理
- 認証失敗時の適切なエラーハンドリング

**メッセージセキュリティ管理**
- メッセージタイプ制限：事前定義された4種類のメッセージのみ許可
- サイズ制限：10KBまでのメッセージによるDoS攻撃防止
- 構造検証：JSONフォーマットの確実な検証
- 不正メッセージの早期検出と拒否

**データ暗号化とプライバシー保護**
- 機密データの選択的AES暗号化
- 送信前のデータサニタイズ処理
- 通信内容の適切なログ記録（個人情報除外）
- エンドツーエンドの整合性確保

## 🔗 関連文書

- [認可・アクセス制御](./authorization.md)
- [データ保護設計](./data-protection.md)
- [セキュリティ概要](./security-overview.md)
- [セキュリティ設計書 README](./README.md)

---

**メタデータ**
- カテゴリ: 認証・認可
- 重要度: 最高
- 更新頻度: 中
- レビュー担当: セキュリティエンジニア