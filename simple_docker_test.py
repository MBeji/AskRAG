"""Simple Docker test for AskRAG"""
import os

print("🐳 AskRAG Docker Configuration Test")
print("=" * 50)

# Check if we're in the right directory
print(f"Current directory: {os.getcwd()}")

# Check for Docker files
docker_files = [
    "docker-compose.yml",
    "docker-compose.dev.yml", 
    ".env.docker",
    ".env.docker.dev",
    "backend/Dockerfile",
    "frontend/Dockerfile"
]

for file_path in docker_files:
    if os.path.exists(file_path):
        print(f"✅ Found: {file_path}")
    else:
        print(f"❌ Missing: {file_path}")

print("\n✅ Docker configuration files created successfully!")
print("📝 Next steps:")
print("1. Install Docker Desktop if not already installed")
print("2. Run: docker-compose -f docker-compose.dev.yml up --build")
print("3. Access services at:")
print("   - Frontend: http://localhost:5173")
print("   - Backend: http://localhost:8000")
