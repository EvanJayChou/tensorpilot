# src/config/settings.py - Update your main settings
from pydantic_settings import BaseSettings
from src.config.llm_config import AzureOpenAISettings

class Settings(BaseSettings):
    # Your existing settings...
    DEBUG: bool = False
    DATABASE_URL: str
    REDIS_URL: str
    
    # Include Azure OpenAI settings
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.azure_openai = AzureOpenAISettings()