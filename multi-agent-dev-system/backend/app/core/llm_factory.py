"""Factory for creating LLM instances."""
from typing import Optional, Any
from langchain.llms.base import BaseLLM
from langchain.chat_models.anthropic import ChatAnthropic
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import logging

from ..config import settings

logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory for creating LLM instances."""
    
    @staticmethod
    def create_llm(
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        streaming_callback: Optional[Any] = None
    ) -> BaseLLM:
        """Create an LLM instance.
        
        Args:
            model: Model name (defaults to settings)
            temperature: Temperature setting
            max_tokens: Maximum tokens
            streaming_callback: Callback for streaming
            
        Returns:
            LLM instance
        """
        model = model or settings.llm_model
        temperature = temperature or settings.llm_temperature
        max_tokens = max_tokens or settings.llm_max_tokens
        
        # Callbacks
        callbacks = []
        if streaming_callback:
            callbacks.append(streaming_callback)
        
        # Create Anthropic Claude instance
        if "claude" in model.lower():
            if not settings.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")
                
            # For now, we'll skip callbacks due to compatibility issues
            # They can be added during chain execution
            llm = ChatAnthropic(
                anthropic_api_key=settings.anthropic_api_key,
                model_name=model,
                temperature=temperature,
                max_tokens_to_sample=max_tokens
            )
            
            logger.info(f"Created Anthropic LLM with model: {model}")
            return llm
            
        else:
            raise ValueError(f"Unsupported model: {model}")
            
    @staticmethod
    def create_agent_llm(
        agent_role: str,
        streaming_callback: Optional[Any] = None
    ) -> BaseLLM:
        """Create an LLM for a specific agent role.
        
        Args:
            agent_role: Role of the agent
            streaming_callback: Callback for streaming
            
        Returns:
            LLM instance
        """
        # For now, all agents use the same model
        # In the future, we could use different models for different roles
        return LLMFactory.create_llm(streaming_callback=streaming_callback)