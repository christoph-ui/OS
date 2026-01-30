'use client';

import { useState, useEffect } from 'react';
import AdminLayout from '@/components/admin/AdminLayout';
import { Users, UserPlus, Search, Filter, ShieldAlert, CheckCircle, Clock, XCircle } from 'lucide-react';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  red: '#d75757',
  green: '#788c5d',
};

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  status: string;
  customer_id: string | null;
  customer_name: string | null;
  last_login_at: string | null;
  created_at: string;
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    loadUsers();
  }, [roleFilter, statusFilter]);

  const loadUsers = async () => {
    try {
      const token = localStorage.getItem('0711_admin_token');

      const params = new URLSearchParams({
        page: '1',
        page_size: '100',
      });

      if (roleFilter !== 'all') params.append('role', roleFilter);
      if (statusFilter !== 'all') params.append('status', statusFilter);
      if (search) params.append('search', search);

      const response = await fetch(`http://localhost:4080/api/admin/users?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setUsers(data.users || []);
        setTotal(data.total || 0);
      }
    } catch (error) {
      console.error('Error loading users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadUsers();
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'platform_admin': return colors.red;
      case 'partner_admin': return colors.orange;
      case 'customer_admin': return colors.blue;
      default: return colors.midGray;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle size={16} color={colors.green} />;
      case 'invited': return <Clock size={16} color={colors.orange} />;
      case 'suspended': return <XCircle size={16} color={colors.red} />;
      default: return <XCircle size={16} color={colors.midGray} />;
    }
  };

  if (loading) {
    return (
      <AdminLayout>
        <div style={{ padding: 40, textAlign: 'center' }}>Loading users...</div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      {/* Header */}
      <div style={{ padding: '32px 40px', borderBottom: `1px solid ${colors.lightGray}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ fontSize: 28, fontWeight: 600, margin: 0, color: colors.dark }}>
              All Users
            </h1>
            <p style={{ fontSize: 15, color: colors.midGray, margin: '8px 0 0' }}>
              {total} users across all customers
            </p>
          </div>
        </div>
      </div>

      <div style={{ padding: 40 }}>
        {/* Filters */}
        <div style={{
          backgroundColor: colors.light,
          border: `2px solid ${colors.lightGray}`,
          borderRadius: 12,
          padding: 24,
          marginBottom: 24,
        }}>
          <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end' }}>
            {/* Search */}
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', fontSize: 13, color: colors.midGray, marginBottom: 6 }}>
                Search
              </label>
              <div style={{ position: 'relative' }}>
                <Search size={18} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: colors.midGray }} />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder="Search by name or email..."
                  style={{
                    width: '100%',
                    padding: '12px 12px 12px 40px',
                    border: `1.5px solid ${colors.lightGray}`,
                    borderRadius: 8,
                    fontSize: 14,
                  }}
                />
              </div>
            </div>

            {/* Role Filter */}
            <div style={{ width: 200 }}>
              <label style={{ display: 'block', fontSize: 13, color: colors.midGray, marginBottom: 6 }}>
                Role
              </label>
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                style={{
                  width: '100%',
                  padding: 12,
                  border: `1.5px solid ${colors.lightGray}`,
                  borderRadius: 8,
                  fontSize: 14,
                }}
              >
                <option value="all">All Roles</option>
                <option value="platform_admin">Platform Admin</option>
                <option value="partner_admin">Partner Admin</option>
                <option value="customer_admin">Customer Admin</option>
                <option value="customer_user">Customer User</option>
              </select>
            </div>

            {/* Status Filter */}
            <div style={{ width: 160 }}>
              <label style={{ display: 'block', fontSize: 13, color: colors.midGray, marginBottom: 6 }}>
                Status
              </label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{
                  width: '100%',
                  padding: 12,
                  border: `1.5px solid ${colors.lightGray}`,
                  borderRadius: 8,
                  fontSize: 14,
                }}
              >
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="invited">Invited</option>
                <option value="suspended">Suspended</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>

            <button
              onClick={handleSearch}
              style={{
                padding: '12px 24px',
                backgroundColor: colors.red,
                color: colors.light,
                border: 'none',
                borderRadius: 8,
                fontSize: 14,
                fontWeight: 500,
                cursor: 'pointer',
              }}
            >
              Search
            </button>
          </div>
        </div>

        {/* Users Table */}
        <div style={{
          backgroundColor: colors.light,
          border: `2px solid ${colors.lightGray}`,
          borderRadius: 12,
          padding: 24,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
            <h2 style={{ fontSize: 18, fontWeight: 600, margin: 0, color: colors.dark }}>
              Users ({users.length})
            </h2>
            <button
              onClick={loadUsers}
              style={{
                padding: '8px 16px',
                backgroundColor: colors.lightGray,
                border: 'none',
                borderRadius: 8,
                cursor: 'pointer',
                fontSize: 14,
              }}
            >
              Refresh
            </button>
          </div>

          {users.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 60, color: colors.midGray }}>
              <Users size={48} style={{ margin: '0 auto 16px', opacity: 0.5 }} />
              <div style={{ fontSize: 16 }}>No users found</div>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: `2px solid ${colors.lightGray}` }}>
                    <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>Name</th>
                    <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>Email</th>
                    <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>Role</th>
                    <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>Customer</th>
                    <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>Status</th>
                    <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>Last Login</th>
                    <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(user => (
                    <tr key={user.id} style={{ borderBottom: `1px solid ${colors.lightGray}` }}>
                      <td style={{ padding: '16px', fontSize: 14, fontWeight: 500 }}>
                        {user.first_name} {user.last_name}
                      </td>
                      <td style={{ padding: '16px', fontSize: 14, color: colors.midGray, fontFamily: 'monospace' }}>
                        {user.email}
                      </td>
                      <td style={{ padding: '16px', fontSize: 13 }}>
                        <span style={{
                          padding: '4px 12px',
                          backgroundColor: `${getRoleBadgeColor(user.role)}20`,
                          color: getRoleBadgeColor(user.role),
                          borderRadius: 12,
                          fontSize: 11,
                          fontWeight: 600,
                          textTransform: 'uppercase',
                        }}>
                          {user.role.replace('_', ' ')}
                        </span>
                      </td>
                      <td style={{ padding: '16px', fontSize: 14, color: colors.midGray }}>
                        {user.customer_name || '-'}
                      </td>
                      <td style={{ padding: '16px', fontSize: 13 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          {getStatusIcon(user.status)}
                          <span style={{ textTransform: 'capitalize' }}>{user.status}</span>
                        </div>
                      </td>
                      <td style={{ padding: '16px', fontSize: 13, color: colors.midGray }}>
                        {user.last_login_at ? new Date(user.last_login_at).toLocaleDateString() : 'Never'}
                      </td>
                      <td style={{ padding: '16px', fontSize: 13, color: colors.midGray }}>
                        {new Date(user.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Stats Summary */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 20, marginTop: 24 }}>
          <div style={{
            backgroundColor: colors.light,
            border: `2px solid ${colors.lightGray}`,
            borderRadius: 12,
            padding: 20,
            textAlign: 'center',
          }}>
            <div style={{ fontSize: 28, fontWeight: 600, color: colors.red, marginBottom: 8 }}>
              {users.filter(u => u.role === 'platform_admin').length}
            </div>
            <div style={{ fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>
              Platform Admins
            </div>
          </div>

          <div style={{
            backgroundColor: colors.light,
            border: `2px solid ${colors.lightGray}`,
            borderRadius: 12,
            padding: 20,
            textAlign: 'center',
          }}>
            <div style={{ fontSize: 28, fontWeight: 600, color: colors.orange, marginBottom: 8 }}>
              {users.filter(u => u.role === 'partner_admin').length}
            </div>
            <div style={{ fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>
              Partner Admins
            </div>
          </div>

          <div style={{
            backgroundColor: colors.light,
            border: `2px solid ${colors.lightGray}`,
            borderRadius: 12,
            padding: 20,
            textAlign: 'center',
          }}>
            <div style={{ fontSize: 28, fontWeight: 600, color: colors.dark, marginBottom: 8 }}>
              {users.filter(u => u.role === 'customer_admin').length}
            </div>
            <div style={{ fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>
              Customer Admins
            </div>
          </div>

          <div style={{
            backgroundColor: colors.light,
            border: `2px solid ${colors.lightGray}`,
            borderRadius: 12,
            padding: 20,
            textAlign: 'center',
          }}>
            <div style={{ fontSize: 28, fontWeight: 600, color: colors.dark, marginBottom: 8 }}>
              {users.filter(u => u.role === 'customer_user').length}
            </div>
            <div style={{ fontSize: 13, color: colors.midGray, textTransform: 'uppercase' }}>
              Customer Users
            </div>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}
