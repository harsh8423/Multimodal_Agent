'use client';

import { useState } from 'react';
import { socialMediaUtils } from '@/lib/api/socialMedia';

export default function BrandCard({ brand, onEdit, onDelete, onDuplicate }) {
  const [showActions, setShowActions] = useState(false);
  const [showDuplicateForm, setShowDuplicateForm] = useState(false);
  const [duplicateName, setDuplicateName] = useState('');
  const [duplicateSlug, setDuplicateSlug] = useState('');

  const handleDuplicate = (e) => {
    e.stopPropagation();
    if (!duplicateName.trim() || !duplicateSlug.trim()) {
      alert('Please enter both name and slug for the duplicate');
      return;
    }
    onDuplicate(brand.id, duplicateName, duplicateSlug);
    setShowDuplicateForm(false);
    setDuplicateName('');
    setDuplicateSlug('');
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
      {/* Brand Header */}
      <div className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">{brand.name}</h3>
            <p className="text-sm text-gray-500 mt-1">{brand.slug}</p>
            <p className="text-sm text-gray-600 mt-2 line-clamp-2">{brand.description}</p>
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
                      onEdit(brand);
                      setShowActions(false);
                    }}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    Edit
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowDuplicateForm(true);
                      setShowActions(false);
                    }}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    Duplicate
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(brand.id);
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

        {/* Brand Theme Colors */}
        <div className="mt-4 flex items-center space-x-2">
          <div className="flex space-x-1">
            <div
              className="w-4 h-4 rounded-full border border-gray-300"
              style={{ backgroundColor: brand.theme.primary_color }}
              title="Primary Color"
            />
            <div
              className="w-4 h-4 rounded-full border border-gray-300"
              style={{ backgroundColor: brand.theme.secondary_color }}
              title="Secondary Color"
            />
          </div>
          <span className="text-xs text-gray-500">{brand.theme.font}</span>
        </div>

        {/* Brand Details */}
        <div className="mt-4 space-y-2">
          {brand.details.website && (
            <div className="flex items-center text-sm text-gray-600">
              <svg className="w-4 h-4 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9v-9m0-9v9" />
              </svg>
              <a href={brand.details.website} target="_blank" rel="noopener noreferrer" className="hover:text-blue-600">
                {brand.details.website}
              </a>
            </div>
          )}
          
          {brand.details.industry && (
            <div className="flex items-center text-sm text-gray-600">
              <svg className="w-4 h-4 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              {brand.details.industry}
            </div>
          )}
        </div>

        {/* Audience Tags */}
        {brand.details.audience && brand.details.audience.length > 0 && (
          <div className="mt-4">
            <div className="flex flex-wrap gap-1">
              {brand.details.audience.map((audience, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                >
                  {audience}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Default Platforms */}
        {brand.default_posting_settings.default_platforms && brand.default_posting_settings.default_platforms.length > 0 && (
          <div className="mt-4">
            <div className="flex flex-wrap gap-1">
              {brand.default_posting_settings.default_platforms.map((platform, index) => (
                <span
                  key={index}
                  className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-white ${socialMediaUtils.getPlatformColor(platform)}`}
                >
                  {socialMediaUtils.formatPlatform(platform)}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Created Date */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            Created {socialMediaUtils.formatDate(brand.created_at)}
          </p>
        </div>
      </div>

      {/* Duplicate Form Modal */}
      {showDuplicateForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Duplicate Brand</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">New Brand Name</label>
                  <input
                    type="text"
                    value={duplicateName}
                    onChange={(e) => setDuplicateName(e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter new brand name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">New Brand Slug</label>
                  <input
                    type="text"
                    value={duplicateSlug}
                    onChange={(e) => setDuplicateSlug(e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter new brand slug"
                  />
                </div>
              </div>
              
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowDuplicateForm(false);
                    setDuplicateName('');
                    setDuplicateSlug('');
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDuplicate}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md"
                >
                  Duplicate
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}