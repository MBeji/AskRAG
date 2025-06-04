# AskRAG - Application RAG Full-Stack

## 🎯 Description
Application complète de Retrieval-Augmented Generation (RAG) permettant de poser des questions sur des documents uploadés et d'obtenir des réponses contextualisées via LLM.

## 🏗️ Architecture

### Stack Technique
- **Backend**: FastAPI + Python 3.11+
- **Frontend**: React + TypeScript + Vite
- **Base de données**: MongoDB
- **Base vectorielle**: FAISS
- **LLM**: OpenAI GPT-4
- **Embeddings**: OpenAI text-embedding-ada-002
- **Authentification**: JWT
- **Containerisation**: Docker + Docker Compose

### Structure du Projet
```
AskRAG/
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── api/            # Endpoints REST
│   │   ├── core/           # Configuration & sécurité
│   │   ├── models/         # Modèles MongoDB
│   │   ├── services/       # Logique métier
│   │   ├── utils/          # Utilitaires
│   │   └── main.py         # Point d'entrée
│   ├── tests/              # Tests backend
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # Application React
│   ├── src/
│   │   ├── components/     # Composants React
│   │   ├── pages/          # Pages principales
│   │   ├── hooks/          # Hooks personnalisés
│   │   ├── services/       # API clients
│   │   ├── store/          # State management
│   │   └── types/          # Types TypeScript
│   ├── public/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml      # Orchestration des services
├── docs/                   # Documentation
└── scripts/               # Scripts utilitaires
```

## 🚀 Roadmap de Développement (24 Étapes)

### Phase 1: Architecture & Setup (1-6)
- [x] **Étape 1**: Architecture & Documentation
- [x] **Étape 2**: Setup Backend Python
- [ ] **Étape 3**: Setup Frontend React
- [ ] **Étape 4**: Base de données & Modèles MongoDB
- [ ] **Étape 5**: Configuration Docker
- [ ] **Étape 6**: Variables d'environnement & Configuration

### Phase 2: Authentification & Sécurité (7-9)
- [ ] **Étape 7**: Authentification Backend
- [ ] **Étape 8**: Authentification Frontend
- [ ] **Étape 9**: Sécurité & Validation

### Phase 3: Ingestion & Vectorisation (10-13)
- [ ] **Étape 10**: Upload & Stockage de fichiers
- [ ] **Étape 11**: Traitement des documents
- [ ] **Étape 12**: Vectorisation & Embeddings
- [ ] **Étape 13**: Base de vecteurs FAISS

### Phase 4: RAG Core (14-17)
- [ ] **Étape 14**: Recherche sémantique
- [ ] **Étape 15**: Intégration LLM
- [ ] **Étape 16**: Pipeline RAG complet
- [ ] **Étape 17**: API Questions/Réponses

### Phase 5: Interface Utilisateur (18-20)
- [ ] **Étape 18**: Interface Chat
- [ ] **Étape 19**: Visualisation des sources
- [ ] **Étape 20**: Paramètres RAG

### Phase 6: Finalisation & Déploiement (21-24)
- [ ] **Étape 21**: Historique & Analytics
- [ ] **Étape 22**: Tests & Qualité
- [ ] **Étape 23**: Production & CI/CD
- [ ] **Étape 24**: Documentation & Maintenance

## 🏃‍♂️ Démarrage Rapide

### Prérequis
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- MongoDB (via Docker)

### Installation
```bash
# Cloner le projet
git clone <repo-url>
cd AskRAG

# Lancer avec Docker
docker-compose up --build
```

## 📊 Fonctionnalités Principales

### Core RAG
- ✅ Upload de documents (PDF, TXT)
- ✅ Vectorisation automatique
- ✅ Recherche sémantique
- ✅ Génération de réponses contextualisées
- ✅ Reranking des résultats

### Interface Utilisateur
- ✅ Chat interactif
- ✅ Visualisation des sources
- ✅ Paramètres RAG configurables
- ✅ Historique des conversations

### Sécurité & Performance
- ✅ Authentification JWT
- ✅ Rate limiting
- ✅ Validation des données
- ✅ Optimisation des requêtes

## 🔧 Configuration

Variables d'environnement requises:
```bash
# API Keys
OPENAI_API_KEY=your_openai_key

# Database
MONGODB_URL=mongodb://localhost:27017/askrag

# JWT
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256

# Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10MB
```

## 📚 Documentation Technique

- [API Documentation](./docs/api.md)
- [Architecture Details](./docs/architecture.md)
- [Deployment Guide](./docs/deployment.md)
- [Development Setup](./docs/development.md)

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 License

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.
