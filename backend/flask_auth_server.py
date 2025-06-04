"""
Serveur HTTP simple pour tester l'authentification AskRAG
Compatible avec Python 3.13 - utilise Flask au lieu de FastAPI
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
from datetime import datetime, timedelta
import json

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://localhost:5173"])

# Configuration
SECRET_KEY = "test-secret-key-for-development"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Base de données mock
mock_users = {
    "test@example.com": {
        "id": "user-123",
        "email": "test@example.com",
        "firstName": "Test",
        "lastName": "User",
        "password": "test123",
        "role": "USER",
        "isActive": True,
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z"
    }
}

def create_access_token(data: dict, expires_delta=None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@app.route('/')
def root():
    return jsonify({
        "message": "AskRAG Authentication Test Server",
        "status": "running",
        "version": "1.0.0"
    })

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "askrag-auth",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Support both username and email fields
    email = data.get('username') or data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"detail": "Email and password required"}), 400
    
    user = mock_users.get(email)
    if not user or user["password"] != password:
        return jsonify({"detail": "Incorrect email or password"}), 401
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, 
        expires_delta=access_token_expires
    )
    refresh_token = create_access_token(
        data={"sub": user["email"], "type": "refresh"}, 
        expires_delta=timedelta(days=7)
    )
    
    user_response = {k: v for k, v in user.items() if k != "password"}
    
    return jsonify({
        "user": user_response,
        "tokens": {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "tokenType": "bearer"
        }
    })

@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    
    if not all([email, password, first_name, last_name]):
        return jsonify({"detail": "All fields are required"}), 400
    
    if email in mock_users:
        return jsonify({"detail": "Email already registered"}), 400
    
    new_user = {
        "id": f"user-{len(mock_users) + 1}",
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "password": password,
        "role": "USER",
        "isActive": True,
        "createdAt": datetime.utcnow().isoformat() + "Z",
        "updatedAt": datetime.utcnow().isoformat() + "Z"
    }
    
    mock_users[email] = new_user
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user["email"]}, 
        expires_delta=access_token_expires
    )
    refresh_token = create_access_token(
        data={"sub": new_user["email"], "type": "refresh"}, 
        expires_delta=timedelta(days=7)
    )
    
    user_response = {k: v for k, v in new_user.items() if k != "password"}
    
    return jsonify({
        "user": user_response,
        "tokens": {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "tokenType": "bearer"
        }
    })

@app.route('/api/v1/auth/me', methods=['GET'])
def get_current_user():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"detail": "Authorization header required"}), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_token(token)
    
    if not payload:
        return jsonify({"detail": "Invalid or expired token"}), 401
    
    email = payload.get('sub')
    user = mock_users.get(email)
    
    if not user:
        return jsonify({"detail": "User not found"}), 404
    
    user_response = {k: v for k, v in user.items() if k != "password"}
    return jsonify(user_response)

@app.route('/api/v1/auth/logout', methods=['POST'])
def logout():
    return jsonify({"message": "Successfully logged out"})

@app.route('/api/v1/auth/refresh', methods=['POST'])
def refresh_token():
    data = request.get_json()
    refresh_token = data.get('refresh_token')
    
    if not refresh_token:
        return jsonify({"detail": "Refresh token required"}), 400
    
    payload = verify_token(refresh_token)
    if not payload or payload.get('type') != 'refresh':
        return jsonify({"detail": "Invalid refresh token"}), 401
    
    email = payload.get('sub')
    user = mock_users.get(email)
    
    if not user:
        return jsonify({"detail": "User not found"}), 404
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": email}, 
        expires_delta=access_token_expires
    )
    new_refresh_token = create_access_token(
        data={"sub": email, "type": "refresh"}, 
        expires_delta=timedelta(days=7)
    )
    
    return jsonify({
        "accessToken": new_access_token,
        "refreshToken": new_refresh_token,
        "tokenType": "bearer"
    })

if __name__ == "__main__":
    print("🚀 Démarrage du serveur d'authentification AskRAG (Flask)...")
    print("📍 Serveur disponible sur: http://localhost:8000")
    print("🔧 Health check: http://localhost:8000/health")
    print("\n📋 Credentials de test:")
    print("  Email: test@example.com")
    print("  Password: test123")
    print("\nPress Ctrl+C to stop the server")
    
    app.run(host='127.0.0.1', port=8000, debug=False)
