# src/core/agent/math_agent.py - Updated with LLM integration
from src.config.llm_config import get_llm, get_llm_manager
from langchain_core.messages import HumanMessage, SystemMessage

class MathAgent:
    def __init__(self):
        self.llm_manager = get_llm_manager()
        self.llm = self.llm_manager.llm
        self.workflow = self._build_workflow()
        
    async def solve_problem(self, problem: str, user_id: str = None) -> Dict[str, Any]:
        # Use LLM for initial problem understanding
        analysis_prompt = f"""
        You are a mathematical problem-solving assistant. Analyze the following problem:
        
        Problem: {problem}
        
        Provide:
        1. Problem type classification
        2. Required mathematical concepts
        3. Suggested solution approach
        4. Difficulty level (1-10)
        """
        
        messages = [
            SystemMessage(content="You are an expert mathematics tutor and problem solver."),
            HumanMessage(content=analysis_prompt)
        ]
        
        analysis_response = await self.llm.ainvoke(messages)
        
        # Continue with your existing workflow...
        initial_state = MathProblemState(
            problem=problem,
            user_id=user_id,
            llm_analysis=analysis_response.content,
            steps=[],
            current_step=0,
            tools_used=[],
            solution=None,
            confidence_score=0.0
        )
        
        result = await self.workflow.ainvoke(initial_state)
        return result