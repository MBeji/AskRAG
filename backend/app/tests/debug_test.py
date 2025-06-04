print("Starting test...")
try:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    print("Path configured")
    
    from app.core.rag_pipeline import RAGPipeline
    print("RAGPipeline imported successfully")
    
    from app.core.document_extractor import DocumentExtractor  
    print("DocumentExtractor imported successfully")
    
    print("Basic imports completed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("Test completed.")
