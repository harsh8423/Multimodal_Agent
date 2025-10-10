#!/usr/bin/env python3
"""
Asset CRUD Operations Tool for Asset Agent

This tool provides CRUD (Create, Read, Update, Delete) operations for
brands, competitors, templates, and scraped posts through the existing API routes.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import httpx


# Base API configuration
API_BASE_URL = "http://localhost:8000"


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
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/brands/",
                json=brand_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "message": "Brand created successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create brand: {response.text}",
                    "status_code": response.status_code
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
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{API_BASE_URL}/api/brands/{brand_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "message": "Brand updated successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to update brand: {response.text}",
                    "status_code": response.status_code
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
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{API_BASE_URL}/api/brands/{brand_id}")
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Brand deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to delete brand: {response.text}",
                    "status_code": response.status_code
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
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/competitors/",
                json=competitor_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "message": "Competitor created successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create competitor: {response.text}",
                    "status_code": response.status_code
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
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{API_BASE_URL}/api/competitors/{competitor_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "message": "Competitor updated successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to update competitor: {response.text}",
                    "status_code": response.status_code
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
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{API_BASE_URL}/api/competitors/{competitor_id}")
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Competitor deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to delete competitor: {response.text}",
                    "status_code": response.status_code
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
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/templates/",
                json=template_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "message": "Template created successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create template: {response.text}",
                    "status_code": response.status_code
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
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{API_BASE_URL}/api/templates/{template_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "message": "Template updated successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to update template: {response.text}",
                    "status_code": response.status_code
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
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{API_BASE_URL}/api/templates/{template_id}")
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Template deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to delete template: {response.text}",
                    "status_code": response.status_code
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


# Synchronous wrappers for compatibility with existing tool router
def create_brand_sync(user_id: str, brand_data: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous wrapper for create_brand"""
    return asyncio.run(create_brand(user_id, brand_data))


def update_brand_sync(user_id: str, brand_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous wrapper for update_brand"""
    return asyncio.run(update_brand(user_id, brand_id, update_data))


def delete_brand_sync(user_id: str, brand_id: str) -> Dict[str, Any]:
    """Synchronous wrapper for delete_brand"""
    return asyncio.run(delete_brand(user_id, brand_id))


def create_competitor_sync(user_id: str, competitor_data: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous wrapper for create_competitor"""
    return asyncio.run(create_competitor(user_id, competitor_data))


def update_competitor_sync(user_id: str, competitor_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous wrapper for update_competitor"""
    return asyncio.run(update_competitor(user_id, competitor_id, update_data))


def delete_competitor_sync(user_id: str, competitor_id: str) -> Dict[str, Any]:
    """Synchronous wrapper for delete_competitor"""
    return asyncio.run(delete_competitor(user_id, competitor_id))


def create_template_sync(user_id: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous wrapper for create_template"""
    return asyncio.run(create_template(user_id, template_data))


def update_template_sync(user_id: str, template_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous wrapper for update_template"""
    return asyncio.run(update_template(user_id, template_id, update_data))


def delete_template_sync(user_id: str, template_id: str) -> Dict[str, Any]:
    """Synchronous wrapper for delete_template"""
    return asyncio.run(delete_template(user_id, template_id))


def scrape_competitor_data_sync(user_id: str, competitor_id: str, limit: int = 10) -> Dict[str, Any]:
    """Synchronous wrapper for scrape_competitor_data"""
    return asyncio.run(scrape_competitor_data(user_id, competitor_id, limit))


def perform_bulk_scraping_sync(user_id: str, scraping_requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Synchronous wrapper for perform_bulk_scraping"""
    return asyncio.run(perform_bulk_scraping(user_id, scraping_requests))