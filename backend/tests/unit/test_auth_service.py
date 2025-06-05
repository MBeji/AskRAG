import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from beanie import PydanticObjectId

# Models and Services to test
from app.models.user import User as UserModel
from app.services.auth_service import authenticate_user, get_current_user, get_current_active_user, TokenData, oauth2_scheme
from app.core.security import verify_password # For mocking
from app.core.config import settings # For JWT settings if needed for token data tests
from fastapi import HTTPException

@pytest.mark.asyncio
@pytest.mark.unit
async def test_authenticate_user_valid_credentials():
    # Mock user data that would be returned by User.find_one
    mock_user_data = UserModel(
        id=PydanticObjectId(), # Simulate a Beanie PydanticObjectId
        username="testuser",
        email="testuser@example.com",
        hashed_password="hashed_password_example", # This will be "verified" by the mocked verify_password
        is_active=True,
        is_superuser=False,
        full_name="Test User"
    )

    # Patch User.find_one to return our mock user
    with patch("app.models.user.User.find_one", new_callable=AsyncMock) as mock_find_one:
        mock_find_one.return_value = mock_user_data

        # Patch security.verify_password to always return True for this test
        with patch("app.core.security.verify_password") as mock_verify_password:
            mock_verify_password.return_value = True

            # Call the authenticate_user function
            authenticated_user = await authenticate_user(username="testuser", password="testpassword")

            # Assertions
            mock_find_one.assert_called_once_with(UserModel.username == "testuser")
            mock_verify_password.assert_called_once_with("testpassword", "hashed_password_example")
            assert authenticated_user is not None
            assert authenticated_user.username == "testuser"
            assert authenticated_user.id == mock_user_data.id

@pytest.mark.asyncio
@pytest.mark.unit
async def test_authenticate_user_invalid_username():
    # Patch User.find_one to return None (user not found)
    with patch("app.models.user.User.find_one", new_callable=AsyncMock) as mock_find_one:
        mock_find_one.return_value = None

        # Patch verify_password (it shouldn't be called if user is not found)
        with patch("app.core.security.verify_password") as mock_verify_password:
            authenticated_user = await authenticate_user(username="nonexistentuser", password="testpassword")

            # Assertions
            mock_find_one.assert_called_once_with(UserModel.username == "nonexistentuser")
            mock_verify_password.assert_not_called() # verify_password should not be called
            assert authenticated_user is None

@pytest.mark.asyncio
@pytest.mark.unit
async def test_authenticate_user_invalid_password():
    mock_user_data = UserModel(
        id=PydanticObjectId(),
        username="testuser",
        email="testuser@example.com",
        hashed_password="hashed_password_example",
        is_active=True
    )
    with patch("app.models.user.User.find_one", new_callable=AsyncMock) as mock_find_one:
        mock_find_one.return_value = mock_user_data
        with patch("app.core.security.verify_password") as mock_verify_password:
            mock_verify_password.return_value = False # Password verification fails

            authenticated_user = await authenticate_user(username="testuser", password="wrongpassword")

            mock_find_one.assert_called_once_with(UserModel.username == "testuser")
            mock_verify_password.assert_called_once_with("wrongpassword", "hashed_password_example")
            assert authenticated_user is None

# Placeholder for get_current_user tests - these are more complex due to token decoding
# For a true unit test, you'd mock jwt.decode and User.find_one
@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_current_user_valid_token():
    mock_user_data = UserModel(
        id=PydanticObjectId(),
        username="testuser",
        email="test@example.com",
        hashed_password="dummy",
        is_active=True
    )
    # This token payload structure must match what create_access_token uses for "sub"
    # and what TokenData model in auth_service expects (if it were used for validation)
    # The key "sub" is standard for subject.
    mock_payload = {"sub": "testuser", "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)}

    with patch("jose.jwt.decode", MagicMock(return_value=mock_payload)) as mock_jwt_decode:
        with patch("app.models.user.User.find_one", AsyncMock(return_value=mock_user_data)) as mock_user_find_one:
            # The token string itself doesn't matter here as jwt.decode is mocked
            user = await get_current_user(token="faketoken")
            mock_jwt_decode.assert_called_once_with("faketoken", settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            mock_user_find_one.assert_called_once_with(UserModel.username == "testuser")
            assert user is not None
            assert user.username == "testuser"

@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_current_user_invalid_token_payload():
    # Token decodes, but payload is missing 'sub' (or 'username')
    mock_payload = {"exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)}
    with patch("jose.jwt.decode", MagicMock(return_value=mock_payload)):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="faketoken")
        assert exc_info.value.status_code == 401

# Example for get_current_active_user
@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_current_active_user_inactive_user():
    mock_inactive_user = UserModel(username="inactive", is_active=False, hashed_password="test", email="test@test.com")

    # This test directly provides the user object, bypassing token logic for this unit
    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_user(current_user=mock_inactive_user)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Inactive user"

# Need to import datetime and timedelta for token expiry mocking
from datetime import datetime, timedelta
