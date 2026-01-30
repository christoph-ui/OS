# Expert Login - Quick Test Guide

## ✅ What's Been Set Up

1. **Database**:
   - ✅ `password_hash` column added to experts table
   - ✅ Test expert account created with credentials

2. **Backend**:
   - ✅ Expert auth routes created (`api/routes/expert_auth.py`)
   - ✅ Login endpoint: `POST /api/expert-auth/login`
   - ✅ Password hashing with bcrypt
   - ✅ JWT token generation

3. **Frontend**:
   - ✅ Expert login page created (`/expert-login`)
   - ✅ Beautiful UI matching 0711 design
   - ✅ Error handling
   - ✅ Link to signup page

---

## 🔑 Test Credentials

**Email**: `sarah@0711.expert`
**Password**: `Expert123!`

**Expert Details**:
- Name: Sarah Mueller
- Title: Senior Tax Specialist
- MCPs: CTAX, FPA, LEGAL
- Rating: 4.9 ⭐
- Status: Active & Verified

---

## 🚀 How to Login

### Option 1: Via Frontend (Recommended)

**1. Visit the login page**:
```
http://localhost:4000/expert-login
```

**2. Enter credentials**:
- Email: `sarah@0711.expert`
- Password: `Expert123!`

**3. Click "Sign In"**

**4. You'll be redirected to**:
```
http://localhost:4000/expert/dashboard
```

### Option 2: Via API (Testing)

**Test the login endpoint directly**:
```bash
curl -X POST http://localhost:4080/api/expert-auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "sarah@0711.expert",
    "password": "Expert123!"
  }'
```

**Expected response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expert_id": "e8b5bfad-0d99-4004-991a-aaa4c5c82bc8",
  "name": "Sarah Mueller",
  "email": "sarah@0711.expert",
  "mcps": ["CTAX", "FPA", "LEGAL"],
  "dashboard_url": "/expert/dashboard"
}
```

---

## 📊 What Happens After Login

Once logged in, the JWT token is stored in localStorage and you get access to:

### Expert Dashboard (`/expert/dashboard`)

**Views Available**:
1. **Mission Control** - Overview of clients, tasks, earnings
2. **Clients** - Manage your 7 active clients
3. **Task Queue** - AI-generated tasks needing review
4. **My MCPs** - CTAX, FPA, LEGAL performance
5. **Earnings** - €25,200/month, next payout Friday
6. **Messages** - Client communications

**Mock Data Included**:
- 7 active clients
- 23 tasks this month
- €25,200 monthly earnings
- 92% AI automation rate
- <2hr avg response time

---

## 🔧 API Endpoints Created

### Authentication
```
POST /api/expert-auth/login
  Request: { email, password }
  Response: { access_token, expert_id, name, mcps, dashboard_url }

POST /api/expert-auth/set-password
  Request: { email, password, token }
  Response: { success, message }

POST /api/expert-auth/forgot-password
  Request: { email }
  Response: { success, message }

GET /api/expert-auth/me?token=...
  Response: { expert_id, name, email, mcps, rating, clients }
```

---

## 🎨 Login Page Features

**Design**:
- Dark background with centered login card
- 0711 logo with orange accent
- Clean, minimal form
- Error message display
- "Forgot password" link
- "Apply to join" CTA for non-experts

**UX**:
- Email validation
- Password field (hidden characters)
- Loading state while authenticating
- Error messages for:
  - Invalid credentials
  - Account not approved yet
  - Account not verified
  - Connection errors

---

## ⚠️ Current Limitations

### What Works:
- ✅ Login page UI (fully functional)
- ✅ Login API endpoint (ready)
- ✅ Password hashing (bcrypt)
- ✅ JWT token generation
- ✅ Test expert account created

### What Needs Work:
- ⏳ Expert dashboard page (use existing component from original code)
- ⏳ Token refresh mechanism
- ⏳ Password reset email flow
- ⏳ Set password on first login (after approval)

---

## 🚀 Next Steps to Complete

### 1. Create Expert Dashboard Page

```typescript
// apps/website/app/expert/dashboard/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function ExpertDashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [expert, setExpert] = useState(null);

  useEffect(() => {
    // Check if logged in
    const token = localStorage.getItem('expert_token');

    if (!token) {
      router.push('/expert-login');
      return;
    }

    // Verify token and get expert data
    fetch(`http://localhost:4080/api/expert-auth/me?token=${token}`)
      .then(res => res.json())
      .then(data => {
        setExpert(data);
        setLoading(false);
      })
      .catch(() => {
        router.push('/expert-login');
      });
  }, []);

  if (loading) return <div>Loading...</div>;

  // Render the dashboard component from your original code
  return <ExpertDashboardApp />;
}
```

### 2. Update Approval Email

When admin approves expert, send email with:
```
Subject: 🎉 You're Approved! Set Your Password

Hi Sarah,

Welcome to the 0711 Expert Network! Click below to set your password:

[Set Password] → http://localhost:4000/expert/set-password?token=...

After setting your password, login at:
http://localhost:4000/expert-login

Email: sarah@0711.expert
```

---

## 💡 Quick Summary

**To login as an expert RIGHT NOW**:

1. **Visit**: http://localhost:4000/expert-login

2. **Credentials**:
   - Email: `sarah@0711.expert`
   - Password: `Expert123!`

3. **Click** "Sign In"

4. **Result**: Redirects to `/expert/dashboard` (needs to be created)

**Status**: Login flow 90% complete, just needs dashboard page integration!
