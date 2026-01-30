'use client';

import { useRouter, usePathname } from 'next/navigation';
import { Code, LayoutDashboard, Package, PlusCircle, BarChart, LogOut } from 'lucide-react';

const colors = {
  dark: '#141413',
  light: '#faf9f5',
  midGray: '#b0aea5',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  blue: '#6a9bcc',
};

interface DeveloperLayoutProps {
  children: React.ReactNode;
}

export default function DeveloperLayout({ children }: DeveloperLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/developer' },
    { id: 'mcps', label: 'My MCPs', icon: Package, path: '/developer/mcps' },
    { id: 'new', label: 'Submit MCP', icon: PlusCircle, path: '/developer/mcps/new' },
    { id: 'analytics', label: 'Analytics', icon: BarChart, path: '/developer/analytics' },
  ];

  const handleLogout = () => {
    localStorage.removeItem('0711_developer_token');
    localStorage.removeItem('0711_developer');
    router.push('/developer/login');
  };

  return (
    <div style={{
      display: 'flex',
      minHeight: '100vh',
      backgroundColor: colors.light,
      fontFamily: "'Lora', Georgia, serif",
    }}>
      {/* Sidebar */}
      <aside style={{
        width: 260,
        backgroundColor: colors.dark,
        color: colors.light,
        display: 'flex',
        flexDirection: 'column',
      }}>
        {/* Logo */}
        <div style={{
          padding: '24px',
          borderBottom: `1px solid ${colors.midGray}33`,
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}>
            <Code size={28} color={colors.blue} />
            <div>
              <h1 style={{
                fontFamily: "'Poppins', Arial, sans-serif",
                fontSize: 20,
                fontWeight: 600,
                margin: 0,
                color: colors.light,
              }}>
                Developer Portal
              </h1>
              <p style={{
                fontSize: 12,
                color: colors.midGray,
                margin: '2px 0 0',
              }}>
                0711 MCP Marketplace
              </p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav style={{ padding: '24px 16px', flex: 1 }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.path;

            return (
              <button
                key={item.id}
                onClick={() => router.push(item.path)}
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
                  backgroundColor: isActive ? `${colors.blue}20` : 'transparent',
                  color: isActive ? colors.blue : colors.midGray,
                  transition: 'all 0.2s ease',
                }}
                onMouseOver={(e) => {
                  if (!isActive) e.currentTarget.style.backgroundColor = `${colors.midGray}22`;
                }}
                onMouseOut={(e) => {
                  if (!isActive) e.currentTarget.style.backgroundColor = 'transparent';
                }}
              >
                <Icon size={18} />
                <span style={{ fontWeight: isActive ? 500 : 400 }}>
                  {item.label}
                </span>
              </button>
            );
          })}
        </nav>

        {/* Revenue Share Badge */}
        <div style={{
          margin: '0 20px 20px',
          padding: 16,
          backgroundColor: `${colors.green}15`,
          borderRadius: 12,
          textAlign: 'center',
        }}>
          <div style={{
            fontSize: 28,
            fontWeight: 600,
            color: colors.green,
            fontFamily: "'Poppins', Arial, sans-serif",
          }}>
            70%
          </div>
          <div style={{
            fontSize: 12,
            color: colors.midGray,
          }}>
            Revenue Share
          </div>
        </div>

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
              color: colors.red,
              transition: 'all 0.2s ease',
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = `${colors.red}15`}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
          >
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main style={{ flex: 1 }}>
        {children}
      </main>
    </div>
  );
}
