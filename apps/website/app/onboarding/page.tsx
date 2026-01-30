'use client';

import React from 'react';
import { useRouter } from 'next/navigation';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
};

export default function OnboardingChoice() {
  const router = useRouter();

  const options = [
    {
      id: 'quick',
      title: 'Quick Setup',
      subtitle: '4 steps • ~5 minutes',
      description: 'AI-powered onboarding. Upload your files and let our AI analyze your data, suggest connectors, and deploy automatically.',
      features: [
        'AI file analysis',
        'Smart connector recommendations',
        'One-click deployment',
        'Best for: Power users & returning customers',
      ],
      icon: '⚡',
      color: colors.orange,
      href: '/onboarding/smart',
    },
    {
      id: 'guided',
      title: 'Guided Setup',
      subtitle: '7 steps • ~15 minutes',
      description: 'Step-by-step wizard with detailed explanations. Perfect if you want to understand each option and customize your setup.',
      features: [
        'Detailed explanations',
        'Manual MCP selection',
        'Full customization',
        'Best for: New users & complex setups',
      ],
      icon: '📋',
      color: '#6a9bcc',
      href: '/onboarding/guided',
    },
  ];

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: colors.light,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px 20px',
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    }}>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <h1 style={{
          fontSize: 36,
          fontWeight: 700,
          color: colors.dark,
          margin: 0,
          marginBottom: 12,
        }}>
          <span style={{ color: colors.orange }}>0711</span> Onboarding
        </h1>
        <p style={{
          fontSize: 18,
          color: colors.midGray,
          margin: 0,
          maxWidth: 500,
        }}>
          Choose how you'd like to set up your account
        </p>
      </div>

      {/* Options Grid */}
      <div style={{
        display: 'flex',
        gap: 24,
        flexWrap: 'wrap',
        justifyContent: 'center',
        maxWidth: 900,
      }}>
        {options.map((option) => (
          <button
            key={option.id}
            onClick={() => router.push(option.href)}
            style={{
              width: 400,
              padding: 32,
              backgroundColor: 'white',
              border: `2px solid ${colors.lightGray}`,
              borderRadius: 16,
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'all 0.2s ease',
              position: 'relative',
              overflow: 'hidden',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = option.color;
              e.currentTarget.style.transform = 'translateY(-4px)';
              e.currentTarget.style.boxShadow = '0 12px 40px rgba(0,0,0,0.1)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = colors.lightGray;
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            {/* Icon */}
            <div style={{
              fontSize: 48,
              marginBottom: 16,
            }}>
              {option.icon}
            </div>

            {/* Title */}
            <h2 style={{
              fontSize: 24,
              fontWeight: 600,
              color: colors.dark,
              margin: 0,
              marginBottom: 4,
            }}>
              {option.title}
            </h2>

            {/* Subtitle */}
            <p style={{
              fontSize: 14,
              color: option.color,
              fontWeight: 500,
              margin: 0,
              marginBottom: 16,
            }}>
              {option.subtitle}
            </p>

            {/* Description */}
            <p style={{
              fontSize: 15,
              color: colors.midGray,
              lineHeight: 1.6,
              margin: 0,
              marginBottom: 20,
            }}>
              {option.description}
            </p>

            {/* Features */}
            <ul style={{
              listStyle: 'none',
              padding: 0,
              margin: 0,
            }}>
              {option.features.map((feature, i) => (
                <li key={i} style={{
                  fontSize: 14,
                  color: colors.dark,
                  marginBottom: 8,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}>
                  <span style={{ color: option.color }}>✓</span>
                  {feature}
                </li>
              ))}
            </ul>

            {/* CTA Arrow */}
            <div style={{
              position: 'absolute',
              bottom: 24,
              right: 24,
              fontSize: 24,
              color: option.color,
              opacity: 0.5,
            }}>
              →
            </div>
          </button>
        ))}
      </div>

      {/* Footer hint */}
      <p style={{
        marginTop: 40,
        fontSize: 14,
        color: colors.midGray,
      }}>
        Not sure? Start with <strong>Guided Setup</strong> — you can always speed up later.
      </p>
    </div>
  );
}
