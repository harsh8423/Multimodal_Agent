'use client';

import { useState, useEffect } from 'react';
import { brandsAPI } from '@/lib/api/socialMedia';

const AssetManagerSidebar = ({ 
  selectedBrand, 
  onBrandSelect, 
  selectedSection, 
  onSectionSelect, 
  onDataUpdate,
  onCollapseChange
}) => {
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    loadBrands();
  }, []);

  const loadBrands = async () => {
    try {
      setLoading(true);
      const response = await brandsAPI.getAll({ limit: 100 });
      setBrands(response.brands || []);
      
      // Auto-select first brand if available
      if (response.brands && response.brands.length > 0 && !selectedBrand) {
        onBrandSelect(response.brands[0]);
      }
    } catch (error) {
      console.error('Failed to load brands:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBrandSelect = (brand) => {
    onBrandSelect(brand);
  };

  const handleCreateBrand = () => {
    // Trigger brand form in the main content area instead of modal
    if (onDataUpdate) {
      onDataUpdate('brand');
    }
  };

  // Simplified navigation sections - removed redundant 'brands' tab
  const sections = [
    { id: 'templates', name: 'Templates', icon: '📝', color: 'text-blue-500' },
    { id: 'competitors', name: 'Competitors', icon: '👥', color: 'text-purple-500' },
    { id: 'scraped-posts', name: 'Scraped Posts', icon: '📊', color: 'text-green-500' },
    { id: 'scraping', name: 'Scraping', icon: '🔍', color: 'text-orange-500' }
  ];

  return (
    <div className={`bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 text-white transition-all duration-500 ease-in-out ${
      isCollapsed ? 'w-16' : 'w-72'
    } flex flex-col h-screen fixed left-0 top-0 shadow-2xl border-r border-gray-700 z-10`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <div className="animate-fade-in flex-1">
              <h1 className="text-2xl font-bold text-white">
                Asset Manager
              </h1>
              <p className="text-gray-400 text-sm mt-1">Manage your brands & assets</p>
            </div>
          )}
          <button
            onClick={() => {
              const newCollapsed = !isCollapsed;
              setIsCollapsed(newCollapsed);
              if (onCollapseChange) {
                onCollapseChange(newCollapsed);
              }
            }}
            className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-all duration-300 hover:scale-105"
          >
            <svg className="w-5 h-5 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d={isCollapsed ? "M9 5l7 7-7 7" : "M15 19l-7-7 7-7"} />
            </svg>
          </button>
        </div>
      </div>

      {/* Brand Workspace Section */}
      {!isCollapsed && (
        <div className="p-4 border-b border-gray-700 animate-fade-in">
          <div className="space-y-4">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
              Brand Workspace
            </h3>
            
            {/* Brand Workspace Dropdown */}
            <div>
              <div className="relative group">
                <select
                  value={selectedBrand?.id || ''}
                  onChange={(e) => {
                    const brand = brands.find(b => b.id === e.target.value);
                    if (brand) handleBrandSelect(brand);
                  }}
                  className="w-full px-4 py-3 bg-gray-700 border-2 border-gray-500 rounded-xl text-white text-base font-medium focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 appearance-none cursor-pointer hover:bg-gray-600 hover:border-gray-400 transition-all duration-300 shadow-lg hover:shadow-xl"
                >
                  <option value="" className="bg-gray-800 text-gray-300 font-medium text-base">
                    Select Brand Workspace
                  </option>
                  {brands.map((brand) => (
                    <option 
                      key={brand.id} 
                      value={brand.id}
                      className="bg-gray-800 text-white font-medium text-base hover:bg-gray-700"
                    >
                      {brand.name}
                    </option>
                  ))}
                </select>
                <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                  <svg className="w-4 h-4 text-gray-400 group-hover:text-gray-300 transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Create New Brand Button */}
            <button
              onClick={handleCreateBrand}
              className="w-full p-3 bg-gradient-to-r from-gray-600 to-gray-700 rounded-lg hover:from-gray-500 hover:to-gray-600 transition-all duration-300 flex items-center space-x-3 shadow-lg hover:shadow-xl hover:scale-105 group"
            >
              <span className="text-xl group-hover:scale-110 transition-transform duration-300">✨</span>
              <span className="font-medium text-white">Create New Brand</span>
            </button>
          </div>
        </div>
      )}

      {/* Navigation Sections - Clean and Simple */}
      {!isCollapsed && selectedBrand && (
        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-2">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
              Navigation
            </h3>
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => onSectionSelect(section.id)}
                className={`w-full p-3 rounded-lg text-left transition-all duration-300 hover:scale-105 group ${
                  selectedSection === section.id
                    ? 'bg-gradient-to-r from-gray-600/30 to-gray-700/30 border border-gray-500/50 shadow-lg'
                    : 'hover:bg-gray-700/50 hover:shadow-md'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <span className="text-xl group-hover:scale-110 transition-transform duration-300">{section.icon}</span>
                  <span className="font-medium text-sm">{section.name}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isCollapsed && !selectedBrand && (
        <div className="flex-1 flex items-center justify-center p-4">
          <div className="text-center animate-fade-in">
            <div className="text-4xl mb-4 animate-bounce">🎯</div>
            <p className="text-gray-400 text-sm">Select a brand workspace</p>
            <p className="text-gray-500 text-xs mt-1">Choose a brand to start managing assets</p>
          </div>
        </div>
      )}

    </div>
  );
};

export default AssetManagerSidebar;