'use client';

import React, { useState, useEffect } from 'react';
import '../styles/onboarding.css';

// Get API URL from environment variable (production-safe)
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4080';

export default function OnboardingPage() {
  const [currentScreen, setCurrentScreen] = useState(1);
  const [formData, setFormData] = useState({
    companyName: '',
    contactName: '',
    contactEmail: '',
    website: '',
    industry: '',
    companySize: '',
    country: 'Germany',
    goals: [] as string[],
    selectedMcps: [] as string[],
    selectedConnectors: [] as string[],
    uploadedFiles: [] as Array<{name: string; size: number; type: string; path?: string}>,
  });

  const [uploadProgress, setUploadProgress] = useState<string>('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadPercent, setUploadPercent] = useState(0);
  const [deploymentStats, setDeploymentStats] = useState<any>(null);

  // Real-time deployment updates
  const [liveMessage, setLiveMessage] = useState<string>('');
  const [deploymentDetails, setDeploymentDetails] = useState<any>(null);

  // Load signup data from localStorage on mount
  useEffect(() => {
    const companyName = localStorage.getItem('signup_company_name');
    const contactName = localStorage.getItem('signup_contact_name');
    const contactEmail = localStorage.getItem('signup_contact_email');

    if (companyName) {
      setFormData(prev => ({
        ...prev,
        companyName,
        contactName: contactName || '',
        contactEmail: contactEmail || '',
      }));
    }
  }, []);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    console.log('=== FILE UPLOAD START ===');
    const files = event.target.files;
    console.log('Files selected:', files?.length || 0);

    if (!files || files.length === 0) {
      console.log('No files selected, aborting');
      return;
    }

    console.log('File list:', Array.from(files).map(f => ({name: f.name, size: f.size})));

    // Show loading message
    setIsUploading(true);
    setUploadPercent(0);
    setUploadProgress(`📤 Uploading ${files.length} file(s) to MinIO... This may take a moment.`);

    // Upload files to backend
    const formDataObj = new FormData();
    Array.from(files).forEach(file => {
      formDataObj.append('files', file);
      console.log('Added to FormData:', file.name);
    });

    try {
      // Use company name as customer ID (sanitized)
      const customerId = formData.companyName.toLowerCase().replace(/[^a-z0-9]/g, '-');
      console.log('Customer ID:', customerId);

      const uploadUrl = `${API_URL}/api/upload-async/start?customer_id=${customerId}`;
      console.log('Starting async upload:', uploadUrl);

      // Start upload (returns immediately with job_id)
      const startResponse = await fetch(uploadUrl, {
        method: 'POST',
        body: formDataObj,
      });

      const startResult = await startResponse.json();
      console.log('Upload job started:', startResult);

      if (!startResult.success) {
        throw new Error('Failed to start upload');
      }

      const jobId = startResult.job_id;
      setUploadProgress(`⟳ Uploading ${files.length} files... 0%`);

      // Poll for status
      const pollStatus = async () => {
        const statusResponse = await fetch(`${API_URL}/api/upload-async/status/${jobId}`);
        const result = await statusResponse.json();

        console.log(`Upload progress: ${result.progress}% (${result.uploaded_count}/${result.total_files})`);
        setUploadPercent(result.progress);
        setUploadProgress(`⟳ Uploading... ${result.progress}% (${result.uploaded_count}/${result.total_files} files)`);

        if (result.status === 'completed') {
          return result;
        } else if (result.status === 'failed') {
          throw new Error(result.error || 'Upload failed');
        }

        // Continue polling
        await new Promise(resolve => setTimeout(resolve, 500));
        return pollStatus();
      };

      console.log('Polling for upload status...');
      const result = await pollStatus();
      console.log('Upload result:', JSON.stringify(result, null, 2));

      if (result.success) {
        console.log('✅ Upload successful!', result.files.length, 'files');

        setUploadPercent(100);
        setUploadProgress(`✓ Success! ${result.files.length} files uploaded to MinIO`);

        // Show file names in console
        console.log('📄 Uploaded files:');
        result.files.forEach((f: any, idx: number) => {
          console.log(`  ${idx + 1}. ${f.filename} (${(f.size / 1024).toFixed(1)} KB)`);
        });

        // Add to uploaded files list
        const newFiles = result.files.map((f: any) => ({
          name: f.filename,
          size: f.size,
          type: f.content_type || 'application/octet-stream',
          path: f.path
        }));

        console.log('Adding files to state:', newFiles.length);

        // Force state update with new array reference
        setFormData(prev => {
          const updated = {
            ...prev,
            uploadedFiles: [...prev.uploadedFiles, ...newFiles]
          };
          console.log('State updated. Total files now:', updated.uploadedFiles.length);
          return updated;
        });

        console.log('Files should now be visible in UI');

        // Clear progress after delay
        setTimeout(() => {
          setUploadProgress('');
          setIsUploading(false);
        }, 2000);
      } else {
        setUploadProgress('❌ Upload failed');
        setIsUploading(false);
      }
    } catch (error) {
      console.error('❌ UPLOAD ERROR:', error);
      setUploadProgress(`❌ Error: ${error}`);
      setTimeout(() => {
        setUploadProgress('');
        setIsUploading(false);
      }, 3000);
    }
  };

  const handleDrop = async (event: React.DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.classList.remove('dragover');

    console.log('Drop event triggered', event.dataTransfer.files);

    const files = event.dataTransfer.files;
    if (!files || files.length === 0) {
      console.log('No files in drop');
      return;
    }

    console.log(`Dropped ${files.length} files`);

    // Upload files to backend
    const formDataObj = new FormData();
    Array.from(files).forEach(file => {
      formDataObj.append('files', file);
    });

    try {
      // Use company name as customer ID (sanitized)
      const customerId = formData.companyName.toLowerCase().replace(/[^a-z0-9]/g, '-');

      const response = await fetch(`${API_URL}/api/upload/files?customer_id=${customerId}`, {
        method: 'POST',
        body: formDataObj,
      });

      const result = await response.json();

      if (result.success) {
        // Show deployment trigger message if first upload
        if (result.installation_triggered) {
          alert(`🚀 First upload for ${formData.companyName}! Your AI brain is being deployed...`);
        }

        // Add to uploaded files list
        const newFiles = result.files.map((f: any) => ({
          name: f.filename,
          size: f.size,
          type: f.content_type || 'application/octet-stream',
          path: f.path
        }));

        setFormData(prev => ({
          ...prev,
          uploadedFiles: [...prev.uploadedFiles, ...newFiles]
        }));
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('Failed to upload files. Please try again.');
    }
  };

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.classList.add('dragover');
  };

  const handleDragEnter = (event: React.DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
  };

  const handleDragLeave = (event: React.DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.classList.remove('dragover');
  };

  const totalScreens = 7;

  const updateProgress = () => {
    // Progress bar update logic handled by CSS classes
  };

  const showScreen = (num: number) => {
    setCurrentScreen(num);
    updateProgress();
  };

  const nextScreen = () => {
    if (currentScreen < totalScreens) {
      showScreen(currentScreen + 1);
    }
  };

  const prevScreen = () => {
    if (currentScreen > 1) {
      showScreen(currentScreen - 1);
    }
  };

  const toggleMcp = (mcpId: string) => {
    setFormData((prev) => ({
      ...prev,
      selectedMcps: prev.selectedMcps.includes(mcpId)
        ? prev.selectedMcps.filter((id) => id !== mcpId)
        : [...prev.selectedMcps, mcpId],
    }));
  };

  const toggleConnector = (connectorId: string) => {
    setFormData((prev) => ({
      ...prev,
      selectedConnectors: prev.selectedConnectors.includes(connectorId)
        ? prev.selectedConnectors.filter((id) => id !== connectorId)
        : [...prev.selectedConnectors, connectorId],
    }));
  };

  const startProcessing = async () => {
    // Validate that files were uploaded
    if (!formData.uploadedFiles || formData.uploadedFiles.length === 0) {
      alert('⚠️ Bitte laden Sie mindestens eine Datei hoch, bevor Sie das Deployment starten.\n\nIhr KI-Brain benötigt Daten zum Lernen.');
      showScreen(2); // Go back to file upload screen
      return;
    }

    showScreen(6);

    // Call backend API to initialize deployment
    try {
      const deploymentData = {
        company_name: formData.companyName,
        industry: formData.industry,
        company_size: formData.companySize,
        country: formData.country,
        goals: formData.goals,
        selected_mcps: formData.selectedMcps,
        selected_connectors: formData.selectedConnectors,
        contact_email: 'onboarding@example.com',
        contact_name: 'Onboarding User'
      };

      console.log('🚀 Starting deployment...');

      const response = await fetch(`${API_URL}/api/onboarding/deploy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(deploymentData),
      });
      const result = await response.json();
      console.log('Deployment initiated:', result);

      const deploymentId = result.deployment_id;

      // Connect to WebSocket for live updates
      const customerId = formData.companyName.toLowerCase().replace(/[^a-z0-9]/g, '-');
      // Convert http:// to ws:// and https:// to wss://
      const wsUrl = API_URL.replace('http://', 'ws://').replace('https://', 'wss://');
      const ws = new WebSocket(`${wsUrl}/ws/deployment/${customerId}`);

      ws.onopen = () => {
        console.log('✓ WebSocket connected');
      };

      ws.onmessage = (event) => {
        const update = JSON.parse(event.data);
        console.log('Deployment update:', update);

        // Update live message
        if (update.message) {
          setLiveMessage(update.message);
        }

        // Update details
        if (update.details) {
          setDeploymentDetails(update.details);
        }

        // Update UI with real status
        if (update.step) {
          const stepMapping: {[key: string]: number} = {
            'Initializing': 0,
            'Generating Configuration': 1,
            'Starting Docker Services': 2,
            'Starting Containers': 2,
            'Containers Running': 2,
            'Initializing Lakehouse': 3,
            'Lakehouse Ready': 3,
            'Starting Ingestion': 4,
            'Ingestion': 4,
            'Ingestion Complete': 4,
            'Training LoRA Adapters': 5,
            'Deploying MCPs': 5
          };

          const stepIndex = stepMapping[update.step] || 0;

          // Update processing steps display
          ['proc1', 'proc2', 'proc3', 'proc4', 'proc5', 'proc6'].forEach((id, idx) => {
            const elem = document.getElementById(id);
            if (elem) {
              if (idx < stepIndex) {
                elem.className = 'processing-step-icon complete';
                elem.textContent = '✓';
              } else if (idx === stepIndex) {
                elem.className = 'processing-step-icon active';
                elem.textContent = '⟳';
              }
            }
          });
        }

        // When complete, verify services and show completion screen
        if (update.status === 'completed' || update.progress === 100) {
          console.log('🎉 Deployment complete!');

          // Verify deployment and get real stats
          fetch(`${API_URL}/api/onboarding/verify/${customerId}`)
            .then(res => res.json())
            .then(stats => {
              console.log('Deployment stats:', stats);
              setDeploymentStats(stats);

              setTimeout(() => {
                ws.close();
                showScreen(7);
              }, 1000);
            })
            .catch(err => {
              console.error('Failed to verify deployment:', err);
              // Show completion screen anyway
              setTimeout(() => {
                ws.close();
                showScreen(7);
              }, 1000);
            });
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setLiveMessage('WebSocket connection error - check backend logs');
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
      };

    } catch (error) {
      console.error('Deployment error:', error);
      setLiveMessage(`Deployment error: ${error}`);
    }
  };

  const mcpPrice = formData.selectedMcps.length * 2500;
  const basePrice = 8000;
  const connectorPrice = formData.selectedConnectors.length * 400;

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="logo">
          <span>0711</span>
        </div>
        <div className="header-right">
          <a href="#" className="help-link">
            Need help?
          </a>
          <div className="user-info">
            <div className="user-avatar">CB</div>
            <span className="user-name">Christoph</span>
          </div>
        </div>
      </header>

      {/* Progress Bar */}
      <div className="progress-container">
        <div className="progress-steps">
          {[1, 2, 3, 4, 5, 6].map((step, idx) => (
            <React.Fragment key={`step-${step}`}>
              <div className="progress-step">
                <div className="step-indicator">
                  <div
                    className={`step-number ${
                      step < currentScreen
                        ? 'completed'
                        : step === currentScreen
                        ? 'active'
                        : ''
                    }`}
                    id={`step${step}-num`}
                  >
                    {step < currentScreen ? '✓' : step}
                  </div>
                  <div
                    className={`step-label ${step === currentScreen ? 'active' : ''}`}
                    id={`step${step}-label`}
                  >
                    {['Welcome', 'Company', 'Data', 'MCPs', 'Connect', 'Launch'][step - 1]}
                  </div>
                </div>
              </div>
              {idx < 5 && (
                <div
                  className={`step-line ${step < currentScreen ? 'completed' : ''}`}
                  id={`line${step}`}
                />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <main className="main-content">
        {/* Screen 1: Welcome */}
        {currentScreen === 1 && (
          <div className="screen active" id="screen1">
            <div className="screen-header">
              <h1>
                Welcome to <strong>0711</strong>
              </h1>
              <p>Let&apos;s set up your Intelligence Orchestrator. This will take about 10 minutes.</p>
            </div>
            <div className="welcome-content">
              <div className="welcome-features">
                <div className="welcome-feature">
                  <div className="feature-icon">🧠</div>
                  <h3>One Brain</h3>
                  <p>A unified intelligence layer that understands your entire business.</p>
                </div>
                <div className="welcome-feature">
                  <div className="feature-icon">⚡</div>
                  <h3>Zero Friction</h3>
                  <p>No integrations to maintain. No consultants to manage. It just works.</p>
                </div>
                <div className="welcome-feature">
                  <div className="feature-icon">∞</div>
                  <h3>Infinite Leverage</h3>
                  <p>20 people with 0711 outperform 200 people without it.</p>
                </div>
              </div>
            </div>
            <div className="btn-container">
              <div></div>
              <button className="btn btn-primary" onClick={nextScreen}>
                Let&apos;s Begin →
              </button>
            </div>
          </div>
        )}

        {/* Screen 2: Company Info */}
        {currentScreen === 2 && (
          <div className="screen active" id="screen2">
            <div className="screen-header">
              <h1>
                Tell us about your <strong>company</strong>
              </h1>
              <p>This helps us configure the right settings and recommendations for you.</p>
            </div>
            <div className="form-section">
              <div className="form-section-title">Basic Information</div>
              <div className="form-grid">
                <div className="form-group">
                  <label>Company Name</label>
                  <input
                    type="text"
                    placeholder="Acme GmbH"
                    value={formData.companyName}
                    onChange={(e) =>
                      setFormData({ ...formData, companyName: e.target.value })
                    }
                  />
                </div>
                <div className="form-group">
                  <label>Company Website</label>
                  <input
                    type="url"
                    placeholder="https://www.your-company.com"
                    value={formData.website}
                    onChange={(e) =>
                      setFormData({ ...formData, website: e.target.value })
                    }
                  />
                </div>
                <div className="form-group">
                  <label>Industry</label>
                  <select
                    value={formData.industry}
                    onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                  >
                    <option>Software & Technology</option>
                    <option>Manufacturing</option>
                    <option>Professional Services</option>
                    <option>Retail & E-Commerce</option>
                    <option>Financial Services</option>
                    <option>Healthcare</option>
                    <option>Other</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Company Size</label>
                  <select
                    value={formData.companySize}
                    onChange={(e) => setFormData({ ...formData, companySize: e.target.value })}
                  >
                    <option>1-10 employees</option>
                    <option>11-50 employees</option>
                    <option>51-200 employees</option>
                    <option>201-500 employees</option>
                    <option>501-1000 employees</option>
                    <option>1000+ employees</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Country</label>
                  <select
                    value={formData.country}
                    onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                  >
                    <option>Germany</option>
                    <option>Austria</option>
                    <option>Switzerland</option>
                    <option>Other EU</option>
                    <option>USA</option>
                    <option>Other</option>
                  </select>
                </div>
              </div>
            </div>
            <div className="btn-container">
              <button className="btn btn-secondary" onClick={prevScreen}>
                ← Back
              </button>
              <button className="btn btn-primary" onClick={nextScreen}>
                Continue →
              </button>
            </div>
          </div>
        )}

        {/* Screen 3: Data Upload */}
        {currentScreen === 3 && (
          <div className="screen active" id="screen3">
            <div className="screen-header">
              <h1>
                Feed the <strong>brain</strong>
              </h1>
              <p>Drop your data in. All of it—messy, scattered, imperfect. The system will understand.</p>
            </div>
            <input
              type="file"
              id="file-input"
              multiple
              onChange={handleFileUpload}
              style={{ display: 'none' }}
            />
            <input
              type="file"
              id="folder-input"
              // @ts-ignore - webkitdirectory is not in TypeScript types
              webkitdirectory=""
              directory=""
              multiple
              onChange={handleFileUpload}
              style={{ display: 'none' }}
            />
            <div
              className="upload-zone"
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
            >
              <div className="upload-icon">📂</div>
              <h3>Drag & drop your files or folders here</h3>
              <p>Or click to browse. We&apos;ll figure out the rest.</p>
              <div style={{display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '1rem'}}>
                <button
                  className="upload-btn"
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    document.getElementById('file-input')?.click();
                  }}
                >
                  📄 Browse Files
                </button>
                <button
                  className="upload-btn"
                  type="button"
                  style={{background: 'var(--green)'}}
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    document.getElementById('folder-input')?.click();
                  }}
                >
                  📁 Browse Folders
                </button>
              </div>
              <div className="upload-types" style={{marginTop: '1.5rem'}}>
                <span className="upload-type">CSV</span>
                <span className="upload-type">Excel</span>
                <span className="upload-type">JSON</span>
                <span className="upload-type">PDF</span>
                <span className="upload-type">SQL</span>
                <span className="upload-type">XML</span>
                <span className="upload-type">Any Format</span>
              </div>
            </div>

            {/* Upload Progress Indicator */}
            {uploadProgress && (
              <div style={{marginTop: '1.5rem'}}>
                <div style={{
                  padding: '1rem',
                  background: isUploading ? 'rgba(106, 155, 204, 0.1)' : 'rgba(120, 140, 93, 0.1)',
                  border: `1px solid ${isUploading ? 'var(--blue)' : 'var(--green)'}`,
                  borderRadius: '8px',
                  textAlign: 'center',
                  fontFamily: 'Poppins, Arial, sans-serif',
                  fontSize: '0.9rem',
                  color: isUploading ? 'var(--blue)' : 'var(--green)'
                }}>
                  {isUploading && <span style={{marginRight: '0.5rem'}}>⟳</span>}
                  {uploadProgress}
                </div>
                {isUploading && (
                  <div style={{
                    marginTop: '0.5rem',
                    background: 'rgba(250, 249, 245, 0.1)',
                    borderRadius: '8px',
                    height: '8px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      height: '100%',
                      background: 'var(--blue)',
                      width: `${uploadPercent}%`,
                      transition: 'width 0.3s ease'
                    }} />
                  </div>
                )}
              </div>
            )}

            {formData.uploadedFiles.length > 0 && (
              <div className="uploaded-files" style={{marginTop: '2rem'}}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '1rem',
                  padding: '1rem',
                  background: 'rgba(120, 140, 93, 0.1)',
                  borderRadius: '8px'
                }}>
                  <div>
                    <h4 style={{marginBottom: '0.25rem'}}>{formData.uploadedFiles.length} files uploaded to MinIO</h4>
                    <p style={{fontSize: '0.85rem', color: 'var(--mid-gray)'}}>
                      Total: {(formData.uploadedFiles.reduce((sum, f) => sum + f.size, 0) / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  <button
                    className="btn btn-secondary"
                    onClick={() => setFormData(prev => ({...prev, uploadedFiles: []}))}
                    style={{padding: '0.5rem 1rem', fontSize: '0.85rem'}}
                  >
                    Clear All
                  </button>
                </div>
                <div style={{maxHeight: '300px', overflowY: 'auto', border: '1px solid rgba(250, 249, 245, 0.1)', borderRadius: '8px', padding: '0.5rem'}}>
                  {formData.uploadedFiles.map((file, idx) => (
                    <div key={idx} className="file-item" style={{marginBottom: '0.5rem'}}>
                      <div className="file-icon">📄</div>
                      <div className="file-info">
                        <div className="file-name">{file.name}</div>
                        <div className="file-size">{(file.size / 1024 / 1024).toFixed(2)} MB</div>
                      </div>
                      <span className="file-status complete">✓</span>
                      <button
                        className="file-remove"
                        onClick={(e) => {
                          e.stopPropagation();
                          setFormData(prev => ({
                            ...prev,
                            uploadedFiles: prev.uploadedFiles.filter((_, i) => i !== idx)
                          }));
                        }}
                      >×</button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="btn-container">
              <button className="btn btn-secondary" onClick={prevScreen}>
                ← Back
              </button>
              <button className="btn btn-primary" onClick={nextScreen}>
                Continue →
              </button>
            </div>
          </div>
        )}

        {/* Screen 4: MCP Selection */}
        {currentScreen === 4 && (
          <div className="screen active" id="screen4">
            <div className="screen-header">
              <h1>
                Choose your <strong>capabilities</strong>
              </h1>
              <p>Select the MCPs you need. You can always add more later.</p>
            </div>
            <div className="mcp-categories">
              <div className="mcp-category">
                <div className="mcp-category-header">
                  <div className="mcp-category-icon orange">◆</div>
                  <h3>Sales & Revenue</h3>
                </div>
                <ul className="mcp-list">
                  {[
                    { id: 'tender', name: 'Tender MCP', price: '€2,500/mo' },
                    { id: 'pricing', name: 'Pricing & Competitor MCP', price: '€3,000/mo' },
                    { id: 'pipeline', name: 'Pipeline MCP', price: '€2,000/mo' },
                  ].map((mcp) => (
                    <li className="mcp-item" key={mcp.id} onClick={() => toggleMcp(mcp.id)}>
                      <div
                        className={`mcp-checkbox ${
                          formData.selectedMcps.includes(mcp.id) ? 'checked' : ''
                        }`}
                      ></div>
                      <div className="mcp-item-info">
                        <div className="mcp-item-name">{mcp.name}</div>
                        <div className="mcp-item-price">{mcp.price}</div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mcp-category">
                <div className="mcp-category-header">
                  <div className="mcp-category-icon blue">◆</div>
                  <h3>Product & Engineering</h3>
                </div>
                <ul className="mcp-list">
                  {[
                    { id: 'etim', name: 'ETIM Classification MCP', price: '€2,000/mo' },
                    { id: 'product', name: 'Product Management MCP', price: '€3,500/mo' },
                    {
                      id: 'multichannel',
                      name: 'Multi-Channel Publishing MCP',
                      price: '€2,000/mo',
                    },
                  ].map((mcp) => (
                    <li className="mcp-item" key={mcp.id} onClick={() => toggleMcp(mcp.id)}>
                      <div
                        className={`mcp-checkbox ${
                          formData.selectedMcps.includes(mcp.id) ? 'checked' : ''
                        }`}
                      ></div>
                      <div className="mcp-item-info">
                        <div className="mcp-item-name">{mcp.name}</div>
                        <div className="mcp-item-price">{mcp.price}</div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mcp-category">
                <div className="mcp-category-header">
                  <div className="mcp-category-icon green">◆</div>
                  <h3>Finance & Operations</h3>
                </div>
                <ul className="mcp-list">
                  {[
                    { id: 'ctax', name: 'CTAX Engine', price: '€3,000/mo' },
                    { id: 'fpa', name: 'FP&A Automation MCP', price: '€2,500/mo' },
                    { id: 'procurement', name: 'Procurement MCP', price: '€2,000/mo' },
                  ].map((mcp) => (
                    <li className="mcp-item" key={mcp.id} onClick={() => toggleMcp(mcp.id)}>
                      <div
                        className={`mcp-checkbox ${
                          formData.selectedMcps.includes(mcp.id) ? 'checked' : ''
                        }`}
                      ></div>
                      <div className="mcp-item-info">
                        <div className="mcp-item-name">{mcp.name}</div>
                        <div className="mcp-item-price">{mcp.price}</div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mcp-category">
                <div className="mcp-category-header">
                  <div className="mcp-category-icon orange">◆</div>
                  <h3>Intelligence & Legal</h3>
                </div>
                <ul className="mcp-list">
                  {[
                    { id: 'law', name: 'Law MCP', price: '€3,000/mo' },
                    {
                      id: 'compliance',
                      name: 'Sanctions & Compliance MCP',
                      price: '€3,000/mo',
                    },
                    { id: 'research', name: 'Research MCP', price: '€2,500/mo' },
                  ].map((mcp) => (
                    <li className="mcp-item" key={mcp.id} onClick={() => toggleMcp(mcp.id)}>
                      <div
                        className={`mcp-checkbox ${
                          formData.selectedMcps.includes(mcp.id) ? 'checked' : ''
                        }`}
                      ></div>
                      <div className="mcp-item-info">
                        <div className="mcp-item-name">{mcp.name}</div>
                        <div className="mcp-item-price">{mcp.price}</div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="selection-summary">
              <div className="selection-info">
                <h4>{formData.selectedMcps.length} MCPs selected</h4>
                <p>Intelligence Orchestrator Core included</p>
              </div>
              <div className="selection-total">
                <div className="amount">€{(basePrice + mcpPrice).toLocaleString()}</div>
                <div className="period">/month</div>
              </div>
            </div>

            <div className="btn-container">
              <button className="btn btn-secondary" onClick={prevScreen}>
                ← Back
              </button>
              <button className="btn btn-primary" onClick={nextScreen}>
                Continue →
              </button>
            </div>
          </div>
        )}

        {/* Screen 5: Connectors */}
        {currentScreen === 5 && (
          <div className="screen active" id="screen5">
            <div className="screen-header">
              <h1>
                Connect your <strong>tools</strong>
              </h1>
              <p>Plug into your existing systems. Bi-directional. Real-time.</p>
            </div>
            <div className="connectors-grid">
              {[
                { id: 'slack', name: 'Slack', icon: '💬', desc: 'Team Communication' },
                { id: 'microsoft365', name: 'Microsoft 365', icon: '📧', desc: 'Email & Docs' },
                { id: 'teams', name: 'Microsoft Teams', icon: '👥', desc: 'Team Communication' },
                { id: 'google', name: 'Google Workspace', icon: '📊', desc: 'Docs & Sheets' },
                { id: 'sap', name: 'SAP', icon: '🗄️', desc: 'ERP System' },
                { id: 'datev', name: 'DATEV', icon: '💰', desc: 'Accounting' },
                { id: 'salesforce', name: 'Salesforce', icon: '📈', desc: 'CRM' },
                { id: 'hubspot', name: 'HubSpot', icon: '🎯', desc: 'Marketing & CRM' },
              ].map((connector) => (
                <div
                  key={connector.id}
                  className={`connector-card ${
                    formData.selectedConnectors.includes(connector.id) ? 'selected' : ''
                  }`}
                  onClick={() => toggleConnector(connector.id)}
                >
                  <div className="connector-icon">{connector.icon}</div>
                  <h4>{connector.name}</h4>
                  <p>{connector.desc}</p>
                  <span
                    className={`connector-status ${
                      formData.selectedConnectors.includes(connector.id) ? 'connected' : 'connect'
                    }`}
                  >
                    {formData.selectedConnectors.includes(connector.id)
                      ? '✓ Connected'
                      : 'Connect'}
                  </span>
                </div>
              ))}
            </div>

            <div className="selection-summary" style={{ marginTop: '2rem' }}>
              <div className="selection-info">
                <h4>{formData.selectedConnectors.length} Connectors configured</h4>
                <p>You can add more from the dashboard anytime</p>
              </div>
              <div className="selection-total">
                <div className="amount">+€{connectorPrice.toLocaleString()}</div>
                <div className="period">/month</div>
              </div>
            </div>

            <div className="btn-container">
              <button className="btn btn-secondary" onClick={prevScreen}>
                ← Back
              </button>
              <button className="btn btn-primary" onClick={startProcessing}>
                Deploy 0711 →
              </button>
            </div>
          </div>
        )}

        {/* Screen 6: Processing */}
        {currentScreen === 6 && (
          <div className="screen active" id="screen6">
            <div className="screen-header">
              <h1>
                Building your <strong>brain</strong>
              </h1>
              <p>This usually takes 2-3 minutes. We&apos;re doing a lot behind the scenes.</p>
            </div>
            <div className="processing-content">
              <div className="processing-animation">
                <div className="processing-ring"></div>
                <div className="processing-ring"></div>
                <div className="processing-ring"></div>
              </div>

              {/* Live Status Panel */}
              {liveMessage && (
                <div style={{
                  margin: '1.5rem 0',
                  padding: '1rem',
                  background: 'rgba(106, 155, 204, 0.1)',
                  border: '1px solid var(--blue)',
                  borderRadius: '8px',
                  fontFamily: 'monospace',
                  fontSize: '0.9rem',
                  color: 'var(--blue)'
                }}>
                  <div style={{fontWeight: 600, marginBottom: '0.5rem'}}>
                    ⟳ {liveMessage}
                  </div>
                  {deploymentDetails?.current_file && (
                    <div style={{fontSize: '0.85rem', opacity: 0.8}}>
                      File: {deploymentDetails.current_file} ({deploymentDetails.processed_files}/{deploymentDetails.total_files})
                    </div>
                  )}
                  {deploymentDetails?.phase && (
                    <div style={{fontSize: '0.85rem', opacity: 0.8}}>
                      Phase: {deploymentDetails.phase}
                    </div>
                  )}
                  {deploymentDetails?.containers && deploymentDetails.containers.length > 0 && (
                    <div style={{fontSize: '0.85rem', opacity: 0.8, marginTop: '0.5rem'}}>
                      {deploymentDetails.containers.map((c: any) => (
                        <div key={c.name}>• {c.name}: {c.status}</div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div className="processing-steps">
                {[
                  {
                    id: 'proc1',
                    title: 'Initializing Docker containers',
                    desc: 'PostgreSQL, pgvector, Apache AGE, Spark',
                  },
                  {
                    id: 'proc2',
                    title: 'Ingesting your data',
                    desc: `${formData.uploadedFiles.length} files uploaded`,
                  },
                  {
                    id: 'proc3',
                    title: 'Building embeddings & knowledge graph',
                    desc: 'Selecting optimal embedding models...',
                  },
                  { id: 'proc4', title: 'Deploying Mixtral LLM', desc: 'Local inference engine' },
                  {
                    id: 'proc5',
                    title: 'Installing MCPs',
                    desc: `${formData.selectedMcps.length} business process modules`,
                  },
                  {
                    id: 'proc6',
                    title: 'Connecting external systems',
                    desc: formData.selectedConnectors.join(', '),
                  },
                ].map((step, idx) => (
                  <div className="processing-step" key={step.id}>
                    <div
                      className={`processing-step-icon ${
                        idx === 0 || idx === 1 ? 'complete' : idx === 2 ? 'active' : 'pending'
                      }`}
                      id={step.id}
                    >
                      {idx === 0 || idx === 1 ? '✓' : idx === 2 ? '⟳' : idx + 1}
                    </div>
                    <div className="processing-step-info">
                      <h4>{step.title}</h4>
                      <p>{step.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Screen 7: Complete */}
        {currentScreen === 7 && (
          <div className="screen active" id="screen7">
            <div className="screen-header">
              <h1>
                You&apos;re <strong>live</strong>
              </h1>
              <p>Your Intelligence Orchestrator is ready. Welcome to the future.</p>
            </div>
            <div className="complete-content">
              <div className="complete-icon">🚀</div>

              {/* Real Deployment Stats */}
              {deploymentStats && deploymentStats.success && (
                <div style={{
                  padding: '1rem',
                  background: 'rgba(120, 140, 93, 0.1)',
                  border: '1px solid var(--green)',
                  borderRadius: '8px',
                  marginBottom: '2rem',
                  fontSize: '0.9rem'
                }}>
                  <div style={{fontWeight: 600, marginBottom: '0.5rem'}}>✓ Deployment Verified</div>
                  <div>Files in MinIO: {deploymentStats.stats?.files_uploaded || formData.uploadedFiles.length}</div>
                  <div>Total Size: {deploymentStats.stats?.total_size_mb || 0} MB</div>
                  <div>Containers Running: {deploymentStats.stats?.containers_running || 0}</div>
                  {deploymentStats.services?.console && (
                    <div style={{marginTop: '0.5rem'}}>
                      Console URL: <a href={deploymentStats.services.console.url} target="_blank" rel="noopener noreferrer" style={{color: 'var(--green)'}}>{deploymentStats.services.console.url}</a>
                    </div>
                  )}
                </div>
              )}

              <div className="complete-stats">
                <div className="complete-stat">
                  <div className="number">{deploymentStats?.stats?.files_uploaded || formData.uploadedFiles.length}</div>
                  <div className="label">Files Uploaded</div>
                </div>
                <div className="complete-stat">
                  <div className="number">{formData.selectedMcps.length}</div>
                  <div className="label">MCPs Selected</div>
                </div>
                <div className="complete-stat">
                  <div className="number">{formData.selectedConnectors.length}</div>
                  <div className="label">Connectors</div>
                </div>
                <div className="complete-stat">
                  <div className="number">{deploymentStats?.status === 'active' ? '✓ Active' : 'Ready'}</div>
                  <div className="label">Status</div>
                </div>
              </div>

              <div className="quick-actions">
                <div className="quick-action">
                  <div className="quick-action-icon">💬</div>
                  <h3>Talk to 0711</h3>
                  <p>Ask anything about your business</p>
                </div>
                <div className="quick-action">
                  <div className="quick-action-icon">⚡</div>
                  <h3>Build Workflows</h3>
                  <p>Connect MCPs into automated chains</p>
                </div>
                <div className="quick-action">
                  <div className="quick-action-icon">🛒</div>
                  <h3>MCP Marketplace</h3>
                  <p>Add more capabilities</p>
                </div>
              </div>

              <div className="btn-container" style={{ justifyContent: 'center' }}>
                <button
                  className="btn btn-success"
                  onClick={() => {
                    const consoleUrl = deploymentStats?.services?.console?.url || 'http://localhost:4020';
                    window.location.href = consoleUrl;
                  }}
                  style={{ fontSize: '1.1rem', padding: '1.25rem 3rem' }}
                >
                  Open Console →
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
