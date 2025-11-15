# streamlit-security-hardener

**Purpose**: Implement comprehensive security hardening for Streamlit applications

**Use When**: Preparing application for production deployment, addressing security vulnerabilities, or implementing security best practices

---

## Domain Knowledge

### OWASP Top 10 for Web Applications
1. **Injection** (SQL, Command, XSS)
2. **Broken Authentication**
3. **Sensitive Data Exposure**
4. **XML External Entities (XXE)**
5. **Broken Access Control**
6. **Security Misconfiguration**
7. **Cross-Site Scripting (XSS)**
8. **Insecure Deserialization**
9. **Using Components with Known Vulnerabilities**
10. **Insufficient Logging & Monitoring**

### Streamlit-Specific Security Concerns
- HTML rendering can introduce XSS vulnerabilities
- Session state accessible client-side
- File upload handling requires validation
- No built-in authentication/authorization
- Rate limiting not included by default

### Security Defense Layers
1. **Input Validation**: Validate all user inputs
2. **Output Encoding**: Sanitize all outputs
3. **Authentication**: Verify user identity
4. **Authorization**: Control resource access
5. **Rate Limiting**: Prevent abuse
6. **Logging**: Detect and respond to attacks

---

## Workflow

### Step 1: Audit Current Security Posture (45-60 min)

**Security Checklist**:
```bash
# Check for unsafe HTML rendering
grep -rn "st.markdown.*unsafe_allow_html=True" src/ streamlit*.py

# Find file operations
grep -rn "open(" src/ streamlit*.py | grep -v "with open"

# Check for hardcoded secrets
grep -rn "password\|secret\|api_key\|token" --include="*.py" | grep -v "TODO"

# Find eval/exec usage (dangerous)
grep -rn "eval\|exec" --include="*.py"

# Check for subprocess calls
grep -rn "subprocess\|os.system" --include="*.py"

# Find pickle usage (insecure serialization)
grep -rn "pickle.loads\|pickle.load" --include="*.py"
```

**Document Findings**:
| Vulnerability | Severity | Location | Impact |
|---------------|----------|----------|--------|
| XSS in markdown | CRITICAL | streamlit_backroom.py:450 | Code execution |
| Path traversal | HIGH | logger.py:120 | File system access |
| No rate limiting | MEDIUM | All endpoints | DoS vulnerability |
| Hardcoded API key | HIGH | config.py:15 | Credential exposure |

### Step 2: Implement Input Validation (60-90 min)

