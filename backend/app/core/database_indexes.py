"""
Database performance indexes for optimized query execution.
Critical indexes for manga generation service performance.
"""

from sqlalchemy import Index, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggerMixin


class DatabaseIndexManager(LoggerMixin):
    """Database index management for performance optimization."""
    
    def __init__(self):
        super().__init__()
        
        # Performance-critical indexes to create
        self.performance_indexes = [
            # Manga Sessions - Most frequent queries
            ("idx_manga_sessions_user_status", "manga_sessions", ["user_id", "status"]),
            ("idx_manga_sessions_created_at", "manga_sessions", ["created_at DESC"]),
            ("idx_manga_sessions_status_updated", "manga_sessions", ["status", "updated_at DESC"]),
            
            # Phase Results - Session and phase queries
            ("idx_phase_results_session_phase", "phase_results", ["session_id", "phase_number"]),
            ("idx_phase_results_status_completed", "phase_results", ["status", "completed_at DESC"]),
            ("idx_phase_results_quality_score", "phase_results", ["quality_score DESC"]),
            
            # Generated Content - Search and filtering
            ("idx_generated_content_session_phase", "generated_content", ["session_id", "phase_number"]),
            ("idx_generated_content_type_status", "generated_content", ["content_type", "status"]),
            ("idx_generated_content_created_at", "generated_content", ["created_at DESC"]),
            ("idx_generated_content_hash", "generated_content", ["content_hash"]),
            
            # User Feedback - HITL queries
            ("idx_user_feedback_session_phase", "user_feedback", ["session_id", "phase_number"]),
            ("idx_user_feedback_created_at", "user_feedback", ["created_at DESC"]),
            
            # Quality Gates - Quality assessment
            ("idx_quality_gates_session_phase", "phase_quality_gates", ["session_id", "phase_number"]),
            ("idx_quality_gates_status", "phase_quality_gates", ["status", "evaluated_at DESC"]),
            
            # Preview Versions - Preview queries
            ("idx_preview_versions_session", "preview_versions", ["session_id", "version_number DESC"]),
            ("idx_preview_versions_quality", "preview_versions", ["quality_score DESC"]),
            
            # Users - Authentication and authorization
            ("idx_users_email", "users", ["email"]),
            ("idx_users_is_active", "users", ["is_active", "last_login_at DESC"])
        ]
        
        # Composite indexes for complex queries
        self.composite_indexes = [
            # Session management complex queries
            ("idx_sessions_user_status_phase", "manga_sessions", 
             ["user_id", "status", "current_phase", "created_at DESC"]),
            
            # Content search optimization
            ("idx_content_search_optimized", "generated_content",
             ["content_type", "status", "session_id", "created_at DESC"]),
            
            # Quality assessment queries
            ("idx_quality_assessment", "phase_quality_gates",
             ["session_id", "phase_number", "status", "quality_score DESC"]),
            
            # Performance monitoring queries
            ("idx_performance_monitoring", "phase_results",
             ["processing_time_seconds DESC", "quality_score DESC", "completed_at DESC"])
        ]
    
    async def create_all_indexes(self, db: AsyncSession) -> Dict[str, Any]:
        """Create all performance indexes."""
        results = {
            "created": [],
            "skipped": [],
            "errors": []
        }
        
        all_indexes = self.performance_indexes + self.composite_indexes
        
        for index_name, table_name, columns in all_indexes:
            try:
                # Check if index already exists
                exists = await self._index_exists(db, index_name)
                if exists:
                    results["skipped"].append(index_name)
                    continue
                
                # Create index
                await self._create_index(db, index_name, table_name, columns)
                results["created"].append(index_name)
                
                self.logger.info(f"Created index: {index_name}")
                
            except Exception as e:
                error_msg = f"Failed to create index {index_name}: {str(e)}"
                results["errors"].append(error_msg)
                self.logger.error(error_msg)
        
        # Log summary
        self.logger.info(
            f"Index creation complete: {len(results['created'])} created, "
            f"{len(results['skipped'])} skipped, {len(results['errors'])} errors"
        )
        
        return results
    
    async def _index_exists(self, db: AsyncSession, index_name: str) -> bool:
        """Check if index already exists."""
        try:
            # PostgreSQL specific query
            if "postgresql" in str(db.get_bind().url):
                query = text("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_indexes 
                        WHERE indexname = :index_name
                    )
                """)
            else:
                # SQLite specific query
                query = text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND name = :index_name
                """)
            
            result = await db.execute(query, {"index_name": index_name})
            return bool(result.scalar())
            
        except Exception as e:
            self.logger.warning(f"Could not check index existence for {index_name}: {e}")
            return False
    
    async def _create_index(
        self, 
        db: AsyncSession, 
        index_name: str, 
        table_name: str, 
        columns: List[str]
    ) -> None:
        """Create a database index."""
        columns_str = ", ".join(columns)
        create_sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns_str})"
        
        await db.execute(text(create_sql))
        await db.commit()
    
    async def analyze_query_performance(self, db: AsyncSession) -> Dict[str, Any]:
        """Analyze current query performance and suggest optimizations."""
        performance_analysis = {
            "timestamp": datetime.utcnow().isoformat(),
            "database_type": str(db.get_bind().url).split("://")[0],
            "suggestions": [],
            "current_indexes": [],
            "missing_indexes": []
        }
        
        try:
            # Get current indexes
            if "postgresql" in str(db.get_bind().url):
                index_query = text("""
                    SELECT schemaname, tablename, indexname, indexdef
                    FROM pg_indexes 
                    WHERE schemaname = 'public'
                    ORDER BY tablename, indexname
                """)
                result = await db.execute(index_query)
                current_indexes = [dict(row._mapping) for row in result]
                performance_analysis["current_indexes"] = current_indexes
            
            # Analyze missing critical indexes
            existing_index_names = {idx.get("indexname", "") for idx in performance_analysis["current_indexes"]}
            
            for index_name, table, columns in self.performance_indexes + self.composite_indexes:
                if index_name not in existing_index_names:
                    performance_analysis["missing_indexes"].append({
                        "name": index_name,
                        "table": table,
                        "columns": columns,
                        "priority": "high" if "session" in table or "user" in table else "medium"
                    })
            
            # Generate optimization suggestions
            missing_high_priority = [
                idx for idx in performance_analysis["missing_indexes"] 
                if idx["priority"] == "high"
            ]
            
            if missing_high_priority:
                performance_analysis["suggestions"].append(
                    f"Create {len(missing_high_priority)} high-priority indexes for critical query paths"
                )
            
            if len(performance_analysis["missing_indexes"]) > 5:
                performance_analysis["suggestions"].append(
                    "Consider creating missing indexes to improve query performance"
                )
            
            return performance_analysis
            
        except Exception as e:
            self.logger.error(f"Query performance analysis failed: {e}")
            performance_analysis["error"] = str(e)
            return performance_analysis


# Global index manager
index_manager = DatabaseIndexManager()