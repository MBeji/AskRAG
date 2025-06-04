# Architecture AskRAG

## 🏗️ Vue d'ensemble

L'application AskRAG suit une architecture microservices avec séparation claire entre le frontend, le backend, et les services de données.

## 🔄 Flux de données RAG

```
1. Upload Document → 2. Chunking → 3. Vectorisation → 4. Stockage FAISS
                                      ↓
8. Réponse LLM ← 7. Génération ← 6. Reranking ← 5. Recherche Vectorielle
```

## 🏛️ Architecture Système

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Services      │
│   (React)       │    │   (FastAPI)     │    │   Externes      │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Chat UI       │◄──►│ • REST API      │◄──►│ • OpenAI API    │
│ • Auth Forms    │    │ • Auth JWT      │    │ • MongoDB       │
│ • File Upload   │    │ • RAG Pipeline  │    │ • FAISS         │
│ • Settings      │    │ • File Handler  │    │ • Redis Cache   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📊 Modèle de Données

### Collections MongoDB

#### Users
```json
{
  "_id": "ObjectId",
  "email": "string",
  "password_hash": "string",
  "created_at": "datetime",
  "is_active": "boolean",
  "settings": {
    "temperature": "float",
    "top_k": "int",
    "model": "string"
  }
}
```

#### Documents
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "filename": "string",
  "file_path": "string",
  "file_size": "int",
  "content_type": "string",
  "upload_date": "datetime",
  "processed": "boolean",
  "chunks": [
    {
      "chunk_id": "string",
      "text": "string",
      "metadata": "object",
      "vector_id": "string"
    }
  ]
}
```

#### Conversations
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "title": "string",
  "created_at": "datetime",
  "updated_at": "datetime",
  "messages": [
    {
      "role": "user|assistant",
      "content": "string",
      "timestamp": "datetime",
      "sources": ["ObjectId"],
      "metadata": "object"
    }
  ]
}
```

#### Queries
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "conversation_id": "ObjectId",
  "query": "string",
  "response": "string",
  "sources": ["ObjectId"],
  "execution_time": "float",
  "timestamp": "datetime",
  "rag_config": {
    "temperature": "float",
    "top_k": "int",
    "model": "string"
  }
}
```

## 🔧 Services Backend

### API Layer (`/api`)
- **Auth**: Authentification JWT, gestion utilisateurs
- **Documents**: Upload, traitement, gestion des fichiers
- **RAG**: Requêtes, recherche, génération de réponses
- **Conversations**: Historique, gestion des sessions
- **Admin**: Analytics, monitoring, configuration

### Core Services (`/services`)
- **DocumentProcessor**: Extraction de texte, chunking
- **VectorService**: Embedding, indexation FAISS
- **RAGService**: Pipeline complet retrieval + generation
- **LLMService**: Interface avec OpenAI API
- **AuthService**: JWT, validation, sécurité

### Data Layer (`/models`)
- **User**: Modèle utilisateur avec Pydantic + MongoDB
- **Document**: Gestion des documents et métadonnées
- **Conversation**: Sessions de chat
- **Query**: Historique des requêtes et réponses

## 🎯 Pipeline RAG Détaillé

### 1. Ingestion
```python
Document → Text Extraction → Chunking → Metadata Enrichment
```

### 2. Vectorisation
```python
Text Chunks → OpenAI Embeddings → FAISS Index → Persistence
```

### 3. Retrieval
```python
User Query → Query Embedding → Similarity Search → Top-K Results
```

### 4. Reranking (Optionnel)
```python
Top-K Results → Cross-Encoder → Reranked Results
```

### 5. Generation
```python
Query + Context → Prompt Template → LLM → Response + Sources
```

## 🔒 Sécurité

### Authentification
- JWT avec refresh tokens
- Hachage bcrypt pour les mots de passe
- Rate limiting par IP et utilisateur

### Autorisation
- RBAC (Role-Based Access Control)
- Isolation des données par utilisateur
- Validation des permissions sur chaque endpoint

### Données
- Chiffrement en transit (HTTPS)
- Validation Pydantic stricte
- Sanitisation des entrées utilisateur
- Gestion sécurisée des clés API

## 📈 Performance & Scalabilité

### Cache Strategy
- Redis pour les requêtes fréquentes
- Cache des embeddings
- Cache des résultats de recherche

### Optimisations
- Lazy loading des composants React
- Pagination des résultats
- Compression des réponses API
- Connection pooling MongoDB

### Monitoring
- Métriques temps de réponse
- Usage des ressources
- Erreurs et exceptions
- Analytics utilisateur

## 🚀 Déploiement

### Environnements
- **Development**: Docker Compose local
- **Staging**: Docker Swarm ou Kubernetes
- **Production**: Kubernetes avec auto-scaling

### CI/CD Pipeline
```
Git Push → Tests → Build Images → Deploy → Health Checks → Rollback si erreur
```

## 🔧 Configuration Environnements

### Variables par Environnement
- Development: `.env.dev`
- Staging: `.env.staging`
- Production: `.env.prod`

### Secrets Management
- Utilisation d'un gestionnaire de secrets (AWS Secrets Manager, Azure Key Vault)
- Rotation automatique des clés
- Chiffrement des variables sensibles
