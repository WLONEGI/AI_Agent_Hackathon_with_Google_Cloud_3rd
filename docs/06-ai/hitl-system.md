---
document_id: "AI-HITL-001"
title: "7フェーズHITLシステム設計"
version: "3.0"
date_created: "2025-01-20"
date_updated: "2025-09-30"
status: "active"
category: "ai"
document_type: "hitl-design"
tags: ["hitl", "human-in-the-loop", "feedback-system", "7-phases", "quality-gates"]
parent_doc: "AI-README-001"
related_docs: ["AI-OVERVIEW-001", "AI-QUALITY-001", "API-GEN-001"]
target_audience: ["ai-engineer", "backend-developer", "frontend-developer", "tech-lead"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# 7フェーズHITLシステム設計

> **TL;DR**: Human-in-the-loop統合設計とフィードバック処理パイプライン。HITLCapablePipelineService設計、フィードバックサイクル、状態管理、エラーハンドリング、3段階マイグレーション戦略で構成。各フェーズ30分タイムアウト、自然言語フィードバック処理、リアルタイムWebSocket通信による協調品質向上を実現。

**ナビゲーション**: [README](./README.md) > HITLシステム設計

**関連文書**:
- [AI設計概要](./ai-overview.md)
- [品質制御システム](./quality-control.md)
- [外部API統合設計](./external-apis.md)

---

## 1. HITLモジュール統合設計

### 1.1 統合設計原則

**現状の問題分析**

現在のパイプライン実装では、フィードバック収集機能は実装されているものの、収集されたフィードバックを実際の再生成に活用する仕組みが不完全です：

```yaml
現在の実装の問題点:
  ファイル: pipeline_service.py:1405-1420
  メソッド: _execute_single_phase

  処理フロー:
    1. フェーズ処理実行:
       phase_result = await _process_phase(session, phase_config, context, attempt=1)

    2. 結果永続化:
       await _persist_phase_results(session, phase_config, phase_result)

    3. 結果返却:
       return phase_result

  問題点:
    - ❌ フィードバック収集後の再生成処理なし
    - ❌ ユーザー承認/修正のサイクルなし
    - ❌ タイムアウト処理なし
    - ❌ 状態管理なし
```

**統合設計原則**

| 原則 | 内容 | 実装アプローチ |
|------|------|---------------|
| 非侵襲的統合 | 既存システムへの最小限の変更 | 継承ベースの拡張クラス |
| 段階的導入 | リスクを最小化した段階的実装 | フェーズ別導入戦略 |
| パフォーマンス重視 | 高速応答とリソース効率 | 非同期処理とキャッシュ最適化 |
| 品質保証 | 信頼性と一貫性の確保 | 包括的エラーハンドリング |

### 1.2 HITLCapablePipelineService設計

```yaml
クラス設計: HITLCapablePipelineService
  継承: PipelineService
  目的: HITL機能を統合したパイプラインサービス
  説明: 既存のPipelineServiceを継承し、フィードバック機能を追加

  構成要素:
    hitl_service:
      型: HITLService
      説明: フィードバック処理サービス

    state_manager:
      型: HITLStateManager
      説明: HITL状態管理

    error_handler:
      型: HITLErrorHandler
      説明: エラーハンドリング

    resource_manager:
      型: HITLResourceManager
      説明: リソース管理

  主要メソッド:
    _execute_single_phase_with_hitl:
      目的: HITLフィードバックサイクルを統合したフェーズ実行
      入力:
        - session: セッション情報
        - phase_config: フェーズ設定
        - context: 処理コンテキスト
      出力: 最終処理結果

      処理フロー:
        1. 初期実行:
           initial_result = await _process_phase(session, phase_config, context, attempt=1)

        2. HITL有効チェック:
           IF await _is_hitl_enabled_for_session(session):
             final_result = await _process_hitl_feedback_cycle(
               session, phase_config, context, initial_result
             )
           ELSE:
             final_result = initial_result

        3. 結果永続化:
           await _persist_phase_results(session, phase_config, final_result)

        4. 結果返却:
           return final_result

    _process_hitl_feedback_cycle:
      目的: フィードバックサイクルのメイン処理ロジック
      入力:
        - session: セッション情報
        - phase_config: フェーズ設定
        - context: 処理コンテキスト
        - initial_result: 初期処理結果
      出力: 最終処理結果（フィードバック反映済み）

      処理フロー:
        1. 初期化:
           current_result = initial_result
           iteration = 0
           max_iterations = 3

        2. フィードバックループ:
           WHILE iteration < max_iterations:
             a. フィードバック状態設定:
                await state_manager.set_waiting_for_feedback(
                  session.id, phase_config.phase_number, current_result
                )

             b. WebSocket通知:
                await _notify_feedback_required(
                  session.id, phase_config.phase_number, current_result
                )

             c. フィードバック待機:
                feedback = await _wait_for_feedback(
                  session.id, phase_config.phase_number, timeout_minutes=30
                )
                説明: 30分タイムアウトでユーザーフィードバックを待機

             d. タイムアウト処理:
                IF feedback is None:
                  i. タイムアウト記録:
                     await state_manager.set_timeout_continue(
                       session.id, phase_config.phase_number
                     )
                  ii. ループ終了:
                     break
                  説明: タイムアウト時は現在の結果で継続

             e. 承認処理:
                IF feedback.action == "approve":
                  i. 承認記録:
                     await state_manager.set_approved(
                       session.id, phase_config.phase_number
                     )
                  ii. ループ終了:
                     break
                  説明: ユーザー承認時は現在の結果で確定

             f. 修正要求処理:
                ELIF feedback.action == "modify":
                  i. フィードバック処理状態設定:
                     await state_manager.set_processing_feedback(
                       session.id, phase_config.phase_number, feedback
                     )

                  ii. フィードバック適用と再生成:
                     TRY:
                       1. フィードバック適用:
                          modified_context = await _apply_feedback_modifications(
                            context, feedback, current_result
                          )

                       2. 再生成実行:
                          current_result = await _process_phase(
                            session, phase_config, modified_context, attempt=iteration + 2
                          )

                       3. 再生成完了記録:
                          await state_manager.set_regeneration_complete(
                            session.id, phase_config.phase_number, current_result
                          )

                     EXCEPT Exception as e:
                       1. エラーハンドリング:
                          await error_handler.handle_regeneration_error(
                            session.id, phase_config.phase_number, e, current_result
                          )
                       2. ループ終了:
                          break
                       説明: エラー時は現在の結果を保持してループ終了

             g. イテレーション更新:
                iteration += 1

        3. 最終結果返却:
           return current_result

  パフォーマンス要件:
    - フィードバック待機タイムアウト: 30分
    - 最大反復回数: 3回
    - 非同期処理: 全メソッド非同期実行
    - 状態管理: トランザクション保証
```

## 2. フィードバック処理パイプライン

### 2.1 フィードバックサイクル詳細設計

**フィードバック処理フロー**

```mermaid
sequenceDiagram
    participant U as User
    participant W as WebSocket
    participant S as HITLService
    participant P as Pipeline
    participant D as Database

    P->>S: フィードバック待機開始
    S->>D: 状態更新 (waiting)
    S->>W: ユーザー通知
    W->>U: フィードバック要求表示

    alt ユーザーフィードバック
        U->>W: フィードバック送信
        W->>S: フィードバック受信
        S->>D: フィードバック保存
        S->>P: フィードバック返却

        alt 修正要求
            P->>P: 再生成実行
            P->>D: 結果更新
            P->>W: 新結果通知
        else 承認
            P->>D: 承認記録
            P->>+: 次フェーズ継続
        end
    else タイムアウト
        S->>D: タイムアウト記録
        S->>P: タイムアウト通知
        P->>+: 現在結果で継続
    end
```

### 2.2 HITLStateManager設計

```yaml
クラス設計: HITLStateManager
  目的: HITL状態管理と複雑な状態遷移の制御

  構成要素:
    db:
      型: AsyncSession
      説明: データベースセッション

    valid_transitions:
      型: dict[HITLState, List[HITLState]]
      説明: 有効な状態遷移の定義
      遷移マトリックス:
        INITIAL:
          遷移可能先: [WAITING_FEEDBACK]
          説明: 初期状態から待機状態へ

        WAITING_FEEDBACK:
          遷移可能先: [FEEDBACK_RECEIVED, TIMEOUT, ERROR]
          説明: フィードバック待機から受信/タイムアウト/エラーへ

        FEEDBACK_RECEIVED:
          遷移可能先: [PROCESSING_FEEDBACK, APPROVED, ERROR]
          説明: フィードバック受信から処理/承認/エラーへ

        PROCESSING_FEEDBACK:
          遷移可能先: [REGENERATION_COMPLETE, WAITING_FEEDBACK, ERROR]
          説明: 処理中から完了/次の反復/エラーへ

        REGENERATION_COMPLETE:
          遷移可能先: [WAITING_FEEDBACK]
          説明: 再生成完了から次の待機状態へ

        APPROVED:
          遷移可能先: [COMPLETED]
          説明: 承認から完了状態へ

        TIMEOUT:
          遷移可能先: [COMPLETED]
          説明: タイムアウトから完了状態へ

        ERROR:
          遷移可能先: [ERROR_RECOVERED, FAILED]
          説明: エラーから回復/失敗へ

        ERROR_RECOVERED:
          遷移可能先: [WAITING_FEEDBACK]
          説明: エラー回復から待機状態へ復帰

        COMPLETED:
          遷移可能先: []
          説明: 終端状態（遷移不可）

        FAILED:
          遷移可能先: []
          説明: 終端状態（遷移不可）

  主要メソッド:
    transition_state:
      目的: 状態遷移の実行と検証
      入力:
        - session_id: UUID セッション識別子
        - phase_number: int フェーズ番号
        - new_state: HITLState 新しい状態
        - metadata: Optional[dict] メタデータ（省略可）
      出力: bool 遷移成功/失敗

      処理フロー:
        1. 現在状態取得:
           current_state = await get_current_state(session_id, phase_number)

        2. 遷移妥当性検証:
           IF new_state NOT IN valid_transitions.get(current_state, []):
             RAISE HITLStateTransitionError(
               f"Invalid transition: {current_state} -> {new_state}"
             )
           説明: 無効な状態遷移を拒否

        3. トランザクション内状態更新:
           async with db.begin():
             a. PhaseFeedbackState更新:
                i. 状態取得:
                   feedback_state = await _get_feedback_state(session_id, phase_number)

                ii. フィールド更新:
                   feedback_state.status = new_state.value
                   feedback_state.updated_at = datetime.utcnow()

                iii. メタデータマージ:
                   IF metadata:
                     feedback_state.metadata = {
                       **(feedback_state.metadata or {}),
                       **metadata
                     }

             b. HITLTransitionLog記録:
                i. ログエントリ作成:
                   transition_log = HITLTransitionLog(
                     session_id=session_id,
                     phase_number=phase_number,
                     from_state=current_state.value,
                     to_state=new_state.value,
                     metadata=metadata,
                     created_at=datetime.utcnow()
                   )

                ii. ログ保存:
                   db.add(transition_log)

             c. コミット:
                await db.commit()

        4. 成功返却:
           return True

  エラーハンドリング:
    HITLStateTransitionError:
      トリガー: 無効な状態遷移試行
      HTTPステータス: 400 Bad Request
      対応: エラーメッセージとともに拒否

  パフォーマンス要件:
    - 状態遷移処理時間: <500ms
    - トランザクション保証: ACID準拠
    - ログ記録: 全遷移履歴保存
    - 並行制御: セッション単位ロック
```

### 2.3 HITLErrorHandler設計

```yaml
クラス設計: HITLErrorHandler
  目的: 包括的エラーハンドリングと回復戦略

  構成要素:
    recovery_strategies:
      型: dict[str, Callable]
      説明: エラー種別ごとの回復戦略マッピング
      戦略マッピング:
        timeout_error:
          ハンドラ: _handle_timeout_error
          説明: タイムアウトエラー処理

        regeneration_error:
          ハンドラ: _handle_regeneration_error
          説明: 再生成エラー処理

        feedback_parse_error:
          ハンドラ: _handle_feedback_parse_error
          説明: フィードバック解析エラー処理

        state_transition_error:
          ハンドラ: _handle_state_transition_error
          説明: 状態遷移エラー処理

        resource_limit_error:
          ハンドラ: _handle_resource_limit_error
          説明: リソース制限エラー処理

  主要メソッド:
    handle_regeneration_error:
      目的: 再生成エラーの包括的処理
      入力:
        - session_id: UUID セッション識別子
        - phase_number: int フェーズ番号
        - error: Exception 発生したエラー
        - fallback_result: dict フォールバック結果
      出力: dict 回復後の結果またはフォールバック結果

      処理フロー:
        1. エラーコンテキスト構築:
           error_context = {
             "session_id": str(session_id),
             "phase_number": phase_number,
             "error_type": type(error).__name__,
             "error_message": str(error),
             "timestamp": datetime.utcnow().isoformat()
           }

        2. エラー分類と回復戦略選択:
           a. タイムアウトエラー:
              IF isinstance(error, (asyncio.TimeoutError, httpx.TimeoutException)):
                return await _handle_timeout_error(error_context, fallback_result)

              処理内容:
                - タイムアウトログ記録
                - フォールバック結果返却
                - タイムアウトメトリクス記録
                - アラート送信（3回連続タイムアウト時）

           b. バリデーションエラー:
              ELIF isinstance(error, (ValidationError, ValueError)):
                return await _handle_validation_error(error_context, fallback_result)

              処理内容:
                - バリデーションエラー詳細ログ
                - データ検証失敗箇所特定
                - フォールバック結果返却
                - エラー分析レポート生成

           c. リソース制限エラー:
              ELIF isinstance(error, ResourceLimitError):
                return await _handle_resource_limit_error(error_context, fallback_result)

              処理内容:
                - リソース使用状況確認
                - 優先度低下設定
                - キュー再投入またはフォールバック
                - リソース監視アラート

           d. 未知のエラー:
              ELSE:
                return await _handle_unknown_error(error_context, fallback_result)

              処理内容:
                - 詳細エラー情報収集
                - スタックトレース記録
                - フォールバック結果返却
                - 緊急アラート送信
                - エラー調査チケット自動作成

  エラー回復戦略:
    タイムアウト:
      対応: フォールバック結果で継続
      通知: 3回連続でアラート
      再試行: なし

    バリデーション:
      対応: データ検証・フォールバック
      通知: エラーログ記録
      再試行: なし（データ不正のため）

    リソース制限:
      対応: キュー再投入または縮退運転
      通知: リソース監視アラート
      再試行: 優先度低下で1回

    未知のエラー:
      対応: フォールバック・緊急対応
      通知: 即時アラート・チケット作成
      再試行: なし

  パフォーマンス要件:
    - エラー処理時間: <1秒
    - ログ記録: 全エラー詳細保存
    - アラート送信: <5秒
    - フォールバック適用: 即座
```

## 3. 実装優先順位とマイグレーション戦略

### 3.1 3段階マイグレーションアプローチ

**Phase 1: 基本統合 (Week 1-2)**

```yaml
Phase 1 Implementation:
  Core Integration:
    - HITLCapablePipelineService実装
    - 基本フィードバックサイクル統合
    - シンプルな状態管理

  Target Phases:
    - Phase 1: コンセプト・世界観分析
    - Phase 2: キャラクター設計

  Success Criteria:
    - フィードバック収集と適用の基本機能
    - 30分タイムアウト機能
    - エラーハンドリング基本機能

  Risk Mitigation:
    - 既存機能への影響最小化
    - フォールバック機能の完全実装
    - A/Bテスト用フラグ制御
```

**Phase 2: 部分統合 (Week 3-4)**

```yaml
Phase 2 Implementation:
  Advanced Features:
    - HITLStateManager完全実装
    - 複雑な状態遷移管理
    - リソース管理基本機能

  Target Phases:
    - Phase 3: ストーリー構造設計
    - Phase 4: ネーム構成生成

  Success Criteria:
    - 並行セッション管理 (5同時セッション)
    - 状態遷移の一貫性保証
    - エラー回復機能

  Performance Targets:
    - フィードバック応答時間: <2秒
    - 状態遷移処理: <500ms
    - メモリ使用量増加: <15%
```

**Phase 3: 完全統合 (Week 5-6)**

```yaml
Phase 3 Implementation:
  Full Production:
    - HITLResourceManager完全実装
    - 包括的モニタリング
    - パフォーマンス最適化

  Target Phases:
    - Phase 5: ビジュアル生成
    - Phase 6: 対話配置最適化
    - Phase 7: 品質統合・調整

  Success Criteria:
    - 全フェーズHITL対応
    - 高負荷環境での安定性
    - 編集同時数: 10セッション

  Production Readiness:
    - 総合テストカバレッジ: >85%
    - パフォーマンスベンチマーク達成
    - モニタリングとアラート設定
```

### 3.2 リスク緩和戦略

**技術リスク管理**

| リスクカテゴリ | 対応戦略 | 緩和手段 |
|------------|----------|--------|
| 既存機能影響 | 非侵襲的統合アプローチ | 継承ベース設計、フェーズ別導入 |
| パフォーマンス低下 | 最適化優先設計 | 非同期処理、キャッシュ戦略 |
| 状態管理複雑化 | 中央集中状態管理 | 適切な状態モデル設計 |
| ユーザー体験悪化 | UX優先設計 | 直観的インターフェース |
| リソース枯渇 | 効率的リソース管理 | 同時数制限、優先度制御 |

## 4. フェーズ仕様

### 4.1 HITLフェーズ個別仕様

```yaml
HITL Phase Specifications:
  Phase1_ConceptAnalysis:
    AI_Input: {text: str, style: str, pages: int}
    AI_Output: {theme: str, genre: str, world_setting: str, target_audience: str, tone: str, keywords: list}
    User_Preview: "テーマ、ジャンル、世界観、対象読者層のプレビュー"
    Feedback_Options: ["テーマ修正", "ジャンル変更", "世界観調整", "雰囲気変更"]
    AI_API: Gemini Pro
    Processing_Time: "12s + 最大30分フィードバック待機"
    Quality_Metrics: [concept_clarity, user_satisfaction, feedback_integration]

  Phase2_CharacterDesign:
    AI_Input: {phase1_concept: dict, user_feedback_history: list}
    AI_Output: {characters: list, relationships: dict, visual_designs: list, reference_images: list}
    User_Preview: "キャラクター設定、関係性、ビジュアルデザインのプレビュー"
    Feedback_Options: ["キャラ追加/削除", "性格変更", "ビジュアル調整", "関係性修正"]
    AI_API: Gemini Pro + Imagen 4
    Processing_Time: "18s + 最大30分フィードバック待機"
    Quality_Metrics: [character_consistency, visual_quality, user_approval]

  Phase3_PlotStructure:
    AI_Input: {phase1_concept: dict, phase2_character: dict, user_feedback: list}
    AI_Output: {three_act_structure: dict, emotional_arc: list, page_allocation: dict}
    User_Preview: "3幕構成、起承転結、感情曲線のプレビュー"
    Feedback_Options: ["プロット変更", "ペーシング調整", "クライマックス修正"]
    AI_API: Gemini Pro
    Processing_Time: "15s + 最大30分フィードバック待機"
    Quality_Metrics: [plot_coherence, story_flow, user_approval]
```

### 4.2 パフォーマンス目標と品質指標

| フェーズ | 応答性目標 | 品質指標 | ユーザーエンゲージメント |
|-------|----------|--------|----------------|
| Phase 4 | 最適化されたレスポンス | レイアウト品質・演出効果 | インタラクティブコマ割り設計 |
| Phase 5 | 並列処理最適化 | 画像品質・スタイル一貫性 | ビジュアルプレビュー体験 |
| Phase 6 | 高速なテキスト配置 | 可読性・バランス | 細かなカスタマイズ対応 |
| Phase 7 | 高速統合処理 | 全体一貫性・製品品質 | 最終品質確認 |

## 5. フェーズ間データインターフェース仕様

### 5.1 データフロー標準化

**フェーズ間データ契約**

各フェーズ間のデータ交換は以下の標準化されたインターフェースに従います：

```yaml
Data Interface Specification:
  Phase 1 → Phase 2:
    Input Fields:
      - story_context: str (物語の基本コンテキスト)
      - genre: str (ジャンル分類)
      - themes: List[str] (主要テーマ一覧)
      - target_audience: str (対象読者層)

  Phase 2 → Phase 3:
    Input Fields:
      - characters: List[Dict] (キャラクター情報)
        - name: str (キャラクター名)
        - visual_description: str (ビジュアル描写)
        - personality: str (性格特性)
        - role: str (物語での役割)
      - story_context: str (継承される物語コンテキスト)

  Phase 3 → Phase 4:
    Input Fields:
      - scenes: List[Dict] (標準化されたシーン情報)
        - scene_id: int (シーン識別子)
        - description: str (シーン描写)
        - characters: List[str] (登場キャラクター)
        - setting: str (舞台設定)
        - emotion: str (感情トーン)
      - story_structure: Dict (物語構造情報)
      - characters: List[Dict] (キャラクター情報継承)
```

### 5.2 標準化フィールド定義

**重要なフィールド名標準化**

```yaml
Standard Field Names:
  Character Information:
    - characters: List[Dict] (キャラクター情報 - 全フェーズ共通)
    - character_name: str (キャラクター名)
    - character_description: str (キャラクター描写)

  Scene Information:
    - scenes: List[Dict] (シーン情報 - Phase 3出力からPhase 6入力まで統一)
    - scene_id: int (シーン識別子)
    - scene_description: str (シーン描写)

  Panel Information:
    - panels: List[Dict] (パネル情報 - Phase 4からPhase 7まで統一)
    - panel_id: int (パネル識別子)
    - panel_description: str (パネル描写)

  Context Information:
    - story_context: str (物語コンテキスト - 全フェーズ継承)
    - processing_metadata: Dict (処理メタデータ)
      - phase: int (フェーズ番号)
      - timestamp: str (処理時刻)
      - processing_status: str (処理ステータス)
```

---

**関連リンク**:
- [AI設計概要](./ai-overview.md)
- [フェーズ別設計詳細](./phases/)
- [品質制御システム](./quality-control.md)

*最終更新: 2025-01-20*