"""API Response Models"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
from uuid import UUID
from datetime import datetime
from enum import Enum


class ProcessingStatus(str, Enum):
    """処理ステータス"""
    QUEUED = "queued"
    PROCESSING = "processing"
    WAITING_FEEDBACK = "waiting_feedback"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MangaGenerationResponse(BaseModel):
    """漫画生成レスポンス"""
    
    session_id: UUID = Field(..., description="Session identifier")
    status: ProcessingStatus = Field(..., description="Current processing status")
    message: str = Field(..., description="Status message")
    queue_position: int = Field(..., description="Position in processing queue")
    estimated_wait_time: int = Field(..., description="Estimated wait time in seconds")
    websocket_url: str = Field(..., description="WebSocket URL for real-time updates")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Response creation time")


class SessionStatusResponse(BaseModel):
    """セッション状態レスポンス"""
    
    session_id: UUID = Field(..., description="Session identifier")
    status: str = Field(..., description="Current session status")
    current_phase: int = Field(..., description="Current processing phase")
    phase_statuses: Dict[int, str] = Field(..., description="Status of each phase")
    quality_scores: Dict[int, float] = Field(..., description="Quality scores by phase")
    processing_time: float = Field(..., description="Total processing time in seconds")
    retry_counts: Dict[int, int] = Field(..., description="Retry counts by phase")
    hitl_feedback_count: int = Field(..., description="Number of HITL feedback interactions")
    websocket_connections: int = Field(..., description="Active WebSocket connections")
    pending_hitl_requests: int = Field(..., description="Pending HITL requests")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last status update")


class SystemStatusResponse(BaseModel):
    """システム状態レスポンス"""
    
    coordinator_status: Dict[str, Any] = Field(..., description="Pipeline coordinator status")
    performance_report: Dict[str, Any] = Field(..., description="Performance metrics report")
    component_stats: Dict[str, Dict[str, Any]] = Field(..., description="Component-specific statistics")
    system_health: str = Field(default="healthy", description="Overall system health")
    timestamp: datetime = Field(..., description="Status timestamp")


class QualityReportResponse(BaseModel):
    """品質レポートレスポンス"""
    
    session_id: Optional[UUID] = Field(None, description="Session ID for specific report")
    overall_quality_score: float = Field(..., description="Overall quality score", ge=0.0, le=1.0)
    phase_quality_scores: Dict[int, float] = Field(..., description="Quality scores by phase")
    quality_metrics: Dict[str, Any] = Field(..., description="Detailed quality metrics")
    quality_issues: List[str] = Field(default_factory=list, description="Identified quality issues")
    recommendations: List[str] = Field(default_factory=list, description="Quality improvement recommendations")
    compliance_rate: float = Field(..., description="Quality threshold compliance rate", ge=0.0, le=1.0)
    generated_at: datetime = Field(..., description="Report generation time")


class PreviewResponse(BaseModel):
    """プレビューレスポンス"""
    
    preview_data: Dict[str, Any] = Field(..., description="Generated preview data")
    quality_achieved: int = Field(..., description="Achieved quality level (1-5)")
    generation_time: float = Field(..., description="Generation time in seconds")
    cache_hit: bool = Field(..., description="Whether result was cached")
    cdn_urls: Dict[str, str] = Field(default_factory=dict, description="CDN URLs for assets")
    expires_at: datetime = Field(..., description="Preview expiration time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class VersionTreeResponse(BaseModel):
    """バージョンツリーレスポンス"""
    
    session_id: UUID = Field(..., description="Session identifier")
    branches: Dict[str, Any] = Field(..., description="Branch information and versions")
    total_versions: int = Field(..., description="Total number of versions")
    active_branch: str = Field(..., description="Currently active branch")
    generated_at: datetime = Field(..., description="Tree generation time")


class VersionComparisonResponse(BaseModel):
    """バージョン比較レスポンス"""
    
    version_a: str = Field(..., description="First version identifier")
    version_b: str = Field(..., description="Second version identifier")
    added_fields: Dict[str, Any] = Field(..., description="Fields added in version B")
    removed_fields: Dict[str, Any] = Field(..., description="Fields removed from version A")
    modified_fields: Dict[str, tuple] = Field(..., description="Fields modified between versions")
    unchanged_fields: Dict[str, Any] = Field(..., description="Fields that remained unchanged")
    similarity_score: float = Field(..., description="Similarity score (0.0-1.0)")
    comparison_metadata: Dict[str, Any] = Field(..., description="Comparison metadata")


class HITLFeedbackResponse(BaseModel):
    """HITLフィードバックレスポンス"""
    
    request_id: str = Field(..., description="Feedback request identifier")
    session_id: UUID = Field(..., description="Session identifier")
    phase_number: int = Field(..., description="Phase number")
    feedback_status: str = Field(..., description="Feedback processing status")
    applied_modifications: Optional[Dict[str, Any]] = Field(None, description="Applied modifications")
    processing_time: float = Field(..., description="Feedback processing time")
    timestamp: datetime = Field(..., description="Response timestamp")


class MetricsResponse(BaseModel):
    """メトリクスレスポンス"""
    
    time_range: str = Field(..., description="Requested time range")
    metrics_data: Dict[str, List[Dict[str, Any]]] = Field(..., description="Time series metrics data")
    summary_statistics: Dict[str, Any] = Field(..., description="Summary statistics")
    performance_indicators: Dict[str, Any] = Field(..., description="Key performance indicators")
    alert_conditions: List[Dict[str, Any]] = Field(default_factory=list, description="Active alerts")
    collected_at: datetime = Field(..., description="Metrics collection time")


class ErrorResponse(BaseModel):
    """エラーレスポンス"""
    
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Human-readable error message")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    suggestions: List[str] = Field(default_factory=list, description="Suggested solutions")


class SuccessResponse(BaseModel):
    """成功レスポンス"""
    
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class PaginatedResponse(BaseModel):
    """ページネーションレスポンス"""
    
    items: List[Dict[str, Any]] = Field(..., description="Response items")
    total_count: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Has next page")
    has_previous: bool = Field(..., description="Has previous page")


class WebSocketMessage(BaseModel):
    """WebSocketメッセージ"""
    
    type: str = Field(..., description="Message type")
    data: Optional[Dict[str, Any]] = Field(None, description="Message data")
    session_id: Optional[UUID] = Field(None, description="Associated session ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    sequence: Optional[int] = Field(None, description="Message sequence number")


class StreamingResponse(BaseModel):
    """ストリーミングレスポンス"""
    
    chunk_id: int = Field(..., description="Chunk sequence number")
    chunk_type: str = Field(..., description="Chunk type")
    chunk_data: Any = Field(..., description="Chunk data")
    is_final: bool = Field(..., description="Is final chunk")
    total_chunks: Optional[int] = Field(None, description="Total expected chunks")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Chunk timestamp")


# 統計・分析レスポンス
class PerformanceMetrics(BaseModel):
    """パフォーマンスメトリクス"""
    
    throughput_per_minute: float = Field(..., description="Requests processed per minute")
    average_response_time: float = Field(..., description="Average response time in seconds")
    error_rate: float = Field(..., description="Error rate (0.0-1.0)")
    quality_score_average: float = Field(..., description="Average quality score")
    resource_utilization: Dict[str, float] = Field(..., description="Resource utilization metrics")
    timestamp: datetime = Field(..., description="Metrics timestamp")


class SystemHealth(BaseModel):
    """システムヘルス"""
    
    overall_status: str = Field(..., description="Overall system status")
    component_health: Dict[str, str] = Field(..., description="Health status by component")
    active_alerts: List[Dict[str, Any]] = Field(default_factory=list, description="Active system alerts")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    last_restart: Optional[datetime] = Field(None, description="Last system restart time")
    health_check_time: datetime = Field(..., description="Health check timestamp")


class ComponentStatistics(BaseModel):
    """コンポーネント統計"""
    
    component_name: str = Field(..., description="Component name")
    requests_processed: int = Field(..., description="Total requests processed")
    success_rate: float = Field(..., description="Success rate (0.0-1.0)")
    average_processing_time: float = Field(..., description="Average processing time")
    error_counts: Dict[str, int] = Field(default_factory=dict, description="Error counts by type")
    resource_usage: Dict[str, Any] = Field(default_factory=dict, description="Resource usage metrics")
    last_updated: datetime = Field(..., description="Statistics last updated")


class BulkOperationResponse(BaseModel):
    """一括操作レスポンス"""
    
    operation_id: str = Field(..., description="Bulk operation identifier")
    total_items: int = Field(..., description="Total items to process")
    processed_items: int = Field(..., description="Successfully processed items")
    failed_items: int = Field(..., description="Failed items")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Processing errors")
    status: str = Field(..., description="Operation status")
    started_at: datetime = Field(..., description="Operation start time")
    completed_at: Optional[datetime] = Field(None, description="Operation completion time")


# WebSocket専用レスポンス
class WSConnectionResponse(WebSocketMessage):
    """WebSocket接続レスポンス"""
    
    connection_id: str = Field(..., description="Connection identifier")
    capabilities: Dict[str, Any] = Field(..., description="Server capabilities")
    heartbeat_interval: int = Field(..., description="Heartbeat interval in seconds")


class WSErrorResponse(WebSocketMessage):
    """WebSocketエラーレスポンス"""
    
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    recoverable: bool = Field(..., description="Whether error is recoverable")


class WSProgressUpdate(WebSocketMessage):
    """WebSocket進捗更新"""
    
    progress_percentage: float = Field(..., description="Progress percentage (0.0-100.0)")
    current_phase: int = Field(..., description="Current phase number")
    phase_name: str = Field(..., description="Current phase name")
    estimated_remaining_time: Optional[int] = Field(None, description="Estimated remaining time in seconds")


class WSQualityUpdate(WebSocketMessage):
    """WebSocket品質更新"""
    
    phase_number: int = Field(..., description="Phase number")
    quality_score: float = Field(..., description="Quality score")
    quality_status: str = Field(..., description="Quality status")
    issues: List[str] = Field(default_factory=list, description="Quality issues")
    improvements: List[str] = Field(default_factory=list, description="Suggested improvements")