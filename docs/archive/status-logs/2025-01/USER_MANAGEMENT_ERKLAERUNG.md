# 0711 User Management - Komplette Erklärung

**Datum**: 2026-01-28
**Status**: ✅ **Produktiv im Einsatz**

---

## 🎯 Überblick

Das 0711 User Management ist ein **Multi-Tenant RBAC-System** mit 4 Rollen und granularen Permissions.

**Kern-Features**:
- 4 User-Rollen (Platform, Partner, Customer Admin/User)
- Multi-Tenant Isolation (jeder Customer sieht nur seine User)
- Granulare Permissions (JSONB: `{"billing.view": true, "users.invite": true}`)
- Invitation Workflow (Email → Token → Passwort setzen)
- Passwort-Reset Flow (Forgot → Reset)
- Security Features (Login-Tracking, Account-Lockout, Soft Delete)

---

## 👥 Die 4 User-Rollen

### 1. **Platform Admin** (`platform_admin`)

**Wer**: 0711 Mitarbeiter (interne Admins)

**Zugriff**:
- ✅ **Alle Kunden** verwalten
- ✅ **Alle MCPs** genehmigen/ablehnen
- ✅ **Alle Developer** verifizieren
- ✅ **System Health** überwachen
- ✅ **Cradle Deployments** erstellen
- ✅ **Wildcard Permission**: `{"*": true}` (alles erlaubt)

**Foreign Keys**:
- `customer_id`: **NULL** (gehört keinem Kunden)
- `partner_id`: **NULL** (ist kein Partner)

**UI-Zugang**:
- Login: http://localhost:4020/admin/login
- Portal: http://localhost:4020/admin/*

**Beispiel**:
```sql
INSERT INTO users (
  email, password_hash, first_name, last_name,
  role, customer_id, partner_id, permissions, status
) VALUES (
  'admin@0711.io', '$2b$12$...', 'Max', 'Müller',
  'platform_admin', NULL, NULL, '{"*": true}', 'active'
);
```

---

### 2. **Partner Admin** (`partner_admin`)

**Wer**: Agenturen/Reseller (verwalten mehrere Kunden)

**Zugriff**:
- ✅ **Eigene Kunden** onboarden
- ✅ **Eigene Kunden** verwalten
- ✅ Dateien für Kunden hochladen
- ✅ Deployments für Kunden triggern
- ❌ **NICHT**: Andere Partner-Kunden sehen
- ❌ **NICHT**: Platform-Admin-Funktionen

**Foreign Keys**:
- `customer_id`: **NULL** (gehört keinem spezifischen Kunden)
- `partner_id`: **SET** (gehört zu Partner XY)

**UI-Zugang**:
- Login: http://localhost:4020/partner-login
- Portal: http://localhost:4020/partner/*

**Beispiel**:
```sql
-- Erst Partner erstellen
INSERT INTO partners (id, company_name, contact_email)
VALUES ('a1b2c3...', 'TechConsult GmbH', 'info@techconsult.de');

-- Dann Partner Admin User
INSERT INTO users (
  email, password_hash, first_name, last_name,
  role, customer_id, partner_id, status
) VALUES (
  'max@techconsult.de', '$2b$12$...', 'Max', 'Schmidt',
  'partner_admin', NULL, 'a1b2c3...', 'active'
);
```

**Kunden-Beziehung**:
```sql
-- Partner-Kunde wird erstellt mit partner_id
INSERT INTO customers (partner_id, company_name, ...)
VALUES ('a1b2c3...', 'Kunde A GmbH', ...);

-- Partner Admin kann Kunde A deployen
-- Aber NICHT Kunden von anderem Partner
```

---

### 3. **Customer Admin** (`customer_admin`)

**Wer**: Primärer Administrator eines Kunden (erster User beim Signup)

**Zugriff**:
- ✅ **Team Members** einladen
- ✅ **Team Members** verwalten (Rollen, Permissions)
- ✅ **Company Settings** bearbeiten
- ✅ **Billing** verwalten
- ✅ **MCPs** installieren
- ✅ **Daten** uploaden
- ❌ **NICHT**: Andere Kunden sehen
- ❌ **NICHT**: Platform/Partner-Funktionen

**Foreign Keys**:
- `customer_id`: **SET** (gehört zu Customer XY)
- `partner_id`: **NULL** (außer wenn Partner-managed)

