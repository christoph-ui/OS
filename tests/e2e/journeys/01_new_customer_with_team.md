# E2E Test Journey: New Customer Onboarding with Team Members

## Metadata

- **Journey ID**: `new_customer_with_team`
- **Priority**: P0 (Critical Path)
- **Estimated Time**: 15-20 minutes
- **Prerequisites**:
  - SSH tunnel active (ports 4000, 4010, 4020, 4080, 4099)
  - All backend services running
  - Test Feedback MCP server running (port 4099)
  - Clean test environment (no existing test users)

## Test Data

```json
{
  "company": {
    "name": "Test Manufacturing GmbH",
    "industry": "Manufacturing",
    "company_size": "50-200",
    "country": "Germany"
  },
  "primary_admin": {
    "email": "admin@testmfg.com",
    "password": "SecureTestPass123!",
    "name": "Admin User"
  },
  "team_member_1": {
    "email": "user1@testmfg.com",
    "name": "John Doe",
    "role": "customer_user"
  },
  "team_member_2": {
    "email": "admin2@testmfg.com",
    "name": "Jane Smith",
    "role": "customer_admin"
  },
  "selected_mcps": ["ctax", "law", "etim"],
  "test_files": [
    "sample_invoice.pdf",
    "sample_products.csv",
    "sample_contract.docx"
  ]
}
```

---

## Journey Steps

### Step 1: Navigate to Marketing Website

**Action**: Navigate to http://localhost:4000

**Screenshot**: `step_01_homepage.png`

**Verify**:
- [ ] Page title contains "0711"
- [ ] "Get Started" button is visible
- [ ] Navigation menu shows: Home, Pricing, Experts, Enterprise
- [ ] No JavaScript console errors
- [ ] Page loads in < 2 seconds

**On Failure**:
- Check if website service is running: `curl http://localhost:4000`
- Check console backend: `curl http://localhost:4010/health`

**Expected Result**: Marketing homepage loads with call-to-action visible

---

### Step 2: Click "Get Started" Button

**Action**: Click the "Get Started" button

**Screenshot**: `step_02_signup_form.png`

**Verify**:
- [ ] Redirects to `/signup` page
- [ ] Signup form is visible with fields:
  - Company Name
  - Contact Email
  - Contact Name
  - Password
  - Confirm Password
- [ ] Password strength indicator visible
- [ ] Terms & Conditions checkbox visible

**On Failure**: Check router configuration in website/app/page.tsx

**Expected Result**: Signup form displayed correctly

---

### Step 3: Fill Signup Form

**Action**: Fill the signup form with test data

**Form Data**:
```
Company Name: Test Manufacturing GmbH
Contact Email: admin@testmfg.com
Contact Name: Admin User
Password: SecureTestPass123!
Confirm Password: SecureTestPass123!
[✓] Accept Terms & Conditions
```

**Screenshot**: `step_03_signup_filled.png`

**Verify**:
- [ ] All fields accept input
- [ ] Password strength shows "Strong"
- [ ] Email format is validated
- [ ] Submit button becomes enabled

**On Failure**: Check form validation in signup component

**Expected Result**: Form filled, ready to submit

---

### Step 4: Submit Signup

**Action**: Click "Create Account" button

**Screenshot**: `step_04_signup_success.png`

**Verify**:
- [ ] Form submits successfully (HTTP 201)
- [ ] Success message displayed
- [ ] Redirects to verification page OR auto-verifies (test mode)
- [ ] Network request shows POST `/api/auth/signup` → 201

**Console Errors**: Check for any API errors

**Network Failures**:
```javascript
// Check for failed requests
{
  "url": "http://localhost:4080/api/auth/signup",
  "method": "POST",
  "status": 400/500,
  "error_message": "..."
}
```

**On Failure**:
- Check PostgreSQL is running
- Check if email already exists in database
- Verify password meets requirements

**Expected Result**: Customer account created, verification email sent (test mode: auto-verified)

---

### Step 5: Navigate to Onboarding Wizard

**Action**: Navigate to http://localhost:4000/onboarding (or auto-redirect after signup)

**Screenshot**: `step_05_onboarding_start.png`

**Verify**:
- [ ] Onboarding wizard loads
- [ ] Progress indicator shows Step 1/4
- [ ] Company info form pre-filled from signup
- [ ] "Continue" button visible

