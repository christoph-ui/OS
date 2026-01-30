'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { colors } from '@/lib/theme';
import {
  LayoutDashboard, User, Calendar, DollarSign, Clock,
  Settings, LogOut, Bell, ChevronRight, Star
} from 'lucide-react';

interface ExpertLayoutProps {
  children: React.ReactNode;
}

export default function ExpertDashboardLayout({ children }: ExpertLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [expert, setExpert] = useState<any>(null);
  const [notifications, setNotifications] = useState(3);

  useEffect(() => {
    // Load expert data
    const expertData = localStorage.getItem('0711_expert');
    if (expertData) {
      setExpert(JSON.parse(expertData));
    }
  }, []);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, href: '/expert-dashboard' },
    { id: 'profile', label: 'My Profile', icon: User, href: '/expert-dashboard/profile' },
    { id: 'bookings', label: 'Bookings', icon: Calendar, href: '/expert-dashboard/bookings', badge: 2 },
    { id: 'availability', label: 'Availability', icon: Clock, href: '/expert-dashboard/availability' },
    { id: 'earnings', label: 'Earnings', icon: DollarSign, href: '/expert-dashboard/earnings' },
    { id: 'settings', label: 'Settings', icon: Settings, href: '/expert-dashboard/settings' },
  ];

  const handleLogout = () => {
    localStorage.removeItem('0711_token');
    localStorage.removeItem('0711_expert');
    router.push('/');
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: colors.light }}>
      {/* Sidebar */}
      <aside style={{
        width: 260,
        backgroundColor: colors.dark,
        color: 'white',
        display: 'flex',
        flexDirection: 'column',
        position: 'fixed',
        top: 0,
        left: 0,
        bottom: 0,
      }}>
        {/* Logo */}
        <div style={{
          padding: '24px',
          borderBottom: `1px solid ${colors.midGray}33`,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              width: 40,
              height: 40,
              borderRadius: 10,
              backgroundColor: colors.orange,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: 14,
            }}>
              07
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 16 }}>0711</div>
              <div style={{ fontSize: 12, color: colors.midGray }}>Expert Portal</div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav style={{ flex: 1, padding: '16px 12px' }}>
          {navItems.map((item) => {
            const isActive = pathname === item.href || 
              (item.href !== '/expert-dashboard' && pathname?.startsWith(item.href));
            
            return (
              <button
                key={item.id}
                onClick={() => router.push(item.href)}
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
                  backgroundColor: isActive ? colors.orange + '20' : 'transparent',
                  color: isActive ? colors.orange : colors.midGray,
                  fontSize: 14,
                  fontWeight: isActive ? 600 : 400,
                  transition: 'all 0.2s',
                  textAlign: 'left',
                }}
              >
                <item.icon size={20} />
                <span style={{ flex: 1 }}>{item.label}</span>
                {item.badge && (
                  <span style={{
                    backgroundColor: colors.orange,
                    color: 'white',
                    fontSize: 11,
                    fontWeight: 600,
                    padding: '2px 8px',
                    borderRadius: 10,
                  }}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* User section */}
        <div style={{
          padding: '16px',
          borderTop: `1px solid ${colors.midGray}33`,
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px',
            backgroundColor: colors.midGray + '15',
            borderRadius: 10,
            marginBottom: 12,
          }}>
            <div style={{
              width: 40,
              height: 40,
              borderRadius: '50%',
              backgroundColor: colors.orange + '30',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: colors.orange,
              fontWeight: 600,
            }}>
              {expert?.display_name?.[0] || 'E'}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 14, fontWeight: 500, color: 'white', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {expert?.display_name || 'Expert'}
              </div>
              <div style={{ fontSize: 12, color: colors.midGray, display: 'flex', alignItems: 'center', gap: 4 }}>
                <Star size={12} fill={colors.orange} color={colors.orange} />
                {expert?.rating || '4.8'}
              </div>
            </div>
          </div>

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
              backgroundColor: 'transparent',
              color: colors.midGray,
              fontSize: 14,
            }}
          >
            <LogOut size={20} />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main style={{ flex: 1, marginLeft: 260 }}>
        {/* Top bar */}
        <div style={{
          backgroundColor: 'white',
          borderBottom: `1px solid ${colors.lightGray}`,
          padding: '16px 32px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          position: 'sticky',
          top: 0,
          zIndex: 10,
        }}>
          <div>
            <h1 style={{
              fontSize: 20,
              fontWeight: 600,
              color: colors.dark,
              margin: 0,
            }}>
              {navItems.find(n => pathname === n.href || (n.href !== '/expert-dashboard' && pathname?.startsWith(n.href)))?.label || 'Dashboard'}
            </h1>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <button style={{
              position: 'relative',
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: 8,
            }}>
              <Bell size={20} color={colors.midGray} />
              {notifications > 0 && (
                <span style={{
                  position: 'absolute',
                  top: 4,
                  right: 4,
                  width: 16,
                  height: 16,
                  backgroundColor: colors.orange,
                  borderRadius: '50%',
                  fontSize: 10,
                  fontWeight: 600,
                  color: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  {notifications}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Page content */}
        <div style={{ padding: '32px' }}>
          {children}
        </div>
      </main>
    </div>
  );
}