**UI-Zugang**:
- Login: http://localhost:4020/login
- Portal: http://localhost:4020/* (hauptsächlich)
- Settings: http://localhost:4020/settings/*

**Beispiel**:
```sql
-- Erstellt beim Signup (POST /api/auth/signup)
INSERT INTO users (
  email, password_hash, first_name, last_name,
  role, customer_id, status, permissions
) VALUES (
  'admin@kunde.de', '$2b$12$...', 'Anna', 'Müller',
  'customer_admin', 'x1y2z3...', 'active',
  '{"billing.view": true, "billing.edit": true, "users.invite": true, "mcps.install": true}'
);
```

**Permissions (typisch für Customer Admin)**:
```json
{
  "billing.view": true,
  "billing.edit": true,
  "users.invite": true,
  "users.edit": true,
  "users.delete": true,
  "mcps.install": true,
  "mcps.uninstall": true,
  "data.upload": true,
  "data.delete": true,
  "company.edit": true
}
```

---

### 4. **Customer User** (`customer_user`)

**Wer**: Normale Mitarbeiter eines Kunden (vom Admin eingeladen)

**Zugriff**:
- ✅ **Chat** mit AI nutzen
- ✅ **Daten** durchsuchen
- ✅ **MCPs** verwenden (wenn erlaubt)
- ✅ **Eigenes Profil** bearbeiten
- ❌ **NICHT**: Team verwalten
- ❌ **NICHT**: Billing sehen
- ❌ **NICHT**: Company Settings ändern

**Foreign Keys**:
- `customer_id`: **SET** (gehört zu Customer XY)
- `partner_id`: **NULL**

**UI-Zugang**:
- Login: http://localhost:4020/login (same as admin)
- Portal: http://localhost:4020/* (eingeschränkt)

**Beispiel**:
```sql
-- Eingeladen vom Customer Admin
INSERT INTO users (
  email, first_name, last_name,
  role, customer_id, status, permissions,
  invited_by_id, invited_at
) VALUES (
  'user@kunde.de', 'Tom', 'Schmidt',
  'customer_user', 'x1y2z3...', 'invited',
  '{"billing.view": false, "data.upload": true}',
  'admin_user_id', NOW()
);
```

**Permissions (typisch für Customer User)**:
```json
{
  "chat.use": true,
  "data.view": true,
  "data.upload": true,
  "mcps.use": true,
  "profile.edit": true
}
```

---

## 🔑 Permission System (Granular RBAC)

### Permission Format

Permissions sind JSONB mit **Punkt-Notation**:

```json
{
  "billing.view": true,       // Kann Rechnungen sehen
  "billing.edit": false,      // Kann Billing NICHT ändern
  "users.invite": true,       // Kann User einladen
  "users.edit": true,         // Kann User bearbeiten
  "users.delete": false,      // Kann User NICHT löschen
  "mcps.install": true,       // Kann MCPs installieren
  "data.upload": true,        // Kann Daten hochladen
  "data.delete": false,       // Kann Daten NICHT löschen
  "company.edit": true        // Kann Company Settings ändern
}
```

### Standard Permissions nach Rolle

**Platform Admin**:
```json
{"*": true}  // Wildcard - alles erlaubt
```

**Partner Admin**:
```json
{
  "customers.view": true,
  "customers.create": true,
  "customers.onboard": true,
  "deployments.view": true
}
```

**Customer Admin**:
```json
{
  "billing.view": true,
  "billing.edit": true,
  "users.invite": true,
  "users.edit": true,
  "users.delete": true,
  "mcps.install": true,
  "mcps.uninstall": true,
  "data.upload": true,
  "data.delete": true,
  "company.edit": true
}
```

**Customer User**:
```json
{
  "chat.use": true,
  "data.view": true,
  "data.upload": true,
  "profile.edit": true
}
```

### Permission Check (Code)

```python
# Im User-Model (api/models/user.py:144)
def has_permission(self, permission: str) -> bool:
    if not self.permissions:
        return False

    # Wildcard für Platform Admins
    if self.permissions.get("*") is True:
        return True

    # Spezifische Permission prüfen
    return self.permissions.get(permission, False) is True

# Verwendung
if user.has_permission("billing.edit"):
    # Erlaubt
else:
    raise HTTPException(403, "No permission")
```

---

## 🔄 Workflows

