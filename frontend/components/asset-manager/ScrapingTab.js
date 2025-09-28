'use client';

import { useState, useEffect } from 'react';
import { scrapingAPI, brandsAPI, competitorsAPI, socialMediaUtils } from '@/lib/api/socialMedia';
import ScrapingForm from './ScrapingForm';
import ScrapingHistory from './ScrapingHistory';

export default function ScrapingTab({ onUpdate }) {
  const [brands, setBrands] = useState([]);
  const [competitors, setCompetitors] = useState([]);
  const [supportedPlatforms, setSupportedPlatforms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [view, setView] = useState('scrape'); // 'scrape' or 'history'
  const [scrapingResults, setScrapingResults] = useState([]);
  const [scraping, setScraping] = useState(false);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [brandsRes, competitorsRes, platformsRes] = await Promise.all([
        brandsAPI.getAll({ limit: 100 }),
        competitorsAPI.getAll({ limit: 100 }),
        scrapingAPI.getPlatforms(),
      ]);

      setBrands(brandsRes.brands || []);
      setCompetitors(competitorsRes.competitors || []);
      setSupportedPlatforms(platformsRes.supported_platforms || []);
    } catch (err) {
      console.error('Failed to load initial data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleScrape = async (scrapingData) => {
    try {
      setScraping(true);
      setError(null);
      
      const result = await scrapingAPI.scrape(scrapingData);
      setScrapingResults(prev => [result, ...prev]);
      onUpdate?.();
    } catch (err) {
      console.error('Failed to scrape:', err);
      setError(err.message);
    } finally {
      setScraping(false);
    }
  };

  const handleBatchScrape = async (requests) => {
    try {
      setScraping(true);
      setError(null);
      
      const result = await scrapingAPI.batchScrape(requests);
      setScrapingResults(prev => [result, ...prev]);
      onUpdate?.();
    } catch (err) {
      console.error('Failed to batch scrape:', err);
      setError(err.message);
    } finally {
      setScraping(false);
    }
  };

  const handleCompetitorScrape = async (competitorId, limit = 10) => {
    try {
      setScraping(true);
      setError(null);
      
      const result = await scrapingAPI.scrapeCompetitor(competitorId, limit);
      setScrapingResults(prev => [result, ...prev]);
      onUpdate?.();
    } catch (err) {
      console.error('Failed to scrape competitor:', err);
      setError(err.message);
    } finally {
      setScraping(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Scraping</h2>
          <p className="mt-1 text-sm text-gray-500">
            Scrape content from social media platforms and manage your scraping history
          </p>
        </div>
        <div className="mt-4 sm:mt-0 flex space-x-2">
          <button
            onClick={() => setView('scrape')}
            className={`px-4 py-2 text-sm font-medium rounded-md ${
              view === 'scrape'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Scrape Content
          </button>
          <button
            onClick={() => setView('history')}
            className={`px-4 py-2 text-sm font-medium rounded-md ${
              view === 'history'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            History
          </button>
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

      {/* Scraping Results */}
      {scrapingResults.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Scraping Results</h3>
          <div className="space-y-3">
            {scrapingResults.slice(0, 5).map((result, index) => (
              <div key={index} className={`p-3 rounded-lg border ${
                result.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-white ${
                      result.success ? 'bg-green-500' : 'bg-red-500'
                    }`}>
                      {result.success ? 'Success' : 'Failed'}
                    </span>
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-white ${socialMediaUtils.getPlatformColor(result.platform)}`}>
                      {socialMediaUtils.formatPlatform(result.platform)}
                    </span>
                    <span className="text-sm text-gray-600">{result.identifier}</span>
                  </div>
                  <div className="text-sm text-gray-500">
                    {result.count || 0} posts
                  </div>
                </div>
                {result.error && (
                  <p className="mt-2 text-sm text-red-600">{result.error}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Scraping Form */}
      {view === 'scrape' && (
        <ScrapingForm
          brands={brands}
          competitors={competitors}
          supportedPlatforms={supportedPlatforms}
          onScrape={handleScrape}
          onBatchScrape={handleBatchScrape}
          onCompetitorScrape={handleCompetitorScrape}
          scraping={scraping}
        />
      )}

      {/* Scraping History */}
      {view === 'history' && (
        <ScrapingHistory />
      )}
    </div>
  );
}