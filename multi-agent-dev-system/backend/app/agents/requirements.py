"""Requirements phase agents."""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from .base import BaseAgent, AgentRole, AgentOutput, ReviewResult
from ..core.llm_factory import LLMFactory

logger = logging.getLogger(__name__)


class RequirementsMainAgent(BaseAgent):
    """Main agent for requirements definition phase."""
    
    def __init__(self, streaming_callback: Optional[Any] = None):
        """Initialize requirements main agent."""
        llm = LLMFactory.create_agent_llm(
            AgentRole.REQUIREMENTS_MAIN,
            streaming_callback
        )
        
        super().__init__(
            agent_id="requirements_main_agent",
            role=AgentRole.REQUIREMENTS_MAIN,
            llm=llm,
            streaming_callback=streaming_callback
        )
        
        # Define prompt template
        self.prompt_template = PromptTemplate(
            input_variables=["requirements"],
            template="""You are an expert requirements analyst for software development projects.

Given the following project requirements:
{requirements}

Please create a comprehensive requirements definition document that includes:

1. **Functional Requirements**
   - List all features and capabilities the system must have
   - Group them by priority (Must Have, Should Have, Nice to Have)
   - Be specific and measurable

2. **Non-Functional Requirements**
   - Performance requirements
   - Security requirements
   - Usability requirements
   - Scalability requirements
   - Compatibility requirements

3. **User Stories**
   - Create user stories in the format: "As a [role], I want [feature] so that [benefit]"
   - Include acceptance criteria for each story

4. **Use Cases**
   - Define main use cases
   - Include actors, preconditions, main flow, and postconditions

5. **Constraints and Assumptions**
   - Technical constraints
   - Business constraints
   - Key assumptions

6. **Success Criteria**
   - Define what success looks like for this project
   - Include measurable KPIs

Format the output as a well-structured document with clear sections and subsections.
"""
        )
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
        
    async def process(self, input_data: Dict[str, Any]) -> AgentOutput:
        """Process requirements and generate requirements document.
        
        Args:
            input_data: Should contain 'requirements' key
            
        Returns:
            AgentOutput with requirements document
        """
        try:
            requirements = input_data.get("requirements", "")
            
            if not requirements:
                raise ValueError("No requirements provided")
                
            # Generate requirements document
            await self._stream_output("Analyzing project requirements...")
            
            result = await self.chain.arun(requirements=requirements)
            
            await self._stream_output("Requirements analysis complete.")
            
            return self._create_agent_output(
                content=result,
                metadata={
                    "phase": "requirements",
                    "input_length": len(requirements),
                    "output_length": len(result)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in requirements processing: {str(e)}")
            return self._create_agent_output(
                content=f"Error processing requirements: {str(e)}",
                metadata={"error": True}
            )
            
    async def review(self, work_product: Dict[str, Any]) -> ReviewResult:
        """Not applicable for main agent."""
        raise NotImplementedError("Main agent does not review")


class RequirementsReviewAgent(BaseAgent):
    """Review agent for requirements definition phase."""
    
    def __init__(self, streaming_callback: Optional[Any] = None):
        """Initialize requirements review agent."""
        llm = LLMFactory.create_agent_llm(
            AgentRole.REQUIREMENTS_REVIEWER,
            streaming_callback
        )
        
        super().__init__(
            agent_id="requirements_review_agent",
            role=AgentRole.REQUIREMENTS_REVIEWER,
            llm=llm,
            streaming_callback=streaming_callback
        )
        
        # Define review prompt template
        self.review_prompt = PromptTemplate(
            input_variables=["requirements_document"],
            template="""You are an expert requirements reviewer for software development projects.

Please review the following requirements document:

{requirements_document}

Evaluate the document based on these criteria:
1. **Completeness**: Are all necessary sections present and well-developed?
2. **Clarity**: Are requirements clear, unambiguous, and specific?
3. **Feasibility**: Are the requirements technically achievable?
4. **Testability**: Can each requirement be tested and verified?
5. **Consistency**: Are there any conflicting requirements?
6. **Prioritization**: Are requirements properly prioritized?

Provide your review in the following JSON format:
{{
    "approved": true/false,
    "overall_quality": "score from 1-10",
    "feedback": "detailed feedback explaining the decision",
    "issues": [
        {{
            "section": "section name",
            "issue": "description of the issue",
            "severity": "high/medium/low"
        }}
    ],
    "suggestions": [
        "specific improvement suggestion 1",
        "specific improvement suggestion 2"
    ]
}}

Be constructive in your feedback and specific about what needs improvement.
"""
        )
        
        self.review_chain = LLMChain(llm=self.llm, prompt=self.review_prompt)
        
    async def process(self, input_data: Dict[str, Any]) -> AgentOutput:
        """Not applicable for review agent."""
        raise NotImplementedError("Review agent does not process initial input")
        
    async def review(self, work_product: Dict[str, Any]) -> ReviewResult:
        """Review requirements document.
        
        Args:
            work_product: Should contain 'content' key with requirements document
            
        Returns:
            ReviewResult with approval status and feedback
        """
        try:
            document = work_product.get("content", "")
            
            if not document:
                raise ValueError("No document provided for review")
                
            await self._stream_output("Reviewing requirements document...")
            
            # Get review from LLM
            review_json = await self.review_chain.arun(
                requirements_document=document
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
                    
            await self._stream_output("Review complete.")
            
            return ReviewResult(
                approved=review_data.get("approved", False),
                feedback=review_data.get("feedback", ""),
                suggestions=review_data.get("suggestions", []),
                reviewer_id=self.agent_id,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error in requirements review: {str(e)}")
            return ReviewResult(
                approved=False,
                feedback=f"Error during review: {str(e)}",
                suggestions=[],
                reviewer_id=self.agent_id,
                timestamp=datetime.utcnow()
            )