import os
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

def get_resource_type(file_path, options=None):
    """
    Determine the Cloudinary resource type based on file extension.
    Returns 'image', 'video', 'raw', or 'auto' for automatic detection.
    """
    if options and options.get("resourceType"):
        return options.get("resourceType")
    
    file_extension = Path(file_path).suffix.lower()
    
    # Image formats
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico', '.tiff', '.tif'}
    
    # Video formats
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v', '.3gp', '.ogv'}
    
    # Audio formats
    audio_extensions = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus', '.amr'}
    
    # Document formats
    document_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt', '.ods', '.odp'}
    
    # Archive formats
    archive_extensions = {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'}
    
    # Code formats
    code_extensions = {'.js', '.css', '.html', '.xml', '.json', '.csv', '.sql', '.py', '.java', '.cpp', '.c', '.h'}
    
    if file_extension in image_extensions:
        return "image"
    elif file_extension in video_extensions:
        return "video"
    elif file_extension in audio_extensions:
        return "raw"  # Audio files are uploaded as raw files
    elif file_extension in document_extensions:
        return "raw"  # Documents are uploaded as raw files
    elif file_extension in archive_extensions:
        return "raw"  # Archives are uploaded as raw files
    elif file_extension in code_extensions:
        return "raw"  # Code files are uploaded as raw files
    else:
        return "raw"  # Default to raw for unknown file types

def validate_file(file_path):
    """
    Validate that the file exists and is readable.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not os.path.isfile(file_path):
        raise ValueError(f"Path is not a file: {file_path}")
    
    if not os.access(file_path, os.R_OK):
        raise PermissionError(f"File is not readable: {file_path}")
    
    # Check file size (optional: warn for very large files)
    file_size = os.path.getsize(file_path)
    if file_size > 100 * 1024 * 1024:  # 100MB
        print(f"Warning: Large file detected ({file_size / (1024*1024):.1f}MB). Upload may take longer.")

def upload_to_cloudinary(file_path, options=None):
    """
    Upload any type of file to Cloudinary using unsigned upload preset.
    
    Args:
        file_path (str): Path to the file to upload
        options (dict): Optional parameters including:
            - cloudName: Cloudinary cloud name (overrides env var)
            - uploadPreset: Upload preset name (overrides env var)
            - folder: Folder to upload to
            - resourceType: Force specific resource type ('image', 'video', 'raw', 'auto')
            - public_id: Custom public ID for the uploaded file
            - tags: Comma-separated tags
            - context: Additional context metadata
    
    Returns:
        dict: Cloudinary upload response with file details
    """
    if options is None:
        options = {}

    # Validate file
    validate_file(file_path)
    
    # Get configuration
    cloud_name = options.get("cloudName") or os.getenv("CLOUDINARY_CLOUD_NAME")
    upload_preset = options.get("uploadPreset") or os.getenv("CLOUDINARY_UPLOAD_PRESET")
    folder = options.get("folder")

    if not cloud_name:
        raise ValueError("Missing Cloudinary cloud name (CLOUDINARY_CLOUD_NAME)")
    if not upload_preset:
        raise ValueError("Missing Cloudinary upload preset (CLOUDINARY_UPLOAD_PRESET)")

    # Determine resource type
    resource_type = get_resource_type(file_path, options)
    
    # Get file extension for proper public_id
    file_extension = Path(file_path).suffix
    if not file_extension:
        # Default extensions based on resource type
        if resource_type == "video":
            file_extension = ".mp4"
        elif resource_type == "image":
            file_extension = ".jpg"
        else:
            file_extension = ".bin"  # Default for raw files

    # Build upload URL
    url = f"https://api.cloudinary.com/v1_1/{cloud_name}/{resource_type}/upload"

    # Prepare upload data
    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {
            "upload_preset": upload_preset
        }
        
        # Add optional parameters
        if folder:
            data["folder"] = folder
        
        if options.get("public_id"):
            data["public_id"] = options.get("public_id")
        
        if options.get("tags"):
            data["tags"] = options.get("tags")
        
        if options.get("context"):
            data["context"] = options.get("context")
        
        # Note: use_filename and unique_filename are not allowed with unsigned uploads
        # For raw files, we rely on Cloudinary's automatic filename handling

        print(f"Uploading to Cloudinary: {file_path} (type: {resource_type}, size: {os.path.getsize(file_path)} bytes)")
        resp = requests.post(url, files=files, data=data)

    if not resp.ok:
        error_msg = f"Cloudinary upload failed: {resp.status_code}"
        try:
            error_detail = resp.json()
            error_msg += f" - {error_detail}"
        except:
            error_msg += f" - {resp.text}"
        raise Exception(error_msg)

    result = resp.json()
    print(f"Upload successful: {result.get('secure_url', 'No URL returned')}")
    print(f"Public ID: {result.get('public_id', 'No public ID')}")
    print(f"Resource type: {result.get('resource_type', 'Unknown')}")
    print(f"Format: {result.get('format', 'Unknown')}")
    
    return result

def upload_multiple_files(file_paths, options=None):
    """
    Upload multiple files to Cloudinary.
    
    Args:
        file_paths (list): List of file paths to upload
        options (dict): Same options as upload_to_cloudinary
    
    Returns:
        list: List of upload results
    """
    results = []
    for file_path in file_paths:
        try:
            result = upload_to_cloudinary(file_path, options)
            results.append({
                "file_path": file_path,
                "success": True,
                "result": result
            })
        except Exception as e:
            results.append({
                "file_path": file_path,
                "success": False,
                "error": str(e)
            })
    
    return results
