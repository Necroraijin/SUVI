import sys
import os

# Ensure the root directory is in the path so we can import the agents
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.code_agent.rag.indexer import CodeIndexer

def run_indexer():
    print("📚 Starting global codebase indexing for RAG...")
    
    # Point the indexer at the root of your project
    indexer = CodeIndexer(workspace_path=".")
    result = indexer.build_index()
    
    print(f"✅ Result: {result}")

if __name__ == "__main__":
    run_indexer()