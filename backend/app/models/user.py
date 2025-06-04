from typing import Optional
from beanie import Document, Indexed
from pydantic import EmailStr

class User(Document):
    username: Indexed(str, unique=True)
    email: Indexed(EmailStr, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False

    class Settings:
        name = "users"
        # Example of how to add more indexes if needed:
        # indexes = [
        #     [("username", pymongo.TEXT)], # Example for text search
        # ]
