'use client';

import { useState, useEffect } from 'react';
import { brandsAPI, templatesAPI, competitorsAPI, scrapedPostsAPI, scrapingAPI } from '@/lib/api/socialMedia';

// Import existing tab components
import TemplatesTab from '@/components/asset-manager/TemplatesTab';
import CompetitorsTab from '@/components/asset-manager/CompetitorsTab';
import ScrapedPostsTab from '@/components/asset-manager/ScrapedPostsTab';
import ScrapingTab from '@/components/asset-manager/ScrapingTab';

// Import form components
import BrandForm from '@/components/asset-manager/BrandForm';
import CompetitorForm from '@/components/asset-manager/CompetitorForm';
import TemplateForm from '@/components/asset-manager/TemplateForm';

const AssetManagerContent = ({ selectedBrand, selectedSection, onDataUpdate, activeForm, onFormClose }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    templates: 0,
    competitors: 0,
    scrapedPosts: 0,
  });

  // Form state management
  const [formData, setFormData] = useState(null);
  const [brands, setBrands] = useState([]);

  useEffect(() => {
    if (selectedBrand) {
      loadBrandStats();
    }
  }, [selectedBrand]);

  useEffect(() => {
    loadBrands();
  }, []);

  const loadBrands = async () => {
    try {
      const response = await brandsAPI.getAll({ limit: 100 });
      setBrands(response.brands || []);
    } catch (err) {
      console.error('Failed to load brands:', err);
    }
  };

  const loadBrandStats = async () => {
    if (!selectedBrand) return;
    
    try {
      setLoading(true);
      const [templatesRes, competitorsRes, scrapedPostsRes] = await Promise.all([
        templatesAPI.getAll({ brand_id: selectedBrand.id, limit: 1 }),
        competitorsAPI.getAll({ brand_id: selectedBrand.id, limit: 1 }),
        scrapedPostsAPI.getAll({ brand_id: selectedBrand.id, limit: 1 }),
      ]);

      setStats({
        templates: templatesRes.total || 0,
        competitors: competitorsRes.total || 0,
        scrapedPosts: scrapedPostsRes.total || 0,
      });
    } catch (err) {
      console.error('Failed to load brand stats:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Form handlers
  const handleFormOpen = (formType, data = null) => {
    console.log('Opening form:', formType, data);
    setFormData(data);
    // Call parent's onDataUpdate to set activeForm
    if (onDataUpdate) {
      onDataUpdate(formType);
    }
  };

  const handleFormClose = () => {
    if (onFormClose) {
      onFormClose();
    }
    setFormData(null);
  };

  const handleFormSubmit = async (data) => {
    try {
      if (activeForm === 'brand') {
        if (formData) {
          await brandsAPI.update(formData.id, data);
        } else {
          await brandsAPI.create(data);
        }
      } else if (activeForm === 'competitor') {
        if (formData) {
          await competitorsAPI.update(formData.id, data);
        } else {
          await competitorsAPI.create(data);
        }
      } else if (activeForm === 'template') {
        if (formData) {
          await templatesAPI.update(formData.id, data);
        } else {
          await templatesAPI.create(data);
        }
      }
      
      handleFormClose();
      loadBrandStats();
      onDataUpdate?.();
    } catch (err) {
      console.error('Failed to submit form:', err);
      throw err;
    }
  };

  const renderContent = () => {
    if (!selectedBrand) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center animate-fade-in">
            <div className="text-8xl mb-6 animate-bounce">🎯</div>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Select a Brand</h2>
            <p className="text-gray-600 text-lg">Choose a brand from the sidebar to view its assets and manage content.</p>
          </div>
        </div>
      );
    }

    if (!selectedSection) {
      return (
        <div className="max-w-6xl mx-auto">
          {/* Brand Header */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 mb-8">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-4 mb-4">
                  <div className="w-16 h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
                    <span className="text-white text-2xl font-bold">{selectedBrand.name.charAt(0)}</span>
                  </div>
                  <div>
                    <h1 className="text-3xl font-bold text-gray-900">{selectedBrand.name}</h1>
                    <p className="text-gray-600 mt-1">{selectedBrand.description || 'No description available'}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-all duration-300">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Templates</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">{stats.templates}</p>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span className="text-blue-600 text-xl">📝</span>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-all duration-300">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Competitors</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">{stats.competitors}</p>
                </div>
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <span className="text-green-600 text-xl">👥</span>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-all duration-300">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Scraped Posts</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">{stats.scrapedPosts}</p>
                </div>
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                  <span className="text-purple-600 text-xl">📊</span>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
            <p className="text-gray-600 mb-6">Choose a section from the sidebar to manage specific assets:</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <span className="text-xl">📝</span>
                <span className="text-sm font-medium text-gray-700">Templates</span>
              </div>
              <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <span className="text-xl">👥</span>
                <span className="text-sm font-medium text-gray-700">Competitors</span>
              </div>
              <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <span className="text-xl">📊</span>
                <span className="text-sm font-medium text-gray-700">Scraped Posts</span>
              </div>
              <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <span className="text-xl">🔍</span>
                <span className="text-sm font-medium text-gray-700">Scraping</span>
              </div>
            </div>
          </div>
        </div>
      );
    }

    // Render the appropriate component based on selected section
    switch (selectedSection) {
      case 'templates':
        return <TemplatesTab onUpdate={loadBrandStats} brandId={selectedBrand.id} onFormOpen={handleFormOpen} />;
      case 'competitors':
        return <CompetitorsTab onUpdate={loadBrandStats} brandId={selectedBrand.id} onFormOpen={handleFormOpen} />;
      case 'scraped-posts':
        return <ScrapedPostsTab onUpdate={loadBrandStats} brandId={selectedBrand.id} />;
      case 'scraping':
        return <ScrapingTab onUpdate={loadBrandStats} brandId={selectedBrand.id} />;
      default:
        return (
          <div className="flex items-center justify-center h-full">
            <div className="text-center animate-fade-in">
              <div className="text-8xl mb-6 animate-bounce">❓</div>
              <h2 className="text-3xl font-bold text-gray-900 mb-4">Unknown Section</h2>
              <p className="text-gray-600 text-lg">The selected section is not recognized.</p>
            </div>
          </div>
        );
    }
  };

  // Render form if active
  const renderForm = () => {
    if (!activeForm) return null;

    console.log('Rendering form:', activeForm, formData);

    const commonProps = {
      onSubmit: handleFormSubmit,
      onClose: handleFormClose,
    };

    switch (activeForm) {
      case 'brand':
        return <BrandForm brand={formData} {...commonProps} />;
      case 'competitor':
        return <CompetitorForm competitor={formData} brands={brands} {...commonProps} />;
      case 'template':
        return <TemplateForm template={formData} brands={brands} {...commonProps} />;
      default:
        return null;
    }
  };

  return (
    <>
      {/* Error Message */}
      {error && (
        <div className="mx-6 mt-4 bg-red-50 border border-red-200 rounded-lg p-4 animate-fade-in">
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

      {/* Main Content */}
      {activeForm ? (
        <div className="flex-1 flex flex-col">
          {renderForm()}
        </div>
      ) : (
        <div className="flex-1 flex flex-col bg-gradient-to-br from-gray-50 to-gray-100">
          <div className="flex-1 overflow-auto p-6">
            {renderContent()}
          </div>
        </div>
      )}
    </>
  );
};

export default AssetManagerContent;