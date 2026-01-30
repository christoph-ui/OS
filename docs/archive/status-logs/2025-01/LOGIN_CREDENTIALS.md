# 0711 Platform - Login Credentials Reference

**Last Updated**: 2025-11-30
**Environment**: Development

---

## 🏢 Customer Login (Companies)

**Login Page**: http://localhost:4000/login

### Eaton Industries GmbH
- **Email**: `michael.weber@eaton.com`
- **Password**: `Eaton2025`
- **Company ID**: `00000000-0000-0000-0000-000000000002`
- **Status**: Active, Email Verified ✅
- **Dashboard**: http://localhost:4020 (Console)
- **Features**: Full platform access, ETIM MCP enabled

### Other Test Customers
Check database for more:
```bash
docker exec 0711-postgres psql -U 0711 -d 0711_control -c \
  "SELECT company_name, contact_email, status FROM customers;"
```

---

## 🚀 Expert Login (Experts Operating MCPs)

**Login Page**: http://localhost:4000/expert-login

### Sarah Mueller - Tax Specialist
- **Email**: `sarah@0711.expert`
- **Password**: `Expert123!`
- **Expert ID**: Check database
- **Status**: Active, Verified ✅
- **MCPs**: CTAX, FPA, LEGAL
- **Rating**: 4.9 ⭐
- **Dashboard**: http://localhost:4000/expert/dashboard (TO BE CREATED)

---

## 🔐 Authentication Endpoints

### Customer Authentication
```
POST /api/auth/login
  Body: { "email": "michael.weber@eaton.com", "password": "Eaton2025" }
  Returns: { "access_token": "...", "customer_id": "...", "company_name": "..." }
```

### Expert Authentication
```
POST /api/expert-auth/login
  Body: { "email": "sarah@0711.expert", "password": "Expert123!" }
  Returns: { "access_token": "...", "expert_id": "...", "name": "...", "mcps": [...] }
```

---

## 🎯 Quick Access Links

### For Companies (Eaton)
- Login: http://localhost:4000/login
- Console: http://localhost:4020
- Browse Experts: http://localhost:4000/experts-marketplace
- My Experts: http://localhost:4000/company/my-experts

### For Experts (Sarah)
- Login: http://localhost:4000/expert-login
- Signup: http://localhost:4000/expert-signup
- Profile: http://localhost:4000/experts/[id]
- Dashboard: http://localhost:4000/expert/dashboard

### For Admins
- Expert Applications: http://localhost:4000/admin/experts
- Customer Management: http://localhost:4000/admin

---

## 🆘 Troubleshooting

### Customer Login Fails
```bash
# Verify customer exists and has password
docker exec 0711-postgres psql -U 0711 -d 0711_control -c \
  "SELECT contact_email, password_hash IS NOT NULL as has_password,
   email_verified, status FROM customers
   WHERE contact_email = 'michael.weber@eaton.com';"
```

### Expert Login Fails
```bash
# Verify expert exists and has password
docker exec 0711-postgres psql -U 0711 -d 0711_control -c \
  "SELECT email, password_hash IS NOT NULL as has_password,
   status, verified FROM experts
   WHERE email = 'sarah@0711.expert';"
```

### API Not Responding
```bash
# Check if API is running
ps aux | grep "uvicorn api.main"

# Restart API
pkill -f "uvicorn api.main"
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 4080 --reload &
```

---

## 🔑 Password Reset

### For Customers
Currently manual - run:
```bash
docker exec 0711-postgres psql -U 0711 -d 0711_control -c "
UPDATE customers SET password_hash = '[NEW_HASH]'
WHERE contact_email = '[EMAIL]';
"
```

### For Experts
Currently manual - run:
```bash
docker exec 0711-postgres psql -U 0711 -d 0711_control -c "
UPDATE experts SET password_hash = '[NEW_HASH]'
WHERE email = '[EMAIL]';
"
```

---

**Note**: Both authentication systems are now operational and working!
