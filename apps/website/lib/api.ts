/**
 * API Client for 0711 Control Plane
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4080';
const API_PREFIX = '/api';

interface SignupData {
  companyName: string;
  contactName: string;
  email: string;
  password: string;
  companyType?: string;
  vatId?: string;
  street?: string;
  city?: string;
  postalCode?: string;
  contactPhone?: string;
}

interface LoginData {
  email: string;
  password: string;
}

interface CreateSubscriptionData {
  plan: string;
  billingCycle: string;
  paymentMethodId: string;
}

interface CreateInvoiceSubscriptionData {
  plan: string;
  billingCycle: string;
  vatId?: string;
  billingEmail?: string;
  poNumber?: string;
}

interface PartnerSignupData {
  companyName: string;
  contactName: string;
  email: string;
  password: string;
  phone?: string;
  street?: string;
  city?: string;
  postalCode?: string;
  country?: string;
  vatId?: string;
}

interface PartnerLoginData {
  email: string;
  password: string;
}

interface CreateCustomerData {
  companyName: string;
  contactName: string;
  contactEmail: string;
  contactPhone?: string;
  companyType?: string;
  tier: string;
  vatId?: string;
  street?: string;
  city?: string;
  postalCode?: string;
  country?: string;
  sendInvitation: boolean;
}

class APIClient {
  private baseURL: string;
  private token: string | null = null;

  constructor() {
    this.baseURL = `${API_URL}${API_PREFIX}`;

    // Load token from localStorage if available
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('0711_token');
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
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

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('0711_token', token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('0711_token');
    }
  }

  // Auth endpoints
  async signup(data: SignupData) {
    return this.request('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({
        company_name: data.companyName,
        contact_name: data.contactName,
        contact_email: data.email,
        password: data.password,
        company_type: data.companyType || 'GmbH',
        vat_id: data.vatId,
        street: data.street,
        city: data.city,
        postal_code: data.postalCode,
        contact_phone: data.contactPhone,
      }),
    });
  }

  async login(data: LoginData) {
    const response = await this.request<{ access_token: string; customer: any }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    this.setToken(response.access_token);
    return response;
  }

  async verifyEmail(token: string) {
    return this.request('/auth/verify-email', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  }

  // Subscription endpoints
  async createSubscription(data: CreateSubscriptionData) {
    return this.request('/subscriptions/create', {
      method: 'POST',
      body: JSON.stringify({
        plan: data.plan,
        billing_cycle: data.billingCycle,
        payment_method_id: data.paymentMethodId,
      }),
    });
  }

  async createInvoiceSubscription(data: CreateInvoiceSubscriptionData) {
    return this.request('/subscriptions/create-invoice', {
      method: 'POST',
      body: JSON.stringify({
        plan: data.plan,
        billing_cycle: data.billingCycle,
        vat_id: data.vatId,
        billing_email: data.billingEmail,
        po_number: data.poNumber,
      }),
    });
  }

  async getCurrentSubscription() {
    return this.request('/subscriptions/current', {
      method: 'GET',
    });
  }

  // Deployment endpoints
  async listDeployments() {
    return this.request('/deployments/', {
      method: 'GET',
    });
  }

  async validateLicense(licenseKey: string) {
    return this.request('/deployments/validate-license', {
      method: 'POST',
      body: JSON.stringify({ license_key: licenseKey }),
    });
  }

  // Onboarding endpoints
  async getOnboardingStatus() {
    return this.request('/onboarding/status', {
      method: 'GET',
    });
  }

  async savePlanChoice(plan: string, billingCycle: string) {
    return this.request('/onboarding/plan', {
      method: 'POST',
      body: JSON.stringify({
        plan: plan,
        billing_cycle: billingCycle,
      }),
    });
  }

  // Partner Auth endpoints
  async partnerSignup(data: PartnerSignupData) {
    return this.request('/partners/register', {
      method: 'POST',
      body: JSON.stringify({
        company_name: data.companyName,
        contact_name: data.contactName,
        contact_email: data.email,
        password: data.password,
        contact_phone: data.phone,
        street: data.street,
        city: data.city,
        postal_code: data.postalCode,
        country: data.country || 'DE',
        vat_id: data.vatId,
      }),
    });
  }

  async partnerLogin(data: PartnerLoginData) {
    const response = await this.request<{ access_token: string; partner: any; user_id: string }>('/partners/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    this.setToken(response.access_token);
    return response;
  }

  // Partner Management endpoints
  async getPartnerDashboard() {
    return this.request('/partners/dashboard', { method: 'GET' });
  }

  async getPartnerProfile() {
    return this.request('/partners/me', { method: 'GET' });
  }

  async updatePartnerProfile(data: Partial<PartnerSignupData>) {
    return this.request('/partners/me', {
      method: 'PATCH',
      body: JSON.stringify({
        company_name: data.companyName,
        contact_email: data.email,
        contact_phone: data.phone,
        street: data.street,
        city: data.city,
        postal_code: data.postalCode,
        country: data.country,
        vat_id: data.vatId,
      }),
    });
  }

  // Customer Management endpoints (for partners)
  async createCustomer(data: CreateCustomerData) {
    return this.request('/partners/customers', {
      method: 'POST',
      body: JSON.stringify({
        company_name: data.companyName,
        contact_name: data.contactName,
        contact_email: data.contactEmail,
        contact_phone: data.contactPhone,
        company_type: data.companyType,
        tier: data.tier,
        vat_id: data.vatId,
        street: data.street,
        city: data.city,
        postal_code: data.postalCode,
        country: data.country || 'DE',
        send_invitation: data.sendInvitation,
      }),
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
}

export const api = new APIClient();
export default api;
