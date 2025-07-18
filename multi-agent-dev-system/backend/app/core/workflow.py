"""Workflow engine for managing the development phases."""
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import asyncio
import logging
from datetime import datetime

from ..agents.base import BaseAgent, AgentOutput, ReviewResult
from .state import StateManager, ProjectStatus, PhaseStatus

logger = logging.getLogger(__name__)


class Phase(str, Enum):
    """Development phases."""
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TEST = "test"


class PhaseResult:
    """Result of a phase execution."""
    def __init__(
        self,
        phase: Phase,
        success: bool,
        output: Dict[str, Any],
        iterations: int = 1,
        error: Optional[str] = None
    ):
        self.phase = phase
        self.success = success
        self.output = output
        self.iterations = iterations
        self.error = error


class WorkflowEngine:
    """Manages the workflow execution across phases."""
    
    def __init__(
        self,
        state_manager: StateManager,
        event_callback: Optional[Callable] = None
    ):
        """Initialize workflow engine.
        
        Args:
            state_manager: State manager instance
            event_callback: Callback for workflow events
        """
        self.state_manager = state_manager
        self.event_callback = event_callback
        
        # Define phase order
        self.phase_order = [
            Phase.REQUIREMENTS,
            Phase.DESIGN,
            Phase.IMPLEMENTATION,
            Phase.TEST
        ]
        
        # Phase transitions
        self.transitions = {
            Phase.REQUIREMENTS: Phase.DESIGN,
            Phase.DESIGN: Phase.IMPLEMENTATION,
            Phase.IMPLEMENTATION: Phase.TEST,
            Phase.TEST: None  # End of workflow
        }
        
        # Agents for each phase (to be registered)
        self.phase_agents: Dict[Phase, Dict[str, BaseAgent]] = {
            phase: {} for phase in Phase
        }
        
    def register_agent(self, phase: Phase, role: str, agent: BaseAgent):
        """Register an agent for a phase.
        
        Args:
            phase: Phase the agent belongs to
            role: Role of the agent (main/reviewer)
            agent: Agent instance
        """
        if phase not in self.phase_agents:
            self.phase_agents[phase] = {}
        self.phase_agents[phase][role] = agent
        logger.info(f"Registered {role} agent for {phase} phase")
        
    async def execute_project(
        self, 
        project_id: str,
        start_phase: Optional[Phase] = None
    ) -> bool:
        """Execute the entire project workflow.
        
        Args:
            project_id: Project ID
            start_phase: Phase to start from (default: REQUIREMENTS)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get project state
            project_state = await self.state_manager.get_project_state(project_id)
            if not project_state:
                logger.error(f"Project {project_id} not found")
                return False
                
            # Update project status
            await self.state_manager.update_project_status(
                project_id, 
                ProjectStatus.REQUIREMENTS,
                Phase.REQUIREMENTS
            )
            
            # Execute phases in order
            current_phase = start_phase or Phase.REQUIREMENTS
            phase_input = {"requirements": project_state.requirements}
            
            while current_phase:
                await self._emit_event("phase_start", {
                    "project_id": project_id,
                    "phase": current_phase
                })
                
                # Execute phase
                result = await self.execute_phase(
                    project_id,
                    current_phase,
                    phase_input
                )
                
                if not result.success:
                    logger.error(f"Phase {current_phase} failed: {result.error}")
                    await self.state_manager.update_project_status(
                        project_id,
                        ProjectStatus.FAILED
                    )
                    return False
                    
                # Prepare input for next phase
                phase_input = result.output
                
                # Move to next phase
                current_phase = self.transitions.get(current_phase)
                if current_phase:
                    await self.state_manager.update_project_status(
                        project_id,
                        ProjectStatus[current_phase.upper()],
                        current_phase
                    )
                    
            # Project completed
            await self.state_manager.update_project_status(
                project_id,
                ProjectStatus.COMPLETED
            )
            
            await self._emit_event("project_completed", {
                "project_id": project_id
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing project {project_id}: {str(e)}")
            await self.state_manager.update_project_status(
                project_id,
                ProjectStatus.FAILED
            )
            return False
            
    async def execute_phase(
        self,
        project_id: str,
        phase: Phase,
        input_data: Dict[str, Any]
    ) -> PhaseResult:
        """Execute a single phase with review loop.
        
        Args:
            project_id: Project ID
            phase: Phase to execute
            input_data: Input data for the phase
            
        Returns:
            PhaseResult
        """
        try:
            # Create phase state
            phase_state = await self.state_manager.create_phase(
                project_id,
                phase,
                input_data
            )
            
            # Get agents
            main_agent = self.phase_agents[phase].get("main")
            review_agent = self.phase_agents[phase].get("reviewer")
            
            if not main_agent or not review_agent:
                return PhaseResult(
                    phase=phase,
                    success=False,
                    output={},
                    error=f"Agents not registered for {phase}"
                )
                
            # Update phase status
            await self.state_manager.update_phase_status(
                project_id,
                phase,
                PhaseStatus.IN_PROGRESS
            )
            
            # Main agent work
            agent_output = await main_agent.process(input_data)
            work_product = {
                "content": agent_output.content,
                "metadata": agent_output.metadata
            }
            
            # Review loop
            max_iterations = phase_state.max_iterations
            iteration = 0
            approved = False
            
            while iteration < max_iterations and not approved:
                # Review
                await self.state_manager.update_phase_status(
                    project_id,
                    phase,
                    PhaseStatus.REVIEW
                )
                
                review_result = await review_agent.review(work_product)
                
                await self._emit_event("review_completed", {
                    "project_id": project_id,
                    "phase": phase,
                    "approved": review_result.approved,
                    "feedback": review_result.feedback
                })
                
                if review_result.approved:
                    approved = True
                else:
                    # Revision needed
                    iteration += 1
                    await self.state_manager.increment_phase_iteration(
                        project_id,
                        phase
                    )
                    
                    if iteration < max_iterations:
                        await self.state_manager.update_phase_status(
                            project_id,
                            phase,
                            PhaseStatus.REVISION
                        )
                        
                        # Main agent revises
                        revision_output = await main_agent.revise(
                            work_product,
                            review_result.feedback
                        )
                        
                        work_product = {
                            "content": revision_output.content,
                            "metadata": revision_output.metadata
                        }
                        
            # Phase completed
            await self.state_manager.update_phase_status(
                project_id,
                phase,
                PhaseStatus.COMPLETED,
                work_product
            )
            
            return PhaseResult(
                phase=phase,
                success=approved,
                output=work_product,
                iterations=iteration + 1,
                error=None if approved else "Max iterations reached without approval"
            )
            
        except Exception as e:
            logger.error(f"Error executing phase {phase}: {str(e)}")
            await self.state_manager.update_phase_status(
                project_id,
                phase,
                PhaseStatus.FAILED
            )
            return PhaseResult(
                phase=phase,
                success=False,
                output={},
                error=str(e)
            )
            
    async def pause_workflow(self, project_id: str) -> bool:
        """Pause workflow execution.
        
        Args:
            project_id: Project ID
            
        Returns:
            True if paused successfully
        """
        return await self.state_manager.update_project_status(
            project_id,
            ProjectStatus.PAUSED
        )
        
    async def resume_workflow(
        self, 
        project_id: str,
        direction: Optional[Dict] = None
    ) -> bool:
        """Resume workflow execution.
        
        Args:
            project_id: Project ID
            direction: Optional new direction/requirements
            
        Returns:
            True if resumed successfully
        """
        project_state = await self.state_manager.get_project_state(project_id)
        if not project_state or project_state.status != ProjectStatus.PAUSED:
            return False
            
        # TODO: Apply new direction if provided
        
        # Resume from current phase
        if project_state.current_phase:
            return await self.execute_project(
                project_id,
                Phase(project_state.current_phase)
            )
            
        return False
        
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit workflow event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if self.event_callback:
            await self.event_callback(event_type, data)