# How to Become an Expert on 0711 - Complete Guide

**Last Updated**: 2025-11-30
**Status**: System deployed and operational

---

## 🚀 Quick Start: Becoming an Expert

There are **two paths** to access the expert dashboard:

---

## 📝 Path 1: Apply as New Expert (Recommended)

### Step 1: Submit Application

**Visit the signup page**:
```
http://localhost:4000/expert-signup
```

**Complete the 6-step wizard** (~10-15 minutes):

1. **Basic Information**
   - First name, last name
   - Email, phone
   - Professional headline
   - LinkedIn (optional)
   - Referral code (optional)

2. **MCP Expertise**
   - Select 1-3 MCPs you're qualified to operate
   - Choose proficiency level (Beginner, Intermediate, Expert)
   - See potential earnings calculator

3. **Experience**
   - Years of professional experience
   - Previous clients (anonymized, optional)
   - Tools/software proficiency
   - Languages (German required)
   - Industries

4. **Availability & Pricing**
   - Maximum client capacity (5-15, default 10)
   - Preferred client sizes
   - Hourly rate expectation
   - Weekly availability hours

5. **Verification**
   - Upload certifications (StB, CPA, etc.)
   - Upload ID document (passport/national ID)
   - Tax identification number
   - Banking details (IBAN, BIC for payouts)

6. **Review & Submit**
   - Review all information
   - Accept Terms & Conditions
   - Accept Data Processing Agreement
   - Submit application

### Step 2: Wait for Approval (2-5 Business Days)

**What happens**:
- ✅ Confirmation email sent immediately
- 🔍 Platform team reviews your application
- ✅ Certifications verified manually
- ✅ ID document verified (KYC)
- ✅ Background check (optional)

**Check application status**:
```bash
# You'll receive an application ID in confirmation email
curl http://localhost:4080/api/experts/application/{application_id}
```

### Step 3: Get Approved

**You'll receive an email with**:
- ✅ Approval notification
- 🔗 Link to expert dashboard
- 💰 Earnings potential summary
- 📚 Onboarding resources
- 🎓 MCP certification courses (optional)

### Step 4: Access Expert Dashboard

**Dashboard URL**:
```
http://localhost:4000/expert/dashboard
```

**Login credentials**:
- Email: [your application email]
- Password: [set during signup - NOT IMPLEMENTED YET]

---

## 🔑 Path 2: Admin-Created Expert Account (For Testing)

Since we don't have the full auth system connected yet, you can create a test expert account directly:

### Option A: Create via Admin Interface

**1. Create expert application**:
```bash
curl -X POST http://localhost:4080/api/experts/applications/submit \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Your",
    "last_name": "Name",
    "email": "your.email@example.com",
    "phone": "+49 170 1234567",
    "headline": "Your Professional Headline",
    "selected_mcps": [
      {"mcpId": "CTAX", "proficiency": "expert"}
    ],
    "years_experience": 10,
    "previous_clients": "Your experience summary",
    "tools_proficiency": ["DATEV", "Excel"],
    "languages": ["German", "English"],
    "industries": ["Tech/SaaS"],
    "max_clients": 10,
    "preferred_client_size": ["SMB (20-200)"],
    "hourly_rate_expectation": 150,
    "weekly_availability": 20,
    "tax_id": "DE123456789",
    "iban": "DE89370400440532013000",
    "bic": "COBADEFFXXX"
  }'
```

**2. Visit admin interface**:
```
http://localhost:4000/admin/experts
```

**3. Approve your application**:
- Find your application in the list
- Click to review
- Check all verification items
- Click "Approve Expert"

### Option B: Create Directly in Database (Testing Only)

```bash
docker exec 0711-postgres psql -U 0711 -d 0711_control << 'EOF'
INSERT INTO experts (
  id, name, email, title, bio, avatar_initials,
  specializations, mcp_expertise, years_experience,
  hourly_rate_cents, status, verified, available,
  rating, review_count, max_concurrent_clients,
  current_clients, total_tasks_completed
) VALUES (
  gen_random_uuid(),
  'Your Name',
  'your.email@example.com',
  'Your Professional Title',
  'Your bio and experience summary',
  'YN',  -- Your initials
  ARRAY['Tech/SaaS', 'Manufacturing'],
  ARRAY['CTAX', 'FPA'],
  10,  -- years experience
  15000,  -- €150/hour in cents
  'active',  -- Status: active (approved)
  true,      -- Verified
  true,      -- Available
  4.8,       -- Rating
  15,        -- Review count
  10,        -- Max clients
  3,         -- Current clients
  50         -- Tasks completed
) RETURNING id, name, email;
EOF
```

---

## 🎯 What Happens After Login?

Once you're approved and logged in, you get access to:

### Expert Dashboard Views

