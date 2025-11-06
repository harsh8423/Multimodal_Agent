'use client';

import { useState, useEffect } from 'react';
import { brandsAPI } from '@/lib/api/socialMedia';

// New components
import AssetManagerSidebar from '@/components/asset-manager/AssetManagerSidebar';
import AssetManagerContent from '@/components/asset-manager/AssetManagerContent';
import AssetManagerChatbot from '@/components/asset-manager/AssetManagerChatbot';

export default function AssetManagerPage() {
  const [selectedBrand, setSelectedBrand] = useState(null);
  const [selectedSection, setSelectedSection] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeForm, setActiveForm] = useState(null);

  const handleBrandSelect = (brand) => {
    setSelectedBrand(brand);
    setSelectedSection(null); // Reset section when brand changes
  };

  const handleSectionSelect = (section) => {
    setSelectedSection(section);
  };

  const handleDataUpdate = async (formType = null) => {
    if (formType) {
      // Open form in main content area
      setActiveForm(formType);
      setSelectedSection(null); // Clear section when opening form
    } else {
      // This will be called when data needs to be refreshed
      // The individual components will handle their own data loading
      console.log('Data update requested');
    }
  };

  const handleFormClose = () => {
    setActiveForm(null);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Left Sidebar - Fixed */}
      <AssetManagerSidebar
        selectedBrand={selectedBrand}
        onBrandSelect={handleBrandSelect}
        selectedSection={selectedSection}
        onSectionSelect={handleSectionSelect}
        onDataUpdate={handleDataUpdate}
        onCollapseChange={setSidebarCollapsed}
      />

      {/* Main Content Area - Scrollable with dynamic left margin */}
      <div className={`min-h-screen overflow-y-auto transition-all duration-500 ${
        sidebarCollapsed ? 'ml-16' : 'ml-72'
      }`}>
        <AssetManagerContent
          selectedBrand={selectedBrand}
          selectedSection={selectedSection}
          onDataUpdate={handleDataUpdate}
          activeForm={activeForm}
          onFormClose={handleFormClose}
        />
      </div>

      {/* Floating Chatbot */}
      <AssetManagerChatbot
        selectedBrand={selectedBrand}
        onDataUpdate={handleDataUpdate}
      />
    </div>
  );
}