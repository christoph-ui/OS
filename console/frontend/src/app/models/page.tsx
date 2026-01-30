'use client';

import { useState, useEffect } from 'react';
import { Search, Download, Check, Cpu, HardDrive, Zap, Clock, ChevronDown } from 'lucide-react';

const colors = {
  dark: '#141413',
  light: '#faf9f5',
  midGray: '#b0aea5',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  blue: '#6a9bcc',
  green: '#788c5d',
};

interface Model {
  id: string;
  name: string;
  display_name: string;
  provider: string;
  description: string;
  size_gb: number;
  parameters: string;
  context_length: number;
  capabilities: string[];
  quantization: string;
  license: string;
  download_count: number;
  featured: boolean;
  installed: boolean;
  downloading?: boolean;
  progress?: number;
}

// Sample models (in production, fetch from API)
const sampleModels: Model[] = [
  {
    id: 'qwen2.5-72b',
    name: 'qwen2.5-72b-instruct',
    display_name: 'Qwen 2.5 72B',
    provider: 'Alibaba',
    description: 'Powerful multilingual model with excellent reasoning. Supports German and 28 other languages.',
    size_gb: 42,
    parameters: '72B',
    context_length: 131072,
    capabilities: ['chat', 'coding', 'reasoning', 'multilingual'],
    quantization: 'FP16',
    license: 'Apache 2.0',
    download_count: 125000,
    featured: true,
    installed: true,
  },
  {
    id: 'llama3.3-70b',
    name: 'llama3.3-70b-instruct',
    display_name: 'Llama 3.3 70B',
    provider: 'Meta',
    description: 'State-of-the-art open model with strong instruction following and tool use.',
    size_gb: 40,
    parameters: '70B',
    context_length: 128000,
    capabilities: ['chat', 'coding', 'tool_use'],
    quantization: 'FP16',
    license: 'Llama 3.3 Community',
    download_count: 890000,
    featured: true,
    installed: false,
  },
  {
    id: 'deepseek-r1-70b',
    name: 'deepseek-r1-distill-llama-70b',
    display_name: 'DeepSeek R1 70B',
    provider: 'DeepSeek',
    description: 'Reasoning-focused model with chain-of-thought capabilities. Excels at complex problem solving.',
    size_gb: 45,
    parameters: '70B',
    context_length: 64000,
    capabilities: ['reasoning', 'math', 'coding'],
    quantization: 'FP16',
    license: 'MIT',
    download_count: 450000,
    featured: true,
    installed: false,
  },
  {
    id: 'mistral-large-2',
    name: 'mistral-large-2',
    display_name: 'Mistral Large 2',
    provider: 'Mistral AI',
    description: 'Enterprise-grade model with 128K context. Excellent for document processing.',
    size_gb: 65,
    parameters: '123B',
    context_length: 128000,
    capabilities: ['chat', 'coding', 'documents'],
    quantization: 'FP16',
    license: 'Mistral Research',
    download_count: 180000,
    featured: false,
    installed: false,
  },
  {
    id: 'qwen2.5-coder-32b',
    name: 'qwen2.5-coder-32b-instruct',
    display_name: 'Qwen 2.5 Coder 32B',
    provider: 'Alibaba',
    description: 'Specialized coding model. Top performance on HumanEval and MBPP benchmarks.',
    size_gb: 18,
    parameters: '32B',
    context_length: 131072,
    capabilities: ['coding', 'debugging', 'code_review'],
    quantization: 'FP16',
    license: 'Apache 2.0',
    download_count: 320000,
    featured: false,
    installed: false,
  },
  {
    id: 'gemma2-27b',
    name: 'gemma-2-27b-it',
    display_name: 'Gemma 2 27B',
    provider: 'Google',
    description: 'Efficient and capable model from Google. Great balance of speed and quality.',
    size_gb: 16,
    parameters: '27B',
    context_length: 8192,
    capabilities: ['chat', 'summarization'],
    quantization: 'FP16',
    license: 'Gemma',
    download_count: 280000,
    featured: false,
    installed: false,
  },
];

