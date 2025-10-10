'use client';

import { useState, useEffect } from 'react';
import { brandsAPI } from '@/lib/api/socialMedia';
import BrandForm from './BrandForm';

const AssetManagerSidebar = ({ 
  selectedBrand, 
  onBrandSelect, 
  selectedSection, 
  onSectionSelect, 
  onDataUpdate 
}) => {
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedBrands, setExpandedBrands] = useState(new Set());
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [showBrandForm, setShowBrandForm] = useState(false);

  useEffect(() => {
    loadBrands();
  }, []);

  const loadBrands = async () => {
    try {
      setLoading(true);
      const response = await brandsAPI.getAll({ limit: 100 });
      setBrands(response.brands || []);
      
      // Auto-expand first brand if available
      if (response.brands && response.brands.length > 0 && !selectedBrand) {
        onBrandSelect(response.brands[0]);
        setExpandedBrands(new Set([response.brands[0].id]));
      }
    } catch (error) {
      console.error('Failed to load brands:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleBrandExpansion = (brandId) => {
    const newExpanded = new Set(expandedBrands);
    if (newExpanded.has(brandId)) {
      newExpanded.delete(brandId);
    } else {
      newExpanded.add(brandId);
    }
    setExpandedBrands(newExpanded);
  };

  const handleBrandSelect = (brand) => {
    onBrandSelect(brand);
    if (!expandedBrands.has(brand.id)) {
      setExpandedBrands(new Set([brand.id]));
    }
  };

  const handleCreateBrand = () => {
    setShowBrandForm(true);
  };

  const handleBrandCreated = async () => {
    setShowBrandForm(false);
    await loadBrands();
    if (onDataUpdate) {
      onDataUpdate();
    }
  };

  const sections = [
    { id: 'templates', name: 'Templates', icon: '📝', color: 'text-blue-500' },
    { id: 'competitors', name: 'Competitors', icon: '👥', color: 'text-purple-500' },
    { id: 'scraped-posts', name: 'Scraped Posts', icon: '📊', color: 'text-green-500' },
    { id: 'scraping', name: 'Scraping', icon: '🔍', color: 'text-orange-500' }
  ];

  return (
    <div className={`bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 text-white transition-all duration-500 ease-in-out ${
      isCollapsed ? 'w-16' : 'w-72'
    } flex flex-col h-full shadow-2xl border-r border-gray-700`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <div className="animate-fade-in">
              <h1 className="text-2xl font-bold text-white">
                Asset Manager
              </h1>
              <p className="text-gray-400 text-sm mt-1">Manage your brands & assets</p>
            </div>
          )}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-all duration-300 hover:scale-105"
          >
            <svg className="w-5 h-5 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d={isCollapsed ? "M9 5l7 7-7 7" : "M15 19l-7-7 7-7"} />
            </svg>
          </button>
        </div>
      </div>

      {/* Quick Actions */}
      {!isCollapsed && (
        <div className="p-4 border-b border-gray-700 animate-fade-in">
          <button
            onClick={handleCreateBrand}
            className="w-full p-3 bg-gradient-to-r from-gray-600 to-gray-700 rounded-lg hover:from-gray-500 hover:to-gray-600 transition-all duration-300 flex items-center space-x-3 shadow-lg hover:shadow-xl hover:scale-105 group"
          >
            <span className="text-xl group-hover:scale-110 transition-transform duration-300">✨</span>
            <span className="font-medium">Create New Brand</span>
          </button>
        </div>
      )}

      {/* Brands List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4">
            <div className="animate-pulse space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-12 bg-gray-700 rounded-lg"></div>
              ))}
            </div>
          </div>
        ) : (
          <div className="p-4 space-y-2">
            {brands.length === 0 ? (
              <div className="text-center py-8 animate-fade-in">
                <div className="text-4xl mb-2 animate-bounce">🏢</div>
                <p className="text-gray-400 text-sm">No brands yet</p>
                <p className="text-gray-500 text-xs mt-1">Create your first brand to get started</p>
              </div>
            ) : (
              brands.map((brand) => (
                <div key={brand.id} className="space-y-1">
                  {/* Brand Header */}
                  <div
                    onClick={() => handleBrandSelect(brand)}
                    className={`p-3 rounded-lg cursor-pointer transition-all duration-300 hover:scale-105 ${
                      selectedBrand?.id === brand.id
                        ? 'bg-gradient-to-r from-gray-600/30 to-gray-700/30 border border-gray-500/50 shadow-lg'
                        : 'hover:bg-gray-700/50 hover:shadow-md'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-gradient-to-r from-gray-600 to-gray-700 rounded-full flex items-center justify-center text-sm font-bold shadow-md hover:shadow-lg transition-all duration-300 hover:scale-110">
                          {brand.name?.charAt(0)?.toUpperCase() || 'B'}
                        </div>
                        {!isCollapsed && (
                          <div className="animate-fade-in">
                            <p className="font-medium text-sm">{brand.name}</p>
                            <p className="text-xs text-gray-400 truncate max-w-32">
                              {brand.industry || 'No industry'}
                            </p>
                          </div>
                        )}
                      </div>
                      {!isCollapsed && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleBrandExpansion(brand.id);
                          }}
                          className="p-1 rounded hover:bg-gray-600 transition-all duration-300 hover:scale-110"
                        >
                          <svg 
                            className={`w-4 h-4 transition-transform duration-300 ${
                              expandedBrands.has(brand.id) ? 'rotate-90' : ''
                            }`} 
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Brand Sections */}
                  {!isCollapsed && expandedBrands.has(brand.id) && (
                    <div className="ml-4 space-y-1 animate-fade-in">
                      {sections.map((section) => (
                        <button
                          key={section.id}
                          onClick={() => onSectionSelect(section.id)}
                          className={`w-full p-2 rounded-lg text-left transition-all duration-300 hover:scale-105 ${
                            selectedSection === section.id && selectedBrand?.id === brand.id
                              ? 'bg-gray-700 border-l-2 border-gray-400 shadow-md'
                              : 'hover:bg-gray-700/50 hover:shadow-sm'
                          }`}
                        >
                          <div className="flex items-center space-x-3">
                            <span className="text-lg hover:scale-110 transition-transform duration-300">{section.icon}</span>
                            <span className="text-sm font-medium">{section.name}</span>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Brand Form Modal */}
      {showBrandForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
          <div className="w-96 bg-white rounded-lg shadow-2xl p-6">
            <BrandForm
              onClose={() => setShowBrandForm(false)}
              onSuccess={handleBrandCreated}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default AssetManagerSidebar;