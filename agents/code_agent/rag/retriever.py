import numpy as np
from google import genai
from google.genai import types

class CodeRetriever:
    """Uses the Vertex AI semantic index to find contextually relevant files."""
    
    def __init__(self, indexer):
        self.indexer = indexer

    def search(self, query: str, top_k: int = 3) -> str:
        """Finds the most relevant indexed files based on semantic similarity."""
        if not self.indexer.index:
            return "No relevant code context found in index. Please build index first."
            
        print(f"[RAG Retriever] Semantic search for: '{query}'")
        
        try:
            # Generate embedding for the query
            if self.indexer.client:
                response = self.indexer.client.models.embed_content(
                    model='text-embedding-004',
                    contents=query,
                    config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
                )
                query_embedding = response.embeddings[0].values
            else:
                # Fallback if auth fails
                query_embedding = [0.0] * 768
                
            query_vec = np.array(query_embedding)
            
            # Calculate cosine similarity
            results = []
            for item in self.indexer.index:
                doc_vec = np.array(item["embedding"])
                
                # Handle zero vectors (mock fallback)
                if not np.any(query_vec) or not np.any(doc_vec):
                    similarity = 0.0
                else:
                    similarity = np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec))
                
                results.append((similarity, item))
                
            # Sort by highest similarity
            results.sort(key=lambda x: x[0], reverse=True)
            
            # Format top results
            output = []
            for sim, item in results[:top_k]:
                # If similarity is exactly 0 and client is None, it means we are using mock embeddings.
                # In that case, do a basic keyword fallback search just to have something.
                if sim == 0.0 and not self.indexer.client:
                    if query.lower() in item['content'].lower() or query.lower() in item['path'].lower():
                        output.append(f"File: {item['path']} (Keyword Match)\nSnippet:\n{item['content'][:300]}...\n")
                else:
                    output.append(f"File: {item['path']} (Similarity: {sim:.2f})\nSnippet:\n{item['content'][:300]}...\n")
                
            if not output:
                 return "No relevant code context found."
                 
            return "\n".join(output)
            
        except Exception as e:
            return f"Error during semantic search: {e}"