### Workflow 1: Customer Signup (Neuer Kunde)

```
1. USER AKTION
   User öffnet: https://0711.cloud/onboarding
   Füllt Formular aus:
     - Company Name: "ACME GmbH"
     - Email: "admin@acme.de"
     - Password: "SecurePass123"

2. API CALL
   POST /api/auth/signup
   {
     "company_name": "ACME GmbH",
     "contact_email": "admin@acme.de",
     "password": "SecurePass123"
   }

3. BACKEND ERSTELLT
   ├─ Customer-Record (customers table)
   │   company_name: "ACME GmbH"
   │   id: UUID (generated)
   │
   └─ Primary Admin User (users table)
       email: "admin@acme.de"
       role: "customer_admin"
       customer_id: UUID (von Customer)
       status: "active"
       permissions: {alle customer_admin permissions}

4. RESPONSE
   {
     "access_token": "eyJhbGc...",
     "user": {...},
     "customer": {...}
   }

5. USER REDIRECTED
   → http://localhost:4020/ (Console)
   Jetzt eingeloggt als Customer Admin
```

**Code**: `api/routes/auth.py` → `signup()` Endpoint

---

### Workflow 2: Team Member Invitation (Vom Customer Admin)

```
1. CUSTOMER ADMIN AKTION
   Eingeloggt im Console (4020)
   Navigate: /settings/team
   Klicke: "Invite Member"
   Füllt Form:
     - Email: "user@acme.de"
     - Name: "Tom Schmidt"
     - Role: "customer_user"
     - Permissions: [x] data.upload [ ] billing.view

2. API CALL
   POST /api/users/invite
   {
     "email": "user@acme.de",
     "first_name": "Tom",
     "last_name": "Schmidt",
     "role": "customer_user",
     "permissions": {"data.upload": true, "billing.view": false}
   }

3. BACKEND ERSTELLT
   ├─ User-Record (users table)
   │   email: "user@acme.de"
   │   role: "customer_user"
   │   customer_id: UUID (same as admin)
   │   status: "invited"  ← WICHTIG!
   │   password_hash: NULL  ← Noch kein Passwort!
   │   invited_by_id: UUID (admin's id)
   │
   └─ Invitation Token (Redis)
       Key: "invite:abc123xyz..."
       Value: user_id (UUID)
       Expiry: 7 Tage

4. EMAIL SENT
   An: user@acme.de
   Subject: "Einladung zu ACME GmbH bei 0711"
   Link: https://0711.cloud/accept-invitation?token=abc123xyz...

5. USER KLICKT LINK
   → /accept-invitation?token=abc123xyz...
   Seite lädt
   Form: "Passwort setzen"

6. USER SETZT PASSWORT
   Gibt ein: "MyPassword123"

   POST /api/users/accept-invitation
   {
     "token": "abc123xyz...",
     "password": "MyPassword123"
   }

7. BACKEND UPDATED
   User-Record:
     status: "invited" → "active"
     password_hash: NULL → "$2b$12$..." (bcrypt)
     invitation_accepted_at: NOW()

   Redis Token gelöscht

8. USER REDIRECTED
   → /login
   "Passwort gesetzt! Jetzt einloggen."

   User logged sich ein
   → Console (eingeschränkte Rechte)
```

**Code**:
- Invite: `api/routes/users.py:90` → `invite_team_member()`
- Accept: `api/routes/users.py:179` → `accept_invitation()`
- Frontend: `console/frontend/src/app/settings/team/page.tsx`

---

### Workflow 3: Partner Onboards Customer

```
1. PARTNER ADMIN AKTION
   Login: http://localhost:4020/partner-login
   Navigate: /partner/customers
   Klicke: "New Customer"
   Form:
     - Company: "Neuer Kunde GmbH"
     - Email: "admin@neuerkunde.de"

2. CUSTOMER ERSTELLT
   POST /api/partners/customers

   Creates:
     - Customer-Record (mit partner_id!)
     - Customer Admin User (für Neuer Kunde)
     - Deployment-Record

3. PARTNER LÄDT DATEN HOCH
   Navigate: /partner/customers/{id}/onboarding
   Upload: Dateien (CSV, PDF, etc.)
   Select: MCPs (CTAX, LAW, ETIM)
   Klicke: "Start Onboarding"

4. UPLOAD & DEPLOYMENT
   POST /api/upload/files?customer_id={id}&selected_mcps=ctax,law,etim

   Triggers:
     - MinIO Upload
     - Cradle Processing (via Orchestrator)
     - Docker Image Build
     - Deployment

   Partner sieht: WebSocket Progress (Upload → Ingestion → Deployment)

5. KUNDE ERHÄLT
   - Docker Image: neuerkunde-v1.0.tar.gz
   - Deployment Files
   - Login Credentials (Email)

6. KUNDE DEPLOYED
   docker load < neuerkunde-v1.0.tar.gz
   docker compose up -d

   → Eigene Console läuft!
```

