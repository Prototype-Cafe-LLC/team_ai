"""Test phase agents."""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from .base import BaseAgent, AgentRole, AgentOutput, ReviewResult
from ..core.llm_factory import LLMFactory

logger = logging.getLogger(__name__)


class TestMainAgent(BaseAgent):
    """Main agent for test phase."""
    
    def __init__(self, streaming_callback: Optional[Any] = None):
        """Initialize test main agent."""
        llm = LLMFactory.create_agent_llm(
            AgentRole.TEST_MAIN,
            streaming_callback
        )
        
        super().__init__(
            agent_id="test_main_agent",
            role=AgentRole.TEST_MAIN,
            llm=llm,
            streaming_callback=streaming_callback
        )
        
        # Define prompt template
        self.prompt_template = PromptTemplate(
            input_variables=["implementation_code"],
            template="""You are an expert QA engineer and test automation specialist.

Based on the following implementation:
{implementation_code}

Please create a comprehensive test suite that includes:

1. **Test Strategy**
   - Overall testing approach
   - Test levels (unit, integration, e2e)
   - Test coverage goals
   - Testing tools and frameworks to use

2. **Unit Tests**
   - Test cases for individual functions/methods
   - Edge cases and boundary conditions
   - Mock dependencies appropriately
   - Aim for high code coverage

3. **Integration Tests**
   - Test component interactions
   - Database integration tests
   - API endpoint tests
   - External service integration tests

4. **End-to-End Tests**
   - User workflow tests
   - Critical path testing
   - UI automation tests (if applicable)

5. **Test Data**
   - Test data setup
   - Fixtures and factories
   - Test database seeding

6. **Performance Tests**
   - Load testing scenarios
   - Performance benchmarks
   - Stress test cases

7. **Security Tests**
   - Basic security test cases
   - Input validation tests
   - Authentication/authorization tests

Format the output as follows:
- Start with the test strategy overview
- Then provide test files with their paths and content
- Use markdown code blocks with appropriate language tags
- Include test configuration files

Example format:
```
## Test Strategy
[Overview of testing approach]

## File: tests/unit/test_user_model.py
```python
[test code]
```

## File: tests/integration/test_api.py
```python
[test code]
```
```

Create practical, runnable tests that thoroughly validate the implementation.
"""
        )
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
        
    async def process(self, input_data: Dict[str, Any]) -> AgentOutput:
        """Process implementation and generate test suite.
        
        Args:
            input_data: Should contain implementation code
            
        Returns:
            AgentOutput with test suite
        """
        try:
            # Get implementation from previous phase
            implementation = input_data.get("content", "")
            
            if not implementation:
                raise ValueError("No implementation provided")
                
            await self._stream_output("Creating test suite...")
            
            result = await self.chain.arun(
                implementation_code=implementation
            )
            
            await self._stream_output("Test suite complete.")
            
            return self._create_agent_output(
                content=result,
                metadata={
                    "phase": "test",
                    "input_length": len(implementation),
                    "output_length": len(result)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in test processing: {str(e)}")
            return self._create_agent_output(
                content=f"Error processing tests: {str(e)}",
                metadata={"error": True}
            )
            
    async def review(self, work_product: Dict[str, Any]) -> ReviewResult:
        """Not applicable for main agent."""
        raise NotImplementedError("Main agent does not review")


class TestReviewAgent(BaseAgent):
    """Review agent for test phase."""
    
    def __init__(self, streaming_callback: Optional[Any] = None):
        """Initialize test review agent."""
        llm = LLMFactory.create_agent_llm(
            AgentRole.TEST_REVIEWER,
            streaming_callback
        )
        
        super().__init__(
            agent_id="test_review_agent",
            role=AgentRole.TEST_REVIEWER,
            llm=llm,
            streaming_callback=streaming_callback
        )
        
        # Define review prompt template
        self.review_prompt = PromptTemplate(
            input_variables=["test_suite"],
            template="""You are an expert QA lead and test architect.

Please review the following test suite:

{test_suite}

Evaluate the test suite based on these criteria:
1. **Coverage**: Are all important code paths tested?
2. **Test Quality**: Are tests well-written and meaningful?
3. **Edge Cases**: Are edge cases and error conditions tested?
4. **Test Organization**: Are tests well-organized and maintainable?
5. **Assertions**: Are assertions specific and comprehensive?
6. **Test Independence**: Are tests independent and isolated?
7. **Performance**: Will tests run efficiently?
8. **Completeness**: Are all test types covered (unit, integration, e2e)?

Provide your review in the following JSON format:
{{
    "approved": true/false,
    "overall_quality": "score from 1-10",
    "feedback": "detailed feedback explaining the decision",
    "coverage_gaps": [
        {{
            "area": "code area or functionality",
            "missing_tests": "what tests are missing",
            "priority": "high/medium/low"
        }}
    ],
    "test_issues": [
        {{
            "test_file": "file name",
            "issue": "description of the issue",
            "severity": "high/medium/low"
        }}
    ],
    "suggestions": [
        "improvement suggestion 1",
        "improvement suggestion 2"
    ],
    "strengths": [
        "what was done well"
    ]
}}

Focus on ensuring comprehensive test coverage and test quality.
"""
        )
        
        self.review_chain = LLMChain(llm=self.llm, prompt=self.review_prompt)
        
    async def process(self, input_data: Dict[str, Any]) -> AgentOutput:
        """Not applicable for review agent."""
        raise NotImplementedError("Review agent does not process initial input")
        
    async def review(self, work_product: Dict[str, Any]) -> ReviewResult:
        """Review test suite.
        
        Args:
            work_product: Should contain 'content' key with test suite
            
        Returns:
            ReviewResult with approval status and feedback
        """
        try:
            test_suite = work_product.get("content", "")
            
            if not test_suite:
                raise ValueError("No test suite provided for review")
                
            await self._stream_output("Reviewing test suite...")
            
            # Get review from LLM
            review_json = await self.review_chain.arun(
                test_suite=test_suite
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
                    
            await self._stream_output("Test review complete.")
            
            return ReviewResult(
                approved=review_data.get("approved", False),
                feedback=review_data.get("feedback", ""),
                suggestions=review_data.get("suggestions", []),
                reviewer_id=self.agent_id,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error in test review: {str(e)}")
            return ReviewResult(
                approved=False,
                feedback=f"Error during review: {str(e)}",
                suggestions=[],
                reviewer_id=self.agent_id,
                timestamp=datetime.utcnow()
            )