export default function ModelsHub() {
  const [models, setModels] = useState<Model[]>(sampleModels);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCapability, setSelectedCapability] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [downloadProgress, setDownloadProgress] = useState<number>(0);

  const capabilities = ['chat', 'coding', 'reasoning', 'multilingual', 'tool_use', 'documents'];

  const filteredModels = models.filter(model => {
    const matchesSearch = !searchQuery ||
      model.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      model.provider.toLowerCase().includes(searchQuery.toLowerCase()) ||
      model.description.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesCapability = !selectedCapability ||
      model.capabilities.includes(selectedCapability);

    return matchesSearch && matchesCapability;
  });

  const handleDownload = async (modelId: string) => {
    setDownloadingId(modelId);
    setDownloadProgress(0);

    // Simulate download progress
    const interval = setInterval(() => {
      setDownloadProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setModels(models.map(m =>
            m.id === modelId ? { ...m, installed: true } : m
          ));
          setDownloadingId(null);
          return 0;
        }
        return prev + Math.random() * 15;
      });
    }, 500);
  };

  const handleUninstall = (modelId: string) => {
    setModels(models.map(m =>
      m.id === modelId ? { ...m, installed: false } : m
    ));
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: colors.light }}>
      {/* Header */}
      <div style={{
        backgroundColor: '#fff',
        borderBottom: `1px solid ${colors.lightGray}`,
        padding: '24px 40px',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
            <div>
              <h1 style={{
                fontFamily: "'Poppins', sans-serif",
                fontSize: 28,
                fontWeight: 600,
                color: colors.dark,
                margin: 0,
              }}>
                Models
              </h1>
              <p style={{ color: colors.midGray, margin: '4px 0 0', fontSize: 14 }}>
                Download and run AI models locally on your H200
              </p>
            </div>

            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              backgroundColor: colors.green + '15',
              color: colors.green,
              padding: '8px 16px',
              borderRadius: 8,
              fontSize: 13,
              fontWeight: 600,
            }}>
              <Cpu size={16} />
              8x H200 • 640GB VRAM
            </div>
          </div>

          {/* Search & Filters */}
          <div style={{ display: 'flex', gap: 16 }}>
            <div style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              backgroundColor: colors.light,
              border: `1px solid ${colors.lightGray}`,
              borderRadius: 10,
              padding: '12px 16px',
              maxWidth: 400,
            }}>
              <Search size={18} color={colors.midGray} />
              <input
                type="text"
                placeholder="Search models..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  flex: 1,
                  border: 'none',
                  backgroundColor: 'transparent',
                  fontSize: 15,
                  outline: 'none',
                  color: colors.dark,
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {capabilities.map(cap => (
                <button
                  key={cap}
                  onClick={() => setSelectedCapability(selectedCapability === cap ? null : cap)}
                  style={{
                    padding: '10px 16px',
                    backgroundColor: selectedCapability === cap ? colors.orange : '#fff',
                    color: selectedCapability === cap ? '#fff' : colors.dark,
                    border: `1px solid ${selectedCapability === cap ? colors.orange : colors.lightGray}`,
                    borderRadius: 8,
                    fontSize: 13,
                    fontWeight: 500,
                    cursor: 'pointer',
                    transition: 'all 0.15s',
                    textTransform: 'capitalize',
                  }}
                >
                  {cap.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Models List */}
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 40px' }}>
        {/* Installed Models */}
        {models.filter(m => m.installed).length > 0 && (
          <div style={{ marginBottom: 40 }}>
            <h2 style={{
              fontFamily: "'Poppins', sans-serif",
              fontSize: 16,
              fontWeight: 600,
              color: colors.dark,
              marginBottom: 16,
            }}>
              Installed Models
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {models.filter(m => m.installed).map(model => (
                <ModelCard
                  key={model.id}
                  model={model}
                  onDownload={handleDownload}
                  onUninstall={handleUninstall}
                  downloading={downloadingId === model.id}
                  progress={downloadingId === model.id ? downloadProgress : 0}
                />
              ))}
            </div>
          </div>
        )}

        {/* Available Models */}
        <div>
          <h2 style={{
            fontFamily: "'Poppins', sans-serif",
            fontSize: 16,
            fontWeight: 600,
            color: colors.dark,
            marginBottom: 16,
          }}>
            Available Models
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {filteredModels.filter(m => !m.installed).map(model => (
              <ModelCard
                key={model.id}
                model={model}
                onDownload={handleDownload}
                onUninstall={handleUninstall}
                downloading={downloadingId === model.id}
                progress={downloadingId === model.id ? downloadProgress : 0}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function ModelCard({
  model,
  onDownload,
  onUninstall,
  downloading,
  progress,
}: {
  model: Model;
  onDownload: (id: string) => void;
  onUninstall: (id: string) => void;
  downloading: boolean;
  progress: number;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div style={{
      backgroundColor: '#fff',
      borderRadius: 12,
      border: `1px solid ${model.installed ? colors.green + '40' : colors.lightGray}`,
      overflow: 'hidden',
      transition: 'all 0.2s',
    }}>
      {/* Main Row */}
      <div
        style={{
          padding: '20px 24px',
          display: 'flex',
          alignItems: 'center',
          gap: 20,
          cursor: 'pointer',
        }}
        onClick={() => setExpanded(!expanded)}
      >
        {/* Icon */}
        <div style={{
          width: 52,
          height: 52,
          borderRadius: 10,
          backgroundColor: model.installed ? colors.green + '15' : colors.dark + '08',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}>
          <Cpu size={24} color={model.installed ? colors.green : colors.dark} />
        </div>

        {/* Info */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h3 style={{
              fontFamily: "'Poppins', sans-serif",
              fontSize: 17,
              fontWeight: 600,
              color: colors.dark,
              margin: 0,
            }}>
              {model.display_name}
            </h3>
            <span style={{
              fontSize: 12,
              color: colors.midGray,
              backgroundColor: colors.light,
              padding: '2px 8px',
              borderRadius: 4,
            }}>
              {model.provider}
            </span>
            {model.featured && (
              <span style={{
                fontSize: 10,
                fontWeight: 600,
                color: colors.orange,
                backgroundColor: colors.orange + '15',
                padding: '2px 8px',
                borderRadius: 4,
              }}>
                FEATURED
              </span>
            )}
          </div>
          <p style={{
            fontSize: 13,
            color: colors.midGray,
            margin: '6px 0 0',
            lineHeight: 1.4,
          }}>
            {model.description}
          </p>
        </div>

        {/* Stats */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 24,
          flexShrink: 0,
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 15, fontWeight: 600, color: colors.dark }}>
              {model.parameters}
            </div>
            <div style={{ fontSize: 11, color: colors.midGray }}>params</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 15, fontWeight: 600, color: colors.dark }}>
              {model.size_gb}GB
            </div>
            <div style={{ fontSize: 11, color: colors.midGray }}>size</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 15, fontWeight: 600, color: colors.dark }}>
              {(model.context_length / 1000).toFixed(0)}K
            </div>
            <div style={{ fontSize: 11, color: colors.midGray }}>context</div>
          </div>
        </div>

        {/* Action Button */}
        <div style={{ flexShrink: 0 }} onClick={(e) => e.stopPropagation()}>
          {downloading ? (
            <div style={{
              width: 140,
              height: 40,
              backgroundColor: colors.light,
              borderRadius: 8,
              overflow: 'hidden',
              position: 'relative',
            }}>
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                height: '100%',
                width: `${Math.min(progress, 100)}%`,
                backgroundColor: colors.orange + '30',
                transition: 'width 0.3s',
              }} />
              <div style={{
                position: 'relative',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 13,
                fontWeight: 600,
                color: colors.orange,
              }}>
                {Math.min(Math.round(progress), 100)}%
              </div>
            </div>
          ) : model.installed ? (
            <button
              onClick={() => onUninstall(model.id)}
              style={{
                padding: '10px 20px',
                backgroundColor: colors.green + '15',
                color: colors.green,
                border: 'none',
                borderRadius: 8,
                fontSize: 14,
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                minWidth: 120,
                justifyContent: 'center',
              }}
            >
              <Check size={16} />
              Installed
            </button>
          ) : (
            <button
              onClick={() => onDownload(model.id)}
              style={{
                padding: '10px 20px',
                backgroundColor: colors.orange,
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                fontSize: 14,
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                minWidth: 120,
                justifyContent: 'center',
                transition: 'all 0.15s',
              }}
            >
              <Download size={16} />
              Pull
            </button>
          )}
        </div>

        {/* Expand Arrow */}
        <ChevronDown
          size={20}
          color={colors.midGray}
          style={{
            transform: expanded ? 'rotate(180deg)' : 'rotate(0)',
            transition: 'transform 0.2s',
          }}
        />
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div style={{
          padding: '0 24px 24px',
          borderTop: `1px solid ${colors.lightGray}`,
          marginTop: -1,
          paddingTop: 20,
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 20 }}>
            <div>
              <div style={{ fontSize: 12, color: colors.midGray, marginBottom: 4 }}>Model ID</div>
              <div style={{ fontSize: 13, color: colors.dark, fontFamily: 'monospace' }}>{model.name}</div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: colors.midGray, marginBottom: 4 }}>Quantization</div>
              <div style={{ fontSize: 13, color: colors.dark }}>{model.quantization}</div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: colors.midGray, marginBottom: 4 }}>License</div>
              <div style={{ fontSize: 13, color: colors.dark }}>{model.license}</div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: colors.midGray, marginBottom: 4 }}>Downloads</div>
              <div style={{ fontSize: 13, color: colors.dark }}>{model.download_count.toLocaleString()}</div>
            </div>
          </div>

          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 12, color: colors.midGray, marginBottom: 8 }}>Capabilities</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {model.capabilities.map(cap => (
                <span
                  key={cap}
                  style={{
                    fontSize: 12,
                    color: colors.dark,
                    backgroundColor: colors.light,
                    padding: '4px 12px',
                    borderRadius: 6,
                    textTransform: 'capitalize',
                  }}
                >
                  {cap.replace('_', ' ')}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
