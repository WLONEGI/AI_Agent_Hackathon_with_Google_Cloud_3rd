"""Redis connection and cache management."""

import json
import asyncio
from typing import Any, Optional, Union
from datetime import timedelta
import redis.asyncio as aioredis
from redis.exceptions import RedisError
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis connection manager with caching utilities."""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self._pool = None
        self._healthy = False
    
    async def connect(self) -> None:
        """Initialize Redis connection pool."""
        try:
            self._pool = aioredis.ConnectionPool.from_url(
                settings.redis_url,
                max_connections=settings.redis_max_connections,
                decode_responses=True
            )
            self.redis = aioredis.Redis(connection_pool=self._pool)
            await self.redis.ping()
            self._healthy = True
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connections."""
        try:
            if self.redis:
                await self.redis.close()
                await self._pool.disconnect()
            logger.info("Redis connections closed")
        except Exception as e:
            logger.error(f"Error closing Redis connections: {e}")
    
    async def health_check(self) -> bool:
        """Check Redis connection health."""
        try:
            if self.redis:
                await self.redis.ping()
                self._healthy = True
                return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            self._healthy = False
        return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except json.JSONDecodeError:
            # Return raw value if not JSON
            return value
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set value in cache with optional TTL."""
        try:
            # Convert value to JSON if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)
            
            if ttl:
                if isinstance(ttl, timedelta):
                    ttl = int(ttl.total_seconds())
                return await self.redis.setex(key, ttl, value)
            else:
                return await self.redis.set(key, value)
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            return await self.redis.delete(key) > 0
        except Exception as e:
            logger.error(f"Error deleting key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking key existence {key}: {e}")
            return False
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        try:
            return await self.redis.incr(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing key {key}: {e}")
            return 0
    
    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """Set expiration time for key."""
        try:
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            return await self.redis.expire(key, ttl)
        except Exception as e:
            logger.error(f"Error setting expiration for key {key}: {e}")
            return False
    
    async def get_ttl(self, key: str) -> int:
        """Get TTL for key in seconds."""
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key {key}: {e}")
            return -1
    
    # Hash operations
    async def hset(self, name: str, key: str, value: Any) -> bool:
        """Set hash field."""
        try:
            if not isinstance(value, str):
                value = json.dumps(value)
            return await self.redis.hset(name, key, value)
        except Exception as e:
            logger.error(f"Error setting hash field {name}:{key}: {e}")
            return False
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """Get hash field."""
        try:
            value = await self.redis.hget(name, key)
            if value:
                return json.loads(value)
            return None
        except json.JSONDecodeError:
            return value
        except Exception as e:
            logger.error(f"Error getting hash field {name}:{key}: {e}")
            return None
    
    async def hgetall(self, name: str) -> dict:
        """Get all hash fields."""
        try:
            data = await self.redis.hgetall(name)
            result = {}
            for key, value in data.items():
                try:
                    result[key] = json.loads(value)
                except json.JSONDecodeError:
                    result[key] = value
            return result
        except Exception as e:
            logger.error(f"Error getting hash {name}: {e}")
            return {}
    
    # List operations
    async def lpush(self, key: str, value: Any) -> int:
        """Push value to list head."""
        try:
            if not isinstance(value, str):
                value = json.dumps(value)
            return await self.redis.lpush(key, value)
        except Exception as e:
            logger.error(f"Error pushing to list {key}: {e}")
            return 0
    
    async def lrange(self, key: str, start: int, stop: int) -> list:
        """Get list range."""
        try:
            values = await self.redis.lrange(key, start, stop)
            result = []
            for value in values:
                try:
                    result.append(json.loads(value))
                except json.JSONDecodeError:
                    result.append(value)
            return result
        except Exception as e:
            logger.error(f"Error getting list range {key}: {e}")
            return []
    
    # Set operations  
    async def sadd(self, key: str, *values) -> int:
        """Add values to set."""
        try:
            return await self.redis.sadd(key, *values)
        except Exception as e:
            logger.error(f"Error adding to set {key}: {e}")
            return 0
    
    async def smembers(self, key: str) -> set:
        """Get all set members."""
        try:
            return await self.redis.smembers(key)
        except Exception as e:
            logger.error(f"Error getting set members {key}: {e}")
            return set()
    
    @property
    def is_healthy(self) -> bool:
        """Check if Redis connection is healthy."""
        return self._healthy


class CacheService:
    """High-level caching service with TTL strategies."""
    
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager
        
        # TTL strategies in seconds
        self.ttl_strategies = {
            'session': settings.cache_l1_ttl_seconds,
            'preview': 120,  # 2 minutes for preview data
            'phase_result': settings.cache_l2_ttl_seconds,
            'user_data': 1800,  # 30 minutes
            'generated_image': settings.cache_l3_ttl_seconds,
        }
    
    async def get_cached_or_compute(
        self,
        key: str,
        compute_func,
        ttl_type: str = 'session'
    ) -> Any:
        """Get from cache or compute and cache."""
        # Try to get from cache
        cached = await self.redis.get(key)
        if cached is not None:
            logger.debug(f"Cache hit for key: {key}")
            return cached
        
        # Compute value
        logger.debug(f"Cache miss for key: {key}, computing...")
        value = await compute_func()
        
        # Cache the result
        ttl = self.ttl_strategies.get(ttl_type, 300)
        await self.redis.set(key, value, ttl)
        
        return value
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        try:
            keys = []
            async for key in self.redis.redis.scan_iter(pattern):
                keys.append(key)
            
            if keys:
                return await self.redis.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error invalidating pattern {pattern}: {e}")
            return 0


# Global Redis manager instance
redis_manager = RedisManager()

# Global cache service instance
cache_service = CacheService(redis_manager)