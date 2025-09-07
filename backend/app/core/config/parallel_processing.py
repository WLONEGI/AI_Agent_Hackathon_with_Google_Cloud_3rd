"""
Parallel Processing Configuration - 並列処理設定管理
品質ゲート、HITLフィードバック、並列実行の設定を統一管理
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from enum import Enum


class ParallelProcessingMode(str, Enum):
    """並列処理モード"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"
    AUTO = "auto"  # 負荷に応じて自動選択


class ParallelProcessingConfig(BaseModel):
    """並列処理設定"""
    
    # 基本並列処理設定
    max_concurrent_workers: int = Field(
        default=5,
        env="MAX_CONCURRENT_WORKERS",
        description="最大並列ワーカー数"
    )
    
    default_processing_mode: ParallelProcessingMode = Field(
        default=ParallelProcessingMode.PARALLEL,
        env="DEFAULT_PROCESSING_MODE",
        description="デフォルト処理モード"
    )
    
    # 品質ゲート並列処理設定
    quality_gate_parallel_enabled: bool = Field(
        default=True,
        env="QUALITY_GATE_PARALLEL_ENABLED",
        description="品質ゲート並列処理有効化"
    )
    
    quality_assessment_parallel_workers: int = Field(
        default=3,
        env="QUALITY_ASSESSMENT_PARALLEL_WORKERS",
        description="品質評価並列ワーカー数"
    )
    
    quality_gate_batch_size: int = Field(
        default=10,
        env="QUALITY_GATE_BATCH_SIZE",
        description="品質ゲートバッチサイズ"
    )
    
    # HITLフィードバック並列処理設定
    hitl_feedback_parallel_enabled: bool = Field(
        default=True,
        env="HITL_FEEDBACK_PARALLEL_ENABLED",
        description="HITLフィードバック並列処理有効化"
    )
    
    hitl_feedback_parallel_workers: int = Field(
        default=5,
        env="HITL_FEEDBACK_PARALLEL_WORKERS",
        description="HITLフィードバック並列ワーカー数"
    )
    
    hitl_feedback_timeout: int = Field(
        default=300,
        env="HITL_FEEDBACK_TIMEOUT",
        description="HITLフィードバックタイムアウト（秒）"
    )
    
    hitl_batch_size: int = Field(
        default=20,
        env="HITL_BATCH_SIZE",
        description="HITLフィードバックバッチサイズ"
    )
    
    # フェーズ別設定
    phase_processing_modes: Dict[int, str] = Field(
        default={
            1: "parallel",  # コンセプト - 並列OK
            2: "hybrid",    # キャラクター - HITL必要のためハイブリッド
            3: "parallel",  # プロット - 並列OK
            4: "hybrid",    # ネーム - HITL必要のためハイブリッド  
            5: "hybrid",    # 画像生成 - 重要フェーズ、HITL必要
            6: "parallel",  # セリフ配置 - 並列OK
            7: "sequential" # 最終統合 - 慎重に順次処理
        },
        description="フェーズ別処理モード設定"
    )
    
    # HITLチェックポイント設定
    hitl_checkpoint_phases: set = Field(
        default={2, 4, 5},
        description="HITLチェックポイントフェーズ"
    )
    
    # パフォーマンス最適化設定
    adaptive_concurrency_enabled: bool = Field(
        default=True,
        env="ADAPTIVE_CONCURRENCY_ENABLED",
        description="適応的並行度調整有効化"
    )
    
    performance_monitoring_enabled: bool = Field(
        default=True,
        env="PERFORMANCE_MONITORING_ENABLED",
        description="パフォーマンス監視有効化"
    )
    
    auto_scaling_enabled: bool = Field(
        default=False,
        env="AUTO_SCALING_ENABLED", 
        description="自動スケーリング有効化"
    )
    
    # リソース制限設定
    memory_limit_mb: int = Field(
        default=2048,
        env="PARALLEL_PROCESSING_MEMORY_LIMIT_MB",
        description="並列処理メモリ制限（MB）"
    )
    
    cpu_usage_threshold: float = Field(
        default=0.8,
        env="CPU_USAGE_THRESHOLD",
        description="CPU使用率しきい値"
    )
    
    # エラーハンドリング設定
    retry_attempts: int = Field(
        default=3,
        env="PARALLEL_PROCESSING_RETRY_ATTEMPTS",
        description="並列処理リトライ回数"
    )
    
    circuit_breaker_enabled: bool = Field(
        default=True,
        env="CIRCUIT_BREAKER_ENABLED",
        description="サーキットブレーカー有効化"
    )
    
    failure_threshold: float = Field(
        default=0.5,
        env="FAILURE_THRESHOLD",
        description="失敗率しきい値（サーキットブレーカー）"
    )
    
    class Config:
        env_prefix = "PARALLEL_PROCESSING_"
        case_sensitive = False


