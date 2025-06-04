# AskRAG Backend API

## 🎯 Description
API FastAPI pour l'application AskRAG (Retrieval-Augmented Generation).

## 🚀 Démarrage Rapide

### 1. Prérequis
- Python 3.11+ (ou la version spécifiée dans les Dockerfiles, ex: Python 3.10)
- MongoDB (maintenant requis)

### 2. Installation
```bash
# Activer l'environnement virtuel
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# source venv/bin/activate   # Linux/Mac

# Installer les dépendances
pip install -r requirements.txt
```

### 3. Configuration
```bash
# Copier le fichier d'exemple
copy .env.example .env

# Éditer .env avec vos configurations
```

### 4. Lancer le serveur
```bash
# Méthode 1: Script PowerShell
.\start_dev.ps1

# Méthode 2: Script Batch
start_dev.bat

# Méthode 3: Uvicorn direct
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📍 Endpoints Disponibles

### Core Endpoints
- **GET /** - Information de l'API
- **GET /health** - Health check
- **GET /api/v1/health** - Health check API v1

### Documentation Interactive
- **Swagger UI**: http://localhost:8000/docs (ou /api/v1/docs si `openapi_url` est préfixé)
- **ReDoc**: http://localhost:8000/redoc (ou /api/v1/redoc)

### Authentification
L'API utilise l'authentification JWT. Les endpoints d'authentification sont disponibles sous `/api/v1/auth`:
- **POST /api/v1/auth/register**: Enregistrer un nouvel utilisateur.
  - Request Body: `UserCreate` schema (username, email, password, full_name).
  - Response: `UserOut` schema.
- **POST /api/v1/auth/login**: Connecter un utilisateur et obtenir un token d'accès.
  - Request Body: Form data (username, password).
  - Response: `{"access_token": "...", "token_type": "bearer"}`.
- **GET /api/v1/auth/users/me**: Obtenir les informations de l'utilisateur actuellement connecté (nécessite un token).
  - Response: `UserOut` schema.

Le token d'accès doit être inclus dans l'en-tête `Authorization` des requêtes protégées:
`Authorization: Bearer <your_token>`

### Recherche Sémantique (RAG)
Un endpoint de recherche sémantique est disponible sous `/api/v1/rag`:
- **POST /api/v1/rag/search**: Effectue une recherche sémantique dans les documents de l'utilisateur.
  - Request Body: `{"query": "votre question ici"}`
  - Response: Liste de chunks pertinents avec leur contenu, score, et métadonnées du document source.
  - Nécessite un token d'accès. Le nombre de résultats (`k`) est configurable via `SEARCH_TOP_K`.
- **POST /api/v1/rag/ask**: Pose une question sur les documents téléversés et obtient une réponse générée par un LLM basé sur le contexte trouvé.
  - Request Body: `{"query": "votre question ici"}`
  - Response: `{"answer": "Réponse générée...", "sources": [liste des chunks sources]}`.
  - Nécessite un token d'accès. Utilise les configurations `LLM_MODEL_NAME`, `MAX_CONTEXT_TOKENS`, etc.

### Rate Limiting
L'API intègre un système de limitation de taux (rate limiting) pour prévenir les abus:
- **Par défaut:** Les routes sont limitées à `100 requêtes par heure` par adresse IP (configurable via `DEFAULT_RATE_LIMIT` dans `.env`).
- **Authentification:** Les endpoints `/login` et `/register` ont des limites plus strictes: `10 requêtes par minute` (configurable via `AUTH_RATE_LIMIT`).
- **Health Check:** L'endpoint `/health` a sa propre limite: `20 requêtes par minute` (configurable via `HEALTH_CHECK_RATE_LIMIT`).
Les réponses incluent les en-têtes `X-RateLimit-Limit` et `X-RateLimit-Remaining`. Si la limite est dépassée, une erreur HTTP 429 est retournée.

### Traitement des Documents
Lors du téléversement, le contenu textuel des documents supportés (PDF via PyMuPDF, DOCX, TXT, MD, HTML) est extrait de manière synchrone. Ce contenu est stocké dans le champ `extracted_text` du modèle `Document` en base de données. L'état du document (`status`) reflète les étapes de traitement (ex: `pending_extraction`, `text_extracted`, `failed_extraction`). Les types de fichiers exacts supportés pour l'extraction sont définis dans `app/core/document_extractor.py`.

## 🏗️ Structure du Projet

```
backend/
├── app/
│   ├── main.py              # Point d'entrée FastAPI
│   ├── api/                 # Endpoints REST
│   │   └── v1/
│   │       └── api.py       # Router API v1
│   ├── core/
│   │   ├── config.py        # Configuration
│   │   ├── security.py      # Utilitaires de sécurité (hachage, tokens JWT)
│   ├── db/
│   │   └── connection.py    # Connexion base de données et initialisation Beanie
│   ├── models/              # Modèles de données (Beanie ODM)
│   │   ├── user.py          # Modèle User
│   │   └── document.py      # Modèle Document (inclut ... extracted_text, chunks: [{"chunk_text": str, "embedding": List[float]}], etc.)
│   ├── schemas/             # Schémas Pydantic pour API (séparés des modèles)
│   │   ├── user.py          # Schémas User
│   │   └── document.py      # Schémas Document
│   ├── services/            # Logique métier
│   │   └── auth_service.py  # Services d'authentification (logique utilisateur actuel, etc.)
│   └── utils/               # Utilitaires
├── tests/                   # Tests unitaires
├── data/                    # Données FAISS
├── uploads/                 # Fichiers uploadés
├── requirements.txt         # Dépendances Python
├── .env.example            # Variables d'environnement exemple
├── start_dev.ps1           # Script démarrage PowerShell
└── start_dev.bat           # Script démarrage Batch
```

## 🔧 Configuration

### Variables d'Environnement
Voir `.env.example` pour la liste complète des variables.

### Variables Principales
```bash
# Base
ENVIRONMENT=development
DEBUG=True

