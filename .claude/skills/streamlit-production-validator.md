# streamlit-production-validator

**Purpose**: Validate Streamlit application production readiness with comprehensive checks

**Use When**: Before deploying to production, during final validation phase, or establishing deployment standards

---

## Domain Knowledge

### Production Readiness Checklist
- **Security**: Vulnerabilities resolved, authentication implemented
- **Performance**: Load tested, optimized, no memory leaks
- **Reliability**: Error handling, logging, monitoring
- **Scalability**: Resource limits, connection pooling
- **Maintainability**: Documentation, code quality, test coverage

### Deployment Environment Types
- **Development**: Local testing with hot reload
- **Staging**: Production-like environment for final validation
- **Production**: Live environment serving real users

### Critical Production Metrics
- **Uptime**: Target 99.9% (< 8.76 hours downtime/year)
- **Response Time**: Target < 2 seconds for p95
- **Error Rate**: Target < 0.1%
- **Test Coverage**: Target > 80%

---

## Workflow

### Step 1: Create Production Validation Script (60-90 min)

**Pattern: Comprehensive Validation**:
```python
"""Production readiness validation script."""
import subprocess
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime


class ProductionValidator:
    """Validates application production readiness.

    Performs comprehensive checks across security, performance,
    reliability, and code quality dimensions.
    """

    def __init__(self, project_root: Path):
        """Initialize validator.

        Args:
            project_root: Path to project root directory
        """
        self.project_root = project_root
        self.results = {
            'timestamp': datetime.utcnow().isoformat(),
            'checks': [],
            'passed': 0,
            'failed': 0,
            'warnings': 0
        }

    def run_all_checks(self) -> bool:
        """Run all production readiness checks.

        Returns:
            bool: True if all critical checks pass
        """
        print("🚀 Running production readiness validation...\n")

        # Security checks
        self._check_no_unsafe_html()
        self._check_no_hardcoded_secrets()
        self._check_input_validation()
        self._check_dependency_vulnerabilities()

        # Performance checks
        self._check_connection_pooling()
        self._check_memory_limits()
        self._check_timeout_configuration()

        # Reliability checks
        self._check_error_handling()
        self._check_logging_configured()
        self._check_health_checks()

        # Code quality checks
        self._check_test_coverage()
        self._check_linting()
        self._check_type_hints()

        # Configuration checks
        self._check_environment_variables()
        self._check_production_config()

        # Documentation checks
        self._check_readme_exists()
        self._check_deployment_docs()

        # Generate report
        self._print_report()

        return self.results['failed'] == 0

    def _add_result(
        self,
        check_name: str,
        status: str,
        message: str,
        severity: str = 'medium'
    ):
        """Add check result.

        Args:
            check_name: Name of check
            status: 'pass', 'fail', or 'warn'
            message: Result message
            severity: 'low', 'medium', 'high', 'critical'
        """
        self.results['checks'].append({
            'name': check_name,
            'status': status,
            'message': message,
            'severity': severity
        })

        if status == 'pass':
            self.results['passed'] += 1
            print(f"✅ {check_name}: {message}")
        elif status == 'fail':
            self.results['failed'] += 1
            print(f"❌ {check_name}: {message}")
        elif status == 'warn':
            self.results['warnings'] += 1
            print(f"⚠️  {check_name}: {message}")

    def _check_no_unsafe_html(self):
        """Check for unsafe HTML rendering."""
        try:
            result = subprocess.run(
                ['grep', '-rn', 'unsafe_allow_html=True', 'src/', 'streamlit*.py'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and result.stdout:
                # Found unsafe HTML usage
                count = len(result.stdout.strip().split('\n'))
                self._add_result(
                    'Unsafe HTML Rendering',
                    'fail',
                    f"Found {count} instances of unsafe_allow_html=True",
                    severity='critical'
                )
            else:
                self._add_result(
                    'Unsafe HTML Rendering',
                    'pass',
                    "No unsafe HTML rendering detected"
                )
        except Exception as e:
            self._add_result(
                'Unsafe HTML Rendering',
                'warn',
                f"Check failed: {e}"
            )

    def _check_no_hardcoded_secrets(self):
        """Check for hardcoded secrets."""
        patterns = [
            'password\s*=\s*["\'][^"\']+["\']',
            'api_key\s*=\s*["\'][^"\']+["\']',
            'secret\s*=\s*["\'][^"\']+["\']',
            'token\s*=\s*["\'][^"\']+["\']'
        ]

        found_secrets = []
        for pattern in patterns:
            try:
                result = subprocess.run(
                    ['grep', '-rn', '-E', pattern, 'src/', '--include=*.py'],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0 and result.stdout:
                    # Filter out comments and TODO items
                    lines = [
                        line for line in result.stdout.split('\n')
                        if line and '#' not in line and 'TODO' not in line
                    ]
                    found_secrets.extend(lines)
            except:
                pass

        if found_secrets:
            self._add_result(
                'Hardcoded Secrets',
                'fail',
                f"Found {len(found_secrets)} potential hardcoded secrets",
                severity='critical'
            )
        else:
            self._add_result(
                'Hardcoded Secrets',
                'pass',
                "No hardcoded secrets detected"
            )

    def _check_input_validation(self):
        """Check input validation is implemented."""
        validation_file = self.project_root / 'src' / 'utils' / 'validation.py'

        if not validation_file.exists():
            self._add_result(
                'Input Validation',
                'fail',
                "Input validation module not found",
                severity='high'
            )
            return

        # Check for validation functions
        content = validation_file.read_text()
        required_validators = [
            'validate_model_name',
            'validate_prompt',
            'sanitize_path'
        ]

        missing = [v for v in required_validators if v not in content]

        if missing:
            self._add_result(
                'Input Validation',
                'fail',
                f"Missing validators: {', '.join(missing)}",
                severity='high'
            )
        else:
            self._add_result(
                'Input Validation',
                'pass',
                "Input validation implemented"
            )

    def _check_dependency_vulnerabilities(self):
        """Check for dependency vulnerabilities."""
        try:
            result = subprocess.run(
                ['pip', 'install', 'safety'],
                capture_output=True
            )

            result = subprocess.run(
                ['safety', 'check', '--json'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                if not data:
                    self._add_result(
                        'Dependency Vulnerabilities',
                        'pass',
                        "No known vulnerabilities found"
                    )
                else:
                    self._add_result(
                        'Dependency Vulnerabilities',
                        'fail',
                        f"Found {len(data)} vulnerable dependencies",
                        severity='high'
                    )
            else:
                self._add_result(
                    'Dependency Vulnerabilities',
                    'warn',
                    "Could not check dependencies"
                )
        except Exception as e:
            self._add_result(
                'Dependency Vulnerabilities',
                'warn',
                f"Check failed: {e}"
            )

    def _check_connection_pooling(self):
        """Check connection pooling is configured."""
        ollama_client = self.project_root / 'src' / 'services' / 'ollama_client.py'

        if not ollama_client.exists():
            self._add_result(
                'Connection Pooling',
                'fail',
                "Ollama client not found",
                severity='high'
            )
            return

        content = ollama_client.read_text()

        if 'TCPConnector' in content and 'limit=' in content:
            self._add_result(
                'Connection Pooling',
                'pass',
                "Connection pooling configured"
            )
        else:
            self._add_result(
                'Connection Pooling',
                'fail',
                "Connection pooling not configured",
                severity='medium'
            )

    def _check_memory_limits(self):
        """Check memory limits are configured."""
        # Check for bounded collections
        memory_limit_patterns = [
            'max_messages',
            'message_limit',
            'MAX_MEMORY'
        ]

        found = False
        for pattern in memory_limit_patterns:
            result = subprocess.run(
                ['grep', '-rn', pattern, 'src/', '--include=*.py'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and result.stdout:
                found = True
                break

        if found:
            self._add_result(
                'Memory Limits',
                'pass',
                "Memory limits configured"
            )
        else:
            self._add_result(
                'Memory Limits',
                'fail',
                "No memory limits found",
                severity='high'
            )

    def _check_timeout_configuration(self):
        """Check timeout configuration."""
        config_patterns = ['timeout=', 'ClientTimeout']

        result = subprocess.run(
            ['grep', '-rn', 'timeout', 'src/', '--include=*.py'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and result.stdout:
            self._add_result(
                'Timeout Configuration',
                'pass',
                "Timeouts configured"
            )
        else:
            self._add_result(
                'Timeout Configuration',
                'warn',
                "No timeout configuration found"
            )

    def _check_error_handling(self):
        """Check error handling is comprehensive."""
        # Look for try/except blocks
        result = subprocess.run(
            ['grep', '-c', 'try:', 'src/**/*.py'],
            capture_output=True,
            text=True,
            shell=True
        )

        # Look for naked except blocks (anti-pattern)
        naked_except = subprocess.run(
            ['grep', '-rn', 'except:$', 'src/', '--include=*.py'],
            capture_output=True,
            text=True
        )

        if naked_except.returncode == 0 and naked_except.stdout:
            self._add_result(
                'Error Handling',
                'fail',
                "Found naked except: blocks (anti-pattern)",
                severity='medium'
            )
        else:
            self._add_result(
                'Error Handling',
                'pass',
                "Error handling looks good"
            )

    def _check_logging_configured(self):
        """Check logging is configured."""
        logger_file = self.project_root / 'src' / 'services' / 'logger.py'

        if not logger_file.exists():
            self._add_result(
                'Logging',
                'fail',
                "Logger module not found",
                severity='high'
            )
            return

        content = logger_file.read_text()

        if 'logging' in content and 'logger' in content.lower():
            self._add_result(
                'Logging',
                'pass',
                "Logging configured"
            )
        else:
            self._add_result(
                'Logging',
                'fail',
                "Logging not properly configured",
                severity='medium'
            )

    def _check_health_checks(self):
        """Check health check endpoints exist."""
        # Look for health check implementation
        result = subprocess.run(
            ['grep', '-rn', 'health_check\|healthz', 'src/', '--include=*.py'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and result.stdout:
            self._add_result(
                'Health Checks',
                'pass',
                "Health check endpoints found"
            )
        else:
            self._add_result(
                'Health Checks',
                'warn',
                "No health check endpoints found"
            )

    def _check_test_coverage(self):
        """Check test coverage meets threshold."""
        try:
            result = subprocess.run(
                ['pytest', '--cov=src', '--cov-report=json', '--cov-report=term'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            coverage_file = self.project_root / 'coverage.json'
            if coverage_file.exists():
                with open(coverage_file) as f:
                    data = json.load(f)

                coverage = data['totals']['percent_covered']

                if coverage >= 80:
                    self._add_result(
                        'Test Coverage',
                        'pass',
                        f"Coverage {coverage:.1f}% meets threshold (>=80%)"
                    )
                elif coverage >= 60:
                    self._add_result(
                        'Test Coverage',
                        'warn',
                        f"Coverage {coverage:.1f}% below target (80%)",
                        severity='medium'
                    )
                else:
                    self._add_result(
                        'Test Coverage',
                        'fail',
                        f"Coverage {coverage:.1f}% critically low",
                        severity='high'
                    )
            else:
                self._add_result(
                    'Test Coverage',
                    'warn',
                    "Could not determine coverage"
                )
        except Exception as e:
            self._add_result(
                'Test Coverage',
                'warn',
                f"Coverage check failed: {e}"
            )

    def _check_linting(self):
        """Check code passes linting."""
        try:
            result = subprocess.run(
                ['ruff', 'check', 'src/'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self._add_result(
                    'Linting',
                    'pass',
                    "Code passes linting checks"
                )
            else:
                error_count = len(result.stdout.strip().split('\n'))
                self._add_result(
                    'Linting',
                    'warn',
                    f"Found {error_count} linting issues"
                )
        except FileNotFoundError:
            self._add_result(
                'Linting',
                'warn',
                "Ruff not installed, skipping linting check"
            )

    def _check_type_hints(self):
        """Check type hints coverage."""
        # Look for type hints in function signatures
        result = subprocess.run(
            ['grep', '-rn', 'def.*->', 'src/', '--include=*.py'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and result.stdout:
            count = len(result.stdout.strip().split('\n'))
            self._add_result(
                'Type Hints',
                'pass' if count > 50 else 'warn',
                f"Found {count} functions with type hints"
            )
        else:
            self._add_result(
                'Type Hints',
                'warn',
                "Few or no type hints found"
            )

    def _check_environment_variables(self):
        """Check environment variable configuration."""
        env_example = self.project_root / '.env.example'

        if env_example.exists():
            self._add_result(
                'Environment Variables',
                'pass',
                ".env.example file exists"
            )
        else:
            self._add_result(
                'Environment Variables',
                'warn',
                ".env.example file missing"
            )

    def _check_production_config(self):
        """Check production configuration exists."""
        config_files = [
            '.streamlit/config.toml',
            'pyproject.toml',
            'requirements.txt'
        ]

        missing = []
        for config_file in config_files:
            if not (self.project_root / config_file).exists():
                missing.append(config_file)

        if missing:
            self._add_result(
                'Production Configuration',
                'warn',
                f"Missing config files: {', '.join(missing)}"
            )
        else:
            self._add_result(
                'Production Configuration',
                'pass',
                "All configuration files present"
            )

    def _check_readme_exists(self):
        """Check README documentation exists."""
        readme = self.project_root / 'README.md'

        if readme.exists() and readme.stat().st_size > 1000:
            self._add_result(
                'README Documentation',
                'pass',
                "README.md exists with content"
            )
        else:
            self._add_result(
                'README Documentation',
                'fail',
                "README.md missing or too short",
                severity='low'
            )

    def _check_deployment_docs(self):
        """Check deployment documentation exists."""
        deployment_docs = [
            'DEPLOYMENT.md',
            'docs/DEPLOYMENT.md',
            'docs/deployment.md'
        ]

        found = any((self.project_root / doc).exists() for doc in deployment_docs)

        if found:
            self._add_result(
                'Deployment Documentation',
                'pass',
                "Deployment documentation exists"
            )
        else:
            self._add_result(
                'Deployment Documentation',
                'warn',
                "No deployment documentation found"
            )

    def _print_report(self):
        """Print validation report."""
        print("\n" + "="*60)
        print("📊 PRODUCTION READINESS REPORT")
        print("="*60)
        print(f"\n✅ Passed:  {self.results['passed']}")
        print(f"⚠️  Warnings: {self.results['warnings']}")
        print(f"❌ Failed:  {self.results['failed']}")

        # Group by severity
        critical_failures = [
            c for c in self.results['checks']
            if c['status'] == 'fail' and c['severity'] == 'critical'
        ]

        if critical_failures:
            print("\n🚨 CRITICAL ISSUES:")
            for check in critical_failures:
                print(f"   - {check['name']}: {check['message']}")

        # Save report
        report_file = self.project_root / 'production_readiness_report.json'
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📄 Full report saved to: {report_file}")

        if self.results['failed'] == 0:
            print("\n✅ Application is PRODUCTION READY!")
            return True
        else:
            print(f"\n❌ Application is NOT PRODUCTION READY ({self.results['failed']} failures)")
            return False


def main():
    """Run production validation."""
    project_root = Path.cwd()
    validator = ProductionValidator(project_root)

    success = validator.run_all_checks()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
```

