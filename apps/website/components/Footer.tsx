import Link from 'next/link';
import styles from './Footer.module.css';

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.footerLogo}>
        <span>0711</span>
      </div>
      <p>The future of enterprise is not enterprise software. It's the end of it.</p>
      <div className={styles.footerLinks}>
        <Link href="/bloodsuckers" className={styles.hiddenLink}>©</Link>
        <span> 2025 0711 Intelligence GmbH</span>
        <span> • </span>
        <Link href="/impressum">Impressum</Link>
        <span> • </span>
        <Link href="/datenschutz">Datenschutz</Link>
      </div>
    </footer>
  );
}
