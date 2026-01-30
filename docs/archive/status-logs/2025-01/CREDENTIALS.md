# 0711 Platform - User Credentials

**Generated**: 2025-11-25

---

## 🔐 Console Access (Port 4020)

### Enterprise Admin - e-ProCat
- **Email**: `christoph@eprocat.de`
- **Password**: `0711Enterprise!`
- **Company**: e-ProCat GmbH
- **Tier**: Enterprise
- **Role**: Admin
- **Access**: Full system access

### Enterprise Admin - Eaton
- **Email**: `michael.weber@eaton.com`
- **Password**: `Eaton2025`
- **Company**: Eaton Industries GmbH
- **Tier**: Enterprise
- **Role**: Admin
- **Access**: Full system access

### Platform Admin
- **Email**: `admin@0711.io`
- **Password**: `admin123!`
- **Company**: 0711 Intelligence
- **Role**: Admin
- **Access**: Full system access

### Demo User
- **Email**: `demo@0711.io`
- **Password**: `demo123`
- **Company**: Demo Corp
- **Role**: User
- **Access**: Standard user access

---

## 💾 Database Access

### PostgreSQL (Port 4005)
- **Host**: localhost
- **Port**: 4005
- **Database**: `0711_control`
- **User**: `0711`
- **Password**: `0711_dev_password`

**Connection String:**
```
postgresql://0711:0711_dev_password@localhost:4005/0711_control
```

**Docker Command:**
```bash
docker exec 0711-postgres psql -U 0711 -d 0711_control
```

---

## 📦 MinIO Storage (Ports 4050/4051)

### API Access (Port 4050)
- **Endpoint**: http://localhost:4050
- **Access Key**: `0711admin`
- **Secret Key**: `0711secret`

### Web Console (Port 4051)
- **URL**: http://localhost:4051
- **Username**: `0711admin`
- **Password**: `0711secret`

---

## 🔑 API Keys

### Control Plane API
**For Next.js → FastAPI calls:**
- **API Key**: `dev_api_key_for_nextjs_to_fastapi_calls`
- **Header**: `Authorization: Bearer {api_key}`

### Webhook Secret
**For FastAPI → Next.js webhooks:**
- **Secret**: `dev_webhook_secret_shared_between_systems`
- **Used for**: HMAC signature verification

### JWT Secret
**For token generation:**
- **Secret**: `VGhpc0lzQVNlY3VyZVNlY3JldEtleUZvckRldmVsb3BtZW50`
- **Algorithm**: HS256
- **Expiration**: 7 days

---

## 🧪 Test Commands

### Login to Console
```bash
curl -X POST http://localhost:4010/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "christoph@eprocat.de",
    "password": "0711Enterprise!"
  }'
```

### Get Current User
```bash
# First login to get token, then:
curl http://localhost:4010/api/auth/me \
  -H "Authorization: Bearer {token}"
```

---

## 📊 Customer Data in Database

### e-ProCat GmbH (Enterprise)
- **Customer ID**: `00000000-0000-0000-0000-000000000001`
- **Deployment ID**: `00000000-0000-0000-0000-000000000101`
- **License Key**: `ENTERPRISE-0711-EPROCAT-2025`
- **Status**: Active
- **Tier**: Enterprise

**Query:**
```sql
SELECT * FROM customers WHERE company_name = 'e-ProCat GmbH';
SELECT * FROM deployments WHERE customer_id = '00000000-0000-0000-0000-000000000001';
```

---

## ⚠️ Security Notes

**Development Mode - NOT FOR PRODUCTION:**

1. All passwords are simple and stored in this file
2. JWT secret is static (regenerate for prod)
3. API keys are placeholders
4. MinIO uses default credentials
5. Database password is weak
6. SSL/TLS not configured

**Before Production:**
- [ ] Generate strong random secrets
- [ ] Use environment-specific .env files
- [ ] Enable SSL/TLS
- [ ] Set up proper user management
- [ ] Configure rate limiting
- [ ] Enable audit logging
- [ ] Set DEBUG=false

---

## 📝 Quick Reference

**Login to any service:**
```
Email: christoph@eprocat.de
Password: 0711Enterprise!
```

**Connect to database:**
```bash
docker exec 0711-postgres psql -U 0711 -d 0711_control
```

**View MinIO files:**
```
http://localhost:4051
Username: 0711admin / Password: 0711secret
```

---

**Keep this file secure! Contains all access credentials.**
