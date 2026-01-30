# Security Policy

## Supported Versions

We release security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**DO NOT open public issues for security vulnerabilities.**

### How to Report

Send vulnerability reports to: **security@0711.io**

### What to Include

Please provide the following information:

1. **Description**: Clear description of the vulnerability
2. **Impact**: Potential security impact (data exposure, unauthorized access, etc.)
3. **Steps to Reproduce**: Detailed steps to reproduce the issue
4. **Proof of Concept**: Code or screenshots demonstrating the vulnerability (if applicable)
5. **Suggested Fix**: Your recommendations for fixing the issue (optional)
6. **Environment**: OS, Python version, deployment mode, etc.

### Response Timeline

- **Initial Response**: Within 48 hours
- **Assessment**: Within 7 days
- **Fix Timeline**: Depends on severity
  - Critical: 7-14 days
  - High: 30 days
  - Medium: 60 days
  - Low: 90 days

### Disclosure Policy

- **Coordinated Disclosure**: We prefer coordinated disclosure
- **Public Disclosure**: After fix is deployed and customers are notified
- **Credit**: Security researchers will be credited (unless they prefer anonymity)

## Security Features

### Authentication & Authorization

- **JWT Tokens**: HS256 algorithm with 7-day expiration
- **Role-Based Access Control (RBAC)**: User roles (platform_admin, customer_admin, customer_user)
- **Granular Permissions**: JSONB-based permission system
- **Failed Login Protection**: Account lockout after 5 failed attempts
- **Password Requirements**: Minimum 8 characters

### Data Protection

- **Per-Customer Isolation**: Separate MinIO buckets, lakehouse directories, LoRA adapters
- **Encryption at Rest**: Customer data encrypted in MinIO
- **Encryption in Transit**: HTTPS/TLS for all API calls
- **DSGVO/GDPR Compliance**: Data minimization, right to erasure, audit logging

### API Security

- **Input Validation**: Pydantic schemas for all API inputs
- **SQL Injection Prevention**: SQLAlchemy ORM (parameterized queries)
- **XSS Prevention**: Input sanitization on frontend
- **CORS**: Configurable CORS origins
- **Rate Limiting**: 100 requests/minute, 2000 requests/hour per user

### Secrets Management

- **Environment Variables**: All secrets in `.env` (never committed)
- **Secret Rotation**: Recommended every 90 days
- **API Key Storage**: Hashed before storage in database
- **Webhook Signatures**: HMAC-SHA256 for webhook verification

### Infrastructure Security

- **Docker Isolation**: Each customer has isolated containers
- **Network Segmentation**: Customer services on private networks
- **Database Security**: PostgreSQL with strong passwords, limited access
- **Redis Security**: Password-protected, no public exposure

## Security Best Practices for Users

### For Administrators

1. **Rotate Secrets Regularly**
   ```bash
   # Generate new secrets every 90 days
   ./scripts/generate-secrets.sh
   ```

2. **Use Strong Database Passwords**
   ```bash
   # Minimum 24 characters
   openssl rand -base64 32
   ```

3. **Enable Audit Logging**
   ```python
   # In .env
   ENABLE_AUDIT_LOGGING=true
   ```

4. **Restrict CORS Origins**
   ```python
   # In .env - Only allow your domains
   CORS_ORIGINS=["https://yourdomain.com"]
   ```

5. **Keep Dependencies Updated**
   ```bash
   pip install --upgrade -r requirements.txt
   npm update
   ```

### For Developers

1. **Never Commit Secrets**
   - Always use `.env` for secrets
   - Check `.gitignore` before commits
   - Use `git diff` to review staged changes

2. **Validate All Input**
   ```python
   from pydantic import BaseModel, validator

   class MyModel(BaseModel):
       email: str

       @validator('email')
       def validate_email(cls, v):
           # Validate email format
           return v
   ```

3. **Use Parameterized Queries**
   ```python
   # ✓ CORRECT - SQLAlchemy ORM
   users = db.query(User).filter(User.email == email).all()

   # ✗ WRONG - SQL injection risk
   db.execute(f"SELECT * FROM users WHERE email = '{email}'")
   ```

4. **Sanitize File Uploads**
   ```python
   # Validate file extensions
   ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx"}
   if file.suffix not in ALLOWED_EXTENSIONS:
       raise ValueError("Invalid file type")
   ```

5. **Use HTTPS in Production**
   ```nginx
   # Nginx config
   server {
       listen 443 ssl;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
   }
   ```

### For Self-Hosted Deployments

1. **Firewall Configuration**
   ```bash
   # Only expose necessary ports
   ufw allow 80/tcp   # HTTP
   ufw allow 443/tcp  # HTTPS
   ufw enable
   ```

2. **Regular Backups**
   ```bash
   # Backup customer data daily
   ./scripts/backup-customer-data.sh
   ```

3. **Monitor Logs**
   ```bash
   # Check for suspicious activity
   tail -f logs/api.log
   grep "ERROR" logs/*.log
   ```

4. **Keep System Updated**
   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt upgrade

   # Docker images
   docker compose pull
   docker compose up -d
   ```

## Known Security Considerations

### Model Inference

- **Prompt Injection**: User queries are sent to LLM - implement input filtering
- **Data Leakage**: Ensure customer data isolation in RAG queries
- **Token Limits**: Implement rate limiting to prevent DoS

### File Uploads

- **File Size Limits**: Maximum 100MB per file (configurable)
- **Malicious Files**: Scan uploads with ClamAV (recommended)
- **Path Traversal**: Validate file paths before saving

### Third-Party APIs

- **API Key Exposure**: Rotate keys if exposed
- **Rate Limits**: Respect provider rate limits
- **Dependency Vulnerabilities**: Run `pip-audit` regularly

## Compliance

### DSGVO/GDPR

- **Data Minimization**: Only collect necessary data
- **Right to Access**: Customers can export their data
- **Right to Erasure**: Customers can delete their accounts
- **Audit Logging**: All data access logged
- **Data Processing Agreement**: Available on request

### SOC 2 (Planned)

- Security controls aligned with SOC 2 Type II requirements
- Annual third-party audits planned for 2026

## Security Tooling

### Recommended Tools

```bash
# Dependency scanning
pip install pip-audit
pip-audit

# Secret scanning
pip install detect-secrets
detect-secrets scan

# Static analysis
pip install bandit
bandit -r .

# Container scanning
docker scan 0711/platform:latest
```

### CI/CD Security Checks

Add to GitHub Actions:
```yaml
- name: Security scan
  run: |
    pip install pip-audit bandit
    pip-audit
    bandit -r api/ ingestion/ lakehouse/
```

## Contact

- **Security Team**: security@0711.io
- **General Support**: support@0711.io
- **Legal**: legal@0711.io

---

**Last Updated**: 2025-01-29
