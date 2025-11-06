'use client';

import { useState, useEffect } from 'react';
import { socialMediaUtils } from '@/lib/api/socialMedia';

export default function CompetitorForm({ competitor, brands, onSubmit, onClose }) {
  const [currentStep, setCurrentStep] = useState(0);
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

  const steps = [
    {
      id: 'basic',
      title: 'Basic Info',
      icon: '👥',
      description: 'Who is this competitor?'
    },
    {
      id: 'metrics',
      title: 'Metrics',
      icon: '📊',
      description: 'Track their performance'
    },
    {
      id: 'scraping',
      title: 'Scraping',
      icon: '🔍',
      description: 'Configure data collection'
    },
    {
      id: 'metadata',
      title: 'Additional Info',
      icon: '🏷️',
      description: 'Notes and tags'
    }
  ];

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

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const platforms = ['instagram', 'linkedin', 'youtube', 'reddit'];
  const frequencies = ['daily', 'weekly', 'monthly'];

  const renderStepContent = () => {
    switch (currentStep) {
      case 0: // Basic Info
        return (
          <div className="space-y-6 animate-slide-in">

            <div className="space-y-6">
              <div className="relative group">
                <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="text-xl mr-2">🏢</span>
                  Brand (Optional)
                </label>
                <select
                  value={formData.brand_id}
                  onChange={(e) => handleInputChange('brand_id', e.target.value)}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                >
                  <option value="">Select a brand (optional)</option>
                  {brands.map((brand) => (
                    <option key={brand.id} value={brand.id}>
                      {brand.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="relative group">
                  <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                    <span className="text-xl mr-2">📱</span>
                    Platform *
                  </label>
                  <select
                    required
                    value={formData.platform}
                    onChange={(e) => handleInputChange('platform', e.target.value)}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                  >
                    {platforms.map((platform) => (
                      <option key={platform} value={platform}>
                        {socialMediaUtils.formatPlatform(platform)}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="relative group">
                  <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                    <span className="text-xl mr-2">📝</span>
                    Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                    placeholder="Competitor name"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="relative group">
                  <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                    <span className="text-xl mr-2">@</span>
                    Handle *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.handle}
                    onChange={(e) => handleInputChange('handle', e.target.value)}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                    placeholder="@username or channel name"
                  />
                </div>

                <div className="relative group">
                  <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                    <span className="text-xl mr-2">🔗</span>
                    Profile URL *
                  </label>
                  <input
                    type="url"
                    required
                    value={formData.profile_url}
                    onChange={(e) => handleInputChange('profile_url', e.target.value)}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                    placeholder="https://instagram.com/username"
                  />
                </div>
              </div>
            </div>
          </div>
        );

      case 1: // Metrics
        return (
          <div className="space-y-6 animate-slide-in">

            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="relative group">
                  <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                    <span className="text-xl mr-2">👥</span>
                    Followers
                  </label>
                  <input
                    type="number"
                    value={formData.metrics.followers}
                    onChange={(e) => handleInputChange('metrics.followers', e.target.value)}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                    placeholder="50000"
                  />
                </div>

                <div className="relative group">
                  <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                    <span className="text-xl mr-2">💬</span>
                    Avg Engagement Rate
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    value={formData.metrics.avg_engagement}
                    onChange={(e) => handleInputChange('metrics.avg_engagement', e.target.value)}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                    placeholder="0.05"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="relative group">
                  <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                    <span className="text-xl mr-2">📝</span>
                    Posts Count
                  </label>
                  <input
                    type="number"
                    value={formData.metrics.posts_count}
                    onChange={(e) => handleInputChange('metrics.posts_count', e.target.value)}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                    placeholder="1200"
                  />
                </div>

                <div className="relative group">
                  <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                    <span className="text-xl mr-2">📅</span>
                    Last Post Date
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.metrics.last_post_date}
                    onChange={(e) => handleInputChange('metrics.last_post_date', e.target.value)}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                  />
                </div>
              </div>
            </div>
          </div>
        );

      case 2: // Scraping
        return (
          <div className="space-y-6 animate-slide-in">

            <div className="space-y-6">
              <div className="relative group">
                <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="text-xl mr-2">⏰</span>
                  Scrape Frequency
                </label>
                <div className="grid grid-cols-3 gap-4">
                  {frequencies.map((freq) => (
                    <label key={freq} className="flex items-center p-4 border-2 border-gray-200 rounded-xl hover:border-blue-500 hover:bg-blue-50 transition-all duration-300 cursor-pointer group">
                      <input
                        type="radio"
                        name="scrape_frequency"
                        value={freq}
                        checked={formData.scrape_config.scrape_frequency === freq}
                        onChange={(e) => handleInputChange('scrape_config.scrape_frequency', e.target.value)}
                        className="h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300"
                      />
                      <span className="ml-3 text-lg font-medium text-gray-700 group-hover:text-blue-700 capitalize">{freq}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="relative group">
                <label className="flex items-center p-6 border-2 border-gray-200 rounded-xl hover:border-blue-500 hover:bg-blue-50 transition-all duration-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.scrape_config.auto_scrape}
                    onChange={(e) => handleInputChange('scrape_config.auto_scrape', e.target.checked)}
                    className="h-6 w-6 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <div className="ml-4">
                    <span className="text-lg font-semibold text-gray-700">Enable Auto Scraping</span>
                    <p className="text-sm text-gray-500 mt-1">Automatically collect new posts based on frequency</p>
                  </div>
                </label>
              </div>
            </div>
          </div>
        );

      case 3: // Metadata
        return (
          <div className="space-y-6 animate-slide-in">

            <div className="space-y-6">
              <div className="relative group">
                <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="text-xl mr-2">📝</span>
                  Notes
                </label>
                <textarea
                  rows={4}
                  value={formData.metadata.notes}
                  onChange={(e) => handleInputChange('metadata.notes', e.target.value)}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium resize-none"
                  placeholder="Add any notes about this competitor..."
                />
              </div>

              <div className="relative group">
                <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="text-xl mr-2">🏷️</span>
                  Tags
                </label>
                <div className="flex space-x-3">
                  <input
                    type="text"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleTagAdd())}
                    className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                    placeholder="Enter tag"
                  />
                  <button
                    type="button"
                    onClick={handleTagAdd}
                    className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl hover:from-purple-600 hover:to-pink-600 transition-all duration-300 font-semibold hover:scale-105 shadow-lg"
                  >
                    Add ✨
                  </button>
                </div>
                {formData.metadata.tags.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {formData.metadata.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-3 py-2 rounded-full text-sm font-medium bg-gradient-to-r from-purple-100 to-pink-100 text-purple-800 hover:scale-105 transition-transform duration-200"
                      >
                        {tag}
                        <button
                          type="button"
                          onClick={() => handleTagRemove(index)}
                          className="ml-2 text-purple-600 hover:text-red-600 transition-colors duration-200"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="w-full bg-gradient-to-br from-pink-100 via-purple-50 to-blue-100">
      <form onSubmit={handleSubmit}>
        {/* Header */}
        <div className="bg-gradient-to-r from-pink-400 via-purple-500 to-blue-500 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-bold text-white mb-2 animate-bounce">
                {isEditing ? '🎨 Edit Competitor' : '✨ Add New Competitor'}
              </h2>
              <p className="text-pink-100 text-sm">Step {currentStep + 1} of {steps.length}</p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-3 text-white hover:bg-white/20 rounded-full transition-all duration-300 hover:scale-110 hover:rotate-12"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          {/* Progress Bar */}
          <div className="mt-6">
            <div className="flex items-center space-x-3">
              {steps.map((step, index) => (
                <div key={step.id} className="flex items-center">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-500 transform hover:scale-110 ${
                    index <= currentStep 
                      ? 'bg-yellow-400 text-purple-800 shadow-lg animate-pulse' 
                      : 'bg-white/30 text-white'
                  }`}>
                    {index < currentStep ? '🎉' : index + 1}
                  </div>
                  {index < steps.length - 1 && (
                    <div className={`w-12 h-2 mx-3 rounded-full transition-all duration-500 ${
                      index < currentStep ? 'bg-yellow-400 shadow-lg' : 'bg-white/30'
                    }`}></div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Navigation Buttons - Moved to Top */}
        <div className="bg-white/80 backdrop-blur-sm p-4 border-b-4 border-purple-200">
          <div className="flex justify-between items-center">
            <button
              type="button"
              onClick={prevStep}
              disabled={currentStep === 0}
              className="px-6 py-3 text-purple-700 bg-gradient-to-r from-pink-200 to-purple-200 border-4 border-purple-300 rounded-2xl hover:from-pink-300 hover:to-purple-300 hover:scale-105 hover:rotate-1 transition-all duration-300 font-bold disabled:opacity-50 disabled:cursor-not-allowed transform hover:skew-x-1"
            >
              ← Previous
            </button>

            <div className="flex space-x-4">
              <button
                type="button"
                onClick={onClose}
                className="px-6 py-3 text-gray-700 bg-gradient-to-r from-gray-200 to-gray-300 border-4 border-gray-400 rounded-2xl hover:from-gray-300 hover:to-gray-400 hover:scale-105 hover:rotate-1 transition-all duration-300 font-bold transform hover:skew-x-1"
              >
                Cancel
              </button>
              
              {currentStep < steps.length - 1 ? (
                <button
                  type="button"
                  onClick={nextStep}
                  className="px-8 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white border-4 border-blue-600 rounded-2xl hover:from-blue-600 hover:to-purple-700 hover:scale-110 hover:rotate-1 transition-all duration-300 font-bold shadow-lg transform hover:skew-x-1 animate-pulse"
                >
                  Next → 🚀
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={loading}
                  className="px-8 py-3 bg-gradient-to-r from-green-500 to-blue-600 text-white border-4 border-green-600 rounded-2xl hover:from-green-600 hover:to-blue-700 hover:scale-110 hover:rotate-1 transition-all duration-300 font-bold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 transform hover:skew-x-1"
                >
                  {loading ? (
                    <>
                      <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      <span>Saving...</span>
                    </>
                  ) : (
                    <>
                      <span>{isEditing ? 'Update Competitor' : 'Add Competitor'}</span>
                      <span className="animate-bounce">🎉</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Content - Scrollable */}
        <div className="p-8 pb-20">
          {renderStepContent()}

          {/* Error Message */}
          {error && (
            <div className="mt-8 bg-red-100 border-4 border-red-300 rounded-2xl p-6 animate-shake">
              <div className="flex items-center">
                <div className="text-3xl mr-4 animate-bounce">🚨</div>
                <div>
                  <h3 className="text-lg font-bold text-red-800">Oops! Something went wrong</h3>
                  <p className="text-red-700 font-medium">{error}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </form>
    </div>
  );
}