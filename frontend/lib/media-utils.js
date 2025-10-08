/**
 * Media Utilities for CDN Detection and Media Handling
 * 
 * This module provides utilities for:
 * - Detecting CDN URLs in text content
 * - Extracting media URLs from various sources
 * - Handling media display in chat messages
 * - Processing media metadata
 */

/**
 * Check if a URL is from a known CDN
 * @param {string} url - The URL to check
 * @returns {boolean} - True if the URL is from a known CDN
 */
export const isCDNUrl = (url) => {
  if (!url || typeof url !== 'string') return false;
  
  const cdnPatterns = [
    /cloudinary\.com/i,
    /cloudfront\.net/i,
    /amazonaws\.com/i,
    /googleusercontent\.com/i,
    /imgur\.com/i,
    /unsplash\.com/i,
    /pexels\.com/i,
    /pixabay\.com/i,
    /freepik\.com/i,
    /shutterstock\.com/i,
    /gettyimages\.com/i,
    /istockphoto\.com/i,
    /adobe\.com/i,
    /dropbox\.com/i,
    /drive\.google\.com/i,
    /onedrive\.live\.com/i,
    /i\.ibb\.co/i, // ImgBB
    /i\.imgur\.com/i,
    /cdn\.discordapp\.com/i,
    /media\.discordapp\.net/i
  ];
  
  return cdnPatterns.some(pattern => pattern.test(url));
};

/**
 * Detect media type from URL
 * @param {string} url - The URL to analyze
 * @returns {string} - The detected media type ('image', 'video', 'audio', 'document', 'unknown')
 */
export const detectMediaType = (url) => {
  if (!url || typeof url !== 'string') return 'unknown';
  
  const urlLower = url.toLowerCase();
  
  // Image extensions
  if (/\.(jpg|jpeg|png|gif|webp|svg|bmp|tiff|ico)$/i.test(urlLower)) {
    return 'image';
  }
  
  // Video extensions
  if (/\.(mp4|mov|avi|mkv|webm|flv|wmv|m4v|3gp|ogv)$/i.test(urlLower)) {
    return 'video';
  }
  
  // Audio extensions
  if (/\.(mp3|wav|ogg|m4a|aac|flac|wma|opus)$/i.test(urlLower)) {
    return 'audio';
  }
  
  // Document extensions
  if (/\.(pdf|doc|docx|txt|rtf|odt)$/i.test(urlLower)) {
    return 'document';
  }
  
  // Check for known CDN patterns that typically serve media
  if (isCDNUrl(url)) {
    // Cloudinary URLs often have format indicators
    if (urlLower.includes('cloudinary')) {
      if (urlLower.includes('/video/') || urlLower.includes('_video_')) {
        return 'video';
      }
      if (urlLower.includes('/audio/') || urlLower.includes('_audio_')) {
        return 'audio';
      }
      return 'image'; // Default for Cloudinary
    }
    
    // Other CDNs - make educated guesses based on common patterns
    if (urlLower.includes('video') || urlLower.includes('mp4')) {
      return 'video';
    }
    if (urlLower.includes('audio') || urlLower.includes('mp3') || urlLower.includes('wav')) {
      return 'audio';
    }
    
    return 'image'; // Default for most CDNs
  }
  
  return 'unknown';
};

/**
 * Extract media URLs from text content
 * @param {string} text - The text to search for URLs
 * @returns {Array} - Array of media URL objects with type detection
 */
export const extractMediaUrls = (text) => {
  if (!text || typeof text !== 'string') return [];
  
  const mediaUrls = [];
  
  // Regex to find URLs (including those in markdown links)
  const urlRegex = /https?:\/\/[^\s\)]+/g;
  const matches = text.match(urlRegex) || [];
  
  matches.forEach(url => {
    // Clean up URL (remove trailing punctuation that might not be part of URL)
    const cleanUrl = url.replace(/[.,;!?]+$/, '');
    
    if (isCDNUrl(cleanUrl) || detectMediaType(cleanUrl) !== 'unknown') {
      mediaUrls.push({
        url: cleanUrl,
        type: detectMediaType(cleanUrl),
        source: 'text_extraction'
      });
    }
  });
  
  return mediaUrls;
};

/**
 * Extract media URLs from JSON content
 * @param {Object} jsonContent - The JSON object to search
 * @returns {Array} - Array of media URL objects
 */
