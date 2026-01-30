'use client';

import { useRouter, usePathname } from 'next/navigation';
import { LayoutDashboard, Users, Package, UserCheck, Activity, LogOut, Shield, Server, Settings, UserCog } from 'lucide-react';
import { colors } from '@/lib/theme';

interface AdminLayoutProps {
  children: React.ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/admin' },
    { id: 'customers', label: 'Customers', icon: Users, path: '/admin/customers' },
    { id: 'users', label: 'All Users', icon: UserCog, path: '/admin/users' },
    { id: 'deployments', label: 'Deployments', icon: Server, path: '/admin/deployments' },
    { id: 'mcps', label: 'MCP Approvals', icon: Package, path: '/admin/mcps' },
    { id: 'developers', label: 'Developers', icon: UserCheck, path: '/admin/developers' },
    { id: 'health', label: 'System Health', icon: Activity, path: '/admin/health' },
    { id: 'settings', label: 'Settings', icon: Settings, path: '/admin/settings' },
  ];

  const handleLogout = () => {
    localStorage.removeItem('0711_admin_token');
    localStorage.removeItem('0711_admin_user');
    router.push('/admin/login');
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
            <Shield size={28} color={colors.red} />
            <div>
              <h1 style={{
                fontFamily: "'Poppins', Arial, sans-serif",
                fontSize: 20,
                fontWeight: 600,
                margin: 0,
                color: colors.light,
              }}>
                Admin Portal
              </h1>
              <p style={{
                fontSize: 12,
                color: colors.midGray,
                margin: '2px 0 0',
              }}>
                0711 Platform
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
                  backgroundColor: isActive ? `${colors.red}20` : 'transparent',
                  color: isActive ? colors.red : colors.midGray,
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
