"""Mock services for local development."""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import uuid4
import asyncio
import json
import random
from collections import defaultdict
import structlog

logger = structlog.get_logger(__name__)

# In-memory storage for mock data
MOCK_STORAGE = {
    "users": {},
    "sessions": {},
    "manga_generations": {},
    "phase_results": defaultdict(list),
}


class MockRedis:
    """Mock Redis implementation for local development."""
    
    def __init__(self):
        self.data = {}
        self.expires = {}
        logger.info("MockRedis initialized")
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from mock Redis."""
        if key in self.expires and datetime.now() > self.expires[key]:
            del self.data[key]
            del self.expires[key]
            return None
        return self.data.get(key)
    
    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """Set value in mock Redis."""
        self.data[key] = value
        if expire:
            self.expires[key] = datetime.now() + timedelta(seconds=expire)
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from mock Redis."""
        if key in self.data:
            del self.data[key]
            if key in self.expires:
                del self.expires[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return key in self.data
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key."""
        if key in self.data:
            self.expires[key] = datetime.now() + timedelta(seconds=seconds)
            return True
        return False
    
    async def hset(self, name: str, key: str, value: str) -> int:
        """Set hash field."""
        if name not in self.data:
            self.data[name] = {}
        self.data[name][key] = value
        return 1
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field."""
        if name in self.data and isinstance(self.data[name], dict):
            return self.data[name].get(key)
        return None
    
    async def hgetall(self, name: str) -> Dict[str, str]:
        """Get all hash fields."""
        if name in self.data and isinstance(self.data[name], dict):
            return self.data[name]
        return {}


class MockDatabase:
    """Mock database implementation for local development."""
    
    def __init__(self):
        self.tables = defaultdict(dict)
        self._init_mock_data()
        logger.info("MockDatabase initialized")
    
    def _init_mock_data(self):
        """Initialize with some mock data."""
        # Create a mock user
        mock_user_id = "mock-user-123"
        self.tables["users"][mock_user_id] = {
            "id": mock_user_id,
            "email": "test@example.com",
            "username": "testuser",
            "display_name": "Test User",
            "account_type": "free",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "daily_generation_limit": 5,
            "daily_generations_used": 0,
        }
    
    async def get(self, table: str, id: str) -> Optional[Dict[str, Any]]:
        """Get record by ID."""
        return self.tables[table].get(id)
    
    async def create(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new record."""
        if "id" not in data:
            data["id"] = str(uuid4())
        data["created_at"] = datetime.utcnow().isoformat()
        data["updated_at"] = data["created_at"]
        self.tables[table][data["id"]] = data
        return data
    
    async def update(self, table: str, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing record."""
        if id in self.tables[table]:
            self.tables[table][id].update(data)
            self.tables[table][id]["updated_at"] = datetime.utcnow().isoformat()
            return self.tables[table][id]
        return None
    
    async def delete(self, table: str, id: str) -> bool:
        """Delete record."""
        if id in self.tables[table]:
            del self.tables[table][id]
            return True
        return False
    
    async def query(self, table: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Query records with filters."""
        results = list(self.tables[table].values())
        if filters:
            for key, value in filters.items():
                results = [r for r in results if r.get(key) == value]
        return results


class MockAIService:
    """Mock AI service for local development."""
    
    def __init__(self):
        self.generation_counter = 0
        logger.info("MockAIService initialized")
    
    async def generate_concept(self, text: str) -> Dict[str, Any]:
        """Generate mock concept analysis."""
        await asyncio.sleep(0.5)  # Simulate processing time
        return {
            "world_setting": "ファンタジー世界",
            "genre": "冒険・アクション",
            "theme": "友情と成長",
            "tone": "明るく前向き",
            "target_audience": "少年・青年",
            "key_elements": ["魔法", "冒険", "仲間", "成長"],
            "confidence_score": 0.95
        }
    
    async def generate_characters(self, concept: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock character designs."""
        await asyncio.sleep(0.7)
        return {
            "main_character": {
                "name": "勇者太郎",
                "age": 16,
                "personality": "明るく前向き",
                "appearance": "黒髪、青い瞳",
                "abilities": ["剣術", "魔法"],
                "visual_description": "A young hero with black hair and blue eyes"
            },
            "supporting_characters": [
                {
                    "name": "魔法使い花子",
                    "role": "仲間",
                    "personality": "賢く冷静",
                    "appearance": "長い金髪、緑の瞳"
                }
            ]
        }
    
    async def generate_plot(self, concept: Dict[str, Any], characters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock plot structure."""
        await asyncio.sleep(0.6)
        return {
            "synopsis": "勇者が仲間と共に魔王を倒す冒険",
            "acts": [
                {
                    "act_number": 1,
                    "title": "旅立ち",
                    "description": "主人公が冒険に出る決意をする",
                    "scenes": ["村での日常", "運命の出会い", "旅立ちの決意"]
                },
                {
                    "act_number": 2,
                    "title": "試練",
                    "description": "仲間と共に困難を乗り越える",
                    "scenes": ["最初の戦い", "仲間との絆", "力の覚醒"]
                },
                {
                    "act_number": 3,
                    "title": "決戦",
                    "description": "魔王との最終決戦",
                    "scenes": ["魔王城への潜入", "最終決戦", "新たな旅立ち"]
                }
            ]
        }
    
    async def generate_panels(self, plot: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock manga panels layout."""
        await asyncio.sleep(0.8)
        return {
            "total_pages": 8,
            "panels": [
                {
                    "page": 1,
                    "panel_count": 4,
                    "layout": "2x2",
                    "panels": [
                        {"id": "p1_1", "description": "村の全景"},
                        {"id": "p1_2", "description": "主人公のアップ"},
                        {"id": "p1_3", "description": "仲間との出会い"},
                        {"id": "p1_4", "description": "旅立ちの決意"}
                    ]
                }
            ]
        }
    
    async def generate_image(self, prompt: str) -> str:
        """Generate mock image URL."""
        await asyncio.sleep(1.0)
        self.generation_counter += 1
        # Return a placeholder image URL
        return f"https://via.placeholder.com/512x768.png?text=Scene_{self.generation_counter}"
    
    async def generate_dialogue(self, panels: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock dialogue for panels."""
        await asyncio.sleep(0.4)
        return {
            "dialogues": [
                {
                    "panel_id": "p1_1",
                    "text": "これが僕たちの村...",
                    "speaker": "narration"
                },
                {
                    "panel_id": "p1_2",
                    "text": "今日から冒険が始まるんだ！",
                    "speaker": "main_character"
                },
                {
                    "panel_id": "p1_3",
                    "text": "一緒に行こう！",
                    "speaker": "supporting_character"
                },
                {
                    "panel_id": "p1_4",
                    "text": "よし、出発だ！",
                    "speaker": "main_character"
                }
            ]
        }
    
    async def finalize_manga(self, all_data: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize and integrate all manga components."""
        await asyncio.sleep(0.3)
        return {
            "manga_id": str(uuid4()),
            "title": all_data.get("title", "無題の漫画"),
            "pages": 8,
            "status": "completed",
            "preview_url": "https://via.placeholder.com/800x1200.png?text=Manga+Preview",
            "download_url": f"/api/v1/manga/{uuid4()}/download",
            "quality_score": 0.92,
            "generation_time_seconds": 5.5,
            "created_at": datetime.utcnow().isoformat()
        }


class MockAuthService:
    """Mock authentication service for local development."""
    
    def __init__(self):
        self.mock_users = {}
        self._init_mock_users()
        logger.info("MockAuthService initialized")
    
    def _init_mock_users(self):
        """Initialize mock users."""
        self.mock_users["mock-user-123"] = {
            "uid": "mock-user-123",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "https://via.placeholder.com/96",
            "email_verified": True,
            "provider": "google.com"
        }
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify mock token."""
        # For mock, accept any token that starts with "mock-"
        if token.startswith("mock-") or token.startswith("eyJ"):
            return {
                "uid": "mock-user-123",
                "email": "test@example.com",
                "email_verified": True,
                "name": "Test User"
            }
        return None
    
    async def get_user(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get mock user info."""
        return self.mock_users.get(uid)
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create mock user."""
        uid = user_data.get("uid", str(uuid4()))
        self.mock_users[uid] = {
            "uid": uid,
            "email": user_data.get("email"),
            "name": user_data.get("name", "Mock User"),
            "picture": user_data.get("picture", "https://via.placeholder.com/96"),
            "email_verified": True,
            "provider": "mock"
        }
        return self.mock_users[uid]


# Global mock service instances
_mock_redis = None
_mock_database = None
_mock_ai_service = None
_mock_auth_service = None


def get_mock_redis() -> MockRedis:
    """Get mock Redis instance."""
    global _mock_redis
    if _mock_redis is None:
        _mock_redis = MockRedis()
    return _mock_redis


def get_mock_database() -> MockDatabase:
    """Get mock database instance."""
    global _mock_database
    if _mock_database is None:
        _mock_database = MockDatabase()
    return _mock_database


def get_mock_ai_service() -> MockAIService:
    """Get mock AI service instance."""
    global _mock_ai_service
    if _mock_ai_service is None:
        _mock_ai_service = MockAIService()
    return _mock_ai_service


def get_mock_auth_service() -> MockAuthService:
    """Get mock auth service instance."""
    global _mock_auth_service
    if _mock_auth_service is None:
        _mock_auth_service = MockAuthService()
    return _mock_auth_service