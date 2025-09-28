'use client';

import { useState, useEffect } from 'react';
import { socialMediaUtils } from '@/lib/api/socialMedia';

export default function CompetitorForm({ competitor, brands, onSubmit, onClose }) {
  const [formData, setFormData] = useState({
    brand_id: '',
    name: '',
    platform: 'instagram',
    handle: '',
    profile_url: '',
    metrics: {
      followers: '',
      avg_engagement: '',
      posts_count: '',
      last_post_date: '',
    },
    scrape_config: {
      scrape_frequency: 'weekly',
      auto_scrape: false,
    },
    metadata: {
      notes: '',
      tags: [],
    },
  });

  const [tagInput, setTagInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const isEditing = !!competitor;

  useEffect(() => {
    if (competitor) {
      setFormData({
        brand_id: competitor.brand_id || '',
        name: competitor.name || '',
        platform: competitor.platform || 'instagram',
        handle: competitor.handle || '',
        profile_url: competitor.profile_url || '',
        metrics: {
          followers: competitor.metrics?.followers || '',
          avg_engagement: competitor.metrics?.avg_engagement || '',
          posts_count: competitor.metrics?.posts_count || '',
          last_post_date: competitor.metrics?.last_post_date || '',
        },
        scrape_config: {
          scrape_frequency: competitor.scrape_config?.scrape_frequency || 'weekly',
          auto_scrape: competitor.scrape_config?.auto_scrape || false,
        },
        metadata: {
          notes: competitor.metadata?.notes || '',
          tags: competitor.metadata?.tags || [],
        },
      });
    }
  }, [competitor]);

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

  const handleTagAdd = () => {
    if (tagInput.trim() && !formData.metadata.tags.includes(tagInput.trim())) {
      setFormData(prev => ({
        ...prev,
        metadata: {
          ...prev.metadata,
          tags: [...prev.metadata.tags, tagInput.trim()],
        },
      }));
      setTagInput('');
    }
  };

  const handleTagRemove = (index) => {
    setFormData(prev => ({
      ...prev,
      metadata: {
        ...prev.metadata,
        tags: prev.metadata.tags.filter((_, i) => i !== index),
      },
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Clean up form data
      const submitData = {
        ...formData,
        metrics: {
          followers: formData.metrics.followers ? parseInt(formData.metrics.followers) : null,
          avg_engagement: formData.metrics.avg_engagement ? parseFloat(formData.metrics.avg_engagement) : null,
          posts_count: formData.metrics.posts_count ? parseInt(formData.metrics.posts_count) : null,
          last_post_date: formData.metrics.last_post_date || null,
        },
        metadata: {
          notes: formData.metadata.notes || '',
          tags: formData.metadata.tags,
        },
      };

      if (isEditing) {
        await onSubmit(competitor.id, submitData);
      } else {
        await onSubmit(submitData);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const platforms = ['instagram', 'linkedin', 'youtube', 'reddit'];
  const frequencies = ['daily', 'weekly', 'monthly'];

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            {isEditing ? 'Edit Competitor' : 'Add New Competitor'}
          </h3>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Brand</label>
                <select
                  value={formData.brand_id}
                  onChange={(e) => handleInputChange('brand_id', e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select a brand (optional)</option>
                  {brands.map((brand) => (
                    <option key={brand.id} value={brand.id}>
                      {brand.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Platform *</label>
                <select
                  required
                  value={formData.platform}
                  onChange={(e) => handleInputChange('platform', e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  {platforms.map((platform) => (
                    <option key={platform} value={platform}>
                      {socialMediaUtils.formatPlatform(platform)}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Name *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Competitor name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Handle *</label>
                <input
                  type="text"
                  required
                  value={formData.handle}
                  onChange={(e) => handleInputChange('handle', e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="@username or channel name"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Profile URL *</label>
              <input
                type="url"
                required
                value={formData.profile_url}
                onChange={(e) => handleInputChange('profile_url', e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="https://instagram.com/username"
              />
            </div>

            {/* Metrics */}
            <div className="border-t pt-6">
              <h4 className="text-md font-medium text-gray-900 mb-4">Metrics (Optional)</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Followers</label>
                  <input
                    type="number"
                    value={formData.metrics.followers}
                    onChange={(e) => handleInputChange('metrics.followers', e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="50000"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Avg Engagement Rate</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    value={formData.metrics.avg_engagement}
                    onChange={(e) => handleInputChange('metrics.avg_engagement', e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="0.05"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Posts Count</label>
                  <input
                    type="number"
                    value={formData.metrics.posts_count}
                    onChange={(e) => handleInputChange('metrics.posts_count', e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="1200"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Last Post Date</label>
                  <input
                    type="datetime-local"
                    value={formData.metrics.last_post_date}
                    onChange={(e) => handleInputChange('metrics.last_post_date', e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            </div>

            {/* Scrape Configuration */}
            <div className="border-t pt-6">
              <h4 className="text-md font-medium text-gray-900 mb-4">Scrape Configuration</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Scrape Frequency</label>
                  <select
                    value={formData.scrape_config.scrape_frequency}
                    onChange={(e) => handleInputChange('scrape_config.scrape_frequency', e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    {frequencies.map((freq) => (
                      <option key={freq} value={freq}>
                        {freq.charAt(0).toUpperCase() + freq.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.scrape_config.auto_scrape}
                      onChange={(e) => handleInputChange('scrape_config.auto_scrape', e.target.checked)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700">Enable Auto Scraping</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Metadata */}
            <div className="border-t pt-6">
              <h4 className="text-md font-medium text-gray-900 mb-4">Additional Information</h4>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Notes</label>
                <textarea
                  rows={3}
                  value={formData.metadata.notes}
                  onChange={(e) => handleInputChange('metadata.notes', e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Add any notes about this competitor..."
                />
              </div>

              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700">Tags</label>
                <div className="mt-1 flex space-x-2">
                  <input
                    type="text"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleTagAdd())}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter tag"
                  />
                  <button
                    type="button"
                    onClick={handleTagAdd}
                    className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Add
                  </button>
                </div>
                {formData.metadata.tags.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {formData.metadata.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800"
                      >
                        {tag}
                        <button
                          type="button"
                          onClick={() => handleTagRemove(index)}
                          className="ml-1 text-purple-600 hover:text-purple-800"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
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
                {loading ? 'Saving...' : (isEditing ? 'Update Competitor' : 'Add Competitor')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}