'use client';

import { useState, useEffect } from 'react';
import {
  Upload,
  FolderOpen,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
} from 'lucide-react';

interface IngestJob {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  files_processed: number;
  files_total: number;
  errors: string[];
}

const MCP_OPTIONS = [
  { value: '', label: 'Auto-detect' },
  { value: 'ctax', label: 'CTAX - German Tax' },
  { value: 'law', label: 'LAW - Legal Documents' },
  { value: 'tender', label: 'TENDER - RFP Processing' },
];

export default function IngestPanel() {
  const [path, setPath] = useState('');
  const [mcp, setMCP] = useState('');
  const [recursive, setRecursive] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [jobs, setJobs] = useState<IngestJob[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadJobs();
    const interval = setInterval(loadJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadJobs = async () => {
    try {
      const response = await fetch('/api/ingest/jobs');
      const data = await response.json();
      setJobs(data.jobs);
    } catch (error) {
      console.error('Error loading jobs:', error);
    }
  };

  const startIngestion = async () => {
    if (!path.trim()) {
      setError('Please enter a path');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch('/api/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          path: path.trim(),
          mcp: mcp || null,
          recursive,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to start ingestion');
      }

      setPath('');
      await loadJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'running':
        return <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4">
        <h2 className="text-lg font-semibold text-gray-800">Data Ingestion</h2>
        <p className="text-sm text-gray-500">Ingest documents into the lakehouse</p>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Ingestion Form */}
        <section className="border border-gray-200 rounded-lg p-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <Upload className="w-5 h-5" />
            New Ingestion
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Source Path
              </label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <FolderOpen className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    value={path}
                    onChange={(e) => setPath(e.target.value)}
                    placeholder="/data/Buchhaltung"
                    className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Enter the path to a folder containing documents
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Target MCP
                </label>
                <select
                  value={mcp}
                  onChange={(e) => setMCP(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  {MCP_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Options
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={recursive}
                    onChange={(e) => setRecursive(e.target.checked)}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-600">
                    Recursive (include subfolders)
                  </span>
                </label>
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <button
              onClick={startIngestion}
              disabled={isSubmitting || !path.trim()}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <RefreshCw className="w-5 h-5 animate-spin" />
              ) : (
                <Play className="w-5 h-5" />
              )}
              Start Ingestion
            </button>
          </div>
        </section>

        {/* Jobs List */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-700">
              Ingestion Jobs
            </h3>
            <button
              onClick={loadJobs}
              className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>

          {jobs.length === 0 ? (
            <div className="text-center text-gray-400 py-8 border border-dashed border-gray-200 rounded-lg">
              <Upload className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No ingestion jobs yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {jobs.map((job) => (
                <div
                  key={job.job_id}
                  className="border border-gray-200 rounded-lg p-4"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      {getStatusIcon(job.status)}
                      <div>
                        <p className="font-medium text-gray-800">
                          Job {job.job_id}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <span
                            className={`px-2 py-0.5 rounded text-xs ${getStatusColor(
                              job.status
                            )}`}
                          >
                            {job.status}
                          </span>
                          {job.files_total > 0 && (
                            <span className="text-xs text-gray-500">
                              {job.files_processed} / {job.files_total} files
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {job.status === 'running' && job.files_total > 0 && (
                      <div className="w-24">
                        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary-600 transition-all"
                            style={{
                              width: `${
                                (job.files_processed / job.files_total) * 100
                              }%`,
                            }}
                          />
                        </div>
                      </div>
                    )}
                  </div>

                  {job.errors.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <p className="text-xs font-medium text-red-600 mb-1">
                        Errors:
                      </p>
                      <ul className="text-xs text-red-500 list-disc list-inside">
                        {job.errors.slice(0, 3).map((err, i) => (
                          <li key={i}>{err}</li>
                        ))}
                        {job.errors.length > 3 && (
                          <li>...and {job.errors.length - 3} more</li>
                        )}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Info */}
        <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
          <p className="font-medium mb-2">Supported File Types</p>
          <p className="text-gray-500">
            PDF, DOCX, XLSX, TXT, CSV, JSON, XML, and more. Documents are
            automatically classified and processed by the appropriate MCP.
          </p>
        </div>
      </div>
    </div>
  );
}
