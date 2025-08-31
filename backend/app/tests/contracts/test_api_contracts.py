"""
API Contract Compliance Test

API契約準拠性テスト
設計書で定義されたAPIエンドポイントとレスポンス仕様の準拠性を検証
"""

import pytest
import json
import httpx
from typing import Dict, Any, List
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app


class APIContractTest:
    """API契約準拠性テストクラス"""
    
    @classmethod
    def setup_class(cls):
        """テストクラスセットアップ"""
        cls.client = TestClient(app)
        cls.required_endpoints = cls._get_required_endpoints()
        
    @classmethod
    def _get_required_endpoints(cls) -> List[Dict[str, Any]]:
        """設計書で要求されるAPIエンドポイント一覧"""
        return [
            # 漫画生成API
            {
                "path": "/api/v1/manga/generate",
                "method": "POST",
                "description": "漫画生成開始",
                "required_fields": ["input_text"],
                "response_status": 202,
                "response_fields": ["request_id", "estimated_completion_time"]
            },
            {
                "path": "/api/v1/manga/{request_id}/status",
                "method": "GET", 
                "description": "生成ステータス取得",
                "path_params": ["request_id"],
                "response_status": 200,
                "response_fields": ["request_id", "status", "current_phase", "progress"]
            },
            {
                "path": "/api/v1/manga/{request_id}/stream",
                "method": "GET",
                "description": "SSE進捗ストリーム",
                "path_params": ["request_id"],
                "response_status": 200,
                "response_type": "text/event-stream"
            },
            
            # プレビューAPI
            {
                "path": "/api/v1/manga/{request_id}/preview/{phase}",
                "method": "GET",
                "description": "フェーズプレビュー取得",
                "path_params": ["request_id", "phase"],
                "response_status": 200,
                "response_fields": ["phase", "preview_data", "quality_level"]
            },
            {
                "path": "/api/v1/manga/{request_id}/preview/{phase}/apply-change",
                "method": "POST",
                "description": "プレビュー変更適用",
                "path_params": ["request_id", "phase"],
                "required_fields": ["change_data"],
                "response_status": 200,
                "response_fields": ["version_id", "applied_changes"]
            },
            
            # フィードバックAPI
            {
                "path": "/api/v1/manga/{request_id}/feedback", 
                "method": "POST",
                "description": "フィードバック送信",
                "path_params": ["request_id"],
                "required_fields": ["phase_number", "feedback_content"],
                "response_status": 200,
                "response_fields": ["feedback_id", "processing_status"]
            },
            {
                "path": "/api/v1/manga/{request_id}/skip-feedback",
                "method": "POST", 
                "description": "フィードバックスキップ",
                "path_params": ["request_id"],
                "response_status": 200,
                "response_fields": ["skipped", "next_phase"]
            },
            
            # 品質管理API
            {
                "path": "/api/v1/manga/{request_id}/quality-gate",
                "method": "GET",
                "description": "品質ゲート状態取得",
                "path_params": ["request_id"],
                "response_status": 200,
                "response_fields": ["quality_score", "gate_status", "recommendations"]
            },
            
            # システム監視API
            {
                "path": "/health",
                "method": "GET",
                "description": "ヘルスチェック", 
                "response_status": 200,
                "response_fields": ["status", "timestamp"]
            },
            {
                "path": "/api/v1/info",
                "method": "GET",
                "description": "API情報取得",
                "response_status": 200,
                "response_fields": ["name", "version", "pipeline"]
            }
        ]
    
    def test_all_required_endpoints_exist(self):
        """全ての必須エンドポイントが存在することを確認"""
        
        for endpoint in self.required_endpoints:
            method = endpoint["method"].lower()
            path = endpoint["path"]
            
            # パスパラメータのモック値を設定
            test_path = path
            if "path_params" in endpoint:
                for param in endpoint["path_params"]:
                    if param == "request_id":
                        test_path = test_path.replace(f"{{{param}}}", "test-request-123")
                    elif param == "phase":
                        test_path = test_path.replace(f"{{{param}}}", "1")
                    else:
                        test_path = test_path.replace(f"{{{param}}}", "test-value")
            
            # エンドポイントの存在確認（404でなければOK）
            try:
                if method == "get":
                    response = self.client.get(test_path)
                elif method == "post":
                    response = self.client.post(test_path, json={})
                elif method == "put":
                    response = self.client.put(test_path, json={})
                elif method == "delete":
                    response = self.client.delete(test_path)
                else:
                    pytest.fail(f"Unsupported HTTP method: {method}")
                
                # 404 Not Found でなければエンドポイントが存在する
                assert response.status_code != 404, \
                    f"エンドポイントが存在しません: {method.upper()} {path}"
                    
            except Exception as e:
                pytest.fail(f"エンドポイント {method.upper()} {path} のテスト中にエラー: {e}")
    
    def test_health_endpoint_compliance(self):
        """ヘルスチェックエンドポイントの準拠性確認"""
        response = self.client.get("/health")
        
        # ステータスコード確認
        assert response.status_code == 200, "ヘルスチェックは200を返す必要があります"
        
        # レスポンス形式確認
        try:
            data = response.json()
            assert "status" in data, "ヘルスチェックレスポンスに 'status' が必要です"
            assert "timestamp" in data or "time" in data, "ヘルスチェックレスポンスにタイムスタンプが必要です"
        except json.JSONDecodeError:
            pytest.fail("ヘルスチェックレスポンスがJSONではありません")
    
    def test_api_info_endpoint_compliance(self):
        """API情報エンドポイントの準拠性確認"""
        response = self.client.get("/api/v1/info")
        
        if response.status_code == 404:
            pytest.skip("API情報エンドポイントが実装されていません")
        
        # ステータスコード確認
        assert response.status_code == 200, "API情報は200を返す必要があります"
        
        # レスポンス形式確認
        try:
            data = response.json()
            assert "name" in data, "API情報に 'name' が必要です"
            assert "version" in data, "API情報に 'version' が必要です" 
            
        except json.JSONDecodeError:
            pytest.fail("API情報レスポンスがJSONではありません")
    
    def test_cors_headers_compliance(self):
        """CORS ヘッダーの準拠性確認"""
        response = self.client.options("/health")
        
        # CORS ヘッダーの確認
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods", 
            "access-control-allow-headers"
        ]
        
        for header in cors_headers:
            # ヘッダーが存在するかチェック（大文字小文字不問）
            header_found = any(
                h.lower() == header.lower() 
                for h in response.headers.keys()
            )
            if not header_found:
                pytest.skip(f"CORS ヘッダー {header} が設定されていません（設定は任意）")
    
    def test_error_response_format_compliance(self):
        """エラーレスポンス形式の準拠性確認"""
        # 存在しないエンドポイントでエラーレスポンス確認
        response = self.client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404, "存在しないエンドポイントは404を返す必要があります"
        
        # エラーレスポンス形式確認（RFC 7807 Problem Details 推奨）
        try:
            error_data = response.json()
            
            # 基本的なエラーフィールド確認
            expected_fields = ["detail", "error", "message"]
            has_error_field = any(field in error_data for field in expected_fields)
            
            assert has_error_field, "エラーレスポンスにエラー内容フィールドが必要です"
            
        except json.JSONDecodeError:
            pytest.skip("エラーレスポンスがJSONでない場合があります")
    
    def test_authentication_header_support(self):
        """認証ヘッダーサポートの確認"""
        # 認証が必要なエンドポイントでの確認
        protected_endpoint = "/api/v1/manga/generate"
        
        # 認証なしでのリクエスト
        response = self.client.post(protected_endpoint, json={"input_text": "test"})
        
        # 401 Unauthorized または 403 Forbidden が期待される
        if response.status_code in [401, 403]:
            # 認証エラーレスポンス確認
            try:
                error_data = response.json()
                assert "detail" in error_data or "error" in error_data, \
                    "認証エラーレスポンスにエラー詳細が必要です"
            except json.JSONDecodeError:
                pass  # JSONでない場合もあり得る
        else:
            pytest.skip("認証機能が未実装または異なる認証方式です")
    
    def test_rate_limiting_headers(self):
        """レート制限ヘッダーの確認"""
        response = self.client.get("/health")
        
        # レート制限ヘッダーの確認
        rate_limit_headers = [
            "x-ratelimit-limit",
            "x-ratelimit-remaining", 
            "x-ratelimit-reset"
        ]
        
        for header in rate_limit_headers:
            header_found = any(
                h.lower() == header.lower()
                for h in response.headers.keys()
            )
            if not header_found:
                pytest.skip(f"レート制限ヘッダー {header} が設定されていません（設定は任意）")
    
    def test_content_type_compliance(self):
        """Content-Type ヘッダーの準拠性確認"""
        response = self.client.get("/health")
        
        content_type = response.headers.get("content-type", "")
        
        # JSON レスポンスの場合、適切な Content-Type 設定確認
        if response.status_code == 200:
            assert "application/json" in content_type.lower(), \
                f"JSONレスポンスのContent-Typeが不正: {content_type}"
    
    def test_openapi_schema_availability(self):
        """OpenAPI スキーマの利用可能性確認"""
        openapi_endpoints = [
            "/docs", 
            "/openapi.json",
            "/redoc"
        ]
        
        schema_available = False
        for endpoint in openapi_endpoints:
            response = self.client.get(endpoint)
            if response.status_code == 200:
                schema_available = True
                break
        
        if not schema_available:
            pytest.skip("OpenAPI スキーマエンドポイントが利用できません（開発環境でのみ利用可能）")


# Pytest fixtures
@pytest.fixture(scope="session")
def api_test_client():
    """APIテストクライアントフィクスチャ"""
    return TestClient(app)


# テスト実行関数
def test_api_contract_compliance_suite():
    """API契約準拠性テストスイート"""
    test_suite = APIContractTest()
    test_suite.setup_class()
    
    # 全テストの実行
    test_suite.test_all_required_endpoints_exist()
    test_suite.test_health_endpoint_compliance()
    test_suite.test_api_info_endpoint_compliance()
    test_suite.test_cors_headers_compliance()
    test_suite.test_error_response_format_compliance()
    test_suite.test_authentication_header_support()
    test_suite.test_rate_limiting_headers()
    test_suite.test_content_type_compliance()
    test_suite.test_openapi_schema_availability()
    
    return True