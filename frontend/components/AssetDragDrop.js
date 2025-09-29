'use client';

import { useState, useEffect } from 'react';
import { brandsAPI, competitorsAPI, templatesAPI, scrapedPostsAPI } from '@/lib/api/socialMedia';
import { X, GripVertical, Building2, Users, FileText, MessageSquare } from 'lucide-react';

const AssetDragDrop = ({ isOpen, onClose, onAssetDrop, embedded = false }) => {
  const [activeTab, setActiveTab] = useState('brands');
  const [brands, setBrands] = useState([]);
  const [competitors, setCompetitors] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [scrapedPosts, setScrapedPosts] = useState([]);
  const [selectedPlatform, setSelectedPlatform] = useState('all');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadAssets();
    }
  }, [isOpen]);

  const loadAssets = async () => {
    setLoading(true);
    try {
      const [brandsRes, competitorsRes, templatesRes, scrapedPostsRes] = await Promise.all([
        brandsAPI.getAll({ limit: 50 }),
        competitorsAPI.getAll({ limit: 50 }),
        templatesAPI.getAll({ limit: 50 }),
        scrapedPostsAPI.getAll({ limit: 50, important: true })
      ]);
      
      setBrands(brandsRes.brands || []);
      setCompetitors(competitorsRes.competitors || []);
      setTemplates(templatesRes.templates || []);
      setScrapedPosts(scrapedPostsRes.posts || []);
    } catch (error) {
      console.error('Failed to load assets:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDragStart = (e, asset, type) => {
    e.dataTransfer.setData('application/json', JSON.stringify({
      type,
      asset
    }));
    e.dataTransfer.effectAllowed = 'copy';
  };

  const tabs = [
    { id: 'brands', label: 'Brands', icon: Building2, count: brands.length },
    { id: 'competitors', label: 'Competitors', icon: Users, count: competitors.length },
    { id: 'templates', label: 'Templates', icon: FileText, count: templates.length },
    { id: 'scraped-posts', label: 'Posts', icon: MessageSquare, count: scrapedPosts.length }
  ];

  const platforms = [
    { value: 'all', label: 'All Platforms' },
    { value: 'instagram', label: 'Instagram' },
    { value: 'linkedin', label: 'LinkedIn' },
    { value: 'youtube', label: 'YouTube' },
    { value: 'reddit', label: 'Reddit' }
  ];

  const getCurrentAssets = () => {
    switch (activeTab) {
      case 'brands': return brands;
      case 'competitors': return competitors;
      case 'templates': return templates;
      case 'scraped-posts': 
        return selectedPlatform === 'all' 
          ? scrapedPosts 
          : scrapedPosts.filter(post => post.platform === selectedPlatform);
      default: return [];
    }
  };

  const getAssetDisplayName = (asset, type) => {
    switch (type) {
      case 'brands':
        return asset.name || 'Unnamed Brand';
      case 'competitors':
        const username = asset.username || asset.name || 'Unknown';
        const competitorPlatform = asset.platform || 'Unknown Platform';
        return `${username} - ${competitorPlatform}`;
      case 'templates':
        return asset.title || asset.name || 'Unnamed Template';
      case 'scraped-posts':
        const text = asset.normalized?.text || 'No text content';
        const postPlatform = asset.platform || 'Unknown';
        const truncatedText = text.length > 30 ? text.substring(0, 30) + '...' : text;
        return `${postPlatform.toUpperCase()}: ${truncatedText}`;
      default:
        return asset.name || asset.title || 'Unnamed Asset';
    }
  };

  if (embedded) {
    return (
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Asset Manager</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-shrink-0 flex items-center justify-center gap-1 px-2 py-2 text-xs font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
              title={tab.label}
            >
              <tab.icon className="w-3 h-3" />
              <span className="hidden sm:inline">{tab.label}</span>
              <span className="text-xs bg-gray-200 text-gray-600 px-1 py-0.5 rounded-full min-w-[18px] text-center">
                {tab.count}
              </span>
            </button>
          ))}
        </div>

        {/* Platform Filter for Scraped Posts */}
        {activeTab === 'scraped-posts' && (
          <div className="px-3 py-2 border-b border-gray-200 bg-gray-50">
            <select
              value={selectedPlatform}
              onChange={(e) => setSelectedPlatform(e.target.value)}
              className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {platforms.map((platform) => (
                <option key={platform.value} value={platform.value}>
                  {platform.label}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="space-y-2">
              {getCurrentAssets().length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-gray-400 mb-2">
                    {activeTab === 'brands' && <Building2 className="w-12 h-12 mx-auto" />}
                    {activeTab === 'competitors' && <Users className="w-12 h-12 mx-auto" />}
                    {activeTab === 'templates' && <FileText className="w-12 h-12 mx-auto" />}
                    {activeTab === 'scraped-posts' && <MessageSquare className="w-12 h-12 mx-auto" />}
                  </div>
                  <p className="text-sm text-gray-500">No {activeTab.replace('-', ' ')} found</p>
                </div>
              ) : (
                getCurrentAssets().map((asset) => (
                  <div
                    key={asset.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, asset, activeTab)}
                    className="flex items-center gap-3 p-3 bg-gray-50 hover:bg-gray-100 rounded-lg cursor-grab active:cursor-grabbing transition-colors border border-transparent hover:border-gray-200"
                  >
                    <GripVertical className="w-4 h-4 text-gray-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {getAssetDisplayName(asset, activeTab)}
                      </p>
                      {activeTab === 'brands' && asset.description && (
                        <p className="text-xs text-gray-500 truncate">{asset.description}</p>
                      )}
                      {activeTab === 'competitors' && asset.brand_name && (
                        <p className="text-xs text-gray-500 truncate">Brand: {asset.brand_name}</p>
                      )}
                      {activeTab === 'templates' && asset.type && (
                        <p className="text-xs text-gray-500 truncate">Type: {asset.type}</p>
                      )}
                      {activeTab === 'scraped-posts' && (
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`text-xs px-2 py-0.5 rounded-full text-white ${
                            asset.platform === 'instagram' ? 'bg-pink-500' :
                            asset.platform === 'linkedin' ? 'bg-blue-600' :
                            asset.platform === 'youtube' ? 'bg-red-500' :
                            asset.platform === 'reddit' ? 'bg-orange-500' :
                            'bg-gray-500'
                          }`}>
                            {asset.platform?.toUpperCase()}
                          </span>
                          {asset.normalized?.engagement?.likes && (
                            <span className="text-xs text-gray-500">
                              ❤️ {asset.normalized.engagement.likes}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <p className="text-xs text-gray-500 text-center">
            Drag any item to the message input to attach its details
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`fixed inset-0 z-50 bg-black bg-opacity-50 transition-opacity duration-300 ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
      <div className={`fixed right-0 top-0 h-full w-96 bg-white shadow-2xl transform transition-transform duration-300 ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Asset Manager</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-shrink-0 flex items-center justify-center gap-1 px-2 py-2 text-xs font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
              title={tab.label}
            >
              <tab.icon className="w-3 h-3" />
              <span className="hidden sm:inline">{tab.label}</span>
              <span className="text-xs bg-gray-200 text-gray-600 px-1 py-0.5 rounded-full min-w-[18px] text-center">
                {tab.count}
              </span>
            </button>
          ))}
        </div>

        {/* Platform Filter for Scraped Posts */}
        {activeTab === 'scraped-posts' && (
          <div className="px-3 py-2 border-b border-gray-200 bg-gray-50">
            <select
              value={selectedPlatform}
              onChange={(e) => setSelectedPlatform(e.target.value)}
              className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {platforms.map((platform) => (
                <option key={platform.value} value={platform.value}>
                  {platform.label}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="space-y-2">
              {getCurrentAssets().length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-gray-400 mb-2">
                    {activeTab === 'brands' && <Building2 className="w-12 h-12 mx-auto" />}
                    {activeTab === 'competitors' && <Users className="w-12 h-12 mx-auto" />}

                    {activeTab === 'templates' && <FileText className="w-12 h-12 mx-auto" />}
                    {activeTab === 'scraped-posts' && <MessageSquare className="w-12 h-12 mx-auto" />}
                  </div>
                  <p className="text-sm text-gray-500">No {activeTab.replace('-', ' ')} found</p>
                </div>
              ) : (
                getCurrentAssets().map((asset) => (
                  <div
                    key={asset.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, asset, activeTab)}
                    className="flex items-center gap-3 p-3 bg-gray-50 hover:bg-gray-100 rounded-lg cursor-grab active:cursor-grabbing transition-colors border border-transparent hover:border-gray-200"
                  >
                    <GripVertical className="w-4 h-4 text-gray-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {getAssetDisplayName(asset, activeTab)}
                      </p>
                      {activeTab === 'brands' && asset.description && (
                        <p className="text-xs text-gray-500 truncate">{asset.description}</p>
                      )}
                      {activeTab === 'competitors' && asset.brand_name && (
                        <p className="text-xs text-gray-500 truncate">Brand: {asset.brand_name}</p>
                      )}
                      {activeTab === 'templates' && asset.type && (
                        <p className="text-xs text-gray-500 truncate">Type: {asset.type}</p>
                      )}
                      {activeTab === 'scraped-posts' && (
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`text-xs px-2 py-0.5 rounded-full text-white ${
                            asset.platform === 'instagram' ? 'bg-pink-500' :
                            asset.platform === 'linkedin' ? 'bg-blue-600' :
                            asset.platform === 'youtube' ? 'bg-red-500' :
                            asset.platform === 'reddit' ? 'bg-orange-500' :
                            'bg-gray-500'
                          }`}>
                            {asset.platform?.toUpperCase()}
                          </span>
                          {asset.normalized?.engagement?.likes && (
                            <span className="text-xs text-gray-500">
                              ❤️ {asset.normalized.engagement.likes}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <p className="text-xs text-gray-500 text-center">
            Drag any item to the message input to attach its details
          </p>
        </div>
      </div>
    </div>
  );
};

export default AssetDragDrop;