"""Agent module for multi-agent system."""
from .base import BaseAgent, AgentRole, AgentOutput, ReviewResult
from .requirements import RequirementsMainAgent, RequirementsReviewAgent
from .design import DesignMainAgent, DesignReviewAgent
from .implementation import ImplementationMainAgent, ImplementationReviewAgent
from .test import TestMainAgent, TestReviewAgent

__all__ = [
    "BaseAgent", 
    "AgentRole", 
    "AgentOutput", 
    "ReviewResult",
    "RequirementsMainAgent",
    "RequirementsReviewAgent",
    "DesignMainAgent",
    "DesignReviewAgent",
    "ImplementationMainAgent",
    "ImplementationReviewAgent",
    "TestMainAgent",
    "TestReviewAgent"
]