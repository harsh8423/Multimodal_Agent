"""
Template Management API Routes

This module provides CRUD operations for template management including:
- Create, read, update, delete templates
- Template versioning and status management
- Template structure and reference management
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio

from services.social_media_db import social_media_db
from models.social_media import (
    Template, TemplateType, TemplateStatus, TemplateStructure, 
    TemplateReferences, Scene, Hook, TemplateTheme
)
from services.auth import get_current_user

router = APIRouter(prefix="/api/templates", tags=["templates"])


# Request/Response Models
class SceneRequest(BaseModel):
    scene_id: int = Field(..., description="Unique scene identifier")
    duration_sec: int = Field(..., ge=1, description="Scene duration in seconds")
    instructions: str = Field(..., min_length=1, description="Scene instructions")
    visual_hints: List[str] = Field(default_factory=list, description="Visual direction hints")
    audio_cue: Optional[str] = Field(None, description="Audio cue for this scene")
    hooks: List[str] = Field(default_factory=list, description="Hook suggestions for this scene")


class HookRequest(BaseModel):
    position: str = Field(..., description="Hook position (start, mid, end)")
    example: Optional[str] = Field(None, description="Example hook text")
    cta: Optional[str] = Field(None, description="Call-to-action text")


class TemplateThemeRequest(BaseModel):
    mood: str = Field(..., description="Content mood (playful, professional, etc.)")
    color_palette: List[str] = Field(..., description="Color palette in hex format")
    preferred_aspect: List[str] = Field(..., description="Preferred aspect ratios")


class TemplateStructureRequest(BaseModel):
    description: str = Field(..., min_length=1, description="Template description")
    scenes: List[SceneRequest] = Field(default_factory=list, description="Video scenes")
    hooks: List[HookRequest] = Field(default_factory=list, description="Content hooks")
    placeholders: List[str] = Field(default_factory=list, description="Content placeholders")
    theme: TemplateThemeRequest = Field(..., description="Template visual theme")
    description_prompt: Optional[str] = Field(None, description="Caption generation prompt")


class TemplateReferencesRequest(BaseModel):
    images: List[str] = Field(default_factory=list, description="Reference image URLs")
    videos: List[str] = Field(default_factory=list, description="Reference video URLs")
    notes: Optional[str] = Field(None, description="Reference notes")


class TemplateCreateRequest(BaseModel):
    brand_id: Optional[str] = Field(None, description="Brand ID if template is brand-specific")
    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    type: TemplateType = Field(..., description="Template type")
    structure: TemplateStructureRequest = Field(..., description="Template structure")
    references: Optional[TemplateReferencesRequest] = Field(
        default_factory=TemplateReferencesRequest, 
        description="Reference materials"
    )
    assets: List[str] = Field(default_factory=list, description="Pre-filled asset IDs")


class TemplateUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[TemplateType] = None
    status: Optional[TemplateStatus] = None
    structure: Optional[TemplateStructureRequest] = None
    references: Optional[TemplateReferencesRequest] = None
    assets: Optional[List[str]] = None


class TemplateResponse(BaseModel):
    id: str
    user_id: str
    brand_id: Optional[str]
    name: str
    type: str
    version: int
    status: str
    structure: Dict[str, Any]
    references: Dict[str, Any]
    assets: List[str]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    templates: List[TemplateResponse]
    total: int
    page: int
    limit: int


# Template CRUD Operations
@router.post("/", response_model=TemplateResponse, status_code=201)
async def create_template(
    template_data: TemplateCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new template.
    
    - **brand_id**: Brand ID if template is brand-specific (optional)
    - **name**: Template name (required)
    - **type**: Template type (required)
    - **structure**: Template structure and content guidelines (required)
    - **references**: Reference materials (optional)
    - **assets**: Pre-filled asset IDs (optional)
    """
    try:
        user_id = current_user["id"]
        
        # Validate brand_id if provided
        if template_data.brand_id:
            brand = await social_media_db.get_brand_by_id(template_data.brand_id)
            if not brand:
                raise HTTPException(status_code=404, detail="Brand not found")
            if brand["user_id"] != user_id:
                raise HTTPException(status_code=403, detail="Access denied to brand")
        
        # Create template data
        template_dict = {
            "user_id": user_id,
            "brand_id": template_data.brand_id,
            "name": template_data.name,
            "type": template_data.type.value,
            "version": 1,
            "status": TemplateStatus.ACTIVE.value,
            "structure": template_data.structure.dict(),
            "references": template_data.references.dict() if template_data.references else {},
            "assets": template_data.assets
        }
        
        template_id = await social_media_db.create_template(template_dict)
        
        # Return created template
        created_template = await social_media_db.get_template_by_id(template_id)
        if not created_template:
            raise HTTPException(status_code=500, detail="Failed to retrieve created template")
        
        return TemplateResponse(**created_template)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")


