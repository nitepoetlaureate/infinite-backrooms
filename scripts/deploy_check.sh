#!/bin/bash
# Pre-deployment validation script for CI/CD pipeline
# Run this before deploying to catch common issues

set -e

# Parse command line arguments
ENVIRONMENT="staging"
VERBOSE=false
SKIP_LINT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --skip-lint)
            SKIP_LINT=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --environment ENV    Environment type (staging|production) [default: staging]"
            echo "  --verbose            Show detailed output"
            echo "  --skip-lint          Skip linting checks"
            echo "  --help, -h           Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "Infinite AI Backrooms - Deployment Checks"
echo "Environment: $ENVIRONMENT"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track failures
FAILURES=0
WARNINGS=0

# Function to print check result
check_result() {
    local exit_code=$1
    local message=$2
    local is_warning=${3:-false}

    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC} $message"
        if [ "$VERBOSE" = true ]; then
            echo "  Details: Check completed successfully"
        fi
    else
        if [ "$is_warning" = true ]; then
            echo -e "${YELLOW}⚠ WARN${NC} $message"
            WARNINGS=$((WARNINGS + 1))
            if [ "$VERBOSE" = true ]; then
                echo "  Details: Warning condition detected"
            fi
        else
            echo -e "${RED}✗ FAIL${NC} $message"
            FAILURES=$((FAILURES + 1))
            if [ "$VERBOSE" = true ]; then
                echo "  Details: Critical issue found"
            fi
        fi
    fi
}

# Function to check environment variable
check_env_var() {
    local var_name=$1
    local required=${2:-false}
    local var_value="${!var_name}"

    if [ -z "$var_value" ]; then
        if [ "$required" = true ]; then
            check_result 1 "Required environment variable $var_name is not set"
            return 1
        else
            check_result 1 "Optional environment variable $var_name is not set" true
            return 1
        fi
    else
        check_result 0 "Environment variable $var_name is set"
        return 0
    fi
}

# Function to run command with timeout
run_with_timeout() {
    local timeout_seconds=$1
    local command="$2"

    if command -v timeout >/dev/null 2>&1; then
        timeout "$timeout_seconds" bash -c "$command"
    elif command -v gtimeout >/dev/null 2>&1; then
        gtimeout "$timeout_seconds" bash -c "$command"
    else
        eval "$command"
    fi
}

# Environment-specific checks
echo "Running environment-specific checks for $ENVIRONMENT..."

if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "${BLUE}🔒 Production Environment Checks${NC}"

    # Check for production-specific files
    check_result $([ -f ".env.production" ] && echo 0 || echo 1) ".env.production file exists"

    # Check production environment variables
    check_env_var "DATABASE_URL" true
    check_env_var "REDIS_URL" false
    check_env_var "OLLAMA_BASE_URL" true

    # Check for security headers and settings
    if [ -f ".streamlit/config.toml" ]; then
        if grep -q "enableXsrfProtection = true" .streamlit/config.toml; then
            check_result 0 "XSRF protection is enabled"
        else
            check_result 1 "XSRF protection should be enabled in production"
        fi

        if grep -q "enableCORS = true" .streamlit/config.toml; then
            check_result 0 "CORS is enabled"
        else
            check_result 1 "CORS should be enabled in production"
        fi
    fi
else
    echo -e "${BLUE}🧪 Staging Environment Checks${NC}"
    check_result $([ -f ".env.staging" ] || [ -f ".env" ] && echo 0 || echo 1) "Environment file exists" true
fi

# Check 1: Python version
echo ""
echo "Checking Python version..."
if command -v python3 >/dev/null 2>&1; then
    python_version=$(python3 --version 2>&1 | sed 's/Python \([0-9]*\.[0-9]*\).*/\1/' | head -1)
    if [ "$(printf '%s\n' "3.12" "$python_version" | sort -V | head -n1)" = "3.12" ]; then
        check_result 0 "Python version ($python_version) is >= 3.12"
    else
        check_result 1 "Python version ($python_version) is < 3.12"
    fi
else
    check_result 1 "Python3 is not available"
fi

