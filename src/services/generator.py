from typing import List, Dict, Optional
from src.services.vector_search import VectorSearchService
from src.services.llm_service import LLMService
from src.services.reranker import RerankerService
from src.core.config import settings

class MedicalRAGGenerator:
    def __init__(self):
        self.vector_search = VectorSearchService()
        self.llm = LLMService()
        self.reranker = RerankerService()
    
    def format_context(self, documents: List[Dict]) -> str:
        if not documents:
            return "Không tìm thấy thông tin liên quan."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            rerank_score = doc.get('rerank_score', 0)
            original_score = doc.get('original_score', doc.get('score', 0))
            
            context_part = f"""
=== Tài liệu {i} ===
Điểm Rerank: {rerank_score:.3f} | Điểm gốc: {original_score:.3f}
Tiêu đề: {doc.get('title', 'N/A')}
Danh mục: {doc.get('category', 'N/A')}
Đề mục: {doc.get('header', 'N/A')}

Nội dung:
{doc.get('text', '')}
"""
            context_parts.append(context_part.strip())
        
        return "\n\n".join(context_parts)
    
    def ask(
        self,
        query: str,
        top_k: int = 20,
        score_threshold: float = 0.5,
        use_query_expansion: bool = True,
        rerank_top_n: int = 5
    ) -> Dict:
        if use_query_expansion:
            queries = self.llm.generate_similar_queries(query, num_queries=3)
            print(f"Generated {len(queries)} queries:")
            for i, q in enumerate(queries, 1):
                print(f"   {i}. {q}")
        else:
            queries = [query]
        
        print(f"\nSearching with {len(queries)} queries (top_k={top_k})...")
        if len(queries) > 1:
            documents = self.vector_search.search_with_multiple_queries(
                queries, top_k, score_threshold
            )
        else:
            documents = self.vector_search.search(
                query, top_k, score_threshold
            )
        
        print(f"Found {len(documents)} unique documents")
        
        if not documents:
            return {
                "query": query,
                "answer": "Xin lỗi, tôi không tìm thấy thông tin liên quan đến câu hỏi của bạn. Bạn có thể diễn đạt lại câu hỏi hoặc liên hệ bác sĩ để được tư vấn trực tiếp.",
                "documents": [],
                "context": "",
                "num_documents": 0,
                "num_reranked": 0
            }
        
        print(f"\nReranking to top {rerank_top_n}...")
        reranked_documents = self.reranker.rerank_with_fallback(
            query, documents, top_n=rerank_top_n
        )
        
        print(f"Reranked to {len(reranked_documents)} documents")
        
        context = self.format_context(reranked_documents)
        
        print(f"\nGenerating answer...")
        answer = self.llm.generate_answer(query, context)

        print(f"Answer generated!\n")

        return {
            "query": query,
            "answer": answer,
            "documents": reranked_documents,
            "all_documents": documents,
            "context": context,
            "num_documents": len(documents),
            "num_reranked": len(reranked_documents),
            "queries_used": queries
        }
    
    def search_only(
        self,
        query: str,
        top_k: int = 20,
        score_threshold: float = 0.5,
        use_rerank: bool = True,
        rerank_top_n: int = 5
    ) -> List[Dict]:
        documents = self.vector_search.search(query, top_k, score_threshold)
        
        if use_rerank and documents:
            documents = self.reranker.rerank_with_fallback(
                query, documents, top_n=rerank_top_n
            )
        
        return documents

rag_generator = MedicalRAGGenerator()