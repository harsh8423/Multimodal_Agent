'use client';

import { useState, useEffect } from 'react';
import { socialMediaUtils } from '@/lib/api/socialMedia';

export default function TemplateForm({ template, brands, onSubmit, onClose }) {
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
        
        // Navigate to the parent object
        for (let i = 0; i < parts.length - 1; i++) {
          if (!current[parts[i]]) {
            current[parts[i]] = {};
          }
          current = current[parts[i]];
        }
        
        // Set the final value
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

  const handleSceneAdd = () => {
    if (sceneInput.instructions) {
      setFormData(prev => ({
        ...prev,
        structure: {
          ...prev.structure,
          scenes: [...(prev.structure?.scenes || []), { ...sceneInput }],
        },
      }));
      setSceneInput({ 
        scene_id: (prev.structure?.scenes?.length || 0) + 2, 
        duration_sec: 5, 
        instructions: '', 
        visual_hints: [], 
        audio_cue: '', 
        hooks: [] 
      });
    }
  };

  const handleSceneRemove = (index) => {
    setFormData(prev => ({
      ...prev,
      structure: {
        ...prev.structure,
        scenes: (prev.structure?.scenes || []).filter((_, i) => i !== index),
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

  const templateTypes = ['instagram_post', 'linkedin_post', 'reel', 'short', 'carousel', 'image_post'];
  const moods = ['professional', 'playful', 'exciting', 'calm', 'energetic', 'elegant', 'bold', 'minimal'];
  const commonAspects = ['1:1', '16:9', '9:16', '4:3', '3:4', '21:9'];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm overflow-y-auto h-full w-full z-50 flex items-start justify-center p-4 pt-8">
      <div className="relative w-full max-w-4xl bg-white rounded-xl shadow-2xl my-8">
        {/* Fixed Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-xl z-10">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-bold text-gray-900">
              {isEditing ? 'Edit Template' : 'Create New Template'}
            </h3>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-all duration-200"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        
        <div className="p-6">

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
                <label className="block text-sm font-medium text-gray-700">Template Type *</label>
                <select
                  required
                  value={formData.type}
                  onChange={(e) => handleInputChange('type', e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  {templateTypes.map((type) => (
                    <option key={type} value={type}>
                      {socialMediaUtils.formatTemplateType(type)}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Template Name *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter template name"
              />
            </div>

            {/* Structure */}
            <div className="border-t pt-6">
              <h4 className="text-md font-medium text-gray-900 mb-4">Template Structure</h4>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Description *</label>
                <textarea
                  required
                  rows={3}
                  value={formData.structure.description}
                  onChange={(e) => handleInputChange('structure.description', e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Describe what this template is for..."
                />
              </div>

              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700">Description Prompt</label>
                <textarea
                  rows={2}
                  value={formData.structure.description_prompt}
                  onChange={(e) => handleInputChange('structure.description_prompt', e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Prompt for generating captions..."
                />
              </div>
            </div>

            {/* Theme */}
            <div className="border-t pt-6">
              <h4 className="text-md font-medium text-gray-900 mb-4">Theme Settings</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Mood</label>
                  <select
                    value={formData.structure.theme.mood}
                    onChange={(e) => handleInputChange('structure.theme.mood', e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    {moods.map((mood) => (
                      <option key={mood} value={mood}>
                        {mood.charAt(0).toUpperCase() + mood.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Color Palette */}
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700">Color Palette</label>
                <div className="mt-1 flex space-x-2">
                  <input
                    type="color"
                    value={colorInput}
                    onChange={(e) => setColorInput(e.target.value)}
                    className="w-12 h-10 border border-gray-300 rounded cursor-pointer"
                  />
                  <button
                    type="button"
                    onClick={handleColorAdd}
                    className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Add Color
                  </button>
                </div>
                {formData.structure?.theme?.color_palette?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {formData.structure?.theme?.color_palette?.map((color, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-white"
                        style={{ backgroundColor: color }}
                      >
                        {color}
                        <button
                          type="button"
                          onClick={() => handleColorRemove(index)}
                          className="ml-1 text-white hover:text-gray-200"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Preferred Aspect Ratios */}
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700">Preferred Aspect Ratios</label>
                <div className="mt-1 flex space-x-2">
                  <select
                    value={aspectInput}
                    onChange={(e) => setAspectInput(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
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
                    className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Add Aspect
                  </button>
                </div>
                {formData.structure?.theme?.preferred_aspect?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {formData.structure?.theme?.preferred_aspect?.map((aspect, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {aspect}
                        <button
                          type="button"
                          onClick={() => handleAspectRemove(index)}
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

            {/* Placeholders */}
            <div className="border-t pt-6">
              <h4 className="text-md font-medium text-gray-900 mb-4">Content Placeholders</h4>
              
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={placeholderInput}
                  onChange={(e) => setPlaceholderInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handlePlaceholderAdd())}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter placeholder name"
                />
                <button
                  type="button"
                  onClick={handlePlaceholderAdd}
                  className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Add
                </button>
              </div>
              {formData.structure.placeholders.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {formData.structure.placeholders.map((placeholder, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800"
                    >
                      {placeholder}
                      <button
                        type="button"
                        onClick={() => handlePlaceholderRemove(index)}
                        className="ml-1 text-green-600 hover:text-green-800"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Hooks */}
            <div className="border-t pt-6">
              <h4 className="text-md font-medium text-gray-900 mb-4">Content Hooks</h4>
              
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Position</label>
                    <select
                      value={hookInput.position}
                      onChange={(e) => setHookInput(prev => ({ ...prev, position: e.target.value }))}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="start">Start</option>
                      <option value="mid">Middle</option>
                      <option value="end">End</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Example</label>
                    <input
                      type="text"
                      value={hookInput.example}
                      onChange={(e) => setHookInput(prev => ({ ...prev, example: e.target.value }))}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Hook example text"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Call to Action</label>
                    <input
                      type="text"
                      value={hookInput.cta}
                      onChange={(e) => setHookInput(prev => ({ ...prev, cta: e.target.value }))}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="CTA text"
                    />
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleHookAdd}
                  className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Add Hook
                </button>
              </div>
              
              {formData.structure?.hooks?.length > 0 && (
                <div className="mt-4 space-y-2">
                  {formData.structure.hooks.map((hook, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                      <div>
                        <span className="text-sm font-medium text-gray-900">{hook.position}</span>
                        <p className="text-sm text-gray-600">{hook.example}</p>
                        {hook.cta && <p className="text-xs text-blue-600">CTA: {hook.cta}</p>}
                      </div>
                      <button
                        type="button"
                        onClick={() => handleHookRemove(index)}
                        className="text-red-600 hover:text-red-800"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Scenes */}
            <div className="border-t pt-6">
              <h4 className="text-md font-medium text-gray-900 mb-4">Video Scenes</h4>
              
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Scene ID</label>
                    <input
                      type="number"
                      value={sceneInput.scene_id}
                      onChange={(e) => setSceneInput(prev => ({ ...prev, scene_id: parseInt(e.target.value) || 1 }))}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      min="1"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Duration (seconds)</label>
                    <input
                      type="number"
                      value={sceneInput.duration_sec}
                      onChange={(e) => setSceneInput(prev => ({ ...prev, duration_sec: parseInt(e.target.value) || 5 }))}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      min="1"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Instructions</label>
                  <textarea
                    rows={3}
                    value={sceneInput.instructions}
                    onChange={(e) => setSceneInput(prev => ({ ...prev, instructions: e.target.value }))}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Describe what should happen in this scene..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Audio Cue</label>
                  <input
                    type="text"
                    value={sceneInput.audio_cue}
                    onChange={(e) => setSceneInput(prev => ({ ...prev, audio_cue: e.target.value }))}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Audio cue description"
                  />
                </div>
                <button
                  type="button"
                  onClick={handleSceneAdd}
                  className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Add Scene
                </button>
              </div>
              
              {formData.structure?.scenes?.length > 0 && (
                <div className="mt-4 space-y-2">
                  {formData.structure.scenes.map((scene, index) => (
                    <div key={index} className="flex items-start justify-between p-3 bg-gray-50 rounded-md">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-medium text-gray-900">Scene {scene.scene_id}</span>
                          <span className="text-xs text-gray-500">({scene.duration_sec}s)</span>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{scene.instructions}</p>
                        {scene.audio_cue && <p className="text-xs text-blue-600 mt-1">Audio: {scene.audio_cue}</p>}
                      </div>
                      <button
                        type="button"
                        onClick={() => handleSceneRemove(index)}
                        className="text-red-600 hover:text-red-800 ml-2"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* References */}
            <div className="border-t pt-6">
              <h4 className="text-md font-medium text-gray-900 mb-4">Reference Materials</h4>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Reference Notes</label>
                  <textarea
                    rows={3}
                    value={formData.references.notes}
                    onChange={(e) => handleInputChange('references.notes', e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Add notes about reference materials..."
                  />
                </div>

                {/* Reference Images */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">Reference Image URLs</label>
                  <div className="mt-1 flex space-x-2">
                    <input
                      type="url"
                      value={referenceImageInput}
                      onChange={(e) => setReferenceImageInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleReferenceImageAdd())}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Enter image URL"
                    />
                    <button
                      type="button"
                      onClick={handleReferenceImageAdd}
                      className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      Add
                    </button>
                  </div>
                  {formData.references?.images?.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {formData.references.images.map((url, index) => (
                        <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
                          <span className="truncate">{url}</span>
                          <button
                            type="button"
                            onClick={() => handleReferenceImageRemove(index)}
                            className="text-red-600 hover:text-red-800 ml-2"
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Reference Videos */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">Reference Video URLs</label>
                  <div className="mt-1 flex space-x-2">
                    <input
                      type="url"
                      value={referenceVideoInput}
                      onChange={(e) => setReferenceVideoInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleReferenceVideoAdd())}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Enter video URL"
                    />
                    <button
                      type="button"
                      onClick={handleReferenceVideoAdd}
                      className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      Add
                    </button>
                  </div>
                  {formData.references?.videos?.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {formData.references.videos.map((url, index) => (
                        <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
                          <span className="truncate">{url}</span>
                          <button
                            type="button"
                            onClick={() => handleReferenceVideoRemove(index)}
                            className="text-red-600 hover:text-red-800 ml-2"
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
            <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                className="px-6 py-3 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-all duration-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-3 text-sm font-medium text-white bg-gray-600 hover:bg-gray-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center space-x-2"
              >
                {loading ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <span>{isEditing ? 'Update Template' : 'Create Template'}</span>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}