**Code**:
- Frontend: `console/frontend/src/app/partner/customers/[id]/onboarding/page.tsx`
- Backend: `api/routes/upload.py` → `upload_files()` → triggers Orchestrator

---

## 🗄️ Datenbank-Schema

### Users Table

```sql
CREATE TABLE users (
    -- Identität
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),  -- NULL für invited users

    -- Personal
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,

    -- Zuordnung (Multi-Tenant)
    customer_id UUID REFERENCES customers(id),  -- NULL für Platform/Partner Admins
    partner_id UUID REFERENCES partners(id),    -- Nur für Partner Admins

    -- Rolle & Permissions
    role VARCHAR(50) NOT NULL,  -- platform_admin, partner_admin, customer_admin, customer_user
    permissions JSONB DEFAULT '{}',  -- {"billing.view": true, ...}
    status VARCHAR(50) DEFAULT 'active',  -- active, invited, suspended, inactive

    -- Email-Verifizierung
    email_verified BOOLEAN DEFAULT false,
    email_verified_at TIMESTAMP,

    -- Security
    last_login_at TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,  -- Account-Lockout nach 5 falschen Logins

    -- Invitation Tracking
    invited_by_id UUID REFERENCES users(id),
    invited_at TIMESTAMP,
    invitation_accepted_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP  -- Soft Delete
);

-- Indexes
CREATE INDEX idx_users_customer_id ON users(customer_id);
CREATE INDEX idx_users_partner_id ON users(partner_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

### Invitation Tokens (Redis)

```
Key: "invite:{token}"
Value: "{user_id}"
TTL: 7 days (604800 seconds)

Beispiel:
  Key: "invite:xY7Kp2Mn..."
  Value: "550e8400-e29b-41d4-a716-446655440000"
  Expires: 2026-02-04
```

### Password Reset Tokens (Redis)

```
Key: "reset:{token}"
Value: "{user_id}"
TTL: 1 hour (3600 seconds)

Beispiel:
  Key: "reset:aB3Cd9Ef..."
  Value: "550e8400-e29b-41d4-a716-446655440000"
  Expires: 2026-01-28 15:30
```

---

## 🔐 Authentication & Security

### JWT Token Structure

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",  // user_id
  "user_id": "550e8400-...",
  "email": "admin@kunde.de",
  "customer_id": "x1y2z3...",                    // NULL für Platform/Partner Admins
  "partner_id": null,                             // SET für Partner Admins
  "role": "customer_admin",
  "permissions": {"billing.view": true, ...},
  "exp": 1738161234,                              // Expiration (7 Tage)
  "iat": 1737556434                               // Issued At
}
```

**Generierung**: `api/utils/security.py` → `create_access_token()`

**Validierung**: `api/utils/security.py` → `get_current_user()`

### Passwort-Hashing

```python
import bcrypt

# Hash erstellen
password = "MyPassword123"
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
# Result: "$2b$12$N9qo8uLOickgx2Z..." (60 chars)

# Verifizieren
is_valid = bcrypt.checkpw(password.encode(), hashed)
# Result: True/False
```

**Code**: `api/utils/security.py` → `hash_password()`, `verify_password()`

### Account Lockout (Brute Force Protection)

```python
# Nach Login-Fehlschlag
user.failed_login_attempts += 1

if user.failed_login_attempts >= 5:
    user.locked_until = datetime.utcnow() + timedelta(hours=1)
    user.status = UserStatus.SUSPENDED
    # User ist für 1 Stunde gesperrt

# Bei erfolgreichem Login
user.failed_login_attempts = 0
user.locked_until = None
```

**Code**: `api/routes/auth.py` → `login()` Endpoint

---

## 📡 API Endpoints

### Authentication

