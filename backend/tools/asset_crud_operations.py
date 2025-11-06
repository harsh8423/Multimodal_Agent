#!/usr/bin/env python3
"""
Asset CRUD Operations Tool for Asset Agent

This tool provides CRUD (Create, Read, Update, Delete) operations for
brands, competitors, templates, and scraped posts through direct database access.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os

# Add the backend directory to the path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.social_media_db import SocialMediaDBService


async def create_brand(user_id: str, brand_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new brand
    
    Args:
        user_id (str): User ID
        brand_data (Dict[str, Any]): Brand data including name, description, etc.
    
    Returns:
        Dict[str, Any]: Created brand data or error information
    """
    try:
        # Add user_id to brand data
        brand_data["user_id"] = user_id
        
        # Use database service directly
        db_service = SocialMediaDBService()
        brand_id = await db_service.create_brand(brand_data)
        
        # Get the created brand to return
        created_brand = await db_service.get_brand_by_id(brand_id)
        
        return {
            "success": True,
            "data": created_brand,
            "brand_id": brand_id,
            "message": "Brand created successfully"
        }
                
    except Exception as e:
        return {
            "success": False,
            "error": f"Error creating brand: {str(e)}"
        }


async def update_brand(user_id: str, brand_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing brand
    
    Args:
        user_id (str): User ID
        brand_id (str): Brand ID to update
        update_data (Dict[str, Any]): Updated brand data
    
    Returns:
        Dict[str, Any]: Updated brand data or error information
    """
    try:
        # Use database service directly
        db_service = SocialMediaDBService()
        
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        # Update the brand
        await db_service.update_brand(brand_id, update_data)
        
        # Get the updated brand to return
        updated_brand = await db_service.get_brand_by_id(brand_id)
        
        return {
            "success": True,
            "data": updated_brand,
            "message": "Brand updated successfully"
        }
                
    except Exception as e:
        return {
            "success": False,
            "error": f"Error updating brand: {str(e)}"
        }


async def delete_brand(user_id: str, brand_id: str) -> Dict[str, Any]:
    """
    Delete a brand
    
    Args:
        user_id (str): User ID
        brand_id (str): Brand ID to delete
    
    Returns:
        Dict[str, Any]: Deletion result or error information
    """
    try:
        # Use database service directly
        db_service = SocialMediaDBService()
        await db_service.delete_brand(brand_id)
        
        return {
            "success": True,
            "message": "Brand deleted successfully"
        }
                
    except Exception as e:
        return {
            "success": False,
            "error": f"Error deleting brand: {str(e)}"
        }


async def create_competitor(user_id: str, competitor_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new competitor
    
    Args:
        user_id (str): User ID
        competitor_data (Dict[str, Any]): Competitor data
    
    Returns:
        Dict[str, Any]: Created competitor data or error information
    """
    try:
        # Add user_id to competitor data
        competitor_data["user_id"] = user_id
        
        # Use database service directly
        db_service = SocialMediaDBService()
        competitor_id = await db_service.create_competitor(competitor_data)
        
        # Get the created competitor to return
        created_competitor = await db_service.get_competitor_by_id(competitor_id)
        
        return {
            "success": True,
            "data": created_competitor,
            "competitor_id": competitor_id,
            "message": "Competitor created successfully"
        }
                
    except Exception as e:
        return {
            "success": False,
            "error": f"Error creating competitor: {str(e)}"
        }


async def update_competitor(user_id: str, competitor_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing competitor
    
    Args:
        user_id (str): User ID
        competitor_id (str): Competitor ID to update
        update_data (Dict[str, Any]): Updated competitor data
    
    Returns:
        Dict[str, Any]: Updated competitor data or error information
    """
    try:
        # Use database service directly
        db_service = SocialMediaDBService()
        
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        # Update the competitor
        await db_service.update_competitor(competitor_id, update_data)
        
        # Get the updated competitor to return
        updated_competitor = await db_service.get_competitor_by_id(competitor_id)
        
        return {
            "success": True,
            "data": updated_competitor,
            "message": "Competitor updated successfully"
        }
                
    except Exception as e:
        return {
            "success": False,
            "error": f"Error updating competitor: {str(e)}"
        }


async def delete_competitor(user_id: str, competitor_id: str) -> Dict[str, Any]:
    """
    Delete a competitor
    
    Args:
        user_id (str): User ID
        competitor_id (str): Competitor ID to delete
    
    Returns:
        Dict[str, Any]: Deletion result or error information
    """
    try:
        # Use database service directly
        db_service = SocialMediaDBService()
        await db_service.delete_competitor(competitor_id)
        
        return {
            "success": True,
            "message": "Competitor deleted successfully"
        }
                
    except Exception as e:
        return {
            "success": False,
            "error": f"Error deleting competitor: {str(e)}"
        }


async def create_template(user_id: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new template
    
    Args:
        user_id (str): User ID
        template_data (Dict[str, Any]): Template data
    
    Returns:
        Dict[str, Any]: Created template data or error information
    """
    try:
        # Add user_id to template data
        template_data["user_id"] = user_id
        
        # Use database service directly
        db_service = SocialMediaDBService()
        template_id = await db_service.create_template(template_data)
        
        # Get the created template to return
        created_template = await db_service.get_template_by_id(template_id)
        
        return {
            "success": True,
            "data": created_template,
            "template_id": template_id,
            "message": "Template created successfully"
        }
                
    except Exception as e:
        return {
            "success": False,
            "error": f"Error creating template: {str(e)}"
        }


async def update_template(user_id: str, template_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing template
    
    Args:
        user_id (str): User ID
        template_id (str): Template ID to update
        update_data (Dict[str, Any]): Updated template data
    
    Returns:
        Dict[str, Any]: Updated template data or error information
    """
    try:
        # Use database service directly
        db_service = SocialMediaDBService()
        
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        # Update the template
        await db_service.update_template(template_id, update_data)
        
        # Get the updated template to return
        updated_template = await db_service.get_template_by_id(template_id)
        
        return {
            "success": True,
            "data": updated_template,
            "message": "Template updated successfully"
        }
                
    except Exception as e:
        return {
            "success": False,
            "error": f"Error updating template: {str(e)}"
        }


async def delete_template(user_id: str, template_id: str) -> Dict[str, Any]:
    """
    Delete a template
    
    Args:
        user_id (str): User ID
        template_id (str): Template ID to delete
    
    Returns:
        Dict[str, Any]: Deletion result or error information
    """
    try:
        # Use database service directly
        db_service = SocialMediaDBService()
        await db_service.delete_template(template_id)
        
        return {
            "success": True,
            "message": "Template deleted successfully"
        }
                
    except Exception as e:
        return {
            "success": False,
            "error": f"Error deleting template: {str(e)}"
        }


async def scrape_competitor_data(user_id: str, competitor_id: str, limit: int = 10) -> Dict[str, Any]:
    """
    Scrape data for a competitor
    
    Args:
        user_id (str): User ID
        competitor_id (str): Competitor ID to scrape
        limit (int): Number of posts to scrape
    
    Returns:
        Dict[str, Any]: Scraping result or error information
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/competitors/{competitor_id}/scrape?limit={limit}"
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "message": f"Successfully scraped {limit} posts from competitor"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to scrape competitor data: {response.text}",
                    "status_code": response.status_code
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": f"Error scraping competitor data: {str(e)}"
        }


async def perform_bulk_scraping(user_id: str, scraping_requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Perform bulk scraping operations
    
    Args:
        user_id (str): User ID
        scraping_requests (List[Dict[str, Any]]): List of scraping requests
    
    Returns:
        Dict[str, Any]: Bulk scraping results or error information
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/scraping/scrape/batch",
                json={"requests": scraping_requests},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "message": f"Successfully processed {len(scraping_requests)} scraping requests"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to perform bulk scraping: {response.text}",
                    "status_code": response.status_code
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": f"Error performing bulk scraping: {str(e)}"
        }

