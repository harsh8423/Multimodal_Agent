"""
Competitor Management API Routes

This module provides CRUD operations for competitor tracking including:
- Create, read, update, delete competitors
- Competitor metrics management
- Scraping configuration management
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio

from services.social_media_db import social_media_db
from models.social_media import (
    Competitor, PlatformType, CompetitorMetrics, ScrapeConfig
)
from services.auth import get_current_user

router = APIRouter(prefix="/api/competitors", tags=["competitors"])


# Request/Response Models
class CompetitorMetricsRequest(BaseModel):
    followers: Optional[int] = Field(None, ge=0, description="Follower count")
    avg_engagement: Optional[float] = Field(None, ge=0, le=1, description="Average engagement rate")
    posts_count: Optional[int] = Field(None, ge=0, description="Total posts count")
    last_post_date: Optional[datetime] = Field(None, description="Last post date")


class ScrapeConfigRequest(BaseModel):
    scrape_frequency: str = Field(default="weekly", description="How often to scrape")
    auto_scrape: bool = Field(default=False, description="Whether to auto-scrape")


class CompetitorCreateRequest(BaseModel):
    brand_id: Optional[str] = Field(None, description="Brand ID if competitor is tied to a brand")
    name: str = Field(..., min_length=1, max_length=100, description="Competitor name")
    platform: PlatformType = Field(..., description="Social media platform")
    handle: str = Field(..., min_length=1, max_length=100, description="Platform handle/username")
    profile_url: str = Field(..., min_length=1, description="Profile URL")
    metrics: Optional[CompetitorMetricsRequest] = Field(
        default_factory=CompetitorMetricsRequest, 
        description="Account metrics"
    )
    scrape_config: Optional[ScrapeConfigRequest] = Field(
        default_factory=ScrapeConfigRequest, 
        description="Scraping configuration"
    )
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Extensible metadata")


class CompetitorUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    platform: Optional[PlatformType] = None
    handle: Optional[str] = Field(None, min_length=1, max_length=100)
    profile_url: Optional[str] = Field(None, min_length=1)
    metrics: Optional[CompetitorMetricsRequest] = None
    scrape_config: Optional[ScrapeConfigRequest] = None
    metadata: Optional[Dict[str, Any]] = None


class CompetitorResponse(BaseModel):
    id: str
    user_id: str
    brand_id: Optional[str]
    name: str
    platform: str
    handle: str
    profile_url: str
    metrics: Dict[str, Any]
    scrape_config: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class CompetitorListResponse(BaseModel):
    competitors: List[CompetitorResponse]
    total: int
    page: int
    limit: int


# Competitor CRUD Operations
@router.post("/", response_model=CompetitorResponse, status_code=201)
async def create_competitor(
    competitor_data: CompetitorCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new competitor entry.
    
    - **brand_id**: Brand ID if competitor is tied to a brand (optional)
    - **name**: Competitor name (required)
    - **platform**: Social media platform (required)
    - **handle**: Platform handle/username (required)
    - **profile_url**: Profile URL (required)
    - **metrics**: Account metrics (optional)
    - **scrape_config**: Scraping configuration (optional)
    - **metadata**: Extensible metadata (optional)
    """
    try:
        user_id = current_user["id"]
        
        # Validate brand_id if provided
        if competitor_data.brand_id:
            brand = await social_media_db.get_brand_by_id(competitor_data.brand_id)
            if not brand:
                raise HTTPException(status_code=404, detail="Brand not found")
            if brand["user_id"] != user_id:
                raise HTTPException(status_code=403, detail="Access denied to brand")
        
        # Create competitor data
        competitor_dict = {
            "user_id": user_id,
            "brand_id": competitor_data.brand_id,
            "name": competitor_data.name,
            "platform": competitor_data.platform.value,
            "handle": competitor_data.handle,
            "profile_url": competitor_data.profile_url,
            "metrics": competitor_data.metrics.dict() if competitor_data.metrics else {},
            "scrape_config": competitor_data.scrape_config.dict() if competitor_data.scrape_config else {},
            "metadata": competitor_data.metadata or {}
        }
        
        competitor_id = await social_media_db.create_competitor(competitor_dict)
        
        # Return created competitor
        created_competitor = await social_media_db.get_competitor_by_id(competitor_id)
        if not created_competitor:
            raise HTTPException(status_code=500, detail="Failed to retrieve created competitor")
        
        return CompetitorResponse(**created_competitor)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create competitor: {str(e)}")