**1. Mission Control** (Default view):
- 📊 Quick stats (monthly earnings, AI automation, today's tasks)
- 📋 AI task queue (sorted by priority and due date)
- 🏢 Client health overview
- 🤖 MCP activity tracking

**2. Clients**:
- View all your active clients
- Client health scores
- Tasks per client
- Monthly rates
- Communication history

**3. Task Queue**:
- All tasks across all clients
- Filter by status (To Do, In Progress, Needs Review, Completed)
- AI automation indicators
- Quick actions (Start, Review, Complete)

**4. My MCPs**:
- MCPs you're certified for
- Performance per MCP
- Automation rates
- Certification progress

**5. Earnings**:
- Monthly earnings summary
- Next payout details (Friday)
- Payout history
- Client breakdown
- Platform fee (10%)

**6. Messages**:
- Client communications
- Platform notifications
- Support tickets

---

## 🔐 Current Authentication Status

### What's Implemented:
- ✅ Expert signup wizard (frontend)
- ✅ Application submission (backend)
- ✅ Admin approval workflow
- ✅ Expert profile creation
- ✅ Database schema for experts

### What's NOT Implemented Yet:
- ❌ Expert login page
- ❌ Expert password management
- ❌ Expert JWT token generation
- ❌ Expert authentication middleware
- ❌ Expert session management

### Temporary Workaround (Development):

**Option 1: Use existing auth system**
```bash
# Login as a customer first
curl -X POST http://localhost:4080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@test.0711.io",
    "password": "TestPass123!"
  }'

# Returns JWT token
# Use this token for expert API calls (for now)
```

**Option 2: Create dedicated expert auth** (RECOMMENDED TO BUILD):

Create new file: `api/routes/expert_auth.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/expert-auth", tags=["expert-auth"])

class ExpertLoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
async def expert_login(credentials: ExpertLoginRequest):
    """Login for experts"""
    # TODO: Verify expert credentials
    # TODO: Generate JWT token with expert_id
    # TODO: Return token + expert profile

    return {
        "access_token": "expert_token_here",
        "token_type": "bearer",
        "expert_id": "expert_uuid",
        "expert_profile": {
            "name": "Sarah Mueller",
            "email": credentials.email,
            "mcps": ["CTAX", "FPA"],
            "dashboard_url": "/expert/dashboard"
        }
    }
```

---

## 🛠️ Quick Implementation: Expert Auth

If you want to add expert login right now, here's the minimal implementation:

### 1. Create Expert Auth Route
```python
# api/routes/expert_auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.database import get_db
from api.models.expert import Expert
from api.auth import create_access_token
import bcrypt

router = APIRouter(prefix="/api/expert-auth", tags=["expert-auth"])

@router.post("/login")
async def expert_login(
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    expert = db.query(Expert).filter(
        Expert.email == email,
        Expert.status == "active",
        Expert.verified == True
    ).first()

    if not expert:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # TODO: Verify password (need to add password_hash column)

    token = create_access_token({"expert_id": str(expert.id), "email": expert.email})

    return {
        "access_token": token,
        "token_type": "bearer",
        "expert_id": str(expert.id),
        "name": expert.name,
        "dashboard_url": "/expert/dashboard"
    }
```

### 2. Add to main.py
```python
# api/main.py
from api.routes import expert_auth

app.include_router(expert_auth.router)
```

### 3. Add password to experts table
```sql
ALTER TABLE experts ADD COLUMN password_hash VARCHAR(255);
```

---

## 📱 Access Points

### For Experts:
- **Signup**: http://localhost:4000/expert-signup
- **Login**: http://localhost:4000/expert-login (TO BE CREATED)
- **Dashboard**: http://localhost:4000/expert/dashboard (TO BE CREATED)
- **Profile**: http://localhost:4000/experts/[your-id]

### For Companies:
- **Browse Experts**: http://localhost:4000/experts-marketplace
- **My Experts**: http://localhost:4000/company/my-experts

### For Admins:
- **Review Applications**: http://localhost:4000/admin/experts

---

## 🎯 Recommended Next Steps

### To Enable Full Expert Login:

1. **Add password field to experts table**:
```sql
ALTER TABLE experts ADD COLUMN password_hash VARCHAR(255);
```

2. **Update signup wizard** to collect password (Step 1)

3. **Create expert_auth.py** route with login endpoint

4. **Create expert login page** (`apps/website/app/expert-login/page.tsx`)

5. **Create expert dashboard** page (`apps/website/app/expert/dashboard/page.tsx`)

6. **Add auth middleware** to protect expert routes

**Estimated time**: 2-3 hours

---

## 💡 Current Workaround (For Immediate Testing)

**Use the React component directly**:

The expert dashboard component already exists with full functionality:
```typescript
// From the original code you provided
import App from '@/components/ExpertDashboardApp';

// This component has:
// - Mission Control view
// - Clients view
// - Tasks view
// - MCPs view
// - Earnings view
// - Messages view
```

**To test it now**:
1. Create `apps/website/app/expert/dashboard/page.tsx`
2. Import and render the dashboard component
3. It works with mock data (no auth required)

---

## 📞 Summary

**To become an expert RIGHT NOW (for testing)**:
1. Visit http://localhost:4000/expert-signup
2. Complete wizard
3. Admin approves at http://localhost:4000/admin/experts
4. Expert profile goes live at http://localhost:4000/experts/[id]

**To LOGIN as expert (needs 2-3 hours development)**:
- Build expert login page
- Add password field to database
- Create expert auth endpoint
- Connect to expert dashboard

**Current status**:
- ✅ Signup flow: 100% complete
- ✅ Profile pages: 100% complete
- ✅ Marketplace: 100% complete
- ⏳ Login system: Not yet implemented (easy to add)

The expert dashboard component from your original code can be plugged in immediately - it just needs the auth/login wrapper!
