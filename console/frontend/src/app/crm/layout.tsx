'use client';

import React from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { colors } from '@/lib/theme';
import {
  LayoutDashboard, Users, Building2, Target, CheckSquare,
  BarChart3, Settings, Search, Bell, Plus, LogOut
} from 'lucide-react';

const navItems = [
  { id: 'dashboard', label: 'Dashboard', path: '/crm', icon: LayoutDashboard },
  { id: 'contacts', label: 'Kontakte', path: '/crm/contacts', icon: Users },
  { id: 'companies', label: 'Firmen', path: '/crm/companies', icon: Building2 },
  { id: 'deals', label: 'Deals', path: '/crm/deals', icon: Target },
  { id: 'activities', label: 'Aktivitäten', path: '/crm/activities', icon: CheckSquare },
  { id: 'reports', label: 'Berichte', path: '/crm/reports', icon: BarChart3 },
];

export default function CRMLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  const isActive = (path: string) => {
    if (path === '/crm') return pathname === '/crm';
    return pathname?.startsWith(path);
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: colors.light }}>
      {/* Sidebar */}
      <aside style={{
        width: 260,
        backgroundColor: colors.dark,
        display: 'flex',
        flexDirection: 'column',
      }}>
        {/* Logo */}
        <div style={{
          padding: '24px',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}>
          <h1 style={{
            fontSize: 22,
            fontWeight: 700,
            color: 'white',
            margin: 0,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}>
            <span style={{
              width: 36,
              height: 36,
              borderRadius: 8,
              backgroundColor: colors.orange,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 18,
            }}>
              📊
            </span>
            CRM
          </h1>
        </div>

        {/* Quick Add */}
        <div style={{ padding: '16px 20px' }}>
          <button
            onClick={() => router.push('/crm/deals?new=1')}
            style={{
              width: '100%',
              padding: '12px 16px',
              backgroundColor: colors.orange,
              color: 'white',
              border: 'none',
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
            }}
          >
            <Plus size={18} />
            Neuer Deal
          </button>
        </div>

        {/* Navigation */}
        <nav style={{ flex: 1, padding: '8px 12px' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            return (
              <button
                key={item.id}
                onClick={() => router.push(item.path)}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  backgroundColor: active ? 'rgba(255,255,255,0.1)' : 'transparent',
                  color: active ? 'white' : 'rgba(255,255,255,0.6)',
                  border: 'none',
                  borderRadius: 8,
                  fontSize: 14,
                  fontWeight: 500,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  marginBottom: 4,
                  textAlign: 'left',
                }}
              >
                <Icon size={20} />
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* User */}
        <div style={{
          padding: '16px 20px',
          borderTop: '1px solid rgba(255,255,255,0.1)',
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}>
            <div style={{
              width: 40,
              height: 40,
              borderRadius: '50%',
              backgroundColor: colors.blue,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontWeight: 600,
            }}>
              MK
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ color: 'white', fontSize: 14, fontWeight: 500 }}>Max Kaufmann</div>
              <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: 12 }}>Vertrieb</div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Top Bar */}
        <header style={{
          height: 64,
          backgroundColor: 'white',
          borderBottom: `1px solid ${colors.lightGray}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
        }}>
          {/* Search */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 16px',
            backgroundColor: colors.light,
            borderRadius: 8,
            width: 400,
          }}>
            <Search size={18} color={colors.midGray} />
            <input
              type="text"
              placeholder="Suchen... (Kontakte, Firmen, Deals)"
              style={{
                flex: 1,
                border: 'none',
                backgroundColor: 'transparent',
                fontSize: 14,
                outline: 'none',
              }}
            />
            <span style={{
              fontSize: 11,
              color: colors.midGray,
              padding: '2px 6px',
              backgroundColor: 'white',
              borderRadius: 4,
            }}>
              ⌘K
            </span>
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <button style={{
              width: 40,
              height: 40,
              borderRadius: 8,
              backgroundColor: colors.light,
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
            }}>
              <Bell size={20} color={colors.midGray} />
              <span style={{
                position: 'absolute',
                top: 8,
                right: 8,
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: colors.orange,
              }} />
            </button>
            <button style={{
              width: 40,
              height: 40,
              borderRadius: 8,
              backgroundColor: colors.light,
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Settings size={20} color={colors.midGray} />
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main style={{
          flex: 1,
          overflow: 'auto',
          padding: 24,
        }}>
          {children}
        </main>
      </div>
    </div>
  );
}
