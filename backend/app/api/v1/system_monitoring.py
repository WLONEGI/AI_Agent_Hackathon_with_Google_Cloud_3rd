"""
System Monitoring API - システム監視API
パフォーマンス監視、設定管理、システムヘルスチェックのAPIエンドポイント
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from app.core.logging import LoggerMixin
from app.services.parallel_system_manager import ParallelSystemManager
from app.services.parallel_configuration_service import ConfigurationScope


# グローバルシステムマネージャー（実際の実装では適切な依存注入を使用）
system_manager = ParallelSystemManager()

router = APIRouter(prefix="/system", tags=["System Monitoring"])


class SystemMonitoringAPI(LoggerMixin):
    """システム監視API"""
    
    def __init__(self):
        super().__init__()


api = SystemMonitoringAPI()


@router.on_event("startup")
async def startup_system_manager():
    """システムマネージャー開始"""
    try:
        await system_manager.start_system()
        api.logger.info("System manager started via API startup")
    except Exception as e:
        api.logger.error(f"Failed to start system manager: {e}")


@router.on_event("shutdown") 
async def shutdown_system_manager():
    """システムマネージャー停止"""
    try:
        await system_manager.stop_system()
        api.logger.info("System manager stopped via API shutdown")
    except Exception as e:
        api.logger.error(f"Failed to stop system manager: {e}")


@router.get("/dashboard")
async def get_system_dashboard() -> Dict[str, Any]:
    """
    システムダッシュボード取得
    
    Returns:
        システム全体の監視情報とステータス
    """
    try:
        dashboard = await system_manager.get_system_dashboard()
        return {
            "status": "success",
            "data": dashboard
        }
    except Exception as e:
        api.logger.error(f"Dashboard retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")


@router.get("/health")
async def get_system_health() -> Dict[str, Any]:
    """
    システムヘルスチェック
    
    Returns:
        システムの健康状態と詳細情報
    """
    try:
        health_report = await system_manager.perform_health_check()
        
        # HTTPステータスコード判定
        health_status = health_report.get("health_status", "unknown")
        if health_status in ["critical", "warning"]:
            status_code = 503  # Service Unavailable
        else:
            status_code = 200
        
        return {
            "status": "success",
            "health_status": health_status,
            "data": health_report
        }
    except Exception as e:
        api.logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=f"Health check error: {str(e)}")


@router.get("/performance/summary")
async def get_performance_summary(
    hours: int = Query(default=1, ge=1, le=24, description="Performance data period in hours")
) -> Dict[str, Any]:
    """
    パフォーマンスサマリー取得
    
    Args:
        hours: 取得期間（時間）
        
    Returns:
        パフォーマンス統計情報
    """
    try:
        performance_summary = system_manager.monitoring_service.get_performance_summary(hours)
        
        return {
            "status": "success",
            "data": performance_summary
        }
    except Exception as e:
        api.logger.error(f"Performance summary error: {e}")
        raise HTTPException(status_code=500, detail=f"Performance summary error: {str(e)}")


@router.get("/performance/report")
async def generate_performance_report(
    hours: int = Query(default=24, ge=1, le=168, description="Report period in hours")
) -> Dict[str, Any]:
    """
    パフォーマンスレポート生成
    
    Args:
        hours: レポート期間（時間、最大1週間）
        
    Returns:
        詳細なパフォーマンスレポート
    """
    try:
        performance_report = await system_manager.monitoring_service.generate_performance_report(hours)
        
        return {
            "status": "success",
            "data": performance_report
        }
    except Exception as e:
        api.logger.error(f"Performance report error: {e}")
        raise HTTPException(status_code=500, detail=f"Performance report error: {str(e)}")


@router.get("/configuration/status")
async def get_configuration_status() -> Dict[str, Any]:
    """
    設定状況取得
    
    Returns:
        現在の設定状況と統計
    """
    try:
        config_status = system_manager.configuration_service.get_configuration_status()
        
        return {
            "status": "success",
            "data": config_status
        }
    except Exception as e:
        api.logger.error(f"Configuration status error: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration status error: {str(e)}")


@router.get("/configuration/effective")
async def get_effective_configuration(
    session_id: Optional[str] = Query(None, description="Session ID for scoped configuration"),
    user_id: Optional[str] = Query(None, description="User ID for user-specific configuration"),
    phase_num: Optional[int] = Query(None, ge=1, le=7, description="Phase number for phase-specific configuration")
) -> Dict[str, Any]:
    """
    有効設定取得
    
    Args:
        session_id: セッションID（スコープ別設定用）
        user_id: ユーザーID（ユーザー別設定用）
        phase_num: フェーズ番号（フェーズ別設定用）
        
    Returns:
        適用される有効な設定
    """
    try:
        effective_config = await system_manager.configuration_service.get_effective_configuration(
            session_id=session_id,
            user_id=user_id,
            phase_num=phase_num
        )
        
        return {
            "status": "success",
            "data": effective_config
        }
    except Exception as e:
        api.logger.error(f"Effective configuration error: {e}")
        raise HTTPException(status_code=500, detail=f"Effective configuration error: {str(e)}")


@router.post("/configuration/update")
async def update_configuration(
    config_path: str,
    new_value: Any,
    scope: ConfigurationScope = ConfigurationScope.GLOBAL,
    scope_id: Optional[str] = None,
    reason: str = "API update",
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    設定更新
    
    Args:
        config_path: 設定パス（例: "max_concurrent_workers"）
        new_value: 新しい値
        scope: 設定適用スコープ
        scope_id: スコープID（session、userスコープで使用）
        reason: 変更理由
        user_id: 変更者ユーザーID
        
    Returns:
        更新結果
    """
    try:
        success = await system_manager.configuration_service.update_configuration(
            config_path=config_path,
            new_value=new_value,
            scope=scope,
            scope_id=scope_id,
            reason=reason,
            user_id=user_id
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Configuration '{config_path}' updated successfully"
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to update configuration '{config_path}'"
            }
    except Exception as e:
        api.logger.error(f"Configuration update error: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration update error: {str(e)}")


