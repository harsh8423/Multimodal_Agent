import os
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from database import get_database
from models.user import User, UserInDB, user_helper, generate_session_token

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 3000

# Password hashing (for future use if needed)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/callback")

class AuthService:
    def __init__(self):
        self.db = None
    
    async def get_db(self):
        if self.db is None:
            self.db = await get_database()
        return self.db
    
    async def verify_google_credential(self, credential: str) -> Optional[Dict[str, Any]]:
        """Verify Google credential token (JWT) and return user info"""
        try:
            print(f"Verifying credential token: {credential[:50]}...")
            
            # Verify the credential token with Google
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
                )
                print(f"Google tokeninfo response status: {response.status_code}")
                
                if response.status_code == 200:
                    token_info = response.json()
                    print(f"Token info received: {token_info}")
                    
                    # Verify the audience matches our client ID
                    client_id = os.getenv("GOOGLE_CLIENT_ID")
                    if token_info.get("aud") != client_id:
                        print(f"Token audience mismatch: expected {client_id}, got {token_info.get('aud')}")
                        return None
                    
                    # Check if token is not expired
                    import time
                    current_time = int(time.time())
                    exp_time = int(token_info.get("exp", 0))
                    if exp_time < current_time:
                        print(f"Token expired: exp={exp_time}, current={current_time}")
                        return None
                    
                    # Extract user info from token
                    user_info = {
                        "id": token_info.get("sub"),
                        "email": token_info.get("email"),
                        "name": token_info.get("name"),
                        "picture": token_info.get("picture"),
                        "email_verified": token_info.get("email_verified", False)
                    }
                    print(f"Extracted user info: {user_info}")
                    return user_info
                else:
                    print(f"Token verification failed with status {response.status_code}: {response.text}")
                    return None
        except Exception as e:
            print(f"Error verifying Google credential: {e}")
            return None
    
    async def get_user_by_google_id(self, google_id: str) -> Optional[User]:
        """Get user by Google ID"""
        db = await self.get_db()
        user = await db.users.find_one({"google_id": google_id})
        return User(**user_helper(user)) if user else None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        db = await self.get_db()
        user = await db.users.find_one({"email": email})
        return User(**user_helper(user)) if user else None
    
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create a new user"""
        db = await self.get_db()
        user_dict = {
            "google_id": user_data["id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "picture": user_data.get("picture"),
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow(),
            "is_active": True
        }
        
        result = await db.users.insert_one(user_dict)
        user_dict["_id"] = result.inserted_id
        return User(**user_helper(user_dict))
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        from bson import ObjectId
        db = await self.get_db()
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        return User(**user_helper(user)) if user else None
    
    async def update_last_login(self, user_id: str):
        """Update user's last login time"""
        from bson import ObjectId
        db = await self.get_db()
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"last_login": datetime.utcnow()}}
        )
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return user ID"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return user_id
        except JWTError:
            return None
    
    async def authenticate_user_with_credential(self, credential: str) -> Optional[User]:
        """Authenticate user with Google credential token"""
        try:
            # Verify the credential token
            google_user_info = await self.verify_google_credential(credential)
            if not google_user_info:
                return None
            
            # Check if user exists
            user = await self.get_user_by_google_id(google_user_info["id"])
            
            if not user:
                # Create new user
                user = await self.create_user(google_user_info)
            else:
                # Update last login
                await self.update_last_login(user.id)
            
            return user
        except Exception as e:
            print(f"Error in authenticate_user_with_credential: {e}")
            return None

# Global auth service instance
auth_service = AuthService()