### Step 2: Create Pre-Deployment Checklist (30-45 min)

**Create Checklist Document**:
```markdown
# Production Deployment Checklist

## Security ✅
- [ ] All inputs validated and sanitized
- [ ] HTML sanitization implemented (no XSS vulnerabilities)
- [ ] Authentication/authorization implemented
- [ ] No hardcoded secrets or credentials
- [ ] Dependency vulnerabilities resolved
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Audit logging active

## Performance ⚡
- [ ] Connection pooling configured
- [ ] Memory limits implemented (bounded collections)
- [ ] Timeout configuration set
- [ ] Database queries optimized
- [ ] Caching implemented where appropriate
- [ ] Resource cleanup verified (no leaks)
- [ ] Load testing completed
- [ ] Performance metrics meet targets

## Reliability 🛡️
- [ ] Comprehensive error handling
- [ ] Logging configured and working
- [ ] Health check endpoints implemented
- [ ] Graceful degradation for failures
- [ ] Retry logic for transient failures
- [ ] Circuit breakers for external services
- [ ] Backup and recovery procedures documented

## Code Quality 📐
- [ ] Test coverage >= 80%
- [ ] All tests passing
- [ ] Code linting passes
- [ ] Type hints throughout
- [ ] No TODO/FIXME in critical paths
- [ ] Code review completed
- [ ] Documentation up-to-date

## Configuration 🔧
- [ ] Environment variables documented (.env.example)
- [ ] Production configuration separate from development
- [ ] Secrets management configured
- [ ] Feature flags implemented (if needed)
- [ ] Configuration validation on startup

## Infrastructure 🏗️
- [ ] CI/CD pipeline configured
- [ ] Deployment automation tested
- [ ] Monitoring and alerting configured
- [ ] Log aggregation setup
- [ ] Backup procedures tested
- [ ] Rollback procedure documented
- [ ] Resource limits configured (CPU, memory)

## Documentation 📚
- [ ] README.md comprehensive
- [ ] Deployment guide complete
- [ ] API documentation generated
- [ ] Architecture diagrams updated
- [ ] Runbook for operations team
- [ ] Troubleshooting guide created
- [ ] Change log maintained

## Compliance 📋
- [ ] Privacy policy reviewed
- [ ] Terms of service updated
- [ ] GDPR compliance verified (if applicable)
- [ ] Data retention policies documented
- [ ] Accessibility standards met
- [ ] License compliance verified

## Final Validation ✓
- [ ] Staging environment tested
- [ ] Production smoke tests pass
- [ ] Performance benchmarks met
- [ ] Security scan passes
- [ ] Stakeholder approval obtained
- [ ] Deployment window scheduled
- [ ] Rollback plan ready
```

