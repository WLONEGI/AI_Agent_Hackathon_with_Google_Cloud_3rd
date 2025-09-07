"""
Parallel Configuration Service - 並列処理設定管理サービス
動的設定変更、A/Bテスト、パフォーマンス最適化、設定バックアップ/復元
"""

import asyncio
import json
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

from app.core.logging import LoggerMixin
from app.core.config.parallel_processing import ParallelProcessingConfig


class ConfigurationScope(str, Enum):
    """設定適用スコープ"""
    GLOBAL = "global"                # 全システム適用
    SESSION = "session"              # セッション単位
    USER = "user"                    # ユーザー単位
    PHASE = "phase"                  # フェーズ単位
    TEMPORARY = "temporary"          # 一時的適用


@dataclass
class ConfigurationChange:
    """設定変更記録"""
    timestamp: datetime
    scope: ConfigurationScope
    config_path: str
    old_value: Any
    new_value: Any
    reason: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    auto_applied: bool = False


@dataclass
class PerformanceOptimizationRule:
    """パフォーマンス最適化ルール"""
    name: str
    condition: str                    # 適用条件（例: "cpu_usage > 80"）
    action: str                       # 実行アクション（例: "reduce_workers"）
    parameters: Dict[str, Any]        # アクションパラメータ
    priority: int = 5                 # 優先度（1=最高, 10=最低）
    enabled: bool = True


