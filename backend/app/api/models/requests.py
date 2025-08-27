"""API Request Models"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional
from uuid import UUID


class MangaGenerationRequest(BaseModel):
    """漫画生成リクエスト"""
    
    user_input: str = Field(..., description="User's creative input/prompt", min_length=10, max_length=2000)
    priority: int = Field(5, description="Generation priority (1-10, higher = more priority)", ge=1, le=10)
    quality_level: str = Field("high", description="Target quality level")
    enable_hitl: bool = Field(True, description="Enable human-in-the-loop feedback")
    hitl_timeout: int = Field(30, description="HITL feedback timeout in seconds", ge=5, le=300)
    options: Optional[Dict[str, Any]] = Field(None, description="Additional generation options")
    
    @validator("quality_level")
    def validate_quality_level(cls, v):
        """品質レベル検証"""
        valid_levels = ["ultra_low", "low", "medium", "high", "ultra_high"]
        if v not in valid_levels:
            raise ValueError(f"Quality level must be one of {valid_levels}")
        return v
    
    @validator("options")
    def validate_options(cls, v):
        """オプション検証"""
        if v is None:
            return {}
        
        # 最大ネスト深度チェック
        def check_depth(obj, depth=0):
            if depth > 5:  # 最大5層まで
                raise ValueError("Options nesting too deep")
            if isinstance(obj, dict):
                for value in obj.values():
                    check_depth(value, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    check_depth(item, depth + 1)
        
        check_depth(v)
        return v


class HITLFeedbackRequest(BaseModel):
    """HITLフィードバックリクエスト"""
    
    session_id: UUID = Field(..., description="Session identifier")
    request_id: str = Field(..., description="Feedback request identifier")
    feedback_data: Dict[str, Any] = Field(..., description="Feedback data")
    
    @validator("feedback_data")
    def validate_feedback_data(cls, v):
        """フィードバックデータ検証"""
        required_fields = ["action"]
        
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Required field '{field}' missing in feedback_data")
        
        # アクション検証
        valid_actions = ["approve", "modify", "regenerate", "skip"]
        if v["action"] not in valid_actions:
            raise ValueError(f"Action must be one of {valid_actions}")
        
        return v


class PreviewRequest(BaseModel):
    """プレビュー生成リクエスト"""
    
    session_id: UUID = Field(..., description="Session identifier")
    phase_number: int = Field(..., description="Phase number (1-7)", ge=1, le=7)
    phase_data: Dict[str, Any] = Field(..., description="Phase result data")
    quality_level: str = Field("medium", description="Preview quality level")
    preview_type: str = Field("interactive", description="Preview type")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Device capability information")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    priority: Optional[int] = Field(5, description="Generation priority (1-10)", ge=1, le=10)
    
    @validator("quality_level")
    def validate_quality_level(cls, v):
        """品質レベル検証"""
        valid_levels = ["ultra_low", "low", "medium", "high", "ultra_high"]
        if v not in valid_levels:
            raise ValueError(f"Quality level must be one of {valid_levels}")
        return v
    
    @validator("preview_type")
    def validate_preview_type(cls, v):
        """プレビュータイプ検証"""
        valid_types = ["thumbnail", "interactive", "full_resolution", "adaptive"]
        if v not in valid_types:
            raise ValueError(f"Preview type must be one of {valid_types}")
        return v
    
    @validator("phase_data")
    def validate_phase_data(cls, v):
        """フェーズデータ検証"""
        if not isinstance(v, dict) or not v:
            raise ValueError("Phase data must be a non-empty dictionary")
        return v


class VersionComparisonRequest(BaseModel):
    """バージョン比較リクエスト"""
    
    version_a: str = Field(..., description="First version to compare")
    version_b: str = Field(..., description="Second version to compare")
    comparison_mode: str = Field("side_by_side", description="Comparison display mode")
    include_metadata: bool = Field(False, description="Include metadata in comparison")
    
    @validator("comparison_mode")
    def validate_comparison_mode(cls, v):
        """比較モード検証"""
        valid_modes = ["side_by_side", "overlay", "diff_highlight", "unified"]
        if v not in valid_modes:
            raise ValueError(f"Comparison mode must be one of {valid_modes}")
        return v


class BranchCreationRequest(BaseModel):
    """ブランチ作成リクエスト"""
    
    branch_name: str = Field(..., description="New branch name", min_length=1, max_length=100)
    base_version: str = Field(..., description="Base version for new branch")
    description: str = Field("", description="Branch description", max_length=500)
    
    @validator("branch_name")
    def validate_branch_name(cls, v):
        """ブランチ名検証"""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Branch name must contain only alphanumeric characters, underscores, and hyphens")
        return v


class SystemCleanupRequest(BaseModel):
    """システムクリーンアップリクエスト"""
    
    days_old: int = Field(30, description="Age threshold in days", ge=1, le=365)
    keep_milestones: bool = Field(True, description="Preserve milestone versions")
    session_filter: Optional[UUID] = Field(None, description="Clean specific session only")
    dry_run: bool = Field(False, description="Perform dry run without actual deletion")


class QualityOverrideRequest(BaseModel):
    """品質オーバーライドリクエスト"""
    
    assessment_id: str = Field(..., description="Assessment identifier to override")
    override_reason: str = Field(..., description="Reason for override", min_length=10, max_length=500)
    target_phase: int = Field(..., description="Phase number to override", ge=1, le=7)


class MetricsRequest(BaseModel):
    """メトリクス取得リクエスト"""
    
    time_range: str = Field("1h", description="Time range for metrics")
    granularity: str = Field("1m", description="Data granularity")
    metrics_types: Optional[List[str]] = Field(None, description="Specific metric types to include")
    
    @validator("time_range")
    def validate_time_range(cls, v):
        """時間範囲検証"""
        valid_ranges = ["5m", "15m", "1h", "6h", "24h", "7d"]
        if v not in valid_ranges:
            raise ValueError(f"Time range must be one of {valid_ranges}")
        return v
    
    @validator("granularity")
    def validate_granularity(cls, v):
        """粒度検証"""
        valid_granularities = ["10s", "30s", "1m", "5m", "15m", "1h"]
        if v not in valid_granularities:
            raise ValueError(f"Granularity must be one of {valid_granularities}")
        return v