'use client';

import { useState, useEffect } from 'react';
import { scrapedPostsAPI, socialMediaUtils } from '@/lib/api/socialMedia';

export default function AnalyticsView({ brands }) {
  const [analytics, setAnalytics] = useState(null);
  const [engagementAnalytics, setEngagementAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedBrand, setSelectedBrand] = useState('');
  const [selectedPlatform, setSelectedPlatform] = useState('');
  const [daysBack, setDaysBack] = useState(30);

  useEffect(() => {
    loadAnalytics();
  }, [selectedBrand, selectedPlatform, daysBack]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = {
        days_back: daysBack,
        ...(selectedBrand && { brand_id: selectedBrand }),
        ...(selectedPlatform && { platform: selectedPlatform }),
      };

      const [analyticsRes, engagementRes] = await Promise.all([
        scrapedPostsAPI.getAnalytics(params),
        scrapedPostsAPI.getEngagementAnalytics(params),
      ]);

      setAnalytics(analyticsRes);
      setEngagementAnalytics(engagementRes);
    } catch (err) {
      console.error('Failed to load analytics:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const platforms = ['instagram', 'linkedin', 'youtube', 'reddit'];

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
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
    );
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Brand</label>
            <select
              value={selectedBrand}
              onChange={(e) => setSelectedBrand(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Brands</option>
              {brands.map((brand) => (
                <option key={brand.id} value={brand.id}>
                  {brand.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Platform</label>
            <select
              value={selectedPlatform}
              onChange={(e) => setSelectedPlatform(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Platforms</option>
              {platforms.map((platform) => (
                <option key={platform} value={platform}>
                  {socialMediaUtils.formatPlatform(platform)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Time Period</label>
            <select
              value={daysBack}
              onChange={(e) => setDaysBack(parseInt(e.target.value))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
              <option value={365}>Last year</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={loadAnalytics}
              className="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Overview Stats */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">📊</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Posts</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {analytics.total_posts}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">❤️</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Likes</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {socialMediaUtils.formatEngagement(analytics.engagement_stats.total_likes)}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">💬</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Comments</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {socialMediaUtils.formatEngagement(analytics.engagement_stats.total_comments)}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">📈</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Avg Engagement</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {analytics.engagement_stats.avg_engagement_per_post.toFixed(1)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Platform Breakdown */}
      {analytics && analytics.platform_breakdown && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Platform Breakdown</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(analytics.platform_breakdown).map(([platform, count]) => (
              <div key={platform} className="text-center p-4 bg-gray-50 rounded-lg">
                <div className={`w-12 h-12 mx-auto rounded-full flex items-center justify-center text-white text-sm font-medium ${socialMediaUtils.getPlatformColor(platform)}`}>
                  {socialMediaUtils.formatPlatform(platform).charAt(0)}
                </div>
                <p className="mt-2 text-2xl font-bold text-gray-900">{count}</p>
                <p className="text-sm text-gray-500">{socialMediaUtils.formatPlatform(platform)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Engagement Analytics */}
      {engagementAnalytics && engagementAnalytics.platform_engagement && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Engagement by Platform</h3>
          <div className="space-y-4">
            {Object.entries(engagementAnalytics.platform_engagement).map(([platform, stats]) => (
              <div key={platform} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium ${socialMediaUtils.getPlatformColor(platform)}`}>
                      {socialMediaUtils.formatPlatform(platform).charAt(0)}
                    </div>
                    <h4 className="font-medium text-gray-900">{socialMediaUtils.formatPlatform(platform)}</h4>
                  </div>
                  <span className="text-sm text-gray-500">{stats.total_posts} posts</span>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <p className="text-lg font-bold text-gray-900">
                      {socialMediaUtils.formatEngagement(stats.total_likes)}
                    </p>
                    <p className="text-xs text-gray-500">Total Likes</p>
                  </div>
                  <div className="text-center">
                    <p className="text-lg font-bold text-gray-900">
                      {socialMediaUtils.formatEngagement(stats.total_comments)}
                    </p>
                    <p className="text-xs text-gray-500">Total Comments</p>
                  </div>
                  <div className="text-center">
                    <p className="text-lg font-bold text-gray-900">
                      {stats.avg_likes_per_post.toFixed(1)}
                    </p>
                    <p className="text-xs text-gray-500">Avg Likes/Post</p>
                  </div>
                  <div className="text-center">
                    <p className="text-lg font-bold text-gray-900">
                      {stats.avg_engagement_per_post.toFixed(1)}
                    </p>
                    <p className="text-xs text-gray-500">Avg Engagement</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Media Stats */}
      {analytics && analytics.media_stats && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Media Statistics</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-900">
                {analytics.media_stats.total_media_items}
              </p>
              <p className="text-sm text-gray-500">Total Media Items</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-900">
                {analytics.media_stats.posts_with_media}
              </p>
              <p className="text-sm text-gray-500">Posts with Media</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-900">
                {analytics.media_stats.avg_media_per_post.toFixed(1)}
              </p>
              <p className="text-sm text-gray-500">Avg Media per Post</p>
            </div>
          </div>
        </div>
      )}

      {/* Date Range */}
      {analytics && analytics.date_range && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Analysis Period</h3>
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>
              From: {new Date(analytics.date_range.from).toLocaleDateString()}
            </span>
            <span>
              To: {new Date(analytics.date_range.to).toLocaleDateString()}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}