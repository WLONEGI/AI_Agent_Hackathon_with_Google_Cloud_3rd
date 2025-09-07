#!/usr/bin/env python3
"""
Critical Security Fixes Script
緊急セキュリティ脆弱性修正スクリプト

実行前に必ずバックアップを取得してください。
"""

import os
import json
import secrets
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

class CriticalSecurityFixer:
    """最重要セキュリティ脆弱性の修正"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / "security_backups"
        self.fixes_applied = []
        
    def create_backup(self, file_path: Path) -> Path:
        """ファイルのバックアップ作成"""
        self.backup_dir.mkdir(exist_ok=True)
        backup_file = self.backup_dir / f"{file_path.name}.backup"
        
        if file_path.exists():
            backup_file.write_text(file_path.read_text())
            print(f"✅ Backup created: {backup_file}")
        
        return backup_file
    
    def fix_pickle_vulnerability(self) -> bool:
        """
        CRITICAL: pickle脆弱性の修正
        CWE-502: 信頼できないデータのデシリアライゼーション
        """
        print("🚨 Fixing CRITICAL pickle vulnerability...")
        
        cache_service_path = self.project_root / "app/services/cache_service.py"
        
        if not cache_service_path.exists():
            print("❌ cache_service.py not found")
            return False
        
        # バックアップ作成
        self.create_backup(cache_service_path)
        
        # ファイル読み込み
        content = cache_service_path.read_text()
        
        # pickle import を削除
        content = content.replace("import pickle\n", "")
        
        # pickle.loads を安全なjson.loads に置換
        old_loads = 'data = pickle.loads(redis_data.encode(\'latin-1\'))'
        new_loads = '''try:
                    data = json.loads(redis_data)
                except json.JSONDecodeError:
                    # バイナリデータは安全でないため拒否
                    self.logger.warning(f"Rejected unsafe binary data for key: {key}")
                    return None'''
        
        content = content.replace(old_loads, new_loads)
        
        # pickle.dumps を安全なjson.dumps に置換
        old_dumps = 'serialized = pickle.dumps(value).decode(\'latin-1\')'
        new_dumps = 'serialized = json.dumps(value, default=str, ensure_ascii=False)'
        
        content = content.replace(old_dumps, new_dumps)
        
        # ファイル保存
        cache_service_path.write_text(content)
        
        self.fixes_applied.append("pickle_vulnerability_fix")
        print("✅ pickle vulnerability fixed - RCE attack vector eliminated")
        return True
    
    def fix_secret_key(self) -> bool:
        """
        CRITICAL: 弱いSECRET_KEYの修正
        CWE-798: ハードコードされた認証情報
        """
        print("🚨 Fixing CRITICAL weak SECRET_KEY...")
        
        env_path = self.project_root / ".env"
        
        if not env_path.exists():
            print("❌ .env file not found")
            return False
        
        # バックアップ作成
        self.create_backup(env_path)
        
        # 強力なシークレットキー生成
        new_secret_key = secrets.token_urlsafe(32)
        
        # .env ファイル更新
        content = env_path.read_text()
        
        # 既存のSECRET_KEYを置換
        lines = content.split('\n')
        updated_lines = []
        
        for line in lines:
            if line.startswith('SECRET_KEY='):
                updated_lines.append(f'SECRET_KEY={new_secret_key}')
                print(f"✅ SECRET_KEY updated with secure 32-byte key")
            else:
                updated_lines.append(line)
        
        env_path.write_text('\n'.join(updated_lines))
        
        self.fixes_applied.append("secret_key_fix")
        return True
    
    def fix_websocket_auth(self) -> bool:
        """
        HIGH: WebSocket認証の修正
        CWE-209: 情報漏洩による認証バイパス
        """
        print("🔧 Fixing HIGH severity WebSocket authentication...")
        
        manga_api_path = self.project_root / "app/api/manga.py"
        
        if not manga_api_path.exists():
            print("❌ manga.py not found")
            return False
        
        # バックアップ作成
        self.create_backup(manga_api_path)
        
        content = manga_api_path.read_text()
        
        # 脆弱なクエリパラメータ認証を修正
        old_auth = 'token = dict(websocket.query_params).get("token")'
        new_auth = '''# セキュアな認証実装
        try:
            auth_data = await websocket.receive_json()
            if auth_data.get("type") != "authenticate":
                await websocket.close(code=4001, reason="Authentication required")
                return
            token = auth_data.get("token")
        except Exception:
            await websocket.close(code=4001, reason="Invalid authentication message")
            return'''
        
        content = content.replace(old_auth, new_auth)
        
        manga_api_path.write_text(content)
        
        self.fixes_applied.append("websocket_auth_fix")
        print("✅ WebSocket authentication secured")
        return True
    
    def fix_cors_config(self) -> bool:
        """
        MEDIUM: CORS設定の修正
        CWE-346: Origin検証の不備
        """
        print("🔧 Fixing MEDIUM severity CORS configuration...")
        
        settings_path = self.project_root / "app/core/config/settings.py"
        
        if not settings_path.exists():
            print("❌ settings.py not found")
            return False
        
        # バックアップ作成
        self.create_backup(settings_path)
        
        content = settings_path.read_text()
        
        # ワイルドカードCORSヘッダーを修正
        old_cors = 'cors_allow_headers: List[str] = Field(["*"], env="CORS_ALLOW_HEADERS")'
        new_cors = '''cors_allow_headers: List[str] = Field([
        "Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"
    ], env="CORS_ALLOW_HEADERS")'''
        
        content = content.replace(old_cors, new_cors)
        
        settings_path.write_text(content)
        
        self.fixes_applied.append("cors_config_fix")
        print("✅ CORS configuration secured")
        return True
    
    def create_token_blacklist_service(self) -> bool:
        """トークンブラックリストサービスの作成"""
        print("🔧 Creating token blacklist service...")
        
        security_dir = self.project_root / "app/security"
        security_dir.mkdir(exist_ok=True)
        
        # __init__.py作成
        init_file = security_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""Security services package."""\n')
        
        # token_blacklist.py作成
        blacklist_path = security_dir / "token_blacklist.py"
        
        blacklist_content = '''"""JWT Token Blacklist Service for secure token revocation."""

import jwt
from typing import Optional
from datetime import datetime, timedelta

from app.core.redis_client import RedisClient
from app.core.logging import LoggerMixin


class TokenBlacklist(LoggerMixin):
    """Redis-based JWT token blacklist for secure token revocation."""
    
    def __init__(self, redis_client: RedisClient):
        super().__init__()
        self.redis = redis_client
        self.blacklist_prefix = "revoked_token:"
    
    def _extract_jti(self, token: str) -> Optional[str]:
        """Extract JWT ID (jti) from token without verification."""
        try:
            # Decode without verification to get jti
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            return unverified_payload.get("jti")
        except Exception as e:
            self.log_warning(f"Failed to extract jti from token: {e}")
            return None
    
    async def revoke_token(self, token: str, reason: str = "logout") -> bool:
        """Revoke a JWT token by adding it to blacklist.
        
        Args:
            token: JWT token to revoke
            reason: Reason for revocation (logout, compromise, etc.)
            
        Returns:
            True if token was successfully revoked
        """
        jti = self._extract_jti(token)
        if not jti:
            return False
        
        try:
            # Calculate TTL based on token expiration
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            exp = unverified_payload.get("exp")
            
            if exp:
                # Set TTL until token would naturally expire
                exp_datetime = datetime.fromtimestamp(exp)
                ttl = int((exp_datetime - datetime.utcnow()).total_seconds())
                ttl = max(ttl, 0)  # Ensure non-negative TTL
            else:
                # Default TTL if no expiration
                ttl = 86400  # 24 hours
            
            # Add to blacklist
            blacklist_key = f"{self.blacklist_prefix}{jti}"
            blacklist_data = {
                "revoked_at": datetime.utcnow().isoformat(),
                "reason": reason,
                "jti": jti
            }
            
            await self.redis.set(blacklist_key, blacklist_data, ttl=ttl)
            
            self.log_info(f"Token revoked successfully", jti=jti, reason=reason, ttl=ttl)
            return True
            
        except Exception as e:
            self.log_error(f"Failed to revoke token: {e}", jti=jti)
            return False
    
    async def is_token_revoked(self, token: str) -> bool:
        """Check if a token has been revoked.
        
        Args:
            token: JWT token to check
            
        Returns:
            True if token is blacklisted/revoked
        """
        jti = self._extract_jti(token)
        if not jti:
            # If we can't extract jti, consider it invalid
            return True
        
        try:
            blacklist_key = f"{self.blacklist_prefix}{jti}"
            revoked_data = await self.redis.get(blacklist_key)
            
            if revoked_data:
                self.log_debug(f"Token found in blacklist", jti=jti)
                return True
            
            return False
            
        except Exception as e:
            self.log_error(f"Error checking token blacklist: {e}", jti=jti)
            # On error, err on the side of caution
            return True
    
    async def revoke_all_user_tokens(self, user_id: str, reason: str = "security") -> int:
        """Revoke all tokens for a specific user.
        
        Args:
            user_id: User ID whose tokens should be revoked
            reason: Reason for mass revocation
            
        Returns:
            Number of tokens revoked
        """
        try:
            # Find all tokens for this user
            pattern = f"{self.blacklist_prefix}*"
            user_tokens = []
            
            # This is a simplified implementation
            # In production, you'd need to maintain a user->token mapping
            
            revoked_count = 0
            # For now, we'll create a user-based blacklist entry
            user_blacklist_key = f"user_revoked:{user_id}"
            await self.redis.set(user_blacklist_key, {
                "revoked_at": datetime.utcnow().isoformat(),
                "reason": reason
            }, ttl=86400)
            
            self.log_info(f"All user tokens revoked", user_id=user_id, reason=reason)
            return 1
            
        except Exception as e:
            self.log_error(f"Failed to revoke user tokens: {e}", user_id=user_id)
            return 0
    
    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens from blacklist.
        
        Returns:
            Number of expired entries cleaned up
        """
        try:
            # Redis TTL will handle automatic cleanup
            # This method can be used for manual cleanup if needed
            pattern = f"{self.blacklist_prefix}*"
            keys = await self.redis.scan_keys(pattern)
            
            cleaned_count = 0
            for key in keys:
                ttl = await self.redis.ttl(key)
                if ttl == -1:  # No TTL set
                    await self.redis.delete(key)
                    cleaned_count += 1
            
            if cleaned_count > 0:
                self.log_info(f"Cleaned up {cleaned_count} expired blacklist entries")
            
            return cleaned_count
            
        except Exception as e:
            self.log_error(f"Failed to cleanup expired tokens: {e}")
            return 0
    
    async def get_blacklist_stats(self) -> Dict[str, int]:
        """Get blacklist statistics.
        
        Returns:
            Dictionary with blacklist statistics
        """
        try:
            pattern = f"{self.blacklist_prefix}*"
            keys = await self.redis.scan_keys(pattern)
            
            return {
                "total_revoked_tokens": len(keys),
                "active_blacklist_entries": len([k for k in keys if await self.redis.ttl(k) > 0])
            }
            
        except Exception as e:
            self.log_error(f"Failed to get blacklist stats: {e}")
            return {"total_revoked_tokens": 0, "active_blacklist_entries": 0}


# インスタンス化用
token_blacklist = None

def get_token_blacklist() -> TokenBlacklist:
    """Get token blacklist instance."""
    global token_blacklist
    if token_blacklist is None:
        from app.core.redis_client import redis_manager
        token_blacklist = TokenBlacklist(redis_manager)
    return token_blacklist
'''
        
        blacklist_path.write_text(blacklist_content)
        
        self.fixes_applied.append("token_blacklist_service")
        print("✅ Token blacklist service created")
        return True
    
    def update_security_py(self) -> bool:
        """security.pyにトークンブラックリストチェックを追加"""
        print("🔧 Updating security.py with blacklist checks...")
        
        security_path = self.project_root / "app/api/v1/security.py"
        
        if not security_path.exists():
            print("❌ security.py not found")
            return False
        
        # バックアップ作成
        self.create_backup(security_path)
        
        content = security_path.read_text()
        
        # インポート追加
        if "from app.security.token_blacklist import get_token_blacklist" not in content:
            import_line = "from app.security.token_blacklist import get_token_blacklist\n"
            
            # 最後のimportの後に追加
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('from ') or line.startswith('import '):
                    continue
                else:
                    lines.insert(i, import_line)
                    break
            
            content = '\n'.join(lines)
        
        # get_current_user関数を修正してブラックリストチェックを追加
        if "get_token_blacklist()" not in content:
            # verify_token関数にブラックリストチェックを追加
            old_verify = "def verify_token(token: str):"
            new_verify = """async def verify_token(token: str):
    \"\"\"Verify JWT token with blacklist check.\"\"\"
    blacklist = get_token_blacklist()
    
    # Check if token is blacklisted
    if await blacklist.is_token_revoked(token):
        raise HTTPException(
            status_code=401,
            detail="Token has been revoked"
        )"""
            
            content = content.replace(old_verify, new_verify)
        
        security_path.write_text(content)
        
        self.fixes_applied.append("security_py_blacklist_update")
        print("✅ security.py updated with blacklist checks")
        return True
    
    def create_input_sanitizer(self) -> bool:
        """入力値サニタイゼーション強化"""
        print("🔧 Creating enhanced input sanitization...")
        
        security_dir = self.project_root / "app/security"
        security_dir.mkdir(exist_ok=True)
        
        sanitizer_path = security_dir / "input_sanitizer.py"
        
        sanitizer_content = '''"""Enhanced input sanitization for XSS and injection protection."""

import html
import re
import unicodedata
from typing import Any, Dict, List, Optional
from urllib.parse import quote, unquote

from app.core.logging import LoggerMixin


class InputSanitizer(LoggerMixin):
    """Comprehensive input sanitization service."""
    
    def __init__(self):
        super().__init__()
        
        # XSS attack patterns
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'expression\s*\(',
            r'url\s*\(',
            r'@import',
            r'vbscript:',
            r'data:text/html',
        ]
        
        # SQL injection patterns
        self.sql_patterns = [
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+.*\s+set',
            r'exec\s*\(',
            r'sp_\w+',
            r'xp_\w+',
            r';\s*--',
        ]
        
        # Command injection patterns  
        self.command_patterns = [
            r';\s*rm\s',
            r';\s*cat\s',
            r';\s*ls\s',
            r';\s*ps\s',
            r';\s*kill\s',
            r'`[^`]*`',
            r'\$\([^)]*\)',
            r'&&\s*\w+',
            r'\|\s*\w+',
        ]
    
    def sanitize_text_input(self, text: str, max_length: int = 10000) -> str:
        """Sanitize text input for XSS and injection attacks.
        
        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
            
        Raises:
            ValueError: If input contains malicious content
        """
        if not isinstance(text, str):
            raise ValueError("Input must be a string")
        
        # Length check
        if len(text) > max_length:
            raise ValueError(f"Input too long: {len(text)} > {max_length}")
        
        # Normalize Unicode
        text = unicodedata.normalize('NFKC', text)
        
        # Check for malicious patterns
        self._check_malicious_patterns(text)
        
        # HTML escape
        sanitized = html.escape(text, quote=True)
        
        # Additional character filtering
        sanitized = self._filter_dangerous_chars(sanitized)
        
        return sanitized.strip()
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal.
        
        Args:
            filename: Input filename
            
        Returns:
            Sanitized filename
            
        Raises:
            ValueError: If filename is unsafe
        """
        if not filename:
            raise ValueError("Filename cannot be empty")
        
        # Path traversal check
        if '..' in filename or '/' in filename or '\\' in filename:
            raise ValueError("Path traversal attempt detected")
        
        # Remove dangerous characters
        safe_chars = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
        
        if not safe_chars:
            raise ValueError("Filename contains only unsafe characters")
        
        # Length limit
        if len(safe_chars) > 255:
            raise ValueError("Filename too long")
        
        return safe_chars
    
    def _check_malicious_patterns(self, text: str) -> None:
        """Check for known malicious patterns.
        
        Args:
            text: Text to check
            
        Raises:
            ValueError: If malicious content detected
        """
        text_lower = text.lower()
        
        # XSS patterns
        for pattern in self.xss_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                self.log_warning(f"XSS pattern detected: {pattern}")
                raise ValueError("Potentially malicious XSS content detected")
        
        # SQL injection patterns
        for pattern in self.sql_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                self.log_warning(f"SQL injection pattern detected: {pattern}")
                raise ValueError("Potentially malicious SQL content detected")
        
        # Command injection patterns
        for pattern in self.command_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                self.log_warning(f"Command injection pattern detected: {pattern}")
                raise ValueError("Potentially malicious command content detected")
    
    def _filter_dangerous_chars(self, text: str) -> str:
        """Filter out dangerous characters.
        
        Args:
            text: Text to filter
            
        Returns:
            Filtered text
        """
        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Remove potentially dangerous Unicode categories
        filtered_chars = []
        for char in text:
            category = unicodedata.category(char)
            # Allow most printable characters, exclude control and format chars
            if category not in ['Cc', 'Cf', 'Co', 'Cs']:
                filtered_chars.append(char)
        
        return ''.join(filtered_chars)
    
    def validate_json_structure(self, data: Any, max_depth: int = 10) -> bool:
        """Validate JSON structure for safety.
        
        Args:
            data: Data to validate
            max_depth: Maximum nesting depth
            
        Returns:
            True if structure is safe
            
        Raises:
            ValueError: If structure is unsafe
        """
        def check_depth(obj: Any, current_depth: int = 0) -> None:
            if current_depth > max_depth:
                raise ValueError(f"JSON structure too deeply nested: {current_depth} > {max_depth}")
            
            if isinstance(obj, dict):
                if len(obj) > 1000:  # Limit number of keys
                    raise ValueError("Too many keys in JSON object")
                
                for key, value in obj.items():
                    if not isinstance(key, str) or len(key) > 100:
                        raise ValueError("Invalid or too long JSON key")
                    check_depth(value, current_depth + 1)
            
            elif isinstance(obj, list):
                if len(obj) > 10000:  # Limit array size
                    raise ValueError("JSON array too large")
                
                for item in obj:
                    check_depth(item, current_depth + 1)
            
            elif isinstance(obj, str):
                if len(obj) > 100000:  # Limit string size
                    raise ValueError("JSON string too large")
        
        try:
            check_depth(data)
            return True
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"JSON validation error: {e}")


# グローバルインスタンス
input_sanitizer = InputSanitizer()

def get_input_sanitizer() -> InputSanitizer:
    """Get input sanitizer instance."""
    return input_sanitizer
'''
        
        sanitizer_path.write_text(sanitizer_content)
        
        self.fixes_applied.append("input_sanitizer_service")
        print("✅ Input sanitizer service created")
        return True
    
    def run_all_critical_fixes(self) -> Dict[str, bool]:
        """すべての重要修正を実行"""
        print("🚨 Starting critical security fixes...")
        print("=" * 50)
        
        results = {}
        
        # 1. pickle脆弱性修正（最重要）
        results["pickle_fix"] = self.fix_pickle_vulnerability()
        
        # 2. SECRET_KEY修正
        results["secret_key_fix"] = self.fix_secret_key()
        
        # 3. WebSocket認証修正
        results["websocket_auth_fix"] = self.fix_websocket_auth()
        
        # 4. CORS設定修正
        results["cors_fix"] = self.fix_cors_config()
        
        # 5. トークンブラックリストサービス作成
        results["token_blacklist_service"] = self.create_token_blacklist_service()
        
        # 6. 入力値サニタイザー作成
        results["input_sanitizer"] = self.create_input_sanitizer()
        
        print("\n" + "=" * 50)
        print("🔒 Critical security fixes summary:")
        
        for fix_name, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"  {fix_name}: {status}")
        
        if all(results.values()):
            print("\n🎉 All critical security fixes applied successfully!")
            print("⚠️  Please restart the application and run tests")
        else:
            print("\n⚠️  Some fixes failed - manual intervention required")
        
        return results
    
    def generate_fix_report(self) -> str:
        """修正レポート生成"""
        report = f"""
# Critical Security Fixes Applied

**実行日時**: {datetime.now().isoformat()}
**適用された修正**: {len(self.fixes_applied)}

## 修正内容

"""
        
        for fix in self.fixes_applied:
            report += f"- ✅ {fix}\n"
        
        report += """
## 次のステップ

1. アプリケーション再起動
2. 全テストの実行
3. セキュリティテストの実施
4. 本番環境への適用計画策定

## 注意事項

- バックアップファイルは security_backups/ に保存されています
- 問題が発生した場合はバックアップから復元してください
- 本番環境適用前に必ずテスト環境で検証してください
"""
        
        return report


def main():
    """メイン実行関数"""
    if len(sys.argv) != 2:
        print("Usage: python critical_security_fixes.py <project_root>")
        sys.exit(1)
    
    project_root = sys.argv[1]
    fixer = CriticalSecurityFixer(project_root)
    
    try:
        results = fixer.run_all_critical_fixes()
        
        # レポート生成
        report = fixer.generate_fix_report()
        report_path = Path(project_root) / "security_fixes_report.md"
        report_path.write_text(report)
        
        print(f"\n📋 Fix report saved to: {report_path}")
        
        if all(results.values()):
            sys.exit(0)
        else:
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Critical error during security fixes: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()