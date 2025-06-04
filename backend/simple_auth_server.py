"""
Serveur d'authentification simple pour AskRAG
Compatible avec le frontend React - Sans FastAPI pour éviter les conflits
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import jwt
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, Any
import re

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
        "password": "test123",  # Mot de passe simple pour les tests
        "role": "USER",
        "isActive": True,
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z"
    }
}

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Créer un token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Vérifier un token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            return None
        return mock_users.get(email)
    except jwt.PyJWTError:
        return None

class AuthRequestHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Gérer les requêtes OPTIONS pour CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.end_headers()

    def send_cors_headers(self):
        """Ajouter les en-têtes CORS"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Credentials', 'true')

    def send_json_response(self, data: Dict[str, Any], status_code: int = 200):
        """Envoyer une réponse JSON"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def send_error_response(self, message: str, status_code: int = 400):
        """Envoyer une réponse d'erreur"""
        self.send_json_response({"detail": message}, status_code)

    def get_request_body(self):
        """Récupérer le corps de la requête"""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            body = self.rfile.read(content_length)
            return json.loads(body.decode('utf-8'))
        return {}

    def get_auth_token(self):
        """Extraire le token d'authentification"""
        auth_header = self.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
        return None

    def do_GET(self):
        """Gérer les requêtes GET"""
        if self.path == '/':
            self.send_json_response({
                "message": "AskRAG Authentication Test Server",
                "status": "running",
                "version": "1.0.0"
            })
        elif self.path == '/health':
            self.send_json_response({
                "status": "healthy",
                "service": "askrag-auth",
                "timestamp": datetime.utcnow().isoformat()
            })
        elif self.path == '/api/v1/auth/me':
            token = self.get_auth_token()
            if not token:
                self.send_error_response("Token required", 401)
                return
            
            user = verify_token(token)
            if not user:
                self.send_error_response("Invalid token", 401)
                return
            
            user_response = {k: v for k, v in user.items() if k != "password"}
            self.send_json_response(user_response)
        else:
            self.send_error_response("Not found", 404)

    def do_POST(self):
        """Gérer les requêtes POST"""
        if self.path == '/api/v1/auth/login':
            self.handle_login()
        elif self.path == '/api/v1/auth/register':
            self.handle_register()
        elif self.path == '/api/v1/auth/logout':
            self.handle_logout()
        elif self.path == '/api/v1/auth/refresh':
            self.handle_refresh()
        else:
            self.send_error_response("Not found", 404)

    def handle_login(self):
        """Gérer la connexion"""
        try:
            # Gérer les données de formulaire URL-encoded
            content_type = self.headers.get('Content-Type', '')
            if 'application/x-www-form-urlencoded' in content_type:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8')
                form_data = urllib.parse.parse_qs(body)
                username = form_data.get('username', [''])[0]
                password = form_data.get('password', [''])[0]
            else:
                # Gérer les données JSON
                data = self.get_request_body()
                username = data.get('username') or data.get('email')
                password = data.get('password')

            if not username or not password:
                self.send_error_response("Username and password required", 400)
                return

            user = mock_users.get(username)
            if not user or user["password"] != password:
                self.send_error_response("Incorrect email or password", 401)
                return

            # Créer les tokens
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

            self.send_json_response({
                "user": user_response,
                "tokens": {
                    "accessToken": access_token,
                    "refreshToken": refresh_token,
                    "tokenType": "bearer"
                }
            })

        except Exception as e:
            print(f"Login error: {e}")
            self.send_error_response("Login failed", 500)

    def handle_register(self):
        """Gérer l'inscription"""
        try:
            data = self.get_request_body()
            email = data.get('email')
            password = data.get('password')
            first_name = data.get('firstName')
            last_name = data.get('lastName')

            if not all([email, password, first_name, last_name]):
                self.send_error_response("All fields required", 400)
                return

            if email in mock_users:
                self.send_error_response("Email already registered", 400)
                return

            # Créer le nouvel utilisateur
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

            # Créer les tokens
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

            self.send_json_response({
                "user": user_response,
                "tokens": {
                    "accessToken": access_token,
                    "refreshToken": refresh_token,
                    "tokenType": "bearer"
                }
            })

        except Exception as e:
            print(f"Register error: {e}")
            self.send_error_response("Registration failed", 500)

    def handle_logout(self):
        """Gérer la déconnexion"""
        self.send_json_response({"message": "Successfully logged out"})

    def handle_refresh(self):
        """Gérer le renouvellement de token"""
        try:
            data = self.get_request_body()
            refresh_token = data.get('refresh_token')

            if not refresh_token:
                self.send_error_response("Refresh token required", 400)
                return

            try:
                payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
                email = payload.get("sub")
                token_type = payload.get("type")

                if email is None or token_type != "refresh":
                    self.send_error_response("Invalid refresh token", 401)
                    return

                user = mock_users.get(email)
                if user is None:
                    self.send_error_response("User not found", 401)
                    return

                # Créer de nouveaux tokens
                access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                new_access_token = create_access_token(
                    data={"sub": email}, 
                    expires_delta=access_token_expires
                )
                new_refresh_token = create_access_token(
                    data={"sub": email, "type": "refresh"}, 
                    expires_delta=timedelta(days=7)
                )

                self.send_json_response({
                    "accessToken": new_access_token,
                    "refreshToken": new_refresh_token,
                    "tokenType": "bearer"
                })

            except jwt.PyJWTError:
                self.send_error_response("Invalid refresh token", 401)

        except Exception as e:
            print(f"Refresh error: {e}")
            self.send_error_response("Token refresh failed", 500)

def run_server(port=8000):
    """Démarrer le serveur"""
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, AuthRequestHandler)
    
    print(f"🚀 Serveur d'authentification AskRAG démarré sur le port {port}")
    print(f"📍 Serveur disponible sur: http://localhost:{port}")
    print(f"🔧 Health check: http://localhost:{port}/health")
    print("\n📋 Credentials de test:")
    print("  Email: test@example.com")
    print("  Password: test123")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du serveur...")
        httpd.shutdown()

if __name__ == "__main__":
    run_server()
