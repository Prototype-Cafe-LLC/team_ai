"""Design phase agents."""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from .base import BaseAgent, AgentRole, AgentOutput, ReviewResult
from ..core.llm_factory import LLMFactory

logger = logging.getLogger(__name__)


class DesignMainAgent(BaseAgent):
    """Main agent for design phase."""
    
    def __init__(self, streaming_callback: Optional[Any] = None):
        """Initialize design main agent."""
        llm = LLMFactory.create_agent_llm(
            AgentRole.DESIGN_MAIN,
            streaming_callback
        )
        
        super().__init__(
            agent_id="design_main_agent",
            role=AgentRole.DESIGN_MAIN,
            llm=llm,
            streaming_callback=streaming_callback
        )
        
        # Define prompt template
        self.prompt_template = PromptTemplate(
            input_variables=["requirements_document"],
            template="""You are an expert software architect and system designer.

Based on the following requirements document:
{requirements_document}

Please create a comprehensive technical design document that includes:

1. **System Architecture**
   - High-level architecture diagram (describe in text/mermaid format)
   - Component breakdown
   - Technology stack recommendations with justifications
   - Deployment architecture

2. **Data Design**
   - Data models and schemas
   - Database design (tables, relationships)
   - Data flow diagrams
   - Storage requirements

3. **API Design**
   - REST API endpoints (if applicable)
   - Request/response formats
   - Authentication and authorization approach
   - API versioning strategy

4. **Component Design**
   - Detailed design for each major component
   - Class diagrams (in text/mermaid format)
   - Sequence diagrams for key workflows
   - Interface definitions

5. **Security Design**
   - Security architecture
   - Authentication/authorization mechanisms
   - Data encryption approach
   - Security best practices

6. **Performance Considerations**
   - Caching strategy
   - Load balancing approach
   - Scalability design
   - Performance optimization techniques

7. **Integration Points**
   - External system integrations
   - Third-party services
   - Integration patterns

8. **Error Handling and Logging**
   - Error handling strategy
   - Logging architecture
   - Monitoring approach

Format the output as a well-structured document with clear sections.
Use Mermaid syntax for diagrams where appropriate.
"""
        )
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
        
    async def process(self, input_data: Dict[str, Any]) -> AgentOutput:
        """Process requirements and generate design document.
        
        Args:
            input_data: Should contain requirements document
            
        Returns:
            AgentOutput with design document
        """
        try:
            # Get requirements document from previous phase
            requirements_doc = input_data.get("content", "")
            
            if not requirements_doc:
                raise ValueError("No requirements document provided")
                
            await self._stream_output("Creating system design...")
            
            result = await self.chain.arun(
                requirements_document=requirements_doc
            )
            
            await self._stream_output("System design complete.")
            
            return self._create_agent_output(
                content=result,
                metadata={
                    "phase": "design",
                    "input_length": len(requirements_doc),
                    "output_length": len(result)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in design processing: {str(e)}")
            return self._create_agent_output(
                content=f"Error processing design: {str(e)}",
                metadata={"error": True}
            )
            
    async def review(self, work_product: Dict[str, Any]) -> ReviewResult:
        """Not applicable for main agent."""
        raise NotImplementedError("Main agent does not review")


class DesignReviewAgent(BaseAgent):
    """Review agent for design phase."""
    
    def __init__(self, streaming_callback: Optional[Any] = None):
        """Initialize design review agent."""
        llm = LLMFactory.create_agent_llm(
            AgentRole.DESIGN_REVIEWER,
            streaming_callback
        )
        
        super().__init__(
            agent_id="design_review_agent",
            role=AgentRole.DESIGN_REVIEWER,
            llm=llm,
            streaming_callback=streaming_callback
        )
        
        # Define review prompt template
        self.review_prompt = PromptTemplate(
            input_variables=["design_document"],
            template="""You are an expert software architecture reviewer.

Please review the following design document:

{design_document}

Evaluate the document based on these criteria:
1. **Completeness**: Are all necessary design aspects covered?
2. **Feasibility**: Is the design technically achievable?
3. **Scalability**: Will the design scale well?
4. **Security**: Are security concerns properly addressed?
5. **Performance**: Are performance considerations adequate?
6. **Maintainability**: Is the design maintainable and extensible?
7. **Best Practices**: Does it follow industry best practices?
8. **Alignment**: Does it align with the requirements?

Provide your review in the following JSON format:
{{
    "approved": true/false,
    "overall_quality": "score from 1-10",
    "feedback": "detailed feedback explaining the decision",
    "issues": [
        {{
            "area": "area of concern",
            "issue": "description of the issue",
            "severity": "high/medium/low",
            "recommendation": "specific recommendation"
        }}
    ],
    "suggestions": [
        "specific improvement suggestion 1",
        "specific improvement suggestion 2"
    ],
    "strengths": [
        "what was done well"
    ]
}}

Be constructive and specific in your feedback.
"""
        )
        
        self.review_chain = LLMChain(llm=self.llm, prompt=self.review_prompt)
        
    async def process(self, input_data: Dict[str, Any]) -> AgentOutput:
        """Not applicable for review agent."""
        raise NotImplementedError("Review agent does not process initial input")
        
    async def review(self, work_product: Dict[str, Any]) -> ReviewResult:
        """Review design document.
        
        Args:
            work_product: Should contain 'content' key with design document
            
        Returns:
            ReviewResult with approval status and feedback
        """
        try:
            document = work_product.get("content", "")
            
            if not document:
                raise ValueError("No document provided for review")
                
            await self._stream_output("Reviewing design document...")
            
            # Get review from LLM
            review_json = await self.review_chain.arun(
                design_document=document
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
                    
            await self._stream_output("Design review complete.")
            
            return ReviewResult(
                approved=review_data.get("approved", False),
                feedback=review_data.get("feedback", ""),
                suggestions=review_data.get("suggestions", []),
                reviewer_id=self.agent_id,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error in design review: {str(e)}")
            return ReviewResult(
                approved=False,
                feedback=f"Error during review: {str(e)}",
                suggestions=[],
                reviewer_id=self.agent_id,
                timestamp=datetime.utcnow()
            )