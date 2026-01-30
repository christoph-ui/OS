# Fix Subscription - Clear Browser Cache

## Problem
Old JWT tokens in localStorage don't work with the new JWT_SECRET configuration.

## Quick Fix

**In your browser (on the Marketplace page):**

1. **Open Developer Tools**: Press `F12` (or `Cmd+Option+I` on Mac)

2. **Go to Console Tab**

3. **Run this command**:
```javascript
localStorage.clear();
alert('Tokens cleared! Logging out...');
window.location.href = '/login';
```

4. **Login Again**:
```
Email: michael.weber@eaton.com
Password: Eaton2025
```

5. **Go to MCPs → Marketplace**

6. **Click Subscribe** - Should work now!

---

## Verification

After subscribing, check the database:
```bash
docker exec 0711-postgres psql -U 0711 -d 0711_control -c \
  "SELECT enabled_mcps FROM customers WHERE contact_email = 'michael.weber@eaton.com';"
```

You should see your subscribed MCPs!

---

## Already Works via API

The subscription backend IS working:
```bash
# Login
curl -s -X POST 'http://localhost:4010/api/auth/login' \
  -H "Content-Type: application/json" \
  -d '{"email": "michael.weber@eaton.com", "password": "Eaton2025"}'

# Subscribe (works!)
curl -s -X POST "http://localhost:4010/api/mcp/marketplace/subscribe/pim" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Just need to clear the browser cache to get the fresh token!
