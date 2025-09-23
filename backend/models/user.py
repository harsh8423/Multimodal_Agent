from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from bson import ObjectId
import secrets
import string

class User(BaseModel):
    id: Optional[str] = None
    google_id: str
    email: EmailStr
    name: str
    picture: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    last_login: datetime = datetime.utcnow()
    is_active: bool = True

class UserInDB(User):
    """User model for database storage"""
    pass

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: User

class TokenData(BaseModel):
    user_id: Optional[str] = None

def generate_session_token(length: int = 32) -> str:
    """Generate a random session token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def user_helper(user) -> dict:
    """Convert MongoDB document to dict"""
    if user:
        user_dict = {
            "id": str(user["_id"]),
            "google_id": user["google_id"],
            "email": user["email"],
            "name": user["name"],
            "picture": user.get("picture"),
            "created_at": user["created_at"],
            "last_login": user["last_login"],
            "is_active": user["is_active"]
        }
        return user_dict
    return None