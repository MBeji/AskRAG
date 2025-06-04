# 🚀 Start AskRAG System - Development Mode (No Docker Required)

## Quick Start Instructions

### Prerequisites ✅ (Already Available)
- ✅ Python 3.8+ with virtual environment
- ✅ All dependencies installed
- ✅ AskRAG system validated and ready

### Option 1: 🖥️ Development Mode (Recommended for Testing)

#### Step 1: Start Backend Server
```powershell
# Navigate to backend directory
cd d:\11-coding\AskRAG\backend

# Start the FastAPI server
python -m uvicorn app_complete:app --reload --host 0.0.0.0 --port 8000
```

#### Step 2: Start Frontend (New Terminal)
```powershell
# Navigate to frontend directory
cd d:\11-coding\AskRAG\frontend

# Install dependencies (first time only)
npm install

# Start React development server
npm run dev
```

#### Step 3: Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Option 2: 🔧 Backend-Only Mode (API Testing)

```powershell
# Start just the backend for API testing
cd d:\11-coding\AskRAG\backend
python app_complete.py

# Test with curl or browse to:
# http://localhost:8000/docs
```

### Option 3: 📱 Simple Test Server

```powershell
# Start a minimal test server
cd d:\11-coding\AskRAG\backend
python simple_test_server.py
```

## 🎯 What You Can Do

### Core Features to Test
1. **Document Upload**: Upload PDF, Word, or TXT files
2. **Ask Questions**: Query your documents with natural language
3. **Get Answers**: Receive AI-powered responses with citations
4. **Chat History**: View conversation history
5. **Multi-Document Search**: Search across all uploaded documents

### API Endpoints Available
- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication
- `POST /documents/upload` - Document upload
- `POST /chat/query` - Ask questions
- `GET /chat/history` - View chat history
- `GET /documents/` - List documents
- `GET /health` - System health check

## 🚀 Ready to Start?

Choose your preferred option:

**For Full System Testing**:
```powershell
# Terminal 1: Backend
cd d:\11-coding\AskRAG\backend
python -m uvicorn app_complete:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend  
cd d:\11-coding\AskRAG\frontend
npm install && npm run dev
```

**For API Testing Only**:
```powershell
cd d:\11-coding\AskRAG\backend
python app_complete.py
# Then visit: http://localhost:8000/docs
```

**For Quick Demo**:
```powershell
# Run the system demonstration
python run_askrag_demo.py
```

Your AskRAG system is ready to run! 🎉