@router.post("/configuration/backup")
async def create_configuration_backup(backup_name: str) -> Dict[str, Any]:
    """
    設定バックアップ作成
    
    Args:
        backup_name: バックアップ名
        
    Returns:
        バックアップ作成結果
    """
    try:
        success = await system_manager.configuration_service.create_configuration_backup(backup_name)
        
        if success:
            return {
                "status": "success",
                "message": f"Backup '{backup_name}' created successfully"
            }
        else:
            return {
                "status": "error", 
                "message": f"Failed to create backup '{backup_name}'"
            }
    except Exception as e:
        api.logger.error(f"Backup creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Backup creation error: {str(e)}")


@router.post("/configuration/restore")
async def restore_configuration_backup(backup_name: str) -> Dict[str, Any]:
    """
    設定バックアップ復元
    
    Args:
        backup_name: 復元するバックアップ名
        
    Returns:
        復元結果
    """
    try:
        success = await system_manager.configuration_service.restore_configuration_backup(backup_name)
        
        if success:
            return {
                "status": "success",
                "message": f"Configuration restored from backup '{backup_name}'"
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to restore from backup '{backup_name}'"
            }
    except Exception as e:
        api.logger.error(f"Backup restore error: {e}")
        raise HTTPException(status_code=500, detail=f"Backup restore error: {str(e)}")


@router.post("/optimization/toggle")
async def toggle_auto_optimization(enabled: bool) -> Dict[str, Any]:
    """
    自動最適化のオン/オフ切り替え
    
    Args:
        enabled: 有効化フラグ
        
    Returns:
        切り替え結果
    """
    try:
        if enabled:
            await system_manager.start_auto_optimization()
            message = "Auto-optimization enabled"
        else:
            await system_manager.stop_auto_optimization()
            message = "Auto-optimization disabled"
        
        return {
            "status": "success",
            "message": message,
            "auto_optimization_active": system_manager.is_auto_optimizing
        }
    except Exception as e:
        api.logger.error(f"Auto-optimization toggle error: {e}")
        raise HTTPException(status_code=500, detail=f"Auto-optimization toggle error: {str(e)}")


@router.get("/alerts")
async def get_system_alerts(
    hours: int = Query(default=24, ge=1, le=168, description="Alert period in hours")
) -> Dict[str, Any]:
    """
    システムアラート取得
    
    Args:
        hours: アラート取得期間（時間）
        
    Returns:
        システムアラート一覧
    """
    try:
        # 古いアラートをクリアしてから取得
        system_manager.clear_old_alerts(hours)
        
        return {
            "status": "success",
            "data": {
                "active_alerts": system_manager.system_alerts,
                "total_count": len(system_manager.system_alerts),
                "period_hours": hours
            }
        }
    except Exception as e:
        api.logger.error(f"Alerts retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Alerts retrieval error: {str(e)}")


@router.get("/statistics")
async def get_system_statistics() -> Dict[str, Any]:
    """
    システム統計取得
    
    Returns:
        システム稼働統計とメトリクス
    """
    try:
        statistics = system_manager.get_system_statistics()
        
        return {
            "status": "success",
            "data": statistics
        }
    except Exception as e:
        api.logger.error(f"Statistics retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Statistics retrieval error: {str(e)}")


@router.post("/system/backup")
async def create_system_backup(backup_name: str) -> Dict[str, Any]:
    """
    システム全体バックアップ作成
    
    Args:
        backup_name: バックアップ名
        
    Returns:
        システムバックアップ情報
    """
    try:
        backup_info = await system_manager.create_system_backup(backup_name)
        
        return {
            "status": "success",
            "data": backup_info
        }
    except Exception as e:
        api.logger.error(f"System backup error: {e}")
        raise HTTPException(status_code=500, detail=f"System backup error: {str(e)}")


@router.post("/monitoring/record-stats")
async def record_parallel_processing_stats(
    active_workers: int,
    queued_tasks: int,
    completed_tasks: int,
    failed_tasks: int,
    processing_times: List[float]
) -> Dict[str, Any]:
    """
    並列処理統計記録（外部システムから呼び出し用）
    
    Args:
        active_workers: アクティブワーカー数
        queued_tasks: キューイングタスク数
        completed_tasks: 完了タスク数
        failed_tasks: 失敗タスク数
        processing_times: 処理時間リスト
        
    Returns:
        記録結果
    """
    try:
        system_manager.monitoring_service.record_parallel_processing_stats(
            active_workers=active_workers,
            queued_tasks=queued_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            processing_times=processing_times
        )
        
        return {
            "status": "success",
            "message": "Processing stats recorded successfully"
        }
    except Exception as e:
        api.logger.error(f"Stats recording error: {e}")
        raise HTTPException(status_code=500, detail=f"Stats recording error: {str(e)}")


# ヘルスチェック用の軽量エンドポイント
@router.get("/ping")
async def ping() -> Dict[str, Any]:
    """
    システム生存確認
    
    Returns:
        システムの基本ステータス
    """
    return {
        "status": "success",
        "message": "System monitoring API is running",
        "timestamp": datetime.utcnow().isoformat(),
        "auto_optimization_active": system_manager.is_auto_optimizing,
        "monitoring_active": system_manager.monitoring_service.is_monitoring
    }