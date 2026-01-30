'use client';

import { useState, useEffect } from 'react';
import { Upload, FolderOpen, Play, CheckCircle, XCircle, Clock, RefreshCw, Database, File } from 'lucide-react';
import { colors, fonts } from './mcps/theme';
import { useProgress } from '@/hooks/useProgress';
import { useCustomer } from '@/context/CustomerContext';

interface IngestJob {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  files_processed: number;
  files_total: number;
  errors: string[];
  current_file?: string;
  current_phase?: string;
}

interface MinIOFile {
  name: string;
  size: number;
  last_modified: string;
}

export default function IngestWorkspace() {
  const { customerId } = useCustomer();
  const { progress, connected, overallProgress } = useProgress(customerId);

  const [sourceType, setSourceType] = useState<'minio' | 'upload' | 'path'>('minio');
  const [path, setPath] = useState('');
  const [selectedMcp, setSelectedMcp] = useState('');
  const [recursive, setRecursive] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [jobs, setJobs] = useState<IngestJob[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [minioFiles, setMinioFiles] = useState<MinIOFile[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadJobs();
    if (sourceType === 'minio') {
      loadMinioFiles();
    }
    const interval = setInterval(loadJobs, 5000);
    return () => clearInterval(interval);
  }, [sourceType]);

  const loadJobs = async () => {
    try {
      const response = await fetch('http://localhost:4010/api/ingest/jobs', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('0711_token')}` }
      });
      const data = await response.json();
      setJobs(data.jobs || []);
    } catch (error) {
      console.error('Error loading jobs:', error);
    }
  };

  const loadMinioFiles = async () => {
    try {
      // Get customer_id from JWT token
      const token = localStorage.getItem('0711_token');
      let customerId = 'eaton'; // fallback
      if (token) {
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          customerId = payload.customer_id || 'eaton';
        } catch (e) {
          console.error('Failed to decode token:', e);
        }
      }

      const response = await fetch(`http://localhost:4080/api/minio/browse/customer-${customerId}`);
      const data = await response.json();
      if (data.success && data.files) {
        setMinioFiles(data.files);
      }
    } catch (error) {
      console.error('Error loading MinIO files:', error);
    }
  };

  const startIngestion = async () => {
    if (sourceType === 'minio' && selectedFiles.size === 0) {
      setError('Bitte wählen Sie mindestens eine Datei aus');
      return;
    }

    if (sourceType === 'path' && !path.trim()) {
      setError('Bitte geben Sie einen Pfad ein');
      return;
    }

    if (sourceType === 'upload' && uploadFiles.length === 0) {
      setError('Bitte wählen Sie mindestens eine Datei zum Upload aus');
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setShowProgressModal(true);

    try {
      const token = localStorage.getItem('0711_token');
      let currentCustomerId = customerId || 'default';

      if (token && !customerId) {
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          currentCustomerId = payload.customer_id || 'default';
        } catch (e) {
          console.error('Failed to decode token:', e);
        }
      }

      const selectedMcpsParam = selectedMcp || 'general';

      // Handle upload source type
      if (sourceType === 'upload') {
        setUploading(true);

        // Upload files to MinIO first
        const formData = new FormData();
        uploadFiles.forEach(file => formData.append('files', file));

        const uploadResponse = await fetch(
          `http://localhost:4080/api/upload/files?customer_id=${currentCustomerId}&selected_mcps=${selectedMcpsParam}`,
          {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
          }
        );

        if (!uploadResponse.ok) {
          const data = await uploadResponse.json();
          throw new Error(data.detail || 'Upload failed');
        }

        const uploadData = await uploadResponse.json();
        console.log('Upload successful:', uploadData);

        // Ingestion is automatically triggered by upload endpoint
        setUploadFiles([]);
        setUploading(false);

      } else {
        // MinIO or path ingestion
        const response = await fetch(
          `http://localhost:4080/api/upload/trigger-ingestion?customer_id=${currentCustomerId}&selected_mcps=${selectedMcpsParam}`,
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              bucket_name: `customer-${currentCustomerId}`,
              selected_files: Array.from(selectedFiles)
            })
          }
        );

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || 'Failed to start ingestion');
        }

        setPath('');
        setSelectedFiles(new Set());
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setShowProgressModal(false);
      setUploading(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5" style={{ color: colors.dark }} />;
      case 'failed':
        return <XCircle className="w-5 h-5" style={{ color: '#dc2626' }} />;
      case 'running':
        return <RefreshCw className="w-5 h-5 animate-spin" style={{ color: colors.orange }} />;
      default:
        return <Clock className="w-5 h-5" style={{ color: colors.midGray }} />;
    }
  };

  return (
    <div style={{ backgroundColor: colors.light, padding: '40px', minHeight: '100vh' }}>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center border" style={{ backgroundColor: colors.dark, borderColor: colors.dark }}>
              <Upload className="w-5 h-5" style={{ color: colors.light }} />
            </div>
            <h1 className="text-3xl font-semibold" style={{ color: colors.dark, fontFamily: fonts.heading, margin: 0 }}>
              Data Ingestion
            </h1>
          </div>
          <p style={{ color: colors.midGray, fontFamily: fonts.body, fontSize: '15px' }}>
            Import data into your lakehouse for processing by connected MCPs
          </p>
        </div>

        <div className="grid grid-cols-3 gap-6">
          {/* Left Column: Configuration */}
          <div className="col-span-2 space-y-6">
            {/* Source Selection */}
            <section className="border rounded-lg p-6" style={{ backgroundColor: colors.light, borderColor: colors.lightGray }}>
              <h3 className="font-semibold mb-4 text-sm" style={{ color: colors.dark, fontFamily: fonts.heading }}>
                1. Select Source
              </h3>

              <div className="grid grid-cols-3 gap-3">
                {[
                  { id: 'minio', label: 'MinIO Storage', icon: Database, desc: 'From uploaded files' },
                  { id: 'upload', label: 'Upload Files', icon: Upload, desc: 'Drag & drop' },
                  { id: 'path', label: 'File System', icon: FolderOpen, desc: 'Server path' }
                ].map((source) => (
                  <button
                    key={source.id}
                    onClick={() => setSourceType(source.id as any)}
                    className="p-4 rounded-lg border-2 transition-all text-left"
                    style={{
                      borderColor: sourceType === source.id ? colors.orange : colors.lightGray,
                      backgroundColor: sourceType === source.id ? colors.orange + '08' : colors.light
                    }}
                  >
                    <source.icon className="w-6 h-6 mb-2" style={{ color: sourceType === source.id ? colors.orange : colors.midGray }} />
                    <div className="font-semibold text-sm mb-1" style={{ color: colors.dark, fontFamily: fonts.heading }}>{source.label}</div>
                    <div className="text-xs" style={{ color: colors.midGray, fontFamily: fonts.body }}>{source.desc}</div>
                  </button>
                ))}
              </div>
            </section>

            {/* MinIO File Browser */}
            {sourceType === 'minio' && (
              <section className="border rounded-lg p-6" style={{ backgroundColor: colors.light, borderColor: colors.lightGray }}>
                <h3 className="font-semibold mb-4 text-sm" style={{ color: colors.dark, fontFamily: fonts.heading }}>
                  2. Select Files from MinIO
                </h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {minioFiles.length === 0 ? (
                    <p className="text-center py-8" style={{ color: colors.midGray, fontFamily: fonts.body }}>
                      No files in MinIO bucket
                    </p>
                  ) : (
                    minioFiles.map((file) => (
                      <label key={file.name} className="flex items-center gap-3 p-3 rounded border hover:border-orange/40 cursor-pointer" style={{ borderColor: colors.lightGray }}>
                        <input
                          type="checkbox"
                          checked={selectedFiles.has(file.name)}
                          onChange={(e) => {
                            const newSet = new Set(selectedFiles);
                            e.target.checked ? newSet.add(file.name) : newSet.delete(file.name);
                            setSelectedFiles(newSet);
                          }}
                          className="w-4 h-4"
                        />
                        <File className="w-5 h-5" style={{ color: colors.midGray }} />
                        <div className="flex-1">
                          <div className="font-medium text-sm" style={{ color: colors.dark, fontFamily: fonts.heading }}>{file.name}</div>
                          <div className="text-xs" style={{ color: colors.midGray }}>{(file.size / 1024 / 1024).toFixed(2)} MB</div>
                        </div>
                      </label>
                    ))
                  )}
                </div>
                {minioFiles.length > 0 && (
                  <div className="flex gap-2 mt-3">
                    <button
                      onClick={() => setSelectedFiles(new Set(minioFiles.map(f => f.name)))}
                      className="text-xs px-3 py-1 rounded border"
                      style={{ borderColor: colors.lightGray, color: colors.dark, fontFamily: fonts.heading }}
                    >
                      Select All
                    </button>
                    <button
                      onClick={() => setSelectedFiles(new Set())}
                      className="text-xs px-3 py-1 rounded border"
                      style={{ borderColor: colors.lightGray, color: colors.dark, fontFamily: fonts.heading }}
                    >
                      Clear
                    </button>
                  </div>
                )}
              </section>
            )}

            {/* Path Input (for filesystem source) */}
            {sourceType === 'path' && (
              <section className="border rounded-lg p-6" style={{ backgroundColor: colors.light, borderColor: colors.lightGray }}>
                <h3 className="font-semibold mb-4 text-sm" style={{ color: colors.dark, fontFamily: fonts.heading }}>
                  2. Enter File System Path
                </h3>
                <div className="relative">
                  <FolderOpen className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5" style={{ color: colors.midGray }} />
                  <input
                    type="text"
                    value={path}
                    onChange={(e) => setPath(e.target.value)}
                    placeholder="/data/customer-{id}"
                    className="w-full pl-11 pr-4 py-3 border rounded-lg focus:outline-none"
                    style={{
                      borderColor: colors.lightGray,
                      backgroundColor: colors.light,
                      color: colors.dark,
                      fontFamily: fonts.body
                    }}
                    onFocus={(e) => e.currentTarget.style.borderColor = colors.orange}
                    onBlur={(e) => e.currentTarget.style.borderColor = colors.lightGray}
                  />
                </div>
                <label className="flex items-center gap-2 mt-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={recursive}
                    onChange={(e) => setRecursive(e.target.checked)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm" style={{ color: colors.midGray, fontFamily: fonts.body }}>
                    Include subfolders (recursive)
                  </span>
                </label>
              </section>
            )}

            {/* Upload Files UI */}
            {sourceType === 'upload' && (
              <section className="border rounded-lg p-6" style={{ backgroundColor: colors.light, borderColor: colors.lightGray }}>
                <h3 className="font-semibold mb-4 text-sm" style={{ color: colors.dark, fontFamily: fonts.heading }}>
                  2. Upload Files from your Mac
                </h3>
                <div
                  className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:border-orange/60 transition-colors"
                  style={{ borderColor: colors.lightGray }}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    const files = Array.from(e.dataTransfer.files);
                    setUploadFiles(prev => [...prev, ...files]);
                  }}
                  onClick={() => {
                    const input = document.createElement('input');
                    input.type = 'file';
                    input.multiple = true;
                    input.onchange = (e: any) => {
                      const files = Array.from(e.target.files || []) as File[];
                      setUploadFiles(prev => [...prev, ...files]);
                    };
                    input.click();
                  }}
                >
                  <Upload className="w-12 h-12 mx-auto mb-3" style={{ color: colors.midGray }} />
                  <p className="font-semibold mb-1" style={{ color: colors.dark, fontFamily: fonts.heading }}>
                    Drop files here or click to browse
                  </p>
                  <p className="text-sm" style={{ color: colors.midGray, fontFamily: fonts.body }}>
                    Supports Excel, PDF, CSV, XML, and more
                  </p>
                </div>

                {uploadFiles.length > 0 && (
                  <div className="mt-4 space-y-2">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-semibold" style={{ color: colors.dark, fontFamily: fonts.heading }}>
                        {uploadFiles.length} file(s) selected
                      </span>
                      <button
                        onClick={() => setUploadFiles([])}
                        className="text-xs px-3 py-1 rounded border"
                        style={{ borderColor: colors.lightGray, color: colors.dark, fontFamily: fonts.heading }}
                      >
                        Clear All
                      </button>
                    </div>
                    {uploadFiles.map((file, idx) => (
                      <div key={idx} className="flex items-center gap-3 p-2 rounded border" style={{ borderColor: colors.lightGray }}>
                        <File className="w-4 h-4" style={{ color: colors.midGray }} />
                        <span className="flex-1 text-sm" style={{ color: colors.dark, fontFamily: fonts.body }}>{file.name}</span>
                        <span className="text-xs" style={{ color: colors.midGray }}>
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            )}

            {/* MCP Routing */}
            <section className="border rounded-lg p-6" style={{ backgroundColor: colors.light, borderColor: colors.lightGray }}>
              <h3 className="font-semibold mb-4 text-sm" style={{ color: colors.dark, fontFamily: fonts.heading }}>
                3. Route to MCP (Optional)
              </h3>
              <select
                value={selectedMcp}
                onChange={(e) => setSelectedMcp(e.target.value)}
                className="w-full px-4 py-3 border rounded-lg focus:outline-none"
                style={{
                  borderColor: colors.lightGray,
                  backgroundColor: colors.light,
                  color: colors.dark,
                  fontFamily: fonts.body
                }}
              >
                <option value="">Auto-detect (recommended)</option>
                <option value="etim">ETIM - Product Classification</option>
                <option value="ctax">CTAX - Tax Documents</option>
                <option value="law">LAW - Legal Contracts</option>
              </select>
              <p className="text-xs mt-2" style={{ color: colors.midGray, fontFamily: fonts.body }}>
                Leave blank to auto-detect based on content
              </p>
            </section>

            {/* Start Ingestion */}
            {error && (
              <div className="p-4 border rounded-lg" style={{ backgroundColor: '#fee', borderColor: '#fcc' }}>
                <p className="text-sm" style={{ color: '#c00', fontFamily: fonts.body }}>{error}</p>
              </div>
            )}

            <button
              onClick={startIngestion}
              disabled={
                isSubmitting ||
                (sourceType === 'minio' && selectedFiles.size === 0) ||
                (sourceType === 'path' && !path.trim()) ||
                (sourceType === 'upload' && uploadFiles.length === 0)
              }
              className="w-full py-4 rounded-lg font-semibold flex items-center justify-center gap-2 transition-all"
              style={{
                backgroundColor: isSubmitting || uploading ? colors.midGray : colors.orange,
                color: colors.light,
                fontFamily: fonts.heading,
                cursor: isSubmitting || uploading ? 'not-allowed' : 'pointer',
                fontSize: '16px',
                border: 'none'
              }}
            >
              {isSubmitting || uploading ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  {uploading ? 'Uploading...' : 'Processing...'}
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5" />
                  {sourceType === 'upload' ? `Upload & Process ${uploadFiles.length} file${uploadFiles.length !== 1 ? 's' : ''}` :
                   sourceType === 'minio' ? `Process ${selectedFiles.size} file${selectedFiles.size !== 1 ? 's' : ''}` :
                   'Process Data'}
                </>
              )}
            </button>
          </div>

          {/* Right Column: Jobs & History */}
          <div className="space-y-6">
            {/* Active Jobs */}
            <section className="border rounded-lg p-6" style={{ backgroundColor: colors.light, borderColor: colors.lightGray }}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-sm" style={{ color: colors.dark, fontFamily: fonts.heading }}>
                  Ingestion Jobs
                </h3>
                <button onClick={loadJobs} style={{ color: colors.midGray }}>
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>

              {jobs.length === 0 ? (
                <div className="text-center py-8">
                  <Upload className="w-8 h-8 mx-auto mb-2" style={{ color: colors.lightGray }} />
                  <p className="text-xs" style={{ color: colors.midGray, fontFamily: fonts.body }}>
                    No jobs yet
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {jobs.slice(0, 5).map((job) => (
                    <div key={job.job_id} className="border rounded-lg p-3" style={{ borderColor: colors.lightGray }}>
                      <div className="flex items-start gap-2">
                        {getStatusIcon(job.status)}
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-xs" style={{ color: colors.dark, fontFamily: fonts.heading }}>
                            Job #{job.job_id}
                          </div>
                          <div className="text-xs mt-1" style={{ color: colors.midGray, fontFamily: fonts.body }}>
                            {job.status} • {job.files_processed}/{job.files_total} files
                          </div>
                          {job.status === 'running' && job.current_phase && (
                            <div className="text-xs mt-1" style={{ color: colors.blue, fontFamily: fonts.body }}>
                              {job.current_phase}
                            </div>
                          )}
                          {job.status === 'running' && job.current_file && (
                            <div className="text-xs mt-1 truncate" style={{ color: colors.midGray, fontFamily: fonts.body, opacity: 0.7 }}>
                              📄 {job.current_file}
                            </div>
                          )}
                          {job.status === 'running' && job.files_total > 0 && (
                            <div className="mt-2 h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: colors.lightGray }}>
                              <div
                                className="h-full transition-all"
                                style={{
                                  backgroundColor: colors.orange,
                                  width: `${(job.files_processed / job.files_total) * 100}%`
                                }}
                              />
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Info Card */}
            <section className="border rounded-lg p-6" style={{ backgroundColor: colors.dark, borderColor: colors.dark }}>
              <h4 className="font-semibold text-sm mb-3" style={{ color: colors.light, fontFamily: fonts.heading }}>
                How it Works
              </h4>
              <div className="space-y-2 text-xs" style={{ color: colors.midGray, fontFamily: fonts.body, lineHeight: '1.6' }}>
                <p><strong style={{ color: colors.light }}>1. Select:</strong> Choose files from MinIO or upload new ones</p>
                <p><strong style={{ color: colors.light }}>2. Route:</strong> Auto-detect MCP or choose manually</p>
                <p><strong style={{ color: colors.light }}>3. Process:</strong> Files are chunked, embedded, and stored</p>
                <p><strong style={{ color: colors.light }}>4. Query:</strong> Data becomes available in chat and tools</p>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
