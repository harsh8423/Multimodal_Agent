"""
Social Media Management Database Models

This module defines MongoDB models for social media asset management including:
- Brands: User brand data with themes, descriptions, and settings
- Templates: Flexible, versioned templates for social media posts
- Scraped Posts: Platform-specific scraped data with normalized fields
- Competitors: Platform-agnostic competitor/reference account tracking
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from bson import ObjectId
from enum import Enum


class PlatformType(str, Enum):
    """Supported social media platforms"""
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"
    REDDIT = "reddit"
    WEB = "web"


class TemplateType(str, Enum):
    """Template types for social media content"""
    INSTAGRAM_POST = "instagram_post"
    LINKEDIN_POST = "linkedin_post"
    REEL = "reel"
    SHORT = "short"
    CAROUSEL = "carousel"
    IMAGE_POST = "image_post"


class TemplateStatus(str, Enum):
    """Template status options"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"


class ProcessingStatus(str, Enum):
    """Processing status for scraped posts"""
    PENDING = "pending"
    PROCESSING = "processing"
    NORMALIZED = "normalized"
    FAILED = "failed"


# Brand Models
class BrandTheme(BaseModel):
    """Brand theme configuration"""
    primary_color: str = Field(..., description="Primary brand color in hex format")
    secondary_color: str = Field(..., description="Secondary brand color in hex format")
    font: str = Field(..., description="Primary font family")
    logo_url: Optional[str] = Field(None, description="Brand logo URL")


class BrandDetails(BaseModel):
    """Brand business details"""
    website: Optional[str] = Field(None, description="Brand website URL")
    industry: Optional[str] = Field(None, description="Industry category")
    audience: List[str] = Field(default_factory=list, description="Target audience segments")


class DefaultPostingSettings(BaseModel):
    """Default posting configuration"""
    timezone: str = Field(default="UTC", description="Default timezone for posting")
    default_platforms: List[PlatformType] = Field(default_factory=list, description="Default platforms for posting")
    post_approval_required: bool = Field(default=False, description="Whether posts require approval")


class Brand(BaseModel):
    """Brand model for user brand management"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(..., description="User ID who owns this brand")
    name: str = Field(..., description="Brand name")
    slug: str = Field(..., description="URL-friendly brand identifier, unique per user")
    description: str = Field(..., description="Brand description")
    theme: BrandTheme = Field(..., description="Brand visual theme")
    details: BrandDetails = Field(..., description="Brand business details")
    default_posting_settings: DefaultPostingSettings = Field(default_factory=DefaultPostingSettings)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible metadata")

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


# Template Models
class Scene(BaseModel):
    """Scene definition for video templates"""
    scene_id: int = Field(..., description="Unique scene identifier")
    duration_sec: int = Field(..., description="Scene duration in seconds")
    instructions: str = Field(..., description="Scene instructions")
    visual_hints: List[str] = Field(default_factory=list, description="Visual direction hints")
    audio_cue: Optional[str] = Field(None, description="Audio cue for this scene")
    hooks: List[str] = Field(default_factory=list, description="Hook suggestions for this scene")


class Hook(BaseModel):
    """Hook definition for content templates"""
    position: str = Field(..., description="Hook position (start, mid, end)")
    example: Optional[str] = Field(None, description="Example hook text")
    cta: Optional[str] = Field(None, description="Call-to-action text")


class TemplateTheme(BaseModel):
    """Template visual theme"""
    mood: str = Field(..., description="Content mood (playful, professional, etc.)")
    color_palette: List[str] = Field(..., description="Color palette in hex format")
    preferred_aspect: List[str] = Field(..., description="Preferred aspect ratios")


class TemplateStructure(BaseModel):
    """Template structure and content guidelines"""
    description: str = Field(..., description="Template description")
    scenes: List[Scene] = Field(default_factory=list, description="Video scenes")
    hooks: List[Hook] = Field(default_factory=list, description="Content hooks")
    placeholders: List[str] = Field(default_factory=list, description="Content placeholders")
    theme: TemplateTheme = Field(..., description="Template visual theme")
    description_prompt: Optional[str] = Field(None, description="Caption generation prompt")


class TemplateReferences(BaseModel):
    """Template reference materials"""
    images: List[str] = Field(default_factory=list, description="Reference image URLs")
    videos: List[str] = Field(default_factory=list, description="Reference video URLs")
    notes: Optional[str] = Field(None, description="Reference notes")


class Template(BaseModel):
    """Template model for social media content"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(..., description="User ID who owns this template")
    brand_id: Optional[str] = Field(None, description="Brand ID if template is brand-specific")
    name: str = Field(..., description="Template name")
    type: TemplateType = Field(..., description="Template type")
    version: int = Field(default=1, description="Template version number")
    status: TemplateStatus = Field(default=TemplateStatus.ACTIVE, description="Template status")
    structure: TemplateStructure = Field(..., description="Template structure")
    references: TemplateReferences = Field(default_factory=TemplateReferences, description="Reference materials")
    assets: List[str] = Field(default_factory=list, description="Pre-filled asset IDs")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible metadata")

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


# Scraped Posts Models
class MediaItem(BaseModel):
    """Normalized media item"""
    type: str = Field(..., description="Media type (image, video)")
    url: str = Field(..., description="Media URL (Cloudinary CDN URL)")


