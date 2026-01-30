'use client';

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

const colors = {
  dark: '#141413',
  light: '#faf9f5',
  midGray: '#b0aea5',
  orange: '#d97757',
  green: '#788c5d',
  red: '#d75757',
  blue: '#6a9bcc',
};

type ToastType = 'success' | 'error' | 'info' | 'warning';

interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextType {
  showToast: (message: string, type?: ToastType) => void;
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
  warning: (message: string) => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = Math.random().toString(36).substring(2, 9);
    const toast: Toast = { id, message, type };

    setToasts((prev) => [...prev, toast]);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  }, []);

  const success = useCallback((message: string) => showToast(message, 'success'), [showToast]);
  const error = useCallback((message: string) => showToast(message, 'error'), [showToast]);
  const info = useCallback((message: string) => showToast(message, 'info'), [showToast]);
  const warning = useCallback((message: string) => showToast(message, 'warning'), [showToast]);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const getToastColor = (type: ToastType) => {
    switch (type) {
      case 'success':
        return colors.green;
      case 'error':
        return colors.red;
      case 'warning':
        return colors.orange;
      case 'info':
      default:
        return colors.blue;
    }
  };

  const getToastIcon = (type: ToastType) => {
    switch (type) {
      case 'success':
        return '✓';
      case 'error':
        return '✗';
      case 'warning':
        return '⚠';
      case 'info':
      default:
        return 'ℹ';
    }
  };

  return (
    <ToastContext.Provider value={{ showToast, success, error, info, warning }}>
      {children}

      {/* Toast Container */}
      <div style={{
        position: 'fixed',
        top: 24,
        right: 24,
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
        pointerEvents: 'none',
      }}>
        {toasts.map((toast) => (
          <div
            key={toast.id}
            style={{
              padding: '16px 20px',
              backgroundColor: '#fff',
              borderRadius: 12,
              border: `2px solid ${getToastColor(toast.type)}`,
              boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
              minWidth: 320,
              maxWidth: 480,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              pointerEvents: 'auto',
              animation: 'slideIn 0.3s ease-out',
            }}
          >
            <div style={{
              width: 28,
              height: 28,
              borderRadius: '50%',
              backgroundColor: `${getToastColor(toast.type)}15`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 16,
              color: getToastColor(toast.type),
              fontWeight: 600,
              flexShrink: 0,
            }}>
              {getToastIcon(toast.type)}
            </div>

            <p style={{
              margin: 0,
              fontSize: 14,
              color: colors.dark,
              flex: 1,
              lineHeight: 1.5,
            }}>
              {toast.message}
            </p>

            <button
              onClick={() => removeToast(toast.id)}
              style={{
                width: 24,
                height: 24,
                borderRadius: '50%',
                backgroundColor: 'transparent',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: colors.midGray,
                fontSize: 18,
                transition: 'all 0.2s',
                flexShrink: 0,
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.backgroundColor = `${colors.lightGray}`;
                e.currentTarget.style.color = colors.dark;
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
                e.currentTarget.style.color = colors.midGray;
              }}
            >
              ×
            </button>
          </div>
        ))}
      </div>

      {/* Animation keyframes */}
      <style jsx global>{`
        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `}</style>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
}
