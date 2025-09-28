'use client';

import { useState, useEffect } from 'react';

export default function BrandForm({ brand, onSubmit, onClose }) {
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    description: '',
    theme: {
      primary_color: '#3B82F6',
      secondary_color: '#10B981',
      font: 'Inter',
      logo_url: '',
    },
    details: {
      website: '',
      industry: '',
      audience: [],
    },
    default_posting_settings: {
      timezone: 'UTC',
      default_platforms: [],
      post_approval_required: false,
    },
  });

  const [audienceInput, setAudienceInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const isEditing = !!brand;

  useEffect(() => {
    if (brand) {
      setFormData({
        name: brand.name || '',
        slug: brand.slug || '',
        description: brand.description || '',
        theme: {
          primary_color: brand.theme?.primary_color || '#3B82F6',
          secondary_color: brand.theme?.secondary_color || '#10B981',
          font: brand.theme?.font || 'Inter',
          logo_url: brand.theme?.logo_url || '',
        },
        details: {
          website: brand.details?.website || '',
          industry: brand.details?.industry || '',
          audience: brand.details?.audience || [],
        },
        default_posting_settings: {
          timezone: brand.default_posting_settings?.timezone || 'UTC',
          default_platforms: brand.default_posting_settings?.default_platforms || [],
          post_approval_required: brand.default_posting_settings?.post_approval_required || false,
        },
      });
    }
  }, [brand]);

  const handleInputChange = (field, value) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      setFormData(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: value,
        },
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [field]: value,
      }));
    }
  };

  const handleAudienceAdd = () => {
    if (audienceInput.trim() && !formData.details.audience.includes(audienceInput.trim())) {
      setFormData(prev => ({
        ...prev,
        details: {
          ...prev.details,
          audience: [...prev.details.audience, audienceInput.trim()],
        },
      }));
      setAudienceInput('');
    }
  };

  const handleAudienceRemove = (index) => {
    setFormData(prev => ({
      ...prev,
      details: {
        ...prev.details,
        audience: prev.details.audience.filter((_, i) => i !== index),
      },
    }));
  };

  const handlePlatformToggle = (platform) => {
    setFormData(prev => ({
      ...prev,
      default_posting_settings: {
        ...prev.default_posting_settings,
        default_platforms: prev.default_posting_settings.default_platforms.includes(platform)
          ? prev.default_posting_settings.default_platforms.filter(p => p !== platform)
          : [...prev.default_posting_settings.default_platforms, platform],
      },
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isEditing) {
        await onSubmit(brand.id, formData);
      } else {
        await onSubmit(formData);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const platforms = ['instagram', 'linkedin', 'youtube', 'reddit'];
  const timezones = [
    'UTC', 'America/New_York', 'America/Los_Angeles', 'Europe/London',
    'Europe/Paris', 'Asia/Tokyo', 'Asia/Kolkata', 'Australia/Sydney'
  ];

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            {isEditing ? 'Edit Brand' : 'Create New Brand'}
          </h3>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Brand Name *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter brand name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Brand Slug *</label>
                <input
                  type="text"
                  required
                  value={formData.slug}
                  onChange={(e) => handleInputChange('slug', e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="brand-slug"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Description *</label>
              <textarea
                required
                rows={3}
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter brand description"
              />
            </div>

            {/* Theme Settings */}
            <div className="border-t pt-6">
              <h4 className="text-md font-medium text-gray-900 mb-4">Theme Settings</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Primary Color</label>
                  <div className="mt-1 flex items-center space-x-2">
                    <input
                      type="color"
                      value={formData.theme.primary_color}
                      onChange={(e) => handleInputChange('theme.primary_color', e.target.value)}
                      className="w-12 h-10 border border-gray-300 rounded cursor-pointer"
                    />
                    <input
                      type="text"
                      value={formData.theme.primary_color}
                      onChange={(e) => handleInputChange('theme.primary_color', e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Secondary Color</label>
                  <div className="mt-1 flex items-center space-x-2">
                    <input
                      type="color"
                      value={formData.theme.secondary_color}
                      onChange={(e) => handleInputChange('theme.secondary_color', e.target.value)}
                      className="w-12 h-10 border border-gray-300 rounded cursor-pointer"
                    />
                    <input
                      type="text"
                      value={formData.theme.secondary_color}
                      onChange={(e) => handleInputChange('theme.secondary_color', e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Font Family</label>
                  <select
                    value={formData.theme.font}
                    onChange={(e) => handleInputChange('theme.font', e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="Inter">Inter</option>
                    <option value="Roboto">Roboto</option>
                    <option value="Open Sans">Open Sans</option>
                    <option value="Lato">Lato</option>
                    <option value="Montserrat">Montserrat</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Logo URL</label>
                  <input
                    type="url"
                    value={formData.theme.logo_url}
                    onChange={(e) => handleInputChange('theme.logo_url', e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="https://example.com/logo.png"
                  />
                </div>
              </div>
            </div>

            {/* Business Details */}
            <div className="border-t pt-6">
              <h4 className="text-md font-medium text-gray-900 mb-4">Business Details</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Website</label>
                  <input
                    type="url"
                    value={formData.details.website}
                    onChange={(e) => handleInputChange('details.website', e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="https://example.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Industry</label>
                  <input
                    type="text"
                    value={formData.details.industry}
                    onChange={(e) => handleInputChange('details.industry', e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Technology, Fashion, etc."
                  />
                </div>
              </div>

              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700">Target Audience</label>
                <div className="mt-1 flex space-x-2">
                  <input
                    type="text"
                    value={audienceInput}
                    onChange={(e) => setAudienceInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAudienceAdd())}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter audience segment"
                  />
                  <button
                    type="button"
                    onClick={handleAudienceAdd}
                    className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Add
                  </button>
                </div>
                {formData.details.audience.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {formData.details.audience.map((audience, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {audience}
                        <button
                          type="button"
                          onClick={() => handleAudienceRemove(index)}
                          className="ml-1 text-blue-600 hover:text-blue-800"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Default Posting Settings */}
            <div className="border-t pt-6">
              <h4 className="text-md font-medium text-gray-900 mb-4">Default Posting Settings</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Timezone</label>
                  <select
                    value={formData.default_posting_settings.timezone}
                    onChange={(e) => handleInputChange('default_posting_settings.timezone', e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    {timezones.map(tz => (
                      <option key={tz} value={tz}>{tz}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Default Platforms</label>
                  <div className="mt-1 space-y-2">
                    {platforms.map(platform => (
                      <label key={platform} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={formData.default_posting_settings.default_platforms.includes(platform)}
                          onChange={() => handlePlatformToggle(platform)}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <span className="ml-2 text-sm text-gray-700 capitalize">{platform}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.default_posting_settings.post_approval_required}
                    onChange={(e) => handleInputChange('default_posting_settings.post_approval_required', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700">Require post approval</span>
                </label>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">Error</h3>
                    <div className="mt-2 text-sm text-red-700">
                      <p>{error}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Form Actions */}
            <div className="flex justify-end space-x-3 pt-6 border-t">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Saving...' : (isEditing ? 'Update Brand' : 'Create Brand')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}