# AskRAG Backend API

## 🎯 Description
API FastAPI pour l'application AskRAG (Retrieval-Augmented Generation).

## 🚀 Démarrage Rapide

### 1. Prérequis
- Python 3.11+
- MongoDB (optionnel pour l'instant)

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
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🏗️ Structure du Projet

```
backend/
├── app/
│   ├── main.py              # Point d'entrée FastAPI
│   ├── api/                 # Endpoints REST
│   │   └── v1/
│   │       └── api.py       # Router API v1
│   ├── core/
│   │   └── config.py        # Configuration
│   ├── models/              # Modèles de données
│   ├── services/            # Logique métier
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

# Base de données
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=askrag

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

### 🚧 En Cours
- [ ] Tests de l'API
- [ ] Validation configuration

### 📋 Prochaines Étapes (Étape 3)
- [ ] Setup Frontend React
- [ ] Configuration TypeScript
- [ ] Structure composants

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
- **Pydantic**: Validation des données
- **Motor**: Driver MongoDB async
- **OpenAI**: API LLM et embeddings
- **FAISS**: Base vectorielle
- **Sentence-Transformers**: Modèles d'embedding

### Conventions de Code
- Format avec `black`
- Import avec `isort`
- Linting avec `flake8`
- Type hints obligatoires
