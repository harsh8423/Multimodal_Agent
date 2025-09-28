/**
 * Social Media Management API Service
 * 
 * This module provides API functions for managing social media assets including
 * brands, templates, competitors, and scraped posts.
 */

import { authService } from '../auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Helper function to make authenticated API requests
async function apiRequest(endpoint, options = {}) {
  const token = authService.token;
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    
    // Handle FastAPI validation errors
    if (error.detail && Array.isArray(error.detail)) {
      const validationErrors = error.detail.map(err => 
        `${err.loc ? err.loc.join('.') : 'field'}: ${err.msg}`
      ).join(', ');
      throw new Error(`Validation error: ${validationErrors}`);
    }
    
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

// Brands API
export const brandsAPI = {
  // Create a new brand
  create: async (brandData) => {
    return apiRequest('/api/brands/', {
      method: 'POST',
      body: JSON.stringify(brandData),
    });
  },

  // Get all brands with pagination and search
  getAll: async (params = {}) => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value);
      }
    });
    return apiRequest(`/api/brands/?${searchParams.toString()}`);
  },

  // Get brand by ID
  getById: async (brandId) => {
    return apiRequest(`/api/brands/${brandId}`);
  },

  // Update brand
  update: async (brandId, updateData) => {
    return apiRequest(`/api/brands/${brandId}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
  },

  // Delete brand
  delete: async (brandId) => {
    return apiRequest(`/api/brands/${brandId}`, {
      method: 'DELETE',
    });
  },

  // Get brand statistics
  getStats: async (brandId) => {
    return apiRequest(`/api/brands/${brandId}/stats`);
  },

  // Duplicate brand
  duplicate: async (brandId, newName, newSlug) => {
    return apiRequest(`/api/brands/${brandId}/duplicate?new_name=${encodeURIComponent(newName)}&new_slug=${encodeURIComponent(newSlug)}`, {
      method: 'POST',
    });
  },
};

// Templates API
export const templatesAPI = {
  // Create a new template
  create: async (templateData) => {
    return apiRequest('/api/templates/', {
      method: 'POST',
      body: JSON.stringify(templateData),
    });
  },

  // Get all templates with filtering
  getAll: async (params = {}) => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value);
      }
    });
    return apiRequest(`/api/templates/?${searchParams.toString()}`);
  },

  // Get template by ID
  getById: async (templateId) => {
    return apiRequest(`/api/templates/${templateId}`);
  },

  // Update template
  update: async (templateId, updateData) => {
    return apiRequest(`/api/templates/${templateId}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
  },

  // Delete template
  delete: async (templateId) => {
    return apiRequest(`/api/templates/${templateId}`, {
      method: 'DELETE',
    });
  },

  // Duplicate template
  duplicate: async (templateId, newName) => {
    return apiRequest(`/api/templates/${templateId}/duplicate?new_name=${encodeURIComponent(newName)}`, {
      method: 'POST',
    });
  },

  // Archive template
  archive: async (templateId) => {
    return apiRequest(`/api/templates/${templateId}/archive`, {
      method: 'POST',
    });
  },

  // Activate template
  activate: async (templateId) => {
    return apiRequest(`/api/templates/${templateId}/activate`, {
      method: 'POST',
    });
  },

  // Get template statistics
  getStats: async (templateId) => {
    return apiRequest(`/api/templates/${templateId}/stats`);
  },
};