```bash
# Signup (erstellt Customer + Admin User)
POST /api/auth/signup
{
  "company_name": "ACME GmbH",
  "contact_email": "admin@acme.de",
  "password": "SecurePass123"
}
→ Returns: JWT token + user + customer

# Login
POST /api/auth/login
{
  "email": "admin@acme.de",
  "password": "SecurePass123"
}
→ Returns: JWT token + user + customer

# Logout (Client-side)
localStorage.removeItem('0711_token');
→ Token wird einfach gelöscht

# Forgot Password
POST /api/auth/forgot-password
{
  "email": "admin@acme.de"
}
→ Sends email with reset link

# Reset Password
POST /api/auth/reset-password
{
  "token": "abc123...",
  "new_password": "NewPass456"
}
→ Updates password_hash
```

### User Management (Team)

```bash
# List Team Members (Customer Admin only)
GET /api/users/?page=1&page_size=20
Authorization: Bearer {token}
→ Returns: Users für aktuellen Customer

# Invite Team Member
POST /api/users/invite
{
  "email": "user@acme.de",
  "first_name": "Tom",
  "last_name": "Schmidt",
  "role": "customer_user",
  "permissions": {"data.upload": true}
}
→ Creates user (status=invited), sends email

# Accept Invitation
POST /api/users/accept-invitation
{
  "token": "abc123...",
  "password": "MyPassword123"
}
→ Sets password, activates user

# Update User
PATCH /api/users/{user_id}
{
  "role": "customer_admin",
  "permissions": {"billing.view": true}
}
→ Updates role/permissions

# Delete User (Soft Delete)
DELETE /api/users/{user_id}
→ Sets deleted_at timestamp

# Change Own Password
POST /api/users/change-password
{
  "current_password": "OldPass123",
  "new_password": "NewPass456"
}
→ Updates password_hash
```

---

## 🎨 Frontend UI

### Customer Console (4020)

**Login**: `/login`
- Email/Password Form
- "Forgot Password?" Link
- Redirects to `/` (Dashboard)

**Settings Hub**: `/settings`
- Profile
- Security (change password)
- **Team** ← Team Management!
- Company
- Billing

**Team Management**: `/settings/team`
- Table: Alle Team Members
  - Name, Email, Role, Status, Actions
- Button: "Invite Member"
- Modal: Invite Form (email, name, role, permissions)
- Actions: Edit (role/permissions), Delete

**Accept Invitation**: `/accept-invitation?token=xxx`
- Token aus URL parsen
- Form: "Set Password"
- Password Strength Indicator
- Submit → Activates user

**Forgot Password**: `/forgot-password`
- Email eingeben
- Submit → Sendet Reset-Email

**Reset Password**: `/reset-password?token=xxx`
- Token aus URL parsen
- Form: "New Password"
- Submit → Updates password

### Admin Portal (4020)

**Login**: `/admin/login`
- Platform Admin credentials
- Red theme (distinguishes from customer)

**Dashboard**: `/admin`
- Stats: Total Customers, Revenue, Pending MCPs
- Quick Links

**Customers**: `/admin/customers`
- All customers table
- View details, Edit, Suspend

**Deployments**: `/admin/deployments` ← NEU!
- Cradle installations table
- Deploy new client
- Download images

### Partner Portal (4020)

**Login**: `/partner-login`
- Partner Admin credentials
- Green theme

**Customers**: `/partner/customers`
- Partner's customers only (filtered by partner_id)
- Add New Customer
- Onboard Customer

**Onboarding**: `/partner/customers/{id}/onboarding`
- Upload files
- Select MCPs
- WebSocket progress tracking

---

## 🔒 Multi-Tenancy & Data Isolation

### Isolation Mechanismus

**1. Customer-Level Isolation**:
```python
# Jeder API-Call hat CustomerContext
ctx: CustomerContext = Depends(require_auth)

# Context enthält
{
  "customer_id": "x1y2z3...",
  "user_id": "abc...",
  "user_email": "admin@kunde.de",
  "is_admin": true,
  "allowed_mcps": ["ctax", "law"]
}

# Alle DB-Queries filtern nach customer_id
users = db.query(User).filter(User.customer_id == ctx.customer_id).all()
# User sieht NUR User seines Customers!
```

**2. Partner-Level Isolation**:
```python
# Partner Admin sieht nur seine Kunden
customers = db.query(Customer).filter(Customer.partner_id == user.partner_id).all()
```

