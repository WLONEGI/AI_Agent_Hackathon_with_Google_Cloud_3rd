"""VersionManager - バージョン管理システム

設計書要件:
- ブランチ型データ構造・ツリー管理
- サイドバイサイド比較・オーバーレイ・差分ハイライト
- 特定バージョンへの復元・新ブランチ作成
- 品質追跡・各バージョンの品質スコア記録
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from uuid import UUID, uuid4
from enum import Enum
from dataclasses import dataclass, asdict
import json
import hashlib
from collections import defaultdict

from app.core.logging import LoggerMixin
from app.core.redis_client import redis_manager
from app.domain.manga.value_objects import QualityMetrics


class VersionType(Enum):
    """Version type enumeration."""
    CHECKPOINT = "checkpoint"      # 自動チェックポイント
    MILESTONE = "milestone"        # マイルストーン
    BRANCH = "branch"              # ブランチ作成
    MERGE = "merge"                # マージ
    ROLLBACK = "rollback"          # ロールバック
    SNAPSHOT = "snapshot"          # スナップショット


class ComparisonMode(Enum):
    """Comparison display modes."""
    SIDE_BY_SIDE = "side_by_side"
    OVERLAY = "overlay"
    DIFF_HIGHLIGHT = "diff_highlight"
    UNIFIED = "unified"


@dataclass
class VersionNode:
    """Version tree node."""
    version_id: str
    session_id: UUID
    phase_number: int
    parent_version: Optional[str]
    children_versions: List[str]
    branch_name: str
    version_type: VersionType
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    quality_score: float
    created_at: datetime
    created_by: Optional[UUID]
    description: str
    tags: List[str]
    is_active: bool


@dataclass
class VersionBranch:
    """Version branch information."""
    branch_name: str
    session_id: UUID
    head_version: str
    base_version: str
    created_at: datetime
    created_by: UUID
    description: str
    version_count: int
    last_updated: datetime


@dataclass
class DiffResult:
    """Difference comparison result."""
    version_a: str
    version_b: str
    added_fields: Dict[str, Any]
    removed_fields: Dict[str, Any]
    modified_fields: Dict[str, Tuple[Any, Any]]
    unchanged_fields: Dict[str, Any]
    similarity_score: float
    comparison_metadata: Dict[str, Any]


class VersionManager(LoggerMixin):
    """バージョン管理システム
    
    ブランチ型データ構造による版数管理・比較・復元機能。
    品質追跡・差分表示・サイドバイサイド比較対応。
    """
    
    def __init__(self, redis_client=None):
        """Initialize VersionManager.
        
        Args:
            redis_client: Redisクライアント
        """
        super().__init__()
        self.redis_client = redis_client or redis_manager
        
        # Version storage
        self.version_cache: Dict[str, VersionNode] = {}
        self.branch_cache: Dict[str, VersionBranch] = {}
        self.session_versions: Dict[UUID, Dict[str, str]] = defaultdict(dict)  # session_id -> {branch_name: head_version}
        
        # Cache prefixes
        self.version_prefix = "version"
        self.branch_prefix = "branch"
        
        # Configuration
        self.max_versions_per_session = 100
        self.max_branches_per_session = 10
        self.cleanup_threshold_days = 30
        
        # Statistics
        self.stats = {
            "total_versions": 0,
            "total_branches": 0,
            "total_checkpoints": 0,
            "total_comparisons": 0,
            "total_rollbacks": 0,
            "quality_improvements": 0,
            "active_sessions": 0,
            "version_size_distribution": defaultdict(int),
            "branch_usage": defaultdict(int)
        }
    
    async def create_checkpoint(
        self,
        session_id: UUID,
        phase_number: int,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        branch_name: str = "main",
        description: str = "",
        user_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """Create version checkpoint.
        
        Args:
            session_id: セッションID
            phase_number: フェーズ番号
            data: バージョンデータ
            metadata: メタデータ
            branch_name: ブランチ名
            description: バージョン説明
            user_id: 作成者ID
            tags: タグリスト
            
        Returns:
            バージョンID
        """
        try:
            # Generate version ID
            version_id = self._generate_version_id(session_id, phase_number)
            
            # Get parent version
            parent_version = self._get_current_head(session_id, branch_name)
            
            # Calculate quality score (if available)
            quality_score = self._extract_quality_score(data, metadata)
            
            # Create version node
            version_node = VersionNode(
                version_id=version_id,
                session_id=session_id,
                phase_number=phase_number,
                parent_version=parent_version,
                children_versions=[],
                branch_name=branch_name,
                version_type=VersionType.CHECKPOINT,
                data=data,
                metadata=metadata or {},
                quality_score=quality_score,
                created_at=datetime.utcnow(),
                created_by=user_id,
                description=description or f"Phase {phase_number} checkpoint",
                tags=tags or [],
                is_active=True
            )
            
            # Update parent's children
            if parent_version:
                await self._add_child_version(parent_version, version_id)
            
            # Store version
            await self._store_version(version_node)
            
            # Update branch head
            await self._update_branch_head(session_id, branch_name, version_id)
            
            # Update statistics
            self.stats["total_versions"] += 1
            self.stats["total_checkpoints"] += 1
            self._update_version_size_stats(data)
            
            self.logger.info(
                f"Created checkpoint {version_id} for session {session_id}, "
                f"phase {phase_number}, branch {branch_name}"
            )
            
            return version_id
            
        except Exception as e:
            self.logger.error(f"Failed to create checkpoint: {e}")
            raise
    
    async def create_branch(
        self,
        session_id: UUID,
        branch_name: str,
        base_version: str,
        description: str = "",
        user_id: Optional[UUID] = None
    ) -> str:
        """Create new branch from base version.
        
        Args:
            session_id: セッションID
            branch_name: 新しいブランチ名
            base_version: ベースバージョン
            description: ブランチ説明
            user_id: 作成者ID
            
        Returns:
            ブランチ名
        """
        try:
            # Validate base version exists
            base_node = await self._get_version(base_version)
            if not base_node:
                raise ValueError(f"Base version {base_version} not found")
            
            # Check branch limit
            session_branches = await self._get_session_branches(session_id)
            if len(session_branches) >= self.max_branches_per_session:
                raise ValueError(f"Maximum branches per session exceeded: {self.max_branches_per_session}")
            
            # Check branch name uniqueness
            if branch_name in session_branches:
                raise ValueError(f"Branch {branch_name} already exists")
            
            # Create branch
            branch = VersionBranch(
                branch_name=branch_name,
                session_id=session_id,
                head_version=base_version,
                base_version=base_version,
                created_at=datetime.utcnow(),
                created_by=user_id or UUID('00000000-0000-0000-0000-000000000000'),
                description=description,
                version_count=1,
                last_updated=datetime.utcnow()
            )
            
            # Store branch
            await self._store_branch(branch)
            
            # Update session branches
            self.session_versions[session_id][branch_name] = base_version
            
            # Update statistics
            self.stats["total_branches"] += 1
            self.stats["branch_usage"][branch_name] += 1
            
            self.logger.info(
                f"Created branch {branch_name} for session {session_id} from {base_version}"
            )
            
            return branch_name
            
        except Exception as e:
            self.logger.error(f"Failed to create branch: {e}")
            raise
    
    async def restore_version(
        self,
        session_id: UUID,
        version_id: str,
        target_branch: str = "main",
        create_rollback_checkpoint: bool = True
    ) -> bool:
        """Restore to specific version.
        
        Args:
            session_id: セッションID
            version_id: 復元するバージョンID
            target_branch: ターゲットブランチ
            create_rollback_checkpoint: ロールバックチェックポイント作成
            
        Returns:
            成功フラグ
        """
        try:
            # Validate version exists
            version_node = await self._get_version(version_id)
            if not version_node:
                raise ValueError(f"Version {version_id} not found")
            
            if version_node.session_id != session_id:
                raise ValueError("Version does not belong to session")
            
            # Create rollback checkpoint if requested
            if create_rollback_checkpoint:
                current_head = self._get_current_head(session_id, target_branch)
                if current_head:
                    current_node = await self._get_version(current_head)
                    if current_node:
                        rollback_id = await self.create_checkpoint(
                            session_id=session_id,
                            phase_number=current_node.phase_number,
                            data=current_node.data,
                            metadata={
                                **current_node.metadata,
                                "rollback_point": True,
                                "restored_from": version_id
                            },
                            branch_name=f"{target_branch}_rollback_{int(datetime.utcnow().timestamp())}",
                            description=f"Rollback point before restoring to {version_id}",
                            tags=["rollback", "auto"]
                        )
                        
                        self.logger.info(f"Created rollback checkpoint: {rollback_id}")
            
            # Update branch head to restored version
            await self._update_branch_head(session_id, target_branch, version_id)
            
            # Mark version as active
            version_node.is_active = True
            await self._store_version(version_node)
            
            # Update statistics
            self.stats["total_rollbacks"] += 1
            
            self.logger.info(
                f"Restored session {session_id} to version {version_id} on branch {target_branch}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore version: {e}")
            return False
    
    async def compare_versions(
        self,
        version_a: str,
        version_b: str,
        comparison_mode: ComparisonMode = ComparisonMode.SIDE_BY_SIDE,
        include_metadata: bool = False
    ) -> DiffResult:
        """Compare two versions.
        
        Args:
            version_a: 比較元バージョン
            version_b: 比較先バージョン
            comparison_mode: 比較モード
            include_metadata: メタデータ比較含む
            
        Returns:
            比較結果
        """
        try:
            # Get version nodes
            node_a = await self._get_version(version_a)
            node_b = await self._get_version(version_b)
            
            if not node_a or not node_b:
                raise ValueError("One or both versions not found")
            
            # Extract comparison data
            data_a = node_a.data
            data_b = node_b.data
            
            if include_metadata:
                data_a = {**data_a, "_metadata": node_a.metadata}
                data_b = {**data_b, "_metadata": node_b.metadata}
            
            # Perform deep comparison
            diff_result = self._deep_compare(data_a, data_b)
            
            # Calculate similarity score
            similarity = self._calculate_similarity(diff_result)
            
            # Create result
            result = DiffResult(
                version_a=version_a,
                version_b=version_b,
                added_fields=diff_result["added"],
                removed_fields=diff_result["removed"],
                modified_fields=diff_result["modified"],
                unchanged_fields=diff_result["unchanged"],
                similarity_score=similarity,
                comparison_metadata={
                    "comparison_mode": comparison_mode.value,
                    "version_a_info": {
                        "created_at": node_a.created_at.isoformat(),
                        "phase_number": node_a.phase_number,
                        "quality_score": node_a.quality_score,
                        "branch": node_a.branch_name
                    },
                    "version_b_info": {
                        "created_at": node_b.created_at.isoformat(),
                        "phase_number": node_b.phase_number,
                        "quality_score": node_b.quality_score,
                        "branch": node_b.branch_name
                    },
                    "quality_delta": node_b.quality_score - node_a.quality_score,
                    "compared_at": datetime.utcnow().isoformat()
                }
            )
            
            # Update statistics
            self.stats["total_comparisons"] += 1
            
            if node_b.quality_score > node_a.quality_score:
                self.stats["quality_improvements"] += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Version comparison failed: {e}")
            raise
    
    async def get_version_tree(
        self,
        session_id: UUID,
        branch_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get version tree structure.
        
        Args:
            session_id: セッションID
            branch_name: ブランチ名（指定時はそのブランチのみ）
            
        Returns:
            バージョンツリー構造
        """
        try:
            session_branches = await self._get_session_branches(session_id)
            
            if branch_name and branch_name not in session_branches:
                raise ValueError(f"Branch {branch_name} not found")
            
            branches_to_include = [branch_name] if branch_name else list(session_branches.keys())
            
            tree_structure = {
                "session_id": str(session_id),
                "branches": {},
                "total_versions": 0,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            for branch in branches_to_include:
                branch_data = session_branches[branch]
                branch_versions = await self._get_branch_versions(session_id, branch)
                
                # Build version hierarchy
                version_nodes = []
                for version_id in branch_versions:
                    node = await self._get_version(version_id)
                    if node:
                        version_nodes.append({
                            "version_id": version_id,
                            "phase_number": node.phase_number,
                            "parent_version": node.parent_version,
                            "children_versions": node.children_versions,
                            "version_type": node.version_type.value,
                            "quality_score": node.quality_score,
                            "created_at": node.created_at.isoformat(),
                            "description": node.description,
                            "tags": node.tags,
                            "is_active": node.is_active,
                            "data_size": len(json.dumps(node.data))
                        })
                
                tree_structure["branches"][branch] = {
                    "branch_info": asdict(branch_data),
                    "versions": version_nodes,
                    "version_count": len(version_nodes)
                }
                
                tree_structure["total_versions"] += len(version_nodes)
            
            return tree_structure
            
        except Exception as e:
            self.logger.error(f"Failed to get version tree: {e}")
            raise
    
    async def get_version_data(
        self,
        version_id: str,
        include_metadata: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get version data.
        
        Args:
            version_id: バージョンID
            include_metadata: メタデータ含む
            
        Returns:
            バージョンデータ
        """
        node = await self._get_version(version_id)
        if not node:
            return None
        
        result = {
            "version_id": version_id,
            "data": node.data
        }
        
        if include_metadata:
            result.update({
                "session_id": str(node.session_id),
                "phase_number": node.phase_number,
                "branch_name": node.branch_name,
                "version_type": node.version_type.value,
                "quality_score": node.quality_score,
                "created_at": node.created_at.isoformat(),
                "created_by": str(node.created_by) if node.created_by else None,
                "description": node.description,
                "tags": node.tags,
                "parent_version": node.parent_version,
                "children_versions": node.children_versions,
                "metadata": node.metadata
            })
        
        return result
    
    async def cleanup_old_versions(
        self,
        session_id: Optional[UUID] = None,
        days_old: int = 30,
        keep_milestones: bool = True
    ) -> Dict[str, int]:
        """Clean up old versions.
        
        Args:
            session_id: セッションID（指定時はそのセッションのみ）
            days_old: 削除対象の日数
            keep_milestones: マイルストーン保持
            
        Returns:
            削除統計
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        cleanup_stats = {
            "versions_deleted": 0,
            "branches_deleted": 0,
            "space_freed": 0
        }
        
        try:
            # Get candidates for cleanup
            sessions_to_clean = [session_id] if session_id else list(self.session_versions.keys())
            
            for sess_id in sessions_to_clean:
                session_branches = await self._get_session_branches(sess_id)
                
                for branch_name, branch_data in session_branches.items():
                    if branch_data.last_updated < cutoff_date:
                        branch_versions = await self._get_branch_versions(sess_id, branch_name)
                        
                        versions_to_delete = []
                        for version_id in branch_versions:
                            node = await self._get_version(version_id)
                            if node and node.created_at < cutoff_date:
                                # Keep milestones if requested
                                if keep_milestones and node.version_type == VersionType.MILESTONE:
                                    continue
                                # Keep active versions
                                if node.is_active:
                                    continue
                                
                                versions_to_delete.append(version_id)
                        
                        # Delete versions
                        for version_id in versions_to_delete:
                            await self._delete_version(version_id)
                            cleanup_stats["versions_deleted"] += 1
                        
                        # Delete branch if empty
                        remaining_versions = await self._get_branch_versions(sess_id, branch_name)
                        if not remaining_versions:
                            await self._delete_branch(sess_id, branch_name)
                            cleanup_stats["branches_deleted"] += 1
            
            self.logger.info(f"Cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            return cleanup_stats
    
    # Private helper methods
    
    def _generate_version_id(self, session_id: UUID, phase_number: int) -> str:
        """Generate unique version ID."""
        timestamp = int(datetime.utcnow().timestamp())
        session_short = str(session_id)[:8]
        return f"v_{session_short}_{phase_number}_{timestamp}"
    
    def _get_current_head(self, session_id: UUID, branch_name: str) -> Optional[str]:
        """Get current head version of branch."""
        return self.session_versions.get(session_id, {}).get(branch_name)
    
    def _extract_quality_score(self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]]) -> float:
        """Extract quality score from data or metadata."""
        if metadata and "quality_score" in metadata:
            return float(metadata["quality_score"])
        
        if "quality_score" in data:
            return float(data["quality_score"])
        
        # Default quality score
        return 0.7
    
    async def _store_version(self, version_node: VersionNode):
        """Store version node."""
        self.version_cache[version_node.version_id] = version_node
        
        if self.redis_client:
            cache_key = f"{self.version_prefix}:{version_node.version_id}"
            version_data = asdict(version_node)
            version_data["created_at"] = version_node.created_at.isoformat()
            
            await self.redis_client.setex(
                cache_key,
                86400 * 7,  # 7 days TTL
                json.dumps(version_data, default=str)
            )
    
    async def _store_branch(self, branch: VersionBranch):
        """Store branch information."""
        branch_key = f"{branch.session_id}_{branch.branch_name}"
        self.branch_cache[branch_key] = branch
        
        if self.redis_client:
            cache_key = f"{self.branch_prefix}:{branch_key}"
            branch_data = asdict(branch)
            branch_data["created_at"] = branch.created_at.isoformat()
            branch_data["last_updated"] = branch.last_updated.isoformat()
            
            await self.redis_client.setex(
                cache_key,
                86400 * 30,  # 30 days TTL
                json.dumps(branch_data, default=str)
            )
    
    async def _get_version(self, version_id: str) -> Optional[VersionNode]:
        """Get version node by ID."""
        # Check cache first
        if version_id in self.version_cache:
            return self.version_cache[version_id]
        
        # Try Redis
        if self.redis_client:
            cache_key = f"{self.version_prefix}:{version_id}"
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                data["created_at"] = datetime.fromisoformat(data["created_at"])
                data["version_type"] = VersionType(data["version_type"])
                data["session_id"] = UUID(data["session_id"])
                if data["created_by"]:
                    data["created_by"] = UUID(data["created_by"])
                
                version_node = VersionNode(**data)
                self.version_cache[version_id] = version_node
                return version_node
        
        return None
    
    async def _add_child_version(self, parent_version_id: str, child_version_id: str):
        """Add child version to parent."""
        parent_node = await self._get_version(parent_version_id)
        if parent_node:
            parent_node.children_versions.append(child_version_id)
            await self._store_version(parent_node)
    
    async def _update_branch_head(self, session_id: UUID, branch_name: str, version_id: str):
        """Update branch head version."""
        self.session_versions[session_id][branch_name] = version_id
        
        # Update branch metadata
        branch_key = f"{session_id}_{branch_name}"
        if branch_key in self.branch_cache:
            branch = self.branch_cache[branch_key]
            branch.head_version = version_id
            branch.last_updated = datetime.utcnow()
            branch.version_count += 1
            await self._store_branch(branch)
    
    async def _get_session_branches(self, session_id: UUID) -> Dict[str, VersionBranch]:
        """Get all branches for session."""
        branches = {}
        
        for branch_key, branch in self.branch_cache.items():
            if branch_key.startswith(str(session_id)):
                branches[branch.branch_name] = branch
        
        # If no cached branches, create default main branch
        if not branches:
            main_branch = VersionBranch(
                branch_name="main",
                session_id=session_id,
                head_version="",
                base_version="",
                created_at=datetime.utcnow(),
                created_by=UUID('00000000-0000-0000-0000-000000000000'),
                description="Default main branch",
                version_count=0,
                last_updated=datetime.utcnow()
            )
            await self._store_branch(main_branch)
            branches["main"] = main_branch
        
        return branches
    
    async def _get_branch_versions(self, session_id: UUID, branch_name: str) -> List[str]:
        """Get all version IDs for branch."""
        versions = []
        
        # Start from current head and traverse backwards
        current_head = self._get_current_head(session_id, branch_name)
        if not current_head:
            return versions
        
        visited = set()
        to_visit = [current_head]
        
        while to_visit:
            version_id = to_visit.pop()
            if version_id in visited:
                continue
            
            visited.add(version_id)
            node = await self._get_version(version_id)
            
            if node and node.branch_name == branch_name:
                versions.append(version_id)
                
                # Add parent to visit list
                if node.parent_version:
                    to_visit.append(node.parent_version)
                
                # Add children to visit list
                to_visit.extend(node.children_versions)
        
        # Sort by creation time (most recent first)
        version_nodes = []
        for version_id in versions:
            node = await self._get_version(version_id)
            if node:
                version_nodes.append((node.created_at, version_id))
        
        version_nodes.sort(reverse=True)
        return [version_id for _, version_id in version_nodes]
    
    async def _delete_version(self, version_id: str):
        """Delete version."""
        # Remove from cache
        if version_id in self.version_cache:
            del self.version_cache[version_id]
        
        # Remove from Redis
        if self.redis_client:
            cache_key = f"{self.version_prefix}:{version_id}"
            await self.redis_client.delete(cache_key)
    
    async def _delete_branch(self, session_id: UUID, branch_name: str):
        """Delete branch."""
        branch_key = f"{session_id}_{branch_name}"
        
        # Remove from cache
        if branch_key in self.branch_cache:
            del self.branch_cache[branch_key]
        
        # Remove from session versions
        if session_id in self.session_versions and branch_name in self.session_versions[session_id]:
            del self.session_versions[session_id][branch_name]
        
        # Remove from Redis
        if self.redis_client:
            cache_key = f"{self.branch_prefix}:{branch_key}"
            await self.redis_client.delete(cache_key)
    
    def _deep_compare(self, data_a: Dict[str, Any], data_b: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Perform deep comparison between two data structures."""
        result = {
            "added": {},      # Fields in B but not in A
            "removed": {},    # Fields in A but not in B
            "modified": {},   # Fields in both but with different values
            "unchanged": {}   # Fields with same values
        }
        
        # Get all keys
        keys_a = set(self._flatten_dict(data_a).keys())
        keys_b = set(self._flatten_dict(data_b).keys())
        
        flat_a = self._flatten_dict(data_a)
        flat_b = self._flatten_dict(data_b)
        
        # Added fields
        for key in keys_b - keys_a:
            result["added"][key] = flat_b[key]
        
        # Removed fields
        for key in keys_a - keys_b:
            result["removed"][key] = flat_a[key]
        
        # Common fields
        for key in keys_a & keys_b:
            if flat_a[key] != flat_b[key]:
                result["modified"][key] = (flat_a[key], flat_b[key])
            else:
                result["unchanged"][key] = flat_a[key]
        
        return result
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(self._flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
                    else:
                        items.append((f"{new_key}[{i}]", item))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _calculate_similarity(self, diff_result: Dict[str, Dict[str, Any]]) -> float:
        """Calculate similarity score between two versions."""
        total_fields = (
            len(diff_result["added"]) +
            len(diff_result["removed"]) +
            len(diff_result["modified"]) +
            len(diff_result["unchanged"])
        )
        
        if total_fields == 0:
            return 1.0
        
        # Unchanged fields contribute 100% to similarity
        # Modified fields contribute 50% to similarity
        # Added/removed fields contribute 0% to similarity
        
        similarity_score = (
            len(diff_result["unchanged"]) +
            len(diff_result["modified"]) * 0.5
        ) / total_fields
        
        return similarity_score
    
    def _update_version_size_stats(self, data: Dict[str, Any]):
        """Update version size statistics."""
        data_size = len(json.dumps(data))
        
        if data_size < 1024:  # < 1KB
            self.stats["version_size_distribution"]["small"] += 1
        elif data_size < 10240:  # < 10KB
            self.stats["version_size_distribution"]["medium"] += 1
        elif data_size < 102400:  # < 100KB
            self.stats["version_size_distribution"]["large"] += 1
        else:
            self.stats["version_size_distribution"]["extra_large"] += 1
    
    def get_version_stats(self) -> Dict[str, Any]:
        """Get version management statistics."""
        self.stats["active_sessions"] = len(self.session_versions)
        
        return {
            **self.stats,
            "cache_sizes": {
                "versions": len(self.version_cache),
                "branches": len(self.branch_cache)
            },
            "average_versions_per_session": (
                self.stats["total_versions"] / max(self.stats["active_sessions"], 1)
            ),
            "average_branches_per_session": (
                self.stats["total_branches"] / max(self.stats["active_sessions"], 1)
            )
        }