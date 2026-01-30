'use client';

import { useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { colors } from '@/lib/theme';

interface NavItem {
  id: string;
  label: string;
  path: string;
  icon: string;
}

const navItems: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', path: '/partner', icon: 'chart' },
  { id: 'customers', label: 'Kunden', path: '/partner/customers', icon: 'users' },
  { id: 'earnings', label: 'Provisionen', path: '/partner/earnings', icon: 'wallet' },
  { id: 'settings', label: 'Einstellungen', path: '/partner/settings', icon: 'settings' },
];

const NavIcon = ({ type }: { type: string }) => {
  const iconStyle = { width: 20, height: 20 };

  switch (type) {
    case 'chart':
      return (
        <svg style={iconStyle} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="12" y1="20" x2="12" y2="10" />
          <line x1="18" y1="20" x2="18" y2="4" />
          <line x1="6" y1="20" x2="6" y2="16" />
        </svg>
      );
    case 'users':
      return (
        <svg style={iconStyle} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
          <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
      );
    case 'settings':
      return (
        <svg style={iconStyle} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
        </svg>
      );
    case 'wallet':
      return (
        <svg style={iconStyle} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 12V7H5a2 2 0 0 1 0-4h14v4" />
          <path d="M3 5v14a2 2 0 0 0 2 2h16v-5" />
          <path d="M18 12a2 2 0 0 0 0 4h4v-4h-4z" />
        </svg>
      );
    case 'logout':
      return (
        <svg style={iconStyle} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <polyline points="16,17 21,12 16,7" />
          <line x1="21" y1="12" x2="9" y2="12" />
        </svg>
      );
    default:
      return null;
  }
};

export default function PartnerSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem('0711_token');
    localStorage.removeItem('0711_partner');
    localStorage.removeItem('0711_user_id');
    router.push('/partner-login');
  };

  const sidebarContent = (
    <>
      {/* Logo */}
      <div style={{
        padding: '0 24px 32px',
        borderBottom: `1px solid ${colors.midGray}33`,
      }}>
        <h1 style={{
          fontFamily: "'Poppins', Arial, sans-serif",
          fontSize: 28,
          fontWeight: 600,
          margin: 0,
          letterSpacing: '-0.5px',
        }}>
          <span style={{ color: colors.orange }}>0711</span>
        </h1>
        <p style={{
          fontSize: 13,
          color: colors.midGray,
          margin: '4px 0 0',
          letterSpacing: '0.5px',
        }}>
          Partner Portal
        </p>
      </div>

      {/* Navigation */}
      <nav style={{ padding: '24px 16px', flex: 1 }}>
        {navItems.map((item) => {
          const isActive = pathname === item.path || (item.path !== '/partner' && pathname?.startsWith(item.path));

          return (
            <button
              key={item.id}
              onClick={() => {
                router.push(item.path);
                setMobileOpen(false);
              }}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '12px 16px',
                marginBottom: 4,
                border: 'none',
                borderRadius: 10,
                cursor: 'pointer',
                fontSize: 15,
                fontFamily: "'Lora', Georgia, serif",
                backgroundColor: isActive ? `${colors.orange}15` : 'transparent',
                color: isActive ? colors.orange : colors.midGray,
                transition: 'all 0.2s ease',
              }}
              onMouseOver={(e) => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor = `${colors.midGray}15`;
                }
              }}
              onMouseOut={(e) => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }
              }}
            >
              <NavIcon type={item.icon} />
              <span style={{ fontWeight: isActive ? 500 : 400 }}>
                {item.label}
              </span>
            </button>
          );
        })}
      </nav>

      {/* Logout */}
      <div style={{
        padding: '16px 20px',
        borderTop: `1px solid ${colors.midGray}33`,
      }}>
        <button
          onClick={handleLogout}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 16px',
            border: 'none',
            borderRadius: 10,
            cursor: 'pointer',
            fontSize: 15,
            fontFamily: "'Lora', Georgia, serif",
            backgroundColor: 'transparent',
            color: colors.midGray,
            transition: 'all 0.2s ease',
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.backgroundColor = `${colors.midGray}15`;
            e.currentTarget.style.color = colors.orange;
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.backgroundColor = 'transparent';
            e.currentTarget.style.color = colors.midGray;
          }}
        >
          <NavIcon type="logout" />
          <span>Abmelden</span>
        </button>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile Hamburger Button */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        style={{
          position: 'fixed',
          top: 20,
          left: 20,
          zIndex: 1001,
          width: 48,
          height: 48,
          backgroundColor: colors.dark,
          border: 'none',
          borderRadius: 12,
          cursor: 'pointer',
          display: 'none',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        }}
        className="mobile-menu-button"
      >
        <svg
          style={{ width: 24, height: 24, color: colors.light }}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          {mobileOpen ? (
            <path d="M18 6L6 18M6 6l12 12" />
          ) : (
            <>
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </>
          )}
        </svg>
      </button>

      {/* Desktop Sidebar */}
      <aside
        className="desktop-sidebar"
        style={{
          width: 260,
          backgroundColor: colors.dark,
          color: colors.light,
          display: 'flex',
          flexDirection: 'column',
          padding: '24px 0',
          height: '100vh',
          position: 'sticky',
          top: 0,
        }}
      >
        {sidebarContent}
      </aside>

      {/* Mobile Sidebar Overlay */}
      {mobileOpen && (
        <>
          <div
            onClick={() => setMobileOpen(false)}
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0,0,0,0.5)',
              zIndex: 999,
              display: 'none',
            }}
            className="mobile-overlay"
          />
          <aside
            className="mobile-sidebar"
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              bottom: 0,
              width: 280,
              backgroundColor: colors.dark,
              color: colors.light,
              display: 'none',
              flexDirection: 'column',
              padding: '24px 0',
              zIndex: 1000,
              boxShadow: '4px 0 24px rgba(0,0,0,0.3)',
            }}
          >
            {sidebarContent}
          </aside>
        </>
      )}

      {/* Responsive Styles */}
      <style jsx global>{`
        @media (max-width: 768px) {
          .desktop-sidebar {
            display: none !important;
          }

          .mobile-menu-button {
            display: flex !important;
          }

          .mobile-overlay {
            display: block !important;
          }

          .mobile-sidebar {
            display: flex !important;
          }
        }
      `}</style>
    </>
  );
}