**Pattern: Comprehensive Input Validator**:
```python
"""Comprehensive input validation for security."""
import re
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Validates inputs for security vulnerabilities.

    Prevents injection attacks, path traversal, and malicious inputs.
    """

    # Validation patterns
    MODEL_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-:]+$')
    CONVERSATION_ID_PATTERN = re.compile(r'^conv_[0-9]{8}_[0-9]{6}$')
    SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.]+$')

    # Dangerous patterns to block
    INJECTION_PATTERNS = [
        r'\.\./+',  # Path traversal
        r'[;&|`$]',  # Command injection
        r'<script',  # XSS
        r'javascript:',  # XSS
        r'on\w+\s*=',  # Event handler injection
    ]

    @classmethod
    def validate_model_name(cls, model_name: str) -> str:
        """Validate Ollama model name.

        Args:
            model_name: Model name to validate

        Returns:
            str: Validated model name

        Raises:
            ValueError: If validation fails

        Example:
            >>> SecurityValidator.validate_model_name("llama2")
            'llama2'
            >>> SecurityValidator.validate_model_name("../../../etc/passwd")
            ValueError: Invalid model name
        """
        if not model_name or not isinstance(model_name, str):
            raise ValueError("Model name must be a non-empty string")

        if len(model_name) > 100:
            raise ValueError("Model name too long (max 100 characters)")

        if not cls.MODEL_NAME_PATTERN.match(model_name):
            raise ValueError(
                f"Invalid model name: {model_name}. "
                "Only alphanumeric, underscore, hyphen, and colon allowed."
            )

        # Check for injection patterns
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, model_name, re.IGNORECASE):
                logger.warning(f"Blocked potentially malicious model name: {model_name}")
                raise ValueError("Model name contains prohibited patterns")

        return model_name

    @classmethod
    def validate_prompt(cls, prompt: str, max_length: int = 10000) -> str:
        """Validate user prompt.

        Args:
            prompt: User prompt to validate
            max_length: Maximum allowed length

        Returns:
            str: Validated prompt

        Raises:
            ValueError: If validation fails
        """
        if not isinstance(prompt, str):
            raise ValueError("Prompt must be a string")

        if len(prompt) > max_length:
            raise ValueError(f"Prompt too long (max {max_length} characters)")

        # Check for excessive newlines (potential DoS)
        if prompt.count('\n') > 100:
            raise ValueError("Prompt contains too many newlines")

        return prompt

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename to prevent path traversal.

        Args:
            filename: Filename to sanitize

        Returns:
            str: Safe filename

        Raises:
            ValueError: If filename is unsafe

        Example:
            >>> SecurityValidator.sanitize_filename("report.txt")
            'report.txt'
            >>> SecurityValidator.sanitize_filename("../../etc/passwd")
            ValueError: Unsafe filename
        """
        if not filename or not isinstance(filename, str):
            raise ValueError("Filename must be a non-empty string")

        # Remove any path components
        filename = Path(filename).name

        # Check against safe pattern
        if not cls.SAFE_FILENAME_PATTERN.match(filename):
            raise ValueError(
                f"Unsafe filename: {filename}. "
                "Only alphanumeric, underscore, hyphen, and dot allowed."
            )

        # Verify no path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            raise ValueError("Filename contains path traversal attempts")

        return filename

    @classmethod
    def validate_path(cls, path: Path, base_dir: Path) -> Path:
        """Validate file path is within allowed directory.

        Args:
            path: Path to validate
            base_dir: Base directory that path must be within

        Returns:
            Path: Validated absolute path

        Raises:
            ValueError: If path escapes base directory

        Example:
            >>> base = Path("/app/logs")
            >>> SecurityValidator.validate_path(Path("conv.json"), base)
            Path('/app/logs/conv.json')
            >>> SecurityValidator.validate_path(Path("../../etc/passwd"), base)
            ValueError: Path escapes base directory
        """
        # Resolve to absolute path
        try:
            absolute_path = (base_dir / path).resolve()
        except Exception as e:
            raise ValueError(f"Invalid path: {e}")

        # Ensure path is within base directory
        try:
            absolute_path.relative_to(base_dir)
        except ValueError:
            logger.warning(f"Blocked path traversal attempt: {path}")
            raise ValueError(
                f"Path {path} escapes base directory {base_dir}"
            )

        return absolute_path

    @classmethod
    def validate_conversation_id(cls, conv_id: str) -> str:
        """Validate conversation ID format.

        Args:
            conv_id: Conversation ID to validate

        Returns:
            str: Validated conversation ID

        Raises:
            ValueError: If format is invalid
        """
        if not isinstance(conv_id, str):
            raise ValueError("Conversation ID must be a string")

        if not cls.CONVERSATION_ID_PATTERN.match(conv_id):
            raise ValueError(
                f"Invalid conversation ID format: {conv_id}. "
                "Expected format: conv_YYYYMMDD_HHMMSS"
            )

        return conv_id

    @classmethod
    def check_injection_patterns(cls, text: str) -> bool:
        """Check if text contains potential injection patterns.

        Args:
            text: Text to check

        Returns:
            bool: True if safe, False if potentially malicious
        """
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        return True
```

### Step 3: Implement HTML Sanitization (45-60 min)

**Pattern: XSS Prevention**:
```python
"""HTML sanitization to prevent XSS attacks."""
import bleach
from typing import Optional, List


class HTMLSanitizer:
    """Sanitizes HTML content to prevent XSS attacks.

    Uses bleach library for whitelist-based sanitization.
    """

    # Allowed HTML tags (whitelist)
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'a', 'span', 'div'
    ]

    # Allowed HTML attributes
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title'],
        'span': ['class'],
        'div': ['class'],
        'code': ['class']
    }

    # Allowed CSS properties
    ALLOWED_STYLES = [
        'color', 'background-color', 'font-weight', 'font-style',
        'text-decoration', 'font-size'
    ]

    @classmethod
    def sanitize_html(
        cls,
        html_content: str,
        strip: bool = True
    ) -> str:
        """Sanitize HTML content to prevent XSS.

        Args:
            html_content: HTML to sanitize
            strip: Whether to strip disallowed tags

        Returns:
            str: Sanitized HTML

        Example:
            >>> HTMLSanitizer.sanitize_html('<script>alert("XSS")</script>')
            ''
            >>> HTMLSanitizer.sanitize_html('<p>Safe content</p>')
            '<p>Safe content</p>'
        """
        if not html_content:
            return ""

        # Use bleach for whitelist-based sanitization
        sanitized = bleach.clean(
            html_content,
            tags=cls.ALLOWED_TAGS,
            attributes=cls.ALLOWED_ATTRIBUTES,
            styles=cls.ALLOWED_STYLES,
            strip=strip
        )

        return sanitized

    @classmethod
    def sanitize_markdown(cls, markdown_content: str) -> str:
        """Sanitize markdown content before rendering.

        Args:
            markdown_content: Markdown to sanitize

        Returns:
            str: Sanitized markdown

        Example:
            >>> HTMLSanitizer.sanitize_markdown('**Bold** text')
            '**Bold** text'
            >>> HTMLSanitizer.sanitize_markdown('<script>alert("XSS")</script>')
            '&lt;script&gt;alert("XSS")&lt;/script&gt;'
        """
        # Remove any HTML tags from markdown
        return bleach.clean(markdown_content, tags=[], strip=True)

    @classmethod
    def escape_html(cls, text: str) -> str:
        """Escape HTML entities in text.

        Args:
            text: Text to escape

        Returns:
            str: HTML-escaped text
        """
        return bleach.clean(text, tags=[], strip=False)
```

**Update Streamlit Usage**:
```python
import streamlit as st
from src.utils.html_sanitizer import HTMLSanitizer

# ❌ UNSAFE
st.markdown(user_input, unsafe_allow_html=True)

# ✅ SAFE
sanitized_html = HTMLSanitizer.sanitize_html(user_input)
st.markdown(sanitized_html, unsafe_allow_html=True)

# ✅ SAFER (if HTML not needed)
sanitized_text = HTMLSanitizer.sanitize_markdown(user_input)
st.markdown(sanitized_text)  # No unsafe_allow_html
```

### Step 4: Implement Authentication (90-120 min)

**Pattern: Simple Authentication**:
```python
"""Simple authentication for Streamlit."""
import streamlit as st
import hashlib
import secrets
from typing import Optional


class StreamlitAuth:
    """Simple authentication system for Streamlit.

    NOT FOR PRODUCTION - use proper auth service like Auth0, Okta, etc.
    This is a basic implementation for demonstration.
    """

    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, bytes]:
        """Hash password with salt.

        Args:
            password: Password to hash
            salt: Optional salt (generated if not provided)

        Returns:
            tuple: (hashed_password, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(32)

        # Use PBKDF2 for password hashing
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000  # iterations
        )

        return hashed.hex(), salt

    @staticmethod
    def verify_password(
        password: str,
        hashed_password: str,
        salt: bytes
    ) -> bool:
        """Verify password against hash.

        Args:
            password: Password to verify
            hashed_password: Stored password hash
            salt: Salt used in hashing

        Returns:
            bool: True if password matches
        """
        computed_hash, _ = StreamlitAuth.hash_password(password, salt)
        return secrets.compare_digest(computed_hash, hashed_password)

    @staticmethod
    def login_form():
        """Display login form and handle authentication.

        Returns:
            bool: True if authenticated
        """
        # Check if already authenticated
        if st.session_state.get('authenticated', False):
            return True

        st.title("🔐 Login Required")

        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                # Verify credentials (use proper user database in production)
                if StreamlitAuth.authenticate_user(username, password):
                    st.session_state['authenticated'] = True
                    st.session_state['username'] = username
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")

        return False

    @staticmethod
    def authenticate_user(username: str, password: str) -> bool:
        """Authenticate user credentials.

        Args:
            username: Username
            password: Password

        Returns:
            bool: True if authenticated

        NOTE: This is a stub - implement proper user database lookup
        """
        # TODO: Replace with proper user database
        # For demo purposes only
        if username == "demo" and password == "demo123":
            return True
        return False

    @staticmethod
    def logout():
        """Log out current user."""
        st.session_state['authenticated'] = False
        st.session_state['username'] = None
        st.rerun()

    @staticmethod
    def require_auth(func):
        """Decorator to require authentication for functions.

        Usage:
            @StreamlitAuth.require_auth
            def protected_function():
                st.write("This requires authentication")
        """
        def wrapper(*args, **kwargs):
            if not StreamlitAuth.login_form():
                st.stop()
            return func(*args, **kwargs)
        return wrapper