**On Failure**: Check auth token was set in localStorage

**Expected Result**: Onboarding wizard ready to start

---

### Step 6: Complete Company Information

**Action**: Fill/verify company information

**Form Data**:
```
Industry: Manufacturing
Company Size: 50-200 employees
Country: Germany
Goals:
  [✓] Tax automation
  [✓] Contract analysis
  [✓] Product data management
```

**Screenshot**: `step_06_company_info.png`

**Verify**:
- [ ] All fields visible
- [ ] Dropdowns work correctly
- [ ] Multiple goals can be selected
- [ ] Progress indicator updates to 1/4

**On Failure**: Check onboarding component state management

**Expected Result**: Company info saved, wizard advances

---

### Step 7: Upload Test Files

**Action**: Upload 3 test files

**Files to Upload**:
1. `sample_invoice.pdf` (Mock PDF with invoice data)
2. `sample_products.csv` (Product catalog with columns: id, name, category, price)
3. `sample_contract.docx` (Mock contract document)

**Screenshot**: `step_07_file_upload.png`

**Verify**:
- [ ] File upload area visible
- [ ] Drag & drop works OR file picker works
- [ ] Upload progress shows for each file
- [ ] All 3 files show "Uploaded" status
- [ ] Total file count: 3
- [ ] Network shows POST `/api/upload/files` → 200

**Console Errors**: Check for upload failures

**Network Failures**: Monitor `/api/upload/files` endpoint

**On Failure**:
- Check MinIO is running: `curl http://localhost:4050/minio/health/live`
- Check bucket permissions
- Verify file size limits

**Expected Result**: 3 files uploaded to MinIO successfully

---

### Step 8: Select MCPs

**Action**: Select MCPs from marketplace

**MCPs to Select**:
- [✓] **CTAX** - German Tax Engine (€3,000/month)
- [✓] **LAW** - Contract Analysis (€3,000/month)
- [✓] **ETIM** - Product Classification (€2,500/month)

**Screenshot**: `step_08_mcp_selection.png`

**Verify**:
- [ ] MCP marketplace shows available MCPs
- [ ] Each MCP shows: Name, Description, Price, Features
- [ ] Selection checkboxes work
- [ ] Price calculation updates dynamically
- [ ] Total monthly cost = Base (€8,000) + MCPs (€8,500) = €16,500

**On Failure**: Check MCP service API is accessible

**Expected Result**: 3 MCPs selected, pricing calculated correctly

---

### Step 9: Review & Deploy

**Action**: Review selections and trigger deployment

**Screenshot**: `step_09_review.png`

**Verify**:
- [ ] Summary shows:
  - Company: Test Manufacturing GmbH
  - Files: 3 uploaded
  - MCPs: CTAX, LAW, ETIM
  - Total: €16,500/month
- [ ] "Start Deployment" button visible
- [ ] Terms accepted

**On Failure**: Check all previous steps completed

**Expected Result**: Ready to deploy

---

### Step 10: Trigger Deployment

**Action**: Click "Start Deployment" button

**Screenshot**: `step_10_deployment_start.png`

**Verify**:
- [ ] Deployment starts (HTTP 200/202)
- [ ] Progress screen shows deployment status
- [ ] Deployment ID received
- [ ] Network shows POST `/api/onboarding/deploy` → 200

**On Failure**: Check deployment orchestrator service

**Expected Result**: Deployment initiated, deployment_id returned

---

### Step 11: Monitor Deployment Progress

**Action**: Wait for deployment to complete (poll every 5 seconds)

**Screenshot**: `step_11_deployment_progress.png`

**Verify**:
- [ ] Progress bar animates
- [ ] Status updates:
  - Creating infrastructure...
  - Deploying AI models...
  - Starting services...
  - Ingesting data...
  - Finalizing setup...
- [ ] Progress reaches 100%
- [ ] Status changes to "Complete"
- [ ] Estimated time: 2-5 minutes

**Network Monitoring**:
```javascript
// Poll: GET /api/onboarding/status/{deployment_id}
{
  "status": "processing" → "complete",
  "progress": 0.0 → 1.0,
  "message": "..."
}
```

**On Failure**:
- Check Docker containers starting
- Check vLLM model loading
- Check lakehouse initialization
- If timeout (>10 min): Report failure with last status

