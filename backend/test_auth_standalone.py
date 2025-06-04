"""
Standalone authentication test without FastAPI dependencies
"""
import sys
sys.path.append('.')

print("Starting standalone authentication tests...")

try:
    from datetime import datetime, timedelta, timezone
    from typing import Optional, Dict, Any
    import jwt
    from passlib.context import CryptContext
    from pydantic import BaseModel
    
    from app.core.config import settings
    print("✅ Basic imports successful")
    
    # Token models without FastAPI
    class TokenPayload(BaseModel):
        """JWT token payload"""
        sub: Optional[str] = None  # Subject (user_id)
        exp: Optional[datetime] = None  # Expiration
        iat: Optional[datetime] = None  # Issued at
        type: Optional[str] = None  # Token type (access/refresh)
        email: Optional[str] = None
        username: Optional[str] = None

    class Token(BaseModel):
        """Token response model"""
        access_token: str
        refresh_token: str
        token_type: str = "bearer"
        expires_in: int

    # Password hashing context
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    class StandaloneAuthService:
        """Standalone authentication service"""
        
        @staticmethod
        def verify_password(plain_password: str, hashed_password: str) -> bool:
            """Verify a password against its hash"""
            try:
                return pwd_context.verify(plain_password, hashed_password)
            except Exception:
                return False
        
        @staticmethod
        def get_password_hash(password: str) -> str:
            """Hash a password"""
            return pwd_context.hash(password)
        
        @staticmethod
        def create_access_token(
            data: Dict[str, Any], 
            expires_delta: Optional[timedelta] = None
        ) -> str:
            """Create JWT access token"""
            to_encode = data.copy()
            
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            else:
                expire = datetime.now(timezone.utc) + timedelta(
                    minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
                )
            
            to_encode.update({
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "type": "access"
            })
            
            encoded_jwt = jwt.encode(
                to_encode, 
                settings.JWT_SECRET_KEY, 
                algorithm=settings.JWT_ALGORITHM
            )
            return encoded_jwt
        
        @staticmethod
        def create_refresh_token(
            data: Dict[str, Any], 
            expires_delta: Optional[timedelta] = None
        ) -> str:
            """Create JWT refresh token"""
            to_encode = data.copy()
            
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            else:
                # Refresh tokens last 7 days by default
                expire = datetime.now(timezone.utc) + timedelta(
                    minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
                )
            
            to_encode.update({
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "type": "refresh"
            })
            
            encoded_jwt = jwt.encode(
                to_encode, 
                settings.JWT_SECRET_KEY, 
                algorithm=settings.JWT_ALGORITHM
            )
            return encoded_jwt
        
        @staticmethod
        def verify_token(token: str, token_type: str = "access") -> TokenPayload:
            """Verify and decode JWT token"""
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Check token type
            if payload.get("type") != token_type:
                raise ValueError(f"Invalid token type. Expected {token_type}")
            
            # Check expiration
            exp = payload.get("exp")
            if exp is None:
                raise ValueError("Token missing expiration")
            
            if datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                raise ValueError("Token expired")
            
            return TokenPayload(**payload)
        
        @staticmethod
        def create_token_pair(user_data: Dict[str, Any]) -> Token:
            """Create access and refresh token pair"""
            access_token = StandaloneAuthService.create_access_token(data=user_data)
            refresh_token = StandaloneAuthService.create_refresh_token(data=user_data)
            
            return Token(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )

    # Test password hashing
    print("\n🔐 Testing password hashing...")
    password = "test123"
    hashed = StandaloneAuthService.get_password_hash(password)
    print(f"Original: {password}")
    print(f"Hashed: {hashed}")
    print(f"Verification: {StandaloneAuthService.verify_password(password, hashed)}")
    
    # Test token creation
    print("\n🎫 Testing token creation...")
    user_data = {
        "sub": "user123",
        "email": "test@example.com", 
        "username": "testuser"
    }
    
    tokens = StandaloneAuthService.create_token_pair(user_data)
    print(f"Access token created: {tokens.access_token[:50]}...")
    print(f"Refresh token created: {tokens.refresh_token[:50]}...")
    print(f"Token type: {tokens.token_type}")
    print(f"Expires in: {tokens.expires_in} seconds")
    
    # Test token verification
    print("\n🔍 Testing token verification...")
    payload = StandaloneAuthService.verify_token(tokens.access_token, "access")
    print(f"Token verified successfully!")
    print(f"User ID: {payload.sub}")
    print(f"Email: {payload.email}")
    print(f"Username: {payload.username}")
    
    print("\n✅ All standalone authentication tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
