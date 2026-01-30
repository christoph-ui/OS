'use client';

import Link from 'next/link';
import { useState } from 'react';
import styles from './Navigation.module.css';

interface NavigationProps {
  variant?: 'light' | 'dark';
  links?: Array<{ href: string; label: string }>;
}

export default function Navigation({ variant = 'light', links }: NavigationProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const defaultLinks = [
    { href: '/#deployment', label: 'Deployment' },
    { href: '/#how', label: 'How It Works' },
    { href: '/#sovereignty', label: 'Sovereignty' },
    { href: '/pricing', label: 'Pricing' },
    { href: '/builders', label: 'For Builders' },
    { href: '/experts', label: 'Expert Network' },
  ];

  const navLinks = links || defaultLinks;

  return (
    <nav className={`${styles.nav} ${variant === 'dark' ? styles.dark : ''}`}>
      <Link href="/" className={styles.logo}>
        <span>0711</span>
        <div className={styles.logoBadge}>Made in Stuttgart</div>
      </Link>

      <ul className={styles.navLinks}>
        {navLinks.map((link, idx) => (
          <li key={idx}>
            <Link href={link.href}>{link.label}</Link>
          </li>
        ))}
      </ul>

      <div className={styles.authButtons}>
        <Link href="/login" className={styles.loginLink}>
          Login
        </Link>
        <Link href="/signup" className={styles.ctaButton}>
          Get Started
        </Link>
      </div>

      {/* Mobile menu button */}
      <button
        className={styles.mobileMenu}
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        aria-label="Toggle menu"
      >
        ☰
      </button>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className={styles.mobileMenuOverlay} onClick={() => setMobileMenuOpen(false)}>
          <div className={styles.mobileMenuContent}>
            {navLinks.map((link, idx) => (
              <Link key={idx} href={link.href} onClick={() => setMobileMenuOpen(false)}>
                {link.label}
              </Link>
            ))}
            <Link href="/signup" className={styles.mobileCta} onClick={() => setMobileMenuOpen(false)}>
              Get Started
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}
