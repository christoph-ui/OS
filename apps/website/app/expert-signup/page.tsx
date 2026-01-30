'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function ExpertSignupRedirect() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to unified signup with expert role pre-selected
    router.replace('/signup?role=expert');
  }, [router]);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <p>Redirecting...</p>
    </div>
  );
}