```

### Step 5: Implement Rate Limiting (60-90 min)

**Pattern: Rate Limiter**:
```python
"""Rate limiting to prevent abuse."""
import time
from collections import defaultdict
from typing import Optional
import streamlit as st


class RateLimiter:
    """Rate limiter to prevent API abuse.

    Implements token bucket algorithm for rate limiting.
    """

    def __init__(
        self,
        max_requests: int = 60,
        time_window: int = 60
    ):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)

    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for identifier.

        Args:
            identifier: Unique identifier (IP, user ID, etc.)

        Returns:
            bool: True if request allowed
        """
        current_time = time.time()

        # Clean old requests outside time window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if current_time - req_time < self.time_window
        ]

        # Check if under limit
        if len(self.requests[identifier]) < self.max_requests:
            self.requests[identifier].append(current_time)
            return True

        return False

    def get_wait_time(self, identifier: str) -> Optional[float]:
        """Get wait time until next request allowed.

        Args:
            identifier: Unique identifier

        Returns:
            float: Seconds to wait, or None if allowed now
        """
        if self.is_allowed(identifier):
            # Remove the request we just added (was just checking)
            self.requests[identifier].pop()
            return None

        # Calculate wait time until oldest request expires
        current_time = time.time()
        oldest_request = min(self.requests[identifier])
        wait_time = self.time_window - (current_time - oldest_request)

        return max(0, wait_time)


# Global rate limiter instances
MESSAGE_RATE_LIMITER = RateLimiter(max_requests=20, time_window=60)
CONNECTION_RATE_LIMITER = RateLimiter(max_requests=5, time_window=60)


def get_client_id() -> str:
    """Get unique client identifier for rate limiting.

    Returns:
        str: Client identifier
    """
    # Use session ID as identifier
    # In production, use IP address or authenticated user ID
    if 'client_id' not in st.session_state:
        import uuid
        st.session_state['client_id'] = str(uuid.uuid4())

    return st.session_state['client_id']


def enforce_rate_limit(rate_limiter: RateLimiter, action: str):
    """Enforce rate limit for action.

    Args:
        rate_limiter: RateLimiter instance
        action: Description of action being rate limited

    Raises:
        st.stop: If rate limit exceeded
    """
    client_id = get_client_id()

    if not rate_limiter.is_allowed(client_id):
        wait_time = rate_limiter.get_wait_time(client_id)
        st.error(
            f"Rate limit exceeded for {action}. "
            f"Please wait {wait_time:.0f} seconds before trying again."
        )
        st.stop()
```

### Step 6: Implement Secure Logging (45-60 min)

**Pattern: Secure Audit Logging**:
```python
"""Secure audit logging for security events."""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class SecurityAuditLogger:
    """Audit logger for security-relevant events.

    Logs authentication attempts, authorization failures,
    input validation failures, and suspicious activity.
    """

    def __init__(self, log_file: Path):
        """Initialize security audit logger.

        Args:
            log_file: Path to audit log file
        """
        self.log_file = log_file
        self.logger = logging.getLogger('security_audit')
        self.logger.setLevel(logging.INFO)

        # Create file handler
        handler = logging.FileHandler(log_file)
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
        )
        self.logger.addHandler(handler)

    def log_event(
        self,
        event_type: str,
        severity: str,
        message: str,
        metadata: Optional[dict] = None
    ):
        """Log security event.

        Args:
            event_type: Type of event (auth, validation, etc.)
            severity: Event severity (low, medium, high, critical)
            message: Event description
            metadata: Additional event metadata
        """
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'severity': severity,
            'message': message,
            'metadata': metadata or {}
        }

        log_message = json.dumps(event)

        if severity in ['high', 'critical']:
            self.logger.error(log_message)
        elif severity == 'medium':
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

    def log_auth_attempt(
        self,
        username: str,
        success: bool,
        client_id: Optional[str] = None
    ):
        """Log authentication attempt.

        Args:
            username: Username attempted
            success: Whether authentication succeeded
            client_id: Client identifier
        """
        self.log_event(
            event_type='authentication',
            severity='medium' if not success else 'low',
            message=f"Authentication {'succeeded' if success else 'failed'} for user: {username}",
            metadata={'username': username, 'client_id': client_id}
        )

    def log_validation_failure(
        self,
        input_type: str,
        value: str,
        reason: str
    ):
        """Log input validation failure.

        Args:
            input_type: Type of input (model_name, path, etc.)
            value: Input value that failed
            reason: Failure reason
        """
        self.log_event(
            event_type='validation_failure',
            severity='high',
            message=f"Validation failed for {input_type}: {reason}",
            metadata={'input_type': input_type, 'value': value[:100]}
        )

    def log_rate_limit_exceeded(
        self,
        client_id: str,
        action: str
    ):
        """Log rate limit violation.

        Args:
            client_id: Client identifier
            action: Action that was rate limited
        """
        self.log_event(
            event_type='rate_limit',
            severity='medium',
            message=f"Rate limit exceeded for action: {action}",
            metadata={'client_id': client_id, 'action': action}
        )
```

---

## Best Practices

### Input Validation
1. Validate all user inputs at entry points
2. Use whitelist validation (allow known good, not block known bad)
3. Validate data type, length, format, and range
4. Reject invalid input, don't try to sanitize

### Output Encoding
1. Always escape/sanitize before rendering
2. Use context-appropriate encoding
3. Never trust data from external sources
4. Use bleach or similar libraries for HTML

### Authentication & Authorization
1. Use established libraries/services (Auth0, Okta)
2. Never roll your own crypto
3. Use secure password hashing (PBKDF2, bcrypt, scrypt)
4. Implement proper session management

### Rate Limiting
1. Limit by user/IP/session
2. Different limits for different actions
3. Provide clear error messages
4. Log rate limit violations

### Logging
1. Log all security-relevant events
2. Don't log sensitive data (passwords, tokens)
3. Use structured logging (JSON)
4. Monitor logs for suspicious patterns

---

## Success Criteria

- [ ] All user inputs validated
- [ ] HTML sanitization implemented
- [ ] XSS vulnerabilities eliminated
- [ ] Path traversal prevented
- [ ] Authentication system deployed
- [ ] Rate limiting active
- [ ] Security audit logging enabled
- [ ] No hardcoded secrets
- [ ] Security headers configured
- [ ] Dependency vulnerabilities resolved

---

## Tools Available
- Read: Audit code for vulnerabilities
- Edit: Fix security issues
- Write: Create security utilities
- Bash: Run security scans
- Grep: Find dangerous patterns

---

## Validation Commands

```bash
# Find unsafe HTML rendering
grep -rn "unsafe_allow_html=True" .

# Check for hardcoded secrets
grep -rn "password\|api_key\|secret" --include="*.py" | grep -v "TODO"

# Find dangerous functions
grep -rn "eval\|exec\|pickle" --include="*.py"

# Run security audit
pip install bandit
bandit -r src/ -f json -o security_report.json

# Check dependencies
pip install safety
safety check --json

# Run all security tests
pytest tests/security/ -v

# Validate input sanitization
python -m pytest tests/test_validation.py -v
```