class ParallelProcessingMonitoring(BaseModel):
    """並列処理監視設定"""
    
    metrics_collection_enabled: bool = Field(
        default=True,
        description="メトリクス収集有効化"
    )
    
    performance_logging_level: str = Field(
        default="INFO",
        env="PERFORMANCE_LOGGING_LEVEL",
        description="パフォーマンスログレベル"
    )
    
    metrics_export_interval: int = Field(
        default=60,
        env="METRICS_EXPORT_INTERVAL",
        description="メトリクス出力間隔（秒）"
    )
    
    alert_thresholds: Dict[str, float] = Field(
        default={
            "processing_time": 300.0,      # 処理時間アラート（秒）
            "failure_rate": 0.1,           # 失敗率アラート
            "queue_length": 100,           # キュー長アラート
            "memory_usage": 0.8            # メモリ使用率アラート
        },
        description="アラートしきい値設定"
    )


class ParallelProcessingOptimization(BaseModel):
    """並列処理最適化設定"""
    
    load_balancing_strategy: str = Field(
        default="round_robin",
        env="LOAD_BALANCING_STRATEGY",
        description="負荷分散戦略（round_robin, least_connections, weighted）"
    )
    
    batching_optimization_enabled: bool = Field(
        default=True,
        env="BATCHING_OPTIMIZATION_ENABLED",
        description="バッチ処理最適化有効化"
    )
    
    dynamic_batch_sizing: bool = Field(
        default=True,
        env="DYNAMIC_BATCH_SIZING",
        description="動的バッチサイズ調整"
    )
    
    prefetch_enabled: bool = Field(
        default=True,
        env="PREFETCH_ENABLED",
        description="プリフェッチ有効化"
    )
    
    prefetch_size: int = Field(
        default=5,
        env="PREFETCH_SIZE",
        description="プリフェッチサイズ"
    )
    
    cache_optimization_enabled: bool = Field(
        default=True,
        env="CACHE_OPTIMIZATION_ENABLED",
        description="キャッシュ最適化有効化"
    )


# グローバル設定インスタンス
parallel_processing_config = ParallelProcessingConfig()
parallel_monitoring_config = ParallelProcessingMonitoring()
parallel_optimization_config = ParallelProcessingOptimization()


def get_phase_processing_mode(phase_num: int) -> ParallelProcessingMode:
    """フェーズ別処理モード取得"""
    mode_str = parallel_processing_config.phase_processing_modes.get(
        phase_num, 
        parallel_processing_config.default_processing_mode.value
    )
    return ParallelProcessingMode(mode_str)


def is_hitl_checkpoint_phase(phase_num: int) -> bool:
    """HITLチェックポイントフェーズ判定"""
    return phase_num in parallel_processing_config.hitl_checkpoint_phases


def get_optimal_worker_count(task_type: str) -> int:
    """タスク種別別最適ワーカー数取得"""
    worker_counts = {
        "quality_assessment": parallel_processing_config.quality_assessment_parallel_workers,
        "hitl_feedback": parallel_processing_config.hitl_feedback_parallel_workers,
        "general": parallel_processing_config.max_concurrent_workers
    }
    return worker_counts.get(task_type, parallel_processing_config.max_concurrent_workers)


def should_use_parallel_processing(
    phase_num: int,
    current_load: Optional[float] = None
) -> bool:
    """並列処理使用判定"""
    # フェーズ別設定チェック
    phase_mode = get_phase_processing_mode(phase_num)
    if phase_mode == ParallelProcessingMode.SEQUENTIAL:
        return False
    
    # 負荷ベースの判定（AUTO モードの場合）
    if phase_mode == ParallelProcessingMode.AUTO and current_load is not None:
        return current_load < parallel_processing_config.cpu_usage_threshold
    
    return True