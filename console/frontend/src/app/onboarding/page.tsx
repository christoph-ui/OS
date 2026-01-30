'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { colors } from '@/lib/theme';
import { Zap, Package, Check, ArrowRight, Sparkles } from 'lucide-react';

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
      icon: <Zap size={32} />,
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
      icon: <Package size={32} />,
      color: colors.blue || '#6a9bcc',
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
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 8,
          padding: '8px 16px',
          backgroundColor: colors.orange + '15',
          borderRadius: 20,
          marginBottom: 20,
        }}>
          <Sparkles size={16} color={colors.orange} />
          <span style={{ fontSize: 14, color: colors.orange, fontWeight: 500 }}>
            Welcome to 0711
          </span>
        </div>

        <h1 style={{
          fontSize: 36,
          fontWeight: 700,
          color: colors.dark,
          margin: 0,
          marginBottom: 12,
          fontFamily: "'Poppins', sans-serif",
        }}>
          Choose your setup
        </h1>
        <p style={{
          fontSize: 18,
          color: colors.midGray,
          margin: 0,
          maxWidth: 500,
        }}>
          Quick AI-powered or detailed guided wizard — your choice.
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
              width: 64,
              height: 64,
              borderRadius: 16,
              backgroundColor: option.color + '15',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: option.color,
              marginBottom: 20,
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
                  <Check size={16} color={option.color} />
                  {feature}
                </li>
              ))}
            </ul>

            {/* CTA */}
            <div style={{
              marginTop: 24,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 14,
              fontWeight: 600,
              color: option.color,
            }}>
              Get Started <ArrowRight size={16} />
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

      {/* Back to home link */}
      <a 
        href="/"
        style={{
          marginTop: 16,
          fontSize: 14,
          color: colors.orange,
          textDecoration: 'none',
        }}
      >
        ← Back to Home
      </a>
    </div>
  );
}
