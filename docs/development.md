# Guide de Développement

## 🛠️ Setup de l'Environnement de Développement

### Prérequis
- Python 3.11+
- Node.js 18+
- Docker Desktop
- Git
- VS Code (recommandé)

### Extensions VS Code Recommandées
- Python
- Pylance
- ES7+ React/Redux/React-Native snippets
- TypeScript Hero
- Docker
- MongoDB for VS Code

## 🚀 Installation Locale

### 1. Cloner le Projet
```bash
git clone <repo-url>
cd AskRAG
```

### 2. Backend Setup
```bash
cd backend

# Créer environnement virtuel
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Installer dépendances
pip install -r requirements.txt

# Configurer variables d'environnement
copy .env.example .env
# Éditer .env avec vos clés API
```

### 3. Frontend Setup
```bash
cd frontend

# Installer dépendances
npm install

# Configurer variables d'environnement
copy .env.example .env.local
# Éditer .env.local
```

### 4. Base de Données
```bash
# Démarrer MongoDB avec Docker
docker run -d --name mongodb -p 27017:27017 mongo:latest

# Ou utiliser Docker Compose
docker-compose up mongodb
```

## 🔧 Variables d'Environnement

### Backend (.env)
```bash
# Database
MONGODB_URL=mongodb://localhost:27017/askrag
MONGODB_DB_NAME=askrag

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# File Upload
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760  # 10MB

# FAISS
FAISS_INDEX_PATH=./data/faiss_index

# Redis (optionnel)
REDIS_URL=redis://localhost:6379

# Environment
ENVIRONMENT=development
DEBUG=True
```

### Frontend (.env.local)
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=AskRAG
VITE_MAX_FILE_SIZE=10485760
```

## 🏃‍♂️ Commandes de Développement

### Backend
```bash
# Démarrer le serveur de développement
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Lancer les tests
pytest tests/ -v

# Linter & Formatage
black app/
isort app/
flake8 app/

# Migrations (si applicable)
alembic upgrade head
```

### Frontend
```bash
# Démarrer le serveur de développement
cd frontend
npm run dev

# Build pour production
npm run build

# Lancer les tests
npm test

# Linter & Formatage
npm run lint
npm run format
```

### Docker Development
```bash
# Build et démarrer tous les services
docker-compose up --build

# Démarrer en arrière-plan
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Arrêter tous les services
docker-compose down
```

## 🧪 Tests

### Structure des Tests

#### Backend Tests
```
backend/tests/
├── __init__.py
├── conftest.py           # Configuration pytest
├── test_auth/           # Tests authentification
├── test_documents/      # Tests gestion documents
├── test_rag/           # Tests pipeline RAG
└── test_api/           # Tests endpoints API
```

#### Frontend Tests
```
frontend/src/tests/
├── components/         # Tests composants
├── hooks/             # Tests hooks personnalisés
├── services/          # Tests services API
└── utils/            # Tests fonctions utilitaires
```

### Commandes de Test
```bash
# Backend - tous les tests
pytest

# Backend - tests spécifiques
pytest tests/test_auth/ -v

# Backend - avec coverage
pytest --cov=app tests/

# Frontend - tous les tests
npm test

# Frontend - en mode watch
npm run test:watch

# Frontend - avec coverage
npm run test:coverage
```

## 📝 Conventions de Code

### Backend Python
```python
# Imports
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from app.models.user import User

# Functions
def get_user_by_email(email: str) -> Optional[User]:
    """Get user by email address."""
    pass

# Classes
class DocumentService:
    """Service for document management."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def create_document(self, document_data: dict) -> Document:
        """Create a new document."""
        pass
```

### Frontend TypeScript
```typescript
// Interfaces
interface User {
  id: string;
  email: string;
  createdAt: Date;
}

// Components
interface ChatMessageProps {
  message: Message;
  onReply: (content: string) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ 
  message, 
  onReply 
}) => {
  return (
    <div className="chat-message">
      {/* Component content */}
    </div>
  );
};

// Hooks
export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  // Hook logic
  return { user, login, logout };
};
```

## 🔍 Debugging

### Backend Debugging
```python
# Utiliser debugger Python
import pdb; pdb.set_trace()

# Ou avec VS Code breakpoints
# F9 pour toggle breakpoint
# F5 pour démarrer debug
```

### Frontend Debugging
```typescript
// Console debugging
console.log('Debug info:', data);

// React DevTools
// Chrome extension pour inspector les composants

// Network tab
// Pour vérifier les appels API
```

## 📊 Monitoring de Développement

### Logs Backend
```python
import logging

logger = logging.getLogger(__name__)

# Log levels
logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
```

### Performance Monitoring
```bash
# Profiling Python
pip install py-spy
py-spy top --pid <python-process-id>

# Memory usage
pip install memory-profiler
@profile
def function_to_profile():
    pass
```

## 🚀 Hot Reload & Live Reload

### Backend
- FastAPI avec `--reload` pour auto-restart
- Watchdog pour surveiller les changements de fichiers

### Frontend
- Vite HMR (Hot Module Replacement)
- Auto-refresh du navigateur

## 🛠️ Outils de Développement

### Backend
- **FastAPI Docs**: http://localhost:8000/docs
- **MongoDB Compass**: Interface graphique MongoDB
- **Postman**: Tests d'API
- **pytest-html**: Rapports de tests HTML

### Frontend
- **React DevTools**: Inspection des composants
- **Redux DevTools**: État de l'application
- **Lighthouse**: Audit de performance
- **Storybook**: Développement de composants isolés

## 🔄 Workflow Git

### Branch Strategy
```bash
main                 # Production
├── develop         # Développement principal
├── feature/auth    # Nouvelles fonctionnalités
├── bugfix/login    # Corrections de bugs
└── hotfix/security # Corrections urgentes
```

### Commits Convention
```bash
feat: add user authentication
fix: resolve login redirect issue
docs: update API documentation
style: format code with black
refactor: improve RAG pipeline performance
test: add unit tests for document service
```

## 📦 Gestion des Dépendances

### Backend
```bash
# Installer nouvelle dépendance
pip install package-name
pip freeze > requirements.txt

# Ou avec pip-tools
pip-compile requirements.in
```

### Frontend
```bash
# Installer nouvelle dépendance
npm install package-name

# Dev dependencies
npm install --save-dev package-name

# Audit de sécurité
npm audit
npm audit fix
```
