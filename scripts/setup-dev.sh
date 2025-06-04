#!/bin/bash

# Script de setup rapide pour l'environnement de développement AskRAG

echo "🚀 Setup AskRAG Development Environment"
echo "======================================="

# Variables
PROJECT_DIR="d:\11-coding\AskRAG"
BACKEND_DIR="$PROJECT_DIR\backend"
FRONTEND_DIR="$PROJECT_DIR\frontend"

echo "📁 Creating project structure..."

# Backend structure
mkdir -p "$BACKEND_DIR\app\api\v1"
mkdir -p "$BACKEND_DIR\app\core"
mkdir -p "$BACKEND_DIR\app\models"
mkdir -p "$BACKEND_DIR\app\services"
mkdir -p "$BACKEND_DIR\app\utils"
mkdir -p "$BACKEND_DIR\tests"
mkdir -p "$BACKEND_DIR\data\faiss_index"
mkdir -p "$BACKEND_DIR\uploads"

# Frontend structure
mkdir -p "$FRONTEND_DIR\src\components\ui"
mkdir -p "$FRONTEND_DIR\src\components\chat"
mkdir -p "$FRONTEND_DIR\src\components\auth"
mkdir -p "$FRONTEND_DIR\src\pages"
mkdir -p "$FRONTEND_DIR\src\hooks"
mkdir -p "$FRONTEND_DIR\src\services"
mkdir -p "$FRONTEND_DIR\src\store"
mkdir -p "$FRONTEND_DIR\src\types"
mkdir -p "$FRONTEND_DIR\src\utils"
mkdir -p "$FRONTEND_DIR\public"

echo "✅ Project structure created!"

echo "📋 Next steps:"
echo "1. cd backend && python -m venv venv"
echo "2. .\venv\Scripts\activate"
echo "3. pip install fastapi uvicorn"
echo "4. cd ..\frontend && npm create vite@latest . --template react-ts"
echo "5. docker-compose up --build"

echo "🎉 Setup complete! Ready for development."
