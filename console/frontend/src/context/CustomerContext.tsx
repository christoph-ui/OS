'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface CustomerContextType {
  customerId: string;
  setCustomerId: (id: string) => void;
  impersonated: boolean;
  impersonatedCustomer: string;
}

const CustomerContext = createContext<CustomerContextType>({
  customerId: '',
  setCustomerId: () => {},
  impersonated: false,
  impersonatedCustomer: '',
});

export function CustomerProvider({ children }: { children: ReactNode }) {
  const [customerId, setCustomerId] = useState('');
  const [impersonated, setImpersonated] = useState(false);
  const [impersonatedCustomer, setImpersonatedCustomer] = useState('');

  useEffect(() => {
    // STEP 1: Check URL params first (for impersonate flow)
    const params = new URLSearchParams(window.location.search);
    const tokenFromUrl = params.get('impersonate_token');
    const customerName = params.get('customer');

    if (tokenFromUrl) {
      console.log('✓ Impersonate token from URL');
      localStorage.setItem('0711_token', tokenFromUrl);
      localStorage.setItem('0711_impersonated', 'true');
      localStorage.setItem('0711_impersonated_customer', customerName || 'Customer');

      // Clean URL (remove token from browser history)
      window.history.replaceState({}, '', window.location.pathname);

      // Reload to apply token
      window.location.reload();
      return;
    }

    // STEP 2: Extract customer_id from JWT token
    const token = localStorage.getItem('0711_token');
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const customerIdFromToken = payload.customer_id;
        if (customerIdFromToken) {
          setCustomerId(customerIdFromToken);
          console.log('✓ Customer ID from token:', customerIdFromToken);
        }
      } catch (e) {
        console.error('Failed to decode token:', e);
      }
    }

    // STEP 3: Check impersonation status
    if (localStorage.getItem('0711_impersonated') === 'true') {
      setImpersonated(true);
      setImpersonatedCustomer(localStorage.getItem('0711_impersonated_customer') || 'Customer');
    }
  }, []);

  return (
    <CustomerContext.Provider value={{ customerId, setCustomerId, impersonated, impersonatedCustomer }}>
      {children}
    </CustomerContext.Provider>
  );
}

export function useCustomer() {
  return useContext(CustomerContext);
}
