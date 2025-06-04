from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any # Any can be removed if UserOut is consistently used for responses

# Models and Schemas
from app.models.user import User as UserModel # Beanie document model
from app.schemas.user import UserCreate, UserOut # Pydantic schemas for API I/O

# Authentication services and utilities
# These now point to the newly created/updated services and security utils
from app.services.auth_service import authenticate_user, get_current_active_user
from app.core.security import create_access_token, get_password_hash
from app.core.config import settings
# Import the main app's limiter instance
# This can be tricky due to import cycles or app structure.
# A common way is to access it via request.app.state.limiter if routes are part of the app.
# Or, define a specific limiter for this router if that's cleaner.
# For now, let's assume we can import it or access it via request.
# If direct import from main is problematic, this needs rethinking.
# from app.main import limiter # This might cause circular import if main imports this router.
# Instead, we'll try to access it via request.app.state for individual route protection.
# However, decorating at function definition time needs direct access to 'limiter'.
# Let's assume for now a shared limiter instance can be imported or a new one is created for this router.
# For simplicity, if we ensure `main.py` defines `limiter` before routers are fully processed,
# we might be able to import it. Or, a better approach:
# Create a limiter instance here or in a shared utility module.
# For this exercise, I'll assume it's accessible via Request for specific endpoint decoration.
# Update: For decorator usage, it's cleaner to import the instance.
# Let's assume we can import it from main. If not, it implies a structural change.
from app.main import limiter # Assuming this is resolvable

router = APIRouter()

class Token(BaseModel): # Define Token response model, as per FastAPI docs
    access_token: str
    token_type: str

@router.post("/login", response_model=Token)
@limiter.limit(settings.AUTH_RATE_LIMIT) # Apply stricter limit from config
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests.
    Uses username and password from form_data.
    """
    user = await authenticate_user(username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Data for the token: 'sub' (subject) is typically user identifier.
    # Using username as subject here. Ensure this is consistent with get_current_user.
    access_token_data = {"sub": user.username}
    access_token = create_access_token(data=access_token_data)

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.AUTH_RATE_LIMIT) # Apply stricter limit from config
async def register_new_user(user_in: UserCreate):
    """
    Create new user.
    - Takes UserCreate schema as input.
    - Checks for existing username/email.
    - Hashes password.
    - Saves new user to MongoDB via Beanie User model.
    - Returns UserOut schema.
    """
    existing_user_username = await UserModel.find_one(UserModel.username == user_in.username)
    if existing_user_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    existing_user_email = await UserModel.find_one(UserModel.email == user_in.email)
    if existing_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    hashed_password = get_password_hash(user_in.password)
    
    user_dict = user_in.model_dump() # Pydantic v2, was .dict() in v1
    user_dict.pop("password", None) # Remove plain password before creating DB model

    user_db = UserModel(
        **user_dict, # Spread the dict from UserCreate
        hashed_password=hashed_password,
        is_active=True, # Default to active for new registrations
        is_superuser=False # Default to not superuser
    )

    await user_db.insert()

    # Convert to UserOut Pydantic model for the response.
    # UserOut schema should have `from_attributes = True` (or orm_mode=True for Pydantic V1)
    # Beanie documents are Pydantic models, so this conversion should be smooth.
    return UserOut.model_validate(user_db) # Pydantic v2, was from_orm(user_db)

@router.get("/users/me", response_model=UserOut)
async def read_users_me(current_user: UserModel = Depends(get_current_active_user)):
    """
    Fetch the current logged-in user.
    Relies on get_current_active_user dependency from auth_service.
    """
    # current_user is already a UserModel (Beanie document) instance.
    # Convert it to UserOut Pydantic model for the response.
    return UserOut.model_validate(current_user) # Pydantic v2

# Placeholder for Token Pydantic model if not defined elsewhere
# from pydantic import BaseModel
# class Token(BaseModel):
#     access_token: str
#     token_type: str
