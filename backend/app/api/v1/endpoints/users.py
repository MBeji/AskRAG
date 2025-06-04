"""
User management endpoints
"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from app.models.user_v1 import User, UserCreate, UserUpdate, UserResponse
from app.db.repositories.mock_repositories import get_mock_user_repository

router = APIRouter()

@router.post("/", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    user_repo = Depends(get_mock_user_repository)
):
    """Create a new user"""
    try:
        # Check if user already exists
        existing_user = await user_repo.get_by_email(user.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        created_user = await user_repo.create(user)
        return UserResponse(**created_user.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    user_repo = Depends(get_mock_user_repository)
):
    """List all users"""
    users = await user_repo.list(skip=skip, limit=limit)
    return [UserResponse(**user.dict()) for user in users]

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    user_repo = Depends(get_mock_user_repository)
):
    """Get a specific user"""
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user.dict())

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    user_repo = Depends(get_mock_user_repository)
):
    """Update a user"""
    user = await user_repo.update(user_id, user_update)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user.dict())

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    user_repo = Depends(get_mock_user_repository)
):
    """Delete a user"""
    success = await user_repo.delete(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}