**Expected Result**: Deployment completes successfully

---

### Step 12: Verify Deployment

**Action**: Check deployment verification endpoint

**Request**: `GET /api/onboarding/verify/{customer_id}`

**Screenshot**: `step_12_deployment_complete.png`

**Verify**:
- [ ] Verification endpoint returns success
- [ ] Services running:
  - vLLM server
  - Embeddings service
  - Lakehouse HTTP API
- [ ] Files ingested: 3
- [ ] MCPs enabled: 3 (CTAX, LAW, ETIM)
- [ ] Console URL provided

**On Failure**: Check Docker containers with `docker ps`

**Expected Result**: All services healthy, data ingested

---

### Step 13: First Login to Console

**Action**: Navigate to Console at http://localhost:4020 and login

**Login Credentials**:
```
Email: admin@testmfg.com
Password: SecureTestPass123!
```

**Screenshot**: `step_13_console_login.png`

**Verify**:
- [ ] Login form visible
- [ ] Credentials accepted
- [ ] JWT token stored in localStorage
- [ ] Redirects to dashboard/chat page

**Network Failures**: Monitor POST `/api/auth/login`

**On Failure**:
- Verify user was created in database
- Check password hash is correct
- Verify JWT secret is configured

**Expected Result**: Successfully logged into console

---

### Step 14: Verify Console Dashboard

**Action**: View console dashboard

**Screenshot**: `step_14_console_dashboard.png`

**Verify**:
- [ ] Sidebar shows navigation:
  - Chat
  - Products
  - Data
  - Syndicate
  - MCPs
  - Ingest
- [ ] Active MCPs indicator shows: CTAX, LAW, ETIM
- [ ] File count badge shows: 3 files
- [ ] vLLM + Mixtral 8x7B shown as active model
- [ ] No console errors

**On Failure**: Check console backend API health

**Expected Result**: Dashboard loads with all components

---

### Step 15: Navigate to User Management

**Action**: Click "Settings" → "Team Members" (or direct URL: /settings/users)

**Screenshot**: `step_15_user_management.png`

**Verify**:
- [ ] User management page loads
- [ ] Current user list shows:
  - Admin User (admin@testmfg.com) - customer_admin
- [ ] "Invite User" button visible
- [ ] User count: 1

**On Failure**: Check user management API endpoint

**Expected Result**: User management interface visible

---

### Step 16: Invite Team Member #1

**Action**: Click "Invite User" and fill invitation form

**Form Data**:
```
Email: user1@testmfg.com
Name: John Doe
Role: Customer User
Permissions: (Default for customer_user)
```

**Screenshot**: `step_16_invite_user1.png`

**Verify**:
- [ ] Invitation form opens
- [ ] Role dropdown shows: Customer User, Customer Admin
- [ ] Email validates format
- [ ] Submit button enabled

**On Failure**: Check permission configuration

**Expected Result**: Invitation form ready

---

### Step 17: Send Invitation #1

**Action**: Click "Send Invitation"

**Screenshot**: `step_17_invitation_sent.png`

**Verify**:
- [ ] Success message shown
- [ ] Network shows POST `/api/users/invite` → 200
- [ ] Invitation token generated
- [ ] Email sent (test mode: check logs)
- [ ] User status: "pending"

**Network Monitoring**:
```javascript
POST /api/users/invite
{
  "email": "user1@testmfg.com",
  "name": "John Doe",
  "role": "customer_user"
}
→ 200 OK
{
  "invitation_token": "...",
  "invitation_url": "..."
}
```

**On Failure**:
- Check email service configuration
- Verify Redis is running (stores invitation tokens)

**Expected Result**: Invitation sent to user1@testmfg.com

---

### Step 18: Invite Team Member #2

**Action**: Repeat invitation flow for second user

**Form Data**:
```
Email: admin2@testmfg.com
Name: Jane Smith
Role: Customer Admin
```

**Screenshot**: `step_18_invite_user2.png`

**Verify**:
- [ ] Second invitation sent successfully
- [ ] User list now shows 3 users:
  - Admin User (active)
  - John Doe (pending)
  - Jane Smith (pending)

**Expected Result**: Second invitation sent

---

### Step 19: Accept Invitation (Team Member #1)

**Action**: Navigate to invitation URL as Team Member #1

**URL**: `http://localhost:4000/accept-invitation?token={invitation_token_1}`

