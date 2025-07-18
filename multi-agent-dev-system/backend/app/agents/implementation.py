"""Implementation phase agents."""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from .base import BaseAgent, AgentRole, AgentOutput, ReviewResult
from ..core.llm_factory import LLMFactory

logger = logging.getLogger(__name__)


class ImplementationMainAgent(BaseAgent):
    """Main agent for implementation phase."""
    
    def __init__(self, streaming_callback: Optional[Any] = None):
        """Initialize implementation main agent."""
        llm = LLMFactory.create_agent_llm(
            AgentRole.IMPLEMENTATION_MAIN,
            streaming_callback
        )
        
        super().__init__(
            agent_id="implementation_main_agent",
            role=AgentRole.IMPLEMENTATION_MAIN,
            llm=llm,
            streaming_callback=streaming_callback
        )
        
        # Define prompt template
        self.prompt_template = PromptTemplate(
            input_variables=["design_document"],
            template="""You are an expert software developer responsible for implementing code based on design specifications.

Based on the following design document:
{design_document}

Please create the implementation following these guidelines:

1. **Code Structure**
   - Create a clear directory structure
   - Implement all major components described in the design
   - Follow the architecture patterns specified

2. **Code Quality**
   - Write clean, readable, and well-documented code
   - Follow language-specific best practices
   - Include appropriate error handling
   - Add logging where necessary

3. **Implementation Details**
   - Implement the core business logic
   - Create necessary data models/schemas
   - Implement API endpoints if specified
   - Add configuration management
   - Include database migrations if needed

4. **Documentation**
   - Add inline code comments
   - Include README files
   - Document API endpoints
   - Add setup instructions

5. **Key Files to Generate**
   - Main application entry point
   - Core business logic modules
   - Data models
   - API routes/controllers
   - Configuration files
   - Docker/deployment files if applicable

Format the output as follows:
- Start with a brief implementation overview
- Then provide each file with its path and content
- Use markdown code blocks with appropriate language tags
- Include clear file separators

Example format:
```
## Implementation Overview
[Brief description]

## File: src/main.py
```python
[code content]
```

## File: src/models/user.py
```python
[code content]
```
```

Focus on creating a working implementation that matches the design specifications.
"""
        )
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
        
    async def process(self, input_data: Dict[str, Any]) -> AgentOutput:
        """Process design and generate implementation.
        
        Args:
            input_data: Should contain design document
            
        Returns:
            AgentOutput with implementation code
        """
        try:
            # Get design document from previous phase
            design_doc = input_data.get("content", "")
            
            if not design_doc:
                raise ValueError("No design document provided")
                
            await self._stream_output("Generating implementation code...")
            
            result = await self.chain.arun(
                design_document=design_doc
            )
            
            await self._stream_output("Implementation complete.")
            
            return self._create_agent_output(
                content=result,
                metadata={
                    "phase": "implementation",
                    "input_length": len(design_doc),
                    "output_length": len(result)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in implementation processing: {str(e)}")
            return self._create_agent_output(
                content=f"Error processing implementation: {str(e)}",
                metadata={"error": True}
            )
            
    async def review(self, work_product: Dict[str, Any]) -> ReviewResult:
        """Not applicable for main agent."""
        raise NotImplementedError("Main agent does not review")


class ImplementationReviewAgent(BaseAgent):
    """Review agent for implementation phase."""
    
    def __init__(self, streaming_callback: Optional[Any] = None):
        """Initialize implementation review agent."""
        llm = LLMFactory.create_agent_llm(
            AgentRole.IMPLEMENTATION_REVIEWER,
            streaming_callback
        )
        
        super().__init__(
            agent_id="implementation_review_agent",
            role=AgentRole.IMPLEMENTATION_REVIEWER,
            llm=llm,
            streaming_callback=streaming_callback
        )
        
        # Define review prompt template
        self.review_prompt = PromptTemplate(
            input_variables=["implementation_code"],
            template="""You are an expert code reviewer.

Please review the following implementation:

{implementation_code}

Evaluate the code based on these criteria:
1. **Correctness**: Does the code implement the design correctly?
2. **Code Quality**: Is the code clean, readable, and maintainable?
3. **Best Practices**: Does it follow language-specific best practices?
4. **Error Handling**: Is error handling appropriate and comprehensive?
5. **Security**: Are there any security vulnerabilities?
6. **Performance**: Are there obvious performance issues?
7. **Testing**: Is the code testable?
8. **Documentation**: Is the code well-documented?

Provide your review in the following JSON format:
{{
    "approved": true/false,
    "overall_quality": "score from 1-10",
    "feedback": "detailed feedback explaining the decision",
    "code_issues": [
        {{
            "file": "file path",
            "line": "line number or range",
            "issue": "description of the issue",
            "severity": "high/medium/low",
            "suggestion": "how to fix it"
        }}
    ],
    "security_concerns": [
        "any security issues found"
    ],
    "performance_concerns": [
        "any performance issues found"
    ],
    "suggestions": [
        "general improvement suggestions"
    ],
    "positive_aspects": [
        "what was done well"
    ]
}}

Be specific about issues and provide actionable feedback.
"""
        )
        
        self.review_chain = LLMChain(llm=self.llm, prompt=self.review_prompt)
        
    async def process(self, input_data: Dict[str, Any]) -> AgentOutput:
        """Not applicable for review agent."""
        raise NotImplementedError("Review agent does not process initial input")
        
    async def review(self, work_product: Dict[str, Any]) -> ReviewResult:
        """Review implementation code.
        
        Args:
            work_product: Should contain 'content' key with implementation
            
        Returns:
            ReviewResult with approval status and feedback
        """
        try:
            code = work_product.get("content", "")
            
            if not code:
                raise ValueError("No code provided for review")
                
            await self._stream_output("Reviewing implementation code...")
            
            # Get review from LLM
            review_json = await self.review_chain.arun(
                implementation_code=code
            )
            
            # Parse JSON response
            try:
                review_data = json.loads(review_json)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract the JSON part
                import re
                json_match = re.search(r'\{.*\}', review_json, re.DOTALL)
                if json_match:
                    review_data = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse review response as JSON")
                    
            await self._stream_output("Code review complete.")
            
            return ReviewResult(
                approved=review_data.get("approved", False),
                feedback=review_data.get("feedback", ""),
                suggestions=review_data.get("suggestions", []),
                reviewer_id=self.agent_id,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error in implementation review: {str(e)}")
            return ReviewResult(
                approved=False,
                feedback=f"Error during review: {str(e)}",
                suggestions=[],
                reviewer_id=self.agent_id,
                timestamp=datetime.utcnow()
            )