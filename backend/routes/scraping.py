"""
Social Media Scraping API Routes

This module provides endpoints for social media scraping including:
- Unified scraping across all platforms
- Scraping with database storage
- Scraping status and progress tracking
- Batch scraping operations
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import asyncio

from tools.unified_scraper import scrape_social_media
from services.social_media_db import social_media_db
from models.social_media import PlatformType
from services.auth import get_current_user

router = APIRouter(prefix="/api/scraping", tags=["scraping"])


# Request/Response Models
class ScrapingRequest(BaseModel):
    platform: PlatformType = Field(..., description="Social media platform")
    identifier: str = Field(..., min_length=1, description="Username, profile URL, or subreddit name")
    brand_id: Optional[str] = Field(None, description="Brand ID if scraping for a specific brand")
    handle_id: Optional[str] = Field(None, description="Handle ID from brands.handles")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results to fetch")
    days_back: Optional[int] = Field(None, ge=1, le=365, description="Number of days to look back for content")
    category: Optional[str] = Field(None, description="Category for Reddit ('hot', 'rising', 'new', 'top')")
    min_score: Optional[int] = Field(None, ge=0, description="Minimum score for Reddit posts")
    min_comments: Optional[int] = Field(None, ge=0, description="Minimum comments for Reddit posts")
    save_to_db: bool = Field(True, description="Whether to save scraped data to database")
    api_token: Optional[str] = Field(None, description="API token for Apify services")
    api_key: Optional[str] = Field(None, description="API key for YouTube")


class BatchScrapingRequest(BaseModel):
    requests: List[ScrapingRequest] = Field(..., min_length=1, max_length=10, description="List of scraping requests")
    save_to_db: bool = Field(True, description="Whether to save scraped data to database")


class ScrapingResponse(BaseModel):
    success: bool
    platform: str
    identifier: str
    method_used: Optional[str] = None
    data: List[Dict[str, Any]] = []
    count: int = 0
    saved_to_db: bool = False
    saved_ids: List[str] = []
    timestamp: str
    error: Optional[str] = None


class BatchScrapingResponse(BaseModel):
    total_requests: int
    successful: int
    failed: int
    results: List[ScrapingResponse]
    timestamp: str


class ScrapingStatusResponse(BaseModel):
    platform: str
    identifier: str
    status: str
    progress: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Scraping Operations
@router.post("/scrape", response_model=ScrapingResponse)
async def scrape_single(
    request: ScrapingRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Scrape data from a single social media platform.
    
    - **platform**: Social media platform (required)
    - **identifier**: Username, profile URL, or subreddit name (required)
    - **brand_id**: Brand ID if scraping for a specific brand (optional)
    - **handle_id**: Handle ID from brands.handles (optional)
    - **limit**: Maximum number of results to fetch (default: 10, max: 100)
    - **days_back**: Number of days to look back for content (optional)
    - **category**: Category for Reddit (optional)
    - **min_score**: Minimum score for Reddit posts (optional)
    - **min_comments**: Minimum comments for Reddit posts (optional)
    - **save_to_db**: Whether to save scraped data to database (default: True)
    - **api_token**: API token for Apify services (optional)
    - **api_key**: API key for YouTube (optional)
    """
    try:
        user_id = current_user["id"]
        
        # Validate brand_id if provided
        if request.brand_id:
            brand = await social_media_db.get_brand_by_id(request.brand_id)
            if not brand:
                raise HTTPException(status_code=404, detail="Brand not found")
            if brand["user_id"] != user_id:
                raise HTTPException(status_code=403, detail="Access denied to brand")
        
        # Perform scraping
        result = await scrape_social_media(
            platform=request.platform.value,
            identifier=request.identifier,
            user_id=user_id,
            brand_id=request.brand_id,
            handle_id=request.handle_id,
            limit=request.limit,
            days_back=request.days_back,
            category=request.category,
            min_score=request.min_score,
            min_comments=request.min_comments,
            api_token=request.api_token,
            api_key=request.api_key,
            save_to_db=request.save_to_db
        )
        
        # Prepare response
        response = ScrapingResponse(
            success=result.get("success", False),
            platform=result.get("platform", request.platform.value),
            identifier=result.get("identifier", request.identifier),
            method_used=result.get("method_used"),
            data=result.get("data", []),
            count=result.get("count", 0),
            saved_to_db=request.save_to_db and result.get("success", False),
            saved_ids=[],  # Will be populated if we track saved IDs
            timestamp=result.get("timestamp", datetime.utcnow().isoformat()),
            error=result.get("error")
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        return ScrapingResponse(
            success=False,
            platform=request.platform.value,
            identifier=request.identifier,
            timestamp=datetime.utcnow().isoformat(),
            error=str(e)
        )


@router.post("/scrape/batch", response_model=BatchScrapingResponse)
async def scrape_batch(
    request: BatchScrapingRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Scrape data from multiple social media platforms in batch.
    
    - **requests**: List of scraping requests (max 10)
    - **save_to_db**: Whether to save scraped data to database (default: True)
    """
    try:
        user_id = current_user["id"]
        
        if len(request.requests) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 requests allowed per batch")
        
        # Validate all brand_ids if provided
        brand_ids = set(req.brand_id for req in request.requests if req.brand_id)
        for brand_id in brand_ids:
            brand = await social_media_db.get_brand_by_id(brand_id)
            if not brand:
                raise HTTPException(status_code=404, detail=f"Brand not found: {brand_id}")
            if brand["user_id"] != user_id:
                raise HTTPException(status_code=403, detail=f"Access denied to brand: {brand_id}")
        
        # Process all requests
        results = []
        successful = 0
        failed = 0
        
        for req in request.requests:
            try:
                # Perform scraping
                result = await scrape_social_media(
                    platform=req.platform.value,
                    identifier=req.identifier,
                    user_id=user_id,
                    brand_id=req.brand_id,
                    handle_id=req.handle_id,
                    limit=req.limit,
                    days_back=req.days_back,
                    category=req.category,
                    min_score=req.min_score,
                    min_comments=req.min_comments,
                    api_token=req.api_token,
                    api_key=req.api_key,
                    save_to_db=request.save_to_db
                )
                
                # Create response
                response = ScrapingResponse(
                    success=result.get("success", False),
                    platform=result.get("platform", req.platform.value),
                    identifier=result.get("identifier", req.identifier),
                    method_used=result.get("method_used"),
                    data=result.get("data", []),
                    count=result.get("count", 0),
                    saved_to_db=request.save_to_db and result.get("success", False),
                    saved_ids=[],
                    timestamp=result.get("timestamp", datetime.utcnow().isoformat()),
                    error=result.get("error")
                )
                
                results.append(response)
                
                if result.get("success", False):
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                # Handle individual request failure
                response = ScrapingResponse(
                    success=False,
                    platform=req.platform.value,
                    identifier=req.identifier,
                    timestamp=datetime.utcnow().isoformat(),
                    error=str(e)
                )
                results.append(response)
                failed += 1
        
        return BatchScrapingResponse(
            total_requests=len(request.requests),
            successful=successful,
            failed=failed,
            results=results,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch scraping failed: {str(e)}")


@router.get("/platforms", response_model=Dict[str, Any])
async def get_supported_platforms():
    """
    Get list of supported platforms and their requirements.
    """
    try:
        from tools.unified_scraper import get_supported_platforms, get_platform_info
        
        platforms = get_supported_platforms()
        platform_info = {}
        
        for platform in platforms:
            try:
                info = get_platform_info(platform)
                platform_info[platform] = info
            except:
                platform_info[platform] = {
                    "identifier_type": "unknown",
                    "description": f"Scraping support for {platform}"
                }
        
        return {
            "supported_platforms": platforms,
            "platform_info": platform_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get platform info: {str(e)}")


@router.get("/status/{platform}/{identifier}", response_model=ScrapingStatusResponse)
async def get_scraping_status(
    platform: str,
    identifier: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get scraping status for a specific platform and identifier.
    
    - **platform**: Social media platform
    - **identifier**: Username, profile URL, or subreddit name
    """
    try:
        user_id = current_user["id"]
        
        # Check if we have recent scraped data for this platform/identifier
        posts = await social_media_db.get_scraped_posts_by_user(
            user_id=user_id,
            platform=PlatformType(platform),
            limit=1000
        )
        
        # Filter posts by identifier (basic matching)
        relevant_posts = []
        for post in posts:
            platform_data = post.get("platform_data", {})
            if platform == "instagram":
                if platform_data.get("username") == identifier.replace("@", ""):
                    relevant_posts.append(post)
            elif platform == "youtube":
                if platform_data.get("channel_title", "").lower() == identifier.lower():
                    relevant_posts.append(post)
            elif platform == "reddit":
                if platform_data.get("subreddit") == identifier.replace("r/", ""):
                    relevant_posts.append(post)
            # Add more platform-specific matching as needed
        
        if relevant_posts:
            # Get the most recent post
            latest_post = max(relevant_posts, key=lambda x: x["scraped_at"])
            
            return ScrapingStatusResponse(
                platform=platform,
                identifier=identifier,
                status="completed",
                progress={
                    "last_scraped": latest_post["scraped_at"],
                    "total_posts": len(relevant_posts),
                    "processing_status": latest_post["processing"]["status"]
                }
            )
        else:
            return ScrapingStatusResponse(
                platform=platform,
                identifier=identifier,
                status="not_found",
                progress={
                    "total_posts": 0
                }
            )
        
    except Exception as e:
        return ScrapingStatusResponse(
            platform=platform,
            identifier=identifier,
            status="error",
            error=str(e)
        )


@router.post("/competitor/{competitor_id}/scrape", response_model=ScrapingResponse)
async def scrape_competitor(
    competitor_id: str,
    limit: int = Query(10, ge=1, le=50, description="Number of posts to scrape"),
    current_user: dict = Depends(get_current_user)
):
    """
    Scrape data for a specific competitor.
    
    - **competitor_id**: Competitor ID
    - **limit**: Number of posts to scrape (default: 10, max: 50)
    """
    try:
        user_id = current_user["id"]
        
        # Get competitor
        competitor = await social_media_db.get_competitor_by_id(competitor_id)
        if not competitor:
            raise HTTPException(status_code=404, detail="Competitor not found")
        
        if competitor["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
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
        
        # Perform scraping
        result = await scrape_social_media(
            platform=platform,
            identifier=identifier,
            user_id=user_id,
            brand_id=competitor["brand_id"],
            limit=limit,
            save_to_db=True
        )
        
        # Update competitor's last scraped time
        if result.get("success"):
            await social_media_db.update_competitor_metrics(
                competitor_id, 
                {"last_scraped": datetime.utcnow()}
            )
        
        # Prepare response
        response = ScrapingResponse(
            success=result.get("success", False),
            platform=result.get("platform", platform),
            identifier=result.get("identifier", identifier),
            method_used=result.get("method_used"),
            data=result.get("data", []),
            count=result.get("count", 0),
            saved_to_db=True,
            saved_ids=[],
            timestamp=result.get("timestamp", datetime.utcnow().isoformat()),
            error=result.get("error")
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scrape competitor: {str(e)}")


@router.get("/history", response_model=Dict[str, Any])
async def get_scraping_history(
    current_user: dict = Depends(get_current_user),
    platform: Optional[PlatformType] = Query(None, description="Filter by platform"),
    brand_id: Optional[str] = Query(None, description="Filter by brand ID"),
    days_back: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Get scraping history for the user.
    
    - **platform**: Filter by platform (optional)
    - **brand_id**: Filter by brand ID (optional)
    - **days_back**: Number of days to look back (default: 7)
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    """
    try:
        user_id = current_user["id"]
        
        # Calculate date range
        date_to = datetime.utcnow()
        date_from = date_to - timedelta(days=days_back)
        
        # Get scraped posts
        all_posts = await social_media_db.get_scraped_posts_by_user(
            user_id=user_id,
            platform=platform,
            brand_id=brand_id,
            limit=10000
        )
        
        # Filter by date range
        filtered_posts = [
            p for p in all_posts 
            if date_from <= p["scraped_at"] <= date_to
        ]
        
        # Group by platform and identifier
        scraping_sessions = {}
        for post in filtered_posts:
            platform = post["platform"]
            platform_data = post["platform_data"]
            
            # Determine identifier
            if platform == "instagram":
                identifier = platform_data.get("username", "unknown")
            elif platform == "youtube":
                identifier = platform_data.get("channel_title", "unknown")
            elif platform == "reddit":
                identifier = platform_data.get("subreddit", "unknown")
            elif platform == "linkedin":
                identifier = platform_data.get("profile_url", "unknown")
            else:
                identifier = "unknown"
            
            key = f"{platform}:{identifier}"
            if key not in scraping_sessions:
                scraping_sessions[key] = {
                    "platform": platform,
                    "identifier": identifier,
                    "first_scraped": post["scraped_at"],
                    "last_scraped": post["scraped_at"],
                    "total_posts": 0,
                    "brand_id": post.get("brand_id")
                }
            
            session = scraping_sessions[key]
            session["total_posts"] += 1
            session["last_scraped"] = max(session["last_scraped"], post["scraped_at"])
        
        # Convert to list and sort by last scraped
        sessions_list = list(scraping_sessions.values())
        sessions_list.sort(key=lambda x: x["last_scraped"], reverse=True)
        
        # Apply pagination
        total = len(sessions_list)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_sessions = sessions_list[start_idx:end_idx]
        
        return {
            "sessions": paginated_sessions,
            "total": total,
            "page": page,
            "limit": limit,
            "date_range": {
                "from": date_from,
                "to": date_to
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scraping history: {str(e)}")