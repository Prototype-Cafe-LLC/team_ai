"""Base Agent class for all multi-agent system agents."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel
from langchain.schema import BaseMessage
from langchain.memory import ConversationBufferMemory
from langchain.llms.base import BaseLLM
from langchain.tools.base import BaseTool
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentRole(str, Enum):
    """Agent roles in the system."""
    CONDUCTOR = "conductor"
    REQUIREMENTS_MAIN = "requirements_main"
    REQUIREMENTS_REVIEWER = "requirements_reviewer"
    DESIGN_MAIN = "design_main"
    DESIGN_REVIEWER = "design_reviewer"
    IMPLEMENTATION_MAIN = "implementation_main"
    IMPLEMENTATION_REVIEWER = "implementation_reviewer"
    TEST_MAIN = "test_main"
    TEST_REVIEWER = "test_reviewer"


class AgentOutput(BaseModel):
    """Output from an agent."""
    agent_id: str
    agent_role: AgentRole
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class ReviewResult(BaseModel):
    """Result of a review."""
    approved: bool
    feedback: str
    suggestions: Optional[List[str]] = None
    reviewer_id: str
    timestamp: datetime


class BaseAgent(ABC):
    """Base class for all agents in the multi-agent system."""
    
    def __init__(
        self,
        agent_id: str,
        role: AgentRole,
        llm: BaseLLM,
        tools: Optional[List[BaseTool]] = None,
        memory: Optional[ConversationBufferMemory] = None,
        streaming_callback: Optional[Any] = None
    ):
        """Initialize the base agent.
        
        Args:
            agent_id: Unique identifier for the agent
            role: Role of the agent in the system
            llm: Language model to use
            tools: List of tools available to the agent
            memory: Memory to maintain context
            streaming_callback: Callback for streaming outputs
        """
        self.agent_id = agent_id
        self.role = role
        self.llm = llm
        self.tools = tools or []
        self.memory = memory or ConversationBufferMemory()
        self.streaming_callback = streaming_callback
        
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> AgentOutput:
        """Process input and generate output.
        
        Args:
            input_data: Input data for the agent to process
            
        Returns:
            AgentOutput containing the agent's response
        """
        pass
    
    @abstractmethod
    async def review(self, work_product: Dict[str, Any]) -> ReviewResult:
        """Review work product from another agent.
        
        Args:
            work_product: Work product to review
            
        Returns:
            ReviewResult with approval status and feedback
        """
        pass
    
    async def revise(self, original: Dict[str, Any], feedback: str) -> AgentOutput:
        """Revise work based on feedback.
        
        Args:
            original: Original work product
            feedback: Feedback from reviewer
            
        Returns:
            AgentOutput with revised content
        """
        revision_input = {
            "original": original,
            "feedback": feedback,
            "instruction": "Please revise your work based on the feedback provided."
        }
        return await self.process(revision_input)
    
    def _create_agent_output(self, content: str, metadata: Optional[Dict] = None) -> AgentOutput:
        """Create an AgentOutput object.
        
        Args:
            content: The output content
            metadata: Optional metadata
            
        Returns:
            AgentOutput object
        """
        return AgentOutput(
            agent_id=self.agent_id,
            agent_role=self.role,
            content=content,
            timestamp=datetime.utcnow(),
            metadata=metadata
        )
    
    async def _stream_output(self, content: str):
        """Stream output if callback is available.
        
        Args:
            content: Content to stream
        """
        if self.streaming_callback:
            await self.streaming_callback(self.agent_id, content)
    
    def add_tool(self, tool: BaseTool):
        """Add a tool to the agent's toolkit.
        
        Args:
            tool: Tool to add
        """
        self.tools.append(tool)
    
    def clear_memory(self):
        """Clear the agent's memory."""
        self.memory.clear()
    
    def get_memory_variables(self) -> Dict:
        """Get current memory variables.
        
        Returns:
            Dictionary of memory variables
        """
        return self.memory.load_memory_variables({})