# Check 2: Required files exist
echo ""
echo "Checking required files..."
required_files=(
    "streamlit_backroom.py"
    "pyproject.toml"
    "requirements.txt"
    "runtime.txt"
    "Procfile"
    ".streamlit/config.toml"
    "static/css/system.css"
    "src/services/ollama_client.py"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        check_result 0 "File exists: $file"
    else
        check_result 1 "File missing: $file"
    fi
done

# Check 3: Dependencies available
echo ""
echo "Checking Python dependencies..."
if command -v pip >/dev/null 2>&1 || command -v uv >/dev/null 2>&1; then
    check_result 0 "Package manager available (pip/uv)"

    # Check if we can install dependencies
    if [ -f "pyproject.toml" ]; then
        if run_with_timeout 60 "python3 -m pip check" >/dev/null 2>&1; then
            check_result 0 "Dependencies are consistent"
        else
            check_result 1 "Dependency conflicts detected" true
        fi
    fi
else
    check_result 1 "No package manager available"
fi

# Check 4: Syntax validation
echo ""
echo "Checking Python syntax..."
syntax_errors=0

# Main application
if python3 -m py_compile streamlit_backroom.py 2>/dev/null; then
    check_result 0 "streamlit_backroom.py syntax is valid"
else
    check_result 1 "streamlit_backroom.py has syntax errors"
    syntax_errors=$((syntax_errors + 1))
fi

# Source files
for py_file in src/**/*.py; do
    if [ -f "$py_file" ]; then
        if python3 -m py_compile "$py_file" 2>/dev/null; then
            if [ "$VERBOSE" = true ]; then
                echo "  ✓ $py_file"
            fi
        else
            check_result 1 "Syntax error in $py_file"
            syntax_errors=$((syntax_errors + 1))
        fi
    fi
done

# Check 5: Linting (optional)
if [ "$SKIP_LINT" = false ]; then
    echo ""
    echo "Running linting checks..."

    # Check for ruff if configured in pyproject.toml
    if command -v ruff >/dev/null 2>&1 && grep -q "\[tool.ruff\]" pyproject.toml; then
        if ruff check . --quiet; then
            check_result 0 "Code passes ruff linting"
        else
            check_result 1 "Linting issues found" true
        fi
    else
        check_result 0 "Linting skipped (ruff not available or not configured)" true
    fi

    # Check for black
    if command -v black >/dev/null 2>&1 && grep -q "\[tool.black\]" pyproject.toml; then
        if black --check . --quiet; then
            check_result 0 "Code passes black formatting"
        else
            check_result 1 "Formatting issues found" true
        fi
    else
        check_result 0 "Formatting check skipped (black not available or not configured)" true
    fi
fi

# Check 6: Security configuration
echo ""
echo "Checking security configuration..."

# Check if .env files are gitignored
if [ -f ".gitignore" ]; then
    if grep -q "^\.env" .gitignore; then
        check_result 0 ".env files are gitignored"
    else
        check_result 1 ".env files should be in .gitignore"
    fi
else
    check_result 1 ".gitignore file missing"
fi

# Check for secrets in config
if [ -f ".streamlit/config.toml" ]; then
    if grep -q "password\|secret\|key\|token" .streamlit/config.toml | grep -v "enableXsrf\|cookieSecret" >/dev/null 2>&1; then
        check_result 1 "Possible hardcoded secrets in config.toml"
    else
        check_result 0 "No hardcoded secrets in config.toml"
    fi
fi

# Check 7: Git repository status
echo ""
echo "Checking git repository..."
if [ -d ".git" ]; then
    check_result 0 "Git repository initialized"

    # Check for uncommitted changes in CI
    if [ "$CI" = "true" ] && [ -n "$(git status --porcelain)" ]; then
        check_result 1 "Uncommitted changes detected in CI environment"
    elif [ -n "$(git status --porcelain)" ]; then
        check_result 0 "Uncommitted changes detected" true
    fi

    # Check remote
    if git remote get-url origin >/dev/null 2>&1; then
        check_result 0 "Git remote configured"
    else
        check_result 1 "Git remote not configured"
    fi
else
    check_result 1 "Not a git repository"
fi

# Check 8: Deployment configuration
echo ""
echo "Checking deployment configuration..."

if [ -f "railway.toml" ]; then
    check_result 0 "Railway configuration exists"
    if grep -q "\$PORT" railway.toml; then
        check_result 0 "Railway config uses \$PORT variable"
    else
        check_result 1 "Railway config should use \$PORT variable"
    fi
fi

if [ -f "render.yaml" ]; then
    check_result 0 "Render configuration exists"
fi

if [ -f "Dockerfile" ]; then
    check_result 0 "Dockerfile exists"
    if [ -f ".dockerignore" ]; then
        check_result 0 ".dockerignore exists"
    else
        check_result 1 ".dockerignore missing (recommended)"
    fi
fi

# Check 9: CI/CD pipeline files
echo ""
echo "Checking CI/CD configuration..."
if [ -f ".github/workflows/ci-cd.yml" ]; then
    check_result 0 "CI/CD pipeline exists"
else
    check_result 1 "CI/CD pipeline missing"
fi

if [ -f ".github/dependabot.yml" ]; then
    check_result 0 "Dependabot configuration exists"
else
    check_result 1 "Dependabot configuration missing" true
fi

# Environment-specific summary
echo ""
echo "=========================================="
echo "Deployment Check Summary ($ENVIRONMENT)"
echo "=========================================="

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARNINGS warning(s) detected - review above${NC}"
    fi
    echo ""
    echo "Ready to deploy to $ENVIRONMENT!"
    if [ "$ENVIRONMENT" = "production" ]; then
        echo "Production deployment checklist:"
        echo "✓ Security settings validated"
        echo "✓ Environment variables configured"
        echo "✓ Dependencies verified"
        echo "✓ CI/CD pipeline ready"
    else
        echo "Staging deployment checklist:"
        echo "✓ Basic configuration validated"
        echo "✓ Dependencies available"
        echo "✓ Ready for testing"
    fi

    # Output for CI systems
    if [ "$CI" = "true" ]; then
        echo "##teamcity[buildStatus status='SUCCESS' text='All deployment checks passed']"
        echo "::set-output name=deployment_ready::true"
        echo "::set-output name=failures::$FAILURES"
        echo "::set-output name=warnings::$WARNINGS"
    fi

    exit 0
else
    echo -e "${RED}✗ $FAILURES critical check(s) failed${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARNINGS warning(s) also detected${NC}"
    fi
    echo ""
    echo "Please fix the critical issues above before deploying."
    echo "See docs/GITHUB_SECRETS.md for deployment guidance."

    # Output for CI systems
    if [ "$CI" = "true" ]; then
        echo "##teamcity[buildStatus status='FAILURE' text='$FAILURES deployment checks failed']"
        echo "::set-output name=deployment_ready::false"
        echo "::set-output name=failures::$FAILURES"
        echo "::set-output name=warnings::$WARNINGS"
    fi

    exit 1
fi
