import os
os.environ['OPENAI_API_KEY'] = 'sk-test-placeholder'

print("Test import embeddings...")
from app.core.embeddings import EmbeddingService
print("✓ Import OK")

print("Test création instance...")
embed_service = EmbeddingService()
print(f"✓ Service créé en mode test: {embed_service.test_mode}")

print("Test génération embedding...")
embedding = embed_service.get_embedding("test text")
print(f"✓ Embedding généré: {len(embedding)} dimensions")

print("🎉 Test embeddings réussi !")
