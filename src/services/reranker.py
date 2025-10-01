import cohere
from typing import List, Dict
from src.core.config import settings, cohere_key_manager

class RerankerService:
    def __init__(self):
        self.model_name = settings.RERANKER_MODEL
        self.top_n = settings.RERANK_TOP_N
        self.key_manager = cohere_key_manager
    
    def rerank(
        self, 
        query: str, 
        documents: List[Dict],
        top_n: int = None
    ) -> List[Dict]:
        if not documents:
            return []
        
        if top_n is None:
            top_n = self.top_n
        top_n = min(top_n, len(documents))

        doc_texts = [doc.get('text', '') for doc in documents]
        
        try:
            api_key = self.key_manager.get_next_key()
            co = cohere.ClientV2(api_key)
            
            response = co.rerank(
                model=self.model_name,
                query=query,
                documents=doc_texts,
                top_n=top_n,
            )
            
            reranked_documents = []
            for result in response.results:
                original_doc = documents[result.index].copy()
                # add rerank score to document
                original_doc['rerank_score'] = result.relevance_score
                original_doc['original_score'] = original_doc.get('score', 0)
                reranked_documents.append(original_doc)
            
            return reranked_documents
            
        except Exception as e:
            print(f"Error in reranking: {e}")
            # if fail, return original documents sorted by original score
            return documents[:top_n]
    
    def rerank_with_fallback(
        self,
        query: str,
        documents: List[Dict],
        top_n: int = None,
        use_original_score: bool = True
    ) -> List[Dict]:
        reranked = self.rerank(query, documents, top_n)
        
        # successful -> return reranked
        if reranked and 'rerank_score' in reranked[0]:
            return reranked
        
        # fallback to original score sorting
        if use_original_score:
            sorted_docs = sorted(
                documents, 
                key=lambda x: x.get('score', 0), 
                reverse=True
            )
            return sorted_docs[:top_n] if top_n else sorted_docs
        
        return documents[:top_n] if top_n else documents