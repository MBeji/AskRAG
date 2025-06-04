"""
Admin user management endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer

from app.core.auth import get_current_user, get_current_admin_user
from app.core.security import get_current_user_dependency
from app.models.user_v1 import User, UserCreate, UserUpdate, UserInDB, UserRole
from app.db.repositories.user_repository import UserRepository
from app.core.config import settings

router = APIRouter()
security = HTTPBearer()

# Dependency injection
def get_user_repository() -> UserRepository:
    """Get user repository instance."""
    return UserRepository()


@router.get("/users", response_model=List[User])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    current_user: UserInDB = Depends(get_current_admin_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    List all users (admin only).
    
    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        role: Filter by user role
        is_active: Filter by active status
        current_user: Current authenticated admin user
        user_repo: User repository
        
    Returns:
        List of users
    """
    try:
        users = await user_repo.get_users(
            skip=skip,
            limit=limit,
            role=role,
            is_active=is_active
        )
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: UserInDB = Depends(get_current_admin_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Get a specific user by ID (admin only).
    
    Args:
        user_id: User ID to retrieve
        current_user: Current authenticated admin user
        user_repo: User repository
        
    Returns:
        User information
    """
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.post("/users", response_model=User)
async def create_user(
    user_data: UserCreate,
    current_user: UserInDB = Depends(get_current_admin_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Create a new user (admin only).
    
    Args:
        user_data: User creation data
        current_user: Current authenticated admin user
        user_repo: User repository
        
    Returns:
        Created user
    """
    # Check if user already exists
    existing_user = await user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    existing_user = await user_repo.get_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username already exists"
        )
    
    try:
        user = await user_repo.create(user_data)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: UserInDB = Depends(get_current_admin_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Update a user (admin only).
    
    Args:
        user_id: User ID to update
        user_data: User update data
        current_user: Current authenticated admin user
        user_repo: User repository
        
    Returns:
        Updated user
    """
    # Check if user exists
    existing_user = await user_repo.get_by_id(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check for email conflicts
    if user_data.email and user_data.email != existing_user.email:
        email_user = await user_repo.get_by_email(user_data.email)
        if email_user and email_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
    
    # Check for username conflicts
    if user_data.username and user_data.username != existing_user.username:
        username_user = await user_repo.get_by_username(user_data.username)
        if username_user and username_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this username already exists"
            )
    
    try:
        user = await user_repo.update(user_id, user_data)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: UserInDB = Depends(get_current_admin_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Delete a user (admin only).
    
    Args:
        user_id: User ID to delete
        current_user: Current authenticated admin user
        user_repo: User repository
        
    Returns:
        Success message
    """
    # Prevent admin from deleting themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Check if user exists
    existing_user = await user_repo.get_by_id(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        await user_repo.delete(user_id)
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: UserInDB = Depends(get_current_admin_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Activate a user account (admin only).
    
    Args:
        user_id: User ID to activate
        current_user: Current authenticated admin user
        user_repo: User repository
        
    Returns:
        Updated user
    """
    # Check if user exists
    existing_user = await user_repo.get_by_id(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if existing_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already active"
        )
    
    try:
        user_data = UserUpdate(is_active=True)
        user = await user_repo.update(user_id, user_data)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate user: {str(e)}"
        )


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: UserInDB = Depends(get_current_admin_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Deactivate a user account (admin only).
    
    Args:
        user_id: User ID to deactivate
        current_user: Current authenticated admin user
        user_repo: User repository
        
    Returns:
        Updated user
    """
    # Prevent admin from deactivating themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    # Check if user exists
    existing_user = await user_repo.get_by_id(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not existing_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already inactive"
        )
    
    try:
        user_data = UserUpdate(is_active=False)
        user = await user_repo.update(user_id, user_data)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate user: {str(e)}"
        )


@router.get("/stats")
async def get_user_stats(
    current_user: UserInDB = Depends(get_current_admin_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Get user statistics (admin only).
    
    Args:
        current_user: Current authenticated admin user
        user_repo: User repository
        
    Returns:
        User statistics
    """
    try:
        stats = await user_repo.get_user_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user statistics: {str(e)}"
        )
