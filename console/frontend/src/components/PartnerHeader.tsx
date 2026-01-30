'use client';

import { useEffect, useState } from 'react';

const colors = {
  dark: '#141413',
  light: '#faf9f5',
  midGray: '#b0aea5',
  lightGray: '#e8e6dc',
  orange: '#d97757',
};

interface PartnerInfo {
  id: string;
  company_name: string;
  contact_email: string;
}

export default function PartnerHeader({ title }: { title: string }) {
  const [partner, setPartner] = useState<PartnerInfo | null>(null);

  useEffect(() => {
    // Load partner info from localStorage
    const partnerData = localStorage.getItem('0711_partner');
    if (partnerData) {
      setPartner(JSON.parse(partnerData));
    }
  }, []);

  return (
    <header style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '24px 40px',
      borderBottom: `1px solid ${colors.lightGray}`,
      backgroundColor: '#fff',
    }}>
      <div>
        <h1 style={{
          fontFamily: "'Poppins', Arial, sans-serif",
          fontSize: 28,
          fontWeight: 600,
          margin: 0,
          color: colors.dark,
        }}>
          {title}
        </h1>
      </div>

      {partner && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
        }}>
          <div style={{ textAlign: 'right' }}>
            <p style={{
              fontSize: 14,
              fontWeight: 500,
              margin: 0,
              color: colors.dark,
            }}>
              {partner.company_name}
            </p>
            <p style={{
              fontSize: 12,
              margin: 0,
              color: colors.midGray,
            }}>
              {partner.contact_email}
            </p>
          </div>
          <div style={{
            width: 40,
            height: 40,
            borderRadius: '50%',
            backgroundColor: colors.orange,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: 16,
            fontWeight: 600,
          }}>
            {partner.company_name.charAt(0).toUpperCase()}
          </div>
        </div>
      )}
    </header>
  );
}
