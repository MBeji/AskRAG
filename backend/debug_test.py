print("Hello from Python!")
print("Test des imports...")

try:
    import sys
    print(f"Python version: {sys.version}")
    
    import os
    print(f"Current dir: {os.getcwd()}")
    
    os.environ['ENVIRONMENT'] = 'development'
    print("Environment set")
    
    sys.path.append('.')
    print("Path added")
    
    from app.core.embeddings import embedding_service
    print("✓ Embedding service imported")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
