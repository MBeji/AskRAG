"""
Serveur HTTP très simple pour tester l'authentification
"""
import http.server
import socketserver
import json
import urllib.parse
from datetime import datetime
import threading

PORT = 8000

# Base de données mock simple
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

class AskRAGAuthHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
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
            auth_header = self.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                self.send_error_response(401, "Authorization required")
                return
            
            # Simple token validation (mock)
            token = auth_header.split(' ')[1]
            if token == "mock-jwt-token":
                user = mock_users["test@example.com"]
                user_response = {k: v for k, v in user.items() if k != "password"}
                self.send_json_response(user_response)
            else:
                self.send_error_response(401, "Invalid token")
        else:
            self.send_error_response(404, "Not found")
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/v1/auth/login':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                email = data.get('username') or data.get('email')
                password = data.get('password')
                
                user = mock_users.get(email)
                if user and user["password"] == password:
                    user_response = {k: v for k, v in user.items() if k != "password"}
                    response = {
                        "user": user_response,
                        "tokens": {
                            "accessToken": "mock-jwt-token",
                            "refreshToken": "mock-refresh-token", 
                            "tokenType": "bearer"
                        }
                    }
                    self.send_json_response(response)
                else:
                    self.send_error_response(401, "Invalid credentials")
            except Exception as e:
                self.send_error_response(400, f"Invalid request: {str(e)}")
        
        elif self.path == '/api/v1/auth/register':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                email = data.get('email')
                
                if email in mock_users:
                    self.send_error_response(400, "Email already registered")
                    return
                
                new_user = {
                    "id": f"user-{len(mock_users) + 1}",
                    "email": email,
                    "firstName": data.get('firstName'),
                    "lastName": data.get('lastName'),
                    "password": data.get('password'),
                    "role": "USER",
                    "isActive": True,
                    "createdAt": datetime.utcnow().isoformat() + "Z",
                    "updatedAt": datetime.utcnow().isoformat() + "Z"
                }
                
                mock_users[email] = new_user
                user_response = {k: v for k, v in new_user.items() if k != "password"}
                
                response = {
                    "user": user_response,
                    "tokens": {
                        "accessToken": "mock-jwt-token",
                        "refreshToken": "mock-refresh-token",
                        "tokenType": "bearer"
                    }
                }
                self.send_json_response(response)
            except Exception as e:
                self.send_error_response(400, f"Invalid request: {str(e)}")
        
        elif self.path == '/api/v1/auth/logout':
            self.send_json_response({"message": "Successfully logged out"})
        
        else:
            self.send_error_response(404, "Not found")
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response with CORS headers"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        
        response_json = json.dumps(data, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
    
    def send_error_response(self, status_code, message):
        """Send error response with CORS headers"""
        self.send_json_response({"detail": message}, status_code)
    
    def log_message(self, format, *args):
        """Override to add timestamp to logs"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def start_server():
    """Start the HTTP server"""
    with socketserver.TCPServer(("", PORT), AskRAGAuthHandler) as httpd:
        print(f"🚀 Serveur d'authentification AskRAG démarré sur le port {PORT}")
        print(f"📍 Serveur disponible sur: http://localhost:{PORT}")
        print(f"🔧 Health check: http://localhost:{PORT}/health")
        print("\n📋 Credentials de test:")
        print("  Email: test@example.com")
        print("  Password: test123")
        print("\nPress Ctrl+C to stop the server\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du serveur...")
            httpd.shutdown()

if __name__ == "__main__":
    start_server()
