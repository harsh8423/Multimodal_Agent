'use client';

import { useState, useEffect } from 'react';

export default function BrandForm({ brand, onSubmit, onClose }) {
  const [currentStep, setCurrentStep] = useState(0);
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
    voice_name: '',
    voice_id: '',
  });

  const [audienceInput, setAudienceInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const isEditing = !!brand;

  const steps = [
    {
      id: 'basic',
      title: 'Basic Info',
      icon: '🏢',
      description: 'Tell us about your brand'
    },
    {
      id: 'theme',
      title: 'Brand Theme',
      icon: '🎨',
      description: 'Choose your colors & style'
    },
    {
      id: 'details',
      title: 'Business Details',
      icon: '💼',
      description: 'Industry & target audience'
    },
    {
      id: 'voice',
      title: 'Brand Voice',
      icon: '🎤',
      description: 'Configure brand voice settings'
    },
    {
      id: 'settings',
      title: 'Posting Settings',
      icon: '⚙️',
      description: 'Configure posting preferences'
    }
  ];

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
        voice_name: brand.voice_name || '',
        voice_id: brand.voice_id || '',
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
  const timezones = [
    'UTC', 'America/New_York', 'America/Los_Angeles', 'Europe/London',
    'Europe/Paris', 'Asia/Tokyo', 'Asia/Kolkata', 'Australia/Sydney'
  ];

  const renderStepContent = () => {
    switch (currentStep) {
      case 0: // Basic Info
        return (
          <div className="space-y-8">
            <div className="space-y-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="transform hover:scale-105 transition-all duration-300">
                  <label className="block text-lg font-bold text-purple-700 mb-3 flex items-center">
                    <span className="text-2xl mr-2">📝</span>
                    Brand Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    className="w-full px-6 py-4 bg-gradient-to-r from-pink-100 to-purple-100 border-4 border-purple-300 rounded-2xl text-purple-800 text-lg font-bold focus:outline-none focus:ring-4 focus:ring-yellow-400 focus:border-yellow-400 transition-all duration-300 hover:scale-105 transform hover:skew-x-1"
                    placeholder="🏢 Enter your amazing brand name"
                  />
                </div>

                <div className="transform hover:scale-105 transition-all duration-300">
                  <label className="block text-lg font-bold text-purple-700 mb-3 flex items-center">
                    <span className="text-2xl mr-2">🔗</span>
                    Brand Slug *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.slug}
                    onChange={(e) => handleInputChange('slug', e.target.value)}
                    className="w-full px-6 py-4 bg-gradient-to-r from-blue-100 to-purple-100 border-4 border-blue-300 rounded-2xl text-blue-800 text-lg font-bold focus:outline-none focus:ring-4 focus:ring-yellow-400 focus:border-yellow-400 transition-all duration-300 hover:scale-105 transform hover:skew-x-1"
                    placeholder="🔗 brand-slug"
                  />
                </div>
              </div>

              <div className="transform hover:scale-105 transition-all duration-300">
                <label className="block text-lg font-bold text-purple-700 mb-3 flex items-center">
                  <span className="text-2xl mr-2">📖</span>
                  Description *
                </label>
                <textarea
                  required
                  rows={4}
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  className="w-full px-6 py-4 bg-gradient-to-r from-green-100 to-blue-100 border-4 border-green-300 rounded-2xl text-purple-800 text-lg font-bold focus:outline-none focus:ring-4 focus:ring-yellow-400 focus:border-yellow-400 transition-all duration-300 resize-none hover:scale-105 transform hover:skew-x-1"
                  placeholder="📖 Tell us what makes your brand special..."
                />
              </div>
            </div>
          </div>
        );

      case 1: // Theme
        return (
          <div className="space-y-6 animate-slide-in">
            <div className="text-center mb-8">
              <div className="text-6xl mb-4 animate-pulse">🎨</div>
              <h3 className="text-2xl font-bold text-gray-800 mb-2">Style Your Brand!</h3>
              <p className="text-gray-600">Choose colors and fonts that represent your brand's personality</p>
            </div>

            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="relative group">
                  <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                    <span className="text-xl mr-2">🎨</span>
                    Primary Color
                  </label>
                  <div className="flex items-center space-x-3">
                    <input
                      type="color"
                      value={formData.theme.primary_color}
                      onChange={(e) => handleInputChange('theme.primary_color', e.target.value)}
                      className="w-16 h-12 border-2 border-gray-200 rounded-xl cursor-pointer hover:scale-110 transition-transform duration-300"
                    />
                    <input
                      type="text"
                      value={formData.theme.primary_color}
                      onChange={(e) => handleInputChange('theme.primary_color', e.target.value)}
                      className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                    />
                  </div>
                </div>

                <div className="relative group">
                  <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                    <span className="text-xl mr-2">🌈</span>
                    Secondary Color
                  </label>
                  <div className="flex items-center space-x-3">
                    <input
                      type="color"
                      value={formData.theme.secondary_color}
                      onChange={(e) => handleInputChange('theme.secondary_color', e.target.value)}
                      className="w-16 h-12 border-2 border-gray-200 rounded-xl cursor-pointer hover:scale-110 transition-transform duration-300"
                    />
                    <input
                      type="text"
                      value={formData.theme.secondary_color}
                      onChange={(e) => handleInputChange('theme.secondary_color', e.target.value)}
                      className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="relative group">
                  <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                    <span className="text-xl mr-2">✍️</span>
                    Font Family
                  </label>
                  <select
                    value={formData.theme.font}
                    onChange={(e) => handleInputChange('theme.font', e.target.value)}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                  >
                    <option value="Inter">Inter</option>
                    <option value="Roboto">Roboto</option>
                    <option value="Open Sans">Open Sans</option>
                    <option value="Lato">Lato</option>
                    <option value="Montserrat">Montserrat</option>
                  </select>
                </div>

                <div className="relative group">
                  <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                    <span className="text-xl mr-2">🖼️</span>
                    Logo URL
                  </label>
                  <input
                    type="url"
                    value={formData.theme.logo_url}
                    onChange={(e) => handleInputChange('theme.logo_url', e.target.value)}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                    placeholder="https://example.com/logo.png"
                  />
                </div>
              </div>
            </div>
          </div>
        );

      case 2: // Business Details
        return (
          <div className="space-y-6 animate-slide-in">
            <div className="text-center mb-8">
              <div className="text-6xl mb-4 animate-bounce">💼</div>
              <h3 className="text-2xl font-bold text-gray-800 mb-2">Business Details</h3>
              <p className="text-gray-600">Tell us about your industry and target audience</p>
            </div>

            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="relative group">
                  <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                    <span className="text-xl mr-2">🌐</span>
                    Website
                  </label>
                  <input
                    type="url"
                    value={formData.details.website}
                    onChange={(e) => handleInputChange('details.website', e.target.value)}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                    placeholder="https://example.com"
                  />
                </div>

                <div className="relative group">
                  <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                    <span className="text-xl mr-2">🏭</span>
                    Industry
                  </label>
                  <input
                    type="text"
                    value={formData.details.industry}
                    onChange={(e) => handleInputChange('details.industry', e.target.value)}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                    placeholder="Technology, Fashion, etc."
                  />
                </div>
              </div>

              <div className="relative group">
                <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="text-xl mr-2">👥</span>
                  Target Audience
                </label>
                <div className="flex space-x-3">
                  <input
                    type="text"
                    value={audienceInput}
                    onChange={(e) => setAudienceInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAudienceAdd())}
                    className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                    placeholder="Enter audience segment"
                  />
                  <button
                    type="button"
                    onClick={handleAudienceAdd}
                    className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl hover:from-blue-600 hover:to-purple-600 transition-all duration-300 font-semibold hover:scale-105 shadow-lg"
                  >
                    Add ✨
                  </button>
                </div>
                {formData.details.audience.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {formData.details.audience.map((audience, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-3 py-2 rounded-full text-sm font-medium bg-gradient-to-r from-blue-100 to-purple-100 text-blue-800 hover:scale-105 transition-transform duration-200"
                      >
                        {audience}
                        <button
                          type="button"
                          onClick={() => handleAudienceRemove(index)}
                          className="ml-2 text-blue-600 hover:text-red-600 transition-colors duration-200"
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

      case 3: // Brand Voice
        return (
          <div className="space-y-6 animate-slide-in">
            <div className="text-center mb-8">
              <div className="text-6xl mb-4 animate-bounce">🎤</div>
              <h3 className="text-2xl font-bold text-gray-800 mb-2">Brand Voice Settings</h3>
              <p className="text-gray-600">Configure your brand's voice and tone</p>
            </div>

            <div className="space-y-6">
              <div className="relative group">
                <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="text-xl mr-2">🎭</span>
                  Voice Name
                </label>
                <input
                  type="text"
                  value={formData.voice_name}
                  onChange={(e) => handleInputChange('voice_name', e.target.value)}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                  placeholder="e.g., Professional, Friendly, Casual"
                />
                <div className="absolute -bottom-1 left-0 w-full h-1 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full transform scale-x-0 group-focus-within:scale-x-100 transition-transform duration-300"></div>
              </div>

              <div className="relative group">
                <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="text-xl mr-2">🆔</span>
                  Voice ID
                </label>
                <input
                  type="text"
                  value={formData.voice_id}
                  onChange={(e) => handleInputChange('voice_id', e.target.value)}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                  placeholder="e.g., voice_123, professional_tone"
                />
                <div className="absolute -bottom-1 left-0 w-full h-1 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full transform scale-x-0 group-focus-within:scale-x-100 transition-transform duration-300"></div>
              </div>

              <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-4">
                <div className="flex items-start">
                  <div className="text-2xl mr-3">💡</div>
                  <div>
                    <h3 className="text-sm font-semibold text-blue-800">Voice Configuration Tips</h3>
                    <ul className="text-sm text-blue-700 mt-2 space-y-1">
                      <li>• Voice Name: Descriptive name for your brand's tone (e.g., "Professional", "Friendly")</li>
                      <li>• Voice ID: Unique identifier for your voice settings (e.g., "voice_123")</li>
                      <li>• These settings help maintain consistent messaging across all content</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 4: // Posting Settings
        return (
          <div className="space-y-6 animate-slide-in">
            <div className="text-center mb-8">
              <div className="text-6xl mb-4 animate-spin">⚙️</div>
              <h3 className="text-2xl font-bold text-gray-800 mb-2">Posting Settings</h3>
              <p className="text-gray-600">Configure your default posting preferences</p>
            </div>

            <div className="space-y-6">
              <div className="relative group">
                <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="text-xl mr-2">🌍</span>
                  Timezone
                </label>
                <select
                  value={formData.default_posting_settings.timezone}
                  onChange={(e) => handleInputChange('default_posting_settings.timezone', e.target.value)}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                >
                  {timezones.map(tz => (
                    <option key={tz} value={tz}>{tz}</option>
                  ))}
                </select>
              </div>

              <div className="relative group">
                <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="text-xl mr-2">📱</span>
                  Default Platforms
                </label>
                <div className="grid grid-cols-2 gap-4">
                  {platforms.map(platform => (
                    <label key={platform} className="flex items-center p-4 border-2 border-gray-200 rounded-xl hover:border-blue-500 hover:bg-blue-50 transition-all duration-300 cursor-pointer group">
                      <input
                        type="checkbox"
                        checked={formData.default_posting_settings.default_platforms.includes(platform)}
                        onChange={() => handlePlatformToggle(platform)}
                        className="h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <span className="ml-3 text-lg font-medium text-gray-700 group-hover:text-blue-700 capitalize">{platform}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="relative group">
                <label className="flex items-center p-4 border-2 border-gray-200 rounded-xl hover:border-blue-500 hover:bg-blue-50 transition-all duration-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.default_posting_settings.post_approval_required}
                    onChange={(e) => handleInputChange('default_posting_settings.post_approval_required', e.target.checked)}
                    className="h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="ml-3 text-lg font-medium text-gray-700">Require post approval</span>
                </label>
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
                {isEditing ? '🎨 Edit Brand' : '✨ Create New Brand'}
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
                      <span>{isEditing ? 'Update Brand' : 'Create Brand'}</span>
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