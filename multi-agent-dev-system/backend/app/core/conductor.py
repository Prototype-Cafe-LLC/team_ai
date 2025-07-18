"""Conductor Manager for orchestrating the multi-agent system."""
from typing import Dict, List, Optional, Any, Callable
import asyncio
import logging
from datetime import datetime
import uuid

from ..agents.base import BaseAgent, AgentRole
from .state import StateManager, ProjectStatus
from .workflow import WorkflowEngine, Phase
from .events import EventBus

logger = logging.getLogger(__name__)


class ConductorManager:
    """Orchestrates the entire multi-agent development system."""
    
    def __init__(
        self,
        state_manager: StateManager,
        event_bus: Optional[EventBus] = None
    ):
        """Initialize conductor manager.
        
        Args:
            state_manager: State manager instance
            event_bus: Event bus for publishing events
        """
        self.state_manager = state_manager
        self.event_bus = event_bus or EventBus()
        
        # Initialize workflow engine
        self.workflow_engine = WorkflowEngine(
            state_manager=state_manager,
            event_callback=self._handle_workflow_event
        )
        
        # Agent registry
        self.agent_registry: Dict[str, BaseAgent] = {}
        
        # Active projects
        self.active_projects: Dict[str, asyncio.Task] = {}
        
    def register_agent(self, agent: BaseAgent):
        """Register an agent in the system.
        
        Args:
            agent: Agent to register
        """
        self.agent_registry[agent.agent_id] = agent
        
        # Map agent to workflow phase
        role_to_phase = {
            AgentRole.REQUIREMENTS_MAIN: (Phase.REQUIREMENTS, "main"),
            AgentRole.REQUIREMENTS_REVIEWER: (Phase.REQUIREMENTS, "reviewer"),
            AgentRole.DESIGN_MAIN: (Phase.DESIGN, "main"),
            AgentRole.DESIGN_REVIEWER: (Phase.DESIGN, "reviewer"),
            AgentRole.IMPLEMENTATION_MAIN: (Phase.IMPLEMENTATION, "main"),
            AgentRole.IMPLEMENTATION_REVIEWER: (Phase.IMPLEMENTATION, "reviewer"),
            AgentRole.TEST_MAIN: (Phase.TEST, "main"),
            AgentRole.TEST_REVIEWER: (Phase.TEST, "reviewer"),
        }
        
        if agent.role in role_to_phase:
            phase, role = role_to_phase[agent.role]
            self.workflow_engine.register_agent(phase, role, agent)
            
        logger.info(f"Registered agent {agent.agent_id} with role {agent.role}")
        
    async def start_project(
        self,
        requirements: str,
        name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Start a new project.
        
        Args:
            requirements: Project requirements
            name: Optional project name
            metadata: Optional project metadata
            
        Returns:
            Project ID
        """
        # Generate project ID
        project_id = str(uuid.uuid4())
        
        # Create project state
        await self.state_manager.create_project(
            project_id=project_id,
            name=name or f"Project-{project_id[:8]}",
            requirements=requirements,
            metadata=metadata
        )
        
        # Emit project created event
        await self.event_bus.emit("project_created", {
            "project_id": project_id,
            "name": name,
            "requirements": requirements,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Start workflow execution
        task = asyncio.create_task(
            self.workflow_engine.execute_project(project_id)
        )
        self.active_projects[project_id] = task
        
        # Handle task completion
        task.add_done_callback(
            lambda t: asyncio.create_task(
                self._handle_project_completion(project_id, t)
            )
        )
        
        logger.info(f"Started project {project_id}")
        return project_id
        
    async def pause_workflow(self, project_id: str) -> bool:
        """Pause project workflow.
        
        Args:
            project_id: Project ID
            
        Returns:
            True if paused successfully
        """
        # Cancel active task if exists
        if project_id in self.active_projects:
            task = self.active_projects[project_id]
            if not task.done():
                task.cancel()
                
        # Update state
        result = await self.workflow_engine.pause_workflow(project_id)
        
        if result:
            await self.event_bus.emit("project_paused", {
                "project_id": project_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        return result
        
    async def resume_workflow(
        self,
        project_id: str,
        direction: Optional[Dict] = None
    ) -> bool:
        """Resume project workflow.
        
        Args:
            project_id: Project ID
            direction: Optional new direction
            
        Returns:
            True if resumed successfully
        """
        # Start new task for resumed workflow
        task = asyncio.create_task(
            self.workflow_engine.resume_workflow(project_id, direction)
        )
        self.active_projects[project_id] = task
        
        # Handle task completion
        task.add_done_callback(
            lambda t: asyncio.create_task(
                self._handle_project_completion(project_id, t)
            )
        )
        
        await self.event_bus.emit("project_resumed", {
            "project_id": project_id,
            "direction": direction,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True
        
    async def get_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project status.
        
        Args:
            project_id: Project ID
            
        Returns:
            Status dictionary if project exists
        """
        project_state = await self.state_manager.get_project_state(project_id)
        if not project_state:
            return None
            
        # Get phase states
        phase_states = {}
        for phase in Phase:
            phase_state = await self.state_manager.get_phase_state(
                project_id,
                phase
            )
            if phase_state:
                phase_states[phase] = {
                    "status": phase_state.status,
                    "iterations": phase_state.current_iteration,
                    "started_at": phase_state.started_at.isoformat() if phase_state.started_at else None,
                    "completed_at": phase_state.completed_at.isoformat() if phase_state.completed_at else None
                }
                
        return {
            "project_id": project_id,
            "name": project_state.name,
            "status": project_state.status,
            "current_phase": project_state.current_phase,
            "phases": phase_states,
            "created_at": project_state.created_at.isoformat(),
            "updated_at": project_state.updated_at.isoformat()
        }
        
    async def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects.
        
        Returns:
            List of project summaries
        """
        project_ids = await self.state_manager.get_all_project_ids()
        projects = []
        
        for project_id in project_ids:
            status = await self.get_status(project_id)
            if status:
                projects.append({
                    "project_id": project_id,
                    "name": status["name"],
                    "status": status["status"],
                    "current_phase": status["current_phase"],
                    "created_at": status["created_at"]
                })
                
        return projects
        
    async def _handle_workflow_event(self, event_type: str, data: Dict[str, Any]):
        """Handle workflow events.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        # Add timestamp
        data["timestamp"] = datetime.utcnow().isoformat()
        
        # Emit to event bus
        await self.event_bus.emit(f"workflow_{event_type}", data)
        
        # Log important events
        if event_type in ["phase_start", "phase_complete", "project_completed"]:
            logger.info(f"Workflow event: {event_type} - {data}")
            
    async def _handle_project_completion(self, project_id: str, task: asyncio.Task):
        """Handle project task completion.
        
        Args:
            project_id: Project ID
            task: Completed task
        """
        # Remove from active projects
        self.active_projects.pop(project_id, None)
        
        # Check if task failed
        if task.cancelled():
            logger.info(f"Project {project_id} was cancelled")
        elif task.exception():
            logger.error(f"Project {project_id} failed with error: {task.exception()}")
            await self.event_bus.emit("project_failed", {
                "project_id": project_id,
                "error": str(task.exception()),
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            result = task.result()
            if result:
                logger.info(f"Project {project_id} completed successfully")
            else:
                logger.error(f"Project {project_id} completed with failure")
                
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent if found
        """
        return self.agent_registry.get(agent_id)
        
    def list_agents(self) -> List[Dict[str, str]]:
        """List all registered agents.
        
        Returns:
            List of agent info
        """
        return [
            {
                "agent_id": agent.agent_id,
                "role": agent.role.value
            }
            for agent in self.agent_registry.values()
        ]