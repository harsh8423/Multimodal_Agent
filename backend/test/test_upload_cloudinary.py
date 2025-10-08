#!/usr/bin/env python3
"""
Test script for the enhanced upload_cloudinary.py functionality.
This script demonstrates how to upload different types of files.
"""

import os
import sys
from pathlib import Path

# Add the utils directory to the path so we can import upload_cloudinary
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from upload_cloudinary import upload_to_cloudinary, upload_multiple_files, get_resource_type

def test_file_type_detection():
    """Test the file type detection functionality."""
    print("=== Testing File Type Detection ===")
    
    test_files = [
        "test_image.jpg",
        "test_video.mp4", 
        "test_audio.mp3",
        "test_audio.wav",
        "test_document.pdf",
        "test_document.docx",
        "test_archive.zip",
        "test_code.py",
        "test_unknown.xyz"
    ]
    
    for file_path in test_files:
        resource_type = get_resource_type(file_path)
        print(f"{file_path:20} -> {resource_type}")
    
    print()

def test_upload_examples():
    """Show examples of how to use the enhanced upload functionality."""
    print("=== Upload Examples ===")
    
    # Example 1: Upload a PDF document
    print("Example 1: Upload PDF with custom options")
    pdf_options = {
        "folder": "documents",
        "tags": "document,pdf,important",
        "context": "alt=Important document;caption=User manual"
    }
    print("upload_to_cloudinary('document.pdf', pdf_options)")
    print()
    
    # Example 2: Upload an audio file
    print("Example 2: Upload audio file")
    audio_options = {
        "folder": "audio",
        "tags": "audio,music,podcast"
    }
    print("upload_to_cloudinary('podcast.mp3', audio_options)")
    print()
    
    # Example 3: Upload multiple files
    print("Example 3: Upload multiple files")
    files_to_upload = [
        "report.pdf",
        "presentation.pptx", 
        "audio_note.wav",
        "data.csv"
    ]
    batch_options = {
        "folder": "batch_upload",
        "tags": "batch,upload"
    }
    print("upload_multiple_files(files_to_upload, batch_options)")
    print()
    
    # Example 4: Force specific resource type
    print("Example 4: Force specific resource type")
    force_options = {
        "resourceType": "raw",
        "folder": "forced_raw"
    }
    print("upload_to_cloudinary('image.jpg', force_options)  # Forces as raw file")
    print()

def show_supported_formats():
    """Display all supported file formats."""
    print("=== Supported File Formats ===")
    
    formats = {
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff", ".tif"],
        "Videos": [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv", ".m4v", ".3gp", ".ogv"],
        "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus", ".amr"],
        "Documents": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".rtf", ".odt", ".ods", ".odp"],
        "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
        "Code": [".js", ".css", ".html", ".xml", ".json", ".csv", ".sql", ".py", ".java", ".cpp", ".c", ".h"]
    }
    
    for category, extensions in formats.items():
        print(f"{category:12}: {', '.join(extensions)}")
    
    print()
    print("Note: All non-image/video files are uploaded as 'raw' files to Cloudinary.")
    print("This allows Cloudinary to serve them directly without processing.")

if __name__ == "__main__":
    print("Enhanced Cloudinary Upload Utility Test")
    print("=" * 50)
    print()
    
    test_file_type_detection()
    show_supported_formats()
    test_upload_examples()
    
    print("=== Usage Notes ===")
    print("1. Make sure CLOUDINARY_CLOUD_NAME and CLOUDINARY_UPLOAD_PRESET are set in your .env file")
    print("2. The upload preset should be configured as 'unsigned' in Cloudinary")
    print("3. For raw files, Cloudinary will preserve the original file format")
    print("4. Large files (>100MB) will show a warning but can still be uploaded")
    print("5. All uploads use the same unsigned preset as requested")
    print()
    print("To test with actual files, uncomment the upload calls and provide real file paths.")