**Screenshot**: `step_19_accept_invitation_user1.png`

**Verify**:
- [ ] Invitation page loads
- [ ] Shows: "You've been invited to join Test Manufacturing GmbH"
- [ ] Password setup form visible
- [ ] Name pre-filled: John Doe
- [ ] Email pre-filled: user1@testmfg.com

**On Failure**: Check invitation token in Redis

**Expected Result**: Invitation page ready

---

### Step 20: Set Password (Team Member #1)

**Action**: Set password for Team Member #1

**Form Data**:
```
Password: UserTestPass123!
Confirm Password: UserTestPass123!
```

**Screenshot**: `step_20_set_password_user1.png`

**Verify**:
- [ ] Password strength validates
- [ ] Passwords match
- [ ] Submit button enabled

**Expected Result**: Password form filled

---

### Step 21: Complete Signup (Team Member #1)

**Action**: Click "Accept Invitation"

**Screenshot**: `step_21_user1_accepted.png`

**Verify**:
- [ ] Network shows POST `/api/users/accept-invitation` → 200
- [ ] User status changes: pending → active
- [ ] JWT token returned
- [ ] Redirects to console

**On Failure**: Check user activation logic in API

**Expected Result**: Team Member #1 activated and logged in

---

### Step 22: Verify User #1 Permissions

**Action**: As Team Member #1, try to access restricted features

**Screenshot**: `step_22_user1_permissions.png`

**Verify**:
- [ ] Can access: Chat, Data Browser, Products
- [ ] **Cannot** access: User Management (should show 403)
- [ ] **Cannot** access: Billing Settings
- [ ] **Cannot** invite other users
- [ ] Sidebar shows limited navigation

**On Failure**: Check RBAC middleware in API

**Expected Result**: customer_user role has limited permissions

---

### Step 23: Accept Invitation (Team Member #2)

**Action**: Repeat acceptance flow for Team Member #2 (admin role)

**URL**: `http://localhost:4000/accept-invitation?token={invitation_token_2}`

**Credentials**:
```
Password: AdminTestPass123!
Confirm Password: AdminTestPass123!
```

**Screenshot**: `step_23_user2_accepted.png`

**Verify**:
- [ ] Invitation accepted successfully
- [ ] User status: pending → active
- [ ] Redirects to console

**Expected Result**: Team Member #2 activated

---

### Step 24: Verify User #2 Permissions (Admin)

**Action**: As Team Member #2, access admin features

**Screenshot**: `step_24_user2_admin_permissions.png`

**Verify**:
- [ ] **Can** access: User Management
- [ ] **Can** invite other users
- [ ] **Can** access: Billing Settings
- [ ] **Can** view all team members
- [ ] Sidebar shows full navigation

**On Failure**: Check role assignment in database

**Expected Result**: customer_admin role has full permissions

---

### Step 25: View Team Members List (as Admin)

**Action**: As primary admin, navigate to Team Members page

**Screenshot**: `step_25_team_list.png`

**Verify**:
- [ ] User list shows 3 users:
  - Admin User (admin@testmfg.com) - customer_admin - ACTIVE
  - John Doe (user1@testmfg.com) - customer_user - ACTIVE
  - Jane Smith (admin2@testmfg.com) - customer_admin - ACTIVE
- [ ] All users show "Active" status
- [ ] Last login timestamps visible
- [ ] Role badges displayed correctly

**Expected Result**: Complete team roster visible

---

### Step 26: Test Team Collaboration (Chat)

**Action**: As Team Member #1, send a chat message

**Chat Message**: "Show me our product catalog"

**Screenshot**: `step_26_user1_chat.png`

**Verify**:
- [ ] Chat interface loads
- [ ] Message sends successfully
- [ ] MCP routing works (should route to ETIM for products)
- [ ] Response received with:
  - Product information from uploaded CSV
  - Sources cited
  - Correct MCP indicator (ETIM)
- [ ] WebSocket connection stable

**Network Monitoring**: Check WebSocket `/api/ws/chat` connection

**On Failure**:
- Check lakehouse has ingested product data
- Verify ETIM MCP is accessible
- Check vLLM inference service

**Expected Result**: AI chat working, retrieves product data

---

### Step 27: Test Admin Can Invite (Team Member #2)