export const extractMediaFromJson = (jsonContent) => {
  if (!jsonContent || typeof jsonContent !== 'object') return [];
  
  const mediaUrls = [];
  const mediaFields = [
    'url', 'image_url', 'video_url', 'audio_url', 'media_url',
    'generated_image_url', 'cloudinary_url', 'cdn_url',
    'thumbnail_url', 'preview_url', 'download_url'
  ];
  
  // Recursively search for media URLs in the JSON
  const searchForMediaUrls = (obj, path = '') => {
    if (typeof obj !== 'object' || obj === null) return;
    
    Object.keys(obj).forEach(key => {
      const value = obj[key];
      const currentPath = path ? `${path}.${key}` : key;
      
      if (typeof value === 'string' && value.startsWith('http')) {
        // Check if this field name suggests it's a media URL
        const isMediaField = mediaFields.some(field => 
          key.toLowerCase().includes(field.toLowerCase()) ||
          key.toLowerCase().includes('url')
        );
        
        if (isMediaField || isCDNUrl(value) || detectMediaType(value) !== 'unknown') {
          mediaUrls.push({
            url: value,
            type: detectMediaType(value),
            source: 'json_extraction',
            field: currentPath
          });
        }
      } else if (typeof value === 'object' && value !== null) {
        searchForMediaUrls(value, currentPath);
      }
    });
  };
  
  searchForMediaUrls(jsonContent);
  return mediaUrls;
};

/**
 * Process message content to extract and categorize media
 * @param {any} content - The message content (string, object, etc.)
 * @param {Object} metadata - Optional metadata object
 * @returns {Object} - Processed media information
 */
export const processMessageMedia = (content, metadata = null) => {
  const mediaItems = [];
  
  // Extract from content
  if (typeof content === 'string') {
    mediaItems.push(...extractMediaUrls(content));
  } else if (typeof content === 'object' && content !== null) {
    mediaItems.push(...extractMediaFromJson(content));
  }
  
  // Extract from metadata
  if (metadata) {
    // Check for media_urls array
    if (metadata.media_urls && Array.isArray(metadata.media_urls)) {
      metadata.media_urls.forEach(item => {
        if (typeof item === 'string') {
          mediaItems.push({
            url: item,
            type: detectMediaType(item),
            source: 'metadata_media_urls'
          });
        } else if (typeof item === 'object' && item.url) {
          mediaItems.push({
            url: item.url,
            type: item.type || detectMediaType(item.url),
            source: 'metadata_media_urls'
          });
        }
      });
    }
    
    // Check for direct media fields in metadata
    const mediaFields = ['generated_image_url', 'audio_url', 'video_url', 'cloudinary_url'];
    mediaFields.forEach(field => {
      if (metadata[field]) {
        mediaItems.push({
          url: metadata[field],
          type: field.includes('image') ? 'image' : 
                field.includes('audio') ? 'audio' : 
                field.includes('video') ? 'video' : 'unknown',
          source: 'metadata_direct'
        });
      }
    });
    
    // Check for media object in metadata
    if (metadata.media && typeof metadata.media === 'object') {
      if (metadata.media.url) {
        mediaItems.push({
          url: metadata.media.url,
          type: metadata.media.type || detectMediaType(metadata.media.url),
          source: 'metadata_media_object'
        });
      }
    }
  }
  
  // Remove duplicates based on URL
  const uniqueMediaItems = mediaItems.filter((item, index, self) => 
    index === self.findIndex(t => t.url === item.url)
  );
  
  return {
    mediaItems: uniqueMediaItems,
    hasMedia: uniqueMediaItems.length > 0,
    mediaTypes: [...new Set(uniqueMediaItems.map(item => item.type))]
  };
};

/**
 * Get appropriate icon for media type
 * @param {string} mediaType - The media type
 * @returns {string} - Lucide icon name
 */
export const getMediaIcon = (mediaType) => {
  switch (mediaType) {
    case 'image':
      return 'Image';
    case 'video':
      return 'Video';
    case 'audio':
      return 'Volume2';
    case 'document':
      return 'FileText';
    default:
      return 'File';
  }
};

/**
 * Check if media URL is accessible (basic validation)
 * @param {string} url - The URL to check
 * @returns {Promise<boolean>} - True if URL appears to be accessible
 */
export const validateMediaUrl = async (url) => {
  if (!url || typeof url !== 'string') return false;
  
  try {
    // Basic URL validation
    new URL(url);
    
    // For CDN URLs, we assume they're accessible
    if (isCDNUrl(url)) {
      return true;
    }
    
    // For other URLs, we could do a HEAD request, but that might be too expensive
    // For now, just validate the URL format
    return true;
  } catch (error) {
    return false;
  }
};

/**
 * Format file size for display
 * @param {number} bytes - File size in bytes
 * @returns {string} - Formatted file size
 */
export const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

/**
 * Get media display configuration
 * @param {string} mediaType - The media type
 * @returns {Object} - Display configuration
 */
export const getMediaDisplayConfig = (mediaType) => {
  const configs = {
    image: {
      maxHeight: '400px',
      className: 'max-w-full h-auto rounded-lg shadow-md border border-gray-200',
      showControls: false
    },
    video: {
      maxHeight: '400px',
      className: 'max-w-full h-auto rounded-lg shadow-md border border-gray-200',
      showControls: true
    },
    audio: {
      maxHeight: 'auto',
      className: 'w-full',
      showControls: true,
      showPlayer: true
    },
    document: {
      maxHeight: 'auto',
      className: 'max-w-full',
      showControls: false,
      showDownload: true
    }
  };
  
  return configs[mediaType] || configs.image;
};