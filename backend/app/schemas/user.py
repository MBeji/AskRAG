from typing import Optional
from pydantic import BaseModel, EmailStr, Field
# For Beanie PydanticObjectId if you directly use it in schemas
# from beanie import PydanticObjectId

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)

class UserUpdate(UserBase):
    # If password is provided, it must meet validation.
    # Pydantic v2: password: Optional[Annotated[str, Field(min_length=8, max_length=128)]] = None
    # For simpler Pydantic v2 without Annotated here, just Field on Optional.
    # If a value is passed for password, it will be validated.
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    # Or, if we want to ensure if it's part of the payload it's validated:
    # class UserUpdate(BaseModel): # Define all fields explicitly, not inheriting UserBase
    #    email: Optional[EmailStr] = None
    #    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    #    full_name: Optional[str] = Field(default=None, max_length=100)
    #    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    #    is_active: Optional[bool] = None
    #    is_superuser: Optional[bool] = None
    # For now, keeping inheritance and applying Field to the Optional password.

class UserInDBBase(UserBase):
    id: str # In MongoDB, this is typically _id, Beanie handles mapping
    # If using Beanie's PydanticObjectId: id: PydanticObjectId

    class Config:
        from_attributes = True # For Pydantic V2 (replaces orm_mode)
        # orm_mode = True # For Pydantic V1

# Schema for returning a user
class UserOut(UserInDBBase):
    pass

# Schema for user in DB (includes hashed_password)
class UserInDB(UserInDBBase):
    hashed_password: str
