'use client';

import { useState } from 'react';
import { socialMediaUtils } from '@/lib/api/socialMedia';

export default function TemplateCard({ template, brands, onEdit, onDelete, onArchive, onActivate, onDuplicate }) {
  const [showActions, setShowActions] = useState(false);
  const [showDuplicateForm, setShowDuplicateForm] = useState(false);
  const [duplicateName, setDuplicateName] = useState('');

  const brand = brands.find(b => b.id === template.brand_id);

  const handleDuplicate = (e) => {
    e.stopPropagation();
    if (!duplicateName.trim()) {
      alert('Please enter a name for the duplicate');
      return;
    }
    onDuplicate(template.id, duplicateName);
    setShowDuplicateForm(false);
    setDuplicateName('');
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'archived':
        return 'bg-gray-100 text-gray-800';
      case 'draft':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
      {/* Template Header */}
      <div className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <h3 className="text-lg font-semibold text-gray-900">{template.name}</h3>
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(template.status)}`}>
                {template.status.charAt(0).toUpperCase() + template.status.slice(1)}
              </span>
            </div>
            <p className="text-sm text-gray-500 mt-1">
              {socialMediaUtils.formatTemplateType(template.type)} • v{template.version}
            </p>
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
                      onEdit(template);
                      setShowActions(false);
                    }}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    Edit
                  </button>
                  {template.status === 'active' ? (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onArchive(template.id);
                        setShowActions(false);
                      }}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Archive
                    </button>
                  ) : (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onActivate(template.id);
                        setShowActions(false);
                      }}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Activate
                    </button>
                  )}
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
                      onDelete(template.id);
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

        {/* Template Description */}
        {template.structure && template.structure.description && (
          <p className="text-sm text-gray-600 mt-3 line-clamp-2">
            {template.structure.description}
          </p>
        )}

        {/* Template Stats */}
        <div className="mt-4 grid grid-cols-3 gap-2 text-center">
          <div className="p-2 bg-gray-50 rounded">
            <p className="text-lg font-bold text-gray-900">
              {template.structure?.scenes?.length || 0}
            </p>
            <p className="text-xs text-gray-500">Scenes</p>
          </div>
          <div className="p-2 bg-gray-50 rounded">
            <p className="text-lg font-bold text-gray-900">
              {template.structure?.hooks?.length || 0}
            </p>
            <p className="text-xs text-gray-500">Hooks</p>
          </div>
          <div className="p-2 bg-gray-50 rounded">
            <p className="text-lg font-bold text-gray-900">
              {template.structure?.placeholders?.length || 0}
            </p>
            <p className="text-xs text-gray-500">Placeholders</p>
          </div>
        </div>

        {/* Theme Colors */}
        {template.structure?.theme && (
          <div className="mt-4">
            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-500">Theme:</span>
              <div className="flex space-x-1">
                {template.structure.theme.color_palette?.slice(0, 3).map((color, index) => (
                  <div
                    key={index}
                    className="w-4 h-4 rounded-full border border-gray-300"
                    style={{ backgroundColor: color }}
                    title={color}
                  />
                ))}
              </div>
              <span className="text-xs text-gray-500 capitalize">
                {template.structure.theme.mood}
              </span>
            </div>
          </div>
        )}

        {/* Aspect Ratios */}
        {template.structure?.theme?.preferred_aspect && (
          <div className="mt-2">
            <div className="flex flex-wrap gap-1">
              {template.structure.theme.preferred_aspect.map((aspect, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                >
                  {aspect}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* References Count */}
        {template.references && (
          <div className="mt-4 p-2 bg-blue-50 rounded">
            <div className="flex items-center justify-between text-sm">
              <span className="text-blue-800">References:</span>
              <span className="text-blue-600">
                {template.references.images?.length || 0} images, {template.references.videos?.length || 0} videos
              </span>
            </div>
          </div>
        )}

        {/* Assets Count */}
        {template.assets && template.assets.length > 0 && (
          <div className="mt-2 p-2 bg-green-50 rounded">
            <div className="flex items-center justify-between text-sm">
              <span className="text-green-800">Assets:</span>
              <span className="text-green-600">{template.assets.length} items</span>
            </div>
          </div>
        )}

        {/* Created Date */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            Created {socialMediaUtils.formatDate(template.created_at)}
          </p>
        </div>
      </div>

      {/* Duplicate Form Modal */}
      {showDuplicateForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Duplicate Template</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">New Template Name</label>
                  <input
                    type="text"
                    value={duplicateName}
                    onChange={(e) => setDuplicateName(e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter new template name"
                  />
                </div>
              </div>
              
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowDuplicateForm(false);
                    setDuplicateName('');
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