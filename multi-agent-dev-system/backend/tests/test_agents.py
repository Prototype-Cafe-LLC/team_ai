"""Test agent functionality."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.agents.base import AgentRole, AgentOutput, ReviewResult
from app.agents.requirements import RequirementsMainAgent, RequirementsReviewAgent
from app.agents.design import DesignMainAgent, DesignReviewAgent
from app.agents.implementation import ImplementationMainAgent, ImplementationReviewAgent
from app.agents.test import TestMainAgent, TestReviewAgent


class TestAgentBase:
    """Test base agent functionality."""
    
    @pytest.mark.asyncio
    async def test_agent_output_creation(self):
        """Test creating agent output."""
        output = AgentOutput(
            agent_id="test-agent",
            role=AgentRole.REQUIREMENTS_MAIN,
            content="Test output",
            metadata={"test": True},
            timestamp=datetime.utcnow()
        )
        
        assert output.agent_id == "test-agent"
        assert output.role == AgentRole.REQUIREMENTS_MAIN
        assert output.content == "Test output"
        assert output.metadata["test"] is True
    
    @pytest.mark.asyncio
    async def test_review_result_creation(self):
        """Test creating review result."""
        result = ReviewResult(
            approved=True,
            feedback="Great work!",
            suggestions=["Add more detail"],
            reviewer_id="reviewer-123",
            timestamp=datetime.utcnow()
        )
        
        assert result.approved is True
        assert result.feedback == "Great work!"
        assert len(result.suggestions) == 1
        assert result.reviewer_id == "reviewer-123"


class TestRequirementsAgents:
    """Test requirements phase agents."""
    
    @pytest.mark.asyncio
    async def test_requirements_main_agent_process(self):
        """Test requirements main agent processing."""
        with patch('app.core.llm_factory.LLMFactory.create_agent_llm') as mock_llm:
            # Mock the LLM chain
            mock_chain = AsyncMock()
            mock_chain.arun.return_value = """
            ## Requirements Document
            
            ### Functional Requirements
            1. User can add todo items
            2. User can mark items complete
            3. User can delete items
            
            ### Non-Functional Requirements
            1. Fast response time
            2. Simple UI
            """
            
            agent = RequirementsMainAgent()
            agent.chain = mock_chain
            
            result = await agent.process({
                "requirements": "Create a todo app"
            })
            
            assert result.agent_id == "requirements_main_agent"
            assert result.role == AgentRole.REQUIREMENTS_MAIN
            assert "Requirements Document" in result.content
            assert "Functional Requirements" in result.content
    
    @pytest.mark.asyncio
    async def test_requirements_review_agent(self):
        """Test requirements review agent."""
        with patch('app.core.llm_factory.LLMFactory.create_agent_llm') as mock_llm:
            # Mock the review chain
            mock_chain = AsyncMock()
            mock_chain.arun.return_value = """
            {
                "approved": true,
                "overall_quality": 8,
                "feedback": "Requirements are clear and complete",
                "missing_requirements": [],
                "suggestions": ["Consider adding performance requirements"],
                "strengths": ["Clear functional requirements"]
            }
            """
            
            agent = RequirementsReviewAgent()
            agent.review_chain = mock_chain
            
            review = await agent.review({
                "content": "## Requirements Document..."
            })
            
            assert review.approved is True
            assert review.feedback == "Requirements are clear and complete"
            assert len(review.suggestions) == 1
            assert review.reviewer_id == "requirements_review_agent"


class TestDesignAgents:
    """Test design phase agents."""
    
    @pytest.mark.asyncio
    async def test_design_main_agent_process(self):
        """Test design main agent processing."""
        with patch('app.core.llm_factory.LLMFactory.create_agent_llm') as mock_llm:
            mock_chain = AsyncMock()
            mock_chain.arun.return_value = """
            ## System Architecture
            
            ### Technology Stack
            - Backend: FastAPI
            - Database: PostgreSQL
            - Frontend: React
            
            ### API Design
            - POST /api/todos
            - GET /api/todos
            - PUT /api/todos/{id}
            - DELETE /api/todos/{id}
            """
            
            agent = DesignMainAgent()
            agent.chain = mock_chain
            
            result = await agent.process({
                "content": "Requirements document..."
            })
            
            assert result.agent_id == "design_main_agent"
            assert result.role == AgentRole.DESIGN_MAIN
            assert "System Architecture" in result.content
            assert "API Design" in result.content
    
    @pytest.mark.asyncio
    async def test_design_review_agent(self):
        """Test design review agent."""
        with patch('app.core.llm_factory.LLMFactory.create_agent_llm') as mock_llm:
            mock_chain = AsyncMock()
            mock_chain.arun.return_value = """
            {
                "approved": true,
                "overall_quality": 9,
                "feedback": "Solid architecture design",
                "issues": [],
                "suggestions": ["Consider adding caching layer"],
                "strengths": ["Good technology choices", "Clear API design"]
            }
            """
            
            agent = DesignReviewAgent()
            agent.review_chain = mock_chain
            
            review = await agent.review({
                "content": "## System Architecture..."
            })
            
            assert review.approved is True
            assert "Solid architecture" in review.feedback
            assert len(review.suggestions) == 1


class TestImplementationAgents:
    """Test implementation phase agents."""
    
    @pytest.mark.asyncio
    async def test_implementation_main_agent_process(self):
        """Test implementation main agent processing."""
        with patch('app.core.llm_factory.LLMFactory.create_agent_llm') as mock_llm:
            mock_chain = AsyncMock()
            mock_chain.arun.return_value = """
            ## Implementation Overview
            Todo API implementation with FastAPI
            
            ## File: src/main.py
            ```python
            from fastapi import FastAPI
            app = FastAPI()
            
            @app.get("/")
            def read_root():
                return {"message": "Todo API"}
            ```
            
            ## File: src/models/todo.py
            ```python
            from pydantic import BaseModel
            
            class Todo(BaseModel):
                id: int
                title: str
                completed: bool = False
            ```
            """
            
            agent = ImplementationMainAgent()
            agent.chain = mock_chain
            
            result = await agent.process({
                "content": "Design document..."
            })
            
            assert result.agent_id == "implementation_main_agent"
            assert result.role == AgentRole.IMPLEMENTATION_MAIN
            assert "Implementation Overview" in result.content
            assert "src/main.py" in result.content
            assert "FastAPI" in result.content
    
    @pytest.mark.asyncio
    async def test_implementation_review_agent(self):
        """Test implementation review agent."""
        with patch('app.core.llm_factory.LLMFactory.create_agent_llm') as mock_llm:
            mock_chain = AsyncMock()
            mock_chain.arun.return_value = """
            {
                "approved": false,
                "overall_quality": 6,
                "feedback": "Code needs error handling",
                "code_issues": [
                    {
                        "file": "src/main.py",
                        "line": "10-15", 
                        "issue": "Missing error handling",
                        "severity": "high",
                        "suggestion": "Add try-except blocks"
                    }
                ],
                "security_concerns": [],
                "performance_concerns": [],
                "suggestions": ["Add input validation", "Add logging"],
                "positive_aspects": ["Clean code structure"]
            }
            """
            
            agent = ImplementationReviewAgent()
            agent.review_chain = mock_chain
            
            review = await agent.review({
                "content": "## Implementation..."
            })
            
            assert review.approved is False
            assert "error handling" in review.feedback
            assert len(review.suggestions) == 2


class TestTestAgents:
    """Test test phase agents."""
    
    @pytest.mark.asyncio 
    async def test_test_main_agent_process(self):
        """Test test main agent processing."""
        with patch('app.core.llm_factory.LLMFactory.create_agent_llm') as mock_llm:
            mock_chain = AsyncMock()
            mock_chain.arun.return_value = """
            ## Test Strategy
            Unit tests for all endpoints and models
            
            ## File: tests/test_api.py
            ```python
            import pytest
            from fastapi.testclient import TestClient
            
            def test_read_root(client):
                response = client.get("/")
                assert response.status_code == 200
            ```
            
            ## File: tests/test_models.py
            ```python
            from src.models.todo import Todo
            
            def test_todo_model():
                todo = Todo(id=1, title="Test")
                assert todo.completed is False
            ```
            """
            
            agent = TestMainAgent()
            agent.chain = mock_chain
            
            result = await agent.process({
                "content": "Implementation code..."
            })
            
            assert result.agent_id == "test_main_agent"
            assert result.role == AgentRole.TEST_MAIN
            assert "Test Strategy" in result.content
            assert "test_api.py" in result.content
            assert "pytest" in result.content
    
    @pytest.mark.asyncio
    async def test_test_review_agent(self):
        """Test test review agent."""
        with patch('app.core.llm_factory.LLMFactory.create_agent_llm') as mock_llm:
            mock_chain = AsyncMock()
            mock_chain.arun.return_value = """
            {
                "approved": true,
                "overall_quality": 8,
                "feedback": "Good test coverage",
                "coverage_gaps": [
                    {
                        "area": "Error handling",
                        "missing_tests": "No tests for error cases",
                        "priority": "medium"
                    }
                ],
                "test_issues": [],
                "suggestions": ["Add edge case tests"],
                "strengths": ["Good happy path coverage"]
            }
            """
            
            agent = TestReviewAgent()
            agent.review_chain = mock_chain
            
            review = await agent.review({
                "content": "## Test Suite..."
            })
            
            assert review.approved is True
            assert "Good test coverage" in review.feedback
            assert len(review.suggestions) == 1