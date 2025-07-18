"""Test workflow engine functionality."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.core.workflow import WorkflowEngine, Phase, PhaseResult
from app.core.state import StateManager, ProjectState, ProjectStatus, PhaseStatus
from app.core.events import EventBus
from app.agents.base import AgentRole, AgentOutput, ReviewResult


class TestWorkflowEngine:
    """Test WorkflowEngine class."""
    
    @pytest.fixture
    def workflow_engine(self, state_manager: StateManager, event_bus: EventBus):
        """Create workflow engine instance."""
        return WorkflowEngine(state_manager, event_bus)
    
    @pytest.mark.asyncio
    async def test_register_agents(self, workflow_engine: WorkflowEngine):
        """Test registering agents."""
        # Create mock agents
        main_agent = Mock()
        main_agent.role = AgentRole.REQUIREMENTS_MAIN
        
        reviewer_agent = Mock()
        reviewer_agent.role = AgentRole.REQUIREMENTS_REVIEWER
        
        # Register agents
        workflow_engine.register_agent(main_agent)
        workflow_engine.register_agent(reviewer_agent)
        
        # Verify registration
        assert workflow_engine.agents[Phase.REQUIREMENTS]["main"] == main_agent
        assert workflow_engine.agents[Phase.REQUIREMENTS]["reviewer"] == reviewer_agent
    
    @pytest.mark.asyncio
    async def test_execute_phase_success(self, workflow_engine: WorkflowEngine):
        """Test successful phase execution."""
        # Create mock agents
        main_agent = AsyncMock()
        main_agent.role = AgentRole.REQUIREMENTS_MAIN
        main_agent.process.return_value = AgentOutput(
            agent_id="req_main",
            role=AgentRole.REQUIREMENTS_MAIN,
            content="Requirements document",
            metadata={},
            timestamp=datetime.utcnow()
        )
        
        reviewer_agent = AsyncMock()
        reviewer_agent.role = AgentRole.REQUIREMENTS_REVIEWER
        reviewer_agent.review.return_value = ReviewResult(
            approved=True,
            feedback="Looks good!",
            suggestions=[],
            reviewer_id="req_reviewer",
            timestamp=datetime.utcnow()
        )
        
        # Register agents
        workflow_engine.register_agent(main_agent)
        workflow_engine.register_agent(reviewer_agent)
        
        # Execute phase
        result = await workflow_engine.execute_phase(
            project_id="test-project",
            phase=Phase.REQUIREMENTS,
            input_data={"requirements": "Build a todo app"}
        )
        
        assert result.success is True
        assert result.phase == Phase.REQUIREMENTS
        assert result.output.content == "Requirements document"
        assert result.iterations == 1
    
    @pytest.mark.asyncio
    async def test_execute_phase_with_revisions(self, workflow_engine: WorkflowEngine):
        """Test phase execution with review iterations."""
        # Create mock agents
        main_agent = AsyncMock()
        main_agent.role = AgentRole.REQUIREMENTS_MAIN
        
        # First iteration - not approved
        main_agent.process.side_effect = [
            AgentOutput(
                agent_id="req_main",
                role=AgentRole.REQUIREMENTS_MAIN,
                content="Initial requirements",
                metadata={},
                timestamp=datetime.utcnow()
            ),
            AgentOutput(
                agent_id="req_main",
                role=AgentRole.REQUIREMENTS_MAIN,
                content="Revised requirements",
                metadata={},
                timestamp=datetime.utcnow()
            )
        ]
        
        reviewer_agent = AsyncMock()
        reviewer_agent.role = AgentRole.REQUIREMENTS_REVIEWER
        reviewer_agent.review.side_effect = [
            ReviewResult(
                approved=False,
                feedback="Needs more detail",
                suggestions=["Add user stories"],
                reviewer_id="req_reviewer",
                timestamp=datetime.utcnow()
            ),
            ReviewResult(
                approved=True,
                feedback="Much better!",
                suggestions=[],
                reviewer_id="req_reviewer",
                timestamp=datetime.utcnow()
            )
        ]
        
        # Register agents
        workflow_engine.register_agent(main_agent)
        workflow_engine.register_agent(reviewer_agent)
        
        # Execute phase
        result = await workflow_engine.execute_phase(
            project_id="test-project",
            phase=Phase.REQUIREMENTS,
            input_data={"requirements": "Build a todo app"}
        )
        
        assert result.success is True
        assert result.iterations == 2
        assert result.output.content == "Revised requirements"
    
    @pytest.mark.asyncio
    async def test_execute_phase_max_iterations(self, workflow_engine: WorkflowEngine):
        """Test phase execution hitting max iterations."""
        # Create mock agents that never approve
        main_agent = AsyncMock()
        main_agent.role = AgentRole.REQUIREMENTS_MAIN
        main_agent.process.return_value = AgentOutput(
            agent_id="req_main",
            role=AgentRole.REQUIREMENTS_MAIN,
            content="Requirements",
            metadata={},
            timestamp=datetime.utcnow()
        )
        
        reviewer_agent = AsyncMock()
        reviewer_agent.role = AgentRole.REQUIREMENTS_REVIEWER
        reviewer_agent.review.return_value = ReviewResult(
            approved=False,
            feedback="Still needs work",
            suggestions=["More detail"],
            reviewer_id="req_reviewer",
            timestamp=datetime.utcnow()
        )
        
        # Register agents
        workflow_engine.register_agent(main_agent)
        workflow_engine.register_agent(reviewer_agent)
        
        # Execute phase
        result = await workflow_engine.execute_phase(
            project_id="test-project",
            phase=Phase.REQUIREMENTS,
            input_data={"requirements": "Build a todo app"}
        )
        
        # Should still succeed but with max iterations
        assert result.success is True
        assert result.iterations == 3  # Max iterations
        assert "Maximum iterations reached" in result.metadata.get("warning", "")
    
    @pytest.mark.asyncio
    async def test_execute_phase_error_handling(self, workflow_engine: WorkflowEngine):
        """Test phase execution with errors."""
        # Create mock agent that raises error
        main_agent = AsyncMock()
        main_agent.role = AgentRole.REQUIREMENTS_MAIN
        main_agent.process.side_effect = Exception("Processing failed")
        
        # Register agent
        workflow_engine.register_agent(main_agent)
        
        # Execute phase
        result = await workflow_engine.execute_phase(
            project_id="test-project",
            phase=Phase.REQUIREMENTS,
            input_data={"requirements": "Build a todo app"}
        )
        
        assert result.success is False
        assert result.error is not None
        assert "Processing failed" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_project_full_workflow(
        self, 
        workflow_engine: WorkflowEngine,
        state_manager: StateManager
    ):
        """Test executing full project workflow."""
        # Create project
        project_id = "test-full-workflow"
        await state_manager.create_project(
            project_id=project_id,
            name="Full Workflow Test",
            requirements="Build a todo app"
        )
        await state_manager.update_project_status(project_id, ProjectStatus.RUNNING)
        
        # Create mock agents for all phases
        for phase in Phase:
            main_role = AgentRole(f"{phase.value}_main")
            reviewer_role = AgentRole(f"{phase.value}_reviewer")
            
            main_agent = AsyncMock()
            main_agent.role = main_role
            main_agent.process.return_value = AgentOutput(
                agent_id=f"{phase.value}_main",
                role=main_role,
                content=f"{phase.value} output",
                metadata={},
                timestamp=datetime.utcnow()
            )
            
            reviewer_agent = AsyncMock()
            reviewer_agent.role = reviewer_role
            reviewer_agent.review.return_value = ReviewResult(
                approved=True,
                feedback="Approved",
                suggestions=[],
                reviewer_id=f"{phase.value}_reviewer",
                timestamp=datetime.utcnow()
            )
            
            workflow_engine.register_agent(main_agent)
            workflow_engine.register_agent(reviewer_agent)
        
        # Execute project
        success = await workflow_engine.execute_project(project_id)
        
        assert success is True
        
        # Verify all phases completed
        project = await state_manager.get_project(project_id)
        assert project.status == ProjectStatus.COMPLETED
        for phase in Phase:
            assert project.phases[phase].status == PhaseStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_execute_project_with_pause(
        self,
        workflow_engine: WorkflowEngine, 
        state_manager: StateManager
    ):
        """Test executing project that gets paused."""
        # Create project
        project_id = "test-pause"
        await state_manager.create_project(
            project_id=project_id,
            name="Pause Test",
            requirements="Test pause"
        )
        await state_manager.update_project_status(project_id, ProjectStatus.RUNNING)
        
        # Create mock agents
        main_agent = AsyncMock()
        main_agent.role = AgentRole.REQUIREMENTS_MAIN
        main_agent.process.return_value = AgentOutput(
            agent_id="req_main",
            role=AgentRole.REQUIREMENTS_MAIN,
            content="Requirements",
            metadata={},
            timestamp=datetime.utcnow()
        )
        
        reviewer_agent = AsyncMock()
        reviewer_agent.role = AgentRole.REQUIREMENTS_REVIEWER
        reviewer_agent.review.return_value = ReviewResult(
            approved=True,
            feedback="Approved",
            suggestions=[],
            reviewer_id="req_reviewer",
            timestamp=datetime.utcnow()
        )
        
        workflow_engine.register_agent(main_agent)
        workflow_engine.register_agent(reviewer_agent)
        
        # Simulate pause after first phase
        async def pause_after_requirements(*args, **kwargs):
            phase = await state_manager.get_project(project_id)
            if phase.current_phase == Phase.REQUIREMENTS:
                await state_manager.update_project_status(
                    project_id, 
                    ProjectStatus.PAUSED
                )
        
        with patch.object(state_manager, 'update_phase_status', 
                         side_effect=pause_after_requirements):
            success = await workflow_engine.execute_project(project_id)
        
        # Should return False due to pause
        assert success is False
        
        project = await state_manager.get_project(project_id)
        assert project.status == ProjectStatus.PAUSED