'use client';

import React, { useState } from 'react';

// ============================================================================
// EXPERT SIGNUP WIZARD COMPONENT
// ============================================================================

const theme = {
  colors: {
    dark: '#141413',
    light: '#faf9f5',
    midGray: '#b0aea5',
    lightGray: '#e8e6dc',
    orange: '#d97757',
    blue: '#6a9bcc',
    green: '#788c5d',
    red: '#c75a5a',
    purple: '#8b7fc7',
  }
};

// MCP Catalog (same as dashboard)
const MCP_CATALOG = {
  CTAX: {
    id: 'CTAX',
    name: 'German Tax Engine',
    category: 'Finance',
    icon: '📊',
    color: theme.colors.orange,
    description: 'Full German tax calculation, ELSTER filing, audit preparation',
    requiredCerts: ['Steuerberater (StB)', 'Certified Tax Advisor'],
    avgRate: 4200,
  },
  FPA: {
    id: 'FPA',
    name: 'FP&A Automation',
    category: 'Finance',
    icon: '📈',
    color: theme.colors.blue,
    description: 'Financial planning, forecasting, variance analysis',
    requiredCerts: ['CFA', 'CPA', 'Finance Degree'],
    avgRate: 3800,
  },
  TENDER: {
    id: 'TENDER',
    name: 'Tender Engine',
    category: 'Sales',
    icon: '📋',
    color: theme.colors.green,
    description: 'RFP/RFQ processing, bid management, proposal generation',
    requiredCerts: ['Sales Certification', 'Business Degree'],
    avgRate: 3500,
  },
  LEGAL: {
    id: 'LEGAL',
    name: 'Legal Intelligence',
    category: 'Legal',
    icon: '⚖️',
    color: theme.colors.dark,
    description: 'Contract analysis, compliance, risk assessment',
    requiredCerts: ['Rechtsanwalt (RA)', 'Bar Admission'],
    avgRate: 4500,
  },
  ETIM: {
    id: 'ETIM',
    name: 'Product Classification',
    category: 'Product',
    icon: '🏷️',
    color: '#5ab5b5',
    description: 'ETIM/ECLASS classification, product data enrichment',
    requiredCerts: ['ETIM Certification', 'Product Management'],
    avgRate: 3200,
  },
};

interface SignupData {
  // Step 1: Basic Info
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  headline: string;
  linkedIn: string;
  referralCode: string;

  // Step 2: MCP Expertise
  selectedMcps: Array<{
    mcpId: string;
    proficiency: 'beginner' | 'intermediate' | 'expert';
  }>;

  // Step 3: Experience
  yearsExperience: number;
  previousClients: string;
  toolsProficiency: string[];
  languages: string[];
  industries: string[];

  // Step 4: Availability
  maxClients: number;
  preferredClientSize: string[];
  hourlyRateExpectation: number;
  weeklyAvailability: number;

  // Step 5: Verification
  certifications: File[];
  idDocument: File | null;
  taxId: string;
  iban: string;
  bic: string;

  // Step 6: Agreement
  termsAccepted: boolean;
  dataProcessingAccepted: boolean;
}

