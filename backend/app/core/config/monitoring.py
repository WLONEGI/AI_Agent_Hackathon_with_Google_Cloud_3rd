"""Monitoring and observability configuration settings."""

from typing import Dict, List, Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field, field_validator


class MonitoringSettings(BaseSettings):
    """Monitoring and observability configuration."""
    
    # Logging Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")
    log_file_path: Optional[str] = Field(None, env="LOG_FILE_PATH")
    log_rotation_size: str = Field("10MB", env="LOG_ROTATION_SIZE")
    log_rotation_count: int = Field(5, env="LOG_ROTATION_COUNT")
    log_compression: bool = Field(True, env="LOG_COMPRESSION")
    
    # Structured Logging
    enable_structured_logging: bool = Field(True, env="ENABLE_STRUCTURED_LOGGING")
    log_correlation_id: bool = Field(True, env="LOG_CORRELATION_ID")
    log_request_details: bool = Field(True, env="LOG_REQUEST_DETAILS")
    log_response_details: bool = Field(False, env="LOG_RESPONSE_DETAILS")  # May contain sensitive data
    
    # Metrics Configuration
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    metrics_port: int = Field(9090, env="METRICS_PORT")
    metrics_path: str = Field("/metrics", env="METRICS_PATH")
    metrics_namespace: str = Field("manga_service", env="METRICS_NAMESPACE")
    
    # Prometheus Configuration
    enable_prometheus: bool = Field(True, env="ENABLE_PROMETHEUS")
    prometheus_multiproc_dir: Optional[str] = Field(None, env="PROMETHEUS_MULTIPROC_DIR")
    prometheus_histogram_buckets: List[float] = Field(
        default=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0],
        env="PROMETHEUS_HISTOGRAM_BUCKETS"
    )
    
    # Health Check Configuration
    health_check_enabled: bool = Field(True, env="HEALTH_CHECK_ENABLED")
    health_check_path: str = Field("/health", env="HEALTH_CHECK_PATH")
    health_check_interval: int = Field(30, env="HEALTH_CHECK_INTERVAL")
    health_check_timeout: int = Field(5, env="HEALTH_CHECK_TIMEOUT")
    
    # Tracing Configuration
    enable_tracing: bool = Field(False, env="ENABLE_TRACING")  # Can be resource intensive
    tracing_service_name: str = Field("manga-generation-service", env="TRACING_SERVICE_NAME")
    tracing_endpoint: Optional[str] = Field(None, env="TRACING_ENDPOINT")
    tracing_sample_rate: float = Field(0.1, env="TRACING_SAMPLE_RATE")  # 10% sampling
    
    # Error Tracking
    enable_error_tracking: bool = Field(True, env="ENABLE_ERROR_TRACKING")
    error_tracking_dsn: Optional[str] = Field(None, env="ERROR_TRACKING_DSN")  # Sentry DSN
    error_tracking_environment: str = Field("development", env="ERROR_TRACKING_ENVIRONMENT")
    error_capture_percentage: float = Field(1.0, env="ERROR_CAPTURE_PERCENTAGE")
    
    # Performance Monitoring
    enable_performance_monitoring: bool = Field(True, env="ENABLE_PERFORMANCE_MONITORING")
    slow_request_threshold: float = Field(2.0, env="SLOW_REQUEST_THRESHOLD")  # seconds
    memory_usage_alert_threshold: int = Field(80, env="MEMORY_USAGE_ALERT_THRESHOLD")  # percentage
    cpu_usage_alert_threshold: int = Field(80, env="CPU_USAGE_ALERT_THRESHOLD")  # percentage
    
    # Custom Metrics
    track_phase_metrics: bool = Field(True, env="TRACK_PHASE_METRICS")
    track_ai_model_metrics: bool = Field(True, env="TRACK_AI_MODEL_METRICS")
    track_cache_metrics: bool = Field(True, env="TRACK_CACHE_METRICS")
    track_user_metrics: bool = Field(True, env="TRACK_USER_METRICS")
    
    # Alerting Configuration
    enable_alerting: bool = Field(True, env="ENABLE_ALERTING")
    alert_webhook_url: Optional[str] = Field(None, env="ALERT_WEBHOOK_URL")
    alert_email_recipients: List[str] = Field(default_factory=list, env="ALERT_EMAIL_RECIPIENTS")
    alert_cooldown_minutes: int = Field(15, env="ALERT_COOLDOWN_MINUTES")
    
    # Database Monitoring
    monitor_database_performance: bool = Field(True, env="MONITOR_DATABASE_PERFORMANCE")
    slow_query_threshold: float = Field(1.0, env="SLOW_QUERY_THRESHOLD")  # seconds
    monitor_connection_pool: bool = Field(True, env="MONITOR_CONNECTION_POOL")
    
    # Application-specific Monitoring
    monitor_generation_success_rate: bool = Field(True, env="MONITOR_GENERATION_SUCCESS_RATE")
    monitor_hitl_response_times: bool = Field(True, env="MONITOR_HITL_RESPONSE_TIMES")
    monitor_ai_api_latency: bool = Field(True, env="MONITOR_AI_API_LATENCY")
    monitor_cache_hit_rate: bool = Field(True, env="MONITOR_CACHE_HIT_RATE")
    
    # Security Monitoring
    enable_security_monitoring: bool = Field(True, env="ENABLE_SECURITY_MONITORING")
    monitor_failed_logins: bool = Field(True, env="MONITOR_FAILED_LOGINS")
    monitor_rate_limit_violations: bool = Field(True, env="MONITOR_RATE_LIMIT_VIOLATIONS")
    monitor_suspicious_requests: bool = Field(True, env="MONITOR_SUSPICIOUS_REQUESTS")
    
    # Data Export
    enable_metrics_export: bool = Field(False, env="ENABLE_METRICS_EXPORT")
    metrics_export_endpoint: Optional[str] = Field(None, env="METRICS_EXPORT_ENDPOINT")
    metrics_export_interval: int = Field(60, env="METRICS_EXPORT_INTERVAL")  # seconds
    
    @field_validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @field_validator("log_format")
    def validate_log_format(cls, v):
        """Validate log format."""
        valid_formats = ["json", "text", "colored"]
        if v not in valid_formats:
            raise ValueError(f"Log format must be one of {valid_formats}")
        return v
    
    @field_validator("tracing_sample_rate")
    def validate_sample_rate(cls, v):
        """Validate tracing sample rate."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Tracing sample rate must be between 0.0 and 1.0")
        return v
    
    @field_validator("error_capture_percentage")
    def validate_error_capture_percentage(cls, v):
        """Validate error capture percentage."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Error capture percentage must be between 0.0 and 1.0")
        return v
    
    @field_validator("memory_usage_alert_threshold")
    def validate_memory_threshold(cls, v):
        """Validate memory usage alert threshold."""
        if not 1 <= v <= 100:
            raise ValueError("Memory usage alert threshold must be between 1 and 100")
        return v
    
    @field_validator("cpu_usage_alert_threshold")
    def validate_cpu_threshold(cls, v):
        """Validate CPU usage alert threshold."""
        if not 1 <= v <= 100:
            raise ValueError("CPU usage alert threshold must be between 1 and 100")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
    
    def get_logging_config(self) -> dict:
        """Get logging configuration."""
        config = {
            "level": self.log_level,
            "format": self.log_format,
            "structured": self.enable_structured_logging,
            "correlation_id": self.log_correlation_id,
            "request_details": self.log_request_details,
            "response_details": self.log_response_details
        }
        
        if self.log_file_path:
            config.update({
                "file_path": self.log_file_path,
                "rotation_size": self.log_rotation_size,
                "rotation_count": self.log_rotation_count,
                "compression": self.log_compression
            })
        
        return config
    
    def get_prometheus_config(self) -> dict:
        """Get Prometheus configuration."""
        return {
            "enabled": self.enable_prometheus,
            "port": self.metrics_port,
            "path": self.metrics_path,
            "namespace": self.metrics_namespace,
            "multiproc_dir": self.prometheus_multiproc_dir,
            "histogram_buckets": self.prometheus_histogram_buckets
        }
    
    def get_health_check_config(self) -> dict:
        """Get health check configuration."""
        return {
            "enabled": self.health_check_enabled,
            "path": self.health_check_path,
            "interval": self.health_check_interval,
            "timeout": self.health_check_timeout
        }
    
    def get_tracing_config(self) -> dict:
        """Get tracing configuration."""
        return {
            "enabled": self.enable_tracing,
            "service_name": self.tracing_service_name,
            "endpoint": self.tracing_endpoint,
            "sample_rate": self.tracing_sample_rate
        }
    
    def get_error_tracking_config(self) -> dict:
        """Get error tracking configuration."""
        return {
            "enabled": self.enable_error_tracking,
            "dsn": self.error_tracking_dsn,
            "environment": self.error_tracking_environment,
            "capture_percentage": self.error_capture_percentage
        }
    
    def get_performance_config(self) -> dict:
        """Get performance monitoring configuration."""
        return {
            "enabled": self.enable_performance_monitoring,
            "slow_request_threshold": self.slow_request_threshold,
            "memory_alert_threshold": self.memory_usage_alert_threshold,
            "cpu_alert_threshold": self.cpu_usage_alert_threshold
        }
    
    def get_custom_metrics_config(self) -> dict:
        """Get custom metrics configuration."""
        return {
            "phase_metrics": self.track_phase_metrics,
            "ai_model_metrics": self.track_ai_model_metrics,
            "cache_metrics": self.track_cache_metrics,
            "user_metrics": self.track_user_metrics
        }
    
    def get_alerting_config(self) -> dict:
        """Get alerting configuration."""
        return {
            "enabled": self.enable_alerting,
            "webhook_url": self.alert_webhook_url,
            "email_recipients": self.alert_email_recipients,
            "cooldown_minutes": self.alert_cooldown_minutes
        }
    
    def get_database_monitoring_config(self) -> dict:
        """Get database monitoring configuration."""
        return {
            "performance_monitoring": self.monitor_database_performance,
            "slow_query_threshold": self.slow_query_threshold,
            "connection_pool_monitoring": self.monitor_connection_pool
        }
    
    def get_application_monitoring_config(self) -> dict:
        """Get application-specific monitoring configuration."""
        return {
            "generation_success_rate": self.monitor_generation_success_rate,
            "hitl_response_times": self.monitor_hitl_response_times,
            "ai_api_latency": self.monitor_ai_api_latency,
            "cache_hit_rate": self.monitor_cache_hit_rate
        }
    
    def get_security_monitoring_config(self) -> dict:
        """Get security monitoring configuration."""
        return {
            "enabled": self.enable_security_monitoring,
            "failed_logins": self.monitor_failed_logins,
            "rate_limit_violations": self.monitor_rate_limit_violations,
            "suspicious_requests": self.monitor_suspicious_requests
        }
    
    def get_export_config(self) -> dict:
        """Get metrics export configuration."""
        return {
            "enabled": self.enable_metrics_export,
            "endpoint": self.metrics_export_endpoint,
            "interval": self.metrics_export_interval
        }
    
    def should_alert(self, metric_name: str, value: float, threshold: float) -> bool:
        """Check if metric value should trigger an alert."""
        if not self.enable_alerting:
            return False
        
        # Define alert conditions based on metric type
        alert_conditions = {
            "memory_usage": lambda v, t: v > t,
            "cpu_usage": lambda v, t: v > t,
            "error_rate": lambda v, t: v > t,
            "response_time": lambda v, t: v > t,
            "success_rate": lambda v, t: v < t  # Lower is worse for success rate
        }
        
        condition = alert_conditions.get(metric_name, lambda v, t: v > t)
        return condition(value, threshold)