**3. Platform Admin = God Mode**:
```python
# Platform Admin sieht ALLES
if user.role == UserRole.PLATFORM_ADMIN:
    # Kein Filter nach customer_id
    customers = db.query(Customer).all()
```

### Enforcement Points

**Middleware**: `api/middleware/auth.py`
```python
@app.middleware("http")
async def add_customer_context(request, call_next):
    # Extrahiert JWT token
    # Lädt User aus DB
    # Erstellt CustomerContext
    # Setzt request.state.customer_id
    response = await call_next(request)
    return response
```

**Dependencies**: `api/utils/security.py`
```python
def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # Validiert JWT
    # Lädt User aus DB
    # Wirft 401 wenn invalid
    return user

def get_current_customer(user: User = Depends(get_current_user)) -> Customer:
    # Lädt Customer für User
    # Nur wenn user.customer_id gesetzt
    return customer
```

---

## 📊 Beispiel-Daten (Aktueller Stand)

### Platform Admin
```sql
SELECT email, role, customer_id, partner_id FROM users WHERE role = 'platform_admin';

email            | role           | customer_id | partner_id
-----------------|----------------|-------------|------------
admin@0711.io    | platform_admin | NULL        | NULL
```

### Partner Admin (Beispiel)
```sql
SELECT u.email, u.role, p.company_name
FROM users u
JOIN partners p ON u.partner_id = p.id
WHERE u.role = 'partner_admin';

email                | role          | company_name
---------------------|---------------|------------------
max@techconsult.de   | partner_admin | TechConsult GmbH
```

### Customer Admin + Users (Beispiel)
```sql
SELECT u.email, u.role, u.status, c.company_name
FROM users u
JOIN customers c ON u.customer_id = c.id
WHERE c.company_name = 'Lightnet GmbH';

email               | role           | status  | company_name
--------------------|----------------|---------|---------------
admin@lightnet.de   | customer_admin | active  | Lightnet GmbH
user1@lightnet.de   | customer_user  | active  | Lightnet GmbH
user2@lightnet.de   | customer_user  | invited | Lightnet GmbH
```

---

## 🎯 Use Cases

### Use Case 1: Customer Team Expansion

**Szenario**: ACME hat 1 Admin, will 5 User hinzufügen

**Flow**:
1. Admin logged in → /settings/team
2. Klickt 5x "Invite Member"
3. Für jeden: Email, Name, Rolle, Permissions
4. System sendet 5 Emails
5. User klicken Links, setzen Passwörter
6. User loggen sich ein → eingeschränkte Console

**Result**: 6 User total (1 admin + 5 users), alle isolated zu ACME

### Use Case 2: Partner onboards 10 Kunden

**Szenario**: TechConsult (Partner) hat 10 neue Kunden

**Flow**:
1. Partner Admin logged in → /partner/customers
2. Klickt 10x "New Customer"
3. Für jeden: Company Name, Email
4. System erstellt 10 Customer Records (alle mit `partner_id = TechConsult`)
5. System erstellt 10 Customer Admin Users
6. Partner lädt Daten hoch für jeden
7. System deployed 10 Docker Images
8. Partner liefert Images an Kunden

**Result**: 10 Customers, alle managed by TechConsult Partner

### Use Case 3: Platform Admin überwacht alles

**Szenario**: 0711 Admin will alle Deployments sehen

**Flow**:
1. Platform Admin logged in → /admin/deployments
2. Sieht Tabelle: ALLE Kunden (ACME, Lightnet, EATON, etc.)
3. Sieht Service Status (GPU, Vision, DB)
4. Kann jedes Image downloaden
5. Kann neue Clients deployen (für Testing)

**Result**: Vollständiger Überblick über gesamte Plattform

---

## 🔧 Wie man User verwaltet

### Als Customer Admin (Team verwalten)

```bash
# 1. Einloggen
open http://localhost:4020/login
Email: admin@kunde.de
Password: ***

# 2. Team öffnen
Navigate: /settings/team

# 3. User einladen
Klicke: "Invite Member"
Email: neuer.user@kunde.de
Name: Hans Müller
Role: customer_user
Permissions: Auswählen (data.upload, etc.)
Submit

# 4. User erhält Email
# Email enthält Link: /accept-invitation?token=...

# 5. User setzt Passwort
# User klickt Link → Formular → Passwort setzen → Aktiviert

# 6. User kann sich einloggen
# Login → Console (mit eingeschränkten Rechten)
```