class EngagementMetrics(BaseModel):
    """Engagement metrics"""
    likes: Optional[int] = Field(None, description="Number of likes")
    comments: Optional[int] = Field(None, description="Number of comments")
    shares: Optional[int] = Field(None, description="Number of shares")
    views: Optional[int] = Field(None, description="Number of views")


class NormalizedPost(BaseModel):
    """Normalized post data for cross-platform queries"""
    text: Optional[str] = Field(None, description="Post text content")
    media: List[MediaItem] = Field(default_factory=list, description="Media items")
    posted_at: Optional[datetime] = Field(None, description="Post publication date")
    engagement: EngagementMetrics = Field(default_factory=EngagementMetrics, description="Engagement metrics")
    source_id: str = Field(..., description="Platform-specific post ID")


class ProcessingInfo(BaseModel):
    """Processing information for scraped posts"""
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING, description="Processing status")
    pipeline: str = Field(..., description="Processing pipeline version")
    normalized_at: Optional[datetime] = Field(None, description="When normalization was completed")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")


class ScrapedPost(BaseModel):
    """Scraped post model with platform-specific and normalized data"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(..., description="User ID who is tracking this post")
    brand_id: Optional[str] = Field(None, description="Brand ID if post belongs to a brand")
    handle_id: Optional[str] = Field(None, description="Handle ID from brands.handles")
    platform: PlatformType = Field(..., description="Social media platform")
    source: str = Field(..., description="Scraping source/method")
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="When the post was scraped")
    platform_data: Dict[str, Any] = Field(..., description="Platform-specific raw data")
    normalized: NormalizedPost = Field(..., description="Normalized post data")
    processing: ProcessingInfo = Field(..., description="Processing information")
    important: bool = Field(default=False, description="Whether the post is marked as important")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible metadata")

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


# Competitor Models
class CompetitorMetrics(BaseModel):
    """Competitor account metrics"""
    followers: Optional[int] = Field(None, description="Follower count")
    avg_engagement: Optional[float] = Field(None, description="Average engagement rate")
    posts_count: Optional[int] = Field(None, description="Total posts count")
    last_post_date: Optional[datetime] = Field(None, description="Last post date")


class ScrapeConfig(BaseModel):
    """Scraping configuration for competitors"""
    scraped_at: Optional[datetime] = Field(None, description="Last scrape date")
    scrape_frequency: str = Field(default="weekly", description="How often to scrape")
    auto_scrape: bool = Field(default=False, description="Whether to auto-scrape")


class Competitor(BaseModel):
    """Competitor/reference account model"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(..., description="User ID who is tracking this competitor")
    brand_id: Optional[str] = Field(None, description="Brand ID if competitor is tied to a brand")
    name: str = Field(..., description="Competitor name")
    platform: PlatformType = Field(..., description="Social media platform")
    handle: str = Field(..., description="Platform handle/username")
    profile_url: str = Field(..., description="Profile URL")
    metrics: CompetitorMetrics = Field(default_factory=CompetitorMetrics, description="Account metrics")
    scrape_config: ScrapeConfig = Field(default_factory=ScrapeConfig, description="Scraping configuration")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


# Helper functions for MongoDB operations
def brand_helper(brand) -> dict:
    """Convert MongoDB brand document to dict"""
    if brand:
        return {
            "id": str(brand["_id"]),
            "user_id": brand["user_id"],
            "name": brand["name"],
            "slug": brand["slug"],
            "description": brand["description"],
            "theme": brand["theme"],
            "details": brand["details"],
            "default_posting_settings": brand["default_posting_settings"],
            "created_at": brand["created_at"],
            "updated_at": brand["updated_at"],
            "metadata": brand.get("metadata", {})
        }
    return None


def template_helper(template) -> dict:
    """Convert MongoDB template document to dict"""
    if template:
        return {
            "id": str(template["_id"]),
            "user_id": template["user_id"],
            "brand_id": template.get("brand_id"),
            "name": template["name"],
            "type": template["type"],
            "version": template["version"],
            "status": template["status"],
            "structure": template["structure"],
            "references": template.get("references", {}),
            "assets": template.get("assets", []),
            "created_at": template["created_at"],
            "updated_at": template["updated_at"],
            "metadata": template.get("metadata", {})
        }
    return None


def scraped_post_helper(post) -> dict:
    """Convert MongoDB scraped post document to dict"""
    if post:
        return {
            "id": str(post["_id"]),
            "user_id": post["user_id"],
            "brand_id": post.get("brand_id"),
            "handle_id": post.get("handle_id"),
            "platform": post["platform"],
            "source": post["source"],
            "scraped_at": post["scraped_at"],
            "platform_data": post["platform_data"],
            "normalized": post["normalized"],
            "processing": post["processing"],
            "important": post.get("important", False),
            "metadata": post.get("metadata", {})
        }
    return None


def competitor_helper(competitor) -> dict:
    """Convert MongoDB competitor document to dict"""
    if competitor:
        return {
            "id": str(competitor["_id"]),
            "user_id": competitor["user_id"],
            "brand_id": competitor.get("brand_id"),
            "name": competitor["name"],
            "platform": competitor["platform"],
            "handle": competitor["handle"],
            "profile_url": competitor["profile_url"],
            "metrics": competitor.get("metrics", {}),
            "scrape_config": competitor.get("scrape_config", {}),
            "metadata": competitor.get("metadata", {}),
            "created_at": competitor["created_at"]
        }
    return None