class ParallelConfigurationService(LoggerMixin):
    """並列処理設定管理サービス"""
    
    def __init__(self, config_file_path: Optional[Path] = None):
        super().__init__()
        
        # 設定ファイルパス
        self.config_file_path = config_file_path or Path("parallel_config.json")
        
        # 現在の設定
        self.current_config = ParallelProcessingConfig()
        self.scoped_configs: Dict[str, Dict[str, Any]] = {}
        
        # 設定変更履歴
        self.configuration_history: List[ConfigurationChange] = []
        self.max_history_size = 1000
        
        # A/Bテスト設定
        self.ab_tests: Dict[str, Dict[str, Any]] = {}
        
        # 自動最適化ルール
        self.optimization_rules: List[PerformanceOptimizationRule] = []
        self.auto_optimization_enabled = True
        
        # 変更コールバック
        self.change_callbacks: List[Callable] = []
        
        # 設定バックアップ
        self.config_backups: Dict[str, Dict[str, Any]] = {}
        
        # 初期化
        asyncio.create_task(self._initialize_configuration())
    
    async def _initialize_configuration(self):
        """設定初期化"""
        try:
            # 設定ファイル読み込み
            await self._load_configuration_file()
            
            # デフォルト最適化ルール設定
            await self._setup_default_optimization_rules()
            
            self.logger.info("Parallel configuration service initialized")
            
        except Exception as e:
            self.logger.error(f"Configuration initialization error: {e}")
    
    async def _load_configuration_file(self):
        """設定ファイル読み込み"""
        try:
            if self.config_file_path.exists():
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 設定適用
                for key, value in config_data.get("global_config", {}).items():
                    if hasattr(self.current_config, key):
                        setattr(self.current_config, key, value)
                
                # スコープ別設定読み込み
                self.scoped_configs = config_data.get("scoped_configs", {})
                
                # A/Bテスト設定読み込み
                self.ab_tests = config_data.get("ab_tests", {})
                
                self.logger.info("Configuration loaded from file")
            else:
                self.logger.info("Configuration file not found, using defaults")
        
        except Exception as e:
            self.logger.error(f"Configuration file loading error: {e}")
    
    async def save_configuration_file(self):
        """設定ファイル保存"""
        try:
            config_data = {
                "global_config": asdict(self.current_config),
                "scoped_configs": self.scoped_configs,
                "ab_tests": self.ab_tests,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # バックアップ作成
            if self.config_file_path.exists():
                backup_path = self.config_file_path.with_suffix('.backup')
                self.config_file_path.rename(backup_path)
            
            # 新しい設定保存
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Configuration saved to file")
            
        except Exception as e:
            self.logger.error(f"Configuration file saving error: {e}")
    
    async def update_configuration(self,
                                 config_path: str,
                                 new_value: Any,
                                 scope: ConfigurationScope = ConfigurationScope.GLOBAL,
                                 scope_id: Optional[str] = None,
                                 reason: str = "Manual update",
                                 user_id: Optional[str] = None) -> bool:
        """設定更新"""
        try:
            # 現在の値取得
            old_value = await self._get_config_value(config_path, scope, scope_id)
            
            # 設定適用
            success = await self._apply_configuration_change(
                config_path, new_value, scope, scope_id
            )
            
            if success:
                # 変更記録
                change = ConfigurationChange(
                    timestamp=datetime.utcnow(),
                    scope=scope,
                    config_path=config_path,
                    old_value=old_value,
                    new_value=new_value,
                    reason=reason,
                    user_id=user_id,
                    session_id=scope_id if scope == ConfigurationScope.SESSION else None
                )
                
                self.configuration_history.append(change)
                
                # 履歴サイズ制限
                if len(self.configuration_history) > self.max_history_size:
                    self.configuration_history = self.configuration_history[-self.max_history_size:]
                
                # コールバック実行
                await self._notify_configuration_change(change)
                
                self.logger.info(
                    f"Configuration updated",
                    config_path=config_path,
                    scope=scope.value,
                    old_value=old_value,
                    new_value=new_value
                )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Configuration update error: {e}")
            return False
    
    async def _get_config_value(self,
                              config_path: str,
                              scope: ConfigurationScope,
                              scope_id: Optional[str] = None) -> Any:
        """設定値取得"""
        if scope == ConfigurationScope.GLOBAL:
            # グローバル設定から取得
            config_obj = self.current_config
            for path_part in config_path.split('.'):
                if hasattr(config_obj, path_part):
                    config_obj = getattr(config_obj, path_part)
                else:
                    return None
            return config_obj
        else:
            # スコープ別設定から取得
            scope_key = f"{scope.value}:{scope_id}" if scope_id else scope.value
            return self.scoped_configs.get(scope_key, {}).get(config_path)
    
    async def _apply_configuration_change(self,
                                        config_path: str,
                                        new_value: Any,
                                        scope: ConfigurationScope,
                                        scope_id: Optional[str] = None) -> bool:
        """設定変更適用"""
        try:
            if scope == ConfigurationScope.GLOBAL:
                # グローバル設定更新
                config_obj = self.current_config
                path_parts = config_path.split('.')
                
                for path_part in path_parts[:-1]:
                    if hasattr(config_obj, path_part):
                        config_obj = getattr(config_obj, path_part)
                    else:
                        return False
                
                if hasattr(config_obj, path_parts[-1]):
                    setattr(config_obj, path_parts[-1], new_value)
                    return True
                else:
                    return False
            else:
                # スコープ別設定更新
                scope_key = f"{scope.value}:{scope_id}" if scope_id else scope.value
                
                if scope_key not in self.scoped_configs:
                    self.scoped_configs[scope_key] = {}
                
                self.scoped_configs[scope_key][config_path] = new_value
                return True
            
        except Exception as e:
            self.logger.error(f"Configuration change application error: {e}")
            return False
    
    async def get_effective_configuration(self,
                                        session_id: Optional[str] = None,
                                        user_id: Optional[str] = None,
                                        phase_num: Optional[int] = None) -> Dict[str, Any]:
        """有効設定取得（優先度順: フェーズ > セッション > ユーザー > グローバル）"""
        try:
            effective_config = asdict(self.current_config)
            
            # A/Bテスト設定適用
            if user_id:
                ab_config = await self._get_ab_test_configuration(user_id)
                effective_config.update(ab_config)
            
            # ユーザー設定適用
            if user_id:
                user_config = self.scoped_configs.get(f"user:{user_id}", {})
                effective_config.update(user_config)
            
            # セッション設定適用
            if session_id:
                session_config = self.scoped_configs.get(f"session:{session_id}", {})
                effective_config.update(session_config)
            
            # フェーズ設定適用
            if phase_num:
                phase_config = self.scoped_configs.get(f"phase:{phase_num}", {})
                effective_config.update(phase_config)
            
            return effective_config
            
        except Exception as e:
            self.logger.error(f"Effective configuration retrieval error: {e}")
            return asdict(self.current_config)
    
    async def _get_ab_test_configuration(self, user_id: str) -> Dict[str, Any]:
        """A/Bテスト設定取得"""
        ab_config = {}
        
        for test_name, test_config in self.ab_tests.items():
            if not test_config.get("enabled", False):
                continue
            
            # ユーザーのテストグループ決定
            user_hash = hash(user_id + test_name) % 100
            
            if user_hash < test_config.get("test_percentage", 50):
                # テストグループの設定適用
                ab_config.update(test_config.get("test_config", {}))
            else:
                # コントロールグループの設定適用
                ab_config.update(test_config.get("control_config", {}))
        
        return ab_config
    
    async def create_ab_test(self,
                           test_name: str,
                           test_config: Dict[str, Any],
                           control_config: Dict[str, Any],
                           test_percentage: int = 50,
                           duration_hours: int = 24) -> bool:
        """A/Bテスト作成"""
        try:
            self.ab_tests[test_name] = {
                "test_config": test_config,
                "control_config": control_config,
                "test_percentage": test_percentage,
                "duration_hours": duration_hours,
                "start_time": datetime.utcnow().isoformat(),
                "enabled": True
            }
            
            self.logger.info(f"A/B test created: {test_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"A/B test creation error: {e}")
            return False
    
    async def _setup_default_optimization_rules(self):
        """デフォルト最適化ルール設定"""
        default_rules = [
            PerformanceOptimizationRule(
                name="reduce_workers_on_high_cpu",
                condition="cpu_usage > 80",
                action="reduce_workers",
                parameters={"reduction_factor": 0.8},
                priority=1
            ),
            PerformanceOptimizationRule(
                name="increase_workers_on_low_cpu",
                condition="cpu_usage < 40 and queue_length > 10",
                action="increase_workers",
                parameters={"increase_factor": 1.2, "max_workers": 10},
                priority=3
            ),
            PerformanceOptimizationRule(
                name="reduce_batch_size_on_high_memory",
                condition="memory_usage > 85",
                action="reduce_batch_size",
                parameters={"reduction_factor": 0.7},
                priority=2
            ),
            PerformanceOptimizationRule(
                name="enable_caching_on_repeated_patterns",
                condition="cache_hit_rate < 0.3 and processing_time > 20",
                action="enable_aggressive_caching",
                parameters={"cache_size_multiplier": 2},
                priority=4
            )
        ]
        
        self.optimization_rules.extend(default_rules)
    
    async def apply_auto_optimization(self, metrics: Dict[str, float]) -> List[str]:
        """自動最適化適用"""
        applied_optimizations = []
        
        if not self.auto_optimization_enabled:
            return applied_optimizations
        
        try:
            # 優先度順にルールを評価
            sorted_rules = sorted(self.optimization_rules, key=lambda r: r.priority)
            
            for rule in sorted_rules:
                if not rule.enabled:
                    continue
                
                # 条件評価
                if await self._evaluate_optimization_condition(rule.condition, metrics):
                    # アクション実行
                    success = await self._execute_optimization_action(rule.action, rule.parameters)
                    
                    if success:
                        applied_optimizations.append(rule.name)
                        
                        self.logger.info(
                            f"Auto-optimization applied: {rule.name}",
                            action=rule.action,
                            parameters=rule.parameters
                        )
            
            return applied_optimizations
            
        except Exception as e:
            self.logger.error(f"Auto-optimization error: {e}")
            return applied_optimizations
    
    async def _evaluate_optimization_condition(self, condition: str, metrics: Dict[str, float]) -> bool:
        """最適化条件評価"""
        try:
            # 安全な条件評価（eval使用時は注意が必要）
            allowed_names = {
                "cpu_usage": metrics.get("cpu_usage", 0),
                "memory_usage": metrics.get("memory_usage", 0),
                "queue_length": metrics.get("queue_length", 0),
                "processing_time": metrics.get("processing_time", 0),
                "cache_hit_rate": metrics.get("cache_hit_rate", 0),
                "error_rate": metrics.get("error_rate", 0)
            }
            
            # 数学演算子のみ許可
            allowed_operators = ['>', '<', '>=', '<=', '==', '!=', 'and', 'or', 'not']
            
            # 条件文字列を安全にチェック
            if any(op in condition for op in ['import', 'exec', 'eval', '__']):
                self.logger.warning(f"Unsafe condition detected: {condition}")
                return False
            
            return eval(condition, {"__builtins__": {}}, allowed_names)
            
        except Exception as e:
            self.logger.error(f"Condition evaluation error: {e}")
            return False
    
    async def _execute_optimization_action(self, action: str, parameters: Dict[str, Any]) -> bool:
        """最適化アクション実行"""
        try:
            if action == "reduce_workers":
                factor = parameters.get("reduction_factor", 0.8)
                new_workers = int(self.current_config.max_concurrent_workers * factor)
                return await self.update_configuration(
                    "max_concurrent_workers",
                    max(1, new_workers),
                    reason=f"Auto-optimization: {action}",
                    scope=ConfigurationScope.TEMPORARY
                )
            
            elif action == "increase_workers":
                factor = parameters.get("increase_factor", 1.2)
                max_workers = parameters.get("max_workers", 10)
                new_workers = int(self.current_config.max_concurrent_workers * factor)
                return await self.update_configuration(
                    "max_concurrent_workers",
                    min(max_workers, new_workers),
                    reason=f"Auto-optimization: {action}",
                    scope=ConfigurationScope.TEMPORARY
                )
            
            elif action == "reduce_batch_size":
                factor = parameters.get("reduction_factor", 0.7)
                new_batch_size = int(self.current_config.quality_gate_batch_size * factor)
                return await self.update_configuration(
                    "quality_gate_batch_size",
                    max(1, new_batch_size),
                    reason=f"Auto-optimization: {action}",
                    scope=ConfigurationScope.TEMPORARY
                )
            
            elif action == "enable_aggressive_caching":
                # キャッシュ設定の最適化実装
                return True
            
            else:
                self.logger.warning(f"Unknown optimization action: {action}")
                return False
            
        except Exception as e:
            self.logger.error(f"Optimization action execution error: {e}")
            return False
    
    async def _notify_configuration_change(self, change: ConfigurationChange):
        """設定変更通知"""
        for callback in self.change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(change)
                else:
                    callback(change)
            except Exception as e:
                self.logger.error(f"Configuration change callback error: {e}")
    
    def add_change_callback(self, callback: Callable):
        """設定変更コールバック追加"""
        self.change_callbacks.append(callback)
    
    async def create_configuration_backup(self, backup_name: str) -> bool:
        """設定バックアップ作成"""
        try:
            backup_data = {
                "config": asdict(self.current_config),
                "scoped_configs": self.scoped_configs.copy(),
                "ab_tests": self.ab_tests.copy(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.config_backups[backup_name] = backup_data
            
            self.logger.info(f"Configuration backup created: {backup_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration backup error: {e}")
            return False
    
    async def restore_configuration_backup(self, backup_name: str) -> bool:
        """設定バックアップ復元"""
        try:
            if backup_name not in self.config_backups:
                self.logger.error(f"Backup not found: {backup_name}")
                return False
            
            backup_data = self.config_backups[backup_name]
            
            # 設定復元
            for key, value in backup_data["config"].items():
                if hasattr(self.current_config, key):
                    setattr(self.current_config, key, value)
            
            self.scoped_configs = backup_data["scoped_configs"].copy()
            self.ab_tests = backup_data["ab_tests"].copy()
            
            self.logger.info(f"Configuration restored from backup: {backup_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration restore error: {e}")
            return False
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """設定状況取得"""
        return {
            "current_config": asdict(self.current_config),
            "scoped_config_count": len(self.scoped_configs),
            "active_ab_tests": len([t for t in self.ab_tests.values() if t.get("enabled")]),
            "optimization_rules_count": len([r for r in self.optimization_rules if r.enabled]),
            "auto_optimization_enabled": self.auto_optimization_enabled,
            "configuration_changes": len(self.configuration_history),
            "available_backups": list(self.config_backups.keys()),
            "last_updated": datetime.utcnow().isoformat()
        }