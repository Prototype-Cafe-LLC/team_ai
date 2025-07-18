"""Test StateManager functionality."""
import pytest
from datetime import datetime
from app.core.state import StateManager, ProjectState, ProjectStatus, PhaseState, PhaseStatus
from app.core.workflow import Phase
from app.core.events import EventBus


class TestStateManager:
    """Test StateManager class."""
    
    @pytest.mark.asyncio
    async def test_create_project(self, state_manager: StateManager):
        """Test creating a new project."""
        project_id = "test-proj-123"
        project_name = "Test Project"
        requirements = "Build a test application"
        
        project = await state_manager.create_project(
            project_id=project_id,
            name=project_name,
            requirements=requirements
        )
        
        assert project is not None
        assert project.project_id == project_id
        assert project.name == project_name
        assert project.requirements == requirements
        assert project.status == ProjectStatus.INITIALIZED
        assert project.current_phase is None
        assert len(project.phases) == 4  # All phases should be initialized
    
    @pytest.mark.asyncio
    async def test_get_project(self, state_manager: StateManager):
        """Test retrieving an existing project."""
        # First create a project
        project_id = "test-proj-456"
        await state_manager.create_project(
            project_id=project_id,
            name="Test Project 2",
            requirements="Another test"
        )
        
        # Now retrieve it
        project = await state_manager.get_project(project_id)
        assert project is not None
        assert project.project_id == project_id
        assert project.name == "Test Project 2"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_project(self, state_manager: StateManager):
        """Test retrieving a non-existent project."""
        project = await state_manager.get_project("non-existent")
        assert project is None
    
    @pytest.mark.asyncio
    async def test_update_project_status(self, state_manager: StateManager):
        """Test updating project status."""
        project_id = "test-proj-789"
        await state_manager.create_project(
            project_id=project_id,
            name="Status Test",
            requirements="Test status updates"
        )
        
        # Update to running
        success = await state_manager.update_project_status(
            project_id, 
            ProjectStatus.RUNNING
        )
        assert success is True
        
        project = await state_manager.get_project(project_id)
        assert project.status == ProjectStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_update_current_phase(self, state_manager: StateManager):
        """Test updating current phase."""
        project_id = "test-phase-123"
        await state_manager.create_project(
            project_id=project_id,
            name="Phase Test",
            requirements="Test phase updates"
        )
        
        # Update current phase
        success = await state_manager.update_current_phase(
            project_id,
            Phase.DESIGN
        )
        assert success is True
        
        project = await state_manager.get_project(project_id)
        assert project.current_phase == Phase.DESIGN
    
    @pytest.mark.asyncio
    async def test_update_phase_status(self, state_manager: StateManager):
        """Test updating phase status."""
        project_id = "test-phase-status"
        await state_manager.create_project(
            project_id=project_id,
            name="Phase Status Test",
            requirements="Test phase status"
        )
        
        # Update phase status
        success = await state_manager.update_phase_status(
            project_id,
            Phase.REQUIREMENTS,
            PhaseStatus.COMPLETED
        )
        assert success is True
        
        project = await state_manager.get_project(project_id)
        assert project.phases[Phase.REQUIREMENTS].status == PhaseStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_add_phase_output(self, state_manager: StateManager):
        """Test adding output to a phase."""
        project_id = "test-output"
        await state_manager.create_project(
            project_id=project_id,
            name="Output Test",
            requirements="Test outputs"
        )
        
        # Add output
        output_data = {
            "content": "Requirements analysis complete",
            "metadata": {"word_count": 100}
        }
        
        success = await state_manager.add_phase_output(
            project_id,
            Phase.REQUIREMENTS,
            output_data
        )
        assert success is True
        
        project = await state_manager.get_project(project_id)
        phase = project.phases[Phase.REQUIREMENTS]
        assert len(phase.outputs) == 1
        assert phase.outputs[0]["content"] == "Requirements analysis complete"
    
    @pytest.mark.asyncio
    async def test_add_phase_review(self, state_manager: StateManager):
        """Test adding review to a phase."""
        project_id = "test-review"
        await state_manager.create_project(
            project_id=project_id,
            name="Review Test",
            requirements="Test reviews"
        )
        
        # Add review
        review_data = {
            "approved": True,
            "feedback": "Looks good!",
            "reviewer_id": "reviewer-123"
        }
        
        success = await state_manager.add_phase_review(
            project_id,
            Phase.REQUIREMENTS,
            review_data
        )
        assert success is True
        
        project = await state_manager.get_project(project_id)
        phase = project.phases[Phase.REQUIREMENTS]
        assert len(phase.reviews) == 1
        assert phase.reviews[0]["approved"] is True
        assert phase.reviews[0]["feedback"] == "Looks good!"
    
    @pytest.mark.asyncio
    async def test_list_projects(self, state_manager: StateManager):
        """Test listing all projects."""
        # Create multiple projects
        for i in range(3):
            await state_manager.create_project(
                project_id=f"list-test-{i}",
                name=f"List Test {i}",
                requirements=f"Test {i}"
            )
        
        projects = await state_manager.list_projects()
        
        # Should have at least the 3 we just created
        assert len(projects) >= 3
        
        # Check that our projects are in the list
        project_ids = [p["project_id"] for p in projects]
        for i in range(3):
            assert f"list-test-{i}" in project_ids
    
    @pytest.mark.asyncio
    async def test_delete_project(self, state_manager: StateManager):
        """Test deleting a project."""
        project_id = "test-delete"
        await state_manager.create_project(
            project_id=project_id,
            name="Delete Test",
            requirements="To be deleted"
        )
        
        # Verify it exists
        project = await state_manager.get_project(project_id)
        assert project is not None
        
        # Delete it
        success = await state_manager.delete_project(project_id)
        assert success is True
        
        # Verify it's gone
        project = await state_manager.get_project(project_id)
        assert project is None
    
    @pytest.mark.asyncio
    async def test_concurrent_updates(self, state_manager: StateManager):
        """Test concurrent updates to same project."""
        project_id = "test-concurrent"
        await state_manager.create_project(
            project_id=project_id,
            name="Concurrent Test",
            requirements="Test concurrency"
        )
        
        # Simulate concurrent updates
        import asyncio
        
        async def update_status():
            await state_manager.update_project_status(
                project_id, 
                ProjectStatus.RUNNING
            )
        
        async def update_phase():
            await state_manager.update_current_phase(
                project_id,
                Phase.DESIGN
            )
        
        async def add_output():
            await state_manager.add_phase_output(
                project_id,
                Phase.REQUIREMENTS,
                {"content": "Concurrent output"}
            )
        
        # Run all updates concurrently
        await asyncio.gather(
            update_status(),
            update_phase(), 
            add_output()
        )
        
        # Verify all updates succeeded
        project = await state_manager.get_project(project_id)
        assert project.status == ProjectStatus.RUNNING
        assert project.current_phase == Phase.DESIGN
        assert len(project.phases[Phase.REQUIREMENTS].outputs) > 0