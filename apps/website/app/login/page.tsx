'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import AuthLayout from '@/components/AuthLayout';
import api from '@/lib/api';
import styles from './login.module.css';

// Get API URL from environment variable (production-safe)
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4080';

type UserRole = 'customer' | 'expert';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [userRole, setUserRole] = useState<UserRole>('customer');
  const [form, setForm] = useState({
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Pre-select role from query param
  useEffect(() => {
    const roleParam = searchParams?.get('role');
    if (roleParam === 'expert') {
      setUserRole('expert');
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (userRole === 'customer') {
        // Customer login
        const response = await api.login(form);

        // Check onboarding status to determine where to redirect
        const onboardingStatus = await api.getOnboardingStatus();

        if (onboardingStatus.status === 'completed' && onboardingStatus.has_deployment) {
          // Fully onboarded - go to console
          const deployments = await api.listDeployments();
          const consoleUrl = deployments[0]?.console_url || 'http://localhost:4020';
          window.location.href = consoleUrl;
        } else if (onboardingStatus.status === 'data_uploaded' || onboardingStatus.status === 'payment_completed') {
          // Resume at data upload/onboarding wizard
          router.push('/onboarding');
        } else if (onboardingStatus.status === 'plan_selected') {
          // Resume at payment step
          const plan = onboardingStatus.onboarding_data?.plan || 'starter';
          const cycle = onboardingStatus.onboarding_data?.billing_cycle || 'monthly';
          router.push(`/signup/payment?plan=${plan}&cycle=${cycle}`);
        } else {
          // Start from plan selection
          router.push('/signup/plan');
        }
      } else {
        // Expert login
        const response = await fetch(`${API_URL}/api/expert-auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(form)
        });

        const data = await response.json();

        if (response.ok) {
          localStorage.setItem('0711_token', data.access_token);
          localStorage.setItem('expert_id', data.expert_id);
          router.push('/expert/dashboard');
        } else {
          setError(data.detail || 'Invalid email or password');
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Welcome Back" subtitle="Sign in to your 0711 account">
      {/* Role Tabs */}
      <div className={styles.roleTabs}>
        <button
          type="button"
          className={`${styles.roleTab} ${userRole === 'customer' ? styles.active : ''}`}
          onClick={() => setUserRole('customer')}
        >
          Customer
        </button>
        <button
          type="button"
          className={`${styles.roleTab} ${userRole === 'expert' ? styles.active : ''}`}
          onClick={() => setUserRole('expert')}
        >
          Expert
        </button>
      </div>

      {error && (
        <div className={styles.error}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.formGroup}>
          <label>Email</label>
          <input
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
            placeholder="your@email.com"
            className={styles.input}
            autoComplete="email"
          />
        </div>

        <div className={styles.formGroup}>
          <label>Password</label>
          <input
            type="password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
            placeholder="Your password"
            className={styles.input}
            autoComplete="current-password"
          />
        </div>

        <div className={styles.forgotPassword}>
          <Link href="/forgot-password">
            Forgot password?
          </Link>
        </div>

        <button type="submit" disabled={loading} className={styles.submitButton}>
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
      </form>

      <p className={styles.switchPrompt}>
        Don't have an account?{' '}
        <Link href={`/signup${userRole === 'expert' ? '?role=expert' : ''}`}>
          Sign up
        </Link>
      </p>
    </AuthLayout>
  );
}
