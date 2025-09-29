"""
Social Media Database Service

This module provides database operations for social media management including:
- Brand management
- Template management  
- Scraped post storage and retrieval
- Competitor tracking
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from dotenv import load_dotenv

from models.social_media import (
    Brand, Template, ScrapedPost, Competitor,
    PlatformType, TemplateType, TemplateStatus, ProcessingStatus,
    brand_helper, template_helper, scraped_post_helper, competitor_helper
)
from database import get_database

# Load environment variables
load_dotenv()


class SocialMediaDBService:
    """Database service for social media management"""
    
    def __init__(self):
        self.db: Optional[AsyncIOMotorDatabase] = None
    
    async def get_db(self) -> AsyncIOMotorDatabase:
        """Get database instance"""
        if self.db is None:
            self.db = await get_database()
        return self.db
    
    # Brand Operations
    async def create_brand(self, brand_data: Dict[str, Any]) -> str:
        """Create a new brand"""
        db = await self.get_db()
        brand_data["created_at"] = datetime.utcnow()
        brand_data["updated_at"] = datetime.utcnow()
        
        result = await db.brands.insert_one(brand_data)
        return str(result.inserted_id)
    
    async def get_brand_by_id(self, brand_id: str) -> Optional[Dict[str, Any]]:
        """Get brand by ID"""
        db = await self.get_db()
        brand = await db.brands.find_one({"_id": ObjectId(brand_id)})
        return brand_helper(brand)
    
    async def get_brands_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all brands for a user"""
        db = await self.get_db()
        cursor = db.brands.find({"user_id": user_id})
        brands = await cursor.to_list(length=None)
        return [brand_helper(brand) for brand in brands]
    
    async def update_brand(self, brand_id: str, update_data: Dict[str, Any]) -> bool:
        """Update brand data"""
        db = await self.get_db()
        update_data["updated_at"] = datetime.utcnow()
        
        result = await db.brands.update_one(
            {"_id": ObjectId(brand_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def delete_brand(self, brand_id: str) -> bool:
        """Delete a brand"""
        db = await self.get_db()
        result = await db.brands.delete_one({"_id": ObjectId(brand_id)})
        return result.deleted_count > 0
    
    # Template Operations
    async def create_template(self, template_data: Dict[str, Any]) -> str:
        """Create a new template"""
        db = await self.get_db()
        template_data["created_at"] = datetime.utcnow()
        template_data["updated_at"] = datetime.utcnow()
        
        result = await db.templates.insert_one(template_data)
        return str(result.inserted_id)
    
    async def get_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template by ID"""
        db = await self.get_db()
        template = await db.templates.find_one({"_id": ObjectId(template_id)})
        return template_helper(template)
    
    async def get_templates_by_user(self, user_id: str, brand_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get templates for a user, optionally filtered by brand"""
        db = await self.get_db()
        query = {"user_id": user_id}
        if brand_id:
            query["brand_id"] = brand_id
            
        cursor = db.templates.find(query)
        templates = await cursor.to_list(length=None)
        return [template_helper(template) for template in templates]
    
    async def update_template(self, template_id: str, update_data: Dict[str, Any]) -> bool:
        """Update template data"""
        db = await self.get_db()
        update_data["updated_at"] = datetime.utcnow()
        
        result = await db.templates.update_one(
            {"_id": ObjectId(template_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    # Scraped Post Operations
    async def save_scraped_post(self, post_data: Dict[str, Any]) -> str:
        """Save scraped post data to database"""
        db = await self.get_db()
        post_data["scraped_at"] = datetime.utcnow()
        
        result = await db.scraped_posts.insert_one(post_data)
        return str(result.inserted_id)
    
    async def save_scraped_posts_batch(self, posts_data: List[Dict[str, Any]]) -> List[str]:
        """Save multiple scraped posts in batch"""
        db = await self.get_db()
        
        # Add timestamps to all posts
        current_time = datetime.utcnow()
        for post in posts_data:
            post["scraped_at"] = current_time
        
        result = await db.scraped_posts.insert_many(posts_data)
        return [str(post_id) for post_id in result.inserted_ids]
    
    async def get_scraped_posts_by_user(
        self, 
        user_id: str, 
        platform: Optional[PlatformType] = None,
        brand_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get scraped posts for a user with optional filters"""
        db = await self.get_db()
        query = {"user_id": user_id}
        
        if platform:
            query["platform"] = platform.value
        if brand_id:
            query["brand_id"] = brand_id
            
        cursor = db.scraped_posts.find(query).sort("scraped_at", -1).limit(limit)
        posts = await cursor.to_list(length=None)
        return [scraped_post_helper(post) for post in posts]
    
    async def get_scraped_post_by_platform_id(
        self, 
        user_id: str, 
        platform: PlatformType, 
        platform_post_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get scraped post by platform-specific post ID"""
        db = await self.get_db()
        post = await db.scraped_posts.find_one({
            "user_id": user_id,
            "platform": platform.value,
            "normalized.source_id": platform_post_id
        })
        return scraped_post_helper(post)
    
    async def update_post_processing_status(
        self, 
        post_id: str, 
        status: ProcessingStatus, 
        error_message: Optional[str] = None
    ) -> bool:
        """Update post processing status"""
        db = await self.get_db()
        update_data = {
            "processing.status": status.value,
            "processing.normalized_at": datetime.utcnow() if status == ProcessingStatus.NORMALIZED else None
        }
        
        if error_message:
            update_data["processing.error_message"] = error_message
            
        result = await db.scraped_posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    # Competitor Operations
    async def create_competitor(self, competitor_data: Dict[str, Any]) -> str:
        """Create a new competitor entry"""
        db = await self.get_db()
        competitor_data["created_at"] = datetime.utcnow()
        
        result = await db.competitors.insert_one(competitor_data)
        return str(result.inserted_id)
    
    async def get_competitor_by_id(self, competitor_id: str) -> Optional[Dict[str, Any]]:
        """Get competitor by ID"""
        db = await self.get_db()
        competitor = await db.competitors.find_one({"_id": ObjectId(competitor_id)})
        return competitor_helper(competitor)
    
    async def get_competitors_by_user(
        self, 
        user_id: str, 
        platform: Optional[PlatformType] = None,
        brand_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get competitors for a user with optional filters"""
        db = await self.get_db()
        query = {"user_id": user_id}
        
        if platform:
            query["platform"] = platform.value
        if brand_id:
            query["brand_id"] = brand_id
            
        cursor = db.competitors.find(query)
        competitors = await cursor.to_list(length=None)
        return [competitor_helper(competitor) for competitor in competitors]
    
    async def update_competitor_metrics(
        self, 
        competitor_id: str, 
        metrics: Dict[str, Any]
    ) -> bool:
        """Update competitor metrics"""
        db = await self.get_db()
        update_data = {
            "metrics": metrics,
            "scrape_config.scraped_at": datetime.utcnow()
        }
        
        result = await db.competitors.update_one(
            {"_id": ObjectId(competitor_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    # Utility Methods
    async def normalize_scraped_post(
        self, 
        platform_data: Dict[str, Any], 
        platform: PlatformType
    ) -> Dict[str, Any]:
        """Normalize platform-specific data to common format"""
        normalized = {
            "text": None,
            "media": [],
            "posted_at": None,
            "engagement": {},
            "source_id": ""
        }
        
        if platform == PlatformType.INSTAGRAM:
            normalized["text"] = platform_data.get("caption")
            normalized["source_id"] = f"IG_{platform_data.get('post_id', '')}"
            
            # Process media
            if platform_data.get("displayUrl"):
                normalized["media"].append({
                    "type": "image",
                    "url": platform_data["displayUrl"]
                })
            if platform_data.get("videoUrl"):
                normalized["media"].append({
                    "type": "video", 
                    "url": platform_data["videoUrl"]
                })
            if platform_data.get("images"):
                for img_url in platform_data["images"]:
                    normalized["media"].append({
                        "type": "image",
                        "url": img_url
                    })
            
            # Engagement
            normalized["engagement"] = {
                "likes": platform_data.get("likesCount"),
                "comments": platform_data.get("commentsCount")
            }
            
        elif platform == PlatformType.LINKEDIN:
            normalized["text"] = platform_data.get("text")
            normalized["source_id"] = f"LI_{platform_data.get('post_id', '')}"
            
            # Process media
            if platform_data.get("postImages"):
                for img_obj in platform_data["postImages"]:
                    if isinstance(img_obj, dict) and "url" in img_obj:
                        normalized["media"].append({
                            "type": "image",
                            "url": img_obj["url"]
                        })
            
            # Engagement
            normalized["engagement"] = {
                "likes": platform_data.get("likesCount"),
                "comments": platform_data.get("commentsCount"),
                "shares": platform_data.get("sharesCount")
            }
            
        elif platform == PlatformType.YOUTUBE:
            normalized["text"] = platform_data.get("title")
            normalized["source_id"] = f"YT_{platform_data.get('video_id', '')}"
            
            # Process media
            if platform_data.get("thumbnail_url"):
                normalized["media"].append({
                    "type": "image",
                    "url": platform_data["thumbnail_url"]
                })
            
            # Engagement
            normalized["engagement"] = {
                "likes": platform_data.get("like_count"),
                "comments": platform_data.get("comment_count"),
                "views": platform_data.get("view_count")
            }
            
        elif platform == PlatformType.REDDIT:
            normalized["text"] = platform_data.get("title")
            if platform_data.get("selftext"):
                normalized["text"] += f"\n\n{platform_data['selftext']}"
            normalized["source_id"] = f"RD_{platform_data.get('id', '')}"
            
            # Process media
            if platform_data.get("url") and not platform_data.get("selftext"):
                # External link or media (not a self post)
                normalized["media"].append({
                    "type": "link",
                    "url": platform_data["url"]
                })
            
            # Engagement
            normalized["engagement"] = {
                "likes": platform_data.get("upvotes"),
                "comments": platform_data.get("num_comments")
            }
        
        return normalized


# Global service instance
social_media_db = SocialMediaDBService()