# Sécurité
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Base de données (MongoDB)
MONGODB_URL=mongodb://localhost:27017 # URL de votre instance MongoDB
MONGODB_DATABASE=askrag_dev          # Nom de la base de données (ex: askrag_dev, askrag_prod)
# DATABASE_URL est construit à partir des deux ci-dessus dans config.py

# OpenAI (optionnel pour l'instant)
OPENAI_API_KEY=sk-your-key
```

## 📊 État Actuel - Étape 2

### ✅ Implémenté
- [x] Structure projet FastAPI
- [x] Configuration avec Pydantic
- [x] Endpoints de base (/, /health)
- [x] Router API v1
- [x] Scripts de démarrage
- [x] Requirements.txt avec dépendances

### Database Setup (Nouvelle section)
L'application utilise maintenant MongoDB comme base de données principale, avec Beanie ODM pour la modélisation des données.

- Assurez-vous que MongoDB est en cours d'exécution et accessible à l'URL spécifiée dans votre fichier `.env` (`MONGODB_URL`).
- Les modèles de données principaux sont `User` (dans `app/models/user.py`) et `Document` (dans `app/models/document.py`).
- La connexion à la base de données et l'initialisation de Beanie sont gérées dans `app/db/connection.py` et appelées au démarrage de l'application FastAPI.

### 🚧 En Cours
- Intégration complète des modèles User et Document dans les endpoints API.
- Tests pour les opérations CRUD sur les nouveaux modèles.

### 📋 Prochaines Étapes
- Développement des endpoints API pour gérer les utilisateurs et les documents.
- Intégration avec le pipeline RAG.

## 🧪 Tests

```bash
# Lancer les tests (quand disponibles)
pytest tests/ -v

# Test de la structure
python test_setup.py
```

## 📝 Notes de Développement

### Dépendances Principales
- **FastAPI**: Framework API moderne
- **Uvicorn**: Serveur ASGI
- **Pydantic**: Validation des données (maintenant v2+)
- **Beanie ODM**: Modélisation de données asynchrone pour MongoDB basée sur Pydantic.
- **Motor**: Driver MongoDB async (utilisé par Beanie)
- **OpenAI**: API LLM et embeddings
- **FAISS**: Base vectorielle
- **Sentence-Transformers**: Modèles d'embedding

### Conventions de Code
- Format avec `black`
- Import avec `isort`
- Linting avec `flake8`
- Type hints obligatoires
