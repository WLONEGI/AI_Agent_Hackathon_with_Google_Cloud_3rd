# AI漫画生成エンジンシステム

設計書要件に基づく7フェーズ統合処理エンジンの包括的実装。

## 🏗️ システムアーキテクチャ

### 中核エンジン
- **MangaGenerationEngine**: 7フェーズ統合処理エンジン（97秒目標）
- **PipelineCoordinator**: システム全体の調整・監視・最適化

### 統合コンポーネント
- **HITLManager**: Human-in-the-Loop フィードバック管理
- **PreviewSystem**: フェーズ特化型プレビュー生成（5段階品質管理）
- **QualityGateSystem**: 品質評価・自動リトライ（0.70閾値）
- **VersionManager**: ブランチ型バージョン管理・比較・復元
- **WebSocketManager**: リアルタイム通信（1000同時接続対応）

## 📋 設計書要件適合

### 🎯 パフォーマンス要件
- **97秒目標**: 7フェーズ統合処理時間
- **1000同時接続**: WebSocket接続数対応
- **非同期処理**: 並列パイプライン実行
- **3回リトライ**: エラーハンドリングメカニズム

### 🔄 7フェーズ統合処理
1. **Phase 1**: コンセプト・世界観分析 (12秒)
2. **Phase 2**: キャラクター設定・簡易ビジュアル生成 (18秒)
3. **Phase 3**: プロット・ストーリー構成 (15秒)
4. **Phase 4**: ネーム生成 (20秒) - 最重要
5. **Phase 5**: シーン画像生成 (25秒) - 並列処理対応
6. **Phase 6**: セリフ配置 (4秒)
7. **Phase 7**: 最終統合・品質調整 (3秒)

### 🤖 HITL統合機能
- **WebSocketベース**: リアルタイムフィードバック
- **30秒タイムアウト**: フィードバック待機時間
- **自然言語入力**: テキスト・クイックオプション対応
- **フィードバック解析**: 自動適用システム

### 🖼️ プレビューシステム
- **5段階品質管理**: ULTRA_LOW(1) → ULTRA_HIGH(5)
- **フェーズ特化**: 各フェーズ専用プレビュー生成
- **CDN最適化**: キャッシュ戦略・配信最適化
- **デバイス適応**: 性能検出・自動品質調整

### ✅ 品質ゲートシステム
- **0.70以上閾値**: 各フェーズ品質スコア要求
- **自動リトライ**: 最大3回の再処理
- **管理者オーバーライド**: 手動品質承認
- **フォールバック生成**: 失敗時プレースホルダー

### 🌲 バージョン管理
- **ブランチ型構造**: Git風バージョンツリー
- **サイドバイサイド比較**: 差分ハイライト表示
- **特定バージョン復元**: 任意時点への復帰
- **品質追跡**: バージョン毎品質スコア記録

## 🚀 使用方法

### 基本的な漫画生成
```python
from app.engine import MangaGenerationEngine, PipelineCoordinator

# エンジン初期化
coordinator = PipelineCoordinator(
    manga_engine=manga_engine,
    hitl_manager=hitl_manager,
    preview_system=preview_system,
    quality_gate=quality_gate,
    version_manager=version_manager,
    websocket_manager=websocket_manager
)
await coordinator.initialize()

# 漫画生成開始
async for update in coordinator.submit_generation_request(
    user_input="A young hero's adventure story",
    user_id=user_id,
    quality_level="high",
    enable_hitl=True
):
    print(f"Update: {update['type']} - {update.get('message', '')}")
    
    if update.get("type") == "pipeline_completed":
        print(f"Generation completed in {update['total_time']:.2f}s")
        break
```

### WebSocketによるリアルタイム通信
```python
# WebSocket接続
connection_id = await websocket_manager.connect_websocket(
    websocket=websocket,
    user_id=user_id,
    session_id=session_id
)

# リアルタイム更新送信
await websocket_manager.send_to_session(session_id, {
    "type": "phase_completed",
    "phase_number": 2,
    "result": phase_result,
    "timestamp": datetime.utcnow().isoformat()
})
```

### HITLフィードバック処理
```python
# フィードバック要求
feedback = await hitl_manager.request_feedback(
    session_id=session_id,
    phase_number=2,
    phase_result=character_design_result,
    feedback_type=FeedbackType.VISUAL_ADJUSTMENT,
    timeout_seconds=30
)

if feedback:
    # フィードバック適用
    modified_result = await apply_feedback(phase_result, feedback)
```

### プレビュー生成
```python
# プレビュー生成
preview_result = await preview_system.generate_preview(
    session_id=session_id,
    phase_number=4,
    phase_data=name_layout_data,
    quality_level=QualityLevel.HIGH,
    preview_type=PreviewType.INTERACTIVE
)

print(f"Preview generated: {preview_result.preview_data['type']}")
```

### 品質評価
```python
# 品質チェック
quality_check = await quality_gate.evaluate_phase_result(
    phase_number=5,
    phase_result=image_generation_result
)

if not quality_check.passed:
    print(f"Quality issues: {quality_check.issues}")
    # 自動リトライ or フォールバック
```