@router.get("/", response_model=TemplateListResponse)
async def get_templates(
    current_user: dict = Depends(get_current_user),
    brand_id: Optional[str] = Query(None, description="Filter by brand ID"),
    type: Optional[TemplateType] = Query(None, description="Filter by template type"),
    status: Optional[TemplateStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in template name")
):
    """
    Get templates with filtering and pagination.
    
    - **brand_id**: Filter by brand ID (optional)
    - **type**: Filter by template type (optional)
    - **status**: Filter by status (optional)
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    - **search**: Search term for template name
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
        
        # Get templates
        all_templates = await social_media_db.get_templates_by_user(user_id, brand_id)
        
        # Apply filters
        filtered_templates = all_templates
        
        if type:
            filtered_templates = [t for t in filtered_templates if t["type"] == type.value]
        
        if status:
            filtered_templates = [t for t in filtered_templates if t["status"] == status.value]
        
        if search:
            search_lower = search.lower()
            filtered_templates = [
                t for t in filtered_templates
                if search_lower in t["name"].lower()
            ]
        
        # Apply pagination
        total = len(filtered_templates)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_templates = filtered_templates[start_idx:end_idx]
        
        return TemplateListResponse(
            templates=[TemplateResponse(**template) for template in paginated_templates],
            total=total,
            page=page,
            limit=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve templates: {str(e)}")


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific template by ID.
    
    - **template_id**: Template ID
    """
    try:
        user_id = current_user["id"]
        
        template = await social_media_db.get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Check if user owns this template
        if template["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return TemplateResponse(**template)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve template: {str(e)}")


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    update_data: TemplateUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a template.
    
    - **template_id**: Template ID
    - **update_data**: Fields to update (all optional)
    """
    try:
        user_id = current_user["id"]
        
        # Check if template exists and user owns it
        existing_template = await social_media_db.get_template_by_id(template_id)
        if not existing_template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        if existing_template["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Prepare update data (only non-None fields)
        update_dict = {}
        for field, value in update_data.dict().items():
            if value is not None:
                if field in ["structure", "references"] and isinstance(value, dict):
                    update_dict[field] = value
                elif field in ["type", "status"] and hasattr(value, "value"):
                    update_dict[field] = value.value
                else:
                    update_dict[field] = value
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Update template
        success = await social_media_db.update_template(template_id, update_dict)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update template")
        
        # Return updated template
        updated_template = await social_media_db.get_template_by_id(template_id)
        return TemplateResponse(**updated_template)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update template: {str(e)}")


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a template.
    
    - **template_id**: Template ID
    """
    try:
        user_id = current_user["id"]
        
        # Check if template exists and user owns it
        existing_template = await social_media_db.get_template_by_id(template_id)
        if not existing_template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        if existing_template["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete template
        success = await social_media_db.delete_template(template_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete template")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete template: {str(e)}")


@router.post("/{template_id}/duplicate", response_model=TemplateResponse, status_code=201)
async def duplicate_template(
    template_id: str,
    new_name: str = Query(..., description="Name for the duplicated template"),
    current_user: dict = Depends(get_current_user)
):
    """
    Duplicate an existing template with a new name.
    
    - **template_id**: Template ID to duplicate
    - **new_name**: Name for the new template
    """
    try:
        user_id = current_user["id"]
        
        # Check if original template exists and user owns it
        original_template = await social_media_db.get_template_by_id(template_id)
        if not original_template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        if original_template["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Create duplicate template data
        duplicate_data = {
            "user_id": user_id,
            "brand_id": original_template["brand_id"],
            "name": new_name,
            "type": original_template["type"],
            "version": 1,
            "status": TemplateStatus.ACTIVE.value,
            "structure": original_template["structure"],
            "references": original_template["references"],
            "assets": original_template["assets"],
            "metadata": {
                "duplicated_from": template_id,
                "duplicated_at": datetime.utcnow().isoformat()
            }
        }
        
        new_template_id = await social_media_db.create_template(duplicate_data)
        
        # Return created template
        new_template = await social_media_db.get_template_by_id(new_template_id)
        return TemplateResponse(**new_template)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to duplicate template: {str(e)}")


@router.post("/{template_id}/archive", response_model=TemplateResponse)
async def archive_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Archive a template (set status to archived).
    
    - **template_id**: Template ID
    """
    try:
        user_id = current_user["id"]
        
        # Check if template exists and user owns it
        template = await social_media_db.get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        if template["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update status to archived
        success = await social_media_db.update_template(template_id, {"status": TemplateStatus.ARCHIVED.value})
        if not success:
            raise HTTPException(status_code=500, detail="Failed to archive template")
        
        # Return updated template
        updated_template = await social_media_db.get_template_by_id(template_id)
        return TemplateResponse(**updated_template)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to archive template: {str(e)}")


@router.post("/{template_id}/activate", response_model=TemplateResponse)
async def activate_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Activate a template (set status to active).
    
    - **template_id**: Template ID
    """
    try:
        user_id = current_user["id"]
        
        # Check if template exists and user owns it
        template = await social_media_db.get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        if template["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update status to active
        success = await social_media_db.update_template(template_id, {"status": TemplateStatus.ACTIVE.value})
        if not success:
            raise HTTPException(status_code=500, detail="Failed to activate template")
        
        # Return updated template
        updated_template = await social_media_db.get_template_by_id(template_id)
        return TemplateResponse(**updated_template)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to activate template: {str(e)}")


@router.get("/{template_id}/stats", response_model=Dict[str, Any])
async def get_template_stats(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get statistics for a template.
    
    - **template_id**: Template ID
    """
    try:
        user_id = current_user["id"]
        
        # Check if template exists and user owns it
        template = await social_media_db.get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        if template["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "template_id": template_id,
            "template_name": template["name"],
            "type": template["type"],
            "status": template["status"],
            "version": template["version"],
            "scenes_count": len(template["structure"].get("scenes", [])),
            "hooks_count": len(template["structure"].get("hooks", [])),
            "placeholders_count": len(template["structure"].get("placeholders", [])),
            "references_count": len(template["references"].get("images", [])) + len(template["references"].get("videos", [])),
            "assets_count": len(template["assets"]),
            "created_at": template["created_at"],
            "updated_at": template["updated_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get template stats: {str(e)}")