"""
Brand Management API Routes

This module provides CRUD operations for brand management including:
- Create, read, update, delete brands
- Brand theme and settings management
- Brand-specific data retrieval
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio

from services.social_media_db import social_media_db
from models.social_media import Brand, BrandTheme, BrandDetails, DefaultPostingSettings
from services.auth import get_current_user

router = APIRouter(prefix="/api/brands", tags=["brands"])


# Request/Response Models
class BrandCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Brand name")
    slug: str = Field(..., min_length=1, max_length=50, description="URL-friendly brand identifier")
    description: str = Field(..., min_length=1, max_length=500, description="Brand description")
    theme: BrandTheme = Field(..., description="Brand visual theme")
    details: BrandDetails = Field(..., description="Brand business details")
    default_posting_settings: Optional[DefaultPostingSettings] = Field(
        default_factory=DefaultPostingSettings, 
        description="Default posting configuration"
    )


class BrandUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    theme: Optional[BrandTheme] = None
    details: Optional[BrandDetails] = None
    default_posting_settings: Optional[DefaultPostingSettings] = None


class BrandResponse(BaseModel):
    id: str
    user_id: str
    name: str
    slug: str
    description: str
    theme: BrandTheme
    details: BrandDetails
    default_posting_settings: DefaultPostingSettings
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class BrandListResponse(BaseModel):
    brands: List[BrandResponse]
    total: int
    page: int
    limit: int


# Brand CRUD Operations
@router.post("/", response_model=BrandResponse, status_code=201)
async def create_brand(
    brand_data: BrandCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new brand for the current user.
    
    - **name**: Brand name (required)
    - **slug**: URL-friendly identifier, must be unique per user (required)
    - **description**: Brand description (required)
    - **theme**: Brand visual theme configuration (required)
    - **details**: Brand business details (required)
    - **default_posting_settings**: Default posting configuration (optional)
    """
    try:
        user_id = current_user["id"]
        
        # Check if slug is already taken by this user
        existing_brands = await social_media_db.get_brands_by_user(user_id)
        for brand in existing_brands:
            if brand["slug"] == brand_data.slug:
                raise HTTPException(
                    status_code=400,
                    detail=f"Brand slug '{brand_data.slug}' is already taken"
                )
        
        # Create brand data
        brand_dict = brand_data.dict()
        brand_dict["user_id"] = user_id
        
        brand_id = await social_media_db.create_brand(brand_dict)
        
        # Return created brand
        created_brand = await social_media_db.get_brand_by_id(brand_id)
        if not created_brand:
            raise HTTPException(status_code=500, detail="Failed to retrieve created brand")
        
        return BrandResponse(**created_brand)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create brand: {str(e)}")


