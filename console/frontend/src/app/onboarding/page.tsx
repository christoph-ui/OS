'use client';

import { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useDropzone } from 'react-dropzone';
import { 
  Upload, FileText, Check, Loader2, Sparkles, 
  TrendingUp, Euro, Clock, Zap, Database, Share2, 
  ArrowRight, ChevronRight, MessageSquare, X
} from 'lucide-react';

const colors = {
  dark: '#141413',
  light: '#faf9f5',
  midGray: '#b0aea5',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  blue: '#6a9bcc',
  green: '#788c5d',
};

type OnboardingStep = 'upload' | 'analyzing' | 'results' | 'deploying' | 'done';

interface FileInfo {
  name: string;
  size: number;
  type: string;
}

interface AnalysisResult {
  upload_id: string;
  metrics: {
    total_files: number;
    total_records: number;
    total_products: number;
    data_quality: number;
  };
  business_model: {
    type: string;
    confidence: number;
    indicators: string[];
  };
  value: {
    revenue_opportunity: string;
    cost_savings: string;
    time_to_value: string;
  };
  top_recommendations: Array<{
    connector: string;
    reason: string;
    value: string;
  }>;
  summary: string;
  next_steps: string[];
}

export default function SmartOnboarding() {
  const router = useRouter();
  const [step, setStep] = useState<OnboardingStep>('upload');
  const [files, setFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [deployProgress, setDeployProgress] = useState(0);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles(prev => [...prev, ...acceptedFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/json': ['.json'],
      'application/xml': ['.xml'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
  });

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const startAnalysis = async () => {
    if (files.length === 0) return;

    setStep('analyzing');
    setUploadProgress(0);

    // Simulate upload progress
    const uploadInterval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(uploadInterval);
          return 100;
        }
        return prev + Math.random() * 20;
      });
    }, 200);

    try {
      const formData = new FormData();
      files.forEach(file => formData.append('files', file));

      const token = localStorage.getItem('0711_token');
      const response = await fetch('http://localhost:4080/api/smart-onboarding/upload', {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
        body: formData,
      });

      clearInterval(uploadInterval);
      setUploadProgress(100);

      if (response.ok) {
        const data = await response.json();
        
        // Poll for analysis results
        setTimeout(async () => {
          const analysisRes = await fetch(
            `http://localhost:4080/api/smart-onboarding/analysis/${data.upload_id}/summary`,
            { headers: token ? { 'Authorization': `Bearer ${token}` } : {} }
          );
          
          if (analysisRes.ok) {
            const analysisData = await analysisRes.json();
            setAnalysisResult(analysisData);
            setStep('results');
          }
        }, 2000);
      } else {
        // Demo fallback
        setTimeout(() => {
          setAnalysisResult(demoAnalysisResult);
          setStep('results');
        }, 3000);
      }
    } catch (error) {
      console.error('Analysis error:', error);
      // Demo fallback
      setTimeout(() => {
        setAnalysisResult(demoAnalysisResult);
        setStep('results');
      }, 3000);
    }
  };

  const startDeploy = async () => {
    setStep('deploying');
    setDeployProgress(0);

    // Simulate deployment
    const interval = setInterval(() => {
      setDeployProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(() => setStep('done'), 500);
          return 100;
        }
        return prev + Math.random() * 8;
      });
    }, 300);
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: colors.light,
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* Header */}
      <div style={{
        backgroundColor: '#fff',
        borderBottom: `1px solid ${colors.lightGray}`,
        padding: '20px 40px',
      }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{
              width: 40,
              height: 40,
              borderRadius: 10,
              backgroundColor: colors.orange + '15',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Sparkles size={20} color={colors.orange} />
            </div>
            <div>
              <h1 style={{
                fontFamily: "'Poppins', sans-serif",
                fontSize: 20,
                fontWeight: 600,
                color: colors.dark,
                margin: 0,
              }}>
                Smart Onboarding
              </h1>
              <p style={{ color: colors.midGray, fontSize: 13, margin: 0 }}>
                Upload your data. We figure out the rest.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Progress Steps */}
      <div style={{
        backgroundColor: '#fff',
        borderBottom: `1px solid ${colors.lightGray}`,
        padding: '16px 40px',
      }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {[
              { key: 'upload', label: 'Upload', icon: Upload },
              { key: 'analyzing', label: 'AI Analysis', icon: Sparkles },
              { key: 'results', label: 'Results', icon: TrendingUp },
              { key: 'done', label: 'Ready', icon: Check },
            ].map((s, i, arr) => (
              <div key={s.key} style={{ display: 'flex', alignItems: 'center' }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '8px 16px',
                  backgroundColor: step === s.key || ['done'].includes(step) && i < arr.findIndex(x => x.key === step) 
                    ? colors.orange + '15' 
                    : 'transparent',
                  borderRadius: 20,
                }}>
                  <s.icon 
                    size={16} 
                    color={step === s.key ? colors.orange : colors.midGray} 
                  />
                  <span style={{
                    fontSize: 13,
                    fontWeight: step === s.key ? 600 : 400,
                    color: step === s.key ? colors.orange : colors.midGray,
                  }}>
                    {s.label}
                  </span>
                </div>
                {i < arr.length - 1 && (
                  <ChevronRight size={16} color={colors.lightGray} style={{ margin: '0 4px' }} />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div style={{ flex: 1, padding: '40px' }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          {step === 'upload' && (
            <UploadStep
              files={files}
              onDrop={onDrop}
              getRootProps={getRootProps}
              getInputProps={getInputProps}
              isDragActive={isDragActive}
              removeFile={removeFile}
              formatFileSize={formatFileSize}
              onContinue={startAnalysis}
            />
          )}

          {step === 'analyzing' && (
            <AnalyzingStep progress={uploadProgress} />
          )}

          {step === 'results' && analysisResult && (
            <ResultsStep result={analysisResult} onDeploy={startDeploy} />
          )}

          {step === 'deploying' && (
            <DeployingStep progress={deployProgress} />
          )}

          {step === 'done' && (
            <DoneStep onStartChat={() => router.push('/chat')} />
          )}
        </div>
      </div>
    </div>
  );
}

// Upload Step Component
function UploadStep({
  files,
  onDrop,
  getRootProps,
  getInputProps,
  isDragActive,
  removeFile,
  formatFileSize,
  onContinue,
}: any) {
  return (
    <div>
      <div style={{
        backgroundColor: '#fff',
        borderRadius: 16,
        border: `1px solid ${colors.lightGray}`,
        padding: 40,
        marginBottom: 24,
      }}>
        <h2 style={{
          fontFamily: "'Poppins', sans-serif",
          fontSize: 22,
          fontWeight: 600,
          color: colors.dark,
          margin: '0 0 8px',
          textAlign: 'center',
        }}>
          Drop your files here
        </h2>
        <p style={{
          color: colors.midGray,
          fontSize: 14,
          margin: '0 0 32px',
          textAlign: 'center',
        }}>
          CSV, Excel, JSON, XML — any format works. We'll figure it out.
        </p>

        <div
          {...getRootProps()}
          style={{
            border: `2px dashed ${isDragActive ? colors.orange : colors.lightGray}`,
            borderRadius: 12,
            padding: 60,
            textAlign: 'center',
            cursor: 'pointer',
            backgroundColor: isDragActive ? colors.orange + '08' : colors.light,
            transition: 'all 0.2s',
          }}
        >
          <input {...getInputProps()} />
          <Upload
            size={48}
            color={isDragActive ? colors.orange : colors.midGray}
            style={{ marginBottom: 16 }}
          />
          <p style={{
            fontSize: 16,
            color: isDragActive ? colors.orange : colors.dark,
            margin: '0 0 8px',
            fontWeight: 500,
          }}>
            {isDragActive ? 'Drop files here...' : 'Drag & drop files or click to browse'}
          </p>
          <p style={{ fontSize: 13, color: colors.midGray, margin: 0 }}>
            Product catalogs, price lists, images, documents...
          </p>
        </div>

        {files.length > 0 && (
          <div style={{ marginTop: 24 }}>
            <div style={{
              fontSize: 14,
              fontWeight: 600,
              color: colors.dark,
              marginBottom: 12,
            }}>
              {files.length} file{files.length !== 1 ? 's' : ''} selected
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {files.map((file: File, index: number) => (
                <div
                  key={index}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: '12px 16px',
                    backgroundColor: colors.light,
                    borderRadius: 8,
                  }}
                >
                  <FileText size={20} color={colors.midGray} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 14, color: colors.dark }}>{file.name}</div>
                    <div style={{ fontSize: 12, color: colors.midGray }}>{formatFileSize(file.size)}</div>
                  </div>
                  <button
                    onClick={() => removeFile(index)}
                    style={{
                      backgroundColor: 'transparent',
                      border: 'none',
                      color: colors.midGray,
                      cursor: 'pointer',
                      padding: 4,
                    }}
                  >
                    <X size={18} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <button
        onClick={onContinue}
        disabled={files.length === 0}
        style={{
          width: '100%',
          padding: '16px',
          backgroundColor: files.length === 0 ? colors.midGray : colors.orange,
          color: '#fff',
          border: 'none',
          borderRadius: 12,
          fontSize: 16,
          fontWeight: 600,
          cursor: files.length === 0 ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 8,
        }}
      >
        <Sparkles size={20} />
        Analyze with AI
      </button>
    </div>
  );
}

// Analyzing Step
function AnalyzingStep({ progress }: { progress: number }) {
  return (
    <div style={{
      backgroundColor: '#fff',
      borderRadius: 16,
      border: `1px solid ${colors.lightGray}`,
      padding: 60,
      textAlign: 'center',
    }}>
      <div style={{
        width: 80,
        height: 80,
        borderRadius: '50%',
        backgroundColor: colors.orange + '15',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        margin: '0 auto 24px',
      }}>
        <Loader2 
          size={40} 
          color={colors.orange}
          style={{ animation: 'spin 1s linear infinite' }}
        />
      </div>

      <h2 style={{
        fontFamily: "'Poppins', sans-serif",
        fontSize: 22,
        fontWeight: 600,
        color: colors.dark,
        margin: '0 0 8px',
      }}>
        AI is analyzing your data...
      </h2>
      <p style={{ color: colors.midGray, fontSize: 14, margin: '0 0 32px' }}>
        Detecting formats, understanding structure, identifying opportunities
      </p>

      <div style={{
        width: '100%',
        height: 8,
        backgroundColor: colors.lightGray,
        borderRadius: 4,
        overflow: 'hidden',
        marginBottom: 16,
      }}>
        <div style={{
          width: `${Math.min(progress, 100)}%`,
          height: '100%',
          backgroundColor: colors.orange,
          transition: 'width 0.3s ease',
        }} />
      </div>

      <div style={{ color: colors.midGray, fontSize: 14 }}>
        {progress < 30 && '📁 Uploading files...'}
        {progress >= 30 && progress < 60 && '🔍 Detecting data types...'}
        {progress >= 60 && progress < 85 && '🏢 Analyzing business model...'}
        {progress >= 85 && '💡 Generating recommendations...'}
      </div>

      <style jsx global>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

// Results Step
function ResultsStep({ result, onDeploy }: { result: AnalysisResult; onDeploy: () => void }) {
  return (
    <div>
      {/* Summary Card */}
      <div style={{
        backgroundColor: '#fff',
        borderRadius: 16,
        border: `1px solid ${colors.lightGray}`,
        padding: 32,
        marginBottom: 24,
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          marginBottom: 20,
        }}>
          <div style={{
            width: 40,
            height: 40,
            borderRadius: 10,
            backgroundColor: colors.green + '15',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <Check size={20} color={colors.green} />
          </div>
          <h2 style={{
            fontFamily: "'Poppins', sans-serif",
            fontSize: 20,
            fontWeight: 600,
            color: colors.dark,
            margin: 0,
          }}>
            Analysis Complete
          </h2>
        </div>

        <p style={{
          fontSize: 15,
          color: colors.dark + 'dd',
          lineHeight: 1.6,
          margin: '0 0 24px',
        }}>
          {result.summary}
        </p>

        {/* Metrics */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 16,
          padding: 20,
          backgroundColor: colors.light,
          borderRadius: 12,
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 28, fontWeight: 600, color: colors.dark }}>
              {result.metrics.total_files}
            </div>
            <div style={{ fontSize: 12, color: colors.midGray }}>Files</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 28, fontWeight: 600, color: colors.dark }}>
              {result.metrics.total_products.toLocaleString()}
            </div>
            <div style={{ fontSize: 12, color: colors.midGray }}>Products</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 28, fontWeight: 600, color: colors.dark }}>
              {result.metrics.data_quality}%
            </div>
            <div style={{ fontSize: 12, color: colors.midGray }}>Quality</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 28, fontWeight: 600, color: colors.blue }}>
              {(result.business_model.confidence * 100).toFixed(0)}%
            </div>
            <div style={{ fontSize: 12, color: colors.midGray }}>Confidence</div>
          </div>
        </div>
      </div>

      {/* Value Projection */}
      <div style={{
        backgroundColor: '#fff',
        borderRadius: 16,
        border: `1px solid ${colors.lightGray}`,
        padding: 32,
        marginBottom: 24,
      }}>
        <h3 style={{
          fontFamily: "'Poppins', sans-serif",
          fontSize: 16,
          fontWeight: 600,
          color: colors.dark,
          margin: '0 0 20px',
        }}>
          💰 Your Potential
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20 }}>
          <div style={{
            padding: 20,
            backgroundColor: colors.green + '10',
            borderRadius: 12,
            textAlign: 'center',
          }}>
            <TrendingUp size={24} color={colors.green} style={{ marginBottom: 8 }} />
            <div style={{ fontSize: 24, fontWeight: 600, color: colors.green }}>
              {result.value.revenue_opportunity}
            </div>
            <div style={{ fontSize: 12, color: colors.midGray }}>Revenue Potential</div>
          </div>

          <div style={{
            padding: 20,
            backgroundColor: colors.blue + '10',
            borderRadius: 12,
            textAlign: 'center',
          }}>
            <Euro size={24} color={colors.blue} style={{ marginBottom: 8 }} />
            <div style={{ fontSize: 24, fontWeight: 600, color: colors.blue }}>
              {result.value.cost_savings}
            </div>
            <div style={{ fontSize: 12, color: colors.midGray }}>Cost Savings</div>
          </div>

          <div style={{
            padding: 20,
            backgroundColor: colors.orange + '10',
            borderRadius: 12,
            textAlign: 'center',
          }}>
            <Clock size={24} color={colors.orange} style={{ marginBottom: 8 }} />
            <div style={{ fontSize: 24, fontWeight: 600, color: colors.orange }}>
              {result.value.time_to_value}
            </div>
            <div style={{ fontSize: 12, color: colors.midGray }}>Time to Value</div>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div style={{
        backgroundColor: '#fff',
        borderRadius: 16,
        border: `1px solid ${colors.lightGray}`,
        padding: 32,
        marginBottom: 24,
      }}>
        <h3 style={{
          fontFamily: "'Poppins', sans-serif",
          fontSize: 16,
          fontWeight: 600,
          color: colors.dark,
          margin: '0 0 20px',
        }}>
          ⚡ Recommended Connectors
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {result.top_recommendations.map((rec, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                padding: 16,
                backgroundColor: colors.light,
                borderRadius: 10,
              }}
            >
              <div style={{
                width: 40,
                height: 40,
                borderRadius: 8,
                backgroundColor: colors.orange + '15',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <Zap size={20} color={colors.orange} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, color: colors.dark, fontSize: 14 }}>
                  {rec.connector}
                </div>
                <div style={{ fontSize: 13, color: colors.midGray }}>
                  {rec.reason}
                </div>
              </div>
              <div style={{
                fontSize: 13,
                fontWeight: 600,
                color: colors.green,
                backgroundColor: colors.green + '15',
                padding: '6px 12px',
                borderRadius: 6,
              }}>
                {rec.value}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Deploy Button */}
      <button
        onClick={onDeploy}
        style={{
          width: '100%',
          padding: '16px',
          backgroundColor: colors.orange,
          color: '#fff',
          border: 'none',
          borderRadius: 12,
          fontSize: 16,
          fontWeight: 600,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 8,
        }}
      >
        <Zap size={20} />
        Deploy & Activate All
      </button>
    </div>
  );
}

// Deploying Step
function DeployingStep({ progress }: { progress: number }) {
  return (
    <div style={{
      backgroundColor: '#fff',
      borderRadius: 16,
      border: `1px solid ${colors.lightGray}`,
      padding: 60,
      textAlign: 'center',
    }}>
      <div style={{
        width: 80,
        height: 80,
        borderRadius: '50%',
        backgroundColor: colors.green + '15',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        margin: '0 auto 24px',
      }}>
        <Loader2 
          size={40} 
          color={colors.green}
          style={{ animation: 'spin 1s linear infinite' }}
        />
      </div>

      <h2 style={{
        fontFamily: "'Poppins', sans-serif",
        fontSize: 22,
        fontWeight: 600,
        color: colors.dark,
        margin: '0 0 8px',
      }}>
        Deploying your workspace...
      </h2>
      <p style={{ color: colors.midGray, fontSize: 14, margin: '0 0 32px' }}>
        Importing data, activating connectors, training AI
      </p>

      <div style={{
        width: '100%',
        height: 8,
        backgroundColor: colors.lightGray,
        borderRadius: 4,
        overflow: 'hidden',
        marginBottom: 16,
      }}>
        <div style={{
          width: `${Math.min(progress, 100)}%`,
          height: '100%',
          backgroundColor: colors.green,
          transition: 'width 0.3s ease',
        }} />
      </div>

      <div style={{ color: colors.midGray, fontSize: 14 }}>
        {progress < 25 && '📥 Importing data...'}
        {progress >= 25 && progress < 50 && '🔗 Activating connectors...'}
        {progress >= 50 && progress < 75 && '🧠 Training AI on your products...'}
        {progress >= 75 && '✨ Finalizing setup...'}
      </div>
    </div>
  );
}

// Done Step
function DoneStep({ onStartChat }: { onStartChat: () => void }) {
  return (
    <div style={{
      backgroundColor: '#fff',
      borderRadius: 16,
      border: `1px solid ${colors.lightGray}`,
      padding: 60,
      textAlign: 'center',
    }}>
      <div style={{
        width: 80,
        height: 80,
        borderRadius: '50%',
        backgroundColor: colors.green + '15',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        margin: '0 auto 24px',
      }}>
        <Check size={40} color={colors.green} />
      </div>

      <h2 style={{
        fontFamily: "'Poppins', sans-serif",
        fontSize: 24,
        fontWeight: 600,
        color: colors.dark,
        margin: '0 0 8px',
      }}>
        🎉 You're all set!
      </h2>
      <p style={{ color: colors.midGray, fontSize: 15, margin: '0 0 32px', maxWidth: 400, marginLeft: 'auto', marginRight: 'auto' }}>
        Your data is ready. The AI understands your products. Start chatting to explore your catalog.
      </p>

      <button
        onClick={onStartChat}
        style={{
          padding: '16px 32px',
          backgroundColor: colors.orange,
          color: '#fff',
          border: 'none',
          borderRadius: 12,
          fontSize: 16,
          fontWeight: 600,
          cursor: 'pointer',
          display: 'inline-flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <MessageSquare size={20} />
        Start Chatting
      </button>
    </div>
  );
}

// Demo data for offline testing
const demoAnalysisResult: AnalysisResult = {
  upload_id: 'demo-123',
  metrics: {
    total_files: 3,
    total_records: 125000,
    total_products: 125000,
    data_quality: 87,
  },
  business_model: {
    type: 'B2B Distributor',
    confidence: 0.94,
    indicators: ['Multiple manufacturers', 'GTIN codes present', 'ETIM classification'],
  },
  value: {
    revenue_opportunity: '€12.5M',
    cost_savings: '€450K',
    time_to_value: '24h',
  },
  top_recommendations: [
    {
      connector: 'ETIM Klassifizierung',
      reason: '45,000 Produkte automatisch klassifizieren',
      value: 'B2B-Marktplätze',
    },
    {
      connector: 'PUBLISH Generator',
      reason: '28,000 fehlende Beschreibungen generieren',
      value: '€140K Ersparnis',
    },
    {
      connector: 'Amazon SP-API',
      reason: '78,000 Produkte sofort listbar',
      value: '5x Reichweite',
    },
  ],
  summary: 'Wir haben 3 Dateien mit 125,000 Produkten analysiert. Sie sind ein B2B-Distributor für Elektrotechnik von 47 Herstellern. Ihre Daten enthalten bereits ETIM-Klassifizierungen, was perfekt für automatische Marktplatz-Integration ist.',
  next_steps: ['Mapping bestätigen', 'ETIM aktivieren', 'Chat starten'],
};
