"""State management for the multi-agent system."""
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
import json
import redis
from redis.asyncio import Redis
import asyncio
import logging

logger = logging.getLogger(__name__)


class ProjectStatus(str, Enum):
    """Project status enum."""
    INITIALIZED = "initialized"
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TEST = "test"
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"


class PhaseStatus(str, Enum):
    """Phase status enum."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    REVISION = "revision"
    COMPLETED = "completed"
    FAILED = "failed"


class ProjectState(BaseModel):
    """State of a project."""
    project_id: str
    name: str
    status: ProjectStatus
    current_phase: Optional[str] = None
    requirements: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = {}
    
    
class PhaseState(BaseModel):
    """State of a phase."""
    phase_id: str
    project_id: str
    phase_type: str
    status: PhaseStatus
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    current_iteration: int = 0
    max_iterations: int = 3
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    

class StateManager:
    """Manages state for projects and phases."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize state manager.
        
        Args:
            redis_url: URL for Redis connection
        """
        self.redis_url = redis_url
        self._redis: Optional[Redis] = None
        
    async def connect(self):
        """Connect to Redis."""
        self._redis = await Redis.from_url(self.redis_url, decode_responses=True)
        
    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            
    def _get_project_key(self, project_id: str) -> str:
        """Get Redis key for project state."""
        return f"project:{project_id}:state"
    
    def _get_phase_key(self, project_id: str, phase_type: str) -> str:
        """Get Redis key for phase state."""
        return f"project:{project_id}:phase:{phase_type}:state"
    
    async def create_project(
        self, 
        project_id: str, 
        name: str, 
        requirements: str,
        metadata: Optional[Dict] = None
    ) -> ProjectState:
        """Create a new project state.
        
        Args:
            project_id: Unique project ID
            name: Project name
            requirements: Project requirements
            metadata: Optional metadata
            
        Returns:
            Created ProjectState
        """
        project_state = ProjectState(
            project_id=project_id,
            name=name,
            status=ProjectStatus.INITIALIZED,
            requirements=requirements,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        await self._redis.set(
            self._get_project_key(project_id),
            project_state.json(),
            ex=86400  # 24 hour expiry
        )
        
        return project_state
    
    async def get_project_state(self, project_id: str) -> Optional[ProjectState]:
        """Get project state.
        
        Args:
            project_id: Project ID
            
        Returns:
            ProjectState if found, None otherwise
        """
        data = await self._redis.get(self._get_project_key(project_id))
        if data:
            return ProjectState.parse_raw(data)
        return None
    
    async def update_project_status(
        self, 
        project_id: str, 
        status: ProjectStatus,
        current_phase: Optional[str] = None
    ) -> bool:
        """Update project status.
        
        Args:
            project_id: Project ID
            status: New status
            current_phase: Current phase if applicable
            
        Returns:
            True if updated, False if project not found
        """
        project_state = await self.get_project_state(project_id)
        if not project_state:
            return False
            
        project_state.status = status
        project_state.current_phase = current_phase
        project_state.updated_at = datetime.utcnow()
        
        await self._redis.set(
            self._get_project_key(project_id),
            project_state.json(),
            ex=86400
        )
        
        return True
    
    async def create_phase(
        self,
        project_id: str,
        phase_type: str,
        input_data: Dict[str, Any]
    ) -> PhaseState:
        """Create a new phase state.
        
        Args:
            project_id: Project ID
            phase_type: Type of phase
            input_data: Input data for the phase
            
        Returns:
            Created PhaseState
        """
        phase_state = PhaseState(
            phase_id=f"{project_id}_{phase_type}",
            project_id=project_id,
            phase_type=phase_type,
            status=PhaseStatus.PENDING,
            input_data=input_data,
            started_at=datetime.utcnow()
        )
        
        await self._redis.set(
            self._get_phase_key(project_id, phase_type),
            phase_state.json(),
            ex=86400
        )
        
        return phase_state
    
    async def get_phase_state(
        self, 
        project_id: str, 
        phase_type: str
    ) -> Optional[PhaseState]:
        """Get phase state.
        
        Args:
            project_id: Project ID
            phase_type: Phase type
            
        Returns:
            PhaseState if found, None otherwise
        """
        data = await self._redis.get(self._get_phase_key(project_id, phase_type))
        if data:
            return PhaseState.parse_raw(data)
        return None
    
    async def update_phase_status(
        self,
        project_id: str,
        phase_type: str,
        status: PhaseStatus,
        output_data: Optional[Dict] = None
    ) -> bool:
        """Update phase status.
        
        Args:
            project_id: Project ID
            phase_type: Phase type
            status: New status
            output_data: Output data if completed
            
        Returns:
            True if updated, False if phase not found
        """
        phase_state = await self.get_phase_state(project_id, phase_type)
        if not phase_state:
            return False
            
        phase_state.status = status
        if output_data:
            phase_state.output_data = output_data
        if status == PhaseStatus.COMPLETED:
            phase_state.completed_at = datetime.utcnow()
            
        await self._redis.set(
            self._get_phase_key(project_id, phase_type),
            phase_state.json(),
            ex=86400
        )
        
        return True
    
    async def increment_phase_iteration(
        self, 
        project_id: str, 
        phase_type: str
    ) -> int:
        """Increment phase iteration count.
        
        Args:
            project_id: Project ID
            phase_type: Phase type
            
        Returns:
            New iteration count
        """
        phase_state = await self.get_phase_state(project_id, phase_type)
        if not phase_state:
            raise ValueError(f"Phase {phase_type} not found for project {project_id}")
            
        phase_state.current_iteration += 1
        
        await self._redis.set(
            self._get_phase_key(project_id, phase_type),
            phase_state.json(),
            ex=86400
        )
        
        return phase_state.current_iteration
    
    async def get_all_project_ids(self) -> List[str]:
        """Get all project IDs.
        
        Returns:
            List of project IDs
        """
        keys = await self._redis.keys("project:*:state")
        project_ids = []
        for key in keys:
            # Extract project ID from key
            parts = key.split(":")
            if len(parts) >= 3:
                project_ids.append(parts[1])
        return project_ids