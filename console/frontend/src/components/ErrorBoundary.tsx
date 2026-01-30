'use client';

import { Component, ReactNode } from 'react';

const colors = {
  dark: '#141413',
  light: '#faf9f5',
  midGray: '#b0aea5',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  red: '#d75757',
};

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '400px',
          padding: 40,
        }}>
          <div style={{
            maxWidth: 600,
            textAlign: 'center',
            backgroundColor: '#fff',
            borderRadius: 16,
            padding: 40,
            border: `2px solid ${colors.red}`,
          }}>
            <div style={{
              width: 80,
              height: 80,
              borderRadius: '50%',
              backgroundColor: `${colors.red}15`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 24px',
              fontSize: 40,
              color: colors.red,
            }}>
              ⚠
            </div>

            <h2 style={{
              fontFamily: "'Poppins', Arial, sans-serif",
              fontSize: 24,
              fontWeight: 600,
              margin: '0 0 12px',
              color: colors.dark,
            }}>
              Etwas ist schiefgelaufen
            </h2>

            <p style={{
              fontSize: 15,
              color: colors.midGray,
              margin: '0 0 24px',
              lineHeight: 1.6,
            }}>
              {this.state.error?.message || 'Ein unerwarteter Fehler ist aufgetreten'}
            </p>

            <button
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.reload();
              }}
              style={{
                padding: '12px 32px',
                backgroundColor: colors.orange,
                color: '#fff',
                border: 'none',
                borderRadius: 10,
                fontSize: 15,
                fontWeight: 600,
                cursor: 'pointer',
                fontFamily: "'Poppins', Arial, sans-serif",
                transition: 'all 0.2s',
              }}
            >
              Seite neu laden
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