@router.get("/", response_model=CompetitorListResponse)
async def get_competitors(
    current_user: dict = Depends(get_current_user),
    brand_id: Optional[str] = Query(None, description="Filter by brand ID"),
    platform: Optional[PlatformType] = Query(None, description="Filter by platform"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in competitor name or handle")
):
    """
    Get competitors with filtering and pagination.
    
    - **brand_id**: Filter by brand ID (optional)
    - **platform**: Filter by platform (optional)
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    - **search**: Search term for competitor name or handle
    """
    try:
        user_id = current_user["id"]
        
        # Validate brand_id if provided
        if brand_id:
            brand = await social_media_db.get_brand_by_id(brand_id)
            if not brand:
                raise HTTPException(status_code=404, detail="Brand not found")
            if brand["user_id"] != user_id:
                raise HTTPException(status_code=403, detail="Access denied to brand")
        
        # Get competitors
        all_competitors = await social_media_db.get_competitors_by_user(user_id, platform, brand_id)
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            all_competitors = [
                competitor for competitor in all_competitors
                if search_lower in competitor["name"].lower() or 
                   search_lower in competitor["handle"].lower()
            ]
        
        # Apply pagination
        total = len(all_competitors)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_competitors = all_competitors[start_idx:end_idx]
        
        return CompetitorListResponse(
            competitors=[CompetitorResponse(**competitor) for competitor in paginated_competitors],
            total=total,
            page=page,
            limit=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve competitors: {str(e)}")


@router.get("/{competitor_id}", response_model=CompetitorResponse)
async def get_competitor(
    competitor_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific competitor by ID.
    
    - **competitor_id**: Competitor ID
    """
    try:
        user_id = current_user["id"]
        
        competitor = await social_media_db.get_competitor_by_id(competitor_id)
        if not competitor:
            raise HTTPException(status_code=404, detail="Competitor not found")
        
        # Check if user owns this competitor
        if competitor["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return CompetitorResponse(**competitor)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve competitor: {str(e)}")


@router.put("/{competitor_id}", response_model=CompetitorResponse)
async def update_competitor(
    competitor_id: str,
    update_data: CompetitorUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a competitor.
    
    - **competitor_id**: Competitor ID
    - **update_data**: Fields to update (all optional)
    """
    try:
        user_id = current_user["id"]
        
        # Check if competitor exists and user owns it
        existing_competitor = await social_media_db.get_competitor_by_id(competitor_id)
        if not existing_competitor:
            raise HTTPException(status_code=404, detail="Competitor not found")
        
        if existing_competitor["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Prepare update data (only non-None fields)
        update_dict = {}
        for field, value in update_data.dict().items():
            if value is not None:
                if field in ["metrics", "scrape_config", "metadata"] and isinstance(value, dict):
                    update_dict[field] = value
                elif field == "platform" and hasattr(value, "value"):
                    update_dict[field] = value.value
                else:
                    update_dict[field] = value
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Update competitor
        success = await social_media_db.update_competitor(competitor_id, update_dict)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update competitor")
        
        # Return updated competitor
        updated_competitor = await social_media_db.get_competitor_by_id(competitor_id)
        return CompetitorResponse(**updated_competitor)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update competitor: {str(e)}")


@router.delete("/{competitor_id}", status_code=204)
async def delete_competitor(
    competitor_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a competitor.
    
    - **competitor_id**: Competitor ID
    """
    try:
        user_id = current_user["id"]
        
        # Check if competitor exists and user owns it
        existing_competitor = await social_media_db.get_competitor_by_id(competitor_id)
        if not existing_competitor:
            raise HTTPException(status_code=404, detail="Competitor not found")
        
        if existing_competitor["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete competitor
        success = await social_media_db.delete_competitor(competitor_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete competitor")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete competitor: {str(e)}")


@router.put("/{competitor_id}/metrics", response_model=CompetitorResponse)
async def update_competitor_metrics(
    competitor_id: str,
    metrics: CompetitorMetricsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update competitor metrics.
    
    - **competitor_id**: Competitor ID
    - **metrics**: Updated metrics data
    """
    try:
        user_id = current_user["id"]
        
        # Check if competitor exists and user owns it
        competitor = await social_media_db.get_competitor_by_id(competitor_id)
        if not competitor:
            raise HTTPException(status_code=404, detail="Competitor not found")
        
        if competitor["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update metrics
        success = await social_media_db.update_competitor_metrics(competitor_id, metrics.dict())
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update metrics")
        
        # Return updated competitor
        updated_competitor = await social_media_db.get_competitor_by_id(competitor_id)
        return CompetitorResponse(**updated_competitor)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update metrics: {str(e)}")


@router.get("/{competitor_id}/stats", response_model=Dict[str, Any])
async def get_competitor_stats(
    competitor_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get statistics for a competitor including scraped posts.
    
    - **competitor_id**: Competitor ID
    """
    try:
        user_id = current_user["id"]
        
        # Check if competitor exists and user owns it
        competitor = await social_media_db.get_competitor_by_id(competitor_id)
        if not competitor:
            raise HTTPException(status_code=404, detail="Competitor not found")
        
        if competitor["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get scraped posts for this competitor
        scraped_posts = await social_media_db.get_scraped_posts_by_user(
            user_id, 
            platform=PlatformType(competitor["platform"]),
            limit=1000
        )
        
        # Filter posts by handle (if we can match them)
        competitor_posts = []
        for post in scraped_posts:
            platform_data = post.get("platform_data", {})
            if competitor["platform"] == "instagram":
                if platform_data.get("username") == competitor["handle"].replace("@", ""):
                    competitor_posts.append(post)
            elif competitor["platform"] == "youtube":
                if platform_data.get("channel_title", "").lower() == competitor["name"].lower():
                    competitor_posts.append(post)
            # Add more platform-specific matching logic as needed
        
        # Calculate engagement stats
        total_likes = sum(post["normalized"]["engagement"].get("likes", 0) for post in competitor_posts)
        total_comments = sum(post["normalized"]["engagement"].get("comments", 0) for post in competitor_posts)
        avg_engagement = 0
        if competitor_posts:
            avg_engagement = (total_likes + total_comments) / len(competitor_posts)
        
        return {
            "competitor_id": competitor_id,
            "competitor_name": competitor["name"],
            "platform": competitor["platform"],
            "handle": competitor["handle"],
            "scraped_posts_count": len(competitor_posts),
            "total_likes": total_likes,
            "total_comments": total_comments,
            "avg_engagement_per_post": avg_engagement,
            "current_metrics": competitor["metrics"],
            "last_scraped": competitor["scrape_config"].get("scraped_at"),
            "created_at": competitor["created_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get competitor stats: {str(e)}")


@router.post("/{competitor_id}/scrape", response_model=Dict[str, Any])
async def scrape_competitor(
    competitor_id: str,
    limit: int = Query(10, ge=1, le=50, description="Number of posts to scrape"),
    current_user: dict = Depends(get_current_user)
):
    """
    Manually trigger scraping for a competitor.
    
    - **competitor_id**: Competitor ID
    - **limit**: Number of posts to scrape (default: 10, max: 50)
    """
    try:
        user_id = current_user["id"]
        
        # Check if competitor exists and user owns it
        competitor = await social_media_db.get_competitor_by_id(competitor_id)
        if not competitor:
            raise HTTPException(status_code=404, detail="Competitor not found")
        
        if competitor["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Import here to avoid circular imports
        from tools.unified_scraper import scrape_social_media
        
        # Determine identifier based on platform
        platform = competitor["platform"]
        handle = competitor["handle"]
        
        if platform == "instagram":
            identifier = handle.replace("@", "")
        elif platform == "youtube":
            identifier = handle
        elif platform == "linkedin":
            identifier = competitor["profile_url"]
        elif platform == "reddit":
            identifier = handle.replace("r/", "")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
        
        # Scrape data
        result = await scrape_social_media(
            platform=platform,
            identifier=identifier,
            user_id=user_id,
            brand_id=competitor["brand_id"],
            limit=limit,
            save_to_db=True
        )
        
        if result.get("success"):
            # Update competitor's last scraped time
            await social_media_db.update_competitor_metrics(
                competitor_id, 
                {"last_scraped": datetime.utcnow()}
            )
            
            return {
                "success": True,
                "competitor_id": competitor_id,
                "scraped_count": result.get("count", 0),
                "platform": platform,
                "method_used": result.get("method_used"),
                "timestamp": result.get("timestamp")
            }
        else:
            return {
                "success": False,
                "competitor_id": competitor_id,
                "error": result.get("error", "Unknown error"),
                "platform": platform
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scrape competitor: {str(e)}")


@router.post("/{competitor_id}/duplicate", response_model=CompetitorResponse, status_code=201)
async def duplicate_competitor(
    competitor_id: str,
    new_name: str = Query(..., description="Name for the duplicated competitor"),
    current_user: dict = Depends(get_current_user)
):
    """
    Duplicate an existing competitor with a new name.
    
    - **competitor_id**: Competitor ID to duplicate
    - **new_name**: Name for the new competitor
    """
    try:
        user_id = current_user["id"]
        
        # Check if original competitor exists and user owns it
        original_competitor = await social_media_db.get_competitor_by_id(competitor_id)
        if not original_competitor:
            raise HTTPException(status_code=404, detail="Competitor not found")
        
        if original_competitor["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Create duplicate competitor data
        duplicate_data = {
            "user_id": user_id,
            "brand_id": original_competitor["brand_id"],
            "name": new_name,
            "platform": original_competitor["platform"],
            "handle": original_competitor["handle"],
            "profile_url": original_competitor["profile_url"],
            "metrics": {},
            "scrape_config": original_competitor["scrape_config"],
            "metadata": {
                "duplicated_from": competitor_id,
                "duplicated_at": datetime.utcnow().isoformat()
            }
        }
        
        new_competitor_id = await social_media_db.create_competitor(duplicate_data)
        
        # Return created competitor
        new_competitor = await social_media_db.get_competitor_by_id(new_competitor_id)
        return CompetitorResponse(**new_competitor)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to duplicate competitor: {str(e)}")