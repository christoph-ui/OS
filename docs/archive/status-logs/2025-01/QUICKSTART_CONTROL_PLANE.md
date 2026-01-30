# 0711 Control Plane - Quick Start

Get the full stack running in 5 minutes.

## Prerequisites

- Docker & Docker Compose
- Stripe account (for payments)
- SMTP server (for emails)

## Step-by-Step

### 1. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set:

```bash
# Minimum required:
JWT_SECRET=your-secret-key-here
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 2. Start Services

```bash
docker-compose up -d
```

Wait ~30 seconds for services to initialize.

### 3. Verify

```bash
# Check all services are running
docker-compose ps

# Check API health
curl http://localhost:8080/health
```

You should see: `{"status":"healthy"}`

### 4. Access

- **Website**: http://localhost:3000
- **API Docs**: http://localhost:8080/docs
- **MinIO Console**: http://localhost:9001 (admin / 0711_minio_password)
- **Database UI**: http://localhost:8081 (PostgreSQL / 0711 / changeme)

## Test the Signup Flow

### 1. Create Customer Account

```bash
curl -X POST http://localhost:8080/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test GmbH",
    "contact_name": "Max Mustermann",
    "contact_email": "test@example.com",
    "password": "testpass123",
    "company_type": "GmbH"
  }'
```

Response:
```json
{
  "message": "Bitte bestätigen Sie Ihre E-Mail-Adresse",
  "customer_id": "uuid-here"
}
```

### 2. Login

```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "customer": { ... }
}
```

### 3. Create Subscription (Free Starter)

Since email verification is required in the full flow, for testing you can manually verify the customer in the database:

```bash
docker-compose exec postgres psql -U 0711 -d 0711_control \
  -c "UPDATE customers SET email_verified = true WHERE contact_email = 'test@example.com';"
```

Then create a free deployment:

```bash
curl -X POST http://localhost:8080/api/deployments/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "name": "My First Deployment",
    "deployment_type": "self_hosted",
    "mcps_enabled": ["ctax"]
  }'
```

## Check the Data

### PostgreSQL (via Adminer)

1. Go to http://localhost:8081
2. Login:
   - System: PostgreSQL
   - Server: postgres
   - Username: 0711
   - Password: changeme
   - Database: 0711_control

3. Browse tables:
   - customers
   - subscriptions
   - deployments
   - invoices

### MinIO (Model Storage)

1. Go to http://localhost:9001
2. Login: `0711_admin` / `0711_minio_password`
3. Create bucket: `0711-models`
4. Upload test files

## Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (DELETES DATA!)
docker-compose down -v
```

## Troubleshooting

**API won't start**:
```bash
docker-compose logs api
# Check for database connection errors
```

**Database connection failed**:
```bash
# Check if postgres is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres
```

**Website can't reach API**:
- Verify NEXT_PUBLIC_API_URL in website/.env.local
- Check CORS settings in api/config.py
- Ensure API is running: `curl http://localhost:8080/health`

## Next Steps

1. **Set up Stripe Products** - Create products in Stripe Dashboard
2. **Configure SMTP** - Test email sending
3. **Test Payment Flow** - Create a paid subscription
4. **Build Admin Console** - Convert HTML prototype to Next.js
5. **Add Real Data** - Seed experts and MCPs

## Production Deployment

See `DEPLOYMENT.md` for full production deployment guide.

---

**Questions?** Check README.md or DEPLOYMENT.md
