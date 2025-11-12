# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Infinite Backrooms seriously. If you discover a security vulnerability, please follow these steps:

### 1. Do Not Publicly Disclose

Please do not create a public GitHub issue for security vulnerabilities. This helps protect users while a fix is being developed.

### 2. Report Privately

Report security vulnerabilities by:
- Opening a private security advisory on GitHub
- Or emailing the maintainer directly through GitHub

### 3. Provide Details

Include the following information in your report:
- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if available)
- Your contact information for follow-up questions

### 4. Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - Critical: Within 7 days
  - High: Within 14 days
  - Medium: Within 30 days
  - Low: Next scheduled release

## Security Best Practices

When using Infinite Backrooms:

1. **Input Validation**: Be cautious when creating persona names and roles with user-provided input
2. **Network Security**: Ensure your Ollama instance is properly secured
3. **File Permissions**: Log files may contain sensitive conversation data - secure appropriately
4. **Updates**: Keep dependencies updated to receive security patches
5. **Environment**: Run in a trusted environment, especially when exposing via network

## Known Security Considerations

### XSS Protection
- Version 0.1.0+: HTML sanitization implemented for all user-provided content
- Persona names and roles are escaped before rendering

### File Operations
- Log files are created with appropriate permissions
- Error handling prevents crashes on file I/O errors

### Dependencies
- Regular dependency audits recommended
- No unnecessary dependencies in production builds

## Security Updates

Security updates will be announced via:
- GitHub Security Advisories
- Release notes with `[SECURITY]` prefix
- Updated CHANGELOG.md

## Contact

For security-related questions that are not vulnerabilities, you can open a regular GitHub issue labeled with `security-question`.

---

Thank you for helping keep Infinite Backrooms and its users safe!
