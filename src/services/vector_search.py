from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
from src.core.config import settings

class VectorSearchService:
    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL if settings.QDRANT_URL else ":memory:",
            api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
        )
        
        self.embedder = SentenceTransformer(
            settings.EMBEDDING_MODEL,
            trust_remote_code=True
        )
        
        self.collection_name = settings.COLLECTION_NAME

    def encode_query(self, query: str) -> List[float]:
        query_vector = self.embedder.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )[0].tolist()
        return query_vector
    
    def search(
        self, 
        query: str, 
        top_k: int = None,
        score_threshold: float = None
    ) -> List[Dict]:
        if top_k is None:
            top_k = settings.DEFAULT_TOP_K
        if score_threshold is None:
            score_threshold = settings.DEFAULT_SCORE_THRESHOLD # default: 0.5

        query_vector = self.encode_query(query)

        # search in Qdrant
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=score_threshold,
            with_payload=True,
            with_vectors=False
        )

        # format results
        documents = []
        for hit in search_result:
            doc = {
                "id": hit.id,
                "score": hit.score,
                "text": hit.payload.get("text", ""),
                "title": hit.payload.get("title", ""),
                "category": hit.payload.get("category", ""),
                "header": hit.payload.get("header", ""),
                "article_id": hit.payload.get("article_id", ""),
                "paragraph_id": hit.payload.get("paragraph_id", ""),
                "metadata": hit.payload
            }
            documents.append(doc)
        
        return documents
    
    def search_with_multiple_queries(
        self, 
        queries: List[str],
        top_k: int = None,
        score_threshold: float = None
    ) -> List[Dict]:
        all_results = []
        for query in queries:
            results = self.search(query, top_k, score_threshold)
            all_results.extend(results)

        unique_results = {}
        for doc in all_results:
            doc_text = doc['text']
            if doc_text in unique_results:
                if doc['score'] > unique_results[doc_text]['score']:
                    unique_results[doc_text] = doc
            else:
                unique_results[doc_text] = doc
        
        return list(unique_results.values())