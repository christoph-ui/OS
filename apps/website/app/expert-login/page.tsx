'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function ExpertLoginRedirect() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to unified login with expert role pre-selected
    router.replace('/login?role=expert');
  }, [router]);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <p>Redirecting...</p>
    </div>
  );
}
