# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
    AZURE_OPENAI_VERSION = "2024-02-15-preview"
    MODEL_NAME = "gpt-4"
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    REDIS_URL = os.getenv("REDIS_URL")
    
    # Sales Framework Configurations
    QUALIFICATION_THRESHOLD = 70
    MAX_QUESTIONS_PER_SESSION = 15