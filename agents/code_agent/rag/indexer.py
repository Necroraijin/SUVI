import os
import json
import numpy as np
from typing import Dict, List, Any
from google import genai
from google.genai import types

class CodeIndexer:
    """Scans local Python files and builds a Vertex AI semantic index."""
    
    def __init__(self, workspace_path: str = ".", project_id: str = None, location: str = "us-central1"):
        self.workspace = workspace_path
        self.project_id = project_id or os.environ.get("GCP_PROJECT", "suvi-project")
        self.location = location
        self.index: List[Dict[str, Any]] = []
        
        try:
            self.client = genai.Client(vertexai=True, project=self.project_id, location=self.location)
        except Exception as e:
            print(f"[RAG Indexer] Warning: Failed to init Gemini client. {e}")
            self.client = None

    def get_embedding(self, text: str) -> List[float]:
        """Synchronous wrapper for getting embeddings."""
        if not self.client:
            return [0.0] * 768 # Dummy embedding if auth fails
            
        response = self.client.models.embed_content(
            model='text-embedding-004',
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
        )
        return response.embeddings[0].values

    def build_index(self):
        """Builds a semantic mapping of file paths to their contents."""
        print(f"[RAG Indexer] Building Vertex AI semantic index for: {self.workspace}...")
        try:
            for root, _, files in os.walk(self.workspace):
                # Skip hidden directories and venvs
                if any(ignored in root for ignored in ['.git', 'venv', '__pycache__', 'node_modules']):
                    continue
                for file in files:
                    if file.endswith(".py") or file.endswith(".md"):
                        path = os.path.join(root, file)
                        try:
                            with open(path, "r", encoding="utf-8") as f:
                                content = f.read(2000) # Limit chunk size
                                if not content.strip(): continue
                                
                                embedding = self.get_embedding(content)
                                
                                self.index.append({
                                    "path": path,
                                    "content": content,
                                    "embedding": embedding
                                })
                        except Exception as e:
                            print(f"[RAG Indexer] Skipping {path}: {e}")
                            
            print(f"[RAG Indexer] Successfully indexed {len(self.index)} files with text-embedding-004.")
            return "Indexing complete."
        except Exception as e:
            return f"Error indexing workspace: {e}"