---

## Best Practices

### Validation Automation
1. Run validation in CI pipeline
2. Block deployment if critical checks fail
3. Generate reports for stakeholders
4. Track validation history over time

### Environment Parity
1. Staging should match production
2. Test with production-like data volumes
3. Validate with production configuration
4. Use same deployment process

### Progressive Rollout
1. Deploy to staging first
2. Run smoke tests before full rollout
3. Monitor metrics during deployment
4. Have rollback plan ready

### Documentation
1. Keep deployment docs updated
2. Document all validation failures
3. Create runbooks for operators
4. Maintain change logs

---

## Success Criteria

- [ ] All critical checks pass
- [ ] Test coverage >= 80%
- [ ] No security vulnerabilities
- [ ] Performance metrics meet targets
- [ ] Documentation complete
- [ ] Stakeholder approval obtained
- [ ] Validation report generated
- [ ] Production deployment approved

---

## Tools Available
- Read: Read configuration files
- Write: Create validation scripts
- Bash: Run validation commands
- Grep: Search for anti-patterns
- Glob: Find all source files

---

## Validation Commands

```bash
# Run full production validation
python scripts/validate_production.py

# Check test coverage
pytest --cov=src --cov-report=term --cov-fail-under=80

# Security scan
bandit -r src/ -f json -o security_report.json

# Dependency audit
pip install safety
safety check --json

# Lint code
ruff check src/

# Type checking
mypy src/

# Run all tests
pytest -v

# Load testing
locust -f tests/load/locustfile.py --headless -u 100 -r 10

# Generate validation report
python scripts/validate_production.py > production_report.txt
```
