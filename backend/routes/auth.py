from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from pydantic import BaseModel
import os
from models.user import User, Token
from services.auth import auth_service

class GoogleAuthRequest(BaseModel):
    token: str

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

@router.post("/google", response_model=Token)
async def google_auth(request: GoogleAuthRequest):
    """Authenticate user with Google credential token"""
    try:
        print(f"Received authentication request with token: {request.token[:50]}...")
        
        user = await auth_service.authenticate_user_with_credential(request.token)
        if not user:
            print("Authentication failed: Invalid credential token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google credential token"
            )
        
        print(f"Authentication successful for user: {user.email}")
        
        # Create access token
        access_token = auth_service.create_access_token(data={"sub": user.id})
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=1800,  # 30 minutes
            user=user
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in google_auth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/me", response_model=User)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    user_id = auth_service.verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.post("/logout")
async def logout():
    """Logout user (client should remove token from storage)"""
    return {"message": "Successfully logged out"}

@router.get("/verify")
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify if token is valid"""
    user_id = auth_service.verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    return {"valid": True, "user_id": user_id}