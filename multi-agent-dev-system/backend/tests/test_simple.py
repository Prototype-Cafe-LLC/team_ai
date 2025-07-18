"""Simple tests to verify basic functionality."""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


class TestBasicFunctionality:
    """Test basic system functionality."""
    
    @pytest.mark.asyncio
    async def test_api_health(self, client: AsyncClient):
        """Test API is healthy."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_api_root(self, client: AsyncClient):
        """Test API root endpoint."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Multi-Agent Development System API"
        assert "endpoints" in data
    
    @pytest.mark.asyncio
    async def test_create_and_get_project(self, client: AsyncClient):
        """Test creating and retrieving a project."""
        # Mock the backend services
        with patch('app.core.conductor.ConductorManager.start_project') as mock_start, \
             patch('app.core.conductor.ConductorManager.get_status') as mock_status:
            
            # Setup mocks
            mock_start.return_value = "test-123"
            mock_status.return_value = {
                "project_id": "test-123",
                "name": "Test Project",
                "status": "running",
                "current_phase": "requirements",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "phases": {}
            }
            
            # Create project
            create_response = await client.post(
                "/api/projects",
                json={
                    "name": "Test Project",
                    "requirements": "Build a simple app"
                }
            )
            assert create_response.status_code == 200
            project = create_response.json()
            assert project["project_id"] == "test-123"
            assert project["name"] == "Test Project"
            
            # Get project status
            status_response = await client.get("/api/projects/test-123")
            assert status_response.status_code == 200
            status = status_response.json()
            assert status["project_id"] == "test-123"
            assert status["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_workflow_operations(self, client: AsyncClient):
        """Test workflow control operations."""
        with patch('app.core.conductor.ConductorManager.pause_workflow') as mock_pause, \
             patch('app.core.conductor.ConductorManager.resume_workflow') as mock_resume:
            
            mock_pause.return_value = True
            mock_resume.return_value = True
            
            # Test pause
            pause_response = await client.post("/api/projects/test-123/pause")
            assert pause_response.status_code == 200
            assert "paused successfully" in pause_response.json()["message"]
            
            # Test resume
            resume_response = await client.post("/api/projects/test-123/resume")
            assert resume_response.status_code == 200
            assert "resumed successfully" in resume_response.json()["message"]
    
    @pytest.mark.asyncio
    async def test_list_projects(self, client: AsyncClient):
        """Test listing projects."""
        with patch('app.core.conductor.ConductorManager.list_projects') as mock_list:
            mock_list.return_value = [
                {
                    "project_id": "proj-1",
                    "name": "Project 1",
                    "status": "completed",
                    "current_phase": "test",
                    "created_at": "2024-01-01T00:00:00"
                }
            ]
            
            response = await client.get("/api/projects")
            assert response.status_code == 200
            projects = response.json()
            assert len(projects) == 1
            assert projects[0]["name"] == "Project 1"