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

  const handleBrandSelect = (brand) => {
    setSelectedBrand(brand);
    setSelectedSection(null); // Reset section when brand changes
  };

  const handleSectionSelect = (section) => {
    setSelectedSection(section);
  };

  const handleDataUpdate = async () => {
    // This will be called when data needs to be refreshed
    // The individual components will handle their own data loading
    console.log('Data update requested');
  };

  return (
    <div className="h-screen flex bg-gray-100 overflow-hidden">
      {/* Left Sidebar */}
      <AssetManagerSidebar
        selectedBrand={selectedBrand}
        onBrandSelect={handleBrandSelect}
        selectedSection={selectedSection}
        onSectionSelect={handleSectionSelect}
        onDataUpdate={handleDataUpdate}
      />

      {/* Main Content Area */}
      <div className="flex-1">
        <AssetManagerContent
          selectedBrand={selectedBrand}
          selectedSection={selectedSection}
          onDataUpdate={handleDataUpdate}
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