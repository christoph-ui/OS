import Link from 'next/link';
import styles from './AuthLayout.module.css';

interface AuthLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
}

export default function AuthLayout({ children, title, subtitle }: AuthLayoutProps) {
  return (
    <div className={styles.container}>
      <div className={styles.box}>
        <Link href="/" className={styles.logo}>
          <span>0711</span>
          <div className={styles.logoBadge}>Made in Stuttgart</div>
        </Link>

        <div className={styles.header}>
          <h1>{title}</h1>
          {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
        </div>

        {children}
      </div>

      <div className={styles.footer}>
        <p>© 2025 0711 Intelligence GmbH</p>
        <div className={styles.footerLinks}>
          <Link href="/impressum">Impressum</Link>
          <span>·</span>
          <Link href="/datenschutz">Datenschutz</Link>
        </div>
      </div>
    </div>
  );
}
