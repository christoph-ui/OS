'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import PartnerHeader from '@/components/PartnerHeader';
import { useToast } from '@/components/Toast';
import { TableSkeleton } from '@/components/LoadingSkeleton';
import consoleAPI from '@/lib/api';

const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  blue: '#6a9bcc',
  green: '#788c5d',
  red: '#d75757',
};

interface Customer {
  id: string;
  company_name: string;
  contact_email: string;
  tier: string;
  status: string;
  partner_id: string;
  created_at: string;
  onboarding_status: string;
}

export default function CustomerListPage() {
  const router = useRouter();
  const toast = useToast();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [tierFilter, setTierFilter] = useState('');
  const [selectedCustomers, setSelectedCustomers] = useState<Set<string>>(new Set());
  const [bulkActionLoading, setBulkActionLoading] = useState(false);

  useEffect(() => {
    loadCustomers();
  }, [page, statusFilter, tierFilter]);

  const loadCustomers = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('0711_token');
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '20',
      });

      if (statusFilter) params.append('status', statusFilter);
      if (tierFilter) params.append('tier', tierFilter);

      const response = await fetch(`http://localhost:4080/api/partners/customers?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error('Failed to load customers');

      const data = await response.json();
      setCustomers(data.customers || []);
      setTotal(data.total || 0);
    } catch (error) {
      console.error('Error loading customers:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredCustomers = customers.filter(c =>
    searchQuery === '' ||
    c.company_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.contact_email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Bulk Actions
  const toggleSelectAll = () => {
    if (selectedCustomers.size === filteredCustomers.length) {
      setSelectedCustomers(new Set());
    } else {
      setSelectedCustomers(new Set(filteredCustomers.map(c => c.id)));
    }
  };

  const toggleSelectCustomer = (customerId: string) => {
    const newSelected = new Set(selectedCustomers);
    if (newSelected.has(customerId)) {
      newSelected.delete(customerId);
    } else {
      newSelected.add(customerId);
    }
    setSelectedCustomers(newSelected);
  };

  const exportToCSV = () => {
    const exportData = filteredCustomers.filter(c =>
      selectedCustomers.size === 0 || selectedCustomers.has(c.id)
    );

    if (exportData.length === 0) {
      toast.warning('Keine Kunden zum Exportieren ausgewählt');
      return;
    }

    const headers = ['Firma', 'E-Mail', 'Tier', 'Status', 'Onboarding', 'Erstellt'];
    const rows = exportData.map(c => [
      c.company_name,
      c.contact_email,
      c.tier,
      c.status,
      c.onboarding_status,
      new Date(c.created_at).toLocaleDateString('de-DE'),
    ]);

    const csv = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `customers_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();

    toast.success(`${exportData.length} Kunden als CSV exportiert`);
  };

  const exportToExcel = () => {
    // For Excel, we use CSV with proper BOM for Excel compatibility
    const exportData = filteredCustomers.filter(c =>
      selectedCustomers.size === 0 || selectedCustomers.has(c.id)
    );

    if (exportData.length === 0) {
      toast.warning('Keine Kunden zum Exportieren ausgewählt');
      return;
    }

    const headers = ['Firma', 'E-Mail', 'Tier', 'Status', 'Onboarding', 'Erstellt'];
    const rows = exportData.map(c => [
      c.company_name,
      c.contact_email,
      c.tier,
      c.status,
      c.onboarding_status,
      new Date(c.created_at).toLocaleDateString('de-DE'),
    ]);

    const csv = [
      headers.join('\t'),
      ...rows.map(row => row.join('\t'))
    ].join('\n');

    const blob = new Blob(['\ufeff' + csv], { type: 'application/vnd.ms-excel;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `customers_${new Date().toISOString().split('T')[0]}.xlsx`;
    link.click();

    toast.success(`${exportData.length} Kunden als Excel exportiert`);
  };

  const bulkDelete = async () => {
    if (selectedCustomers.size === 0) return;

    if (!confirm(`${selectedCustomers.size} Kunden wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.`)) return;

    setBulkActionLoading(true);
    try {
      await consoleAPI.bulkDeleteCustomers(Array.from(selectedCustomers));

      toast.success(`${selectedCustomers.size} Kunden erfolgreich gelöscht`);

      // Reload customers and clear selection
      setSelectedCustomers(new Set());
      await loadCustomers();
    } catch (error) {
      console.error('Error deleting customers:', error);
      toast.error(error instanceof Error ? error.message : 'Fehler beim Löschen');
    } finally {
      setBulkActionLoading(false);
    }
  };

  return (
    <div>
      <PartnerHeader title="Kunden" />

      <div style={{ padding: 40 }}>
        {/* Header Actions */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 32,
        }}>
          <div style={{
            flex: 1,
            maxWidth: 400,
            position: 'relative',
          }}>
            <svg
              style={{
                position: 'absolute',
                left: 16,
                top: '50%',
                transform: 'translateY(-50%)',
                width: 18,
                height: 18,
                color: colors.midGray,
              }}
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              type="text"
              placeholder="Suche nach Firma oder E-Mail..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '12px 16px 12px 44px',
                border: `1.5px solid ${colors.lightGray}`,
                borderRadius: 10,
                fontSize: 14,
                fontFamily: "'Lora', Georgia, serif",
                backgroundColor: '#fff',
                outline: 'none',
                transition: 'border-color 0.2s',
              }}
              onFocus={(e) => e.currentTarget.style.borderColor = colors.orange}
              onBlur={(e) => e.currentTarget.style.borderColor = colors.lightGray}
            />
          </div>

          <button
            onClick={() => router.push('/partner/customers/new')}
            style={{
              padding: '12px 24px',
              backgroundColor: colors.orange,
              color: '#fff',
              border: 'none',
              borderRadius: 10,
              fontSize: 15,
              fontWeight: 600,
              cursor: 'pointer',
              fontFamily: "'Poppins', Arial, sans-serif",
              boxShadow: `0 4px 12px ${colors.orange}40`,
              transition: 'all 0.2s',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = 'translateY(-1px)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            + Neuer Kunde
          </button>
        </div>

        {/* Filters + Bulk Actions */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 24,
        }}>
          <div style={{ display: 'flex', gap: 12 }}>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{
                padding: '8px 12px',
                border: `1px solid ${colors.lightGray}`,
                borderRadius: 8,
                fontSize: 14,
                backgroundColor: '#fff',
                cursor: 'pointer',
                outline: 'none',
              }}
            >
              <option value="">Alle Status</option>
              <option value="active">Active</option>
              <option value="churned">Churned</option>
              <option value="suspended">Suspended</option>
            </select>

            <select
              value={tierFilter}
              onChange={(e) => setTierFilter(e.target.value)}
              style={{
                padding: '8px 12px',
                border: `1px solid ${colors.lightGray}`,
                borderRadius: 8,
                fontSize: 14,
                backgroundColor: '#fff',
                cursor: 'pointer',
                outline: 'none',
              }}
            >
              <option value="">Alle Tiers</option>
              <option value="starter">Starter</option>
              <option value="professional">Professional</option>
              <option value="business">Business</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>

          {/* Bulk Actions */}
          {selectedCustomers.size > 0 && (
            <div style={{
              display: 'flex',
              gap: 8,
              alignItems: 'center',
            }}>
              <span style={{
                fontSize: 14,
                color: colors.midGray,
                marginRight: 8,
              }}>
                {selectedCustomers.size} ausgewählt
              </span>
              <button
                onClick={exportToCSV}
                style={{
                  padding: '8px 16px',
                  backgroundColor: colors.blue,
                  color: '#fff',
                  border: 'none',
                  borderRadius: 8,
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                📄 CSV Export
              </button>
              <button
                onClick={exportToExcel}
                style={{
                  padding: '8px 16px',
                  backgroundColor: colors.green,
                  color: '#fff',
                  border: 'none',
                  borderRadius: 8,
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                📊 Excel Export
              </button>
              <button
                onClick={bulkDelete}
                disabled={bulkActionLoading}
                style={{
                  padding: '8px 16px',
                  backgroundColor: colors.red,
                  color: '#fff',
                  border: 'none',
                  borderRadius: 8,
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: bulkActionLoading ? 'not-allowed' : 'pointer',
                  opacity: bulkActionLoading ? 0.6 : 1,
                }}
              >
                🗑 Löschen
              </button>
            </div>
          )}
        </div>

        {/* Customer Table */}
        {loading ? (
          <TableSkeleton rows={10} columns={8} />
        ) : filteredCustomers.length > 0 ? (
          <div
            className="customer-table-wrapper"
            style={{
              backgroundColor: '#fff',
              borderRadius: 16,
              border: `1.5px solid ${colors.lightGray}`,
              overflow: 'hidden',
            }}
          >
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 800 }}>
              <thead>
                <tr style={{ backgroundColor: colors.light }}>
                  <th style={{ padding: '14px 24px', width: 40 }}>
                    <input
                      type="checkbox"
                      checked={selectedCustomers.size === filteredCustomers.length && filteredCustomers.length > 0}
                      onChange={toggleSelectAll}
                      style={{ width: 16, height: 16, cursor: 'pointer' }}
                    />
                  </th>
                  <th style={{
                    padding: '14px 24px',
                    textAlign: 'left',
                    fontSize: 11,
                    fontWeight: 600,
                    color: colors.midGray,
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                  }}>
                    Firma
                  </th>
                  <th style={{
                    padding: '14px 24px',
                    textAlign: 'left',
                    fontSize: 11,
                    fontWeight: 600,
                    color: colors.midGray,
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                  }}>
                    E-Mail
                  </th>
                  <th style={{
                    padding: '14px 24px',
                    textAlign: 'left',
                    fontSize: 11,
                    fontWeight: 600,
                    color: colors.midGray,
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                  }}>
                    Tier
                  </th>
                  <th style={{
                    padding: '14px 24px',
                    textAlign: 'left',
                    fontSize: 11,
                    fontWeight: 600,
                    color: colors.midGray,
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                  }}>
                    Status
                  </th>
                  <th style={{
                    padding: '14px 24px',
                    textAlign: 'left',
                    fontSize: 11,
                    fontWeight: 600,
                    color: colors.midGray,
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                  }}>
                    Onboarding
                  </th>
                  <th style={{
                    padding: '14px 24px',
                    textAlign: 'left',
                    fontSize: 11,
                    fontWeight: 600,
                    color: colors.midGray,
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                  }}>
                    Erstellt
                  </th>
                  <th style={{ padding: '14px 24px', width: 80 }}></th>
                </tr>
              </thead>
              <tbody>
                {filteredCustomers.map((customer) => (
                  <tr
                    key={customer.id}
                    style={{
                      borderTop: `1px solid ${colors.lightGray}`,
                      backgroundColor: selectedCustomers.has(customer.id) ? `${colors.orange}08` : 'transparent',
                      transition: 'background 0.15s',
                    }}
                    onMouseOver={(e) => {
                      if (!selectedCustomers.has(customer.id)) {
                        e.currentTarget.style.backgroundColor = colors.light;
                      }
                    }}
                    onMouseOut={(e) => {
                      if (!selectedCustomers.has(customer.id)) {
                        e.currentTarget.style.backgroundColor = 'transparent';
                      }
                    }}
                  >
                    <td style={{ padding: '16px 24px' }}>
                      <input
                        type="checkbox"
                        checked={selectedCustomers.has(customer.id)}
                        onChange={() => toggleSelectCustomer(customer.id)}
                        onClick={(e) => e.stopPropagation()}
                        style={{ width: 16, height: 16, cursor: 'pointer' }}
                      />
                    </td>
                    <td
                      style={{ padding: '16px 24px', fontSize: 14, fontWeight: 500, cursor: 'pointer' }}
                      onClick={() => router.push(`/partner/customers/${customer.id}`)}
                    >
                      {customer.company_name}
                    </td>
                    <td
                      style={{ padding: '16px 24px', fontSize: 14, color: colors.midGray, cursor: 'pointer' }}
                      onClick={() => router.push(`/partner/customers/${customer.id}`)}
                    >
                      {customer.contact_email}
                    </td>
                    <td
                      style={{ padding: '16px 24px', cursor: 'pointer' }}
                      onClick={() => router.push(`/partner/customers/${customer.id}`)}
                    >
                      <span style={{
                        padding: '4px 12px',
                        backgroundColor: `${colors.blue}15`,
                        borderRadius: 6,
                        fontSize: 12,
                        color: colors.blue,
                        fontWeight: 600,
                      }}>
                        {customer.tier}
                      </span>
                    </td>
                    <td
                      style={{ padding: '16px 24px', cursor: 'pointer' }}
                      onClick={() => router.push(`/partner/customers/${customer.id}`)}
                    >
                      <span style={{
                        padding: '4px 12px',
                        backgroundColor: customer.status === 'active' ? `${colors.green}15` : `${colors.midGray}15`,
                        borderRadius: 6,
                        fontSize: 12,
                        color: customer.status === 'active' ? colors.green : colors.midGray,
                        fontWeight: 600,
                      }}>
                        {customer.status}
                      </span>
                    </td>
                    <td
                      style={{ padding: '16px 24px', fontSize: 13, color: colors.midGray, cursor: 'pointer' }}
                      onClick={() => router.push(`/partner/customers/${customer.id}`)}
                    >
                      {customer.onboarding_status}
                    </td>
                    <td
                      style={{ padding: '16px 24px', fontSize: 13, color: colors.midGray, cursor: 'pointer' }}
                      onClick={() => router.push(`/partner/customers/${customer.id}`)}
                    >
                      {new Date(customer.created_at).toLocaleDateString('de-DE')}
                    </td>
                    <td style={{ padding: '16px 24px' }}>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/partner/customers/${customer.id}/edit`);
                        }}
                        style={{
                          padding: '6px 12px',
                          backgroundColor: colors.lightGray,
                          border: 'none',
                          borderRadius: 6,
                          fontSize: 12,
                          cursor: 'pointer',
                          color: colors.dark,
                        }}
                      >
                        ✏ Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            <div style={{
              padding: '16px 24px',
              borderTop: `1px solid ${colors.lightGray}`,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}>
              <p style={{
                margin: 0,
                fontSize: 13,
                color: colors.midGray,
              }}>
                {total} Kunden gesamt
              </p>
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  style={{
                    padding: '6px 12px',
                    border: `1px solid ${colors.lightGray}`,
                    borderRadius: 6,
                    backgroundColor: '#fff',
                    cursor: page === 1 ? 'not-allowed' : 'pointer',
                    fontSize: 13,
                    opacity: page === 1 ? 0.5 : 1,
                  }}
                >
                  ←
                </button>
                <span style={{
                  padding: '6px 12px',
                  fontSize: 13,
                  color: colors.dark,
                }}>
                  Seite {page}
                </span>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={customers.length < 20}
                  style={{
                    padding: '6px 12px',
                    border: `1px solid ${colors.lightGray}`,
                    borderRadius: 6,
                    backgroundColor: '#fff',
                    cursor: customers.length < 20 ? 'not-allowed' : 'pointer',
                    fontSize: 13,
                    opacity: customers.length < 20 ? 0.5 : 1,
                  }}
                >
                  →
                </button>
              </div>
            </div>
            </div>
          </div>
        ) : (
          <div style={{
            padding: 80,
            textAlign: 'center',
            backgroundColor: '#fff',
            borderRadius: 16,
            border: `1.5px dashed ${colors.lightGray}`,
          }}>
            <p style={{ fontSize: 16, color: colors.midGray, margin: '0 0 16px' }}>
              {searchQuery ? 'Keine Kunden gefunden' : 'Noch keine Kunden erstellt'}
            </p>
            {!searchQuery && (
              <button
                onClick={() => router.push('/partner/customers/new')}
                style={{
                  padding: '10px 20px',
                  backgroundColor: colors.orange,
                  color: '#fff',
                  border: 'none',
                  borderRadius: 8,
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Ersten Kunden erstellen
              </button>
            )}
          </div>
        )}
      </div>

      {/* Responsive Styles */}
      <style jsx global>{`
        @media (max-width: 1024px) {
          .customer-table-wrapper {
            overflow-x: auto !important;
          }
        }

        @media (max-width: 768px) {
          /* Stack filters vertically on mobile */
          .filters-row {
            flex-direction: column !important;
            align-items: stretch !important;
          }

          /* Hide some table columns on mobile */
          table th:nth-child(6),
          table td:nth-child(6),
          table th:nth-child(7),
          table td:nth-child(7) {
            display: none;
          }

          /* Adjust padding */
          .customer-table-wrapper {
            margin: 0 -20px !important;
            border-radius: 0 !important;
          }
        }

        @media (max-width: 480px) {
          /* Further reduce columns on very small screens */
          table th:nth-child(4),
          table td:nth-child(4),
          table th:nth-child(5),
          table td:nth-child(5) {
            display: none;
          }

          table {
            font-size: 12px !important;
          }

          th, td {
            padding: 8px 10px !important;
          }
        }
      `}</style>
    </div>
  );
}