**Action**: As Team Member #2 (admin), attempt to invite another user

**Screenshot**: `step_27_admin2_can_invite.png`

**Verify**:
- [ ] "Invite User" button visible and enabled
- [ ] Can access invitation form
- [ ] RBAC allows customer_admin to invite

**Expected Result**: Admin user can access invitation feature

---

### Step 28: Test User Cannot Invite (Team Member #1)

**Action**: As Team Member #1 (user), attempt to access user management

**Screenshot**: `step_28_user1_cannot_invite.png`

**Verify**:
- [ ] User Management link hidden OR shows 403 error
- [ ] Direct navigation to `/settings/users` → 403 Forbidden
- [ ] Error message: "Only administrators can manage team members"

**Expected Result**: Non-admin user blocked from user management

---

### Step 29: Verify Data Isolation

**Action**: Check that all team members see same customer data

**Screenshot**: `step_29_data_isolation.png`

**Verify**:
- [ ] All users (Admin, User1, User2) see:
  - Same 3 uploaded files
  - Same product data
  - Same MCP access (CTAX, LAW, ETIM)
  - Same lakehouse data

**Expected Result**: Data is shared across team, isolated from other customers

---

### Step 30: Final Summary

**Action**: Review complete journey

**Screenshot**: `step_30_journey_complete.png`

**Final Checks**:
- [ ] Customer created: "Test Manufacturing GmbH"
- [ ] Total users: 3 (1 primary admin, 1 customer_admin, 1 customer_user)
- [ ] Files uploaded: 3
- [ ] Files ingested to lakehouse: 3
- [ ] MCPs active: 3 (CTAX, LAW, ETIM)
- [ ] Deployment status: Complete
- [ ] All Docker containers running
- [ ] AI chat working for all users
- [ ] RBAC working correctly (admin vs user permissions)
- [ ] Team collaboration enabled

**Performance Metrics**:
- Total journey time: ________ minutes
- Deployment time: ________ minutes
- File ingestion time: ________ minutes
- Any failures: Y/N
- Retry count: ________

---

## Success Criteria

### Must Pass
- ✅ Customer signup completes successfully
- ✅ 3 files uploaded and ingested
- ✅ Deployment completes in < 10 minutes
- ✅ All 3 users can login
- ✅ RBAC permissions work correctly
- ✅ AI chat retrieves data from lakehouse
- ✅ No critical console errors

### Should Pass
- ✅ Journey completes in < 20 minutes total
- ✅ All UI elements load without visual glitches
- ✅ WebSocket connections stable
- ✅ MCP routing works correctly

### Nice to Have
- ✅ Smooth animations and transitions
- ✅ Helpful error messages
- ✅ Progress indicators accurate
- ✅ Mobile responsive (if testing on mobile)

---

## Known Issues

1. **vLLM startup can be slow** - First deployment may take 5-10 minutes if model needs to download
2. **Email in test mode** - Emails not actually sent, invitation URLs generated in API response
3. **MinIO bucket creation** - Sometimes requires manual bucket creation on first run

---

## Cleanup (After Test)

```bash
# Remove test customer from database
psql -h localhost -p 4005 -U 0711 -d 0711_control \
  -c "DELETE FROM users WHERE email LIKE '%@testmfg.com';"

# Remove MinIO bucket
docker exec 0711-minio mc rb --force /data/customer-testmfg

# Remove lakehouse data
rm -rf /tmp/lakehouse/testmfg

# Remove Docker containers (if per-customer deployment)
cd /home/christoph.bertsch/0711/deployments/testmfg
docker compose down -v
```

---

## Report Template

```json
{
  "journey_id": "new_customer_with_team",
  "timestamp": "2026-01-20T10:00:00Z",
  "status": "pass" | "fail",
  "duration_minutes": 18,
  "steps_completed": 30,
  "steps_failed": 0,
  "screenshots": ["step_01_homepage.png", "..."],
  "errors": [],
  "suggestions": [
    "Loading state for file upload could be improved",
    "Add skeleton loaders to user list"
  ],
  "performance": {
    "deployment_time_minutes": 3.5,
    "total_journey_time_minutes": 18,
    "page_load_avg_ms": 1200
  }
}
```

---

**Journey Created**: 2026-01-20
**Last Updated**: 2026-01-20
**Test Feedback Server**: http://localhost:4099
