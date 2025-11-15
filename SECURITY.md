# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Infinite Backrooms seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via:
- Email: [Create an issue with "SECURITY" prefix and we'll contact you privately]
- GitHub Security Advisories: Use the "Security" tab in this repository

Please include the following information:
- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### What to Expect

- Acknowledgment of your report within 48 hours
- Regular updates on our progress
- Notification when the vulnerability is fixed
- Public credit for responsible disclosure (if desired)

## Security Best Practices

When using Infinite Backrooms:

1. **Never commit sensitive data**
   - Don't commit `.env` files with real credentials
   - Don't commit API keys or tokens
   - Review conversation logs before sharing

2. **Network security**
   - Run Ollama on localhost only unless you have proper network security
   - Use firewalls to restrict access to Ollama ports
   - Don't expose Streamlit to the public internet without authentication

3. **Docker security**
   - Keep Docker images updated
   - Review docker-compose.yml network settings
   - Use secrets management for sensitive configuration

4. **Dependencies**
   - Keep all dependencies updated
   - Review security advisories regularly
   - Use `pip-audit` or similar tools to check for known vulnerabilities

5. **Logs and data**
   - Conversation logs may contain sensitive information
   - Configure appropriate file permissions for log directories
   - Implement log rotation and retention policies

## Known Security Considerations

1. **Local-only by design**: This application is designed to run locally and connect to a local Ollama instance. It is not designed for multi-user or public internet deployment without significant additional security measures.

2. **No authentication**: The Streamlit interface does not include authentication. Anyone with access to the application can view and modify conversations.

3. **Conversation privacy**: All conversations are stored in plain text log files. Ensure appropriate file system permissions.

4. **Ollama access**: The application makes direct HTTP requests to Ollama. Ensure your Ollama instance is properly secured.

## Security Updates

Security updates will be released as soon as possible after a vulnerability is confirmed. Updates will be announced through:
- GitHub Security Advisories
- Release notes
- CHANGELOG.md

## Attribution

We appreciate the security research community and will publicly acknowledge researchers who report valid security issues (unless they prefer to remain anonymous).
