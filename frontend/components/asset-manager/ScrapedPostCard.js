'use client';

import { useState } from 'react';
import { socialMediaUtils } from '@/lib/api/socialMedia';

export default function ScrapedPostCard({ post, brands, selected, onSelect, onDelete, onToggleImportant }) {
  const [showActions, setShowActions] = useState(false);

  const brand = brands.find(b => b.id === post.brand_id);

  const getStatusColor = (status) => {
    switch (status) {
      case 'normalized':
        return 'bg-green-100 text-green-800';
      case 'processing':
        return 'bg-yellow-100 text-yellow-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow ${
      selected ? 'ring-2 ring-blue-500' : ''
    }`}>
      {/* Post Header */}
      <div className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={selected}
                onChange={(e) => onSelect(post.id, e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onToggleImportant(post.id, !post.important);
                }}
                className={`p-1 rounded-full transition-colors ${
                  post.important 
                    ? 'text-yellow-500 hover:text-yellow-600' 
                    : 'text-gray-300 hover:text-yellow-500'
                }`}
                title={post.important ? 'Mark as not important' : 'Mark as important'}
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              </button>
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-white ${socialMediaUtils.getPlatformColor(post.platform)}`}>
                {socialMediaUtils.formatPlatform(post.platform)}
              </span>
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(post.processing.status)}`}>
                {post.processing.status}
              </span>
            </div>
            {brand && (
              <p className="text-xs text-blue-600 mt-1">Brand: {brand.name}</p>
            )}
          </div>
          
          {/* Actions Dropdown */}
          <div className="relative">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowActions(!showActions);
              }}
              className="p-2 text-gray-400 hover:text-gray-600 focus:outline-none"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
              </svg>
            </button>
            
            {showActions && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border border-gray-200">
                <div className="py-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(post.id);
                      setShowActions(false);
                    }}
                    className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
                  >
                    Delete
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Post Content */}
        {post.normalized.text && (
          <div className="mt-4">
            <p className="text-sm text-gray-900 line-clamp-3">
              {post.normalized.text}
            </p>
          </div>
        )}

        {/* Media Preview */}
        {post.normalized.media && post.normalized.media.length > 0 && (
          <div className="mt-4">
            <div className="grid grid-cols-2 gap-2">
              {post.normalized.media.slice(0, 4).map((media, index) => (
                <div key={index} className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
                  {media.type === 'image' ? (
                    <img
                      src={media.url}
                      alt={`Media ${index + 1}`}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                    />
                  ) : media.type === 'video' ? (
                    <div className="w-full h-full flex items-center justify-center bg-gray-200">
                      <svg className="w-8 h-8 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" />
                      </svg>
                    </div>
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-gray-200">
                      <svg className="w-8 h-8 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
                      </svg>
                    </div>
                  )}
                </div>
              ))}
            </div>
            {post.normalized.media.length > 4 && (
              <p className="text-xs text-gray-500 mt-2">
                +{post.normalized.media.length - 4} more media items
              </p>
            )}
          </div>
        )}

        {/* Engagement Stats */}
        {post.normalized.engagement && (
          <div className="mt-4 grid grid-cols-3 gap-2 text-center">
            {post.normalized.engagement.likes && (
              <div className="p-2 bg-gray-50 rounded">
                <p className="text-lg font-bold text-gray-900">
                  {socialMediaUtils.formatEngagement(post.normalized.engagement.likes)}
                </p>
                <p className="text-xs text-gray-500">Likes</p>
              </div>
            )}
            {post.normalized.engagement.comments && (
              <div className="p-2 bg-gray-50 rounded">
                <p className="text-lg font-bold text-gray-900">
                  {socialMediaUtils.formatEngagement(post.normalized.engagement.comments)}
                </p>
                <p className="text-xs text-gray-500">Comments</p>
              </div>
            )}
            {post.normalized.engagement.shares && (
              <div className="p-2 bg-gray-50 rounded">
                <p className="text-lg font-bold text-gray-900">
                  {socialMediaUtils.formatEngagement(post.normalized.engagement.shares)}
                </p>
                <p className="text-xs text-gray-500">Shares</p>
              </div>
            )}
          </div>
        )}

        {/* Source Information */}
        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
          <div className="flex items-center justify-between text-sm">
            <span className="text-blue-800">Source:</span>
            <span className="text-blue-600">{post.source}</span>
          </div>
          <div className="flex items-center justify-between text-sm mt-1">
            <span className="text-blue-800">Scraped:</span>
            <span className="text-blue-600">
              {socialMediaUtils.formatDate(post.scraped_at)}
            </span>
          </div>
        </div>

        {/* Processing Information */}
        {post.processing.error_message && (
          <div className="mt-4 p-3 bg-red-50 rounded-lg">
            <div className="flex items-start">
              <svg className="h-5 w-5 text-red-400 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Processing Error</h3>
                <div className="mt-1 text-sm text-red-700">
                  <p>{post.processing.error_message}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Metadata */}
        {post.metadata && Object.keys(post.metadata).length > 0 && (
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <div className="text-xs text-gray-600">
              <strong>Metadata:</strong> {Object.keys(post.metadata).length} fields
            </div>
          </div>
        )}
      </div>
    </div>
  );
}