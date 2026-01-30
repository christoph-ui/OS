'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { colors } from '@/lib/theme';
import { 
  Building2, Upload, Puzzle, Link, Cog, Check, 
  ArrowRight, ArrowLeft, ChevronRight
} from 'lucide-react';

const steps = [
  { id: 1, title: 'Welcome', icon: Building2, description: 'Company information' },
  { id: 2, title: 'Company', icon: Building2, description: 'Business details' },
  { id: 3, title: 'Data Upload', icon: Upload, description: 'Import your files' },
  { id: 4, title: 'MCPs', icon: Puzzle, description: 'Choose AI modules' },
  { id: 5, title: 'Connectors', icon: Link, description: 'Connect channels' },
  { id: 6, title: 'Configure', icon: Cog, description: 'Final settings' },
  { id: 7, title: 'Complete', icon: Check, description: 'Ready to go!' },
];

export default function GuidedOnboarding() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    companyName: '',
    industry: '',
    companySize: '',
    country: 'Germany',
    files: [] as File[],
    selectedMcps: [] as string[],
    selectedConnectors: [] as string[],
  });

  const handleNext = () => {
    if (currentStep < 7) {
      setCurrentStep(currentStep + 1);
    } else {
      router.push('/dashboard');
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: colors.light,
      fontFamily: "'Inter', -apple-system, sans-serif",
    }}>
      {/* Header */}
      <div style={{
        backgroundColor: 'white',
        borderBottom: `1px solid ${colors.lightGray}`,
        padding: '20px 40px',
      }}>
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h1 style={{
                fontSize: 20,
                fontWeight: 600,
                color: colors.dark,
                margin: 0,
                fontFamily: "'Poppins', sans-serif",
              }}>
                <span style={{ color: colors.orange }}>0711</span> Setup Wizard
              </h1>
              <p style={{ fontSize: 13, color: colors.midGray, margin: '4px 0 0' }}>
                Step {currentStep} of 7 — {steps[currentStep - 1].description}
              </p>
            </div>
            <button
              onClick={() => router.push('/onboarding')}
              style={{
                padding: '8px 16px',
                backgroundColor: 'transparent',
                border: `1px solid ${colors.lightGray}`,
                borderRadius: 8,
                fontSize: 13,
                color: colors.midGray,
                cursor: 'pointer',
              }}
            >
              Switch to Quick Setup
            </button>
          </div>
        </div>
      </div>

      {/* Progress Steps */}
      <div style={{
        backgroundColor: 'white',
        borderBottom: `1px solid ${colors.lightGray}`,
        padding: '16px 40px',
      }}>
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            {steps.map((step, i) => (
              <React.Fragment key={step.id}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '8px 12px',
                    backgroundColor: currentStep === step.id 
                      ? colors.orange + '15' 
                      : currentStep > step.id 
                        ? colors.orange + '08'
                        : 'transparent',
                    borderRadius: 8,
                    cursor: step.id < currentStep ? 'pointer' : 'default',
                  }}
                  onClick={() => step.id < currentStep && setCurrentStep(step.id)}
                >
                  <div style={{
                    width: 24,
                    height: 24,
                    borderRadius: '50%',
                    backgroundColor: currentStep >= step.id ? colors.orange : colors.lightGray,
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 12,
                    fontWeight: 600,
                  }}>
                    {currentStep > step.id ? <Check size={14} /> : step.id}
                  </div>
                  <span style={{
                    fontSize: 13,
                    fontWeight: currentStep === step.id ? 600 : 400,
                    color: currentStep === step.id ? colors.orange : colors.midGray,
                  }}>
                    {step.title}
                  </span>
                </div>
                {i < steps.length - 1 && (
                  <ChevronRight size={14} color={colors.lightGray} />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div style={{ padding: '40px', maxWidth: 800, margin: '0 auto' }}>
        <div style={{
          backgroundColor: 'white',
          borderRadius: 16,
          border: `1px solid ${colors.lightGray}`,
          padding: 40,
          minHeight: 400,
        }}>
          {/* Step Content */}
          {currentStep === 1 && (
            <WelcomeStep />
          )}
          {currentStep === 2 && (
            <CompanyStep formData={formData} setFormData={setFormData} />
          )}
          {currentStep === 3 && (
            <UploadStep formData={formData} setFormData={setFormData} />
          )}
          {currentStep === 4 && (
            <MCPStep formData={formData} setFormData={setFormData} />
          )}
          {currentStep === 5 && (
            <ConnectorStep formData={formData} setFormData={setFormData} />
          )}
          {currentStep === 6 && (
            <ConfigureStep formData={formData} />
          )}
          {currentStep === 7 && (
            <CompleteStep />
          )}
        </div>

        {/* Navigation */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: 24,
        }}>
          <button
            onClick={handleBack}
            disabled={currentStep === 1}
            style={{
              padding: '12px 24px',
              backgroundColor: 'white',
              border: `1px solid ${colors.lightGray}`,
              borderRadius: 10,
              fontSize: 14,
              fontWeight: 500,
              color: currentStep === 1 ? colors.lightGray : colors.dark,
              cursor: currentStep === 1 ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <ArrowLeft size={16} /> Back
          </button>

          <button
            onClick={handleNext}
            style={{
              padding: '12px 24px',
              backgroundColor: colors.orange,
              border: 'none',
              borderRadius: 10,
              fontSize: 14,
              fontWeight: 600,
              color: 'white',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            {currentStep === 7 ? 'Go to Dashboard' : 'Continue'} <ArrowRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}

// Step Components
function WelcomeStep() {
  return (
    <div style={{ textAlign: 'center', padding: '40px 0' }}>
      <div style={{
        fontSize: 64,
        marginBottom: 24,
      }}>
        👋
      </div>
      <h2 style={{
        fontSize: 28,
        fontWeight: 600,
        color: colors.dark,
        margin: '0 0 16px',
        fontFamily: "'Poppins', sans-serif",
      }}>
        Welcome to 0711
      </h2>
      <p style={{
        fontSize: 16,
        color: colors.midGray,
        lineHeight: 1.6,
        maxWidth: 500,
        margin: '0 auto',
      }}>
        We'll guide you through setting up your product intelligence platform. 
        This takes about 15 minutes and you can always change settings later.
      </p>
    </div>
  );
}

function CompanyStep({ formData, setFormData }: any) {
  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 600, color: colors.dark, margin: '0 0 24px' }}>
        Tell us about your company
      </h2>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        <div>
          <label style={{ display: 'block', fontSize: 14, fontWeight: 500, color: colors.dark, marginBottom: 8 }}>
            Company Name
          </label>
          <input
            type="text"
            value={formData.companyName}
            onChange={(e) => setFormData({ ...formData, companyName: e.target.value })}
            placeholder="Acme GmbH"
            style={{
              width: '100%',
              padding: '12px 16px',
              border: `1px solid ${colors.lightGray}`,
              borderRadius: 8,
              fontSize: 14,
              outline: 'none',
            }}
          />
        </div>
        
        <div>
          <label style={{ display: 'block', fontSize: 14, fontWeight: 500, color: colors.dark, marginBottom: 8 }}>
            Industry
          </label>
          <select
            value={formData.industry}
            onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
            style={{
              width: '100%',
              padding: '12px 16px',
              border: `1px solid ${colors.lightGray}`,
              borderRadius: 8,
              fontSize: 14,
              outline: 'none',
              backgroundColor: 'white',
            }}
          >
            <option value="">Select industry...</option>
            <option value="elektro">Elektrotechnik</option>
            <option value="sanitaer">Sanitär / Heizung</option>
            <option value="werkzeug">Werkzeug / Befestigung</option>
            <option value="bau">Baustoffe</option>
            <option value="other">Andere</option>
          </select>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: 14, fontWeight: 500, color: colors.dark, marginBottom: 8 }}>
            Company Size
          </label>
          <select
            value={formData.companySize}
            onChange={(e) => setFormData({ ...formData, companySize: e.target.value })}
            style={{
              width: '100%',
              padding: '12px 16px',
              border: `1px solid ${colors.lightGray}`,
              borderRadius: 8,
              fontSize: 14,
              outline: 'none',
              backgroundColor: 'white',
            }}
          >
            <option value="">Select size...</option>
            <option value="1-10">1-10 employees</option>
            <option value="11-50">11-50 employees</option>
            <option value="51-200">51-200 employees</option>
            <option value="200+">200+ employees</option>
          </select>
        </div>
      </div>
    </div>
  );
}

