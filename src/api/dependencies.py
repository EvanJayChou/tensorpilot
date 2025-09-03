# src/api/dependencies.py - Dependency injection
from fastapi import Depends
from src.config.llm_config import get_llm_manager, LLMManager

def get_llm_dependency() -> LLMManager:
    """FastAPI dependency for LLM manager"""
    return get_llm_manager()