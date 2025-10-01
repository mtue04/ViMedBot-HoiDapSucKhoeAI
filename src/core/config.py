import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Settings:
    QDRANT_URL: str = os.getenv("QDRANT_URL", "").strip()
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "").strip()
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "med_vn_rag")
    
    GEMINI_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.0-flash")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_APIS_LIST: List[str] = os.getenv('APIS_GEMINI_LIST', '').split(',')
    
    RERANKER_MODEL: str = os.getenv("MODEL_RERANKER", "rerank-multilingual-v3.0")
    COHERE_API_KEYS: List[str] = os.getenv('APIS_COHERE_LIST', '').split(',')
    
    EMBEDDING_MODEL: str = os.getenv(
        "MODEL_EMBEDDING", 
        "Dqdung205/medical_vietnamese_embedding"
    )
    
    DEFAULT_TOP_K: int = 20
    DEFAULT_SCORE_THRESHOLD: float = 0.5
    RERANK_TOP_N: int = 5

class APIKeyManager:
    def __init__(self, api_keys: List[str]):
        self.api_keys = [key.strip() for key in api_keys if key.strip()]
        self.current_index = 0
        
    def get_next_key(self) -> str:
        if not self.api_keys:
            raise ValueError("No API keys available")
        
        key = self.api_keys[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        return key
    
    def get_all_keys(self) -> List[str]:
        return self.api_keys.copy()

settings = Settings()
gemini_key_manager = APIKeyManager(settings.GEMINI_APIS_LIST)
cohere_key_manager = APIKeyManager(settings.COHERE_API_KEYS)