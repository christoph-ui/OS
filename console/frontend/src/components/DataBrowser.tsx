'use client';

import { useState, useEffect } from 'react';
import { Search, FileText, Filter, ChevronLeft, ChevronRight } from 'lucide-react';

interface Document {
  id: string;
  filename: string;
  category: string;
  mcp: string | null;
  ingested_at: string;
  size_bytes: number;
  snippet: string | null;
}

interface Category {
  name: string;
  count: number;
}

export default function DataBrowser() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [minioFiles, setMinioFiles] = useState<any>(null);
  const [ingestionStatus, setIngestionStatus] = useState<string>('');
  const [isIngesting, setIsIngesting] = useState(false);

  const pageSize = 20;

  useEffect(() => {
    loadCategories();
    loadDocuments();
    loadMinioFiles();
  }, [page, selectedCategory]);

  const loadMinioFiles = async () => {
    try {
      const response = await fetch('http://localhost:4080/api/minio/browse/customer-eaton');
      const data = await response.json();
      if (data.success) {
        setMinioFiles(data);
      }
    } catch (error) {
      console.error('Error loading MinIO files:', error);
    }
  };

  const startIngestion = async () => {
    setIsIngesting(true);
    setIngestionStatus('Starting ingestion...');

    try {
      const response = await fetch('http://localhost:4080/api/ingestion/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_id: 'eaton',
          minio_bucket: 'customer-eaton',
          target_mcp: 'general'
        })
      });

      const result = await response.json();

      if (result.success) {
        setIngestionStatus('✓ Ingestion started! Processing files...');

        // Poll for status
        const pollInterval = setInterval(async () => {
          const statusRes = await fetch('http://localhost:4080/api/ingestion/status/eaton');
          const status = await statusRes.json();

          if (status.status === 'in_progress') {
            setIngestionStatus(`Processing: ${status.progress || 0}% - ${status.message || ''}`);
          } else if (status.status === 'complete') {
            setIngestionStatus('✓ Ingestion complete! Reloading documents...');
            clearInterval(pollInterval);
            setIsIngesting(false);
            loadDocuments();
          } else if (status.status === 'failed') {
            setIngestionStatus(`❌ Ingestion failed: ${status.error}`);
            clearInterval(pollInterval);
            setIsIngesting(false);
          }
        }, 2000);

        // Stop polling after 5 minutes
        setTimeout(() => clearInterval(pollInterval), 300000);
      }
    } catch (error) {
      console.error('Error starting ingestion:', error);
      setIngestionStatus(`❌ Error: ${error}`);
      setIsIngesting(false);
    }
  };

  const loadCategories = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4010';
      const response = await fetch(`${apiUrl}/api/data/categories`);
      const data = await response.json();
      setCategories(data.categories || []);
    } catch (error) {
      console.error('Error loading categories:', error);
      setCategories([]); // Set empty array on error
    }
  };

  const loadDocuments = async () => {
    setIsLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4010';
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });
      if (selectedCategory) {
        params.append('category', selectedCategory);
      }

      const response = await fetch(`${apiUrl}/api/data/browse?${params}`);
      const data = await response.json();
      setDocuments(data.documents || []);
      setTotal(data.total || 0);
    } catch (error) {
      console.error('Error loading documents:', error);
      setDocuments([]);
      setTotal(0);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsLoading(true);
    try {
      const response = await fetch('/api/data/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: searchQuery,
          category: selectedCategory,
          limit: pageSize,
        }),
      });
      const data = await response.json();
      // Map search results to document format
      setDocuments(
        data.results.map((r: any) => ({
          id: r.id,
          filename: r.filename,
          category: r.category,
          mcp: null,
          ingested_at: '',
          size_bytes: 0,
          snippet: r.snippet,
        }))
      );
      setTotal(data.total);
    } catch (error) {
      console.error('Error searching:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">Data Browser</h2>
            <p className="text-sm text-gray-500">Browse and search lakehouse documents</p>
          </div>

          {/* MinIO Files Card */}
          {minioFiles && (
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <div className="text-sm font-medium text-gray-700">MinIO Storage</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {minioFiles.file_count} files ({minioFiles.total_size_mb} MB)
                  </div>
                  {ingestionStatus && (
                    <div className="text-xs mt-2 text-blue-700 font-medium">
                      {ingestionStatus}
                    </div>
                  )}
                </div>
                <button
                  onClick={startIngestion}
                  disabled={isIngesting}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                >
                  {isIngesting ? '⟳ Ingesting...' : '▶ Start Ingestion'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Search and Filters */}
      <div className="px-6 py-4 border-b border-gray-200 space-y-4">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Semantic search..."
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={handleSearch}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Search
          </button>
        </div>

        <div className="flex gap-2 items-center">
          <Filter className="w-4 h-4 text-gray-400" />
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => {
                setSelectedCategory(null);
                setPage(1);
              }}
              className={`px-3 py-1 rounded-full text-sm ${
                !selectedCategory
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              All
            </button>
            {categories.map((cat) => (
              <button
                key={cat.name}
                onClick={() => {
                  setSelectedCategory(cat.name);
                  setPage(1);
                }}
                className={`px-3 py-1 rounded-full text-sm ${
                  selectedCategory === cat.name
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {cat.name} ({cat.count})
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Document List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center text-gray-400 py-12">
            <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No documents found</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Filename
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  MCP
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Size
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ingested
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="text-sm font-medium text-gray-800">
                          {doc.filename}
                        </p>
                        {doc.snippet && (
                          <p className="text-xs text-gray-500 truncate max-w-md">
                            {doc.snippet}
                          </p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-600">
                      {doc.category}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {doc.mcp || '-'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {formatBytes(doc.size_bytes)}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {doc.ingested_at ? new Date(doc.ingested_at).toLocaleDateString() : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="border-t border-gray-200 px-6 py-4 flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Showing {(page - 1) * pageSize + 1} to{' '}
            {Math.min(page * pageSize, total)} of {total} documents
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
