# CRITICAL BUG: Production Signup Broken

**Discovered During**: E2E Test Journey - Step 4 (Submit Signup)
**Severity**: 🔴 CRITICAL
**Status**: Production is broken
**Discovered By**: Claude Desktop E2E Testing
**Date**: 2026-01-20

---

## Issue

Production website (https://0711.io) signup form **cannot reach the API** due to hardcoded localhost URL.

## Root Cause

The API URL is hardcoded to `http://localhost:4080` instead of using environment variables.

**Impact:**
- ❌ Signup will **NEVER work** on production
- ❌ No new customers can register
- ❌ API endpoint is not configurable per environment
- ❌ CORS errors block all requests from production domain

## Error Details

```
Console Error:
Access to fetch at 'http://localhost:4080/api/auth/signup'
from origin 'https://0711.io' has been blocked by CORS policy:
No 'Access-Control-Allow-Origin' header is present on the requested resource.

Network Request:
POST http://localhost:4080/api/auth/signup
Status: FAILED (CORS)
Origin: https://0711.io
```

## Test Evidence

**Journey**: new_customer_with_team
**Step**: 4 - Submit Signup
**Result**: ❌ FAIL

**Steps Completed:**
1. ✅ Navigate to Marketing Website
2. ✅ Click "Get Started"
3. ✅ Fill Signup Form
4. ❌ Submit Signup → **CORS ERROR**

## Affected Files

Likely one or more of:
- `apps/website/app/signup/page.tsx` - Signup form component
- `apps/website/lib/api.ts` - API client (if exists)
- `apps/website/app/login/page.tsx` - Login form (same issue)
- `apps/website/next.config.js` - Environment config
- `.env.production` - Production environment variables

## Suggested Fix

### Option 1: Create Centralized API Client

**File**: `apps/website/lib/api.ts` (NEW)

```typescript
/**
 * API Client with environment-aware base URL
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4080';

export const apiClient = {
  async post(endpoint: string, data: any) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return response.json();
  },

  async get(endpoint: string) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return response.json();
  },
};
```

### Option 2: Update Signup Form

**File**: `apps/website/app/signup/page.tsx`

```typescript
// BEFORE (BROKEN)
const handleSubmit = async () => {
  const response = await fetch('http://localhost:4080/api/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData)
  });
  // ...
};

// AFTER (FIXED)
import { apiClient } from '@/lib/api';

const handleSubmit = async () => {
  try {
    const response = await apiClient.post('/api/auth/signup', formData);
    // Handle success
  } catch (error) {
    // Handle error
  }
};
```

### Option 3: Set Environment Variables

**File**: `.env.local` (Development)
```bash
NEXT_PUBLIC_API_URL=http://localhost:4080
```

**File**: `.env.production` (Production)
```bash
NEXT_PUBLIC_API_URL=https://api.0711.io
```

**File**: `apps/website/next.config.js` (Verify env vars exposed)
```javascript
module.exports = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
  // ... other config
};
```

## Additional Files to Check

All forms that call the API might have the same issue:
- Login form (`app/login/page.tsx`)
- Password reset (`app/forgot-password/page.tsx`)
- Expert signup (`app/expert-signup/page.tsx`)
- Contact form (if exists)

## Test Plan

1. **Implement Fix**
   - Create `lib/api.ts` with environment-aware URL
   - Update all forms to use `apiClient`
   - Set `NEXT_PUBLIC_API_URL` in `.env.production`

2. **Test Locally**
   ```bash
   # Should work with localhost
   curl http://localhost:4000
   # Fill signup form
   # Verify: POST goes to http://localhost:4080
   ```

3. **Test Production Build Locally**
   ```bash
   NEXT_PUBLIC_API_URL=https://api.0711.io npm run build
   npm start
   # Verify: API calls go to api.0711.io
   ```

4. **Deploy to Production**
   - Set environment variable on hosting platform
   - Deploy new build
   - Test on https://0711.io

5. **Re-run E2E Journey**
   - Verify Step 4 now passes
   - Complete full journey

## Priority

**🔴 CRITICAL - P0**

This blocks all new customer signups on production. Should be fixed immediately.

## Estimated Fix Time

- **Code changes**: 30 minutes
- **Testing**: 15 minutes
- **Deployment**: 10 minutes
- **Total**: ~1 hour

## Next Actions for Claude Code

1. Read this bug report
2. Search for hardcoded API URLs in website codebase
3. Create centralized API client
4. Update all forms to use it
5. Set environment variables
6. Test locally
7. Mark as fixed

---

**Reported**: 2026-01-20T10:00:00Z
**Reporter**: Claude Desktop (E2E Testing)
**Journey**: new_customer_with_team (Step 4)
