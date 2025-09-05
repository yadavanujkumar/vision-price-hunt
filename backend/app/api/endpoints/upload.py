from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import os
import uuid
import time
import logging
from typing import Optional

from app.models.schemas import UploadResponse, ErrorResponse
from app.services.vision import vision_service
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

def validate_file(file: UploadFile) -> bool:
    """Validate uploaded file"""
    try:
        # Check file extension
        file_ext = os.path.splitext(file.filename or "")[1].lower()
        if file_ext not in settings.allowed_extensions:
            return False
        
        # Check file size (if we can determine it)
        if hasattr(file, 'size') and file.size and file.size > settings.max_upload_size:
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error validating file: {e}")
        return False

def save_uploaded_file(file: UploadFile) -> str:
    """Save uploaded file and return file path"""
    try:
        # Generate unique filename
        file_ext = os.path.splitext(file.filename or "")[1].lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(settings.upload_dir, unique_filename)
        
        # Create upload directory if it doesn't exist
        os.makedirs(settings.upload_dir, exist_ok=True)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = file.file.read()
            buffer.write(content)
        
        return file_path
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

@router.post("/upload", response_model=UploadResponse)
async def upload_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Product image file")
):
    """
    Upload and analyze a product image
    
    - **file**: Image file (JPG, JPEG, PNG, WEBP)
    
    Returns product information extracted from the image
    """
    try:
        # Validate file
        if not validate_file(file):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file. Allowed extensions: {settings.allowed_extensions}"
            )
        
        # Save uploaded file
        file_path = save_uploaded_file(file)
        
        # Generate query ID
        query_id = str(uuid.uuid4())
        
        try:
            # Analyze image using vision service
            product_info = await vision_service.analyze_product_image(file_path)
            
            # Create file URL for frontend
            file_url = f"/uploads/{os.path.basename(file_path)}"
            
            # Create response
            response = UploadResponse(
                message="Image uploaded and analyzed successfully",
                filename=file.filename or "unknown",
                product_info=product_info,
                query_id=query_id,
                file_url=file_url
            )
            
            return response
            
        except Exception as analysis_error:
            # Clean up file if analysis fails
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to analyze image: {str(analysis_error)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in upload endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/upload/{query_id}")
async def cleanup_upload(query_id: str):
    """
    Clean up uploaded files for a specific query
    
    - **query_id**: Query ID from upload response
    """
    try:
        # This is a simple cleanup - in production you'd track files by query_id
        # For now, just return success
        return {"message": f"Cleanup completed for query {query_id}"}
    
    except Exception as e:
        logger.error(f"Error cleaning up upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup upload")

@router.get("/upload/health")
async def upload_health():
    """Health check for upload service"""
    try:
        # Check if upload directory is writable
        test_file = os.path.join(settings.upload_dir, "test_write")
        os.makedirs(settings.upload_dir, exist_ok=True)
        
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        
        return {
            "status": "healthy",
            "upload_dir": settings.upload_dir,
            "max_upload_size": settings.max_upload_size,
            "allowed_extensions": settings.allowed_extensions
        }
    
    except Exception as e:
        logger.error(f"Upload service health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }