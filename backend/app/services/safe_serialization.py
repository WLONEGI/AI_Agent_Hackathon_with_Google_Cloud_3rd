"""
Safe Serialization Service - Replaces pickle with secure JSON serialization
SECURITY: Eliminates RCE attack vector from pickle.loads()
"""

import json
import base64
import gzip
from typing import Any, Dict, Optional, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SafeSerializer:
    """Production-safe serialization without pickle vulnerabilities."""
    
    @staticmethod
    def serialize(data: Any, compress: bool = False) -> str:
        """
        Safely serialize data to JSON string.
        
        Args:
            data: Data to serialize (must be JSON-compatible)
            compress: Whether to compress with gzip
            
        Returns:
            Serialized string safe for storage
            
        Raises:
            ValueError: If data contains non-serializable objects
        """
        try:
            # Convert complex objects to JSON-compatible format
            json_data = SafeSerializer._make_serializable(data)
            
            # Serialize to JSON
            json_str = json.dumps(json_data, ensure_ascii=False, separators=(',', ':'))
            
            if compress:
                # Compress and base64 encode
                compressed = gzip.compress(json_str.encode('utf-8'))
                return base64.b64encode(compressed).decode('ascii')
            
            return json_str
            
        except Exception as e:
            logger.error(f"Serialization failed: {e}")
            raise ValueError(f"Failed to serialize data: {str(e)}")
    
    @staticmethod
    def deserialize(data_str: str, compressed: bool = False) -> Any:
        """
        Safely deserialize JSON string to Python objects.
        
        Args:
            data_str: Serialized string from serialize()
            compressed: Whether data is compressed
            
        Returns:
            Deserialized Python object
            
        Raises:
            ValueError: If deserialization fails
        """
        try:
            if compressed:
                # Base64 decode and decompress
                compressed_data = base64.b64decode(data_str.encode('ascii'))
                json_str = gzip.decompress(compressed_data).decode('utf-8')
            else:
                json_str = data_str
            
            # Parse JSON safely
            return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"Deserialization failed: {e}")
            raise ValueError(f"Failed to deserialize data: {str(e)}")
    
    @staticmethod
    def _make_serializable(obj: Any) -> Any:
        """Convert objects to JSON-compatible format."""
        
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [SafeSerializer._make_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {str(k): SafeSerializer._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            # Convert object to dict, filtering private attributes
            return {
                k: SafeSerializer._make_serializable(v)
                for k, v in obj.__dict__.items()
                if not k.startswith('_')
            }
        else:
            # Convert to string as fallback
            return str(obj)


class CacheMigrator:
    """Migrate existing pickle-based cache data to safe format."""
    
    @staticmethod
    def migrate_redis_data(redis_client, pattern: str = "*") -> Dict[str, int]:
        """
        Migrate Redis cache from pickle to JSON format.
        
        Returns:
            Migration statistics
        """
        stats = {
            "scanned": 0,
            "migrated": 0,
            "failed": 0,
            "skipped": 0
        }
        
        try:
            # Scan for keys to migrate
            for key in redis_client.scan_iter(pattern):
                stats["scanned"] += 1
                
                try:
                    # Get existing data
                    raw_data = redis_client.get(key)
                    if not raw_data:
                        stats["skipped"] += 1
                        continue
                    
                    # Check if already JSON
                    try:
                        json.loads(raw_data)
                        stats["skipped"] += 1  # Already JSON
                        continue
                    except json.JSONDecodeError:
                        pass  # Not JSON, needs migration
                    
                    # Attempt to deserialize with pickle (dangerous but necessary for migration)
                    import pickle
                    try:
                        old_data = pickle.loads(raw_data.encode('latin-1'))
                    except:
                        stats["failed"] += 1
                        logger.warning(f"Failed to read pickle data for key: {key}")
                        continue
                    
                    # Convert to safe format
                    new_data = SafeSerializer.serialize(old_data)
                    
                    # Replace with safe data
                    redis_client.set(key, new_data)
                    stats["migrated"] += 1
                    
                except Exception as e:
                    stats["failed"] += 1
                    logger.error(f"Migration failed for key {key}: {e}")
        
        except Exception as e:
            logger.error(f"Redis migration failed: {e}")
            raise
        
        return stats


# Migration utility functions
def safe_serialize(data: Any, compress: bool = False) -> str:
    """Replacement for pickle.dumps()"""
    return SafeSerializer.serialize(data, compress)


def safe_deserialize(data_str: str, compressed: bool = False) -> Any:
    """Replacement for pickle.loads()"""
    return SafeSerializer.deserialize(data_str, compressed)


# Emergency migration for existing cache_service.py
async def migrate_cache_service():
    """
    Emergency migration of cache service from pickle to safe serialization.
    Run this immediately to eliminate RCE vulnerability.
    """
    from app.core.redis_client import redis_manager
    
    migrator = CacheMigrator()
    redis_client = await redis_manager.get_client()
    
    # Migrate all cache data
    stats = migrator.migrate_redis_data(redis_client)
    
    logger.info("Cache migration completed", **stats)
    return stats