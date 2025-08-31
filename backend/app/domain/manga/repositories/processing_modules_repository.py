"""Processing module repository interface for domain layer."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from ...common.entities import ProcessingModuleEntity


class ProcessingModulesRepository(ABC):
    """Abstract repository interface for processing module operations.
    
    This interface defines the contract for processing module data persistence
    operations including execution management and performance tracking.
    """
    
    @abstractmethod
    async def create(self, module: ProcessingModuleEntity) -> ProcessingModuleEntity:
        """Create a new processing module.
        
        Args:
            module: Module entity to create
            
        Returns:
            Created module entity with populated fields
            
        Raises:
            RepositoryError: If creation fails
            ModuleNameExistsError: If module name already exists
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, module_id: UUID) -> Optional[ProcessingModuleEntity]:
        """Find module by ID.
        
        Args:
            module_id: Module ID to search for
            
        Returns:
            Module entity if found, None otherwise
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_by_name(self, module_name: str) -> Optional[ProcessingModuleEntity]:
        """Find module by name.
        
        Args:
            module_name: Module name to search for
            
        Returns:
            Module entity if found, None otherwise
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_by_type(
        self,
        module_type: str,
        is_enabled: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ProcessingModuleEntity]:
        """Find modules by type.
        
        Args:
            module_type: Module type to search for
            is_enabled: Filter by enabled status
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of matching module entities
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def update(self, module: ProcessingModuleEntity) -> ProcessingModuleEntity:
        """Update existing module.
        
        Args:
            module: Module entity with updated data
            
        Returns:
            Updated module entity
            
        Raises:
            RepositoryError: If update fails
            ModuleNotFoundError: If module doesn't exist
        """
        pass
    
    @abstractmethod
    async def delete(self, module_id: UUID) -> bool:
        """Delete module by ID.
        
        Args:
            module_id: ID of module to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            RepositoryError: If deletion fails
        """
        pass
    
    @abstractmethod
    async def get_enabled_modules(
        self,
        module_type: Optional[str] = None,
        order_by: str = "module_name"
    ) -> List[ProcessingModuleEntity]:
        """Get all enabled modules.
        
        Args:
            module_type: Optional module type filter
            order_by: Field to order by
            
        Returns:
            List of enabled module entities
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def get_processing_pipeline(self) -> List[ProcessingModuleEntity]:
        """Get modules in processing pipeline order.
        
        Returns:
            List of modules in execution order:
            0: text_analysis
            1: character_extraction  
            2: panel_generation
            3: speech_bubble
            4: background_generation
            5: style_transfer
            6: quality_control
            7: output_formatting
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def record_execution_metrics(
        self,
        module_id: UUID,
        request_id: UUID,
        execution_time_seconds: float,
        memory_usage_mb: Optional[float] = None,
        cpu_usage_percent: Optional[float] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> bool:
        """Record module execution metrics.
        
        Args:
            module_id: Module ID that executed
            request_id: Request ID that was processed
            execution_time_seconds: Execution time in seconds
            memory_usage_mb: Memory usage in MB
            cpu_usage_percent: CPU usage percentage
            success: Whether execution was successful
            error_message: Error message if failed
            
        Returns:
            True if metrics recorded successfully
            
        Raises:
            RepositoryError: If operation fails
        """
        pass
    
    @abstractmethod
    async def get_performance_stats(
        self,
        module_id: Optional[UUID] = None,
        module_type: Optional[str] = None,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Get module performance statistics.
        
        Args:
            module_id: Optional specific module ID
            module_type: Optional module type filter
            period_days: Period in days to analyze
            
        Returns:
            Dictionary containing performance metrics:
            - total_executions: Total number of executions
            - success_rate: Success rate (0.0 - 1.0)
            - average_execution_time: Average execution time in seconds
            - median_execution_time: Median execution time in seconds
            - p95_execution_time: 95th percentile execution time
            - average_memory_usage: Average memory usage in MB
            - peak_memory_usage: Peak memory usage in MB
            - error_distribution: Distribution of error types
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def get_bottlenecks(
        self,
        period_days: int = 7
    ) -> List[Dict[str, Any]]:
        """Identify processing bottlenecks.
        
        Args:
            period_days: Period in days to analyze
            
        Returns:
            List of bottleneck information:
            - module_id: Module causing bottleneck
            - module_name: Module name
            - average_time: Average execution time
            - impact_score: Impact on overall processing time
            - recommendation: Optimization recommendation
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def get_resource_usage(
        self,
        module_id: Optional[UUID] = None,
        period_hours: int = 24
    ) -> Dict[str, Any]:
        """Get current resource usage metrics.
        
        Args:
            module_id: Optional specific module ID
            period_hours: Period in hours to analyze
            
        Returns:
            Dictionary containing resource usage:
            - current_memory_usage: Current memory usage in MB
            - peak_memory_usage: Peak memory usage in period
            - average_cpu_usage: Average CPU usage percentage
            - peak_cpu_usage: Peak CPU usage percentage
            - concurrent_executions: Current concurrent executions
            - queue_length: Current queue length
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def create_checkpoint(
        self,
        request_id: UUID,
        module_id: UUID,
        checkpoint_data: Dict[str, Any]
    ) -> str:
        """Create processing checkpoint.
        
        Args:
            request_id: Request ID being processed
            module_id: Module ID creating checkpoint
            checkpoint_data: Checkpoint data to save
            
        Returns:
            Checkpoint ID
            
        Raises:
            RepositoryError: If operation fails
        """
        pass
    
    @abstractmethod
    async def get_checkpoint(
        self,
        checkpoint_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve processing checkpoint.
        
        Args:
            checkpoint_id: Checkpoint ID to retrieve
            
        Returns:
            Checkpoint data if found, None otherwise
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def delete_checkpoint(
        self,
        checkpoint_id: str
    ) -> bool:
        """Delete processing checkpoint.
        
        Args:
            checkpoint_id: Checkpoint ID to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            RepositoryError: If operation fails
        """
        pass
    
    @abstractmethod
    async def cleanup_old_metrics(
        self,
        days_to_keep: int = 90
    ) -> int:
        """Cleanup old execution metrics.
        
        Args:
            days_to_keep: Number of days of metrics to keep
            
        Returns:
            Number of records cleaned up
            
        Raises:
            RepositoryError: If operation fails
        """
        pass


# Repository-specific exceptions
class ProcessingModuleRepositoryError(Exception):
    """Base processing module repository error."""
    pass


class ModuleNotFoundError(ProcessingModuleRepositoryError):
    """Module not found error."""
    pass


class ModuleNameExistsError(ProcessingModuleRepositoryError):
    """Module name already exists error."""
    pass


class CheckpointNotFoundError(ProcessingModuleRepositoryError):
    """Checkpoint not found error."""
    pass


class ModuleExecutionError(ProcessingModuleRepositoryError):
    """Module execution error."""
    pass