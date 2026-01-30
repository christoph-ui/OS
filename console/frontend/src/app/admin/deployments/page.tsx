'use client';

import { useState, useEffect } from 'react';
import AdminLayout from '@/components/admin/AdminLayout';
import FileUploadZone from '@/components/FileUploadZone';
import { Server, Package, Cpu, Database, CheckCircle, AlertCircle, Download, Plus, X, Users, Upload } from 'lucide-react';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  red: '#d75757',
  green: '#788c5d',
};

interface Installation {
  customer_id: string;
  company_name: string;
  deployment_target: string;
  deployment_date: string;
  enabled_mcps: string[];
  initial_stats: {
    files_processed?: number;
    embeddings_generated?: number;
  };
  created_at: string;
}

interface ServiceStatus {
  status: string;
  port: number;
  details?: any;
}

export default function DeploymentsPage() {
  const [installations, setInstallations] = useState<Installation[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [services, setServices] = useState<Record<string, ServiceStatus>>({});
  const [loading, setLoading] = useState(true);
  const [showDeployForm, setShowDeployForm] = useState(false);
  const [deploying, setDeploying] = useState(false);
  const [deployResult, setDeployResult] = useState<any>(null);

  const [formData, setFormData] = useState({
    company_name: '',
    contact_email: '',
    data_sources: '',
    deployment_target: 'on-premise',
    mcps: ['ctax', 'law', 'etim'],
  });

  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const token = localStorage.getItem('0711_admin_token');

      // Load Cradle installations
      const installResp = await fetch('http://localhost:4080/api/admin/cradle/installations', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (installResp.ok) {
        const data = await installResp.json();
        setInstallations(data.installations || []);
      }

      // Load all customers from main DB
      const customersResp = await fetch('http://localhost:4080/api/admin/customers?limit=100', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (customersResp.ok) {
        const data = await customersResp.json();
        setCustomers(data || []);
      }

      // Load service status
      const servicesResp = await fetch('http://localhost:4080/api/admin/cradle/services', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (servicesResp.ok) {
        const data = await servicesResp.json();
        setServices(data.services || {});
      }

    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeploy = async () => {
    if (selectedFiles.length === 0) {
      setDeployResult({ success: false, error: 'Please upload at least one file' });
      return;
    }

    setDeploying(true);
    setUploading(true);
    setDeployResult(null);

    try {
      const token = localStorage.getItem('0711_admin_token');

      // Generate customer_id from company name
      const customer_id = formData.company_name.toLowerCase()
        .replace(/[^a-z0-9]+/g, '')
        .substring(0, 20);

      // Upload files via existing upload endpoint
      const formDataUpload = new FormData();
      selectedFiles.forEach(file => {
        formDataUpload.append('files', file);
      });

      const mcpsParam = formData.mcps.join(',');

      const response = await fetch(
        `http://localhost:4080/api/upload/files?customer_id=${customer_id}&selected_mcps=${mcpsParam}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          body: formDataUpload,
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();

      setDeployResult({
        success: true,
        message: `Files uploaded successfully. Deployment triggered for ${customer_id}.`,
        details: `${selectedFiles.length} files uploaded. Building console in background (~15-20 min).`
      });

      // Reset form
      setSelectedFiles([]);
      setFormData({
        company_name: '',
        contact_email: '',
        data_sources: '',
        deployment_target: 'on-premise',
        mcps: ['ctax', 'law', 'etim'],
      });

      // Reload data after delay
      setTimeout(() => {
        loadData();
        setShowDeployForm(false);
      }, 3000);

    } catch (error: any) {
      setDeployResult({ success: false, error: error.message });
    } finally {
      setDeploying(false);
      setUploading(false);
    }
  };

  const handleDownload = async (customerId: string) => {
    try {
      const token = localStorage.getItem('0711_admin_token');

      const response = await fetch(`http://localhost:4080/api/admin/cradle/images/${customerId}/download`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${customerId}-v1.0.tar.gz`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        alert('Download failed');
      }
    } catch (error) {
      console.error('Download error:', error);
      alert('Download error');
    }
  };

  const toggleMCP = (mcp: string) => {
    setFormData(prev => ({
      ...prev,
      mcps: prev.mcps.includes(mcp)
        ? prev.mcps.filter(m => m !== mcp)
        : [...prev.mcps, mcp]
    }));
  };

  if (loading) {
    return (
      <AdminLayout>
        <div style={{ padding: 40, textAlign: 'center' }}>Loading...</div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      {/* Header */}
      <div style={{ padding: '32px 40px', borderBottom: `1px solid ${colors.lightGray}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ fontSize: 28, fontWeight: 600, margin: 0, color: colors.dark }}>
              Cradle Deployments
            </h1>
            <p style={{ fontSize: 15, color: colors.midGray, margin: '8px 0 0' }}>
              GPU Processing Central • Client Console Builder
            </p>
          </div>
          <button
            onClick={() => setShowDeployForm(true)}
            style={{
              padding: '12px 24px',
              backgroundColor: colors.red,
              color: colors.light,
              border: 'none',
              borderRadius: 10,
              fontSize: 15,
              fontWeight: 500,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <Plus size={18} />
            Deploy New Client
          </button>
        </div>
      </div>

      <div style={{ padding: 40 }}>
        {/* Service Status Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20, marginBottom: 40 }}>
          {Object.entries(services).map(([name, status]) => (
            <div
              key={name}
              style={{
                padding: 24,
                backgroundColor: colors.light,
                border: `2px solid ${colors.lightGray}`,
                borderRadius: 12,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                {status.status === 'healthy' ? (
                  <CheckCircle size={24} color={colors.green} />
                ) : (
                  <AlertCircle size={24} color={colors.red} />
                )}
                <div>
                  <div style={{ fontSize: 15, fontWeight: 500, textTransform: 'capitalize' }}>{name}</div>
                  <div style={{ fontSize: 13, color: colors.midGray }}>Port {status.port}</div>
                </div>
              </div>
              <div style={{
                fontSize: 12,
                color: status.status === 'healthy' ? colors.green : colors.red,
                textTransform: 'uppercase',
                fontWeight: 600
              }}>
                {status.status}
              </div>
            </div>
          ))}
        </div>

        {/* Cradle Deployments Table */}
        <div style={{
          backgroundColor: colors.light,
          border: `2px solid ${colors.lightGray}`,
          borderRadius: 12,
          padding: 24,
          marginBottom: 40,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
            <h2 style={{ fontSize: 18, fontWeight: 600, margin: 0, color: colors.dark }}>
              Cradle Deployments (Baked Images)
            </h2>
            <button
              onClick={loadData}
              style={{
                padding: '8px 16px',
                backgroundColor: colors.lightGray,
                border: 'none',
                borderRadius: 8,
                cursor: 'pointer',
                fontSize: 14,
              }}
            >
              Refresh
            </button>
          </div>

          {installations.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 60, color: colors.midGray }}>
              <Package size={48} style={{ margin: '0 auto 16px', opacity: 0.5 }} />
              <div style={{ fontSize: 16 }}>No installations yet</div>
              <div style={{ fontSize: 14, marginTop: 8 }}>Deploy your first client to get started</div>
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: `2px solid ${colors.lightGray}` }}>
                  <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>Customer ID</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>Company</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>Target</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>MCPs</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>Stats</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>Deployed</th>
                  <th style={{ textAlign: 'right', padding: '12px 16px', fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {installations.map(install => (
                  <tr key={install.customer_id} style={{ borderBottom: `1px solid ${colors.lightGray}` }}>
                    <td style={{ padding: '16px', fontSize: 14, fontWeight: 500, fontFamily: 'monospace' }}>{install.customer_id}</td>
                    <td style={{ padding: '16px', fontSize: 14 }}>{install.company_name}</td>
                    <td style={{ padding: '16px', fontSize: 13 }}>
                      <span style={{ padding: '4px 12px', backgroundColor: colors.lightGray, borderRadius: 12, fontSize: 12 }}>
                        {install.deployment_target}
                      </span>
                    </td>
                    <td style={{ padding: '16px', fontSize: 13, color: colors.midGray }}>
                      {install.enabled_mcps.join(', ')}
                    </td>
                    <td style={{ padding: '16px', fontSize: 13, color: colors.midGray }}>
                      {install.initial_stats.files_processed || 0} files, {install.initial_stats.embeddings_generated || 0} embeddings
                    </td>
                    <td style={{ padding: '16px', fontSize: 13, color: colors.midGray }}>
                      {new Date(install.deployment_date).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '16px', textAlign: 'right' }}>
                      <button
                        onClick={() => handleDownload(install.customer_id)}
                        style={{
                          padding: '6px 12px',
                          backgroundColor: colors.dark,
                          color: colors.light,
                          border: 'none',
                          borderRadius: 6,
                          cursor: 'pointer',
                          fontSize: 13,
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 6,
                        }}
                      >
                        <Download size={14} />
                        Download
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* All Customers Table */}
        <div style={{
          backgroundColor: colors.light,
          border: `2px solid ${colors.lightGray}`,
          borderRadius: 12,
          padding: 24,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
            <h2 style={{ fontSize: 18, fontWeight: 600, margin: 0, color: colors.dark }}>
              All Customers ({customers.length})
            </h2>
          </div>

          {customers.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 60, color: colors.midGray }}>
              <Users size={48} style={{ margin: '0 auto 16px', opacity: 0.5 }} />
              <div style={{ fontSize: 16 }}>No customers yet</div>
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: `2px solid ${colors.lightGray}` }}>
                  <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>Company</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>Email</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>Tier</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>Status</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>Cradle</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>Created</th>
                </tr>
              </thead>
              <tbody>
                {customers.map(customer => {
                  const hasDeployment = installations.some(i =>
                    i.company_name.toLowerCase() === customer.company_name.toLowerCase()
                  );

                  return (
                    <tr key={customer.id} style={{ borderBottom: `1px solid ${colors.lightGray}` }}>
                      <td style={{ padding: '16px', fontSize: 14, fontWeight: 500 }}>{customer.company_name}</td>
                      <td style={{ padding: '16px', fontSize: 14, color: colors.midGray }}>{customer.contact_email}</td>
                      <td style={{ padding: '16px', fontSize: 13 }}>
                        <span style={{
                          padding: '4px 12px',
                          backgroundColor: colors.lightGray,
                          borderRadius: 12,
                          fontSize: 12,
                          textTransform: 'uppercase'
                        }}>
                          {customer.tier}
                        </span>
                      </td>
                      <td style={{ padding: '16px', fontSize: 13 }}>
                        <span style={{
                          padding: '4px 12px',
                          backgroundColor: customer.status === 'active' ? `${colors.green}20` : `${colors.red}20`,
                          color: customer.status === 'active' ? colors.green : colors.red,
                          borderRadius: 12,
                          fontSize: 12,
                          textTransform: 'uppercase'
                        }}>
                          {customer.status}
                        </span>
                      </td>
                      <td style={{ padding: '16px', fontSize: 13 }}>
                        {hasDeployment ? (
                          <span style={{ color: colors.green, fontWeight: 500 }}>✓ Deployed</span>
                        ) : (
                          <span style={{ color: colors.midGray }}>Not deployed</span>
                        )}
                      </td>
                      <td style={{ padding: '16px', fontSize: 13, color: colors.midGray }}>
                        {new Date(customer.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Deploy Modal */}
      {showDeployForm && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            backgroundColor: colors.light,
            borderRadius: 16,
            padding: 32,
            width: 600,
            maxHeight: '80vh',
            overflowY: 'auto',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <h2 style={{ fontSize: 22, fontWeight: 600, margin: 0 }}>Deploy New Client</h2>
              <button
                onClick={() => setShowDeployForm(false)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4 }}
              >
                <X size={24} color={colors.midGray} />
              </button>
            </div>

            {deployResult && (
              <div style={{
                padding: 16,
                backgroundColor: deployResult.success ? `${colors.green}20` : `${colors.red}20`,
                border: `2px solid ${deployResult.success ? colors.green : colors.red}`,
                borderRadius: 10,
                marginBottom: 20,
              }}>
                <div style={{ fontSize: 15, fontWeight: 600, color: deployResult.success ? colors.green : colors.red, marginBottom: 8 }}>
                  {deployResult.success ? '✓ Deployment Started' : '✗ Deployment Failed'}
                </div>
                <div style={{ fontSize: 13, color: colors.dark, marginBottom: deployResult.details ? 8 : 0 }}>
                  {deployResult.success ? deployResult.message : deployResult.error}
                </div>
                {deployResult.details && (
                  <div style={{ fontSize: 12, color: colors.midGray }}>
                    {deployResult.details}
                  </div>
                )}
              </div>
            )}

            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: 13, color: colors.midGray, marginBottom: 6 }}>
                Company Name *
              </label>
              <input
                type="text"
                required
                value={formData.company_name}
                onChange={e => setFormData({ ...formData, company_name: e.target.value })}
                style={{
                  width: '100%',
                  padding: 12,
                  border: `2px solid ${colors.lightGray}`,
                  borderRadius: 10,
                  fontSize: 14,
                }}
              />
            </div>

            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: 13, color: colors.midGray, marginBottom: 6 }}>
                Contact Email *
              </label>
              <input
                type="email"
                required
                value={formData.contact_email}
                onChange={e => setFormData({ ...formData, contact_email: e.target.value })}
                style={{
                  width: '100%',
                  padding: 12,
                  border: `2px solid ${colors.lightGray}`,
                  borderRadius: 10,
                  fontSize: 14,
                }}
              />
            </div>

            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: 13, color: colors.midGray, marginBottom: 12 }}>
                Upload Files *
              </label>

              <FileUploadZone
                onFilesSelected={(files) => setSelectedFiles(prev => [...prev, ...files])}
                uploading={uploading}
              />

              {selectedFiles.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <div style={{ fontSize: 13, color: colors.midGray, marginBottom: 8 }}>
                    Selected Files ({selectedFiles.length}):
                  </div>
                  {selectedFiles.map((file, idx) => (
                    <div key={idx} style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 12px',
                      backgroundColor: colors.lightGray,
                      borderRadius: 6,
                      marginBottom: 4,
                      fontSize: 13,
                    }}>
                      <span>📄 {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
                      <button
                        onClick={() => setSelectedFiles(prev => prev.filter((_, i) => i !== idx))}
                        style={{
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          color: colors.red,
                        }}
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: 13, color: colors.midGray, marginBottom: 6 }}>
                Deployment Target
              </label>
              <select
                value={formData.deployment_target}
                onChange={e => setFormData({ ...formData, deployment_target: e.target.value })}
                style={{
                  width: '100%',
                  padding: 12,
                  border: `2px solid ${colors.lightGray}`,
                  borderRadius: 10,
                  fontSize: 14,
                }}
              >
                <option value="on-premise">On-Premise</option>
                <option value="cloud">Cloud</option>
                <option value="hybrid">Hybrid</option>
              </select>
            </div>

            <div style={{ marginBottom: 24 }}>
              <label style={{ display: 'block', fontSize: 13, color: colors.midGray, marginBottom: 12 }}>
                Enabled MCPs
              </label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                {['ctax', 'law', 'etim', 'tender', 'market', 'publish'].map(mcp => (
                  <label key={mcp} style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={formData.mcps.includes(mcp)}
                      onChange={() => toggleMCP(mcp)}
                      style={{ width: 16, height: 16 }}
                    />
                    <span style={{ fontSize: 14, textTransform: 'uppercase' }}>{mcp}</span>
                  </label>
                ))}
              </div>
            </div>

            <button
              onClick={handleDeploy}
              disabled={deploying}
              style={{
                width: '100%',
                padding: 16,
                backgroundColor: deploying ? colors.midGray : colors.red,
                color: colors.light,
                border: 'none',
                borderRadius: 10,
                fontSize: 16,
                fontWeight: 600,
                cursor: deploying ? 'not-allowed' : 'pointer',
              }}
            >
              {deploying ? 'Deploying...' : 'Deploy Customer Console'}
            </button>

            <div style={{ fontSize: 12, color: colors.midGray, marginTop: 12, textAlign: 'center' }}>
              Build will run in background (~15-20 minutes)
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
