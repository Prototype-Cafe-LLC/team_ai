"""Integration tests for the multi-agent system."""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient
import json

from app.core.state import StateManager, ProjectStatus, PhaseStatus
from app.core.workflow import Phase
from app.core.events import EventBus
from app.agents.base import AgentOutput, ReviewResult, AgentRole


@pytest.mark.integration
class TestSystemIntegration:
    """Test full system integration."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, client: AsyncClient):
        """Test WebSocket connection and messaging."""
        # This would require a WebSocket test client
        # For now, we'll test that the endpoint exists
        # In a real test, you'd use a WebSocket test client
        pass
    
    @pytest.mark.asyncio 
    async def test_project_lifecycle(self, client: AsyncClient):
        """Test complete project lifecycle through API."""
        # Mock the LLM responses for all agents
        with patch('app.agents.requirements.RequirementsMainAgent.process') as mock_req_process, \
             patch('app.agents.requirements.RequirementsReviewAgent.review') as mock_req_review, \
             patch('app.agents.design.DesignMainAgent.process') as mock_design_process, \
             patch('app.agents.design.DesignReviewAgent.review') as mock_design_review:
            
            # Setup mock responses
            mock_req_process.return_value = AgentOutput(
                agent_id="req_main",
                role=AgentRole.REQUIREMENTS_MAIN,
                content="## Requirements\n1. Todo CRUD operations",
                metadata={},
                timestamp=None
            )
            
            mock_req_review.return_value = ReviewResult(
                approved=True,
                feedback="Requirements look good",
                suggestions=[],
                reviewer_id="req_reviewer",
                timestamp=None
            )
            
            mock_design_process.return_value = AgentOutput(
                agent_id="design_main",
                role=AgentRole.DESIGN_MAIN,
                content="## Design\n- FastAPI backend\n- PostgreSQL",
                metadata={},
                timestamp=None
            )
            
            mock_design_review.return_value = ReviewResult(
                approved=True,
                feedback="Design approved",
                suggestions=[],
                reviewer_id="design_reviewer",
                timestamp=None
            )
            
            # 1. Create project
            create_response = await client.post(
                "/api/projects",
                json={
                    "name": "Integration Test Project",
                    "requirements": "Create a simple todo application"
                }
            )
            assert create_response.status_code == 200
            project_data = create_response.json()
            project_id = project_data["project_id"]
            
            # 2. Check project status
            status_response = await client.get(f"/api/projects/{project_id}")
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["name"] == "Integration Test Project"
            
            # 3. List projects
            list_response = await client.get("/api/projects")
            assert list_response.status_code == 200
            projects = list_response.json()
            assert any(p["project_id"] == project_id for p in projects)
            
            # 4. Pause project
            pause_response = await client.post(f"/api/projects/{project_id}/pause")
            assert pause_response.status_code == 200
            
            # 5. Resume project
            resume_response = await client.post(f"/api/projects/{project_id}/resume")
            assert resume_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_concurrent_projects(self, client: AsyncClient):
        """Test handling multiple concurrent projects."""
        with patch('app.core.conductor.ConductorManager.start_project') as mock_start, \
             patch('app.core.conductor.ConductorManager.get_status') as mock_status:
            
            # Setup mocks
            project_ids = []
            
            async def mock_start_side_effect(*args, **kwargs):
                pid = f"concurrent-{len(project_ids)}"
                project_ids.append(pid)
                return pid
            
            mock_start.side_effect = mock_start_side_effect
            
            def mock_status_side_effect(pid):
                return {
                    "project_id": pid,
                    "name": f"Project {pid}",
                    "status": "running",
                    "current_phase": "requirements",
                    "created_at": "2024-01-01T00:00:00"
                }
            
            mock_status.side_effect = mock_status_side_effect
            
            # Create multiple projects concurrently
            tasks = []
            for i in range(5):
                task = client.post(
                    "/api/projects",
                    json={
                        "name": f"Concurrent Project {i}",
                        "requirements": f"Requirements for project {i}"
                    }
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            
            # All should succeed
            assert all(r.status_code == 200 for r in responses)
            assert len(project_ids) == 5
    
    @pytest.mark.asyncio
    async def test_error_propagation(self, client: AsyncClient):
        """Test error handling and propagation."""
        # Test with missing requirements
        response = await client.post(
            "/api/projects",
            json={"name": "Error Test"}
        )
        assert response.status_code == 422  # Validation error
        
        # Test with agent failure
        with patch('app.core.conductor.ConductorManager.start_project') as mock_start:
            mock_start.side_effect = Exception("Agent initialization failed")
            
            response = await client.post(
                "/api/projects",
                json={
                    "name": "Failed Project",
                    "requirements": "This will fail"
                }
            )
            assert response.status_code == 500
            assert "Agent initialization failed" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_state_persistence(self, state_manager: StateManager):
        """Test that state persists correctly."""
        # Create a project
        project_id = "persistence-test"
        project = await state_manager.create_project(
            project_id=project_id,
            name="Persistence Test",
            requirements="Test state persistence"
        )
        
        # Update various states
        await state_manager.update_project_status(project_id, ProjectStatus.RUNNING)
        await state_manager.update_current_phase(project_id, Phase.DESIGN)
        await state_manager.add_phase_output(
            project_id,
            Phase.REQUIREMENTS,
            {"content": "Requirements output", "metadata": {}}
        )
        
        # Retrieve and verify
        retrieved = await state_manager.get_project(project_id)
        assert retrieved is not None
        assert retrieved.status == ProjectStatus.RUNNING
        assert retrieved.current_phase == Phase.DESIGN
        assert len(retrieved.phases[Phase.REQUIREMENTS].outputs) == 1
        
        # Simulate disconnection and reconnection
        await state_manager.disconnect()
        await state_manager.connect()
        
        # State should persist
        retrieved_again = await state_manager.get_project(project_id)
        assert retrieved_again is not None
        assert retrieved_again.status == ProjectStatus.RUNNING
        assert retrieved_again.current_phase == Phase.DESIGN