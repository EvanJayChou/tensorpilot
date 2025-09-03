# src/core/workflow/langgraph_nodes.py - LLM-powered nodes
from src.config.llm_config import get_llm_manager
from langchain_core.messages import HumanMessage, SystemMessage

async def problem_analysis_node(state: MathProblemState) -> MathProblemState:
    """Analyze the mathematical problem using LLM"""
    llm_manager = get_llm_manager()
    reasoning_llm = llm_manager.get_llm_for_task("reasoning")
    
    analysis_prompt = f"""
    Analyze this mathematical problem step by step:
    
    Problem: {state.problem}
    
    Provide detailed analysis including:
    1. Mathematical domain (algebra, calculus, geometry, etc.)
    2. Key concepts involved
    3. Problem complexity
    4. Recommended solution strategy
    5. Required tools or methods
    """
    
    messages = [
        SystemMessage(content="You are an expert mathematical analyst."),
        HumanMessage(content=analysis_prompt)
    ]
    
    analysis = await reasoning_llm.ainvoke(messages)
    
    return state.copy(update={
        "analysis": analysis.content,
        "current_step": state.current_step + 1,
        "steps": state.steps + [{"step": "analysis", "content": analysis.content}]
    })

async def synthesis_node(state: MathProblemState) -> MathProblemState:
    """Synthesize final solution using LLM"""
    llm_manager = get_llm_manager()
    creative_llm = llm_manager.get_llm_for_task("creative")
    
    synthesis_prompt = f"""
    Create a comprehensive solution based on the following information:
    
    Original Problem: {state.problem}
    Analysis: {state.analysis}
    Tool Results: {state.tool_results}
    Steps Taken: {state.steps}
    
    Provide:
    1. Clear, step-by-step solution
    2. Explanation of each step
    3. Final answer
    4. Alternative approaches if applicable
    5. Confidence level in the solution
    """
    
    messages = [
        SystemMessage(content="You are an expert mathematics tutor creating clear, educational solutions."),
        HumanMessage(content=synthesis_prompt)
    ]
    
    solution = await creative_llm.ainvoke(messages)
    
    return state.copy(update={
        "solution": solution.content,
        "current_step": state.current_step + 1,
        "steps": state.steps + [{"step": "synthesis", "content": solution.content}]
    })