function UploadStep({ formData, setFormData }: any) {
  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 600, color: colors.dark, margin: '0 0 8px' }}>
        Upload your product data
      </h2>
      <p style={{ fontSize: 14, color: colors.midGray, margin: '0 0 24px' }}>
        Supported formats: BMECat, ETIM, DATANORM, CSV, Excel, JSON, XML
      </p>
      
      <div style={{
        border: `2px dashed ${colors.lightGray}`,
        borderRadius: 12,
        padding: 60,
        textAlign: 'center',
        backgroundColor: colors.light,
      }}>
        <Upload size={48} color={colors.midGray} style={{ marginBottom: 16 }} />
        <p style={{ fontSize: 16, color: colors.dark, margin: '0 0 8px' }}>
          Drag & drop files or click to browse
        </p>
        <p style={{ fontSize: 13, color: colors.midGray, margin: 0 }}>
          Product catalogs, price lists, images...
        </p>
      </div>
    </div>
  );
}

function MCPStep({ formData, setFormData }: any) {
  const mcps = [
    { id: 'etim', name: 'ETIM Klassifizierung', description: 'Automatische Produktklassifizierung' },
    { id: 'publish', name: 'PUBLISH', description: 'KI-Texte & Beschreibungen' },
    { id: 'price', name: 'PRICE Monitor', description: 'Preisüberwachung & Optimierung' },
    { id: 'tender', name: 'TENDER', description: 'Ausschreibungsassistent' },
  ];

  const toggleMcp = (id: string) => {
    const selected = formData.selectedMcps.includes(id)
      ? formData.selectedMcps.filter((m: string) => m !== id)
      : [...formData.selectedMcps, id];
    setFormData({ ...formData, selectedMcps: selected });
  };

  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 600, color: colors.dark, margin: '0 0 8px' }}>
        Choose AI Modules (MCPs)
      </h2>
      <p style={{ fontSize: 14, color: colors.midGray, margin: '0 0 24px' }}>
        Select the AI capabilities you want to use
      </p>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {mcps.map((mcp) => (
          <button
            key={mcp.id}
            onClick={() => toggleMcp(mcp.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              padding: 16,
              border: `2px solid ${formData.selectedMcps.includes(mcp.id) ? colors.orange : colors.lightGray}`,
              borderRadius: 10,
              backgroundColor: formData.selectedMcps.includes(mcp.id) ? colors.orange + '08' : 'white',
              cursor: 'pointer',
              textAlign: 'left',
            }}
          >
            <div style={{
              width: 24,
              height: 24,
              borderRadius: 6,
              border: `2px solid ${formData.selectedMcps.includes(mcp.id) ? colors.orange : colors.lightGray}`,
              backgroundColor: formData.selectedMcps.includes(mcp.id) ? colors.orange : 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              {formData.selectedMcps.includes(mcp.id) && <Check size={14} color="white" />}
            </div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 600, color: colors.dark }}>{mcp.name}</div>
              <div style={{ fontSize: 13, color: colors.midGray }}>{mcp.description}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function ConnectorStep({ formData, setFormData }: any) {
  const connectors = [
    { id: 'amazon', name: 'Amazon SP-API', description: 'Verkaufen auf Amazon' },
    { id: 'ebay', name: 'eBay', description: 'eBay Marketplace' },
    { id: 'shopify', name: 'Shopify', description: 'Eigener Online-Shop' },
    { id: 'datanorm', name: 'DATANORM Export', description: 'B2B Katalogexport' },
  ];

  const toggleConnector = (id: string) => {
    const selected = formData.selectedConnectors.includes(id)
      ? formData.selectedConnectors.filter((c: string) => c !== id)
      : [...formData.selectedConnectors, id];
    setFormData({ ...formData, selectedConnectors: selected });
  };

  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 600, color: colors.dark, margin: '0 0 8px' }}>
        Connect your channels
      </h2>
      <p style={{ fontSize: 14, color: colors.midGray, margin: '0 0 24px' }}>
        Where do you want to publish your products?
      </p>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
        {connectors.map((connector) => (
          <button
            key={connector.id}
            onClick={() => toggleConnector(connector.id)}
            style={{
              padding: 16,
              border: `2px solid ${formData.selectedConnectors.includes(connector.id) ? colors.orange : colors.lightGray}`,
              borderRadius: 10,
              backgroundColor: formData.selectedConnectors.includes(connector.id) ? colors.orange + '08' : 'white',
              cursor: 'pointer',
              textAlign: 'left',
            }}
          >
            <div style={{ fontSize: 15, fontWeight: 600, color: colors.dark }}>{connector.name}</div>
            <div style={{ fontSize: 13, color: colors.midGray }}>{connector.description}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

function ConfigureStep({ formData }: any) {
  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 600, color: colors.dark, margin: '0 0 24px' }}>
        Review your setup
      </h2>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div style={{ padding: 16, backgroundColor: colors.light, borderRadius: 10 }}>
          <div style={{ fontSize: 13, color: colors.midGray, marginBottom: 4 }}>Company</div>
          <div style={{ fontSize: 15, fontWeight: 500, color: colors.dark }}>
            {formData.companyName || 'Not set'}
          </div>
        </div>
        
        <div style={{ padding: 16, backgroundColor: colors.light, borderRadius: 10 }}>
          <div style={{ fontSize: 13, color: colors.midGray, marginBottom: 4 }}>AI Modules</div>
          <div style={{ fontSize: 15, fontWeight: 500, color: colors.dark }}>
            {formData.selectedMcps.length > 0 ? formData.selectedMcps.join(', ') : 'None selected'}
          </div>
        </div>
        
        <div style={{ padding: 16, backgroundColor: colors.light, borderRadius: 10 }}>
          <div style={{ fontSize: 13, color: colors.midGray, marginBottom: 4 }}>Connectors</div>
          <div style={{ fontSize: 15, fontWeight: 500, color: colors.dark }}>
            {formData.selectedConnectors.length > 0 ? formData.selectedConnectors.join(', ') : 'None selected'}
          </div>
        </div>
      </div>
    </div>
  );
}

function CompleteStep() {
  return (
    <div style={{ textAlign: 'center', padding: '40px 0' }}>
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
        <Check size={40} color={colors.orange} />
      </div>
      <h2 style={{
        fontSize: 28,
        fontWeight: 600,
        color: colors.dark,
        margin: '0 0 16px',
        fontFamily: "'Poppins', sans-serif",
      }}>
        🎉 You're all set!
      </h2>
      <p style={{
        fontSize: 16,
        color: colors.midGray,
        lineHeight: 1.6,
        maxWidth: 400,
        margin: '0 auto',
      }}>
        Your workspace is ready. Click continue to go to your dashboard and start exploring.
      </p>
    </div>
  );
}
