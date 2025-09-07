"""Security configuration settings."""

from typing import List, Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field, field_validator
import secrets


class SecuritySettings(BaseSettings):
    """Security configuration settings."""
    
    # JWT Configuration
    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(60, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    jwt_issuer: str = Field("manga-service", env="JWT_ISSUER")
    jwt_audience: str = Field("manga-users", env="JWT_AUDIENCE")
    
    # Password Security
    bcrypt_rounds: int = Field(12, env="BCRYPT_ROUNDS")
    password_min_length: int = Field(8, env="PASSWORD_MIN_LENGTH")
    password_require_uppercase: bool = Field(True, env="PASSWORD_REQUIRE_UPPERCASE")
    password_require_lowercase: bool = Field(True, env="PASSWORD_REQUIRE_LOWERCASE")
    password_require_numbers: bool = Field(True, env="PASSWORD_REQUIRE_NUMBERS")
    password_require_symbols: bool = Field(False, env="PASSWORD_REQUIRE_SYMBOLS")
    password_history_count: int = Field(5, env="PASSWORD_HISTORY_COUNT")
    
    # Session Security
    session_cookie_secure: bool = Field(True, env="SESSION_COOKIE_SECURE")
    session_cookie_httponly: bool = Field(True, env="SESSION_COOKIE_HTTPONLY")
    session_cookie_samesite: str = Field("lax", env="SESSION_COOKIE_SAMESITE")
    session_timeout_minutes: int = Field(480, env="SESSION_TIMEOUT_MINUTES")  # 8 hours
    
    # API Security
    api_key_header: str = Field("X-API-Key", env="API_KEY_HEADER")
    api_key_length: int = Field(32, env="API_KEY_LENGTH")
    api_rate_limit_enabled: bool = Field(True, env="API_RATE_LIMIT_ENABLED")
    
    # CORS Security
    cors_max_age: int = Field(86400, env="CORS_MAX_AGE")  # 24 hours
    cors_expose_headers: List[str] = Field(
        ["X-Request-ID", "X-Rate-Limit-Remaining"],
        env="CORS_EXPOSE_HEADERS"
    )
    
    # Content Security Policy
    enable_csp: bool = Field(True, env="ENABLE_CSP")
    csp_default_src: str = Field("'self'", env="CSP_DEFAULT_SRC")
    csp_script_src: str = Field("'self' 'unsafe-inline'", env="CSP_SCRIPT_SRC")
    csp_style_src: str = Field("'self' 'unsafe-inline'", env="CSP_STYLE_SRC")
    csp_img_src: str = Field("'self' data: https:", env="CSP_IMG_SRC")
    csp_connect_src: str = Field("'self' wss: https:", env="CSP_CONNECT_SRC")
    
    # Security Headers
    enable_security_headers: bool = Field(True, env="ENABLE_SECURITY_HEADERS")
    hsts_max_age: int = Field(31536000, env="HSTS_MAX_AGE")  # 1 year
    hsts_include_subdomains: bool = Field(True, env="HSTS_INCLUDE_SUBDOMAINS")
    enable_referrer_policy: bool = Field(True, env="ENABLE_REFERRER_POLICY")
    referrer_policy: str = Field("strict-origin-when-cross-origin", env="REFERRER_POLICY")
    
    # Input Validation
    max_request_size_mb: int = Field(10, env="MAX_REQUEST_SIZE_MB")
    max_file_upload_size_mb: int = Field(5, env="MAX_FILE_UPLOAD_SIZE_MB")
    allowed_file_types: List[str] = Field(
        ["image/jpeg", "image/png", "image/gif", "text/plain"],
        env="ALLOWED_FILE_TYPES"
    )
    
    # Rate Limiting
    rate_limit_per_ip: int = Field(100, env="RATE_LIMIT_PER_IP")
    rate_limit_window_seconds: int = Field(60, env="RATE_LIMIT_WINDOW_SECONDS")
    rate_limit_per_user: int = Field(200, env="RATE_LIMIT_PER_USER")
    burst_rate_limit: int = Field(20, env="BURST_RATE_LIMIT")
    
    # Account Security
    max_login_attempts: int = Field(5, env="MAX_LOGIN_ATTEMPTS")
    lockout_duration_minutes: int = Field(15, env="LOCKOUT_DURATION_MINUTES")
    require_email_verification: bool = Field(True, env="REQUIRE_EMAIL_VERIFICATION")
    enable_2fa: bool = Field(False, env="ENABLE_2FA")
    
    # Data Protection
    enable_data_encryption: bool = Field(True, env="ENABLE_DATA_ENCRYPTION")
    encryption_key: Optional[str] = Field(None, env="ENCRYPTION_KEY")
    enable_audit_logging: bool = Field(True, env="ENABLE_AUDIT_LOGGING")
    audit_log_retention_days: int = Field(90, env="AUDIT_LOG_RETENTION_DAYS")
    
    # IP Filtering
    enable_ip_filtering: bool = Field(False, env="ENABLE_IP_FILTERING")
    allowed_ip_ranges: List[str] = Field(default_factory=list, env="ALLOWED_IP_RANGES")
    blocked_ip_ranges: List[str] = Field(default_factory=list, env="BLOCKED_IP_RANGES")
    
    @field_validator("secret_key")
    def validate_secret_key(cls, v):
        """Validate secret key strength."""
        if not v:
            raise ValueError("Secret key is required")
        
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        
        return v
    
    @field_validator("jwt_algorithm")
    def validate_jwt_algorithm(cls, v):
        """Validate JWT algorithm."""
        valid_algorithms = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]
        if v not in valid_algorithms:
            raise ValueError(f"JWT algorithm must be one of {valid_algorithms}")
        return v
    
    @field_validator("bcrypt_rounds")
    def validate_bcrypt_rounds(cls, v):
        """Validate bcrypt rounds."""
        if v < 10:
            raise ValueError("Bcrypt rounds must be at least 10 for security")
        if v > 15:
            raise ValueError("Bcrypt rounds should not exceed 15 for performance")
        return v
    
    @field_validator("session_cookie_samesite")
    def validate_samesite(cls, v):
        """Validate SameSite cookie attribute."""
        valid_values = ["strict", "lax", "none"]
        if v.lower() not in valid_values:
            raise ValueError(f"SameSite must be one of {valid_values}")
        return v.lower()
    
    @field_validator("referrer_policy")
    def validate_referrer_policy(cls, v):
        """Validate referrer policy."""
        valid_policies = [
            "no-referrer", "no-referrer-when-downgrade", "origin",
            "origin-when-cross-origin", "same-origin", "strict-origin",
            "strict-origin-when-cross-origin", "unsafe-url"
        ]
        if v not in valid_policies:
            raise ValueError(f"Referrer policy must be one of {valid_policies}")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
    
    def generate_secret_key(self) -> str:
        """Generate a secure secret key."""
        return secrets.token_urlsafe(32)
    
    def generate_api_key(self) -> str:
        """Generate a secure API key."""
        return secrets.token_urlsafe(self.api_key_length)
    
    def get_jwt_config(self) -> dict:
        """Get JWT configuration."""
        return {
            "secret_key": self.secret_key,
            "algorithm": self.jwt_algorithm,
            "access_token_expire_minutes": self.access_token_expire_minutes,
            "refresh_token_expire_days": self.refresh_token_expire_days,
            "issuer": self.jwt_issuer,
            "audience": self.jwt_audience
        }
    
    def get_password_policy(self) -> dict:
        """Get password policy configuration."""
        return {
            "min_length": self.password_min_length,
            "require_uppercase": self.password_require_uppercase,
            "require_lowercase": self.password_require_lowercase,
            "require_numbers": self.password_require_numbers,
            "require_symbols": self.password_require_symbols,
            "history_count": self.password_history_count
        }
    
    def get_session_config(self) -> dict:
        """Get session configuration."""
        return {
            "cookie_secure": self.session_cookie_secure,
            "cookie_httponly": self.session_cookie_httponly,
            "cookie_samesite": self.session_cookie_samesite,
            "timeout_minutes": self.session_timeout_minutes
        }
    
    def get_csp_header(self) -> str:
        """Get Content Security Policy header value."""
        if not self.enable_csp:
            return ""
        
        csp_directives = [
            f"default-src {self.csp_default_src}",
            f"script-src {self.csp_script_src}",
            f"style-src {self.csp_style_src}",
            f"img-src {self.csp_img_src}",
            f"connect-src {self.csp_connect_src}"
        ]
        
        return "; ".join(csp_directives)
    
    def get_security_headers(self) -> dict:
        """Get security headers configuration."""
        if not self.enable_security_headers:
            return {}
        
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block"
        }
        
        # HSTS header
        hsts_value = f"max-age={self.hsts_max_age}"
        if self.hsts_include_subdomains:
            hsts_value += "; includeSubDomains"
        headers["Strict-Transport-Security"] = hsts_value
        
        # Referrer Policy
        if self.enable_referrer_policy:
            headers["Referrer-Policy"] = self.referrer_policy
        
        # CSP header
        csp = self.get_csp_header()
        if csp:
            headers["Content-Security-Policy"] = csp
        
        return headers
    
    def get_rate_limit_config(self) -> dict:
        """Get rate limiting configuration."""
        return {
            "enabled": self.api_rate_limit_enabled,
            "per_ip": self.rate_limit_per_ip,
            "per_user": self.rate_limit_per_user,
            "window_seconds": self.rate_limit_window_seconds,
            "burst_limit": self.burst_rate_limit
        }
    
    def get_account_security_config(self) -> dict:
        """Get account security configuration."""
        return {
            "max_login_attempts": self.max_login_attempts,
            "lockout_duration_minutes": self.lockout_duration_minutes,
            "require_email_verification": self.require_email_verification,
            "enable_2fa": self.enable_2fa
        }
    
    def get_data_protection_config(self) -> dict:
        """Get data protection configuration."""
        return {
            "encryption_enabled": self.enable_data_encryption,
            "encryption_key": self.encryption_key,
            "audit_logging_enabled": self.enable_audit_logging,
            "audit_retention_days": self.audit_log_retention_days
        }
    
    def validate_password(self, password: str) -> tuple[bool, List[str]]:
        """Validate password against policy."""
        errors = []
        
        if len(password) < self.password_min_length:
            errors.append(f"Password must be at least {self.password_min_length} characters long")
        
        if self.password_require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.password_require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.password_require_numbers and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if self.password_require_symbols and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one symbol")
        
        return len(errors) == 0, errors