'use client';

import { useState } from 'react';
import { socialMediaUtils } from '@/lib/api/socialMedia';

export default function ScrapingForm({ 
  brands, 
  competitors, 
  supportedPlatforms, 
  onScrape, 
  onBatchScrape, 
  onCompetitorScrape, 
  scraping 
}) {
  const [scrapeType, setScrapeType] = useState('single'); // 'single', 'batch', 'competitor'
  const [formData, setFormData] = useState({
    platform: 'instagram',
    identifier: '',
    brand_id: '',
    limit: 10,
    days_back: 7,
    save_to_db: true,
  });
  const [batchRequests, setBatchRequests] = useState([
    { platform: 'instagram', identifier: '', limit: 5 }
  ]);
  const [selectedCompetitor, setSelectedCompetitor] = useState('');
  const [competitorLimit, setCompetitorLimit] = useState(10);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleBatchRequestChange = (index, field, value) => {
    setBatchRequests(prev => prev.map((request, i) => 
      i === index ? { ...request, [field]: value } : request
    ));
  };

  const handleAddBatchRequest = () => {
    setBatchRequests(prev => [...prev, { platform: 'instagram', identifier: '', limit: 5 }]);
  };

  const handleRemoveBatchRequest = (index) => {
    setBatchRequests(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (scrapeType === 'single') {
      await onScrape(formData);
    } else if (scrapeType === 'batch') {
      await onBatchScrape(batchRequests);
    } else if (scrapeType === 'competitor') {
      await onCompetitorScrape(selectedCompetitor, competitorLimit);
    }
  };

  const getPlatformPlaceholder = (platform) => {
    switch (platform) {
      case 'instagram':
        return 'username (without @)';
      case 'linkedin':
        return 'profile URL';
      case 'youtube':
        return 'channel username';
      case 'reddit':
        return 'subreddit name (without r/)';
      default:
        return 'identifier';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-6">Scraping Configuration</h3>

      {/* Scrape Type Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-3">Scraping Type</label>
        <div className="flex space-x-4">
          <label className="flex items-center">
            <input
              type="radio"
              value="single"
              checked={scrapeType === 'single'}
              onChange={(e) => setScrapeType(e.target.value)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
            />
            <span className="ml-2 text-sm text-gray-700">Single Platform</span>
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              value="batch"
              checked={scrapeType === 'batch'}
              onChange={(e) => setScrapeType(e.target.value)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
            />
            <span className="ml-2 text-sm text-gray-700">Batch Scraping</span>
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              value="competitor"
              checked={scrapeType === 'competitor'}
              onChange={(e) => setScrapeType(e.target.value)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
            />
            <span className="ml-2 text-sm text-gray-700">Competitor Scraping</span>
          </label>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Single Platform Scraping */}
        {scrapeType === 'single' && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Platform *</label>
                <select
                  required
                  value={formData.platform}
                  onChange={(e) => handleInputChange('platform', e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  {supportedPlatforms.map((platform) => (
                    <option key={platform} value={platform}>
                      {socialMediaUtils.formatPlatform(platform)}
                    </option>
                  ))}
                </select>
              </div>

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
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Identifier *</label>
              <input
                type="text"
                required
                value={formData.identifier}
                onChange={(e) => handleInputChange('identifier', e.target.value)}
                placeholder={getPlatformPlaceholder(formData.platform)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Limit</label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={formData.limit}
                  onChange={(e) => handleInputChange('limit', parseInt(e.target.value))}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Days Back</label>
                <input
                  type="number"
                  min="1"
                  max="365"
                  value={formData.days_back}
                  onChange={(e) => handleInputChange('days_back', parseInt(e.target.value))}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div className="flex items-center">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.save_to_db}
                    onChange={(e) => handleInputChange('save_to_db', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700">Save to Database</span>
                </label>
              </div>
            </div>
          </div>
        )}

        {/* Batch Scraping */}
        {scrapeType === 'batch' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-md font-medium text-gray-900">Batch Requests</h4>
              <button
                type="button"
                onClick={handleAddBatchRequest}
                className="px-3 py-1 text-sm font-medium text-blue-600 hover:text-blue-800"
              >
                Add Request
              </button>
            </div>

            {batchRequests.map((request, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h5 className="text-sm font-medium text-gray-700">Request {index + 1}</h5>
                  {batchRequests.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveBatchRequest(index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Platform</label>
                    <select
                      value={request.platform}
                      onChange={(e) => handleBatchRequestChange(index, 'platform', e.target.value)}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    >
                      {supportedPlatforms.map((platform) => (
                        <option key={platform} value={platform}>
                          {socialMediaUtils.formatPlatform(platform)}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Identifier</label>
                    <input
                      type="text"
                      value={request.identifier}
                      onChange={(e) => handleBatchRequestChange(index, 'identifier', e.target.value)}
                      placeholder={getPlatformPlaceholder(request.platform)}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Limit</label>
                    <input
                      type="number"
                      min="1"
                      max="50"
                      value={request.limit}
                      onChange={(e) => handleBatchRequestChange(index, 'limit', parseInt(e.target.value))}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Competitor Scraping */}
        {scrapeType === 'competitor' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Competitor *</label>
              <select
                required
                value={selectedCompetitor}
                onChange={(e) => setSelectedCompetitor(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Select a competitor</option>
                {competitors.map((competitor) => (
                  <option key={competitor.id} value={competitor.id}>
                    {competitor.name} ({socialMediaUtils.formatPlatform(competitor.platform)})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Posts Limit</label>
              <input
                type="number"
                min="1"
                max="50"
                value={competitorLimit}
                onChange={(e) => setCompetitorLimit(parseInt(e.target.value))}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={scraping}
            className="px-6 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {scraping ? 'Scraping...' : 'Start Scraping'}
          </button>
        </div>
      </form>
    </div>
  );
}