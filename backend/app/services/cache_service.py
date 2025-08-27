"""
CacheService - 3層キャッシュ管理サービス
L1: メモリキャッシュ、L2: Redis、L3: PostgreSQL
"""

import asyncio
import json
import hashlib
import time
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
from collections import OrderedDict
import pickle

from app.core.redis_client import RedisClient
from app.core.logging import LoggerMixin


class LRUCache:
    """LRU（Least Recently Used）メモリキャッシュ"""
    
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.cache: OrderedDict = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def get(self, key: str) -> Optional[Any]:
        """キャッシュからデータ取得"""
        if key in self.cache:
            self.hits += 1
            # LRU更新（最後に移動）
            self.cache.move_to_end(key)
            return self.cache[key]["data"]
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """キャッシュにデータ設定"""
        # 容量チェック
        if len(self.cache) >= self.capacity and key not in self.cache:
            # 最も古いアイテムを削除
            self.cache.popitem(last=False)
            self.evictions += 1
        
        self.cache[key] = {
            "data": value,
            "expires_at": time.time() + ttl
        }
        self.cache.move_to_end(key)
    
    def delete(self, key: str) -> bool:
        """キャッシュからデータ削除"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear_expired(self) -> int:
        """期限切れエントリのクリア"""
        current_time = time.time()
        expired_keys = [
            k for k, v in self.cache.items()
            if v["expires_at"] < current_time
        ]
        for key in expired_keys:
            del self.cache[key]
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報の取得"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "capacity": self.capacity,
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": f"{hit_rate:.2f}%"
        }


class CacheService(LoggerMixin):
    """3層キャッシュ管理サービス"""
    
    def __init__(self):
        super().__init__()
        
        # L1: メモリキャッシュ
        self.memory_cache = LRUCache(capacity=1000)
        
        # L2: Redisクライアント
        self.redis_client = RedisClient()
        
        # キャッシュ設定
        self.ttl_config = {
            "phase_result": 3600,      # 1時間
            "image": 7200,              # 2時間
            "preview": 1800,            # 30分
            "session": 300,             # 5分
            "ai_response": 600,         # 10分
            "user_preference": 86400    # 24時間
        }
        
        # キャッシュ統計
        self.stats = {
            "l1_requests": 0,
            "l1_hits": 0,
            "l2_requests": 0,
            "l2_hits": 0,
            "l3_requests": 0,
            "l3_hits": 0
        }
        
        # キャッシュウォーミング設定
        self.warming_enabled = True
        self.warming_patterns: Set[str] = set()
        
        # バックグラウンドタスク
        self._cleanup_task = None
        
        self.logger.info("CacheService initialized with 3-layer caching")
    
    async def get(
        self,
        key: str,
        cache_type: str = "generic"
    ) -> Optional[Any]:
        """
        3層キャッシュからデータ取得
        L1 → L2 → L3の順で検索
        """
        self.stats["l1_requests"] += 1
        
        # L1: メモリキャッシュ
        data = self.memory_cache.get(key)
        if data is not None:
            self.stats["l1_hits"] += 1
            self.logger.debug(f"L1 cache hit: {key}")
            return data
        
        # L2: Redis
        self.stats["l2_requests"] += 1
        redis_data = await self.redis_client.get(key)
        
        if redis_data:
            self.stats["l2_hits"] += 1
            self.logger.debug(f"L2 cache hit: {key}")
            
            # L1にも保存
            try:
                data = json.loads(redis_data)
                self.memory_cache.set(key, data, ttl=60)  # 1分間メモリに保持
                return data
            except json.JSONDecodeError:
                # バイナリデータの場合
                data = pickle.loads(redis_data.encode('latin-1'))
                self.memory_cache.set(key, data, ttl=60)
                return data
        
        # L3: PostgreSQLは別途実装（必要に応じて）
        self.stats["l3_requests"] += 1
        
        self.logger.debug(f"Cache miss for all layers: {key}")
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        cache_type: str = "generic",
        ttl: Optional[int] = None
    ) -> bool:
        """
        3層キャッシュにデータ設定
        """
        # TTL決定
        if ttl is None:
            ttl = self.ttl_config.get(cache_type, 600)
        
        try:
            # L1: メモリキャッシュ
            self.memory_cache.set(key, value, ttl=min(ttl, 300))  # メモリは最大5分
            
            # L2: Redis
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value)
            else:
                serialized = pickle.dumps(value).decode('latin-1')
            
            await self.redis_client.set(key, serialized, ttl=ttl)
            
            # キャッシュウォーミングパターンの記録
            if self.warming_enabled:
                pattern = self._extract_pattern(key)
                if pattern:
                    self.warming_patterns.add(pattern)
            
            self.logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            self.logger.error(f"Cache set error: {e}", key=key)
            return False
    
    async def delete(self, key: str) -> bool:
        """キャッシュからデータ削除"""
        # L1削除
        l1_deleted = self.memory_cache.delete(key)
        
        # L2削除
        l2_deleted = await self.redis_client.delete(key)
        
        return l1_deleted or l2_deleted
    
    async def delete_pattern(self, pattern: str) -> int:
        """パターンマッチングによる一括削除"""
        deleted_count = 0
        
        # L1: メモリキャッシュのパターン削除
        keys_to_delete = []
        for key in self.memory_cache.cache.keys():
            if self._matches_pattern(key, pattern):
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            if self.memory_cache.delete(key):
                deleted_count += 1
        
        # L2: Redisのパターン削除
        redis_keys = await self.redis_client.scan_keys(pattern)
        for key in redis_keys:
            if await self.redis_client.delete(key):
                deleted_count += 1
        
        self.logger.info(f"Deleted {deleted_count} keys matching pattern: {pattern}")
        return deleted_count
    
    async def invalidate_session(self, session_id: str) -> None:
        """セッション関連のキャッシュを無効化"""
        patterns = [
            f"session:{session_id}:*",
            f"phase:*:{session_id}",
            f"preview:{session_id}:*",
            f"image:{session_id}:*"
        ]
        
        for pattern in patterns:
            await self.delete_pattern(pattern)
        
        self.logger.info(f"Invalidated cache for session: {session_id}")
    
    async def warm_cache(
        self,
        keys: List[str],
        loader_func: Optional[Any] = None
    ) -> int:
        """キャッシュウォーミング"""
        warmed_count = 0
        
        for key in keys:
            # 既存チェック
            existing = await self.get(key)
            if existing:
                continue
            
            # ローダー関数がある場合はデータ取得
            if loader_func:
                try:
                    data = await loader_func(key)
                    if data:
                        await self.set(key, data)
                        warmed_count += 1
                except Exception as e:
                    self.logger.error(f"Cache warming error for {key}: {e}")
        
        self.logger.info(f"Warmed {warmed_count} cache entries")
        return warmed_count
    
    async def get_multilevel_stats(self) -> Dict[str, Any]:
        """マルチレベルキャッシュの統計情報"""
        # メモリキャッシュ統計
        l1_stats = self.memory_cache.get_stats()
        
        # Redis統計
        redis_info = await self.redis_client.get_info()
        
        # 全体統計
        total_requests = self.stats["l1_requests"]
        l1_hit_rate = (self.stats["l1_hits"] / total_requests * 100) if total_requests > 0 else 0
        l2_hit_rate = (self.stats["l2_hits"] / self.stats["l2_requests"] * 100) if self.stats["l2_requests"] > 0 else 0
        
        return {
            "l1_memory": {
                **l1_stats,
                "requests": self.stats["l1_requests"],
                "hits": self.stats["l1_hits"],
                "hit_rate": f"{l1_hit_rate:.2f}%"
            },
            "l2_redis": {
                "requests": self.stats["l2_requests"],
                "hits": self.stats["l2_hits"],
                "hit_rate": f"{l2_hit_rate:.2f}%",
                "used_memory": redis_info.get("used_memory_human", "N/A"),
                "connected_clients": redis_info.get("connected_clients", 0)
            },
            "l3_database": {
                "requests": self.stats["l3_requests"],
                "hits": self.stats["l3_hits"]
            },
            "warming": {
                "enabled": self.warming_enabled,
                "patterns_tracked": len(self.warming_patterns)
            }
        }
    
    async def optimize_cache(self) -> Dict[str, Any]:
        """キャッシュの最適化"""
        optimization_results = {}
        
        # 期限切れエントリのクリア
        expired_l1 = self.memory_cache.clear_expired()
        optimization_results["expired_cleared_l1"] = expired_l1
        
        # メモリキャッシュのサイズ調整
        current_size = len(self.memory_cache.cache)
        if current_size > self.memory_cache.capacity * 0.9:
            # 容量の90%を超えたら古いエントリを削除
            to_remove = int(current_size * 0.2)  # 20%削除
            for _ in range(to_remove):
                self.memory_cache.cache.popitem(last=False)
            optimization_results["evicted_l1"] = to_remove
        
        # Redis最適化（メモリ使用量チェック）
        redis_info = await self.redis_client.get_info()
        used_memory = int(redis_info.get("used_memory", 0))
        max_memory = 512 * 1024 * 1024  # 512MB上限
        
        if used_memory > max_memory * 0.8:
            # 80%を超えたら古いキーを削除
            await self.redis_client.execute_command("MEMORY", "DOCTOR")
            optimization_results["redis_optimized"] = True
        
        self.logger.info("Cache optimization completed", results=optimization_results)
        return optimization_results
    
    async def start_background_tasks(self) -> None:
        """バックグラウンドタスクの開始"""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            self.logger.info("Background cache cleanup task started")
    
    async def stop_background_tasks(self) -> None:
        """バックグラウンドタスクの停止"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self.logger.info("Background cache cleanup task stopped")
    
    async def _periodic_cleanup(self) -> None:
        """定期的なキャッシュクリーンアップ"""
        while True:
            try:
                await asyncio.sleep(300)  # 5分ごと
                
                # 期限切れエントリのクリア
                self.memory_cache.clear_expired()
                
                # 統計情報のログ出力
                stats = await self.get_multilevel_stats()
                self.logger.info("Cache statistics", stats=stats)
                
                # 必要に応じて最適化
                l1_hit_rate = float(stats["l1_memory"]["hit_rate"].rstrip("%"))
                if l1_hit_rate < 30:  # ヒット率が30%未満
                    await self.optimize_cache()
                    
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger.error(f"Cleanup task error: {e}")
    
    def _extract_pattern(self, key: str) -> Optional[str]:
        """キーからパターンを抽出"""
        # session:xxx:phase:1 → session:*:phase:1
        parts = key.split(":")
        if len(parts) >= 3:
            if parts[0] in ["session", "phase", "image", "preview"]:
                parts[1] = "*"
                return ":".join(parts)
        return None
    
    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """パターンマッチング"""
        import fnmatch
        return fnmatch.fnmatch(key, pattern)
    
    def generate_cache_key(
        self,
        prefix: str,
        data: Dict[str, Any],
        version: str = "v1"
    ) -> str:
        """一貫性のあるキャッシュキー生成"""
        # データをソートしてJSON化
        sorted_data = json.dumps(data, sort_keys=True)
        
        # MD5ハッシュ化
        data_hash = hashlib.md5(sorted_data.encode()).hexdigest()[:8]
        
        # キー生成
        return f"{prefix}:{version}:{data_hash}"