"""PreviewSystem - フェーズ特化型プレビューシステム

設計書要件:
- フェーズ特化型プレビューデータ生成
- 5段階品質管理（ULTRA_LOW(1) → ULTRA_HIGH(5)）
- CDN最適化・キャッシュ戦略
- デバイス性能検出・自動品質調整
"""

import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from uuid import UUID, uuid4
from enum import IntEnum, Enum
import json
import base64
from dataclasses import dataclass

from app.core.logging import LoggerMixin
from app.core.redis_client import redis_manager
from app.core.config.settings import get_settings
from app.domain.manga.value_objects import QualityLevel, PreviewData
from .websocket_manager import WebSocketManager


class QualityLevel(IntEnum):
    """Preview quality levels (1-5)."""
    ULTRA_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    ULTRA_HIGH = 5


class PreviewType(Enum):
    """Preview data types."""
    THUMBNAIL = "thumbnail"
    INTERACTIVE = "interactive"
    FULL_RESOLUTION = "full_resolution"
    ADAPTIVE = "adaptive"


class DeviceCapability(Enum):
    """Device performance categories."""
    LOW_END = "low_end"
    MID_RANGE = "mid_range"
    HIGH_END = "high_end"
    UNKNOWN = "unknown"


@dataclass
class PreviewRequest:
    """Preview generation request."""
    session_id: UUID
    phase_number: int
    phase_data: Dict[str, Any]
    quality_level: QualityLevel
    preview_type: PreviewType
    device_capability: DeviceCapability
    user_preferences: Dict[str, Any]
    cache_key: str
    requested_at: datetime
    priority: int = 5  # 1-10, higher is higher priority


@dataclass
class PreviewResult:
    """Preview generation result."""
    request_id: str
    preview_data: Dict[str, Any]
    quality_achieved: QualityLevel
    generation_time: float
    cache_hit: bool
    cdn_urls: Dict[str, str]
    metadata: Dict[str, Any]
    expires_at: datetime