@router.get("/", response_model=BrandListResponse)
async def get_brands(
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in brand name or description")
):
    """
    Get all brands for the current user with pagination and search.
    
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    - **search**: Search term for brand name or description
    """
    try:
        user_id = current_user["id"]
        
        # Get all brands for user
        all_brands = await social_media_db.get_brands_by_user(user_id)
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            all_brands = [
                brand for brand in all_brands
                if search_lower in brand["name"].lower() or 
                   search_lower in brand["description"].lower()
            ]
        
        # Apply pagination
        total = len(all_brands)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_brands = all_brands[start_idx:end_idx]
        
        return BrandListResponse(
            brands=[BrandResponse(**brand) for brand in paginated_brands],
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve brands: {str(e)}")


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific brand by ID.
    
    - **brand_id**: Brand ID
    """
    try:
        user_id = current_user["id"]
        
        brand = await social_media_db.get_brand_by_id(brand_id)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Check if user owns this brand
        if brand["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return BrandResponse(**brand)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve brand: {str(e)}")


@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: str,
    update_data: BrandUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a brand.
    
    - **brand_id**: Brand ID
    - **update_data**: Fields to update (all optional)
    """
    try:
        user_id = current_user["id"]
        
        # Check if brand exists and user owns it
        existing_brand = await social_media_db.get_brand_by_id(brand_id)
        if not existing_brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        if existing_brand["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check slug uniqueness if being updated
        if update_data.slug and update_data.slug != existing_brand["slug"]:
            all_brands = await social_media_db.get_brands_by_user(user_id)
            for brand in all_brands:
                if brand["slug"] == update_data.slug and brand["id"] != brand_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Brand slug '{update_data.slug}' is already taken"
                    )
        
        # Prepare update data (only non-None fields)
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Update brand
        success = await social_media_db.update_brand(brand_id, update_dict)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update brand")
        
        # Return updated brand
        updated_brand = await social_media_db.get_brand_by_id(brand_id)
        return BrandResponse(**updated_brand)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update brand: {str(e)}")


@router.delete("/{brand_id}", status_code=204)
async def delete_brand(
    brand_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a brand.
    
    - **brand_id**: Brand ID
    """
    try:
        user_id = current_user["id"]
        
        # Check if brand exists and user owns it
        existing_brand = await social_media_db.get_brand_by_id(brand_id)
        if not existing_brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        if existing_brand["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete brand
        success = await social_media_db.delete_brand(brand_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete brand")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete brand: {str(e)}")


@router.get("/{brand_id}/stats", response_model=Dict[str, Any])
async def get_brand_stats(
    brand_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get statistics for a brand including templates, competitors, and scraped posts.
    
    - **brand_id**: Brand ID
    """
    try:
        user_id = current_user["id"]
        
        # Check if brand exists and user owns it
        brand = await social_media_db.get_brand_by_id(brand_id)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        if brand["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get statistics
        templates = await social_media_db.get_templates_by_user(user_id, brand_id)
        competitors = await social_media_db.get_competitors_by_user(user_id, brand_id=brand_id)
        scraped_posts = await social_media_db.get_scraped_posts_by_user(user_id, brand_id=brand_id)
        
        # Count by platform
        platform_counts = {}
        for post in scraped_posts:
            platform = post["platform"]
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        return {
            "brand_id": brand_id,
            "brand_name": brand["name"],
            "templates_count": len(templates),
            "competitors_count": len(competitors),
            "scraped_posts_count": len(scraped_posts),
            "platform_breakdown": platform_counts,
            "created_at": brand["created_at"],
            "updated_at": brand["updated_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get brand stats: {str(e)}")


@router.post("/{brand_id}/duplicate", response_model=BrandResponse, status_code=201)
async def duplicate_brand(
    brand_id: str,
    new_name: str = Query(..., description="Name for the duplicated brand"),
    new_slug: str = Query(..., description="Slug for the duplicated brand"),
    current_user: dict = Depends(get_current_user)
):
    """
    Duplicate an existing brand with a new name and slug.
    
    - **brand_id**: Brand ID to duplicate
    - **new_name**: Name for the new brand
    - **new_slug**: Slug for the new brand
    """
    try:
        user_id = current_user["id"]
        
        # Check if original brand exists and user owns it
        original_brand = await social_media_db.get_brand_by_id(brand_id)
        if not original_brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        if original_brand["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if new slug is available
        existing_brands = await social_media_db.get_brands_by_user(user_id)
        for brand in existing_brands:
            if brand["slug"] == new_slug:
                raise HTTPException(
                    status_code=400,
                    detail=f"Brand slug '{new_slug}' is already taken"
                )
        
        # Create duplicate brand data
        duplicate_data = {
            "user_id": user_id,
            "name": new_name,
            "slug": new_slug,
            "description": f"Copy of {original_brand['name']}",
            "theme": original_brand["theme"],
            "details": original_brand["details"],
            "default_posting_settings": original_brand["default_posting_settings"],
            "metadata": {
                "duplicated_from": brand_id,
                "duplicated_at": datetime.utcnow().isoformat()
            }
        }
        
        new_brand_id = await social_media_db.create_brand(duplicate_data)
        
        # Return created brand
        new_brand = await social_media_db.get_brand_by_id(new_brand_id)
        return BrandResponse(**new_brand)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to duplicate brand: {str(e)}")