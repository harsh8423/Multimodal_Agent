import os
import requests
from dotenv import load_dotenv

load_dotenv()

def upload_to_cloudinary(file_path, options=None):
    if options is None:
        options = {}

    cloud_name = options.get("cloudName") or os.getenv("CLOUDINARY_CLOUD_NAME")
    upload_preset = options.get("uploadPreset") or os.getenv("CLOUDINARY_UPLOAD_PRESET")
    folder = options.get("folder")

    if not cloud_name:
        raise ValueError("Missing Cloudinary cloud name (CLOUDINARY_CLOUD_NAME)")
    if not upload_preset:
        raise ValueError("Missing Cloudinary upload preset (CLOUDINARY_UPLOAD_PRESET)")

    # Detect if it's a video or image
    resource_type = "image"
    if options.get("resourceType") == "video" or (file_path.lower().endswith((".mp4", ".avi", ".mov", ".mkv"))):
        resource_type = "video"

    url = f"https://api.cloudinary.com/v1_1/{cloud_name}/{resource_type}/upload"

    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {"upload_preset": upload_preset}
        if folder:
            data["folder"] = folder

        resp = requests.post(url, files=files, data=data)

    if not resp.ok:
        raise Exception(f"Cloudinary upload failed: {resp.status_code} {resp.text}")

    return resp.json()