### Als Platform Admin (Alle verwalten)

```bash
# 1. Einloggen
open http://localhost:4020/admin/login
Email: admin@0711.io
Password: admin123

# 2. Kunden sehen
Navigate: /admin/customers
# Sieht: Alle Customers (ACME, Lightnet, etc.)

# 3. Deployments verwalten
Navigate: /admin/deployments
# Sieht: Alle Cradle Installations
# Kann: Neue Clients deployen
```

---

## ✅ Was funktioniert JETZT

### Produktiv im Einsatz ✅

**1. Customer Signup & Login**:
- ✅ Signup erstellt Customer + Admin User
- ✅ Login mit JWT
- ✅ Multi-Tenant Isolation (Customer sieht nur eigene Daten)

**2. Team Invitation**:
- ✅ Admin kann User einladen
- ✅ Email mit Token-Link (oder Token in Response bei TESTING=true)
- ✅ User setzt Passwort via /accept-invitation
- ✅ Redis Token-Management (7 Tage Expiry)

**3. Passwort-Management**:
- ✅ Change Password (eigenes Passwort ändern)
- ✅ Forgot Password (Reset-Link per Email)
- ✅ Reset Password (neues Passwort setzen)

**4. Permissions & RBAC**:
- ✅ 4 Rollen (Platform, Partner, Customer Admin/User)
- ✅ Granulare Permissions (JSONB)
- ✅ Permission-Checks in Backend
- ✅ UI passt sich an Permissions an

**5. Admin Portal**:
- ✅ Platform Admin kann alles verwalten
- ✅ Customer Management
- ✅ MCP Approvals
- ✅ Developer Verification
- ✅ **Cradle Deployments** (neu!)

**6. Partner Portal**:
- ✅ Partner kann eigene Kunden verwalten
- ✅ Customer Onboarding Flow
- ✅ File Upload für Kunden
- ✅ WebSocket Progress Tracking

---

## 📚 Code-Referenzen

### Backend (Port 4080)
- **Models**: `api/models/user.py` (User, UserRole, UserStatus)
- **Routes**: `api/routes/users.py` (Invite, Accept, Update, Delete)
- **Auth**: `api/routes/auth.py` (Signup, Login, Forgot, Reset)
- **Security**: `api/utils/security.py` (JWT, Password Hashing, Permissions)

### Frontend (Port 4020)
- **Login**: `console/frontend/src/app/login/page.tsx`
- **Settings**: `console/frontend/src/app/settings/*`
- **Team**: `console/frontend/src/app/settings/team/page.tsx`
- **Accept Invitation**: `console/frontend/src/app/accept-invitation/page.tsx`
- **Forgot/Reset**: `console/frontend/src/app/forgot-password/page.tsx`, `/reset-password/page.tsx`

### Admin Frontend (Port 4020)
- **Layout**: `console/frontend/src/components/admin/AdminLayout.tsx`
- **Dashboard**: `console/frontend/src/app/admin/page.tsx`
- **Customers**: `console/frontend/src/app/admin/customers/page.tsx`
- **Deployments**: `console/frontend/src/app/admin/deployments/page.tsx`

### Partner Frontend (Port 4020)
- **Customers**: `console/frontend/src/app/partner/customers/page.tsx`
- **Onboarding**: `console/frontend/src/app/partner/customers/[id]/onboarding/page.tsx`

---

## 🎯 Zusammenfassung

**User Management ist**:
- ✅ **Multi-Tenant** (Customer Isolation)
- ✅ **Multi-Role** (4 Rollen: Platform, Partner, Customer Admin/User)
- ✅ **Granular Permissions** (JSONB pro User)
- ✅ **Invitation Flow** (Email → Token → Password)
- ✅ **Secure** (JWT, bcrypt, Account Lockout)
- ✅ **Complete UI** (Login, Team Management, Settings)
- ✅ **Production Ready** (läuft bei Lightnet, EATON)

**Kern-Konzept**: Ein User gehört zu einem Customer (oder Partner oder ist Platform Admin), hat eine Rolle, und granulare Permissions die genau steuern was er darf.

**Alles integriert in den Console Builder** - jedes neue Customer-Image bekommt automatisch User Management! 🎉