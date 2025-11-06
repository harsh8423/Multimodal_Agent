'use client';

import { useState, useEffect } from 'react';
import { socialMediaUtils } from '@/lib/api/socialMedia';

export default function TemplateForm({ template, brands, onSubmit, onClose }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState({
    brand_id: '',
    name: '',
    type: 'instagram_post',
    structure: {
      description: '',
      scenes: [],
      hooks: [],
      placeholders: [],
      theme: {
        mood: 'professional',
        color_palette: ['#3B82F6', '#10B981'],
        preferred_aspect: ['1:1'],
      },
      description_prompt: '',
    },
    references: {
      images: [],
      videos: [],
      notes: '',
    },
    assets: [],
  });

  const [placeholderInput, setPlaceholderInput] = useState('');
  const [colorInput, setColorInput] = useState('#3B82F6');
  const [aspectInput, setAspectInput] = useState('1:1');
  const [hookInput, setHookInput] = useState({ position: 'start', example: '', cta: '' });
  const [sceneInput, setSceneInput] = useState({ scene_id: 1, duration_sec: 5, instructions: '', visual_hints: [], audio_cue: '', hooks: [] });
  const [referenceImageInput, setReferenceImageInput] = useState('');
  const [referenceVideoInput, setReferenceVideoInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const isEditing = !!template;

  const steps = [
    {
      id: 'basic',
      title: 'Basic Info',
      icon: '📝',
      description: 'What type of template?'
    },
    {
      id: 'structure',
      title: 'Structure',
      icon: '🏗️',
      description: 'Define the template structure'
    },
    {
      id: 'theme',
      title: 'Theme',
      icon: '🎨',
      description: 'Choose colors and mood'
    },
    {
      id: 'content',
      title: 'Content',
      icon: '📋',
      description: 'Add hooks and placeholders'
    },
    {
      id: 'references',
      title: 'References',
      icon: '📚',
      description: 'Reference materials'
    }
  ];

  useEffect(() => {
    if (template) {
      setFormData({
        brand_id: template.brand_id || '',
        name: template.name || '',
        type: template.type || 'instagram_post',
        structure: {
          description: template.structure?.description || '',
          scenes: template.structure?.scenes || [],
          hooks: template.structure?.hooks || [],
          placeholders: template.structure?.placeholders || [],
          theme: {
            mood: template.structure?.theme?.mood || 'professional',
            color_palette: template.structure?.theme?.color_palette || ['#3B82F6', '#10B981'],
            preferred_aspect: template.structure?.theme?.preferred_aspect || ['1:1'],
          },
          description_prompt: template.structure?.description_prompt || '',
        },
        references: {
          images: template.references?.images || [],
          videos: template.references?.videos || [],
          notes: template.references?.notes || '',
        },
        assets: template.assets || [],
      });
    }
  }, [template]);

  const handleInputChange = (field, value) => {
    if (field.includes('.')) {
      const parts = field.split('.');
      setFormData(prev => {
        const newData = { ...prev };
        let current = newData;
        
        for (let i = 0; i < parts.length - 1; i++) {
          if (!current[parts[i]]) {
            current[parts[i]] = {};
          }
          current = current[parts[i]];
        }
        
        current[parts[parts.length - 1]] = value;
        return newData;
      });
    } else {
      setFormData(prev => ({
        ...prev,
        [field]: value,
      }));
    }
  };

  const handlePlaceholderAdd = () => {
    if (placeholderInput.trim() && !formData.structure.placeholders.includes(placeholderInput.trim())) {
      setFormData(prev => ({
        ...prev,
        structure: {
          ...prev.structure,
          placeholders: [...prev.structure.placeholders, placeholderInput.trim()],
        },
      }));
      setPlaceholderInput('');
    }
  };

  const handlePlaceholderRemove = (index) => {
    setFormData(prev => ({
      ...prev,
      structure: {
        ...prev.structure,
        placeholders: prev.structure.placeholders.filter((_, i) => i !== index),
      },
    }));
  };

  const handleColorAdd = () => {
    if (colorInput && !formData.structure?.theme?.color_palette?.includes(colorInput)) {
      setFormData(prev => ({
        ...prev,
        structure: {
          ...prev.structure,
          theme: {
            ...prev.structure.theme,
            color_palette: [...(prev.structure?.theme?.color_palette || []), colorInput],
          },
        },
      }));
    }
  };

  const handleColorRemove = (index) => {
    setFormData(prev => ({
      ...prev,
      structure: {
        ...prev.structure,
        theme: {
          ...prev.structure.theme,
          color_palette: (prev.structure?.theme?.color_palette || []).filter((_, i) => i !== index),
        },
      },
    }));
  };

  const handleAspectAdd = () => {
    if (aspectInput && !formData.structure?.theme?.preferred_aspect?.includes(aspectInput)) {
      setFormData(prev => ({
        ...prev,
        structure: {
          ...prev.structure,
          theme: {
            ...prev.structure.theme,
            preferred_aspect: [...(prev.structure?.theme?.preferred_aspect || []), aspectInput],
          },
        },
      }));
    }
  };

  const handleAspectRemove = (index) => {
    setFormData(prev => ({
      ...prev,
      structure: {
        ...prev.structure,
        theme: {
          ...prev.structure.theme,
          preferred_aspect: (prev.structure?.theme?.preferred_aspect || []).filter((_, i) => i !== index),
        },
      },
    }));
  };

  const handleHookAdd = () => {
    if (hookInput.position && hookInput.example) {
      setFormData(prev => ({
        ...prev,
        structure: {
          ...prev.structure,
          hooks: [...(prev.structure?.hooks || []), { ...hookInput }],
        },
      }));
      setHookInput({ position: 'start', example: '', cta: '' });
    }
  };

  const handleHookRemove = (index) => {
    setFormData(prev => ({
      ...prev,
      structure: {
        ...prev.structure,
        hooks: (prev.structure?.hooks || []).filter((_, i) => i !== index),
      },
    }));
  };

  const handleReferenceImageAdd = () => {
    if (referenceImageInput.trim()) {
      setFormData(prev => ({
        ...prev,
        references: {
          ...prev.references,
          images: [...(prev.references?.images || []), referenceImageInput.trim()],
        },
      }));
      setReferenceImageInput('');
    }
  };

  const handleReferenceImageRemove = (index) => {
    setFormData(prev => ({
      ...prev,
      references: {
        ...prev.references,
        images: (prev.references?.images || []).filter((_, i) => i !== index),
      },
    }));
  };

  const handleReferenceVideoAdd = () => {
    if (referenceVideoInput.trim()) {
      setFormData(prev => ({
        ...prev,
        references: {
          ...prev.references,
          videos: [...(prev.references?.videos || []), referenceVideoInput.trim()],
        },
      }));
      setReferenceVideoInput('');
    }
  };

  const handleReferenceVideoRemove = (index) => {
    setFormData(prev => ({
      ...prev,
      references: {
        ...prev.references,
        videos: (prev.references?.videos || []).filter((_, i) => i !== index),
      },
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isEditing) {
        await onSubmit(template.id, formData);
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

  const templateTypes = ['instagram_post', 'linkedin_post', 'reel', 'short', 'carousel', 'image_post'];
  const moods = ['professional', 'playful', 'exciting', 'calm', 'energetic', 'elegant', 'bold', 'minimal'];
  const commonAspects = ['1:1', '16:9', '9:16', '4:3', '3:4', '21:9'];

  const renderStepContent = () => {
    switch (currentStep) {
      case 0: // Basic Info
        return (
          <div className="space-y-8">
            

            <div className="space-y-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="transform hover:scale-105 transition-all duration-300">
                  <label className="block text-lg font-bold text-purple-700 mb-3 flex items-center">
                    <span className="text-2xl mr-2">🏢</span>
                    Brand (Optional)
                  </label>
                  <select
                    value={formData.brand_id}
                    onChange={(e) => handleInputChange('brand_id', e.target.value)}
                    className="w-full px-6 py-4 bg-gradient-to-r from-pink-100 to-purple-100 border-4 border-purple-300 rounded-2xl text-purple-800 text-lg font-bold focus:outline-none focus:ring-4 focus:ring-yellow-400 focus:border-yellow-400 transition-all duration-300 hover:scale-105 transform hover:skew-x-1"
                  >
                    <option value="">🎯 Select a brand (optional)</option>
                    {brands.map((brand) => (
                      <option key={brand.id} value={brand.id}>
                        🏢 {brand.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="transform hover:scale-105 transition-all duration-300">
                  <label className="block text-lg font-bold text-purple-700 mb-3 flex items-center">
                    <span className="text-2xl mr-2">📱</span>
                    Template Type *
                  </label>
                  <select
                    required
                    value={formData.type}
                    onChange={(e) => handleInputChange('type', e.target.value)}
                    className="w-full px-6 py-4 bg-gradient-to-r from-blue-100 to-purple-100 border-4 border-blue-300 rounded-2xl text-blue-800 text-lg font-bold focus:outline-none focus:ring-4 focus:ring-yellow-400 focus:border-yellow-400 transition-all duration-300 hover:scale-105 transform hover:skew-x-1"
                  >
                    {templateTypes.map((type) => (
                      <option key={type} value={type}>
                        📱 {socialMediaUtils.formatTemplateType(type)}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="transform hover:scale-105 transition-all duration-300">
                <label className="block text-lg font-bold text-purple-700 mb-3 flex items-center">
                  <span className="text-2xl mr-2">✨</span>
                  Template Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="w-full px-6 py-4 bg-gradient-to-r from-yellow-100 to-pink-100 border-4 border-yellow-300 rounded-2xl text-purple-800 text-lg font-bold focus:outline-none focus:ring-4 focus:ring-purple-400 focus:border-purple-400 transition-all duration-300 hover:scale-105 transform hover:skew-x-1"
                  placeholder="🎨 Enter your amazing template name"
                />
              </div>
            </div>
          </div>
        );

      case 1: // Structure
        return (
          <div className="space-y-8">
            <div className="space-y-8">
              <div className="transform hover:scale-105 transition-all duration-300">
                <label className="block text-lg font-bold text-purple-700 mb-3 flex items-center">
                  <span className="text-2xl mr-2">📖</span>
                  Description *
                </label>
                <textarea
                  required
                  rows={4}
                  value={formData.structure.description}
                  onChange={(e) => handleInputChange('structure.description', e.target.value)}
                  className="w-full px-6 py-4 bg-gradient-to-r from-green-100 to-blue-100 border-4 border-green-300 rounded-2xl text-purple-800 text-lg font-bold focus:outline-none focus:ring-4 focus:ring-yellow-400 focus:border-yellow-400 transition-all duration-300 resize-none hover:scale-105 transform hover:skew-x-1"
                  placeholder="🏗️ Describe what this template is for..."
                />
              </div>

              <div className="transform hover:scale-105 transition-all duration-300">
                <label className="block text-lg font-bold text-purple-700 mb-3 flex items-center">
                  <span className="text-2xl mr-2">🤖</span>
                  Description Prompt
                </label>
                <textarea
                  rows={3}
                  value={formData.structure.description_prompt}
                  onChange={(e) => handleInputChange('structure.description_prompt', e.target.value)}
                  className="w-full px-6 py-4 bg-gradient-to-r from-orange-100 to-pink-100 border-4 border-orange-300 rounded-2xl text-purple-800 text-lg font-bold focus:outline-none focus:ring-4 focus:ring-yellow-400 focus:border-yellow-400 transition-all duration-300 resize-none hover:scale-105 transform hover:skew-x-1"
                  placeholder="🤖 Prompt for generating captions..."
                />
              </div>
            </div>
          </div>
        );

      case 2: // Theme
        return (
          <div className="space-y-6 animate-slide-in">
            <div className="text-center mb-8">
              <div className="text-6xl mb-4 animate-spin">🎨</div>
              <h3 className="text-2xl font-bold text-gray-800 mb-2">Style Your Template!</h3>
              <p className="text-gray-600">Choose colors, mood, and aspect ratios</p>
            </div>

            <div className="space-y-6">
              <div className="relative group">
                <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="text-xl mr-2">😊</span>
                  Mood
                </label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {moods.map((mood) => (
                    <label key={mood} className="flex items-center p-4 border-2 border-gray-200 rounded-xl hover:border-blue-500 hover:bg-blue-50 transition-all duration-300 cursor-pointer group">
                      <input
                        type="radio"
                        name="mood"
                        value={mood}
                        checked={formData.structure.theme.mood === mood}
                        onChange={(e) => handleInputChange('structure.theme.mood', e.target.value)}
                        className="h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300"
                      />
                      <span className="ml-3 text-lg font-medium text-gray-700 group-hover:text-blue-700 capitalize">{mood}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="relative group">
                <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="text-xl mr-2">🌈</span>
                  Color Palette
                </label>
                <div className="flex space-x-3">
                  <input
                    type="color"
                    value={colorInput}
                    onChange={(e) => setColorInput(e.target.value)}
                    className="w-16 h-12 border-2 border-gray-200 rounded-xl cursor-pointer hover:scale-110 transition-transform duration-300"
                  />
                  <button
                    type="button"
                    onClick={handleColorAdd}
                    className="px-6 py-3 bg-gradient-to-r from-pink-500 to-purple-500 text-white rounded-xl hover:from-pink-600 hover:to-purple-600 transition-all duration-300 font-semibold hover:scale-105 shadow-lg"
                  >
                    Add Color ✨
                  </button>
                </div>
                {formData.structure?.theme?.color_palette?.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {formData.structure?.theme?.color_palette?.map((color, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-3 py-2 rounded-full text-sm font-medium text-white hover:scale-105 transition-transform duration-200"
                        style={{ backgroundColor: color }}
                      >
                        {color}
                        <button
                          type="button"
                          onClick={() => handleColorRemove(index)}
                          className="ml-2 text-white hover:text-gray-200 transition-colors duration-200"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="relative group">
                <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="text-xl mr-2">📐</span>
                  Preferred Aspect Ratios
                </label>
                <div className="flex space-x-3">
                  <select
                    value={aspectInput}
                    onChange={(e) => setAspectInput(e.target.value)}
                    className="px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                  >
                    {commonAspects.map((aspect) => (
                      <option key={aspect} value={aspect}>
                        {aspect}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={handleAspectAdd}
                    className="px-6 py-3 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-xl hover:from-green-600 hover:to-blue-600 transition-all duration-300 font-semibold hover:scale-105 shadow-lg"
                  >
                    Add Aspect ✨
                  </button>
                </div>
                {formData.structure?.theme?.preferred_aspect?.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {formData.structure?.theme?.preferred_aspect?.map((aspect, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-3 py-2 rounded-full text-sm font-medium bg-gradient-to-r from-blue-100 to-green-100 text-blue-800 hover:scale-105 transition-transform duration-200"
                      >
                        {aspect}
                        <button
                          type="button"
                          onClick={() => handleAspectRemove(index)}
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

      case 3: // Content
        return (
          <div className="space-y-6 animate-slide-in">
            

            <div className="space-y-6">
              <div className="relative group">
                <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="text-xl mr-2">🔤</span>
                  Content Placeholders
                </label>
                <div className="flex space-x-3">
                  <input
                    type="text"
                    value={placeholderInput}
                    onChange={(e) => setPlaceholderInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handlePlaceholderAdd())}
                    className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                    placeholder="Enter placeholder name"
                  />
                  <button
                    type="button"
                    onClick={handlePlaceholderAdd}
                    className="px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl hover:from-orange-600 hover:to-red-600 transition-all duration-300 font-semibold hover:scale-105 shadow-lg"
                  >
                    Add ✨
                  </button>
                </div>
                {formData.structure.placeholders.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {formData.structure.placeholders.map((placeholder, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-3 py-2 rounded-full text-sm font-medium bg-gradient-to-r from-green-100 to-blue-100 text-green-800 hover:scale-105 transition-transform duration-200"
                      >
                        {placeholder}
                        <button
                          type="button"
                          onClick={() => handlePlaceholderRemove(index)}
                          className="ml-2 text-green-600 hover:text-red-600 transition-colors duration-200"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="relative group">
                <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="text-xl mr-2">🎣</span>
                  Content Hooks
                </label>
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Position</label>
                      <select
                        value={hookInput.position}
                        onChange={(e) => setHookInput(prev => ({ ...prev, position: e.target.value }))}
                        className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                      >
                        <option value="start">Start</option>
                        <option value="mid">Middle</option>
                        <option value="end">End</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Example</label>
                      <input
                        type="text"
                        value={hookInput.example}
                        onChange={(e) => setHookInput(prev => ({ ...prev, example: e.target.value }))}
                        className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                        placeholder="Hook example text"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Call to Action</label>
                      <input
                        type="text"
                        value={hookInput.cta}
                        onChange={(e) => setHookInput(prev => ({ ...prev, cta: e.target.value }))}
                        className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                        placeholder="CTA text"
                      />
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={handleHookAdd}
                    className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl hover:from-purple-600 hover:to-pink-600 transition-all duration-300 font-semibold hover:scale-105 shadow-lg"
                  >
                    Add Hook ✨
                  </button>
                </div>
                
                {formData.structure?.hooks?.length > 0 && (
                  <div className="mt-4 space-y-2">
                    {formData.structure.hooks.map((hook, index) => (
                      <div key={index} className="flex items-center justify-between p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl border-2 border-purple-200">
                        <div>
                          <span className="text-sm font-semibold text-purple-800">{hook.position}</span>
                          <p className="text-sm text-gray-600">{hook.example}</p>
                          {hook.cta && <p className="text-xs text-blue-600">CTA: {hook.cta}</p>}
                        </div>
                        <button
                          type="button"
                          onClick={() => handleHookRemove(index)}
                          className="text-red-600 hover:text-red-800 transition-colors duration-200"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        );

      case 4: // References
        return (
          <div className="space-y-6 animate-slide-in">

            <div className="space-y-6">
              <div className="relative group">
                <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="text-xl mr-2">📝</span>
                  Reference Notes
                </label>
                <textarea
                  rows={4}
                  value={formData.references.notes}
                  onChange={(e) => handleInputChange('references.notes', e.target.value)}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium resize-none"
                  placeholder="Add notes about reference materials..."
                />
              </div>

              <div className="relative group">
                <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="text-xl mr-2">🖼️</span>
                  Reference Image URLs
                </label>
                <div className="flex space-x-3">
                  <input
                    type="url"
                    value={referenceImageInput}
                    onChange={(e) => setReferenceImageInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleReferenceImageAdd())}
                    className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                    placeholder="Enter image URL"
                  />
                  <button
                    type="button"
                    onClick={handleReferenceImageAdd}
                    className="px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-xl hover:from-blue-600 hover:to-cyan-600 transition-all duration-300 font-semibold hover:scale-105 shadow-lg"
                  >
                    Add ✨
                  </button>
                </div>
                {formData.references?.images?.length > 0 && (
                  <div className="mt-4 space-y-2">
                    {formData.references.images.map((url, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-xl border border-blue-200">
                        <span className="truncate text-sm font-medium text-blue-800">{url}</span>
                        <button
                          type="button"
                          onClick={() => handleReferenceImageRemove(index)}
                          className="text-red-600 hover:text-red-800 ml-2 transition-colors duration-200"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="relative group">
                <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="text-xl mr-2">🎥</span>
                  Reference Video URLs
                </label>
                <div className="flex space-x-3">
                  <input
                    type="url"
                    value={referenceVideoInput}
                    onChange={(e) => setReferenceVideoInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleReferenceVideoAdd())}
                    className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 text-lg font-medium"
                    placeholder="Enter video URL"
                  />
                  <button
                    type="button"
                    onClick={handleReferenceVideoAdd}
                    className="px-6 py-3 bg-gradient-to-r from-red-500 to-pink-500 text-white rounded-xl hover:from-red-600 hover:to-pink-600 transition-all duration-300 font-semibold hover:scale-105 shadow-lg"
                  >
                    Add ✨
                  </button>
                </div>
                {formData.references?.videos?.length > 0 && (
                  <div className="mt-4 space-y-2">
                    {formData.references.videos.map((url, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gradient-to-r from-red-50 to-pink-50 rounded-xl border border-red-200">
                        <span className="truncate text-sm font-medium text-red-800">{url}</span>
                        <button
                          type="button"
                          onClick={() => handleReferenceVideoRemove(index)}
                          className="text-red-600 hover:text-red-800 ml-2 transition-colors duration-200"
                        >
                          ×
                        </button>
                      </div>
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
                {isEditing ? '🎨 Edit Template' : '✨ Create New Template'}
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
                      <span>{isEditing ? 'Update Template' : 'Create Template'}</span>
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