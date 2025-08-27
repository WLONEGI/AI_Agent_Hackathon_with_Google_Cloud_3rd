"""Content management domain service."""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import hashlib
import json

from app.domain.manga.entities.generated_content import (
    GeneratedContent, ContentId, ContentType, ContentStatus, ContentFormat
)
from app.domain.manga.entities.session import MangaSession, SessionId
from app.domain.manga.value_objects.quality_metrics import QualityScore
from app.domain.manga.repositories.generated_content_repository import GeneratedContentRepository
from app.domain.manga.repositories.session_repository import SessionRepository


class ContentManagementService:
    """Domain service for content management and lifecycle."""
    
    def __init__(
        self,
        content_repository: GeneratedContentRepository,
        session_repository: SessionRepository
    ):
        self.content_repository = content_repository
        self.session_repository = session_repository
    
    async def create_content(
        self,
        session_id: str,
        phase_number: int,
        content_type: ContentType,
        content_data: Union[str, Dict[str, Any]],
        title: Optional[str] = None,
        description: Optional[str] = None,
        content_format: ContentFormat = ContentFormat.JSON,
        metadata: Optional[Dict[str, Any]] = None
    ) -> GeneratedContent:
        """Create new generated content."""
        # Generate content hash for deduplication
        content_hash = self._generate_content_hash(content_data)
        
        # Check for duplicates
        existing_content = await self.content_repository.find_by_hash(content_hash)
        if existing_content:
            # Return reference to existing content instead of creating duplicate
            for content in existing_content:
                if (content.session_id == session_id and 
                    content.phase_number == phase_number and 
                    content.content_type == content_type):
                    return content
        
        # Create new content
        content = GeneratedContent(
            session_id=session_id,
            phase_number=phase_number,
            content_type=content_type,
            content_format=content_format,
            title=title,
            description=description,
            content_data=content_data,
            content_hash=content_hash,
            metadata=metadata or {}
        )
        
        # Save content
        await self.content_repository.save(content)
        
        return content
    
    async def generate_and_save_content(
        self,
        session_id: str,
        phase_number: int,
        content_type: ContentType,
        content_data: Union[str, Dict[str, Any]],
        generated_by: str,
        generation_time: float,
        generation_params: Optional[Dict[str, Any]] = None,
        quality_score: Optional[QualityScore] = None
    ) -> GeneratedContent:
        """Generate and save content with generation metadata."""
        # Create content
        content = await self.create_content(
            session_id=session_id,
            phase_number=phase_number,
            content_type=content_type,
            content_data=content_data
        )
        
        # Mark as generated
        content.generate_content(
            content_data=content_data,
            generated_by=generated_by,
            generation_time=generation_time,
            generation_params=generation_params
        )
        
        # Update quality score if provided
        if quality_score:
            content.update_quality_score(quality_score)
        
        # Save updated content
        await self.content_repository.save(content)
        
        return content
    
    async def submit_content_for_review(self, content_id: ContentId) -> GeneratedContent:
        """Submit content for human review."""
        content = await self.content_repository.find_by_id(content_id)
        if not content:
            raise ValueError(f"Content not found: {content_id}")
        
        content.submit_for_review()
        await self.content_repository.save(content)
        
        return content
    
    async def approve_content(
        self,
        content_id: ContentId,
        approval_score: float,
        feedback: Optional[Dict[str, Any]] = None
    ) -> GeneratedContent:
        """Approve content with feedback."""
        content = await self.content_repository.find_by_id(content_id)
        if not content:
            raise ValueError(f"Content not found: {content_id}")
        
        content.approve_content(approval_score, feedback)
        await self.content_repository.save(content)
        
        return content
    
    async def reject_content(
        self,
        content_id: ContentId,
        reason: str,
        feedback: Optional[Dict[str, Any]] = None
    ) -> GeneratedContent:
        """Reject content with reason and feedback."""
        content = await self.content_repository.find_by_id(content_id)
        if not content:
            raise ValueError(f"Content not found: {content_id}")
        
        content.reject_content(reason, feedback)
        await self.content_repository.save(content)
        
        return content
    
    async def revise_content(
        self,
        content_id: ContentId,
        new_content_data: Union[str, Dict[str, Any]],
        revision_reason: str,
        generated_by: str
    ) -> GeneratedContent:
        """Create revised version of content."""
        content = await self.content_repository.find_by_id(content_id)
        if not content:
            raise ValueError(f"Content not found: {content_id}")
        
        content.revise_content(new_content_data, revision_reason, generated_by)
        await self.content_repository.save(content)
        
        return content
    
    async def finalize_content(self, content_id: ContentId) -> GeneratedContent:
        """Finalize approved content."""
        content = await self.content_repository.find_by_id(content_id)
        if not content:
            raise ValueError(f"Content not found: {content_id}")
        
        content.finalize_content()
        await self.content_repository.save(content)
        
        return content
    
    async def create_content_relationship(
        self,
        content_id: ContentId,
        related_content_id: ContentId,
        relationship_type: str
    ) -> None:
        """Create relationship between content items."""
        content = await self.content_repository.find_by_id(content_id)
        if not content:
            raise ValueError(f"Content not found: {content_id}")
        
        # Verify related content exists
        related_content = await self.content_repository.find_by_id(related_content_id)
        if not related_content:
            raise ValueError(f"Related content not found: {related_content_id}")
        
        content.add_relationship(related_content_id, relationship_type)
        await self.content_repository.save(content)
    
    async def add_content_dependency(
        self,
        content_id: ContentId,
        dependency_id: ContentId
    ) -> None:
        """Add content dependency."""
        content = await self.content_repository.find_by_id(content_id)
        if not content:
            raise ValueError(f"Content not found: {content_id}")
        
        # Verify dependency exists
        dependency = await self.content_repository.find_by_id(dependency_id)
        if not dependency:
            raise ValueError(f"Dependency content not found: {dependency_id}")
        
        content.add_dependency(dependency_id)
        await self.content_repository.save(content)
    
    async def bulk_approve_session_content(
        self,
        session_id: str,
        approval_score: float,
        content_types: Optional[List[ContentType]] = None
    ) -> List[GeneratedContent]:
        """Bulk approve content for a session."""
        # Get session content
        all_content = await self.content_repository.find_by_session_id(session_id)
        
        # Filter by content types if specified
        if content_types:
            content_to_approve = [c for c in all_content if c.content_type in content_types]
        else:
            content_to_approve = all_content
        
        # Filter to only reviewable content
        reviewable_content = [
            c for c in content_to_approve 
            if c.status in [ContentStatus.GENERATED, ContentStatus.REVIEWED]
        ]
        
        # Approve content
        approved_content = []
        for content in reviewable_content:
            try:
                content.approve_content(approval_score)
                await self.content_repository.save(content)
                approved_content.append(content)
            except Exception as e:
                # Log error but continue with other content
                continue
        
        return approved_content
    
    async def get_session_content_summary(self, session_id: str) -> Dict[str, Any]:
        """Get content summary for a session."""
        content_items = await self.content_repository.find_by_session_id(session_id)
        
        # Group by phase and type
        by_phase = {}
        by_type = {}
        by_status = {}
        
        total_size = 0
        total_cost = 0
        
        for content in content_items:
            # By phase
            phase = content.phase_number
            if phase not in by_phase:
                by_phase[phase] = []
            by_phase[phase].append(content)
            
            # By type
            content_type = content.content_type.value
            if content_type not in by_type:
                by_type[content_type] = 0
            by_type[content_type] += 1
            
            # By status
            status = content.status.value
            if status not in by_status:
                by_status[status] = 0
            by_status[status] += 1
            
            # Totals
            total_size += content.content_size_bytes
            total_cost += content.calculate_total_cost()
        
        return {
            "total_items": len(content_items),
            "by_phase": {
                phase: {
                    "count": len(items),
                    "types": list(set(item.content_type.value for item in items)),
                    "statuses": list(set(item.status.value for item in items))
                }
                for phase, items in by_phase.items()
            },
            "by_type": by_type,
            "by_status": by_status,
            "storage": {
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            },
            "cost": {
                "total_usd": round(total_cost, 4)
            },
            "quality": {
                "average_score": self._calculate_average_quality_score(content_items),
                "high_quality_count": len([
                    c for c in content_items 
                    if c.quality_score and c.quality_score.overall_score >= 0.8
                ]),
                "low_quality_count": len([
                    c for c in content_items 
                    if c.quality_score and c.quality_score.overall_score < 0.6
                ])
            }
        }
    
    async def cleanup_old_content(
        self,
        days_old: int = 90,
        exclude_finalized: bool = True
    ) -> Dict[str, int]:
        """Clean up old content."""
        # Find content candidates for cleanup
        content_ids = await self.content_repository.find_content_needing_cleanup(days_old)
        
        archived_count = 0
        deleted_count = 0
        
        for content_id in content_ids:
            content = await self.content_repository.find_by_id(content_id)
            if not content:
                continue
            
            # Skip finalized content if requested
            if exclude_finalized and content.status == ContentStatus.FINALIZED:
                continue
            
            try:
                if content.status in [ContentStatus.DRAFT, ContentStatus.REJECTED]:
                    # Delete draft and rejected content
                    await self.content_repository.delete(content_id)
                    deleted_count += 1
                else:
                    # Archive other content
                    content.archive_content("Automated cleanup")
                    await self.content_repository.save(content)
                    archived_count += 1
            except Exception as e:
                # Log error but continue with other content
                continue
        
        return {
            "archived_count": archived_count,
            "deleted_count": deleted_count,
            "total_processed": archived_count + deleted_count
        }
    
    async def find_duplicate_content(
        self,
        session_id: Optional[str] = None
    ) -> List[List[GeneratedContent]]:
        """Find duplicate content groups."""
        if session_id:
            all_content = await self.content_repository.find_by_session_id(session_id)
        else:
            all_content = await self.content_repository.find_duplicate_content()
        
        # Group by content hash
        hash_groups = {}
        for content in all_content:
            if content.content_hash:
                if content.content_hash not in hash_groups:
                    hash_groups[content.content_hash] = []
                hash_groups[content.content_hash].append(content)
        
        # Return groups with more than one item
        duplicate_groups = [
            group for group in hash_groups.values() if len(group) > 1
        ]
        
        return duplicate_groups
    
    async def optimize_content_storage(self, session_id: str) -> Dict[str, Any]:
        """Optimize content storage for a session."""
        # Find duplicates
        duplicate_groups = await self.find_duplicate_content(session_id)
        
        deduplicated_count = 0
        space_saved = 0
        
        for group in duplicate_groups:
            if len(group) <= 1:
                continue
            
            # Keep the highest quality version
            best_content = max(
                group, 
                key=lambda c: c.quality_score.overall_score if c.quality_score else 0.0
            )
            
            # Archive duplicates
            for content in group:
                if content.id != best_content.id:
                    space_saved += content.content_size_bytes
                    content.archive_content("Duplicate content optimization")
                    await self.content_repository.save(content)
                    deduplicated_count += 1
        
        return {
            "deduplicated_count": deduplicated_count,
            "space_saved_bytes": space_saved,
            "space_saved_mb": round(space_saved / (1024 * 1024), 2),
            "duplicate_groups_processed": len(duplicate_groups)
        }
    
    def _generate_content_hash(self, content_data: Union[str, Dict[str, Any]]) -> str:
        """Generate hash for content data."""
        if isinstance(content_data, str):
            data_str = content_data
        else:
            data_str = json.dumps(content_data, sort_keys=True)
        
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()
    
    def _calculate_average_quality_score(self, content_items: List[GeneratedContent]) -> float:
        """Calculate average quality score for content items."""
        scored_items = [c for c in content_items if c.quality_score]
        
        if not scored_items:
            return 0.0
        
        total_score = sum(c.quality_score.overall_score for c in scored_items)
        return round(total_score / len(scored_items), 3)