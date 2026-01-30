'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import PartnerSidebar from '@/components/PartnerSidebar';
import { ToastProvider } from '@/components/Toast';
import { ErrorBoundary } from '@/components/ErrorBoundary';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
};

export default function PartnerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Skip auth check for login/signup pages
    const publicPaths = ['/partner-login', '/partner-signup'];
    if (publicPaths.some(path => pathname?.startsWith(path))) {
      return;
    }

    // Check if partner is logged in
    const token = localStorage.getItem('0711_token');
    if (!token) {
      // Redirect to login (same port now!)
      router.push('/partner-login');
    }
  }, [router, pathname]);

  // Don't show sidebar on auth pages
  const isAuthPage = pathname === '/partner-login' || pathname === '/partner-signup';

  if (isAuthPage) {
    return (
      <ErrorBoundary>
        <ToastProvider>
          {children}
        </ToastProvider>
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <ToastProvider>
        <div style={{
          display: 'flex',
          height: '100vh',
          fontFamily: "'Lora', Georgia, serif",
          backgroundColor: colors.light,
          color: colors.dark,
        }}>
          <PartnerSidebar />
          <main style={{
            flex: 1,
            overflowY: 'auto',
          }}>
            {children}
          </main>
        </div>
      </ToastProvider>
    </ErrorBoundary>
  );
}
