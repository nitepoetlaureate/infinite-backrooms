# Security Policy

## Overview

This document outlines the security measures implemented in the Infinite AI Backrooms Streamlit application. The application has been hardened for production deployment with multiple layers of security controls.

## Security Architecture

### Defense in Depth

The application implements multiple security layers:

1. **Input Validation** - All user inputs are validated before processing
2. **Output Sanitization** - All outputs are sanitized to prevent injection attacks
3. **Rate Limiting** - API calls and user actions are rate-limited
4. **Error Handling** - Errors are handled securely without leaking sensitive information
5. **Session Security** - Streamlit sessions are configured with security best practices
6. **Secure Configuration** - Production configuration disables development features

## Security Measures

### 1. Input Validation

**Location**: `src/utils/validation.py`

All user inputs are validated before use:

- **Persona Names**: Limited to 50 characters, alphanumeric + spaces/hyphens/underscores only
- **Model Names**: Must match Ollama naming convention (name[:tag])
- **System Prompts**: Limited to 10,000 characters
- **URLs**: Must be valid http/https URLs (localhost and IP addresses allowed)
- **Colors**: Must be valid hex color codes (#RGB or #RRGGBB)
- **Roles**: Limited to 50 characters, safe characters only
- **Timeouts**: Must be between 10-600 seconds

**Security Benefits**:
- Prevents command injection attacks
- Prevents path traversal attacks
- Prevents DoS via excessively long inputs
- Ensures data integrity

### 2. Output Sanitization

**Location**: `src/utils/sanitization.py`

All user-controlled data rendered in HTML is sanitized:

- **HTML Escaping**: All persona names, roles, and colors are HTML-escaped
- **CSS Validation**: Color values are validated to prevent CSS injection
- **Markdown Escaping**: Markdown special characters are escaped when needed
- **URL Sanitization**: URLs are validated to prevent javascript: and data: URIs

**Security Benefits**:
- Prevents Cross-Site Scripting (XSS) attacks
- Prevents CSS injection attacks
- Prevents HTML injection attacks

**Example**:
```python
# Before sanitization (vulnerable)
persona_name = '<script>alert("xss")</script>'
html = f'<span>{persona_name}</span>'  # XSS vulnerability!

# After sanitization (secure)
from src.utils.sanitization import sanitize_html
safe_name = sanitize_html(persona_name)
html = f'<span>{safe_name}</span>'  # Safe: outputs escaped HTML
```

### 3. Rate Limiting

**Location**: `src/utils/rate_limiter.py`

Implemented rate limits to prevent abuse:

- **Ollama API**: 30 requests per minute
- **Conversation Turns**: 100 turns per 5 minutes
- **Manual Messages**: 20 messages per minute
- **Auto-Run Mode**: 1000 turns per hour

**Features**:
- Sliding window rate limiting
- Progressive penalties for violations
- Temporary locks after repeated violations
- Per-session tracking

**Security Benefits**:
- Prevents Denial of Service (DoS) attacks
- Prevents API abuse
- Ensures fair resource usage
- Protects against automated attacks

**Usage Example**:
```python
from src.utils.rate_limiter import check_rate_limit

allowed, error = check_rate_limit("ollama_api", session_id)
if not allowed:
    st.error(error)
    return
```

### 4. Regular Expression Security

**Location**: `log_viewer.py`

The regex search feature in log viewer has been protected against ReDoS (Regular Expression Denial of Service) attacks:

- **Timeout Protection**: 5-second timeout on regex searches (Unix systems)
- **Error Handling**: Invalid regex patterns are caught and reported safely
- **Input Validation**: Regex patterns are compiled and validated before use

**Security Benefits**:
- Prevents catastrophic backtracking attacks
- Prevents application hang/freeze
- Safe error messages without information leakage

### 5. Error Handling

**Locations**: Throughout codebase

All error handlers follow security best practices:

- **No Bare Exceptions**: All `except:` handlers specify exception types
- **Sanitized Error Messages**: Error messages don't leak sensitive information
- **Debug Logging**: Detailed errors logged for debugging but not shown to users
- **User-Friendly Messages**: Users see helpful messages without technical details

**Example**:
```python
# Before (vulnerable)
try:
    result = process_data()
except:  # Bare exception
    st.error(f"Error: {sys.exc_info()}")  # Leaks details!

# After (secure)
try:
    result = process_data()
except ValueError as e:
    logger.debug(f"Validation error: {e}")  # Log details
    st.error("Invalid input. Please check your data.")  # Safe message
except Exception as e:
    logger.error(f"Unexpected error: {type(e).__name__}")
    st.error("An error occurred. Please try again.")
```

### 6. Session Security

**Location**: `.streamlit/config.toml`

Streamlit is configured with security-focused settings:

- **XSRF Protection**: Enabled (`enableXsrfProtection = true`)
- **Custom Cookie Name**: Unique session cookie name
- **CORS Enabled**: Configured for legitimate cross-origin requests
- **Upload Limits**: Max 10MB uploads to prevent DoS
- **Message Limits**: Max 200MB message size
- **Error Details Hidden**: Detailed errors not shown in production

### 7. Secure Configuration

**Production Settings**:

- **Magic Commands Disabled**: `magicEnabled = false`
- **Static Serving Disabled**: `enableStaticServing = false`
- **File Watching Disabled**: `fileWatcherType = "none"`
- **Auto-Reload Disabled**: `runOnSave = false`
- **Usage Stats Disabled**: `gatherUsageStats = false`
- **Minimal Toolbar**: `toolbarMode = "minimal"`

### 8. Secrets Management

**Location**: `.gitignore`

Sensitive files are excluded from version control:

```
.env
*.log
conversations/*.txt
.streamlit/secrets.toml
```

**Best Practices**:
- No hardcoded secrets in code
- Environment variables for configuration
- Secrets rotation strategy documented
- API keys stored securely

### 9. Logging Security

**Location**: `src/services/logger.py`

Conversation logging is designed with security in mind:

- **Sanitized Filenames**: Path traversal prevention
- **UTF-8 Encoding**: Proper character handling
- **No Sensitive Data**: Only conversation content is logged
- **Access Controls**: Log files should have restricted permissions

**Recommendation**:
```bash
# Set proper permissions on log directory
chmod 750 conversations/
chmod 640 conversations/*.txt
```

## Security Checklist

- [x] All user inputs validated
- [x] All outputs sanitized (HTML, CSS, URLs)
- [x] Rate limiting implemented
- [x] No bare exception handlers
- [x] Error messages don't leak sensitive info
- [x] XSRF protection enabled
- [x] Secure session configuration
- [x] Secrets properly managed
- [x] Security headers configured
- [x] XSS prevention in place
- [x] ReDoS protection implemented
- [x] SQL injection not applicable (no SQL database)
- [x] Production settings configured

## Vulnerability Fixes

### Fixed Vulnerabilities

1. **XSS in components.py** (CRITICAL)
   - **Issue**: User-controlled persona names/colors directly inserted into HTML
   - **Fix**: All HTML output is now sanitized using `sanitize_html()` and `sanitize_css_value()`
   - **Files**: `src/ui/components.py`

2. **ReDoS in log_viewer.py** (HIGH)
   - **Issue**: User-provided regex patterns could cause catastrophic backtracking
   - **Fix**: Added 5-second timeout and error handling for regex operations
   - **Files**: `log_viewer.py` (lines 187-227)

3. **Bare Exception Handlers** (MEDIUM)
   - **Issue**: Generic `except:` blocks could hide errors and leak information
   - **Fix**: All exception handlers now specify exception types
   - **Files**: `src/services/ollama_client.py`

4. **Missing Input Validation** (HIGH)
   - **Issue**: No validation on persona creation inputs
   - **Fix**: Comprehensive validation in `AIPersona.__post_init__()`
   - **Files**: `src/models/persona.py`, `src/utils/validation.py`

5. **No Rate Limiting** (HIGH)
   - **Issue**: Unlimited API calls could lead to abuse
   - **Fix**: Implemented comprehensive rate limiting system
   - **Files**: `src/utils/rate_limiter.py`

## Deployment Recommendations

### For Production Deployment

1. **Set Proper File Permissions**:
   ```bash
   chmod 750 conversations/
   chmod 640 conversations/*.txt
   chmod 600 .streamlit/secrets.toml
   ```

2. **Use HTTPS**:
   - Deploy behind a reverse proxy (nginx, Apache, Caddy)
   - Enable SSL/TLS encryption
   - Use valid SSL certificates

3. **Environment Configuration**:
   ```bash
   export STREAMLIT_SERVER_ENABLE_CORS=true
   export STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true
   export STREAMLIT_CLIENT_SHOW_ERROR_DETAILS=false
   ```

4. **Network Security**:
   - Use firewall to restrict access
   - Only expose necessary ports
   - Consider VPN or IP whitelisting for admin access

5. **Monitoring**:
   - Monitor log files for suspicious activity
   - Set up alerts for rate limit violations
   - Track error rates and response times

6. **Regular Updates**:
   - Keep Streamlit updated to latest stable version
   - Update Python dependencies regularly
   - Monitor security advisories

### Reverse Proxy Example (nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name backroom.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' 'unsafe-inline' 'unsafe-eval'; img-src 'self' data:; font-src 'self' data:;" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=streamlit:10m rate=10r/s;
    limit_req zone=streamlit burst=20 nodelay;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

## Reporting Security Issues

If you discover a security vulnerability, please report it by:

1. **DO NOT** create a public GitHub issue
2. Email security details to the maintainers
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

We will respond within 48 hours and work with you to address the issue.

## Security Updates

- **2025-01-13**: Initial security hardening
  - Added input validation and sanitization
  - Implemented rate limiting
  - Fixed XSS and ReDoS vulnerabilities
  - Configured secure Streamlit settings
  - Added comprehensive security documentation

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Streamlit Security](https://docs.streamlit.io/library/advanced-features/configuration)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)

## License

This security documentation is part of the Infinite AI Backrooms project and follows the same license.