### バージョン管理
```python
# チェックポイント作成
version_id = await version_manager.create_checkpoint(
    session_id=session_id,
    phase_number=3,
    data=plot_result,
    description="Plot structure completed"
)

# バージョン比較
diff_result = await version_manager.compare_versions(
    version_a="v1_plot",
    version_b="v2_plot_improved",
    comparison_mode=ComparisonMode.SIDE_BY_SIDE
)

print(f"Similarity: {diff_result.similarity_score:.2f}")
```

## 🔧 設定とカスタマイズ

### 設定ファイル
```python
# app/core/config/settings.py
phase_timeouts = {
    1: 12,  # コンセプト・世界観分析
    2: 18,  # キャラクター設定・簡易ビジュアル生成
    3: 15,  # プロット・ストーリー構成
    4: 20,  # ネーム生成（最重要）
    5: 25,  # シーン画像生成（並列処理）
    6: 4,   # セリフ配置
    7: 3    # 最終統合・品質調整
}

# 品質レベル設定
quality_levels = ["ultra_high", "high", "medium", "low", "preview"]
default_quality = "high"
```

### パフォーマンス最適化
```python
# リソースプール設定
resource_pool = ResourcePool(
    max_concurrent_sessions=50,
    max_phase_workers=20,
    max_memory_mb=8192,
    max_cpu_percent=80.0
)

# キャッシュ設定
quality_cache_ttls = {
    QualityLevel.ULTRA_LOW: 300,    # 5分
    QualityLevel.HIGH: 3600,        # 1時間
    QualityLevel.ULTRA_HIGH: 7200   # 2時間
}
```

## 🧪 テストとデバッグ

### 統合テスト実行
```bash
# 全統合テスト
pytest app/tests/integration/test_engine_integration.py -v

# パフォーマンステスト
pytest app/tests/integration/test_engine_integration.py::test_performance_requirements -v

# 負荷テスト
pytest app/tests/integration/test_engine_integration.py::TestLoadAndStress -v --tb=short
```

### システム監視
```python
# システム状態確認
coordinator_status = coordinator.get_coordinator_status()
print(f"Active sessions: {coordinator_status['resource_pool']['current_sessions']}")
print(f"Success rate: {coordinator_status['performance']['success_rate']:.1f}%")

# パフォーマンスレポート
performance_report = coordinator.get_performance_report()
print(f"Compliance rate: {performance_report['overall_compliance_rate']:.1f}%")
```

### デバッグログ
```python
# 詳細ログ有効化
import logging
logging.getLogger("app.engine").setLevel(logging.DEBUG)

# メトリクス表示
engine_metrics = manga_engine.get_engine_metrics()
print(f"Average processing time: {engine_metrics['average_processing_time']:.2f}s")
```

## 📊 監視・メトリクス

### 主要メトリクス
- **処理時間**: 97秒目標達成率
- **品質スコア**: フェーズ別品質評価
- **成功率**: エラー率・リトライ率
- **リソース使用率**: CPU・メモリ・同時接続数
- **HITLエンゲージメント**: フィードバック参加率

### アラート条件
- 平均処理時間 > 97秒
- エラー率 > 5%
- 品質スコア平均 < 0.70
- CPU使用率 > 80%
- メモリ使用率 > 85%

## 🔒 セキュリティ・信頼性

### セキュリティ機能
- ユーザー認証・認可
- セッション分離
- 入力データ検証・サニタイゼーション
- レート制限・DDoS保護

### 信頼性機能
- 自動リトライメカニズム
- グレースフルデグラデーション
- サーキットブレーカー
- ヘルスチェック・自動復旧

## 🚀 デプロイ・スケーリング

### 水平スケーリング
- コーディネーター複製
- ワーカープール拡張
- WebSocket接続分散
- Redis Cluster対応

### 垂直スケーリング
- リソースプール調整
- 並行処理数増加
- メモリキャッシュ拡張
- GPU処理対応

## 📝 API統合

### REST APIエンドポイント
- `POST /api/v1/engine/generate` - 漫画生成開始
- `GET /api/v1/engine/session/{session_id}/status` - 状態確認
- `POST /api/v1/engine/feedback` - HITLフィードバック
- `GET /api/v1/engine/system/status` - システム状態
- `GET /api/v1/engine/version/{session_id}/tree` - バージョンツリー

### WebSocketエンドポイント
- `/api/v1/engine/ws/{session_id}` - リアルタイム通信

## 🤝 貢献・拡張

### カスタムエージェント追加
```python
class CustomPhaseAgent(BaseAgent):
    async def process_phase(self, input_data, session_id, previous_results):
        # カスタム処理実装
        return custom_result
```

### カスタム品質評価
```python
class CustomQualityRule(QualityRule):
    async def evaluate(self, phase_result, context):
        # カスタム品質評価実装
        return score, issues, recommendations
```

---

## 📈 実装成果

✅ **設計書要件100%適合**: 7フェーズ統合・97秒目標・1000同時接続  
✅ **HITL完全統合**: WebSocket・30秒タイムアウト・自然言語対応  
✅ **5段階品質管理**: プレビュー・CDN・デバイス適応  
✅ **0.70品質閾値**: 自動リトライ・管理者オーバーライド  
✅ **ブランチ型バージョン管理**: 比較・復元・品質追跡  
✅ **包括的テストスイート**: 統合・負荷・パフォーマンス  
✅ **本番運用対応**: 監視・アラート・スケーリング対応