// Competitors API
export const competitorsAPI = {
  // Create a new competitor
  create: async (competitorData) => {
    return apiRequest('/api/competitors/', {
      method: 'POST',
      body: JSON.stringify(competitorData),
    });
  },

  // Get all competitors with filtering
  getAll: async (params = {}) => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value);
      }
    });
    return apiRequest(`/api/competitors/?${searchParams.toString()}`);
  },

  // Get competitor by ID
  getById: async (competitorId) => {
    return apiRequest(`/api/competitors/${competitorId}`);
  },

  // Update competitor
  update: async (competitorId, updateData) => {
    return apiRequest(`/api/competitors/${competitorId}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
  },

  // Delete competitor
  delete: async (competitorId) => {
    return apiRequest(`/api/competitors/${competitorId}`, {
      method: 'DELETE',
    });
  },

  // Update competitor metrics
  updateMetrics: async (competitorId, metrics) => {
    return apiRequest(`/api/competitors/${competitorId}/metrics`, {
      method: 'PUT',
      body: JSON.stringify(metrics),
    });
  },

  // Get competitor statistics
  getStats: async (competitorId) => {
    return apiRequest(`/api/competitors/${competitorId}/stats`);
  },

  // Scrape competitor
  scrape: async (competitorId, limit = 10) => {
    return apiRequest(`/api/competitors/${competitorId}/scrape?limit=${limit}`, {
      method: 'POST',
    });
  },

  // Duplicate competitor
  duplicate: async (competitorId, newName) => {
    return apiRequest(`/api/competitors/${competitorId}/duplicate?new_name=${encodeURIComponent(newName)}`, {
      method: 'POST',
    });
  },
};

// Scraped Posts API
export const scrapedPostsAPI = {
  // Get all scraped posts with filtering
  getAll: async (params = {}) => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value);
      }
    });
    return apiRequest(`/api/scraped-posts/?${searchParams.toString()}`);
  },

  // Get post by ID
  getById: async (postId) => {
    return apiRequest(`/api/scraped-posts/${postId}`);
  },

  // Delete post
  delete: async (postId) => {
    return apiRequest(`/api/scraped-posts/${postId}`, {
      method: 'DELETE',
    });
  },

  // Get posts analytics
  getAnalytics: async (params = {}) => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value);
      }
    });
    return apiRequest(`/api/scraped-posts/analytics/overview?${searchParams.toString()}`);
  },

  // Get engagement analytics
  getEngagementAnalytics: async (params = {}) => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value);
      }
    });
    return apiRequest(`/api/scraped-posts/analytics/engagement?${searchParams.toString()}`);
  },

  // Bulk delete posts
  bulkDelete: async (postIds) => {
    return apiRequest('/api/scraped-posts/bulk-delete', {
      method: 'POST',
      body: JSON.stringify(postIds),
    });
  },

  // Advanced search
  advancedSearch: async (params = {}) => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value);
      }
    });
    return apiRequest(`/api/scraped-posts/search/advanced?${searchParams.toString()}`);
  },
};

// Scraping API
export const scrapingAPI = {
  // Scrape single platform
  scrape: async (scrapingData) => {
    return apiRequest('/api/scraping/scrape', {
      method: 'POST',
      body: JSON.stringify(scrapingData),
    });
  },

  // Batch scraping
  batchScrape: async (requests) => {
    return apiRequest('/api/scraping/scrape/batch', {
      method: 'POST',
      body: JSON.stringify({ requests }),
    });
  },

  // Get supported platforms
  getPlatforms: async () => {
    return apiRequest('/api/scraping/platforms');
  },

  // Get scraping status
  getStatus: async (platform, identifier) => {
    return apiRequest(`/api/scraping/status/${platform}/${identifier}`);
  },

  // Scrape competitor
  scrapeCompetitor: async (competitorId, limit = 10) => {
    return apiRequest(`/api/scraping/competitor/${competitorId}/scrape?limit=${limit}`, {
      method: 'POST',
    });
  },

  // Get scraping history
  getHistory: async (params = {}) => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value);
      }
    });
    return apiRequest(`/api/scraping/history?${searchParams.toString()}`);
  },
};

// Utility functions
export const socialMediaUtils = {
  // Format platform name
  formatPlatform: (platform) => {
    const platformNames = {
      instagram: 'Instagram',
      linkedin: 'LinkedIn',
      youtube: 'YouTube',
      reddit: 'Reddit',
    };
    return platformNames[platform] || platform;
  },

  // Format template type
  formatTemplateType: (type) => {
    const typeNames = {
      instagram_post: 'Instagram Post',
      linkedin_post: 'LinkedIn Post',
      reel: 'Reel',
      short: 'Short',
      carousel: 'Carousel',
      image_post: 'Image Post',
    };
    return typeNames[type] || type;
  },

  // Format engagement numbers
  formatEngagement: (number) => {
    if (number >= 1000000) {
      return `${(number / 1000000).toFixed(1)}M`;
    } else if (number >= 1000) {
      return `${(number / 1000).toFixed(1)}K`;
    }
    return number.toString();
  },

  // Format date
  formatDate: (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  },

  // Get platform color
  getPlatformColor: (platform) => {
    const colors = {
      instagram: 'bg-gradient-to-r from-purple-500 to-pink-500',
      linkedin: 'bg-blue-600',
      youtube: 'bg-red-600',
      reddit: 'bg-orange-500',
    };
    return colors[platform] || 'bg-gray-500';
  },
};