const ExpertSignupWizard: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<SignupData>({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    headline: '',
    linkedIn: '',
    referralCode: '',
    selectedMcps: [],
    yearsExperience: 0,
    previousClients: '',
    toolsProficiency: [],
    languages: ['German'],
    industries: [],
    maxClients: 10,
    preferredClientSize: [],
    hourlyRateExpectation: 0,
    weeklyAvailability: 20,
    certifications: [],
    idDocument: null,
    taxId: '',
    iban: '',
    bic: '',
    termsAccepted: false,
    dataProcessingAccepted: false,
  });

  const totalSteps = 6;

  const updateFormData = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const nextStep = () => {
    if (currentStep < totalSteps) setCurrentStep(currentStep + 1);
  };

  const prevStep = () => {
    if (currentStep > 1) setCurrentStep(currentStep - 1);
  };

  const handleSubmit = async () => {
    // TODO: Submit to API
    console.log('Submitting application:', formData);
    alert('Application submitted! We\'ll review it within 2-5 business days.');
  };

  // ============================================================================
  // STEP 1: BASIC INFORMATION
  // ============================================================================
  const Step1BasicInfo = () => (
    <div>
      <h2 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '24px', fontWeight: 600, marginBottom: '8px' }}>
        Let's get to know you
      </h2>
      <p style={{ color: theme.colors.midGray, marginBottom: '32px' }}>
        Tell us about yourself and your professional background
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
            First Name *
          </label>
          <input
            type="text"
            value={formData.firstName}
            onChange={(e) => updateFormData('firstName', e.target.value)}
            placeholder="Sarah"
            style={{
              width: '100%',
              padding: '12px 16px',
              borderRadius: '12px',
              border: `1px solid ${theme.colors.lightGray}`,
              fontFamily: "'Lora', serif",
              fontSize: '14px',
            }}
          />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
            Last Name *
          </label>
          <input
            type="text"
            value={formData.lastName}
            onChange={(e) => updateFormData('lastName', e.target.value)}
            placeholder="Müller"
            style={{
              width: '100%',
              padding: '12px 16px',
              borderRadius: '12px',
              border: `1px solid ${theme.colors.lightGray}`,
              fontFamily: "'Lora', serif",
              fontSize: '14px',
            }}
          />
        </div>
      </div>

      <div style={{ marginBottom: '16px' }}>
        <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
          Email Address *
        </label>
        <input
          type="email"
          value={formData.email}
          onChange={(e) => updateFormData('email', e.target.value)}
          placeholder="sarah.mueller@example.com"
          style={{
            width: '100%',
            padding: '12px 16px',
            borderRadius: '12px',
            border: `1px solid ${theme.colors.lightGray}`,
            fontFamily: "'Lora', serif",
            fontSize: '14px',
          }}
        />
      </div>

      <div style={{ marginBottom: '16px' }}>
        <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
          Phone Number *
        </label>
        <input
          type="tel"
          value={formData.phone}
          onChange={(e) => updateFormData('phone', e.target.value)}
          placeholder="+49 170 1234567"
          style={{
            width: '100%',
            padding: '12px 16px',
            borderRadius: '12px',
            border: `1px solid ${theme.colors.lightGray}`,
            fontFamily: "'Lora', serif",
            fontSize: '14px',
          }}
        />
      </div>

      <div style={{ marginBottom: '16px' }}>
        <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
          Professional Headline *
        </label>
        <input
          type="text"
          value={formData.headline}
          onChange={(e) => updateFormData('headline', e.target.value)}
          placeholder="e.g., Senior Tax Specialist | 10+ years in German Corporate Tax"
          style={{
            width: '100%',
            padding: '12px 16px',
            borderRadius: '12px',
            border: `1px solid ${theme.colors.lightGray}`,
            fontFamily: "'Lora', serif",
            fontSize: '14px',
          }}
        />
        <p style={{ fontSize: '12px', color: theme.colors.midGray, marginTop: '6px' }}>
          This will appear on your profile and in search results
        </p>
      </div>

      <div style={{ marginBottom: '16px' }}>
        <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
          LinkedIn Profile (Optional)
        </label>
        <input
          type="url"
          value={formData.linkedIn}
          onChange={(e) => updateFormData('linkedIn', e.target.value)}
          placeholder="https://linkedin.com/in/..."
          style={{
            width: '100%',
            padding: '12px 16px',
            borderRadius: '12px',
            border: `1px solid ${theme.colors.lightGray}`,
            fontFamily: "'Lora', serif",
            fontSize: '14px',
          }}
        />
      </div>

      <div style={{ marginBottom: '16px' }}>
        <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
          Referral Code (Optional)
        </label>
        <input
          type="text"
          value={formData.referralCode}
          onChange={(e) => updateFormData('referralCode', e.target.value)}
          placeholder="Enter code if referred by existing expert"
          style={{
            width: '100%',
            padding: '12px 16px',
            borderRadius: '12px',
            border: `1px solid ${theme.colors.lightGray}`,
            fontFamily: "'Lora', serif",
            fontSize: '14px',
          }}
        />
      </div>
    </div>
  );

  // ============================================================================
  // STEP 2: MCP EXPERTISE
  // ============================================================================
  const Step2McpExpertise = () => {
    const toggleMcp = (mcpId: string) => {
      const existing = formData.selectedMcps.find(m => m.mcpId === mcpId);
      if (existing) {
        updateFormData('selectedMcps', formData.selectedMcps.filter(m => m.mcpId !== mcpId));
      } else {
        updateFormData('selectedMcps', [
          ...formData.selectedMcps,
          { mcpId, proficiency: 'intermediate' }
        ]);
      }
    };

    const updateProficiency = (mcpId: string, proficiency: 'beginner' | 'intermediate' | 'expert') => {
      updateFormData('selectedMcps', formData.selectedMcps.map(m =>
        m.mcpId === mcpId ? { ...m, proficiency } : m
      ));
    };

    const categories = [...new Set(Object.values(MCP_CATALOG).map(m => m.category))];

    return (
      <div>
        <h2 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '24px', fontWeight: 600, marginBottom: '8px' }}>
          Select your MCP expertise
        </h2>
        <p style={{ color: theme.colors.midGray, marginBottom: '32px' }}>
          Choose 1-3 Model Context Protocols you're qualified to operate. You can add more later.
        </p>

        {categories.map(category => (
          <div key={category} style={{ marginBottom: '32px' }}>
            <h3 style={{
              fontFamily: "'Poppins', sans-serif",
              fontSize: '16px',
              fontWeight: 500,
              color: theme.colors.midGray,
              marginBottom: '16px',
            }}>
              {category}
            </h3>
            <div style={{ display: 'grid', gap: '16px' }}>
              {Object.values(MCP_CATALOG)
                .filter(mcp => mcp.category === category)
                .map(mcp => {
                  const isSelected = formData.selectedMcps.some(m => m.mcpId === mcp.id);
                  const selectedMcp = formData.selectedMcps.find(m => m.mcpId === mcp.id);

                  return (
                    <div
                      key={mcp.id}
                      style={{
                        padding: '20px',
                        borderRadius: '16px',
                        border: isSelected ? `2px solid ${mcp.color}` : `1px solid ${theme.colors.lightGray}`,
                        background: isSelected ? `${mcp.color}05` : 'white',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                      }}
                      onClick={() => toggleMcp(mcp.id)}
                    >
                      <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
                        <div style={{
                          width: '56px',
                          height: '56px',
                          borderRadius: '12px',
                          background: `${mcp.color}15`,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '28px',
                          flexShrink: 0,
                        }}>
                          {mcp.icon}
                        </div>
                        <div style={{ flex: 1 }}>
                          <h4 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '16px', fontWeight: 600, marginBottom: '4px' }}>
                            {mcp.name}
                          </h4>
                          <p style={{ fontSize: '13px', color: theme.colors.midGray, marginBottom: '12px' }}>
                            {mcp.description}
                          </p>
                          <p style={{ fontSize: '12px', color: theme.colors.midGray }}>
                            💰 Avg. rate: €{mcp.avgRate.toLocaleString()}/month per client
                          </p>
                          <p style={{ fontSize: '12px', color: theme.colors.midGray, marginTop: '4px' }}>
                            📜 Preferred: {mcp.requiredCerts.join(', ')}
                          </p>

                          {isSelected && (
                            <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: `1px solid ${theme.colors.lightGray}` }}>
                              <p style={{ fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
                                Your proficiency level:
                              </p>
                              <div style={{ display: 'flex', gap: '8px' }}>
                                {['beginner', 'intermediate', 'expert'].map(level => (
                                  <button
                                    key={level}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      updateProficiency(mcp.id, level as any);
                                    }}
                                    style={{
                                      padding: '8px 16px',
                                      borderRadius: '8px',
                                      border: 'none',
                                      background: selectedMcp?.proficiency === level ? mcp.color : theme.colors.lightGray,
                                      color: selectedMcp?.proficiency === level ? 'white' : theme.colors.dark,
                                      fontFamily: "'Poppins', sans-serif",
                                      fontSize: '12px',
                                      fontWeight: 500,
                                      cursor: 'pointer',
                                      textTransform: 'capitalize',
                                    }}
                                  >
                                    {level}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                        <div style={{
                          width: '24px',
                          height: '24px',
                          borderRadius: '6px',
                          border: `2px solid ${isSelected ? mcp.color : theme.colors.lightGray}`,
                          background: isSelected ? mcp.color : 'white',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'white',
                          fontSize: '14px',
                          fontWeight: 'bold',
                        }}>
                          {isSelected && '✓'}
                        </div>
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        ))}

        {formData.selectedMcps.length > 0 && (
          <div style={{
            padding: '20px',
            borderRadius: '16px',
            background: `${theme.colors.green}10`,
            border: `1px solid ${theme.colors.green}`,
          }}>
            <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '14px', fontWeight: 500, marginBottom: '8px' }}>
              ✓ {formData.selectedMcps.length} MCP{formData.selectedMcps.length > 1 ? 's' : ''} selected
            </p>
            <p style={{ fontSize: '13px', color: theme.colors.midGray }}>
              Potential earnings: €{Math.round(formData.selectedMcps.reduce((sum, m) => {
                const mcp = MCP_CATALOG[m.mcpId as keyof typeof MCP_CATALOG];
                return sum + (mcp?.avgRate || 0);
              }, 0) * 0.9 * formData.maxClients / formData.selectedMcps.length).toLocaleString()}/month
              ({formData.maxClients} clients max)
            </p>
          </div>
        )}
      </div>
    );
  };

  // ============================================================================
  // STEP 3: EXPERIENCE
  // ============================================================================
  const Step3Experience = () => (
    <div>
      <h2 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '24px', fontWeight: 600, marginBottom: '8px' }}>
        Tell us about your experience
      </h2>
      <p style={{ color: theme.colors.midGray, marginBottom: '32px' }}>
        Help us understand your background and qualifications
      </p>

      <div style={{ marginBottom: '24px' }}>
        <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
          Years of Professional Experience *
        </label>
        <input
          type="number"
          value={formData.yearsExperience || ''}
          onChange={(e) => updateFormData('yearsExperience', parseInt(e.target.value))}
          placeholder="10"
          min="0"
          max="50"
          style={{
            width: '100%',
            padding: '12px 16px',
            borderRadius: '12px',
            border: `1px solid ${theme.colors.lightGray}`,
            fontFamily: "'Lora', serif",
            fontSize: '14px',
          }}
        />
      </div>

      <div style={{ marginBottom: '24px' }}>
        <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
          Previous Clients (Optional, Anonymized)
        </label>
        <textarea
          value={formData.previousClients}
          onChange={(e) => updateFormData('previousClients', e.target.value)}
          placeholder="E.g., 'Worked with 15+ SMB clients in manufacturing, 3 enterprise clients in tech, advised 5 startups on tax optimization...'"
          rows={4}
          style={{
            width: '100%',
            padding: '12px 16px',
            borderRadius: '12px',
            border: `1px solid ${theme.colors.lightGray}`,
            fontFamily: "'Lora', serif",
            fontSize: '14px',
            resize: 'vertical',
          }}
        />
        <p style={{ fontSize: '12px', color: theme.colors.midGray, marginTop: '6px' }}>
          Keep it general - no specific company names due to NDA
        </p>
      </div>

      <div style={{ marginBottom: '24px' }}>
        <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
          Tools & Software Proficiency
        </label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '12px' }}>
          {['DATEV', 'SAP', 'Excel', 'Power BI', 'SQL', 'Python', 'QuickBooks', 'Salesforce'].map(tool => {
            const isSelected = formData.toolsProficiency.includes(tool);
            return (
              <button
                key={tool}
                onClick={() => {
                  if (isSelected) {
                    updateFormData('toolsProficiency', formData.toolsProficiency.filter(t => t !== tool));
                  } else {
                    updateFormData('toolsProficiency', [...formData.toolsProficiency, tool]);
                  }
                }}
                style={{
                  padding: '8px 16px',
                  borderRadius: '8px',
                  border: 'none',
                  background: isSelected ? theme.colors.orange : theme.colors.lightGray,
                  color: isSelected ? 'white' : theme.colors.dark,
                  fontFamily: "'Poppins', sans-serif",
                  fontSize: '13px',
                  fontWeight: 500,
                  cursor: 'pointer',
                }}
              >
                {tool}
              </button>
            );
          })}
        </div>
      </div>

      <div style={{ marginBottom: '24px' }}>
        <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
          Languages
        </label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {['German', 'English', 'French', 'Spanish', 'Italian'].map(lang => {
            const isSelected = formData.languages.includes(lang);
            return (
              <button
                key={lang}
                onClick={() => {
                  if (lang === 'German') return; // German always required
                  if (isSelected) {
                    updateFormData('languages', formData.languages.filter(l => l !== lang));
                  } else {
                    updateFormData('languages', [...formData.languages, lang]);
                  }
                }}
                style={{
                  padding: '8px 16px',
                  borderRadius: '8px',
                  border: 'none',
                  background: isSelected ? theme.colors.blue : theme.colors.lightGray,
                  color: isSelected ? 'white' : theme.colors.dark,
                  fontFamily: "'Poppins', sans-serif",
                  fontSize: '13px',
                  fontWeight: 500,
                  cursor: lang === 'German' ? 'not-allowed' : 'pointer',
                  opacity: lang === 'German' ? 0.7 : 1,
                }}
              >
                {lang} {lang === 'German' && '(Required)'}
              </button>
            );
          })}
        </div>
      </div>

      <div style={{ marginBottom: '24px' }}>
        <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
          Industry Experience
        </label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {['Manufacturing', 'Tech/SaaS', 'Retail', 'Healthcare', 'Finance', 'Real Estate', 'Logistics', 'E-commerce'].map(industry => {
            const isSelected = formData.industries.includes(industry);
            return (
              <button
                key={industry}
                onClick={() => {
                  if (isSelected) {
                    updateFormData('industries', formData.industries.filter(i => i !== industry));
                  } else {
                    updateFormData('industries', [...formData.industries, industry]);
                  }
                }}
                style={{
                  padding: '8px 16px',
                  borderRadius: '8px',
                  border: 'none',
                  background: isSelected ? theme.colors.green : theme.colors.lightGray,
                  color: isSelected ? 'white' : theme.colors.dark,
                  fontFamily: "'Poppins', sans-serif",
                  fontSize: '13px',
                  fontWeight: 500,
                  cursor: 'pointer',
                }}
              >
                {industry}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );

  // ============================================================================
  // STEP 4: AVAILABILITY & PRICING
  // ============================================================================
  const Step4Availability = () => {
    const estimatedHours = formData.selectedMcps.reduce((sum, mcp) => {
      const hours = { CTAX: 4, FPA: 5, LEGAL: 6, ETIM: 3, TENDER: 5, PRICING: 4, HR: 5 };
      return sum + (hours[mcp.mcpId as keyof typeof hours] || 4);
    }, 0);

    const totalMonthlyHours = estimatedHours * formData.maxClients;
    const weeklyHours = Math.round(totalMonthlyHours / 4);

    const avgRates = formData.selectedMcps.reduce((sum, mcp) => {
      const rates = { CTAX: 4200, FPA: 3800, LEGAL: 4500, ETIM: 3200, TENDER: 3500, PRICING: 3200, HR: 2800 };
      return sum + (rates[mcp.mcpId as keyof typeof rates] || 3500);
    }, 0);
    const avgRate = Math.round(avgRates / Math.max(formData.selectedMcps.length, 1));
    const potentialEarnings = Math.round(avgRate * 0.9 * formData.maxClients);

    return (
      <div>
        <h2 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '24px', fontWeight: 600, marginBottom: '8px' }}>
          Availability & Pricing
        </h2>
        <p style={{ color: theme.colors.midGray, marginBottom: '32px' }}>
          Set your capacity and pricing expectations
        </p>

        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
            Maximum Client Capacity *
          </label>
          <input
            type="range"
            min="5"
            max="15"
            value={formData.maxClients}
            onChange={(e) => updateFormData('maxClients', parseInt(e.target.value))}
            style={{ width: '100%', marginBottom: '8px' }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
            <span style={{ fontFamily: "'Poppins', sans-serif", fontSize: '24px', fontWeight: 600, color: theme.colors.orange }}>
              {formData.maxClients} clients
            </span>
            <span style={{ color: theme.colors.midGray }}>
              ~{weeklyHours} hours/week
            </span>
          </div>
          <p style={{ fontSize: '12px', color: theme.colors.midGray, marginTop: '8px' }}>
            Based on your selected MCPs, we estimate {estimatedHours} hours/month per client (AI handles 85-95%)
          </p>
        </div>

        <div style={{
          padding: '20px',
          background: `${theme.colors.green}10`,
          borderRadius: '16px',
          border: `1px solid ${theme.colors.green}`,
          marginBottom: '24px',
        }}>
          <p style={{ fontSize: '12px', color: theme.colors.midGray, marginBottom: '4px' }}>
            Potential Monthly Earnings
          </p>
          <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '36px', fontWeight: 600, color: theme.colors.green }}>
            €{potentialEarnings.toLocaleString()}
          </p>
          <p style={{ fontSize: '13px', color: theme.colors.midGray }}>
            ({formData.maxClients} clients × €{avgRate.toLocaleString()}/month avg × 90% expert share)
          </p>
        </div>

        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
            Preferred Client Size (select all that apply)
          </label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {['Startup (5-20)', 'SMB (20-200)', 'Mid-market (200-1000)', 'Enterprise (1000+)'].map(size => {
              const isSelected = formData.preferredClientSize.includes(size);
              return (
                <button
                  key={size}
                  onClick={() => {
                    if (isSelected) {
                      updateFormData('preferredClientSize', formData.preferredClientSize.filter(s => s !== size));
                    } else {
                      updateFormData('preferredClientSize', [...formData.preferredClientSize, size]);
                    }
                  }}
                  style={{
                    padding: '10px 18px',
                    borderRadius: '8px',
                    border: 'none',
                    background: isSelected ? theme.colors.blue : theme.colors.lightGray,
                    color: isSelected ? 'white' : theme.colors.dark,
                    fontFamily: "'Poppins', sans-serif",
                    fontSize: '13px',
                    fontWeight: 500,
                    cursor: 'pointer',
                  }}
                >
                  {size}
                </button>
              );
            })}
          </div>
        </div>

        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
            Hourly Rate Expectation (Optional)
          </label>
          <input
            type="number"
            value={formData.hourlyRateExpectation || ''}
            onChange={(e) => updateFormData('hourlyRateExpectation', parseInt(e.target.value))}
            placeholder="150"
            style={{
              width: '100%',
              padding: '12px 16px',
              borderRadius: '12px',
              border: `1px solid ${theme.colors.lightGray}`,
              fontFamily: "'Lora', serif",
              fontSize: '14px',
            }}
          />
          <p style={{ fontSize: '12px', color: theme.colors.midGray, marginTop: '6px' }}>
            Platform suggests €100-200/hour for your expertise level. Final rates are per client/month.
          </p>
        </div>

        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
            Weekly Availability (hours)
          </label>
          <input
            type="range"
            min="5"
            max="40"
            value={formData.weeklyAvailability}
            onChange={(e) => updateFormData('weeklyAvailability', parseInt(e.target.value))}
            style={{ width: '100%', marginBottom: '8px' }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
            <span style={{ fontFamily: "'Poppins', sans-serif", fontSize: '18px', fontWeight: 600 }}>
              {formData.weeklyAvailability} hours/week
            </span>
            <span style={{ color: weeklyHours > formData.weeklyAvailability ? theme.colors.red : theme.colors.green }}>
              {weeklyHours > formData.weeklyAvailability
                ? `⚠ ${weeklyHours} hours needed for ${formData.maxClients} clients`
                : `✓ Sufficient for ${formData.maxClients} clients`
              }
            </span>
          </div>
        </div>
      </div>
    );
  };

  // ============================================================================
  // STEP 5: VERIFICATION
  // ============================================================================
  const Step5Verification = () => {
    return (
      <div>
        <h2 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '24px', fontWeight: 600, marginBottom: '8px' }}>
          Verification & Documents
        </h2>
        <p style={{ color: theme.colors.midGray, marginBottom: '32px' }}>
          Upload required documents for verification
        </p>

        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
            Professional Certifications *
          </label>
          <div style={{
            padding: '32px',
            border: `2px dashed ${theme.colors.lightGray}`,
            borderRadius: '16px',
            textAlign: 'center',
            background: theme.colors.light,
            cursor: 'pointer',
          }}>
            <p style={{ fontSize: '48px', marginBottom: '12px' }}>📄</p>
            <p style={{ fontFamily: "'Poppins', sans-serif", fontWeight: 500, marginBottom: '4px' }}>
              Drop files here or click to upload
            </p>
            <p style={{ fontSize: '12px', color: theme.colors.midGray }}>
              PDF, JPG, PNG (max 10MB each)
            </p>
            <p style={{ fontSize: '12px', color: theme.colors.midGray, marginTop: '8px' }}>
              {formData.certifications.length} file(s) uploaded
            </p>
          </div>
          <p style={{ fontSize: '12px', color: theme.colors.midGray, marginTop: '8px' }}>
            Upload: StB, WP, CPA, CFA, or other relevant certifications
          </p>
        </div>

        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
            ID Document (for KYC) *
          </label>
          <div style={{
            padding: '24px',
            border: `2px dashed ${theme.colors.lightGray}`,
            borderRadius: '16px',
            textAlign: 'center',
            background: theme.colors.light,
            cursor: 'pointer',
          }}>
            <p style={{ fontSize: '36px', marginBottom: '8px' }}>🪪</p>
            <p style={{ fontFamily: "'Poppins', sans-serif", fontSize: '13px', fontWeight: 500 }}>
              {formData.idDocument ? 'ID uploaded ✓' : 'Upload ID document'}
            </p>
            <p style={{ fontSize: '11px', color: theme.colors.midGray }}>
              Passport or National ID
            </p>
          </div>
        </div>

        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
            Tax Identification Number *
          </label>
          <input
            type="text"
            value={formData.taxId}
            onChange={(e) => updateFormData('taxId', e.target.value)}
            placeholder="DE123456789"
            style={{
              width: '100%',
              padding: '12px 16px',
              borderRadius: '12px',
              border: `1px solid ${theme.colors.lightGray}`,
              fontFamily: "'Lora', serif",
              fontSize: '14px',
            }}
          />
          <p style={{ fontSize: '12px', color: theme.colors.midGray, marginTop: '6px' }}>
            Required for tax reporting and invoicing
          </p>
        </div>

        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
            Banking Details (SEPA) *
          </label>
          <input
            type="text"
            value={formData.iban}
            onChange={(e) => updateFormData('iban', e.target.value)}
            placeholder="DE89 3704 0044 0532 0130 00"
            style={{
              width: '100%',
              padding: '12px 16px',
              borderRadius: '12px',
              border: `1px solid ${theme.colors.lightGray}`,
              fontFamily: "'Lora', serif",
              fontSize: '14px',
              marginBottom: '12px',
            }}
          />
          <input
            type="text"
            value={formData.bic}
            onChange={(e) => updateFormData('bic', e.target.value)}
            placeholder="BIC/SWIFT Code"
            style={{
              width: '100%',
              padding: '12px 16px',
              borderRadius: '12px',
              border: `1px solid ${theme.colors.lightGray}`,
              fontFamily: "'Lora', serif",
              fontSize: '14px',
            }}
          />
          <p style={{ fontSize: '12px', color: theme.colors.midGray, marginTop: '6px' }}>
            Weekly payouts every Friday via SEPA transfer
          </p>
        </div>

        <div style={{
          padding: '16px',
          background: `${theme.colors.blue}10`,
          borderRadius: '12px',
          border: `1px solid ${theme.colors.blue}`,
        }}>
          <p style={{ fontSize: '12px', color: theme.colors.midGray, marginBottom: '4px' }}>
            🔒 Secure Processing
          </p>
          <p style={{ fontSize: '13px' }}>
            All documents are encrypted and processed securely. Your data is DSGVO/GDPR compliant and never shared without consent.
          </p>
        </div>
      </div>
    );
  };

  // ============================================================================
  // STEP 6: REVIEW & SUBMIT
  // ============================================================================
  const Step6Review = () => {
    return (
      <div>
        <h2 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '24px', fontWeight: 600, marginBottom: '8px' }}>
          Review & Submit
        </h2>
        <p style={{ color: theme.colors.midGray, marginBottom: '32px' }}>
          Review your application before submitting
        </p>

        {/* Basic Info */}
        <div style={{
          padding: '20px',
          background: 'white',
          border: `1px solid ${theme.colors.lightGray}`,
          borderRadius: '16px',
          marginBottom: '16px',
        }}>
          <h3 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '16px', fontWeight: 600, marginBottom: '12px' }}>
            Basic Information
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: '8px', fontSize: '14px' }}>
            <span style={{ color: theme.colors.midGray }}>Name:</span>
            <span style={{ fontWeight: 500 }}>{formData.firstName} {formData.lastName}</span>

            <span style={{ color: theme.colors.midGray }}>Email:</span>
            <span>{formData.email}</span>

            <span style={{ color: theme.colors.midGray }}>Headline:</span>
            <span>{formData.headline}</span>

            <span style={{ color: theme.colors.midGray }}>Phone:</span>
            <span>{formData.phone}</span>
          </div>
        </div>

        {/* MCP Expertise */}
        <div style={{
          padding: '20px',
          background: 'white',
          border: `1px solid ${theme.colors.lightGray}`,
          borderRadius: '16px',
          marginBottom: '16px',
        }}>
          <h3 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '16px', fontWeight: 600, marginBottom: '12px' }}>
            MCP Expertise
          </h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {formData.selectedMcps.map(mcp => {
              const mcpInfo = MCP_CATALOG[mcp.mcpId as keyof typeof MCP_CATALOG];
              return (
                <span key={mcp.mcpId} style={{
                  padding: '8px 14px',
                  borderRadius: '8px',
                  background: `${mcpInfo.color}15`,
                  color: mcpInfo.color,
                  fontFamily: "'Poppins', sans-serif",
                  fontSize: '13px',
                  fontWeight: 500,
                }}>
                  {mcpInfo.icon} {mcpInfo.name} ({mcp.proficiency})
                </span>
              );
            })}
          </div>
        </div>

        {/* Experience */}
        <div style={{
          padding: '20px',
          background: 'white',
          border: `1px solid ${theme.colors.lightGray}`,
          borderRadius: '16px',
          marginBottom: '16px',
        }}>
          <h3 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '16px', fontWeight: 600, marginBottom: '12px' }}>
            Experience
          </h3>
          <div style={{ fontSize: '14px' }}>
            <p><strong>Years:</strong> {formData.yearsExperience}</p>
            <p style={{ marginTop: '8px' }}><strong>Languages:</strong> {formData.languages.join(', ')}</p>
            <p style={{ marginTop: '8px' }}><strong>Industries:</strong> {formData.industries.join(', ') || 'Not specified'}</p>
            <p style={{ marginTop: '8px' }}><strong>Tools:</strong> {formData.toolsProficiency.join(', ') || 'Not specified'}</p>
          </div>
        </div>

        {/* Availability */}
        <div style={{
          padding: '20px',
          background: 'white',
          border: `1px solid ${theme.colors.lightGray}`,
          borderRadius: '16px',
          marginBottom: '24px',
        }}>
          <h3 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '16px', fontWeight: 600, marginBottom: '12px' }}>
            Availability & Pricing
          </h3>
          <div style={{ fontSize: '14px' }}>
            <p><strong>Max Clients:</strong> {formData.maxClients}</p>
            <p style={{ marginTop: '8px' }}><strong>Weekly Hours:</strong> {formData.weeklyAvailability}</p>
            <p style={{ marginTop: '8px' }}><strong>Client Sizes:</strong> {formData.preferredClientSize.join(', ') || 'All sizes'}</p>
          </div>
        </div>

        {/* Terms & Conditions */}
        <div style={{
          padding: '20px',
          background: theme.colors.light,
          borderRadius: '16px',
          marginBottom: '16px',
        }}>
          <label style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={formData.termsAccepted}
              onChange={(e) => updateFormData('termsAccepted', e.target.checked)}
              style={{ marginTop: '4px' }}
            />
            <span style={{ fontSize: '13px' }}>
              I accept the <a href="/terms" style={{ color: theme.colors.orange }}>Terms & Conditions</a> and <a href="/expert-agreement" style={{ color: theme.colors.orange }}>Expert Agreement</a>. I understand that:
              <ul style={{ marginTop: '8px', paddingLeft: '20px' }}>
                <li>The platform takes a 10% fee on all transactions</li>
                <li>Payouts occur weekly via SEPA transfer</li>
                <li>I must maintain professional standards and respond within stated timeframes</li>
                <li>My application will be reviewed within 2-5 business days</li>
              </ul>
            </span>
          </label>
        </div>

        <div style={{
          padding: '20px',
          background: theme.colors.light,
          borderRadius: '16px',
        }}>
          <label style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={formData.dataProcessingAccepted}
              onChange={(e) => updateFormData('dataProcessingAccepted', e.target.checked)}
              style={{ marginTop: '4px' }}
            />
            <span style={{ fontSize: '13px' }}>
              I consent to data processing as described in the <a href="/privacy" style={{ color: theme.colors.orange }}>Privacy Policy</a>. My data will be processed in accordance with DSGVO/GDPR.
            </span>
          </label>
        </div>
      </div>
    );
  };

  // ============================================================================
  // RENDER
  // ============================================================================
  return (
    <div style={{ minHeight: '100vh', background: theme.colors.light, padding: '40px 20px' }}>
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <h1 style={{ fontFamily: "'Poppins', sans-serif", fontSize: '32px', fontWeight: 600, marginBottom: '8px' }}>
            Join 0711 Expert Network
          </h1>
          <p style={{ color: theme.colors.midGray, fontSize: '16px' }}>
            Step {currentStep} of {totalSteps}
          </p>
        </div>

        {/* Progress Bar */}
        <div style={{ marginBottom: '40px' }}>
          <div style={{
            height: '8px',
            background: theme.colors.lightGray,
            borderRadius: '4px',
            overflow: 'hidden',
          }}>
            <div style={{
              width: `${(currentStep / totalSteps) * 100}%`,
              height: '100%',
              background: theme.colors.orange,
              borderRadius: '4px',
              transition: 'width 0.3s ease',
            }} />
          </div>
        </div>

        {/* Main Form Card */}
        <div style={{
          background: 'white',
          borderRadius: '20px',
          padding: '40px',
          marginBottom: '24px',
        }}>
          {currentStep === 1 && <Step1BasicInfo />}
          {currentStep === 2 && <Step2McpExpertise />}
          {currentStep === 3 && <Step3Experience />}
          {currentStep === 4 && <Step4Availability />}
          {currentStep === 5 && <Step5Verification />}
          {currentStep === 6 && <Step6Review />}
        </div>

        {/* Navigation */}
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '16px' }}>
          <button
            onClick={prevStep}
            disabled={currentStep === 1}
            style={{
              padding: '14px 32px',
              borderRadius: '100px',
              border: `1.5px solid ${theme.colors.dark}`,
              background: 'transparent',
              color: theme.colors.dark,
              fontFamily: "'Poppins', sans-serif",
              fontSize: '14px',
              fontWeight: 500,
              cursor: currentStep === 1 ? 'not-allowed' : 'pointer',
              opacity: currentStep === 1 ? 0.3 : 1,
            }}
          >
            ← Back
          </button>
          <button
            onClick={currentStep === totalSteps ? handleSubmit : nextStep}
            style={{
              padding: '14px 32px',
              borderRadius: '100px',
              border: 'none',
              background: theme.colors.orange,
              color: 'white',
              fontFamily: "'Poppins', sans-serif",
              fontSize: '14px',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            {currentStep === totalSteps ? 'Submit Application' : 'Continue →'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExpertSignupWizard;
