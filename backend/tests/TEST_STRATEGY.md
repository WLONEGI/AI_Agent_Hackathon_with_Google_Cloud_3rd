# Backend Design Compliance Testing Strategy

設計書準拠性テストの実施方針とツール使用方法

## 概要

このテスト戦略は、バックエンド実装が設計書の要件に準拠していることを自動検証するためのフレームワークです。継続的インテグレーション（CI/CD）に統合され、設計仕様からの逸脱を早期に検出します。

## テスト構成

### 1. テストカテゴリ

| カテゴリ | 目的 | テストファイル |
|---------|------|--------------|
| **Design Compliance** | 設計書要件準拠性 | `tests/compliance/test_design_requirements.py` |
| **Phase Pipeline** | 7フェーズパイプライン検証 | `tests/compliance/test_phase_pipeline_compliance.py` |
| **HITL System** | Human-in-the-Loop機能 | `tests/compliance/test_hitl_compliance.py` |
| **API Contracts** | API仕様準拠性 | `tests/contracts/test_api_contracts.py` |
| **Architecture** | アーキテクチャパターン | `tests/compliance/test_architecture_compliance.py` |

### 2. 準拠性カテゴリ

#### 🔴 Critical (重要度: 高)
- **フェーズパイプライン**: 7フェーズ構成とAIモデル統合
- **HITL システム**: クリティカルフェーズでのフィードバック機能
- **品質ゲート**: 各フェーズでの品質管理

#### 🟡 Important (重要度: 中)
- **API契約**: エンドポイント仕様とレスポンス形式
- **アーキテクチャパターン**: DDD・CQRS実装
- **WebSocket統合**: リアルタイム通信

#### 🟢 Recommended (重要度: 低)
- **コード品質**: 命名規則とファイル構成
- **ドキュメント**: API仕様書との整合性
- **パフォーマンス**: レスポンス時間要件

## 使用方法

### ローカル実行

```bash
# 全テスト実行
./test.sh

# 特定のテストスイート実行
./test.sh -s compliance
./test.sh -s contracts

# 詳細出力付き実行
./test.sh -v

# レポートのみ生成
./test.sh -r

# ヘルプ表示
./test.sh -h
```

### Python直接実行

```bash
# 全テスト実行
python run_compliance_tests.py

# オプション付き実行
python run_compliance_tests.py --suite compliance --output-dir results

# レポート生成のみ
python run_compliance_tests.py --report-only
```

### CI/CD統合

GitHub Actionsワークフローが自動実行:

- **トリガー**: `backend/**` フォルダの変更時
- **実行環境**: Python 3.11, 3.12
- **アーティファクト**: テスト結果、HTMLレポート
- **品質ゲート**: 95%以上の準拠率でデプロイ承認

## 出力ファイル

### テスト結果

```
test_results/
├── compliance-results.xml      # JUnit形式テスト結果
├── contracts-results.xml       # API契約テスト結果
├── test_summary.json          # 実行サマリー
├── compliance_report.html     # HTML準拠性レポート
└── compliance_report.json     # JSON準拠性レポート
```

### レポート内容

- **総合準拠度**: 全カテゴリの重み付き平均
- **カテゴリ別スコア**: 各テスト領域の詳細評価
- **推奨事項**: 準拠性向上のための具体的アクション
- **実装ステータス**: 各要件の実装状況

## テスト要件定義

### YAML設定ファイル

`tests/compliance/fixtures/design_requirements.yaml` で要件定義:

```yaml
phase_pipeline:
  total_phases: 7
  required_phases:
    - phase_number: 1
      name: "コンセプト・世界観分析"
      ai_model: "gemini-pro"
      timeout_seconds: 30

hitl_requirements:
  feedback_timeout_seconds: 30
  critical_phases: [4, 5, 7]
  feedback_types:
    - "natural_language"
    - "quick_options" 
    - "skip"

api_requirements:
  required_endpoints:
    - path: "/api/v1/manga/generate"
      method: "POST"
      response_status: 202
```

## カスタマイズ

### 新しいテストの追加

1. `tests/compliance/` にテストファイル作成
2. `ComplianceTest` クラスを継承
3. `design_requirements.yaml` に要件追加
4. `__init__.py` にテストクラス追加

### レポート設定変更

`app/tests/reports/compliance_reporter.py` で以下を調整:

- 重み付け係数 (`CATEGORY_WEIGHTS`)
- 合格基準 (`PASS_THRESHOLD`)
- 推奨事項テンプレート (`RECOMMENDATIONS`)

### CI/CD設定調整

`.github/workflows/backend-compliance-tests.yml` で:

- 実行トリガー条件
- Python版本マトリックス
- デプロイメントゲート基準

## トラブルシューティング

### 一般的な問題

#### テスト失敗時の対処

```bash
# 詳細ログで問題特定
./test.sh -v -s compliance

# 個別テスト実行
python -m pytest tests/compliance/test_design_requirements.py -v
```

#### 依存関係エラー

```bash
# 必要パッケージインストール
pip install pytest pytest-asyncio pyyaml jinja2

# 要件ファイルから一括インストール
pip install -r requirements-test.txt
```

#### 設定ファイル問題

- `design_requirements.yaml` の構文確認
- パスの正確性検証
- 権限問題の確認

### パフォーマンス最適化

#### テスト実行時間短縮

- 並列実行: `pytest -n auto`
- 選択的実行: `pytest -m "not slow"`
- キャッシュ利用: `pytest --cache-dir=.pytest_cache`

#### レポート生成最適化

- テンプレートキャッシュ有効化
- 大量データの分割処理
- 非同期レポート生成

## セキュリティ考慮事項

- 機密情報のテストデータからの除外
- 認証情報の環境変数化
- テスト結果の適切な権限管理
- CI/CDシークレットの安全な管理

## メンテナンス

### 定期的な更新

- **月次**: テスト要件の見直し
- **リリース毎**: 設計書との同期
- **四半期**: パフォーマンス評価
- **年次**: テスト戦略全体見直し

### 設計書変更時の対応

1. `design_requirements.yaml` 更新
2. 関連テストケース修正
3. レポートテンプレート調整
4. CI/CD設定見直し

## 参考資料

- [設計書](../docs/05.API設計書.md)
- [アーキテクチャ設計](../docs/04.システム設計書.md) 
- [AI設計仕様](../docs/08.AI設計書.md)
- [pytest Documentation](https://docs.pytest.org/)
- [GitHub Actions Guide](https://docs.github.com/actions)