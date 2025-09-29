'use client';

import { useState, useEffect } from 'react';
import { scrapedPostsAPI, brandsAPI, socialMediaUtils } from '@/lib/api/socialMedia';
import ScrapedPostCard from './ScrapedPostCard';
import AnalyticsView from './AnalyticsView';

export default function ScrapedPostsTab({ onUpdate }) {
  const [posts, setPosts] = useState([]);
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [view, setView] = useState('posts'); // 'posts' or 'analytics'
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBrand, setSelectedBrand] = useState('');
  const [selectedPlatform, setSelectedPlatform] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [selectedPosts, setSelectedPosts] = useState([]);
  const [showBulkActions, setShowBulkActions] = useState(false);

  const limit = 12;

  useEffect(() => {
    loadBrands();
  }, []);

  useEffect(() => {
    if (view === 'posts') {
      loadPosts();
    }
  }, [currentPage, searchTerm, selectedBrand, selectedPlatform, selectedStatus, dateFrom, dateTo, view]);

  const loadBrands = async () => {
    try {
      const response = await brandsAPI.getAll({ limit: 100 });
      setBrands(response.brands || []);
    } catch (err) {
      console.error('Failed to load brands:', err);
    }
  };

  const loadPosts = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = {
        page: currentPage,
        limit,
        ...(searchTerm && { search: searchTerm }),
        ...(selectedBrand && { brand_id: selectedBrand }),
        ...(selectedPlatform && { platform: selectedPlatform }),
        ...(selectedStatus && { status: selectedStatus }),
        ...(dateFrom && { date_from: dateFrom }),
        ...(dateTo && { date_to: dateTo }),
      };

      const response = await scrapedPostsAPI.getAll(params);
      setPosts(response.posts || []);
      setTotal(response.total || 0);
      setTotalPages(Math.ceil((response.total || 0) / limit));
    } catch (err) {
      console.error('Failed to load posts:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (postId) => {
    if (!confirm('Are you sure you want to delete this post?')) {
      return;
    }

    try {
      await scrapedPostsAPI.delete(postId);
      loadPosts();
      onUpdate?.();
    } catch (err) {
      console.error('Failed to delete post:', err);
      setError(err.message);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedPosts.length === 0) {
      alert('Please select posts to delete');
      return;
    }

    if (!confirm(`Are you sure you want to delete ${selectedPosts.length} posts?`)) {
      return;
    }

    try {
      await scrapedPostsAPI.bulkDelete(selectedPosts);
      setSelectedPosts([]);
      setShowBulkActions(false);
      loadPosts();
      onUpdate?.();
    } catch (err) {
      console.error('Failed to delete posts:', err);
      setError(err.message);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setCurrentPage(1);
    loadPosts();
  };

  const handleFilterChange = () => {
    setCurrentPage(1);
    loadPosts();
  };

  const handlePostSelect = (postId, selected) => {
    if (selected) {
      setSelectedPosts([...selectedPosts, postId]);
    } else {
      setSelectedPosts(selectedPosts.filter(id => id !== postId));
    }
  };

  const handleToggleImportant = async (postId, important) => {
    try {
      await scrapedPostsAPI.toggleImportant(postId, important);
      // Update the post in the local state
      setPosts(posts.map(post => 
        post.id === postId ? { ...post, important } : post
      ));
    } catch (err) {
      console.error('Failed to toggle important status:', err);
      setError(err.message);
    }
  };

  const handleSelectAll = () => {
    if (selectedPosts.length === posts.length) {
      setSelectedPosts([]);
    } else {
      setSelectedPosts(posts.map(post => post.id));
    }
  };

  const platforms = ['instagram', 'linkedin', 'youtube', 'reddit'];
  const statuses = ['normalized', 'processing', 'error'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Scraped Posts</h2>
          <p className="mt-1 text-sm text-gray-500">
            View and analyze scraped content from your competitors
          </p>
        </div>
        <div className="mt-4 sm:mt-0 flex space-x-2">
          <button
            onClick={() => setView('analytics')}
            className={`px-4 py-2 text-sm font-medium rounded-md ${
              view === 'analytics'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Analytics
          </button>
          <button
            onClick={() => setView('posts')}
            className={`px-4 py-2 text-sm font-medium rounded-md ${
              view === 'posts'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Posts
          </button>
        </div>
      </div>

      {view === 'analytics' ? (
        <AnalyticsView brands={brands} />
      ) : (
        <>
          {/* Filters and Search */}
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <form onSubmit={handleSearch} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
                {/* Search */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
                  <input
                    type="text"
                    placeholder="Search posts..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                {/* Brand Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Brand</label>
                  <select
                    value={selectedBrand}
                    onChange={(e) => {
                      setSelectedBrand(e.target.value);
                      handleFilterChange();
                    }}
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

                {/* Platform Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Platform</label>
                  <select
                    value={selectedPlatform}
                    onChange={(e) => {
                      setSelectedPlatform(e.target.value);
                      handleFilterChange();
                    }}
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

                {/* Status Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                  <select
                    value={selectedStatus}
                    onChange={(e) => {
                      setSelectedStatus(e.target.value);
                      handleFilterChange();
                    }}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">All Statuses</option>
                    {statuses.map((status) => (
                      <option key={status} value={status}>
                        {status.charAt(0).toUpperCase() + status.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Date From */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">From Date</label>
                  <input
                    type="date"
                    value={dateFrom}
                    onChange={(e) => {
                      setDateFrom(e.target.value);
                      handleFilterChange();
                    }}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                {/* Date To */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">To Date</label>
                  <input
                    type="date"
                    value={dateTo}
                    onChange={(e) => {
                      setDateTo(e.target.value);
                      handleFilterChange();
                    }}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            </form>
          </div>

          {/* Bulk Actions */}
          {selectedPosts.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <span className="text-sm text-blue-800">
                    {selectedPosts.length} post{selectedPosts.length !== 1 ? 's' : ''} selected
                  </span>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={handleBulkDelete}
                    className="px-3 py-1 text-sm font-medium text-red-600 hover:text-red-800"
                  >
                    Delete Selected
                  </button>
                  <button
                    onClick={() => {
                      setSelectedPosts([]);
                      setShowBulkActions(false);
                    }}
                    className="px-3 py-1 text-sm font-medium text-blue-600 hover:text-blue-800"
                  >
                    Clear Selection
                  </button>
                </div>
              </div>
            </div>
          )}

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

          {/* Loading State */}
          {loading && (
            <div className="flex justify-center items-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          )}

          {/* Posts Grid */}
          {!loading && (
            <>
              {posts.length === 0 ? (
                <div className="text-center py-12">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No posts found</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Try adjusting your filters or start scraping some content.
                  </p>
                </div>
              ) : (
                <>
                  {/* Select All */}
                  <div className="flex items-center justify-between mb-4">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={selectedPosts.length === posts.length && posts.length > 0}
                        onChange={handleSelectAll}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-sm text-gray-700">Select All</span>
                    </label>
                    <span className="text-sm text-gray-500">
                      {total} total posts
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {posts.map((post) => (
                      <ScrapedPostCard
                        key={post.id}
                        post={post}
                        brands={brands}
                        selected={selectedPosts.includes(post.id)}
                        onSelect={handlePostSelect}
                        onDelete={handleDelete}
                        onToggleImportant={handleToggleImportant}
                      />
                    ))}
                  </div>

                  {/* Pagination */}
                  {totalPages > 1 && (
                    <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6 mt-6">
                      <div className="flex flex-1 justify-between sm:hidden">
                        <button
                          onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                          disabled={currentPage === 1}
                          className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Previous
                        </button>
                        <button
                          onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                          disabled={currentPage === totalPages}
                          className="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Next
                        </button>
                      </div>
                      <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                        <div>
                          <p className="text-sm text-gray-700">
                            Showing <span className="font-medium">{(currentPage - 1) * limit + 1}</span> to{' '}
                            <span className="font-medium">
                              {Math.min(currentPage * limit, total)}
                            </span>{' '}
                            of <span className="font-medium">{total}</span> results
                          </p>
                        </div>
                        <div>
                          <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
                            <button
                              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                              disabled={currentPage === 1}
                              className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              <span className="sr-only">Previous</span>
                              <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                <path fillRule="evenodd" d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z" clipRule="evenodd" />
                              </svg>
                            </button>
                            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                              <button
                                key={page}
                                onClick={() => setCurrentPage(page)}
                                className={`relative inline-flex items-center px-4 py-2 text-sm font-semibold ${
                                  page === currentPage
                                    ? 'z-10 bg-blue-600 text-white focus:z-20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600'
                                    : 'text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0'
                                }`}
                              >
                                {page}
                              </button>
                            ))}
                            <button
                              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                              disabled={currentPage === totalPages}
                              className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              <span className="sr-only">Next</span>
                              <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
                              </svg>
                            </button>
                          </nav>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}