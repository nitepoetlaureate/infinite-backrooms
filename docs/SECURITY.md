# Security Documentation

Comprehensive security guide for deploying and maintaining Infinite AI Backrooms.

## Table of Contents

- [Security Overview](#security-overview)
- [Implemented Security Features](#implemented-security-features)
- [Deployment Security](#deployment-security)
- [Network Security](#network-security)
- [Application Security](#application-security)
- [Data Security](#data-security)
- [Monitoring and Incident Response](#monitoring-and-incident-response)
- [Security Checklist](#security-checklist)
- [Vulnerability Reporting](#vulnerability-reporting)

---

## Security Overview

Infinite AI Backrooms implements multiple layers of security to protect against common vulnerabilities and ensure safe operation in production environments.

### Security Principles

1. **Defense in Depth**: Multiple layers of security controls
2. **Least Privilege**: Minimal permissions for all components
3. **Input Validation**: All user inputs are validated and sanitized
4. **Secure by Default**: Security features enabled by default
5. **Transparency**: Open source allows security audits

### Threat Model

**Assets to Protect:**
- User conversation data
- System configuration
- API endpoints
- Server resources

**Potential Threats:**
- Injection attacks (SQL, command, code)
- Denial of Service (DoS/DDoS)
- Regular Expression DoS (ReDoS)
- Path traversal attacks
- Information disclosure
- Man-in-the-middle attacks

---

## Implemented Security Features

### 1. Input Validation

All user inputs are validated using comprehensive validation functions.

#### Persona Name Validation

```python
from src.utils.validation import validate_persona_name

# Validates:
# - Non-empty names
# - Length limits (max 50 characters)
# - Allowed characters: alphanumeric, spaces, hyphens, underscores
# - Prevents injection attacks

is_valid, error = validate_persona_name(user_input)
if not is_valid:
    st.error(error)
```

**Prevents:**
- Code injection
- XSS attacks
- Database manipulation
- File system attacks

#### Model Name Validation

```python
from src.utils.validation import validate_model_name

# Validates Ollama model format: name or name:tag
# Prevents command injection via model names

is_valid, error = validate_model_name(model_name)
```

**Prevents:**
- Command injection
- Path traversal
- Arbitrary code execution

#### URL Validation

```python
from src.utils.validation import validate_url

# Validates:
# - Proper URL format
# - Only http/https protocols
# - Prevents SSRF attacks

is_valid, error = validate_url(ollama_url)
```

**Prevents:**
- Server-Side Request Forgery (SSRF)
- Protocol smuggling
- Internal network scanning

#### Path Sanitization

```python
from src.utils.validation import sanitize_log_filename

# Removes:
# - Path traversal attempts (..)
# - Directory separators (/, \)
# - Unsafe characters

safe_filename = sanitize_log_filename(user_provided_name)
```

**Prevents:**
- Path traversal attacks
- Arbitrary file access
- File system manipulation

### 2. ReDoS Protection

Regular Expression Denial of Service (ReDoS) protection with timeout mechanism.

```python
import re
import signal
import platform

def regex_search_with_timeout(pattern: str, text: str, timeout: int = 5):
    """Execute regex search with timeout protection."""
    try:
        compiled_pattern = re.compile(pattern, re.IGNORECASE)

        # Timeout protection (Unix only)
        if platform.system() != 'Windows':
            def timeout_handler(signum, frame):
                raise TimeoutError("Regex search timed out")

            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)

            try:
                result = compiled_pattern.search(text)
            finally:
                signal.alarm(0)  # Cancel alarm
        else:
            # Windows: No signal support, use simpler approach
            result = compiled_pattern.search(text)

        return result

    except re.error:
        raise ValueError("Invalid regular expression")
    except TimeoutError:
        raise TimeoutError("Regex search timed out")
```

**Configuration:**

```env
# .env
REGEX_TIMEOUT=5  # 5-second timeout for regex operations
```

**Prevents:**
- Catastrophic backtracking
- CPU exhaustion
- Denial of Service

### 3. Information Disclosure Prevention

Error messages are sanitized to prevent information leakage.

```python
import logging

logger = logging.getLogger(__name__)

try:
    # Sensitive operation
    result = perform_sensitive_operation()
except Exception as e:
    # Log detailed error server-side
    logger.error(f"Operation failed: {e}", exc_info=True)

    # Show generic message to user
    st.error("An error occurred. Please try again.")

    # Optional: Show details in expandable section (for debugging)
    if DEBUG:
        with st.expander("Technical details"):
            st.code(str(e))
```

**Prevents:**
- Stack trace exposure
- Configuration disclosure
- Internal path disclosure
- Database structure leakage

### 4. Environment Variable Security

Sensitive configuration stored in environment variables, not code.

```env
# .env (gitignored)
OLLAMA_URL=https://ollama.internal:11434
API_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@host/db
```

**Configuration loaded securely:**

```python
from dotenv import load_dotenv
import os

load_dotenv()

# Access secrets
OLLAMA_URL = os.getenv("OLLAMA_URL")
API_KEY = os.getenv("API_KEY")

# Never log secrets
logger.info(f"Connecting to {OLLAMA_URL}")  # OK
logger.debug(f"API Key: {API_KEY}")  # NEVER DO THIS
```

**Best Practices:**
- Never commit `.env` files
- Use `.env.example` as template
- Rotate secrets regularly
- Use secret management systems in production

### 5. SSL/TLS Support

HTTPS support for Ollama connections with certificate verification.

```python
import ssl
import aiohttp

class SecureOllamaClient:
    def __init__(
        self,
        base_url: str,
        verify_ssl: bool = True,
        ca_cert_path: str = None
    ):
        self.base_url = base_url
        self.verify_ssl = verify_ssl

        # Create SSL context
        if verify_ssl:
            self.ssl_context = ssl.create_default_context()
            if ca_cert_path:
                self.ssl_context.load_verify_locations(ca_cert_path)
        else:
            self.ssl_context = False  # Disable verification (dev only)

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            ssl=self.ssl_context,
            force_close=True
        )
        self.session = aiohttp.ClientSession(connector=connector)
        return self
```

**Configuration:**

```env
# Production (always verify)
OLLAMA_VERIFY_SSL=true

# Development with self-signed cert (not recommended)
OLLAMA_VERIFY_SSL=false
```

### 6. Rate Limiting (Recommended)

Implement rate limiting for production deployments.

```python
# Example using nginx
# /etc/nginx/conf.d/rate-limit.conf

limit_req_zone $binary_remote_addr zone=backrooms:10m rate=10r/s;

server {
    location / {
        limit_req zone=backrooms burst=20 nodelay;
        limit_req_status 429;

        proxy_pass http://localhost:8501;
    }
}
```

Or application-level with Streamlit:

```python
from functools import wraps
import time
from collections import defaultdict

# Simple rate limiter
rate_limit_store = defaultdict(list)

def rate_limit(max_calls: int, time_window: int):
    """Rate limit decorator."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = st.session_state.get("session_id", "anonymous")
            now = time.time()

            # Clean old entries
            rate_limit_store[user_id] = [
                t for t in rate_limit_store[user_id]
                if now - t < time_window
            ]

            # Check limit
            if len(rate_limit_store[user_id]) >= max_calls:
                st.error("Rate limit exceeded. Please wait before trying again.")
                return None

            # Add current request
            rate_limit_store[user_id].append(now)

            return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@rate_limit(max_calls=10, time_window=60)  # 10 calls per minute
def process_message(message: str):
    # Process message
    pass
```

---

## Deployment Security

### 1. Operating System Hardening

#### Update System Regularly

```bash
# Enable automatic security updates (Ubuntu/Debian)
sudo apt-get install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades

# Manual updates
sudo apt-get update && sudo apt-get upgrade -y
```

#### Disable Unnecessary Services

```bash
# List running services
systemctl list-units --type=service --state=running

# Disable unused services
sudo systemctl disable cups
sudo systemctl stop cups
```

#### Configure Firewall

```bash
# Install UFW
sudo apt-get install ufw

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose
```

### 2. SSH Hardening

Edit `/etc/ssh/sshd_config`:

```
# Disable root login
PermitRootLogin no

# Disable password authentication (use keys only)
PasswordAuthentication no
PubkeyAuthentication yes

# Disable empty passwords
PermitEmptyPasswords no

# Limit authentication attempts
MaxAuthTries 3

# Limit concurrent sessions
MaxSessions 2

# Use strong ciphers
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com

# Enable logging
LogLevel VERBOSE
```

Restart SSH:

```bash
sudo systemctl restart sshd
```

### 3. Application User Security

Run application as dedicated user (not root):

```bash
# Create application user
sudo useradd -m -s /bin/bash backrooms

# No sudo privileges
# No password login

# Set file permissions
sudo chown -R backrooms:backrooms /home/backrooms/infinite-backrooms
sudo chmod 750 /home/backrooms/infinite-backrooms
```

### 4. File Permissions

```bash
# Application directory
chmod 750 /home/backrooms/infinite-backrooms

# Configuration files
chmod 600 /home/backrooms/infinite-backrooms/.env

# Log directory
chmod 750 /home/backrooms/infinite-backrooms/conversations

# Log files
chmod 640 /home/backrooms/infinite-backrooms/conversations/*.txt

# Executable scripts
chmod 750 /home/backrooms/infinite-backrooms/scripts/*.sh
```

---

## Network Security

### 1. Reverse Proxy Security

#### Nginx Security Headers

```nginx
# /etc/nginx/conf.d/security-headers.conf

# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self' 'unsafe-inline' 'unsafe-eval'; connect-src 'self' ws: wss:;" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;

# Hide server information
server_tokens off;

# Prevent clickjacking
add_header X-Permitted-Cross-Domain-Policies "none" always;
```

#### SSL/TLS Configuration

```nginx
# /etc/nginx/conf.d/ssl.conf

# SSL protocols and ciphers
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers on;

# SSL session cache
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;

# OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;

# HSTS (enforce HTTPS)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

### 2. Network Segmentation

Isolate components on separate networks:

```
┌─────────────────┐
│  Internet       │
└────────┬────────┘
         │
    ┌────▼─────┐
    │ Firewall │
    └────┬─────┘
         │
    ┌────▼──────────┐
    │  DMZ          │  Public subnet
    │  - Web server │  - 10.0.1.0/24
    │  - Nginx      │
    └────┬──────────┘
         │
    ┌────▼──────────┐
    │ App Network   │  Private subnet
    │ - Streamlit   │  - 10.0.2.0/24
    └────┬──────────┘
         │
    ┌────▼──────────┐
    │ Backend       │  Private subnet
    │ - Ollama      │  - 10.0.3.0/24
    └───────────────┘
```

### 3. DDoS Protection

#### Application Level

Use CDN with DDoS protection:
- Cloudflare
- AWS CloudFront + Shield
- Google Cloud Armor
- Akamai

#### Network Level

Configure fail2ban:

```bash
# Install fail2ban
sudo apt-get install fail2ban

# Configure for nginx
sudo nano /etc/fail2ban/jail.local
```

```ini
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-noscript]
enabled = true
port = http,https
logpath = /var/log/nginx/access.log

[nginx-badbots]
enabled = true
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 2
```

Restart fail2ban:

```bash
sudo systemctl restart fail2ban
sudo fail2ban-client status
```

---

## Application Security

### 1. Secure Coding Practices

#### Avoid Common Vulnerabilities

```python
# BAD: SQL Injection vulnerability
query = f"SELECT * FROM users WHERE name = '{user_input}'"

# GOOD: Parameterized query
query = "SELECT * FROM users WHERE name = ?"
cursor.execute(query, (user_input,))

# BAD: Command injection vulnerability
os.system(f"ls {user_input}")

# GOOD: Use subprocess with list
subprocess.run(["ls", user_input], check=True)

# BAD: Path traversal vulnerability
file_path = f"logs/{user_input}.txt"

# GOOD: Sanitize input
from src.utils.validation import sanitize_log_filename
safe_name = sanitize_log_filename(user_input)
file_path = f"logs/{safe_name}.txt"
```

### 2. Dependency Security

#### Regular Updates

```bash
# Check for vulnerabilities
uv pip install safety
uv run safety check

# Update dependencies
uv sync --upgrade

# Audit dependencies
uv pip list --outdated
```

#### Pin Dependencies

Always use pinned versions:

```toml
# pyproject.toml
[project]
dependencies = [
    "aiohttp>=3.8.0,<4.0.0",    # Pin major version
    "streamlit>=1.39.0,<2.0.0",
    "pandas>=2.0.0,<3.0.0",
]
```

#### Automated Dependency Scanning

Use GitHub Dependabot:

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

### 3. Security Scanning

#### Bandit (Security Linter)

```bash
# Install bandit
uv pip install bandit

# Run security scan
uv run bandit -r . -f json -o bandit-report.json

# Check specific files
uv run bandit streamlit_backroom.py
```

#### SAST (Static Application Security Testing)

Use CodeQL or Semgrep:

```yaml
# .github/workflows/security.yml
name: Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Run Bandit
        run: |
          pip install bandit
          bandit -r . -f json -o bandit-report.json

      - name: Run Safety
        run: |
          pip install safety
          safety check --json

      - name: CodeQL Analysis
        uses: github/codeql-action/analyze@v2
```

---

## Data Security

### 1. Data at Rest

#### Encrypt Conversation Logs

```python
from cryptography.fernet import Fernet
import os

class EncryptedLogger:
    def __init__(self, encryption_key: str = None):
        # Load or generate encryption key
        key = encryption_key or os.getenv("LOG_ENCRYPTION_KEY")
        if not key:
            key = Fernet.generate_key().decode()
            print(f"Generated new key: {key}")
            print("Store this key securely!")

        self.cipher = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt_message(self, message: str) -> bytes:
        """Encrypt message before writing to log."""
        return self.cipher.encrypt(message.encode())

    def decrypt_message(self, encrypted: bytes) -> str:
        """Decrypt message when reading log."""
        return self.cipher.decrypt(encrypted).decode()

    def log_message(self, persona: str, message: str):
        """Log encrypted message."""
        encrypted = self.encrypt_message(f"{persona}: {message}")
        # Write encrypted bytes to file
```

#### Disk Encryption

Enable full disk encryption:

```bash
# Linux: Use LUKS
cryptsetup luksFormat /dev/sdb
cryptsetup open /dev/sdb encrypted_disk
mkfs.ext4 /dev/mapper/encrypted_disk

# Mount encrypted volume
mount /dev/mapper/encrypted_disk /mnt/secure
```

### 2. Data in Transit

All data in transit must use TLS/SSL:

```env
# Force HTTPS
OLLAMA_URL=https://ollama.internal:11434
OLLAMA_VERIFY_SSL=true
```

Nginx forces HTTPS:

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### 3. Data Retention

Implement data retention policies:

```python
# src/utils/retention.py
from datetime import datetime, timedelta
from pathlib import Path

def enforce_retention_policy(
    log_dir: Path,
    retention_days: int = 90
):
    """Delete logs older than retention period."""
    cutoff = datetime.now() - timedelta(days=retention_days)

    for log_file in log_dir.glob("*.txt"):
        try:
            # Parse date from filename
            date_str = log_file.stem.split("_")[-1]
            file_date = datetime.strptime(date_str, "%Y-%m-%d")

            if file_date < cutoff:
                log_file.unlink()
                print(f"Deleted old log: {log_file}")
        except (ValueError, IndexError):
            pass  # Skip files with unexpected names

# Run daily via cron
if __name__ == "__main__":
    enforce_retention_policy(Path("conversations"), retention_days=90)
```

---

## Monitoring and Incident Response

### 1. Security Monitoring

#### Log All Security Events

```python
import logging

# Configure security logger
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.WARNING)

handler = logging.FileHandler("/var/log/backrooms/security.log")
handler.setFormatter(logging.Formatter(
    "%(asctime)s - SECURITY - %(levelname)s - %(message)s"
))
security_logger.addHandler(handler)

# Log security events
def log_security_event(event_type: str, details: dict):
    security_logger.warning(f"{event_type}: {details}")

# Examples
log_security_event("INVALID_INPUT", {
    "user": user_id,
    "input": sanitized_input,
    "violation": "Path traversal attempt"
})

log_security_event("RATE_LIMIT_EXCEEDED", {
    "user": user_id,
    "endpoint": "/api/generate",
    "count": request_count
})
```

#### Monitor Failed Login Attempts

```bash
# Watch auth logs
sudo tail -f /var/log/auth.log | grep "Failed password"

# Setup alert for multiple failures
# Install logtrigger or similar
```

### 2. Incident Response Plan

#### Incident Categories

1. **Severity 1 (Critical)**: Data breach, system compromise
2. **Severity 2 (High)**: Service outage, security vulnerability
3. **Severity 3 (Medium)**: Performance degradation
4. **Severity 4 (Low)**: Minor issues, informational

#### Response Procedures

**Step 1: Detection and Analysis**
- Identify the incident type and severity
- Gather evidence and logs
- Assess impact and scope

**Step 2: Containment**
- Isolate affected systems
- Block malicious traffic
- Preserve evidence

**Step 3: Eradication**
- Remove threat or vulnerability
- Patch systems
- Update security rules

**Step 4: Recovery**
- Restore services
- Verify system integrity
- Monitor for reoccurrence

**Step 5: Lessons Learned**
- Document incident
- Update procedures
- Implement preventive measures

### 3. Security Alerts

Configure automated alerts:

```python
# Example: Email alert on security event
import smtplib
from email.mime.text import MIMEText

def send_security_alert(subject: str, message: str):
    """Send security alert email."""
    msg = MIMEText(message)
    msg['Subject'] = f"[SECURITY ALERT] {subject}"
    msg['From'] = "alerts@your-domain.com"
    msg['To'] = "security-team@your-domain.com"

    with smtplib.SMTP('localhost') as smtp:
        smtp.send_message(msg)

# Trigger on critical events
if detect_intrusion_attempt():
    send_security_alert(
        "Intrusion Attempt Detected",
        f"Multiple failed authentication attempts from {ip_address}"
    )
```

---

## Security Checklist

### Deployment Checklist

- [ ] All dependencies updated and scanned for vulnerabilities
- [ ] Environment variables configured (no secrets in code)
- [ ] SSL/TLS enabled and certificates valid
- [ ] Firewall configured and unnecessary ports closed
- [ ] Application running as non-root user
- [ ] File permissions properly configured
- [ ] Input validation enabled
- [ ] Error messages sanitized
- [ ] Security headers configured in reverse proxy
- [ ] Rate limiting implemented
- [ ] Logging enabled and monitored
- [ ] Backup system configured
- [ ] Incident response plan documented

### Ongoing Security Tasks

#### Daily
- [ ] Review security logs
- [ ] Monitor system resources
- [ ] Check for unusual activity

#### Weekly
- [ ] Review access logs
- [ ] Check for failed login attempts
- [ ] Verify backup integrity
- [ ] Review alerts and incidents

#### Monthly
- [ ] Update dependencies
- [ ] Review user accounts and permissions
- [ ] Test backup restoration
- [ ] Review and update firewall rules
- [ ] Conduct security scan (bandit, safety)

#### Quarterly
- [ ] Security audit
- [ ] Penetration testing
- [ ] Update incident response plan
- [ ] Security training for team
- [ ] Review and update security policies

---

## Vulnerability Reporting

### How to Report

If you discover a security vulnerability:

1. **DO NOT** open a public issue
2. Email security contact directly: security@your-domain.com
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

1. **Acknowledgment** within 48 hours
2. **Initial assessment** within 7 days
3. **Regular updates** on progress
4. **Credit** in security advisory (if desired)

### Responsible Disclosure

We follow a 90-day disclosure timeline:
- Day 0: Vulnerability reported
- Day 7: Severity assessment completed
- Day 30: Fix developed and tested
- Day 60: Fix deployed to production
- Day 90: Public disclosure (if not resolved sooner)

---

## Security Resources

### External Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

### Tools

- **Bandit**: Python security linter
- **Safety**: Dependency vulnerability scanner
- **OWASP ZAP**: Web application security scanner
- **Nmap**: Network scanner
- **Wireshark**: Network protocol analyzer

### Documentation

- [Deployment Guide](DEPLOYMENT.md)
- [Production Setup](PRODUCTION_SETUP.md)
- [Monitoring Guide](MONITORING.md)

---

**Last Updated:** 2025-11-13
**Version:** 1.0.0
