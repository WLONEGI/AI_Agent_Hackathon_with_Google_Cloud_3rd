# 一時テストファイル

このディレクトリには開発中に作成された一時的なテストファイルが格納されています。

## 移動されたファイル

### ルート直下から移動
- load_test_performance.py - パフォーマンステスト  
- test_preview_interactive_websocket.py - WebSocket統合テスト
- test_websocket_integration.py - WebSocket統合テスト
- manga_service.db - テスト用データベースファイル

### test/ディレクトリから移動
- test_api_endpoints.py - APIエンドポイントテスト
- test_database_setup.py - データベースセットアップテスト  
- test_minimal_main.py - メイン機能テスト

### tests/ディレクトリから移動
- test_ai_integration.py - AI統合テスト
- test_code_validation.py - コード検証テスト
- test_simple_ai.py - AI簡単テスト

## 注意
これらのファイルは開発・デバッグ目的で作成されたものです。
正式なテストはapp/tests/以下の構造化されたテストスイートを使用してください。
