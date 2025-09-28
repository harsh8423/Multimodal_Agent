'use client';

import { useState, useEffect } from 'react';
import { brandsAPI, templatesAPI, competitorsAPI, scrapedPostsAPI, scrapingAPI, socialMediaUtils } from '@/lib/api/socialMedia';

// Tab components
import BrandsTab from '@/components/asset-manager/BrandsTab';
import TemplatesTab from '@/components/asset-manager/TemplatesTab';
import CompetitorsTab from '@/components/asset-manager/CompetitorsTab';
import ScrapedPostsTab from '@/components/asset-manager/ScrapedPostsTab';
import ScrapingTab from '@/components/asset-manager/ScrapingTab';

const tabs = [
  { id: 'brands', name: 'Brands', icon: '🏢' },
  { id: 'templates', name: 'Templates', icon: '📝' },
  { id: 'competitors', name: 'Competitors', icon: '👥' },
  { id: 'scraped-posts', name: 'Scraped Posts', icon: '📊' },
  { id: 'scraping', name: 'Scraping', icon: '🔍' },
];

export default function AssetManagerPage() {
  const [activeTab, setActiveTab] = useState('brands');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    brands: 0,
    templates: 0,
    competitors: 0,
    scrapedPosts: 0,
  });

  // Load initial stats
  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const [brandsRes, templatesRes, competitorsRes, scrapedPostsRes] = await Promise.all([
        brandsAPI.getAll({ limit: 1 }),
        templatesAPI.getAll({ limit: 1 }),
        competitorsAPI.getAll({ limit: 1 }),
        scrapedPostsAPI.getAll({ limit: 1 }),
      ]);

      setStats({
        brands: brandsRes.total || 0,
        templates: templatesRes.total || 0,
        competitors: competitorsRes.total || 0,
        scrapedPosts: scrapedPostsRes.total || 0,
      });
    } catch (err) {
      console.error('Failed to load stats:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'brands':
        return <BrandsTab onUpdate={loadStats} />;
      case 'templates':
        return <TemplatesTab onUpdate={loadStats} />;
      case 'competitors':
        return <CompetitorsTab onUpdate={loadStats} />;
      case 'scraped-posts':
        return <ScrapedPostsTab onUpdate={loadStats} />;
      case 'scraping':
        return <ScrapingTab onUpdate={loadStats} />;
      default:
        return <BrandsTab onUpdate={loadStats} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <h1 className="text-3xl font-bold text-gray-900">Asset Manager</h1>
            <p className="mt-2 text-gray-600">
              Manage your social media brands, templates, competitors, and scraped content
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">🏢</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Brands</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {loading ? '...' : stats.brands}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">📝</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Templates</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {loading ? '...' : stats.templates}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">👥</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Competitors</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {loading ? '...' : stats.competitors}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">📊</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Scraped Posts</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {loading ? '...' : stats.scrapedPosts}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
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

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow">
          {/* Tab Navigation */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6" aria-label="Tabs">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {renderTabContent()}
          </div>
        </div>
      </div>
    </div>
  );
}