'use client';

import { useState } from 'react';
import { socialMediaUtils } from '@/lib/api/socialMedia';

export default function CompetitorCard({ competitor, brands, onEdit, onDelete, onScrape, onDuplicate }) {
  const [showActions, setShowActions] = useState(false);
  const [showDuplicateForm, setShowDuplicateForm] = useState(false);
  const [duplicateName, setDuplicateName] = useState('');
  const [scraping, setScraping] = useState(false);

  const brand = brands.find(b => b.id === competitor.brand_id);

  const handleScrape = async (e) => {
    e.stopPropagation();
    setScraping(true);
    try {
      await onScrape(competitor.id, 10);
    } finally {
      setScraping(false);
    }
  };

  const handleDuplicate = (e) => {
    e.stopPropagation();
    if (!duplicateName.trim()) {
      alert('Please enter a name for the duplicate');
      return;
    }
    onDuplicate(competitor.id, duplicateName);
    setShowDuplicateForm(false);
    setDuplicateName('');
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
      {/* Competitor Header */}
      <div className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <h3 className="text-lg font-semibold text-gray-900">{competitor.name}</h3>
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-white ${socialMediaUtils.getPlatformColor(competitor.platform)}`}>
                {socialMediaUtils.formatPlatform(competitor.platform)}
              </span>
            </div>
            <p className="text-sm text-gray-500 mt-1">{competitor.handle}</p>
            {brand && (
              <p className="text-xs text-blue-600 mt-1">Brand: {brand.name}</p>
            )}
          </div>
          
          {/* Actions Dropdown */}
          <div className="relative">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowActions(!showActions);
              }}
              className="p-2 text-gray-400 hover:text-gray-600 focus:outline-none"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
              </svg>
            </button>
            
            {showActions && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border border-gray-200">
                <div className="py-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onEdit(competitor);
                      setShowActions(false);
                    }}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    Edit
                  </button>
                  <button
                    onClick={handleScrape}
                    disabled={scraping}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50"
                  >
                    {scraping ? 'Scraping...' : 'Scrape Data'}
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowDuplicateForm(true);
                      setShowActions(false);
                    }}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    Duplicate
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(competitor.id);
                      setShowActions(false);
                    }}
                    className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
                  >
                    Delete
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Profile URL */}
        <div className="mt-4">
          <a
            href={competitor.profile_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            View Profile
          </a>
        </div>

        {/* Metrics */}
        {competitor.metrics && (
          <div className="mt-4 grid grid-cols-2 gap-4">
            {competitor.metrics.followers && (
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-gray-900">
                  {socialMediaUtils.formatEngagement(competitor.metrics.followers)}
                </p>
                <p className="text-xs text-gray-500">Followers</p>
              </div>
            )}
            {competitor.metrics.avg_engagement && (
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-gray-900">
                  {(competitor.metrics.avg_engagement * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500">Avg Engagement</p>
              </div>
            )}
          </div>
        )}

        {/* Scrape Config */}
        {competitor.scrape_config && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-between text-sm">
              <span className="text-blue-800">Auto Scrape:</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                competitor.scrape_config.auto_scrape 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {competitor.scrape_config.auto_scrape ? 'Enabled' : 'Disabled'}
              </span>
            </div>
            {competitor.scrape_config.scrape_frequency && (
              <div className="flex items-center justify-between text-sm mt-1">
                <span className="text-blue-800">Frequency:</span>
                <span className="text-blue-600 capitalize">
                  {competitor.scrape_config.scrape_frequency}
                </span>
              </div>
            )}
            {competitor.scrape_config.scraped_at && (
              <div className="flex items-center justify-between text-sm mt-1">
                <span className="text-blue-800">Last Scraped:</span>
                <span className="text-blue-600">
                  {socialMediaUtils.formatDate(competitor.scrape_config.scraped_at)}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Metadata Tags */}
        {competitor.metadata && competitor.metadata.tags && competitor.metadata.tags.length > 0 && (
          <div className="mt-4">
            <div className="flex flex-wrap gap-1">
              {competitor.metadata.tags.map((tag, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Notes */}
        {competitor.metadata && competitor.metadata.notes && (
          <div className="mt-4 p-3 bg-yellow-50 rounded-lg">
            <p className="text-sm text-yellow-800">{competitor.metadata.notes}</p>
          </div>
        )}

        {/* Created Date */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            Added {socialMediaUtils.formatDate(competitor.created_at)}
          </p>
        </div>
      </div>

      {/* Duplicate Form Modal */}
      {showDuplicateForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Duplicate Competitor</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">New Competitor Name</label>
                  <input
                    type="text"
                    value={duplicateName}
                    onChange={(e) => setDuplicateName(e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter new competitor name"
                  />
                </div>
              </div>
              
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowDuplicateForm(false);
                    setDuplicateName('');
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDuplicate}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md"
                >
                  Duplicate
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}