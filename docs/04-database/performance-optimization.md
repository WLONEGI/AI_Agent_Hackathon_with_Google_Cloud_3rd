---
document_id: "DB-PERF-001"
title: "データベースパフォーマンス最適化"
version: "4.0"
date_created: "2025-01-20"
date_updated: "2025-10-01"
status: "active"
category: "database"
document_type: "performance-optimization"
tags: ["database-performance", "indexing", "query-optimization", "connection-pooling", "caching", "partitioning", "monitoring", "materialized-views"]
parent_doc: "DB-README-001"
related_docs: ["DB-SCHEMA-001", "DB-MIG-001", "INF-MON-001", "INF-OPT-001"]
target_audience: ["database-architect", "sre-engineer", "backend-developer", "performance-engineer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# データベースパフォーマンス最適化

> **TL;DR**: 包括的なPostgreSQL最適化戦略。インデックス設計、クエリ最適化、接続管理、キャッシュ戦略、パーティショニング、監視で構成。Materialized View、LISTEN/NOTIFY、月次パーティショニング、スロークエリ監視、自動VACUUM完備。

---

## ⚡ インデックス設計

### インデックス戦略概要

```yaml
目的: クエリ性能向上とディスクI/O削減

基本方針:
  - 頻繁に検索されるカラムに優先的にインデックス作成
  - 複合インデックスは選択性の高いカラムを先頭に配置
  - 部分インデックスで不要なデータを除外
  - JSONB列にはGINインデックスを使用
  - 全文検索にはtsvector型とGINインデックス

インデックス種別:
  BTREE:
    用途: 範囲検索、ソート、等値検索
    適用: 主キー、外部キー、created_at、status等

  GIN:
    用途: JSONB、配列、全文検索
    適用: metadata列、tags配列、全文検索カラム

  UNIQUE:
    用途: 一意性制約とインデックス
    適用: email、(request_id, module_number)等

  PARTIAL:
    用途: 条件付きインデックス
    適用: アクティブレコード、期限切れ対象等
```

---

### テーブル別インデックス設計

```yaml
テーブル: users
インデックス:
  idx_users_email:
    タイプ: BTREE UNIQUE
    カラム: [email]
    用途: ログイン時の検索
    選択性: 高 (100%)
    推定サイズ: 小 (~1MB)

  idx_users_account_type:
    タイプ: BTREE
    カラム: [account_type]
    用途: ユーザー種別フィルタリング
    選択性: 低 (~4種類)
    推定サイズ: 小

テーブル: manga_projects
インデックス:
  idx_projects_user_created:
    タイプ: BTREE 複合
    カラム: [user_id, created_at DESC]
    用途: ユーザー別作品一覧（最頻出クエリ）
    選択性: 高
    推定サイズ: 中 (~10MB)
    理由: user_id でフィルタ後 created_at でソート

  idx_projects_expiring:
    タイプ: BTREE PARTIAL
    カラム: [expires_at]
    条件: expires_at IS NOT NULL
    用途: 期限切れ削除バッチ
    選択性: 高
    推定サイズ: 小
    理由: Freeユーザー作品のみ対象

  idx_projects_metadata_gin:
    タイプ: GIN
    カラム: [metadata]
    用途: JSONB全体のインデックス検索
    推定サイズ: 大 (~50MB)

  idx_projects_style:
    タイプ: BTREE
    式: [(metadata->>'style')]
    用途: スタイル別フィルタリング
    選択性: 中 (~7種類)

  idx_projects_tags:
    タイプ: GIN
    式: [(metadata->'tags')]
    用途: タグ配列検索
    選択性: 高

  idx_projects_title_fulltext:
    タイプ: GIN
    式: [to_tsvector('japanese', title)]
    用途: タイトル全文検索
    推定サイズ: 中

  idx_projects_content_search:
    タイプ: GIN
    式: [to_tsvector('japanese', coalesce(title, '') || ' ' || coalesce(metadata->>'description', ''))]
    用途: タイトル+説明の複合全文検索
    推定サイズ: 大

テーブル: generation_requests
インデックス:
  idx_requests_queue:
    タイプ: BTREE 複合 PARTIAL
    カラム: [status, priority DESC, created_at]
    条件: status IN ('queued', 'processing')
    用途: 処理キュー最適化
    選択性: 高
    推定サイズ: 小
    理由: アクティブなリクエストのみインデックス化

  idx_requests_active:
    タイプ: BTREE PARTIAL
    カラム: [created_at DESC]
    条件: status IN ('queued', 'processing')
    用途: アクティブリクエスト一覧
    選択性: 高
    推定サイズ: 小

  idx_requests_failed:
    タイプ: BTREE PARTIAL
    カラム: [created_at DESC, error_message]
    条件: status = 'failed'
    用途: エラー分析
    選択性: 高
    推定サイズ: 小

テーブル: phase_executions
インデックス:
  idx_executions_timeout:
    タイプ: BTREE PARTIAL
    カラム: [feedback_timeout]
    条件: feedback_timeout IS NOT NULL AND status = 'feedback_waiting'
    用途: フィードバック待ちタイムアウト処理
    選択性: 高
    推定サイズ: 極小

テーブル: processing_modules
インデックス:
  idx_modules_request_number:
    タイプ: BTREE UNIQUE 複合
    カラム: [request_id, module_number]
    用途: モジュール順序管理
    選択性: 高 (100%)

テーブル: api_usage_logs
インデックス:
  idx_logs_user_created:
    タイプ: BTREE 複合
    カラム: [user_id, created_at DESC]
    用途: 使用状況分析
    選択性: 高
    推定サイズ: 中
    パーティション: 月次パーティション各テーブルに自動作成
```

---

### インデックス作成要件

```yaml
作成タイミング:
  - 初期マイグレーション時: 全インデックス作成
  - 新テーブル追加時: 設計に基づきインデックス作成
  - パフォーマンス問題発生時: スロークエリ分析後追加

作成方法:
  - CONCURRENTLY オプション使用（本番環境）
  - ロック最小化
  - オフピーク時間帯での実行

削除基準:
  - 使用率が低い (idx_tup_read < 100)
  - 更新コストが高い (テーブルの頻繁なINSERT/UPDATE)
  - 重複インデックス存在時

メンテナンス:
  - 月次でインデックス使用統計確認
  - 不要インデックス削除
  - REINDEXによる断片化解消（必要時）
```

---

## 🎯 クエリ最適化

### 主要クエリパターン最適化設計

#### 1. ユーザー作品一覧取得

```yaml
クエリ名: get_user_projects
目的: ユーザーの作品一覧を最新順に取得
頻度: 高 (毎ページロード時)

最適化前の問題:
  - サブクエリでfile_count算出 → N+1問題
  - 全カラム取得 → 不要なデータ転送
  - expires_atチェック不足 → 期限切れ表示

最適化手法:
  - LEFT JOIN による集約
  - 必要カラムのみ SELECT
  - WHERE句で期限切れフィルタ
  - LIMIT/OFFSET によるページネーション
  - 複合インデックス利用 (user_id, created_at)

期待パフォーマンス:
  実行時間: < 50ms
  使用インデックス: idx_projects_user_created
  スキャン行数: ~20行

要求仕様:
  入力:
    - user_id: UUID
    - offset: integer (デフォルト: 0)
    - limit: integer (デフォルト: 20, 最大: 100)

  出力カラム:
    - project_id: UUID
    - title: string
    - status: string
    - created_at: timestamp
    - style: string (metadata->'style')
    - file_count: integer (集約結果)

  ソート: created_at DESC
  フィルタ:
    - user_id = ?
    - expires_at IS NULL OR expires_at > NOW()
```

---

#### 2. 処理状況確認

```yaml
クエリ名: get_processing_status
目的: リアルタイム処理状況取得
頻度: 高 (WebSocket経由で2-5秒間隔)

最適化手法:
  - LEFT JOIN で現在フェーズのみ取得
  - CASE式でフィードバック残り時間計算
  - WHERE句でアクティブなリクエストのみ
  - 複合インデックス利用

期待パフォーマンス:
  実行時間: < 20ms
  使用インデックス: idx_requests_active
  スキャン行数: ~1-5行

要求仕様:
  入力:
    - user_id: UUID

  出力カラム:
    - request_id: UUID
    - request_status: string
    - current_module: integer
    - phase_number: integer
    - phase_name: string
    - phase_status: string
    - started_at: timestamp
    - duration_ms: integer
    - feedback_remaining: interval (NULL if not waiting)

  フィルタ:
    - user_id = ?
    - status IN ('processing', 'queued')

  ソート: created_at DESC
```

---

#### 3. 処理キュー取得

```yaml
クエリ名: get_next_queued_request
目的: 次に処理すべきリクエスト取得
頻度: 高 (ワーカープロセスごとに1秒間隔)

最適化手法:
  - 部分インデックス利用 (idx_requests_queue)
  - FOR UPDATE SKIP LOCKED で排他制御
  - priority DESC, created_at ASC でソート

期待パフォーマンス:
  実行時間: < 10ms
  使用インデックス: idx_requests_queue
  スキャン行数: 1行

要求仕様:
  入力: なし

  出力カラム:
    - request_id: UUID
    - user_id: UUID
    - priority: string
    - created_at: timestamp
    - input_data: jsonb

  フィルタ:
    - status = 'queued'

  ソート:
    - priority DESC (urgent > high > normal > low)
    - created_at ASC (古いものから)

  排他制御:
    - FOR UPDATE SKIP LOCKED (ロック競合回避)
    - 取得後即座に status = 'processing' に更新
```

---

### クエリ実行計画分析要件

```yaml
分析ツール:
  - EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
  - pg_stat_statements 拡張機能

分析項目:
  実行時間:
    - Planning Time: < 1ms
    - Execution Time: 目標値参照

  インデックス使用:
    - Index Scan: 推奨
    - Seq Scan: 避けるべき (小テーブル除く)
    - Bitmap Heap Scan: 許容

  バッファ使用:
    - Shared Hit: 高いほど良い (キャッシュヒット)
    - Shared Read: 低いほど良い (ディスクI/O)

  行数:
    - Rows Removed by Filter: 低いほど良い
    - Actual Rows vs Estimated Rows: 乖離が小さいほど良い

統計情報更新:
  頻度: 日次自動 + 必要時手動
  対象テーブル: 全テーブル
  方法: ANALYZE コマンド実行

インデックス使用率確認:
  対象: pg_stat_user_indexes ビュー
  確認項目:
    - idx_tup_read: インデックススキャン行数
    - idx_tup_fetch: 実際に取得した行数
    - selectivity: 選択性 (read/fetch)

  判断基準:
    - selectivity > 10: インデックス効率低い → 見直し検討
    - idx_tup_read = 0: 未使用インデックス → 削除検討
```

---

## 🔄 接続管理設計

### 接続プール戦略

```yaml
目的: データベース接続の効率的な管理とリソース最適化

実装ライブラリ:
  Python: psycopg2.pool / asyncpg
  Node.js: pg.Pool
  Java: HikariCP

接続プール設定:
  最小接続数 (min_connections):
    値: 5
    理由: 常時接続を維持してレイテンシ削減
    適用: 各アプリケーションインスタンス

  最大接続数 (max_connections):
    値: 20
    理由: PostgreSQL max_connections (100) / インスタンス数 (5) = 20
    制約: 全インスタンス合計で max_connections 未満

  アイドルタイムアウト (idle_timeout):
    値: 300秒 (5分)
    理由: 未使用接続の自動解放
    動作: アイドル時間超過で接続クローズ

  接続タイムアウト (connection_timeout):
    値: 30秒
    理由: 接続確立失敗時の待機時間
    エラー: タイムアウト時は接続失敗として処理

  ステートメントタイムアウト (statement_timeout):
    値: 60秒
    理由: 長時間クエリの強制終了
    適用: 全クエリ
    除外: バッチ処理（個別設定）

接続ライフサイクル:
  取得:
    - プールから未使用接続を取得
    - 全接続使用中の場合は待機（タイムアウトまで）
    - 健全性チェック実施

  使用:
    - トランザクション開始
    - クエリ実行
    - コミット/ロールバック

  返却:
    - トランザクション終了確認
    - 接続状態リセット
    - プールに返却

エラーハンドリング:
  接続失敗:
    - リトライ: 3回まで (指数バックオフ)
    - フォールバック: プライマリDB へ接続
    - ログ: ERROR レベルで記録

  接続切断:
    - 自動再接続
    - トランザクション再実行不可を明示
    - クライアントにエラー返却
```

---

### リードレプリカ負荷分散設計

```yaml
目的: 読み取りクエリの負荷分散とパフォーマンス向上

構成:
  プライマリDB: 1台 (書き込み専用)
  リードレプリカ: 2台 (読み取り専用)
  レプリケーション遅延: < 1秒

負荷分散方式:
  アルゴリズム: ラウンドロビン
  説明: レプリカを順番に選択
  利点: シンプルで公平な分散

  代替方式:
    - 重み付けラウンドロビン (性能差がある場合)
    - 最小接続数 (接続数を監視)
    - ランダム (完全にランダム)

ルーティングルール:
  書き込みクエリ:
    対象: INSERT, UPDATE, DELETE, DDL
    ルーティング先: プライマリDB
    理由: レプリカは読み取り専用

  読み取りクエリ:
    対象: SELECT (FOR UPDATE除く)
    ルーティング先: リードレプリカ (ラウンドロビン)
    フォールバック: プライマリDB (レプリカ障害時)

  トランザクション内クエリ:
    対象: BEGIN ~ COMMIT 内の全クエリ
    ルーティング先: プライマリDB
    理由: 一貫性保証

ヘルスチェック:
  間隔: 30秒
  方法: SELECT 1 実行
  タイムアウト: 5秒
  失敗判定: 3回連続失敗
  復旧判定: 2回連続成功

フェイルオーバー:
  検知: ヘルスチェック失敗
  動作:
    1. 当該レプリカを利用不可としてマーク
    2. 他のレプリカまたはプライマリDBにルーティング
    3. アラート送信

  復旧:
    1. ヘルスチェック成功確認
    2. レプリケーション遅延確認 (< 5秒)
    3. 利用可能としてマーク
    4. ルーティング再開

一貫性要件:
  強い一貫性が必要な場合:
    - プライマリDBから読み取り
    - 例: 直前の書き込み結果を読む場合

  結果整合性で許容される場合:
    - リードレプリカから読み取り
    - 例: ダッシュボード統計、履歴データ
```

---

### プリペアドステートメント活用

```yaml
目的: クエリ解析コストの削減とSQLインジェクション防止

利点:
  - 解析・計画の再利用によるパフォーマンス向上
  - プレースホルダによるSQLインジェクション防止
  - ネットワーク転送量削減

適用対象:
  - 頻繁に実行されるクエリ (1秒あたり10回以上)
  - パラメータのみが異なる同一構造のクエリ
  - バッチ処理での反復実行

実装要件:
  定義:
    - PREPARE 文で事前定義
    - 名前付きステートメント作成
    - パラメータプレースホルダ使用

  実行:
    - EXECUTE 文でパラメータ指定
    - 実行計画の再利用

  破棄:
    - DEALLOCATE 文で明示的破棄
    - セッション終了時の自動破棄

例示:
  ステートメント名: get_user_projects
  パラメータ: (user_id UUID)
  SQL構造:
    - SELECT 句: 固定カラムリスト
    - FROM 句: manga_projects + LEFT JOIN manga_files
    - WHERE 句: user_id = $1 AND (expires_at IS NULL OR expires_at > NOW())
    - ORDER BY 句: created_at DESC
    - LIMIT 句: 20

監視項目:
  - pg_prepared_statements ビューで確認
  - from_sql: 元のSQL
  - parameter_types: パラメータ型
  - calls: 実行回数
```

---

### 接続統計監視要件

```yaml
監視対象: pg_stat_activity ビュー

監視項目:
  application_name:
    説明: アプリケーション識別子
    用途: アプリケーション別接続数集計

  state:
    説明: 接続状態
    値: active | idle | idle in transaction | idle in transaction (aborted)
    問題状態: idle in transaction が長時間継続

  connection_count:
    説明: 状態別接続数
    アラート: max_connections の80%超過

  avg_duration:
    説明: 各状態の平均継続時間（秒）
    アラート: idle in transaction が60秒以上

データベース名フィルタ: manga_db

アラート基準:
  - 総接続数 > 80: WARNING
  - 総接続数 > 90: CRITICAL
  - idle in transaction > 10接続: WARNING
  - idle in transaction 継続 > 60秒: CRITICAL
```

---

## 💾 キャッシュ戦略

### キャッシュ階層設計

```yaml
目的: データアクセスの高速化とデータベース負荷軽減

キャッシュ階層:
  L1 - アプリケーションメモリ:
    用途: 頻繁にアクセスされる静的データ
    保存先: プロセスメモリ
    TTL: 5-60分
    無効化: アプリケーション再起動、手動クリア
    対象データ: プロジェクト一覧、システム設定

  L2 - Materialized View:
    用途: 集計データ・統計情報
    保存先: PostgreSQL内
    TTL: 1時間リフレッシュ
    無効化: REFRESH MATERIALIZED VIEW 実行
    対象データ: ユーザー統計、使用状況集計

  L3 - データベーステーブル:
    用途: 永続データ
    保存先: PostgreSQL テーブル
    TTL: なし（永続）
    対象データ: 全ての業務データ

リアルタイム通知:
  機構: PostgreSQL LISTEN/NOTIFY
  用途: キャッシュ無効化トリガー
  遅延: < 100ms
  対象イベント: フェーズ完了、処理状態変更
```

---

### データ種別別キャッシュ設計

```yaml
データ種別: ユーザー情報
キャッシュ場所: Materialized View (user_project_stats)
TTL: 1時間（定期リフレッシュ）
無効化タイミング: プロジェクト作成/更新時
理由: 頻繁な集計クエリの実行コスト削減
実装要件:
  - CONCURRENTLY オプションでロック最小化
  - 定期リフレッシュジョブ (cron: 0 * * * *)
  - トリガー関数での即時リフレッシュ

データ種別: プロジェクト一覧
キャッシュ場所: アプリケーションメモリ
TTL: 5分
無効化タイミング: プロジェクト作成/更新/削除時
理由: ページロード時の高頻度アクセス
実装要件:
  - LRU キャッシュアルゴリズム
  - ユーザーID キー
  - LISTEN/NOTIFY による無効化

データ種別: 処理状況
キャッシュ場所: LISTEN/NOTIFY (リアルタイム)
TTL: 即時
無効化タイミング: フェーズ完了時
理由: リアルタイム更新が必須
実装要件:
  - phase_completed チャネル購読
  - WebSocket経由でクライアント通知

データ種別: システム設定
キャッシュ場所: アプリケーション起動時読み込み
TTL: 1時間
無効化タイミング: デプロイ時・手動更新時
理由: 変更頻度が低い
実装要件:
  - 起動時に全設定ロード
  - 環境変数でオーバーライド可能

データ種別: フェーズ結果
キャッシュ場所: データベーステーブル (phase_executions)
TTL: なし（永続）
無効化タイミング: なし
理由: 履歴データとして保持
実装要件:
  - 全フェーズ結果を保存
  - version_id による履歴管理
```

---

### Materialized View設計要件

```yaml
Materialized View名: user_project_stats

目的: ユーザー別プロジェクト統計の高速取得

集計内容:
  - user_id: ユーザーID
  - account_type: アカウント種別
  - total_projects: 総プロジェクト数
  - completed_projects: 完了プロジェクト数
  - last_project_date: 最終プロジェクト作成日
  - total_pages_created: 総ページ数

ソーステーブル:
  - users (LEFT JOIN)
  - manga_projects

インデックス:
  - PRIMARY KEY (user_id)
  - INDEX (account_type)
  - INDEX (last_project_date DESC)

リフレッシュ方式:
  方法: REFRESH MATERIALIZED VIEW CONCURRENTLY
  頻度: 毎時 0分 (cron: 0 * * * *)
  所要時間: < 1分
  ロック: CONCURRENTLY オプションで読み取り可能

手動リフレッシュ:
  トリガー: プロジェクト作成/更新トリガー
  条件: 重要な統計変更時（完了、削除等）
  実装: refresh_user_stats() 関数呼び出し

監視項目:
  - last_refresh: 最終リフレッシュ日時
  - refresh_duration: リフレッシュ所要時間
  - view_size: ビューサイズ

制約:
  - users.user_id の削除時は統計行も削除
  - account_type 変更時は即座に反映不要（次回リフレッシュ待ち）
```

---

### LISTEN/NOTIFY実装要件

```yaml
目的: リアルタイムイベント通知によるキャッシュ無効化

チャネル: phase_completed

通知タイミング:
  - phase_executions テーブルの status が 'completed' に更新時
  - トリガー関数 notify_phase_completion() で発行

通知ペイロード (JSON):
  request_id: UUID - リクエストID
  phase_number: integer - 完了したフェーズ番号
  user_id: UUID - ユーザーID

トリガー実装要件:
  タイミング: AFTER UPDATE ON phase_executions
  粒度: FOR EACH ROW
  条件: NEW.status = 'completed' AND OLD.status != 'completed'
  関数: notify_phase_completion()

アプリケーション側実装:
  接続:
    - LISTEN phase_completed 実行
    - 専用接続を維持（接続プールとは別）

  受信:
    - 非同期イベントループでペイロード受信
    - JSON パース
    - 該当キャッシュ無効化
    - WebSocket 経由でクライアント通知

  再接続:
    - 接続断時の自動再接続
    - LISTEN コマンド再実行

他のチャネル (将来拡張):
  - project_created: プロジェクト作成通知
  - project_updated: プロジェクト更新通知
  - request_failed: リクエスト失敗通知

制約:
  - ペイロードサイズ: < 8KB
  - 配信保証: at-most-once (接続断時は損失)
  - 順序保証: なし
```

---

## 📊 パーティショニング設計

### 月次パーティショニング戦略

```yaml
目的: 大量データテーブルのクエリ性能向上と古データ削除の効率化

対象テーブル: api_usage_logs

パーティショニング方式:
  タイプ: RANGE パーティショニング
  キー: created_at (TIMESTAMP)
  範囲: 月次 (1ヶ月単位)

親テーブル設計:
  テーブル名: api_usage_logs
  主キー: (log_id, created_at)
  理由: パーティションキー created_at を主キーに含める必要

子パーティション命名規則:
  形式: {table_name}_y{YYYY}m{MM}
  例: api_usage_logs_y2025m01, api_usage_logs_y2025m02

パーティション自動作成:
  タイミング: 毎月1日 0:00 (cron: 0 0 1 * *)
  作成数: 未来3ヶ月分
  理由: 月境界でのINSERT失敗防止

パーティション削除:
  タイミング: 保持期間超過後（12ヶ月保持の場合は13ヶ月目に削除）
  方法: DROP TABLE {partition_name}
  利点: DELETE よりも高速（メタデータ操作のみ）

インデックス:
  継承: 親テーブルのインデックスは自動的に各パーティションに作成
  個別作成: パーティション固有のインデックスは手動作成可能

クエリ最適化:
  - WHERE 句に created_at 条件を含める → パーティションプルーニング発動
  - 特定月のみスキャン → 全テーブルスキャン回避
  - 実行計画で使用パーティション確認

制約:
  - UNIQUE 制約はパーティションキーを含む必要
  - 外部キー制約は個別パーティションごとに設定
```

---

### パーティション管理要件

```yaml
未来パーティション事前作成:
  目的: 月境界での INSERT 失敗防止
  実行タイミング: 毎月1日 0:00
  作成対象: 当月 + 未来2ヶ月
  実装: create_monthly_partition() 関数

  処理フロー:
    1. 当月の月初日を算出
    2. i = 0 to 2 のループ
    3. 各月のパーティション存在チェック
    4. 未作成の場合のみ CREATE TABLE ... PARTITION OF 実行
    5. 作成ログ出力

古いパーティション削除:
  目的: ストレージ使用量削減
  実行タイミング: 毎月1日 1:00 (作成後)
  削除対象: 作成日から13ヶ月以上経過
  実装: DROP TABLE IF EXISTS {partition_name}

  処理フロー:
    1. 現在日時から13ヶ月前の年月を算出
    2. 該当パーティション名を生成
    3. DROP TABLE 実行
    4. 削除ログ出力

バックアップ:
  - パーティション削除前にバックアップ（オプション）
  - Cloud Storage へのエクスポート
  - 1年間保持後、アーカイブまたは削除

監視:
  - 各パーティションのサイズ監視
  - 未来パーティション存在確認
  - パーティション作成/削除の成功/失敗ログ

エラーハンドリング:
  - パーティション作成失敗: アラート送信、手動対応
  - パーティション削除失敗: ログ記録、次回リトライ
```

---

## 📈 パフォーマンス監視

### 重要メトリクス監視設計

#### スロークエリ監視

```yaml
目的: パフォーマンス問題の早期発見と対応

監視ツール: pg_stat_statements 拡張機能

有効化要件:
  - postgresql.conf: shared_preload_libraries = 'pg_stat_statements'
  - CREATE EXTENSION pg_stat_statements

監視項目:
  query:
    説明: 実行されたクエリ（正規化済み）
    用途: 問題クエリの特定

  calls:
    説明: 実行回数
    用途: 頻度分析

  total_time:
    説明: 累積実行時間（ミリ秒）
    用途: 全体への影響度評価

  mean_time:
    説明: 平均実行時間（ミリ秒）
    用途: 個別クエリのパフォーマンス評価
    アラート基準: > 1000ms

  stddev_time:
    説明: 実行時間の標準偏差
    用途: パフォーマンスの安定性評価

  rows:
    説明: 返却行数
    用途: データ量の把握

  hit_percent:
    説明: バッファキャッシュヒット率
    計算: 100.0 * shared_blks_hit / (shared_blks_hit + shared_blks_read)
    アラート基準: < 90%

抽出条件:
  - mean_time > 1000 (1秒以上の平均実行時間)
  - ORDER BY mean_time DESC
  - LIMIT 10 (上位10件)

対応アクション:
  mean_time > 1000ms:
    1. EXPLAIN ANALYZE でクエリ実行計画確認
    2. インデックス不足の確認
    3. インデックス追加または既存クエリ最適化
    4. 統計情報更新 (ANALYZE)

  hit_percent < 90%:
    1. shared_buffers 設定見直し
    2. effective_cache_size 調整
    3. work_mem 増加検討
```

---

#### インデックス効率性監視

```yaml
目的: 不要インデックスの検出と削除

監視対象: pg_stat_user_indexes ビュー

監視項目:
  schemaname:
    説明: スキーマ名
    フィルタ: public

  tablename:
    説明: テーブル名
    用途: テーブル別分析

  indexname:
    説明: インデックス名
    用途: 個別インデックス特定

  idx_tup_read:
    説明: インデックススキャンで読み取った行数
    用途: インデックス使用頻度

  idx_tup_fetch:
    説明: インデックスから実際に取得した行数
    用途: 実効取得数

  selectivity:
    説明: 選択性
    計算: idx_tup_read / idx_tup_fetch
    判断基準:
      - selectivity > 10: インデックス効率低い
      - selectivity < 2: 高効率

判断基準:
  不要インデックス:
    - idx_tup_read = 0 (未使用)
    - idx_tup_fetch = 0 (取得なし)
    - 作成後1ヶ月以上経過

  効率の悪いインデックス:
    - selectivity > 10
    - 多くの行をスキャンするが少数しか取得しない

対応アクション:
  不要インデックス:
    - DROP INDEX {indexname} で削除
    - ストレージとメンテナンスコスト削減

  効率の悪いインデックス:
    - WHERE 句の見直し
    - 部分インデックス化の検討
    - 複合インデックスへの変更検討
```

---

#### テーブルサイズ監視

```yaml
目的: ストレージ使用量の監視と容量計画

監視対象: pg_tables + pg_total_relation_size 関数

監視項目:
  schemaname:
    説明: スキーマ名
    フィルタ: public

  tablename:
    説明: テーブル名
    用途: テーブル別サイズ分析

  size:
    説明: 人間が読みやすい形式のサイズ
    関数: pg_size_pretty()
    例: 1024 MB, 512 KB

  size_bytes:
    説明: バイト単位のサイズ
    関数: pg_total_relation_size()
    用途: 数値比較・ソート

ソート: size_bytes DESC (大きい順)

アラート基準:
  個別テーブル:
    - size > 10GB: WARNING
    - size > 50GB: CRITICAL
    - パーティショニング検討

  全テーブル合計:
    - size > 100GB: WARNING
    - size > 500GB: CRITICAL
    - ストレージ拡張計画

対応アクション:
  大容量テーブル:
    - パーティショニング導入
    - アーカイブ戦略策定
    - 古データの削除または移動

  急激な増加:
    - データ増加原因調査
    - ログテーブルのローテーション確認
    - 不要データの削除
```

---

### 自動最適化設計

#### 自動VACUUM設定

```yaml
目的: デッドタプル除去と統計情報更新の自動化

設定対象: 全テーブル (個別設定可能)

主要パラメータ:
  autovacuum_vacuum_scale_factor:
    説明: VACUUM 実行のしきい値（テーブルサイズ比）
    デフォルト: 0.2 (20%)
    推奨値: 0.1 (10%)
    理由: より頻繁な VACUUM で性能維持

  autovacuum_analyze_scale_factor:
    説明: ANALYZE 実行のしきい値（テーブルサイズ比）
    デフォルト: 0.1 (10%)
    推奨値: 0.05 (5%)
    理由: 統計情報の鮮度向上

  autovacuum_vacuum_cost_delay:
    説明: VACUUM コスト遅延（ミリ秒）
    デフォルト: 20ms
    推奨値: 10ms (低負荷時は短縮)

  autovacuum_vacuum_cost_limit:
    説明: VACUUM コスト制限
    デフォルト: 200
    推奨値: 300 (高負荷時は増加)

テーブル別設定:
  manga_projects:
    - autovacuum_vacuum_scale_factor = 0.1
    - 理由: 頻繁な更新

  api_usage_logs:
    - autovacuum_vacuum_scale_factor = 0.05
    - 理由: 大量の INSERT

  phase_executions:
    - autovacuum_vacuum_scale_factor = 0.1
    - 理由: 頻繁な status 更新

監視項目:
  - pg_stat_user_tables.n_dead_tup: デッドタプル数
  - pg_stat_user_tables.last_autovacuum: 最終自動VACUUM日時
  - pg_stat_user_tables.last_autoanalyze: 最終自動ANALYZE日時

アラート基準:
  - n_dead_tup > 100000: WARNING
  - last_autovacuum が24時間以上前: WARNING
```

---

#### 統計情報自動更新

```yaml
目的: クエリオプティマイザの精度向上

更新対象テーブル:
  - manga_projects
  - generation_requests
  - phase_executions
  - manga_files
  - users

更新頻度:
  自動: autovacuum_analyze_scale_factor (5%)
  手動: 日次 cron ジョブ (3:00 AM)

実装要件:
  関数名: auto_analyze()
  実行内容:
    - ANALYZE manga_projects
    - ANALYZE generation_requests
    - ANALYZE phase_executions
    - その他主要テーブル

  実行タイミング:
    - cron: 0 3 * * * (毎日 3:00 AM)
    - 低負荷時間帯を選択
    - 所要時間: < 5分

  ログ出力:
    - 開始/終了時刻
    - 各テーブルの統計情報更新結果
    - エラー発生時の詳細

監視:
  - pg_stat_user_tables.last_analyze: 最終手動ANALYZE日時
  - 統計情報の鮮度確認
  - オプティマイザの実行計画精度

効果:
  - クエリ実行計画の最適化
  - インデックス使用判断の精度向上
  - パフォーマンスの安定化
```

---

## 🔗 関連文書

- [スキーマ設計](./schema-design.md)
- [マイグレーション戦略](./migration-strategy.md)
- [データベース設計書 README](./README.md)
- [インフラ設計書](../07-infrastructure/README.md)
- [インフラ監視設計](../07-infrastructure/monitoring.md)

---

## 実装ガイドライン

```yaml
PostgreSQL設定:
  ファイル: postgresql.conf
  重要パラメータ:
    - shared_buffers: メモリの25%
    - effective_cache_size: メモリの50-75%
    - work_mem: 16-64MB
    - maintenance_work_mem: 256MB
    - max_connections: 100
    - shared_preload_libraries: 'pg_stat_statements'

接続プール実装:
  Python: psycopg2.pool.ThreadedConnectionPool
  設定: min_conn=5, max_conn=20

監視ダッシュボード:
  ツール: Grafana + Prometheus postgres_exporter
  主要パネル:
    - スロークエリTop 10
    - 接続数推移
    - キャッシュヒット率
    - テーブルサイズ推移

運用手順:
  日次:
    - スロークエリ確認
    - 接続数監視
    - デッドタプル確認

  週次:
    - インデックス使用率レビュー
    - テーブルサイズ確認
    - パーティション作成確認

  月次:
    - 不要インデックス削除検討
    - 古いパーティション削除
    - 統計情報レビュー
```

---

**メタデータ**
- カテゴリ: データベースパフォーマンス
- 重要度: 高
- 更新頻度: 中
- レビュー担当: データベースアーキテクト

---

**承認**
- データベースアーキテクト: TBD 日付: TBD
- SREエンジニア: TBD 日付: TBD
- バックエンド開発者: TBD 日付: TBD
