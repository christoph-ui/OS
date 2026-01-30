/**
 * API Client for 0711 Console
 * Shared client for both customer and partner portals
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4080';
const API_PREFIX = '/api';

class ConsoleAPIClient {
  private baseURL: string;

  constructor() {
    this.baseURL = `${API_URL}${API_PREFIX}`;
  }

  private getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('0711_token');
    }
    return null;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const token = this.getToken();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Partner endpoints
  async getPartnerDashboard() {
    return this.request('/partners/dashboard', { method: 'GET' });
  }

  async getPartnerProfile() {
    return this.request('/partners/me', { method: 'GET' });
  }

  async updatePartnerProfile(data: any) {
    return this.request('/partners/me', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async listCustomers(params: { page?: number; page_size?: number; status?: string; tier?: string } = {}) {
    const query = new URLSearchParams();
    if (params.page) query.append('page', params.page.toString());
    if (params.page_size) query.append('page_size', params.page_size.toString());
    if (params.status) query.append('status', params.status);
    if (params.tier) query.append('tier', params.tier);

    return this.request(`/partners/customers?${query.toString()}`, { method: 'GET' });
  }

  async getCustomer(customerId: string) {
    return this.request(`/partners/customers/${customerId}`, { method: 'GET' });
  }

  async createCustomer(data: any) {
    return this.request('/partners/customers', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateCustomer(customerId: string, data: any) {
    return this.request(`/partners/customers/${customerId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async getDeployments(customerId: string) {
    return this.request(`/deployments/?customer_id=${customerId}`, { method: 'GET' });
  }

  async deleteCustomer(customerId: string) {
    return this.request(`/partners/customers/${customerId}`, { method: 'DELETE' });
  }

  async bulkDeleteCustomers(customerIds: string[]) {
    return this.request('/partners/customers/bulk-delete', {
      method: 'POST',
      body: JSON.stringify(customerIds),
    });
  }

  async getCustomerUsage(customerId: string) {
    return this.request(`/partners/customers/${customerId}/usage`, { method: 'GET' });
  }
}

export const consoleAPI = new ConsoleAPIClient();
export default consoleAPI;
