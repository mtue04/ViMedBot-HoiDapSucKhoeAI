from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from src.services.generator import rag_generator
import time

router = APIRouter()

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="Câu hỏi của người dùng")
    conversation_id: Optional[str] = None
    use_query_expansion: bool = True
    top_k: int = Field(default=12, ge=1, le=50)
    rerank_top_n: int = Field(default=5, ge=1, le=20)

class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    processing_time: float
    metadata: Dict[str, Any]

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=10, ge=1, le=50)
    use_rerank: bool = True
    rerank_top_n: int = Field(default=5, ge=1, le=20)

class DocumentResult(BaseModel):
    title: str
    category: str
    text: str
    score: float
    rerank_score: Optional[float] = None

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        start_time = time.time()

        # generate conversation_id (if not provided)
        conversation_id = request.conversation_id or f"conv_{int(time.time() * 1000)}"
        
        # call RAG system
        result = rag_generator.ask(
            query=request.message,
            top_k=request.top_k,
            use_query_expansion=request.use_query_expansion,
            rerank_top_n=request.rerank_top_n
        )
        
        processing_time = time.time() - start_time
        
        return ChatResponse(
            answer=result['answer'],
            conversation_id=conversation_id,
            processing_time=round(processing_time, 2),
            metadata={
                "num_documents_found": result['num_documents'],
                "num_documents_used": result['num_reranked'],
                "queries_generated": len(result.get('queries_used', [])),
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý: {str(e)}")

@router.post("/search", response_model=List[DocumentResult])
async def search(request: SearchRequest):
    try:
        documents = rag_generator.search_only(
            query=request.query,
            top_k=request.top_k,
            use_rerank=request.use_rerank,
            rerank_top_n=request.rerank_top_n
        )
        
        return [
            DocumentResult(
                title=doc.get('title', 'N/A'),
                category=doc.get('category', 'N/A'),
                text=doc.get('text', '')[:500] + '...',
                score=doc.get('original_score', doc.get('score', 0)),
                rerank_score=doc.get('rerank_score')
            )
            for doc in documents
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi search: {str(e)}")

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ViMedBot API",
        "version": "1.0.0"
    }

@router.get("/stats")
async def get_stats():
    try:
        # Test a simple query to check system status
        test_result = rag_generator.search_only("test", top_k=1, use_rerank=False)
        
        return {
            "status": "operational",
            "vector_search": "ok" if test_result is not None else "error",
            "services": {
                "qdrant": "connected",
                "gemini": "configured",
                "cohere": "configured"
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e)
        }