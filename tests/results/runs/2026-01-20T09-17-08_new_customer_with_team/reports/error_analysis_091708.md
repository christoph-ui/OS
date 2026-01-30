# Critical Bug: Production Signup Form Broken

## Issue

Production website (0711.io) signup form cannot reach the API.

## Root Cause

The API URL is hardcoded to `http://localhost:4080` instead of using environment variables. This means:

1. Signup will **never work** on production
2. The API endpoint is not configurable per environment
3. CORS errors block all API requests from production domain

## Error Details

```
Access to fetch at 'http://localhost:4080/api/auth/signup' 
from origin 'https://0711.io' has been blocked by CORS policy: 
No 'Access-Control-Allow-Origin' header is present.
```

## Affected Files

Likely one of:
- `apps/website/app/signup/page.tsx`
- `apps/website/lib/api.ts`
- `apps/website/next.config.js`

## Suggested Fix

### 1. Create API Client with Environment Variable

```typescript
// apps/website/lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4080';

export const apiClient = {
  async post(endpoint: string, data: any) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  }
};
```

### 2. Update Signup Form

```typescript
// apps/website/app/signup/page.tsx
import { apiClient } from '@/lib/api';

const handleSubmit = async () => {
  const response = await apiClient.post('/api/auth/signup', formData);
  // ...
};
```

### 3. Set Environment Variable for Production

```bash
# .env.production
NEXT_PUBLIC_API_URL=https://api.0711.io
```

## Priority

**CRITICAL** - Production signup is completely broken. No new customers can register.

## Test Plan

1. Implement fix
2. Test locally: signup should work on localhost:4000
3. Deploy to production
4. Test on 0711.io: signup should work
5. Re-run E2E journey to verify
