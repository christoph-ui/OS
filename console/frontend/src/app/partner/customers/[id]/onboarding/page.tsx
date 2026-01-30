'use client';

import { useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import PartnerHeader from '@/components/PartnerHeader';
import FileUploadZone from '@/components/FileUploadZone';
import ProgressModal from '@/components/ProgressModal';
import { useProgress } from '@/hooks/useProgress';

const colors = {
  dark: '#141413',
  light: '#faf9f5',
  midGray: '#b0aea5',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  green: '#788c5d',
};

const availableMCPs = [
  { id: 'ctax', name: 'CTAX', description: 'Corporate Tax Specialist' },
  { id: 'law', name: 'LAW', description: 'Legal Contracts Specialist' },
  { id: 'etim', name: 'ETIM', description: 'Product Classification (ETIM/ECLASS)' },
  { id: 'tender', name: 'TENDER', description: 'Public Tender Specialist' },
];

export default function CustomerOnboardingPage() {
  const router = useRouter();
  const params = useParams();
  const customerId = params?.id as string;

  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedMCPs, setSelectedMCPs] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [showProgress, setShowProgress] = useState(false);

  // Real-time progress from WebSocket
  const { progress, connected, overallProgress } = useProgress(customerId);

  console.log('Progress state:', progress, 'Overall:', overallProgress);

  const handleFilesSelected = (files: File[]) => {
    setSelectedFiles(prev => [...prev, ...files]);
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const toggleMCP = (mcpId: string) => {
    setSelectedMCPs(prev =>
      prev.includes(mcpId)
        ? prev.filter(id => id !== mcpId)
        : [...prev, mcpId]
    );
  };

  const startOnboarding = async () => {
    if (selectedFiles.length === 0) {
      alert('Bitte laden Sie mindestens eine Datei hoch');
      return;
    }

    setUploading(true);
    setShowProgress(true);  // Show Progress Modal

    try {
      const token = localStorage.getItem('0711_token');
      const formData = new FormData();

      selectedFiles.forEach(file => {
        formData.append('files', file);
      });

      const mcpsParam = selectedMCPs.join(',') || 'general';

      const response = await fetch(
        `http://localhost:4080/api/upload/files?customer_id=${customerId}&selected_mcps=${mcpsParam}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          body: formData,
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload fehlgeschlagen');
      }

      const data = await response.json();

      // Progress Modal will show updates via WebSocket
      // Wait for completion (overallProgress === 100) or timeout
      const checkCompletion = setInterval(() => {
        if (overallProgress >= 90) {
          clearInterval(checkCompletion);
          setTimeout(() => {
            router.push(`/partner/customers/${customerId}`);
          }, 2000);
        }
      }, 1000);

      // Safety timeout: redirect after 5 minutes regardless
      setTimeout(() => {
        clearInterval(checkCompletion);
        router.push(`/partner/customers/${customerId}`);
      }, 300000);
    } catch (error) {
      console.error('Error during onboarding:', error);
      alert(error instanceof Error ? error.message : 'Fehler beim Onboarding');
      setUploading(false);
      setShowProgress(false);
    }
  };

  return (
    <div>
      <PartnerHeader title="Customer Onboarding" />

      {/* Real-time Progress Modal */}
      {showProgress && (
        <ProgressModal
          upload={(progress?.upload as any) || null}
          ingestion={(progress?.ingestion as any) || null}
          deployment={(progress?.deployment as any) || null}
          overallProgress={overallProgress}
          onClose={() => router.push(`/partner/customers/${customerId}`)}
        />
      )}

      <div style={{ padding: 40, maxWidth: 1000, margin: '0 auto' }}>
        {/* Progress Indicator */}
        {!showProgress && (
          <div style={{ marginBottom: 40 }}>
            <div style={{ display: 'flex', gap: 16, marginBottom: 32 }}>
              {['Dateien', 'MCPs', 'Start'].map((step, idx) => (
                <div
                  key={step}
                  style={{
                    flex: 1,
                    padding: 16,
                    textAlign: 'center',
                    backgroundColor: idx === 0 ? colors.orange : colors.lightGray,
                    borderRadius: 12,
                    color: idx === 0 ? '#fff' : colors.dark,
                    fontWeight: idx === 0 ? 600 : 400,
                  }}
                >
                  {idx + 1}. {step}
                </div>
              ))}
            </div>
          </div>
        )}

        {!showProgress && (
          <>
            {/* File Upload */}
            <div style={{
              backgroundColor: '#fff',
              borderRadius: 16,
              padding: 32,
              border: `1.5px solid ${colors.lightGray}`,
              marginBottom: 24,
            }}>
              <h3 style={{
                fontFamily: "'Poppins', Arial, sans-serif",
                fontSize: 18,
                fontWeight: 600,
                margin: '0 0 24px',
                color: colors.dark,
              }}>
                1. Dateien hochladen
              </h3>

              <FileUploadZone onFilesSelected={handleFilesSelected} uploading={uploading} />

              {selectedFiles.length > 0 && (
                <div style={{ marginTop: 24 }}>
                  <p style={{
                    fontSize: 14,
                    fontWeight: 600,
                    color: colors.dark,
                    marginBottom: 12,
                  }}>
                    {selectedFiles.length} Datei(en) ausgewählt:
                  </p>
                  {selectedFiles.map((file, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '8px 12px',
                        backgroundColor: colors.light,
                        borderRadius: 8,
                        marginBottom: 8,
                      }}
                    >
                      <span style={{ fontSize: 14 }}>{file.name}</span>
                      <button
                        onClick={() => removeFile(idx)}
                        style={{
                          padding: '4px 12px',
                          backgroundColor: 'transparent',
                          border: 'none',
                          color: colors.midGray,
                          cursor: 'pointer',
                          fontSize: 18,
                        }}
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* MCP Selection */}
            <div style={{
              backgroundColor: '#fff',
              borderRadius: 16,
              padding: 32,
              border: `1.5px solid ${colors.lightGray}`,
              marginBottom: 24,
            }}>
              <h3 style={{
                fontFamily: "'Poppins', Arial, sans-serif",
                fontSize: 18,
                fontWeight: 600,
                margin: '0 0 24px',
                color: colors.dark,
              }}>
                2. MCPs auswählen (optional)
              </h3>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                {availableMCPs.map(mcp => (
                  <div
                    key={mcp.id}
                    onClick={() => toggleMCP(mcp.id)}
                    style={{
                      padding: 20,
                      border: `2px solid ${selectedMCPs.includes(mcp.id) ? colors.orange : colors.lightGray}`,
                      borderRadius: 12,
                      cursor: 'pointer',
                      backgroundColor: selectedMCPs.includes(mcp.id) ? `${colors.orange}08` : '#fff',
                      transition: 'all 0.2s',
                    }}
                  >
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: 8,
                    }}>
                      <strong style={{ fontSize: 16, color: colors.dark }}>{mcp.name}</strong>
                      {selectedMCPs.includes(mcp.id) && (
                        <span style={{ fontSize: 20, color: colors.orange }}>✓</span>
                      )}
                    </div>
                    <p style={{ fontSize: 13, color: colors.midGray, margin: 0 }}>
                      {mcp.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}>
              <button
                onClick={() => router.back()}
                disabled={uploading}
                style={{
                  padding: '12px 24px',
                  backgroundColor: colors.lightGray,
                  color: colors.dark,
                  border: 'none',
                  borderRadius: 10,
                  fontSize: 15,
                  fontWeight: 500,
                  cursor: uploading ? 'not-allowed' : 'pointer',
                }}
              >
                Abbrechen
              </button>

              <button
                onClick={startOnboarding}
                disabled={uploading || selectedFiles.length === 0}
                style={{
                  padding: '12px 32px',
                  backgroundColor: uploading || selectedFiles.length === 0 ? colors.midGray : colors.orange,
                  color: '#fff',
                  border: 'none',
                  borderRadius: 10,
                  fontSize: 15,
                  fontWeight: 600,
                  cursor: uploading || selectedFiles.length === 0 ? 'not-allowed' : 'pointer',
                  fontFamily: "'Poppins', Arial, sans-serif",
                  boxShadow: uploading || selectedFiles.length === 0 ? 'none' : `0 4px 12px ${colors.orange}40`,
                }}
              >
                {uploading ? 'Upload läuft...' : 'Onboarding starten'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