class PreviewSystem(LoggerMixin):
    """フェーズ特化型プレビューシステム
    
    5段階品質管理・CDN最適化・デバイス適応対応。
    各フェーズ完了後のインタラクティブプレビュー生成。
    """
    
    def __init__(
        self,
        websocket_manager: WebSocketManager,
        redis_client=None,
        cdn_base_url: Optional[str] = None
    ):
        """Initialize PreviewSystem.
        
        Args:
            websocket_manager: WebSocket通信マネージャー
            redis_client: Redisクライアント
            cdn_base_url: CDNベースURL
        """
        super().__init__()
        self.settings = get_settings()
        self.websocket_manager = websocket_manager
        self.redis_client = redis_client or redis_manager
        self.cdn_base_url = cdn_base_url or self.settings.cdn_url
        
        # Preview generation queue
        self.preview_queue: asyncio.Queue = asyncio.Queue()
        self.active_generations: Dict[str, PreviewRequest] = {}
        self.generation_tasks: List[asyncio.Task] = []
        
        # Cache management
        self.cache_prefix = "preview"
        self.default_cache_ttl = 3600  # 1 hour
        self.quality_cache_ttls = {
            QualityLevel.ULTRA_LOW: 300,    # 5 minutes
            QualityLevel.LOW: 900,          # 15 minutes
            QualityLevel.MEDIUM: 1800,      # 30 minutes
            QualityLevel.HIGH: 3600,        # 1 hour
            QualityLevel.ULTRA_HIGH: 7200   # 2 hours
        }
        
        # Phase-specific generators
        self.phase_generators = {
            1: self._generate_concept_preview,
            2: self._generate_character_preview,
            3: self._generate_plot_preview,
            4: self._generate_name_preview,
            5: self._generate_image_preview,
            6: self._generate_dialogue_preview,
            7: self._generate_integration_preview
        }
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "generation_errors": 0,
            "average_generation_time": 0.0,
            "quality_distribution": {level: 0 for level in QualityLevel},
            "phase_request_counts": {i: 0 for i in range(1, 8)}
        }
        
        # Start background workers
        asyncio.create_task(self._start_workers())
    
    async def _start_workers(self):
        """Start preview generation workers."""
        await asyncio.sleep(1)  # Wait for initialization
        
        # Start multiple workers for parallel processing
        worker_count = 3
        for i in range(worker_count):
            task = asyncio.create_task(self._preview_worker(f"worker_{i}"))
            self.generation_tasks.append(task)
    
    async def generate_preview(
        self,
        session_id: UUID,
        phase_number: int,
        phase_data: Dict[str, Any],
        quality_level: Optional[QualityLevel] = None,
        preview_type: PreviewType = PreviewType.INTERACTIVE,
        device_info: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
        priority: int = 5
    ) -> PreviewResult:
        """Generate phase-specific preview.
        
        Args:
            session_id: セッションID
            phase_number: フェーズ番号 (1-7)
            phase_data: フェーズデータ
            quality_level: 品質レベル
            preview_type: プレビュータイプ
            device_info: デバイス情報
            user_preferences: ユーザー設定
            priority: 生成優先度
            
        Returns:
            PreviewResult オブジェクト
        """
        # Auto-detect quality level and device capability
        if quality_level is None:
            quality_level = self._detect_optimal_quality(device_info, phase_number)
        
        device_capability = self._detect_device_capability(device_info)
        
        # Generate cache key
        cache_key = self._generate_cache_key(
            session_id, phase_number, phase_data, quality_level, preview_type
        )
        
        # Check cache first
        cached_result = await self._get_cached_preview(cache_key)
        if cached_result:
            self.stats["cache_hits"] += 1
            return cached_result
        
        self.stats["cache_misses"] += 1
        
        # Create preview request
        request = PreviewRequest(
            session_id=session_id,
            phase_number=phase_number,
            phase_data=phase_data,
            quality_level=quality_level,
            preview_type=preview_type,
            device_capability=device_capability,
            user_preferences=user_preferences or {},
            cache_key=cache_key,
            requested_at=datetime.utcnow(),
            priority=priority
        )
        
        # Add to generation queue
        await self.preview_queue.put(request)
        
        # Wait for result (with timeout)
        request_id = cache_key
        self.active_generations[request_id] = request
        
        try:
            # Wait for generation with timeout
            timeout = 60  # 1 minute timeout
            start_time = datetime.utcnow()
            
            while request_id in self.active_generations:
                await asyncio.sleep(0.1)
                
                if (datetime.utcnow() - start_time).total_seconds() > timeout:
                    raise TimeoutError("Preview generation timed out")
            
            # Get result from cache
            result = await self._get_cached_preview(cache_key)
            if result:
                return result
            else:
                raise Exception("Preview generation failed")
                
        except Exception as e:
            self.logger.error(f"Preview generation error: {e}")
            self.stats["generation_errors"] += 1
            
            # Return fallback result
            return self._create_fallback_preview(request)
        
        finally:
            if request_id in self.active_generations:
                del self.active_generations[request_id]
    
    async def _preview_worker(self, worker_id: str):
        """Background preview generation worker.
        
        Args:
            worker_id: Worker identifier
        """
        self.logger.info(f"Preview worker {worker_id} started")
        
        while True:
            try:
                # Get next request from queue
                request = await self.preview_queue.get()
                
                # Generate preview
                await self._process_preview_request(request, worker_id)
                
                # Mark task as done
                self.preview_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)
    
    async def _process_preview_request(self, request: PreviewRequest, worker_id: str):
        """Process individual preview request.
        
        Args:
            request: Preview request
            worker_id: Worker identifier
        """
        start_time = datetime.utcnow()
        
        try:
            # Get phase-specific generator
            generator = self.phase_generators.get(request.phase_number)
            if not generator:
                raise ValueError(f"No generator for phase {request.phase_number}")
            
            # Generate preview data
            preview_data = await generator(request)
            
            # Calculate generation time
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Upload to CDN (if applicable)
            cdn_urls = await self._upload_to_cdn(preview_data, request)
            
            # Create result
            result = PreviewResult(
                request_id=request.cache_key,
                preview_data=preview_data,
                quality_achieved=request.quality_level,
                generation_time=generation_time,
                cache_hit=False,
                cdn_urls=cdn_urls,
                metadata={
                    "worker_id": worker_id,
                    "device_capability": request.device_capability.value,
                    "preview_type": request.preview_type.value,
                    "generated_at": datetime.utcnow().isoformat()
                },
                expires_at=datetime.utcnow() + timedelta(
                    seconds=self.quality_cache_ttls[request.quality_level]
                )
            )
            
            # Cache result
            await self._cache_preview_result(request.cache_key, result)
            
            # Send real-time update
            await self._send_preview_update(request.session_id, result)
            
            # Update statistics
            self.stats["total_requests"] += 1
            self.stats["quality_distribution"][request.quality_level] += 1
            self.stats["phase_request_counts"][request.phase_number] += 1
            
            # Update average generation time
            current_avg = self.stats["average_generation_time"]
            total_requests = self.stats["total_requests"]
            self.stats["average_generation_time"] = (
                (current_avg * (total_requests - 1) + generation_time) / total_requests
            )
            
            self.logger.info(
                f"Generated preview for phase {request.phase_number} "
                f"in {generation_time:.2f}s (quality: {request.quality_level})"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate preview: {e}")
            self.stats["generation_errors"] += 1
            
            # Cache error result with shorter TTL
            error_result = self._create_error_preview(request, str(e))
            await self._cache_preview_result(request.cache_key, error_result, ttl=60)
    
    def _detect_optimal_quality(
        self,
        device_info: Optional[Dict[str, Any]],
        phase_number: int
    ) -> QualityLevel:
        """Detect optimal quality level based on device and phase.
        
        Args:
            device_info: Device capability information
            phase_number: Phase number
            
        Returns:
            Optimal quality level
        """
        # Default quality mapping by phase
        phase_quality_defaults = {
            1: QualityLevel.MEDIUM,     # Concept - text heavy
            2: QualityLevel.HIGH,       # Character - visual important
            3: QualityLevel.MEDIUM,     # Plot - text heavy
            4: QualityLevel.HIGH,       # Name - layout critical
            5: QualityLevel.ULTRA_HIGH, # Image - visual critical
            6: QualityLevel.HIGH,       # Dialogue - visual important
            7: QualityLevel.ULTRA_HIGH  # Final - highest quality
        }
        
        base_quality = phase_quality_defaults.get(phase_number, QualityLevel.MEDIUM)
        
        if not device_info:
            return base_quality
        
        # Adjust based on device capability
        device_capability = self._detect_device_capability(device_info)
        
        if device_capability == DeviceCapability.LOW_END:
            # Reduce quality for low-end devices
            return min(base_quality, QualityLevel.MEDIUM)
        elif device_capability == DeviceCapability.HIGH_END:
            # Use high quality for high-end devices
            return max(base_quality, QualityLevel.HIGH)
        else:
            return base_quality
    
    def _detect_device_capability(
        self,
        device_info: Optional[Dict[str, Any]]
    ) -> DeviceCapability:
        """Detect device performance capability.
        
        Args:
            device_info: Device information
            
        Returns:
            Device capability category
        """
        if not device_info:
            return DeviceCapability.UNKNOWN
        
        # Check various device indicators
        screen_width = device_info.get("screen_width", 0)
        memory = device_info.get("memory", 0)
        connection_type = device_info.get("connection", "unknown")
        user_agent = device_info.get("user_agent", "").lower()
        
        # Low-end indicators
        if (screen_width < 768 or
            memory < 2000 or  # Less than 2GB
            "mobile" in user_agent and "android" in user_agent or
            connection_type in ["2g", "slow-2g"]):
            return DeviceCapability.LOW_END
        
        # High-end indicators
        if (screen_width >= 1920 or
            memory >= 8000 or  # 8GB or more
            "desktop" in user_agent or
            connection_type in ["wifi", "4g", "5g"]):
            return DeviceCapability.HIGH_END
        
        # Default to mid-range
        return DeviceCapability.MID_RANGE
    
    def _generate_cache_key(
        self,
        session_id: UUID,
        phase_number: int,
        phase_data: Dict[str, Any],
        quality_level: QualityLevel,
        preview_type: PreviewType
    ) -> str:
        """Generate unique cache key for preview.
        
        Args:
            session_id: Session identifier
            phase_number: Phase number
            phase_data: Phase data
            quality_level: Quality level
            preview_type: Preview type
            
        Returns:
            Cache key string
        """
        # Create hash of phase data for uniqueness
        data_str = json.dumps(phase_data, sort_keys=True)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()[:8]
        
        return f"{self.cache_prefix}:{session_id}:{phase_number}:{data_hash}:{quality_level.value}:{preview_type.value}"
    
    async def _get_cached_preview(self, cache_key: str) -> Optional[PreviewResult]:
        """Get cached preview result.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached PreviewResult or None
        """
        if not self.redis_client:
            return None
        
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                
                # Check if not expired
                expires_at = datetime.fromisoformat(data["expires_at"])
                if expires_at > datetime.utcnow():
                    return PreviewResult(**data)
        
        except Exception as e:
            self.logger.warning(f"Cache retrieval error: {e}")
        
        return None
    
    async def _cache_preview_result(
        self,
        cache_key: str,
        result: PreviewResult,
        ttl: Optional[int] = None
    ):
        """Cache preview result.
        
        Args:
            cache_key: Cache key
            result: PreviewResult to cache
            ttl: Time to live in seconds
        """
        if not self.redis_client:
            return
        
        try:
            # Convert result to dict
            result_dict = {
                "request_id": result.request_id,
                "preview_data": result.preview_data,
                "quality_achieved": result.quality_achieved.value,
                "generation_time": result.generation_time,
                "cache_hit": result.cache_hit,
                "cdn_urls": result.cdn_urls,
                "metadata": result.metadata,
                "expires_at": result.expires_at.isoformat()
            }
            
            # Use provided TTL or calculate from result
            if ttl is None:
                ttl = int((result.expires_at - datetime.utcnow()).total_seconds())
            
            await self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result_dict, default=str)
            )
            
        except Exception as e:
            self.logger.warning(f"Cache storage error: {e}")
    
    async def _upload_to_cdn(
        self,
        preview_data: Dict[str, Any],
        request: PreviewRequest
    ) -> Dict[str, str]:
        """Upload preview assets to CDN.
        
        Args:
            preview_data: Preview data containing assets
            request: Preview request
            
        Returns:
            CDN URLs mapping
        """
        cdn_urls = {}
        
        # Extract uploadable assets
        assets_to_upload = self._extract_uploadable_assets(preview_data)
        
        for asset_key, asset_data in assets_to_upload.items():
            try:
                # Generate CDN path
                cdn_path = self._generate_cdn_path(request, asset_key)
                cdn_url = f"{self.cdn_base_url}/{cdn_path}"
                
                # In a real implementation, you would upload to CDN here
                # For now, we'll just store the expected URL
                cdn_urls[asset_key] = cdn_url
                
                # Update preview data to reference CDN URL
                self._replace_asset_with_cdn_url(preview_data, asset_key, cdn_url)
                
            except Exception as e:
                self.logger.warning(f"CDN upload failed for {asset_key}: {e}")
        
        return cdn_urls
    
    def _extract_uploadable_assets(self, preview_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract assets that should be uploaded to CDN.
        
        Args:
            preview_data: Preview data
            
        Returns:
            Assets to upload
        """
        assets = {}
        
        # Look for base64 encoded images
        def find_assets(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    if isinstance(value, str) and value.startswith("data:image/"):
                        assets[current_path] = value
                    elif isinstance(value, (dict, list)):
                        find_assets(value, current_path)
                        
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_path = f"{path}[{i}]"
                    find_assets(item, current_path)
        
        find_assets(preview_data)
        return assets
    
    def _generate_cdn_path(self, request: PreviewRequest, asset_key: str) -> str:
        """Generate CDN path for asset.
        
        Args:
            request: Preview request
            asset_key: Asset key
            
        Returns:
            CDN path
        """
        timestamp = int(request.requested_at.timestamp())
        asset_hash = hashlib.md5(asset_key.encode()).hexdigest()[:8]
        
        return (
            f"previews/{request.session_id}/{request.phase_number}/"
            f"{timestamp}_{asset_hash}_{asset_key.replace('.', '_')}.webp"
        )
    
    def _replace_asset_with_cdn_url(
        self,
        preview_data: Dict[str, Any],
        asset_path: str,
        cdn_url: str
    ):
        """Replace asset data with CDN URL in preview data.
        
        Args:
            preview_data: Preview data to modify
            asset_path: Asset path (e.g., "images.thumbnail")
            cdn_url: CDN URL to use
        """
        path_parts = asset_path.split('.')
        current = preview_data
        
        # Navigate to parent
        for part in path_parts[:-1]:
            if '[' in part and ']' in part:
                # Array index
                key, index = part.split('[')
                index = int(index.rstrip(']'))
                current = current[key][index]
            else:
                current = current[part]
        
        # Set final value
        final_key = path_parts[-1]
        if '[' in final_key and ']' in final_key:
            key, index = final_key.split('[')
            index = int(index.rstrip(']'))
            current[key][index] = cdn_url
        else:
            current[final_key] = cdn_url
    
    async def _send_preview_update(self, session_id: UUID, result: PreviewResult):
        """Send real-time preview update to WebSocket clients.
        
        Args:
            session_id: Session identifier
            result: Preview result
        """
        message = {
            "type": "preview_ready",
            "session_id": str(session_id),
            "request_id": result.request_id,
            "preview_data": result.preview_data,
            "quality_achieved": result.quality_achieved.value,
            "generation_time": result.generation_time,
            "cdn_urls": result.cdn_urls,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.websocket_manager.send_to_session(session_id, message)
    
    def _create_fallback_preview(self, request: PreviewRequest) -> PreviewResult:
        """Create fallback preview when generation fails.
        
        Args:
            request: Preview request
            
        Returns:
            Fallback PreviewResult
        """
        fallback_data = {
            "type": "fallback",
            "phase_number": request.phase_number,
            "phase_name": self._get_phase_name(request.phase_number),
            "message": "プレビュー生成中にエラーが発生しました",
            "status": "error",
            "retry_available": True
        }
        
        return PreviewResult(
            request_id=request.cache_key,
            preview_data=fallback_data,
            quality_achieved=QualityLevel.ULTRA_LOW,
            generation_time=0.0,
            cache_hit=False,
            cdn_urls={},
            metadata={"fallback": True},
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )
    
    def _create_error_preview(self, request: PreviewRequest, error: str) -> PreviewResult:
        """Create error preview result.
        
        Args:
            request: Preview request
            error: Error message
            
        Returns:
            Error PreviewResult
        """
        error_data = {
            "type": "error",
            "phase_number": request.phase_number,
            "error_message": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return PreviewResult(
            request_id=request.cache_key,
            preview_data=error_data,
            quality_achieved=QualityLevel.ULTRA_LOW,
            generation_time=0.0,
            cache_hit=False,
            cdn_urls={},
            metadata={"error": True},
            expires_at=datetime.utcnow() + timedelta(minutes=1)
        )
    
    def _get_phase_name(self, phase_number: int) -> str:
        """Get phase name."""
        phase_names = {
            1: "コンセプト・世界観分析",
            2: "キャラクター設定・簡易ビジュアル生成",
            3: "プロット・ストーリー構成",
            4: "ネーム生成",
            5: "シーン画像生成",
            6: "セリフ配置",
            7: "最終統合・品質調整"
        }
        return phase_names.get(phase_number, f"フェーズ{phase_number}")
    
    # Phase-specific preview generators
    
    async def _generate_concept_preview(self, request: PreviewRequest) -> Dict[str, Any]:
        """Generate Phase 1 (Concept) preview."""
        phase_data = request.phase_data
        
        preview = {
            "type": "concept_preview",
            "phase_number": 1,
            "concept_summary": phase_data.get("concept", {}),
            "genre_analysis": phase_data.get("genre", ""),
            "theme_breakdown": phase_data.get("themes", []),
            "world_setting": phase_data.get("world_setting", {}),
            "tone_mood": phase_data.get("tone_and_mood", {}),
            "interactive_elements": {
                "genre_selector": {
                    "current": phase_data.get("genre", ""),
                    "options": ["少年漫画", "少女漫画", "青年漫画", "4コマ", "SF", "ファンタジー"]
                },
                "theme_editor": {
                    "themes": phase_data.get("themes", []),
                    "suggested_themes": ["友情", "冒険", "恋愛", "成長", "正義"]
                },
                "world_builder": {
                    "setting": phase_data.get("world_setting", {}),
                    "time_period": ["現代", "未来", "過去", "架空"],
                    "location": ["日本", "海外", "異世界", "宇宙"]
                }
            },
            "quality_level": request.quality_level.value,
            "editable_fields": ["genre", "themes", "world_setting", "tone_and_mood"]
        }
        
        return preview
    
    async def _generate_character_preview(self, request: PreviewRequest) -> Dict[str, Any]:
        """Generate Phase 2 (Character) preview."""
        phase_data = request.phase_data
        
        characters = phase_data.get("characters", [])
        
        # Generate character cards with visual elements
        character_cards = []
        for i, char in enumerate(characters):
            card = {
                "id": i,
                "name": char.get("name", f"キャラクター{i+1}"),
                "description": char.get("description", ""),
                "visual_description": char.get("visual_description", ""),
                "personality": char.get("personality", []),
                "role": char.get("role", ""),
                "relationships": char.get("relationships", {}),
                "design_notes": char.get("design_notes", ""),
                # Placeholder for generated visual
                "character_image": self._generate_character_placeholder(char, request.quality_level)
            }
            character_cards.append(card)
        
        # Generate relationship graph
        relationship_graph = self._generate_relationship_graph(characters)
        
        preview = {
            "type": "character_preview",
            "phase_number": 2,
            "character_count": len(characters),
            "character_cards": character_cards,
            "relationship_graph": relationship_graph,
            "interactive_elements": {
                "character_editor": {
                    "selected_character": 0,
                    "edit_mode": "visual",
                    "style_options": ["アニメ風", "リアル調", "デフォルメ", "ミニマル"]
                },
                "relationship_editor": {
                    "mode": "graph",
                    "editable": True
                },
                "design_gallery": {
                    "style_variations": 3,
                    "color_schemes": ["標準", "暖色系", "寒色系", "モノクロ"]
                }
            },
            "quality_level": request.quality_level.value,
            "editable_fields": ["characters", "relationships"]
        }
        
        return preview
    
    async def _generate_plot_preview(self, request: PreviewRequest) -> Dict[str, Any]:
        """Generate Phase 3 (Plot) preview."""
        phase_data = request.phase_data
        
        story_structure = phase_data.get("story_structure", {})
        scenes = phase_data.get("scenes", [])
        
        # Generate story flow diagram
        story_flow = self._generate_story_flow_diagram(story_structure, scenes)
        
        # Generate emotion curve
        emotion_curve = self._generate_emotion_curve(scenes)
        
        preview = {
            "type": "plot_preview",
            "phase_number": 3,
            "story_structure": story_structure,
            "scene_count": len(scenes),
            "story_flow_diagram": story_flow,
            "emotion_curve": emotion_curve,
            "scene_summaries": [
                {
                    "scene_id": i,
                    "title": scene.get("title", f"シーン{i+1}"),
                    "summary": scene.get("summary", ""),
                    "emotion_level": scene.get("emotion_level", 5),
                    "key_events": scene.get("key_events", [])
                }
                for i, scene in enumerate(scenes)
            ],
            "interactive_elements": {
                "scene_reorder": {
                    "draggable": True,
                    "scenes": list(range(len(scenes)))
                },
                "emotion_editor": {
                    "curve_points": len(scenes),
                    "editable": True
                },
                "structure_editor": {
                    "acts": story_structure.get("acts", []),
                    "editable": True
                }
            },
            "quality_level": request.quality_level.value,
            "editable_fields": ["story_structure", "scenes", "emotion_curve"]
        }
        
        return preview
    
    async def _generate_name_preview(self, request: PreviewRequest) -> Dict[str, Any]:
        """Generate Phase 4 (Name) preview."""
        phase_data = request.phase_data
        
        panels = phase_data.get("panels", [])
        layout = phase_data.get("layout", {})
        
        # Generate interactive panel layout
        panel_layout = self._generate_interactive_panel_layout(panels, layout, request.quality_level)
        
        preview = {
            "type": "name_preview",
            "phase_number": 4,
            "panel_count": len(panels),
            "layout_type": layout.get("type", "grid"),
            "panel_layout": panel_layout,
            "panels": [
                {
                    "panel_id": i,
                    "size": panel.get("size", "medium"),
                    "position": panel.get("position", {}),
                    "content_type": panel.get("content_type", "scene"),
                    "description": panel.get("description", ""),
                    "dialogue_count": len(panel.get("dialogues", [])),
                    "visual_elements": panel.get("visual_elements", [])
                }
                for i, panel in enumerate(panels)
            ],
            "interactive_elements": {
                "panel_editor": {
                    "resize_handles": True,
                    "drag_drop": True,
                    "layout_presets": ["1列", "2列", "3列", "見開き"]
                },
                "size_adjuster": {
                    "sizes": ["small", "medium", "large", "full"],
                    "custom_resize": True
                },
                "layout_selector": {
                    "templates": ["縦読み", "横読み", "見開き", "4コマ"],
                    "custom_grid": True
                }
            },
            "quality_level": request.quality_level.value,
            "editable_fields": ["panels", "layout"]
        }
        
        return preview
    
    async def _generate_image_preview(self, request: PreviewRequest) -> Dict[str, Any]:
        """Generate Phase 5 (Image) preview."""
        phase_data = request.phase_data
        
        generated_images = phase_data.get("images", [])
        style_params = phase_data.get("style_parameters", {})
        
        # Process images based on quality level
        image_previews = []
        for i, img_data in enumerate(generated_images):
            image_preview = await self._process_image_for_preview(img_data, request.quality_level)
            image_previews.append({
                "image_id": i,
                "preview_url": image_preview.get("preview_url", ""),
                "thumbnail_url": image_preview.get("thumbnail_url", ""),
                "style_applied": img_data.get("style", ""),
                "quality_score": img_data.get("quality_score", 0.0),
                "generation_params": img_data.get("parameters", {}),
                "variations": image_preview.get("variations", [])
            })
        
        preview = {
            "type": "image_preview",
            "phase_number": 5,
            "image_count": len(generated_images),
            "style_parameters": style_params,
            "image_previews": image_previews,
            "generation_stats": {
                "total_generated": len(generated_images),
                "successful": sum(1 for img in generated_images if img.get("status") == "success"),
                "average_quality": sum(img.get("quality_score", 0) for img in generated_images) / max(len(generated_images), 1)
            },
            "interactive_elements": {
                "image_selector": {
                    "multi_select": True,
                    "comparison_mode": True
                },
                "style_editor": {
                    "presets": ["マンガ風", "アニメ風", "リアル調", "水彩風"],
                    "custom_params": True
                },
                "quality_enhancer": {
                    "upscale_options": ["2x", "4x"],
                    "enhancement_filters": ["シャープ", "コントラスト", "彩度"]
                }
            },
            "quality_level": request.quality_level.value,
            "editable_fields": ["images", "style_parameters"]
        }
        
        return preview
    
    async def _generate_dialogue_preview(self, request: PreviewRequest) -> Dict[str, Any]:
        """Generate Phase 6 (Dialogue) preview."""
        phase_data = request.phase_data
        
        dialogue_layout = phase_data.get("dialogue_layout", {})
        speech_bubbles = phase_data.get("speech_bubbles", [])
        
        # Generate interactive dialogue editor
        dialogue_editor = self._generate_dialogue_editor_layout(dialogue_layout, speech_bubbles)
        
        preview = {
            "type": "dialogue_preview",
            "phase_number": 6,
            "bubble_count": len(speech_bubbles),
            "dialogue_editor": dialogue_editor,
            "speech_bubbles": [
                {
                    "bubble_id": i,
                    "text": bubble.get("text", ""),
                    "character": bubble.get("character", ""),
                    "style": bubble.get("style", "normal"),
                    "position": bubble.get("position", {}),
                    "size": bubble.get("size", "medium"),
                    "emotion": bubble.get("emotion", "neutral")
                }
                for i, bubble in enumerate(speech_bubbles)
            ],
            "font_styles": {
                "available_fonts": ["ゴシック", "明朝", "手書き風", "デジタル"],
                "sizes": ["小", "中", "大", "特大"],
                "effects": ["太字", "斜体", "影付き", "縁取り"]
            },
            "interactive_elements": {
                "bubble_editor": {
                    "drag_drop": True,
                    "resize_handles": True,
                    "text_editor": True
                },
                "style_selector": {
                    "bubble_shapes": ["楕円", "角丸四角", "雲形", "考え事"],
                    "line_styles": ["実線", "点線", "ギザギザ"]
                },
                "layout_assistant": {
                    "auto_arrange": True,
                    "collision_detection": True
                }
            },
            "quality_level": request.quality_level.value,
            "editable_fields": ["dialogue_layout", "speech_bubbles"]
        }
        
        return preview
    
    async def _generate_integration_preview(self, request: PreviewRequest) -> Dict[str, Any]:
        """Generate Phase 7 (Final Integration) preview."""
        phase_data = request.phase_data
        
        final_pages = phase_data.get("final_pages", [])
        export_settings = phase_data.get("export_settings", {})
        
        # Generate final manga preview
        manga_preview = await self._generate_final_manga_preview(final_pages, request.quality_level)
        
        preview = {
            "type": "integration_preview",
            "phase_number": 7,
            "page_count": len(final_pages),
            "manga_preview": manga_preview,
            "export_formats": {
                "available": ["PDF", "PNG", "JPEG", "WebP"],
                "recommended": "PDF"
            },
            "export_settings": export_settings,
            "quality_metrics": {
                "overall_score": phase_data.get("quality_score", 0.0),
                "completeness": phase_data.get("completeness", 0.0),
                "consistency": phase_data.get("consistency", 0.0)
            },
            "interactive_elements": {
                "page_navigator": {
                    "current_page": 0,
                    "total_pages": len(final_pages),
                    "thumbnail_view": True
                },
                "export_configurator": {
                    "quality_settings": ["draft", "standard", "high", "print"],
                    "size_options": ["A4", "B5", "Letter", "Custom"]
                },
                "final_editor": {
                    "page_order": True,
                    "cover_page": True,
                    "metadata": True
                }
            },
            "quality_level": request.quality_level.value,
            "editable_fields": ["final_pages", "export_settings"]
        }
        
        return preview
    
    # Helper methods
    
    def _generate_character_placeholder(self, character: Dict[str, Any], quality: QualityLevel) -> str:
        """Generate character placeholder image."""
        # In a real implementation, this would generate or fetch character images
        return f"data:image/svg+xml;base64,{self._create_character_svg_placeholder(character, quality)}"
    
    def _create_character_svg_placeholder(self, character: Dict[str, Any], quality: QualityLevel) -> str:
        """Create SVG placeholder for character."""
        name = character.get("name", "Character")
        svg = f"""
        <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
            <rect width="200" height="200" fill="#e1e1e1"/>
            <text x="100" y="100" text-anchor="middle" fill="#666" font-size="16">{name}</text>
            <text x="100" y="120" text-anchor="middle" fill="#888" font-size="12">Quality: {quality.value}</text>
        </svg>"""
        return base64.b64encode(svg.encode()).decode()
    
    def _generate_relationship_graph(self, characters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate character relationship graph data."""
        nodes = []
        edges = []
        
        for i, char in enumerate(characters):
            nodes.append({
                "id": i,
                "name": char.get("name", f"キャラクター{i+1}"),
                "role": char.get("role", ""),
                "x": 100 + (i % 3) * 150,
                "y": 100 + (i // 3) * 150
            })
            
            # Add relationships as edges
            relationships = char.get("relationships", {})
            for target_name, relationship in relationships.items():
                # Find target character index
                target_idx = None
                for j, target_char in enumerate(characters):
                    if target_char.get("name") == target_name:
                        target_idx = j
                        break
                
                if target_idx is not None:
                    edges.append({
                        "source": i,
                        "target": target_idx,
                        "relationship": relationship,
                        "label": relationship
                    })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "layout": "force",
            "interactive": True
        }
    
    def _generate_story_flow_diagram(
        self,
        structure: Dict[str, Any],
        scenes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate story flow diagram data."""
        flow_nodes = []
        
        for i, scene in enumerate(scenes):
            flow_nodes.append({
                "id": i,
                "title": scene.get("title", f"シーン{i+1}"),
                "type": scene.get("type", "scene"),
                "duration": scene.get("duration", 1),
                "importance": scene.get("importance", 5),
                "x": i * 120,
                "y": 100
            })
        
        return {
            "nodes": flow_nodes,
            "structure": structure,
            "layout": "horizontal",
            "interactive": True
        }
    
    def _generate_emotion_curve(self, scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate emotion curve data."""
        curve_points = []
        
        for i, scene in enumerate(scenes):
            curve_points.append({
                "x": i,
                "y": scene.get("emotion_level", 5),
                "scene_title": scene.get("title", f"シーン{i+1}")
            })
        
        return {
            "points": curve_points,
            "min_y": 0,
            "max_y": 10,
            "editable": True,
            "smooth": True
        }
    
    def _generate_interactive_panel_layout(
        self,
        panels: List[Dict[str, Any]],
        layout: Dict[str, Any],
        quality: QualityLevel
    ) -> Dict[str, Any]:
        """Generate interactive panel layout."""
        layout_data = {
            "type": layout.get("type", "grid"),
            "columns": layout.get("columns", 2),
            "rows": layout.get("rows", 3),
            "panels": [],
            "canvas_size": {
                "width": 800 if quality.value >= 3 else 400,
                "height": 1200 if quality.value >= 3 else 600
            }
        }
        
        for i, panel in enumerate(panels):
            panel_data = {
                "id": i,
                "x": panel.get("position", {}).get("x", (i % 2) * 400),
                "y": panel.get("position", {}).get("y", (i // 2) * 200),
                "width": panel.get("size", {}).get("width", 380),
                "height": panel.get("size", {}).get("height", 180),
                "content": panel.get("description", ""),
                "resizable": True,
                "draggable": True
            }
            layout_data["panels"].append(panel_data)
        
        return layout_data
    
    async def _process_image_for_preview(
        self,
        image_data: Dict[str, Any],
        quality: QualityLevel
    ) -> Dict[str, Any]:
        """Process image for preview display."""
        # This would normally process actual images
        # For now, return placeholder data
        
        return {
            "preview_url": f"https://via.placeholder.com/{800 if quality.value >= 3 else 400}x{600 if quality.value >= 3 else 300}",
            "thumbnail_url": f"https://via.placeholder.com/200x150",
            "variations": [
                {"style": "variation_1", "url": "https://via.placeholder.com/400x300"},
                {"style": "variation_2", "url": "https://via.placeholder.com/400x300"}
            ]
        }
    
    def _generate_dialogue_editor_layout(
        self,
        layout: Dict[str, Any],
        bubbles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate dialogue editor layout."""
        return {
            "canvas": {
                "width": 800,
                "height": 600,
                "background": "#f5f5f5"
            },
            "bubbles": [
                {
                    "id": i,
                    "x": bubble.get("position", {}).get("x", 100 + i * 150),
                    "y": bubble.get("position", {}).get("y", 100 + (i % 3) * 100),
                    "width": bubble.get("size", {}).get("width", 120),
                    "height": bubble.get("size", {}).get("height", 60),
                    "text": bubble.get("text", ""),
                    "style": bubble.get("style", "normal")
                }
                for i, bubble in enumerate(bubbles)
            ],
            "tools": {
                "add_bubble": True,
                "text_editor": True,
                "style_selector": True,
                "auto_layout": True
            }
        }
    
    async def _generate_final_manga_preview(
        self,
        pages: List[Dict[str, Any]],
        quality: QualityLevel
    ) -> Dict[str, Any]:
        """Generate final manga preview."""
        return {
            "pages": [
                {
                    "page_id": i,
                    "preview_url": f"https://via.placeholder.com/{800 if quality.value >= 4 else 400}x{1200 if quality.value >= 4 else 600}",
                    "thumbnail_url": "https://via.placeholder.com/100x150",
                    "page_number": i + 1,
                    "content_summary": page.get("summary", "")
                }
                for i, page in enumerate(pages)
            ],
            "navigation": {
                "current_page": 0,
                "total_pages": len(pages),
                "view_mode": "single"
            },
            "reader_options": {
                "zoom_levels": [0.5, 0.75, 1.0, 1.5, 2.0],
                "reading_direction": "ltr",
                "fullscreen": True
            }
        }
    
    def get_preview_stats(self) -> Dict[str, Any]:
        """Get preview system statistics."""
        cache_hit_rate = (
            self.stats["cache_hits"] / max(self.stats["cache_hits"] + self.stats["cache_misses"], 1) * 100
        )
        
        return {
            **self.stats,
            "active_generations": len(self.active_generations),
            "queue_size": self.preview_queue.qsize(),
            "cache_hit_rate": cache_hit_rate,
            "worker_count": len(self.generation_tasks),
            "quality_distribution_percentage": {
                level.name: (count / max(self.stats["total_requests"], 1) * 100)
                for level, count in self.stats["quality_distribution"].items()
            }
        }