from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel #, EmailStr # EmailStr not used in this version

from app.models.user import User # Beanie User model
from app.core.security import verify_password, create_access_token # create_access_token is in security.py
from app.core.config import settings
# Beanie's find_one will be used on the User model directly.

# OAuth2PasswordBearer scheme. tokenUrl should point to the login endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login") # Corrected tokenUrl

class TokenData(BaseModel):
    # This model defines the expected structure of the JWT payload's subject data.
    # If 'sub' in JWT contains username, then 'username: Optional[str] = None'
    # If 'sub' in JWT contains user_id, then 'user_id: Optional[str] = None' or int
    # For this implementation, we'll assume 'sub' holds the username.
    sub: Optional[str] = None


async def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    Authenticates a user by username and password.
    - Retrieves the user by username using Beanie model.
    - Verifies the password using the utility from core.security.
    - Returns the user object if authentication is successful, otherwise None.
    """
    user = await User.find_one(User.username == username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency to get the current user from a JWT token.
    - Decodes the JWT token.
    - Retrieves the user based on the token's subject (username).
    - Raises HTTPException for invalid tokens or non-existent users.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        # Assuming the 'sub' claim in the token stores the username.
        # This needs to be consistent with how the token is created.
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception

        # Optional: Validate payload structure with TokenData model
        # token_data = TokenData(sub=username) # If TokenData has 'sub' field

    except JWTError:
        raise credentials_exception
    
    user = await User.find_one(User.username == username) # Query by username
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to get the current active user.
    - Checks if the user (obtained from get_current_user) is active.
    - Raises HTTPException if the user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

# Note on create_access_token:
# It is already implemented in app.core.security.
# When calling it for login, ensure the data passed is like:
# data_to_encode = {"sub": user.username} # or user.id if preferred, adjust TokenData & get_current_user
# access_token = create_access_token(data=data_to_encode)
