"""Test API endpoints."""
import pytest
from httpx import AsyncClient
import json
from unittest.mock import patch, AsyncMock


class TestAPI:
    """Test API endpoints."""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns API info."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Multi-Agent Development System API"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "multi-agent-dev-system"
    
    @pytest.mark.asyncio
    async def test_list_agents(self, client: AsyncClient):
        """Test listing all registered agents."""
        response = await client.get("/api/agents")
        assert response.status_code == 200
        data = response.json()
        
        assert "agents" in data
        agents = data["agents"]
        assert len(agents) == 8  # 4 phases × 2 agents each
        
        # Check that all expected agents are present
        expected_roles = [
            "requirements_main", "requirements_reviewer",
            "design_main", "design_reviewer", 
            "implementation_main", "implementation_reviewer",
            "test_main", "test_reviewer"
        ]
        
        agent_roles = [agent["role"] for agent in agents]
        for role in expected_roles:
            assert role in agent_roles
    
    @pytest.mark.asyncio
    async def test_create_project(self, client: AsyncClient, test_project_requirements: str):
        """Test creating a new project."""
        with patch('app.core.conductor.ConductorManager.start_project') as mock_start:
            mock_start.return_value = "test-project-123"
            
            with patch('app.core.conductor.ConductorManager.get_status') as mock_status:
                mock_status.return_value = {
                    "project_id": "test-project-123",
                    "name": "Test Project",
                    "status": "running",
                    "current_phase": "requirements",
                    "created_at": "2024-01-01T00:00:00"
                }
                
                response = await client.post(
                    "/api/projects",
                    json={
                        "name": "Test Project",
                        "requirements": test_project_requirements
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["project_id"] == "test-project-123"
                assert data["name"] == "Test Project"
                assert data["status"] == "running"
                assert data["current_phase"] == "requirements"
    
    @pytest.mark.asyncio
    async def test_list_projects(self, client: AsyncClient):
        """Test listing all projects."""
        with patch('app.core.conductor.ConductorManager.list_projects') as mock_list:
            mock_list.return_value = [
                {
                    "project_id": "proj-1",
                    "name": "Project 1",
                    "status": "completed",
                    "current_phase": "test",
                    "created_at": "2024-01-01T00:00:00"
                },
                {
                    "project_id": "proj-2",
                    "name": "Project 2", 
                    "status": "running",
                    "current_phase": "design",
                    "created_at": "2024-01-02T00:00:00"
                }
            ]
            
            response = await client.get("/api/projects")
            assert response.status_code == 200
            data = response.json()
            
            assert len(data) == 2
            assert data[0]["project_id"] == "proj-1"
            assert data[1]["project_id"] == "proj-2"
    
    @pytest.mark.asyncio
    async def test_get_project_status(self, client: AsyncClient):
        """Test getting project status."""
        with patch('app.core.conductor.ConductorManager.get_status') as mock_status:
            mock_status.return_value = {
                "project_id": "test-project-123",
                "name": "Test Project",
                "status": "running",
                "current_phase": "design",
                "phases": {
                    "requirements": {"status": "completed"},
                    "design": {"status": "in_progress"}
                },
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T01:00:00"
            }
            
            response = await client.get("/api/projects/test-project-123")
            assert response.status_code == 200
            data = response.json()
            
            assert data["project_id"] == "test-project-123"
            assert data["current_phase"] == "design"
            assert data["phases"]["requirements"]["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_get_project_status_not_found(self, client: AsyncClient):
        """Test getting status for non-existent project."""
        with patch('app.core.conductor.ConductorManager.get_status') as mock_status:
            mock_status.return_value = None
            
            response = await client.get("/api/projects/non-existent")
            assert response.status_code == 404
            assert response.json()["detail"] == "Project not found"
    
    @pytest.mark.asyncio
    async def test_pause_project(self, client: AsyncClient):
        """Test pausing a project."""
        with patch('app.core.conductor.ConductorManager.pause_workflow') as mock_pause:
            mock_pause.return_value = True
            
            response = await client.post("/api/projects/test-project-123/pause")
            assert response.status_code == 200
            assert response.json()["message"] == "Project paused successfully"
    
    @pytest.mark.asyncio
    async def test_resume_project(self, client: AsyncClient):
        """Test resuming a project."""
        with patch('app.core.conductor.ConductorManager.resume_workflow') as mock_resume:
            mock_resume.return_value = True
            
            response = await client.post("/api/projects/test-project-123/resume")
            assert response.status_code == 200
            assert response.json()["message"] == "Project resumed successfully"
    
    @pytest.mark.asyncio
    async def test_resume_project_with_direction(self, client: AsyncClient):
        """Test resuming a project with new direction."""
        with patch('app.core.conductor.ConductorManager.resume_workflow') as mock_resume:
            mock_resume.return_value = True
            
            response = await client.post(
                "/api/projects/test-project-123/resume",
                json={"direction": {"focus": "performance", "priority": "high"}}
            )
            assert response.status_code == 200
            assert response.json()["message"] == "Project resumed successfully"
            
            # Verify the direction was passed
            mock_resume.assert_called_once_with(
                "test-project-123",
                {"focus": "performance", "priority": "high"}
            )