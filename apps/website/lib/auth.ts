/**
 * Unified Auth Utilities
 * Handles authentication for both customers and experts
 */

export type UserRole = 'customer' | 'expert';

export interface DecodedToken {
  user_id: string;
  email: string;
  role: UserRole;
  customer_id?: string;
  expert_id?: string;
  exp: number;
}

export interface CurrentUser {
  id: string;
  email: string;
  role: UserRole;
  customerId?: string;
  expertId?: string;
}

const TOKEN_KEY = '0711_token';

/**
 * Simple JWT decode (no verification, just payload extraction)
 */
function decodeJWT(token: string): DecodedToken | null {
  try {
    const payload = token.split('.')[1];
    const decoded = JSON.parse(atob(payload));
    return decoded;
  } catch (error) {
    console.error('Failed to decode JWT:', error);
    return null;
  }
}

/**
 * Get current authenticated user from localStorage token
 */
export function getCurrentUser(): CurrentUser | null {
  if (typeof window === 'undefined') return null;

  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) return null;

  const decoded = decodeJWT(token);
  if (!decoded) return null;

  // Check if token is expired
  if (decoded.exp * 1000 < Date.now()) {
    clearAuth();
    return null;
  }

  return {
    id: decoded.user_id,
    email: decoded.email,
    role: decoded.role,
    customerId: decoded.customer_id,
    expertId: decoded.expert_id,
  };
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return getCurrentUser() !== null;
}

/**
 * Check if current user is a customer
 */
export function isCustomer(): boolean {
  const user = getCurrentUser();
  return user?.role === 'customer';
}

/**
 * Check if current user is an expert
 */
export function isExpert(): boolean {
  const user = getCurrentUser();
  return user?.role === 'expert';
}

/**
 * Get stored auth token
 */
export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Store auth token
 */
export function setToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(TOKEN_KEY, token);
}

/**
 * Clear auth token and user data
 */
export function clearAuth(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem('expert_token');  // Legacy
  localStorage.removeItem('expert_id');  // Legacy
  localStorage.removeItem('expert_name');  // Legacy
}

/**
 * Get appropriate dashboard URL based on user role
 */
export function getDashboardUrl(user: CurrentUser | null): string {
  if (!user) return '/login';

  if (user.role === 'expert') {
    return '/expert/dashboard';
  }

  // Customer - will need to check deployment status
  return '/dashboard';
}

/**
 * Require authentication - redirect to login if not authenticated
 * Use this in protected pages
 */
export function requireAuth(allowedRoles?: UserRole[]): CurrentUser {
  const user = getCurrentUser();

  if (!user) {
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    throw new Error('Not authenticated');
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    throw new Error('Insufficient permissions');
  }

  return user;
}
