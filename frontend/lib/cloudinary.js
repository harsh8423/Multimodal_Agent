// Simple Cloudinary unsigned upload helper for image/video
// Requires NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME and NEXT_PUBLIC_CLOUDINARY_UPLOAD_PRESET

export async function uploadToCloudinary(file, options = {}) {
  const cloudName = options.cloudName || process.env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME;
  const uploadPreset = options.uploadPreset || process.env.NEXT_PUBLIC_CLOUDINARY_UPLOAD_PRESET;
  const folder = options.folder;

  if (!cloudName) {
    throw new Error('Missing Cloudinary cloud name (NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME)');
  }
  if (!uploadPreset) {
    throw new Error('Missing Cloudinary upload preset (NEXT_PUBLIC_CLOUDINARY_UPLOAD_PRESET)');
  }

  const isVideo = (options.resourceType
    ? options.resourceType === 'video'
    : (file && typeof file.type === 'string' && file.type.startsWith('video/')));
  const resourceType = isVideo ? 'video' : 'image';

  const url = `https://api.cloudinary.com/v1_1/${cloudName}/${resourceType}/upload`;

  const formData = new FormData();
  formData.append('file', file);
  formData.append('upload_preset', uploadPreset);
  if (folder) formData.append('folder', folder);

  const resp = await fetch(url, {
    method: 'POST',
    body: formData
  });

  if (!resp.ok) {
    const text = await resp.text().catch(() => '');
    throw new Error(`Cloudinary upload failed: ${resp.status} ${text}`);
  }

  const json = await resp.json();
  // Expected fields: secure_url, public_id, resource_type, bytes, width, height, duration (for video)
  return json;
}

