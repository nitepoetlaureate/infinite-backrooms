#!/bin/bash
# Pre-deployment validation script
# Run this before deploying to catch common issues

set -e

echo "=========================================="
echo "Infinite AI Backrooms - Deployment Checks"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILURES=0

# Function to print check result
check_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC} $2"
    else
        echo -e "${RED}✗ FAIL${NC} $2"
        FAILURES=$((FAILURES + 1))
    fi
}

# Check 1: Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | sed 's/Python \([0-9]*\.[0-9]*\).*/\1/' | head -1)
if [ "$(printf '%s\n' "3.12" "$python_version" | sort -V | head -n1)" = "3.12" ]; then
    check_result 0 "Python version ($python_version) is >= 3.12"
else
    check_result 1 "Python version ($python_version) is < 3.12"
fi

# Check 2: Required files exist
echo ""
echo "Checking required files..."
required_files=(
    "streamlit_backroom.py"
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

# Check 3: Dependencies installed
echo ""
echo "Checking Python dependencies..."
if pip3 show streamlit > /dev/null 2>&1; then
    check_result 0 "Streamlit is installed"
else
    check_result 1 "Streamlit is not installed"
fi

if pip3 show aiohttp > /dev/null 2>&1; then
    check_result 0 "aiohttp is installed"
else
    check_result 1 "aiohttp is not installed"
fi

# Check 4: Syntax check main file
echo ""
echo "Checking Python syntax..."
if python3 -m py_compile streamlit_backroom.py 2>/dev/null; then
    check_result 0 "streamlit_backroom.py syntax is valid"
else
    check_result 1 "streamlit_backroom.py has syntax errors"
fi

# Check 5: Environment variables
echo ""
echo "Checking environment configuration..."
if [ -f ".env.production" ]; then
    check_result 0 ".env.production file exists"

    if grep -q "OLLAMA_URL=" .env.production; then
        ollama_url=$(grep "OLLAMA_URL=" .env.production | cut -d '=' -f2)
        if [[ $ollama_url == *"localhost"* || $ollama_url == *"your-ollama"* ]]; then
            check_result 1 "OLLAMA_URL still points to localhost or placeholder"
            echo -e "  ${YELLOW}⚠ Update OLLAMA_URL in .env.production${NC}"
        else
            check_result 0 "OLLAMA_URL is configured"
        fi
    else
        check_result 1 "OLLAMA_URL not set in .env.production"
    fi
else
    check_result 1 ".env.production file missing"
fi

# Check 6: Docker files (if using Docker)
if [ -f "Dockerfile" ]; then
    echo ""
    echo "Checking Docker configuration..."
    check_result 0 "Dockerfile exists"

    if [ -f "docker-compose.yml" ]; then
        check_result 0 "docker-compose.yml exists"
    fi

    if [ -f ".dockerignore" ]; then
        check_result 0 ".dockerignore exists"
    else
        check_result 1 ".dockerignore missing (recommended)"
    fi
fi

# Check 7: Git repository
echo ""
echo "Checking git configuration..."
if [ -d ".git" ]; then
    check_result 0 "Git repository initialized"

    # Check for uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "  ${YELLOW}⚠ You have uncommitted changes${NC}"
    fi

    # Check remote
    if git remote get-url origin > /dev/null 2>&1; then
        check_result 0 "Git remote configured"
    else
        check_result 1 "Git remote not configured"
    fi
else
    check_result 1 "Not a git repository"
fi

# Check 8: Security checks
echo ""
echo "Checking security configuration..."

# Check if .env files are gitignored
if grep -q "^\.env$" .gitignore 2>/dev/null; then
    check_result 0 ".env files are gitignored"
else
    check_result 1 ".env should be in .gitignore"
fi

# Check for sensitive data in config
if grep -rq "password\|secret\|key" .streamlit/*.toml 2>/dev/null | grep -v "enableXsrf"; then
    check_result 1 "Possible sensitive data in .streamlit/config.toml"
else
    check_result 0 "No sensitive data in config files"
fi

# Check 9: Port configuration
echo ""
echo "Checking port configuration..."
if grep -q "PORT" Procfile; then
    check_result 0 "Procfile uses \$PORT variable"
else
    check_result 1 "Procfile should use \$PORT variable"
fi

# Check 10: Static files directory
echo ""
echo "Checking static assets..."
if [ -d "static/css" ]; then
    check_result 0 "static/css directory exists"
    css_count=$(find static/css -name "*.css" | wc -l)
    echo "  Found $css_count CSS file(s)"
else
    check_result 1 "static/css directory missing"
fi

# Summary
echo ""
echo "=========================================="
echo "Deployment Check Summary"
echo "=========================================="

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Ready to deploy! Next steps:"
    echo "1. Review DEPLOYMENT.md for deployment instructions"
    echo "2. Configure OLLAMA_URL for your environment"
    echo "3. Push to your deployment platform"
    exit 0
else
    echo -e "${RED}✗ $FAILURES check(s) failed${NC}"
    echo ""
    echo "Please fix the issues above before deploying."
    echo "See DEPLOYMENT.md for detailed guidance."
    exit 1
fi
