# git-flow-deployment-orchestrator

**Purpose**: Orchestrate complete Git Flow deployment workflow from feature development through production release

**Use When**: Managing production deployments, coordinating releases, or implementing Git Flow best practices

---

## Domain Knowledge

### Git Flow Model
- **Main Branch**: Production-ready code
- **Develop Branch**: Integration branch for features
- **Feature Branches**: Individual feature development
- **Release Branches**: Release preparation
- **Hotfix Branches**: Emergency production fixes

### Branch Naming Conventions
- Feature: `feature/description` or `feature/TICKET-123-description`
- Release: `release/vX.Y.Z`
- Hotfix: `hotfix/vX.Y.Z-description`

### Deployment Pipeline Stages
1. **Development**: Feature branch work
2. **Integration**: Merge to develop, run integration tests
3. **Release Preparation**: Create release branch, finalize
4. **Staging**: Deploy to staging environment
5. **Production**: Deploy to production

---

## Workflow

### Step 1: Feature Development Workflow (Varies)

**Pattern: Feature Branch Management**:
```bash
#!/bin/bash
# Feature development workflow

# Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/PROJ-123-awesome-feature

# Make changes and commit
git add .
git commit -m "feat: Add awesome feature

- Implement core functionality
- Add comprehensive tests
- Update documentation

Closes PROJ-123"

# Keep feature branch updated with develop
git fetch origin
git rebase origin/develop

# Push feature branch
git push origin feature/PROJ-123-awesome-feature

# Create pull request
gh pr create --base develop \
  --title "feat: Add awesome feature" \
  --body "$(cat <<EOF
## Summary
Implements awesome feature as described in PROJ-123.

## Changes
- Core functionality implementation
- Comprehensive test suite
- Updated documentation

## Testing
- Unit tests: ✅ Passing
- Integration tests: ✅ Passing
- Manual testing: ✅ Complete

## Checklist
- [x] Tests added and passing
- [x] Documentation updated
- [x] No breaking changes
- [x] Changelog updated
EOF
)"
```

### Step 2: Release Preparation (60-90 min)

**Pattern: Release Branch Creation**:
```bash
#!/bin/bash
# scripts/prepare_release.sh

set -e

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 1.2.0"
    exit 1
fi

echo "🚀 Preparing release v$VERSION"

# Ensure we're on develop and up to date
git checkout develop
git pull origin develop

# Create release branch
git checkout -b release/v$VERSION

echo "📝 Updating version numbers..."

# Update version in pyproject.toml
sed -i '' "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml

# Update version in __init__.py
cat > src/__init__.py <<EOF
"""Infinite Backrooms application."""
__version__ = "$VERSION"
EOF

# Update CHANGELOG.md
DATE=$(date +%Y-%m-%d)
cat > CHANGELOG_UPDATE.md <<EOF
## [$VERSION] - $DATE

### Added
- [List new features]

### Changed
- [List changes to existing functionality]

### Fixed
- [List bug fixes]

### Deprecated
- [List soon-to-be removed features]

### Removed
- [List removed features]

### Security
- [List security improvements]

EOF

# Prepend to existing CHANGELOG.md
cat CHANGELOG_UPDATE.md CHANGELOG.md > CHANGELOG_NEW.md
mv CHANGELOG_NEW.md CHANGELOG.md
rm CHANGELOG_UPDATE.md

# Commit version bump
git add pyproject.toml src/__init__.py CHANGELOG.md
git commit -m "chore: Bump version to v$VERSION

Prepare release v$VERSION with updated version numbers and changelog."

# Push release branch
git push origin release/v$VERSION

echo "✅ Release branch release/v$VERSION created"
echo ""
echo "Next steps:"
echo "1. Review and finalize CHANGELOG.md"
echo "2. Run full test suite: pytest -v"
echo "3. Run production validation: python scripts/validate_production.py"
echo "4. Deploy to staging for final validation"
echo "5. Run: ./scripts/finalize_release.sh $VERSION"
```

### Step 3: Production Validation (45-60 min)

**Pattern: Pre-Release Validation**:
```bash
#!/bin/bash
# scripts/validate_release.sh

set -e

VERSION=$1

echo "🔍 Validating release v$VERSION"

# Ensure we're on release branch
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" != "release/v$VERSION" ]]; then
    echo "❌ Must be on release/v$VERSION branch"
    exit 1
fi

# Run comprehensive validation
echo "📋 Running production readiness validation..."
python scripts/validate_production.py

if [ $? -ne 0 ]; then
    echo "❌ Production validation failed"
    exit 1
fi

# Run full test suite
echo "🧪 Running full test suite..."
pytest -v --cov=src --cov-report=term --cov-fail-under=80

if [ $? -ne 0 ]; then
    echo "❌ Tests failed or coverage insufficient"
    exit 1
fi

# Security scan
echo "🔒 Running security scan..."
bandit -r src/ -f json -o security_report.json

# Check for high/critical issues
CRITICAL=$(jq '.results | map(select(.issue_severity == "HIGH" or .issue_severity == "CRITICAL")) | length' security_report.json)

if [ "$CRITICAL" -gt 0 ]; then
    echo "❌ Found $CRITICAL high/critical security issues"
    exit 1
fi

# Dependency audit
echo "📦 Auditing dependencies..."
pip install safety
safety check --json

# Lint check
echo "🎨 Running linting..."
ruff check src/

# Build check
echo "🏗️  Testing build..."
python -m build

echo "✅ Release validation passed!"
echo ""
echo "Release v$VERSION is ready for deployment to staging"
```

### Step 4: Staging Deployment (30-45 min)

**Pattern: Staging Deployment**:
```bash
#!/bin/bash
# scripts/deploy_staging.sh

set -e

VERSION=$1
STAGING_URL="https://staging.example.com"

echo "🚀 Deploying v$VERSION to staging..."

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t infinite-backrooms:v$VERSION .
docker tag infinite-backrooms:v$VERSION infinite-backrooms:staging

# Push to container registry
echo "📤 Pushing to registry..."
docker push infinite-backrooms:staging

# Deploy to staging (example using Railway)
echo "🚂 Deploying to Railway staging..."
railway up --service staging --environment staging

# Wait for deployment
echo "⏳ Waiting for deployment to complete..."
sleep 30

# Health check
echo "🏥 Running health checks..."
for i in {1..10}; do
    if curl -f "$STAGING_URL/healthz" > /dev/null 2>&1; then
        echo "✅ Staging is healthy!"
        break
    fi

    if [ $i -eq 10 ]; then
        echo "❌ Staging health check failed"
        exit 1
    fi

    echo "Waiting... ($i/10)"
    sleep 10
done

# Run smoke tests
echo "💨 Running smoke tests..."
pytest tests/smoke/ --base-url="$STAGING_URL" -v

if [ $? -ne 0 ]; then
    echo "❌ Smoke tests failed"
    exit 1
fi

echo "✅ Successfully deployed v$VERSION to staging!"
echo ""
echo "Staging URL: $STAGING_URL"
echo "Run comprehensive E2E tests before production deployment"
```

### Step 5: Production Release (45-60 min)

**Pattern: Production Release Finalization**:
```bash
#!/bin/bash
# scripts/finalize_release.sh

set -e

VERSION=$1

echo "🎉 Finalizing release v$VERSION"

# Ensure we're on release branch
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" != "release/v$VERSION" ]]; then
    echo "❌ Must be on release/v$VERSION branch"
    exit 1
fi

# Merge to main
echo "🔀 Merging release to main..."
git checkout main
git pull origin main
git merge --no-ff release/v$VERSION -m "Release v$VERSION"

# Tag the release
echo "🏷️  Creating release tag..."
git tag -a "v$VERSION" -m "Release version $VERSION

$(cat CHANGELOG.md | sed -n '/^## \['$VERSION'\]/,/^## \[/p' | head -n -1)
"

# Push main and tag
git push origin main
git push origin "v$VERSION"

# Merge back to develop
echo "🔀 Merging back to develop..."
git checkout develop
git pull origin develop
git merge --no-ff release/v$VERSION -m "Merge release v$VERSION back to develop"
git push origin develop

# Delete release branch
echo "🗑️  Cleaning up release branch..."
git branch -d release/v$VERSION
git push origin --delete release/v$VERSION

# Create GitHub release
echo "📦 Creating GitHub release..."
gh release create "v$VERSION" \
  --title "Release v$VERSION" \
  --notes "$(cat CHANGELOG.md | sed -n '/^## \['$VERSION'\]/,/^## \[/p' | head -n -1)"

echo "✅ Release v$VERSION finalized!"
echo ""
echo "Next step: Deploy to production"
echo "Run: ./scripts/deploy_production.sh $VERSION"
```

### Step 6: Production Deployment (30-45 min)

**Pattern: Blue-Green Production Deployment**:
```bash
#!/bin/bash
# scripts/deploy_production.sh

set -e

VERSION=$1
PRODUCTION_URL="https://app.example.com"

echo "🚀 Deploying v$VERSION to production..."

# Confirm deployment
read -p "Deploy v$VERSION to PRODUCTION? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled"
    exit 0
fi

# Verify we're on main branch with correct tag
git checkout main
git pull origin main

CURRENT_VERSION=$(git describe --tags)
if [ "$CURRENT_VERSION" != "v$VERSION" ]; then
    echo "❌ Version mismatch: current=$CURRENT_VERSION, expected=v$VERSION"
    exit 1
fi

# Create backup tag
BACKUP_TAG="backup-$(date +%Y%m%d-%H%M%S)"
git tag "$BACKUP_TAG"
git push origin "$BACKUP_TAG"

echo "💾 Backup tag created: $BACKUP_TAG"

# Build production image
echo "🐳 Building production Docker image..."
docker build -t infinite-backrooms:v$VERSION --build-arg ENV=production .
docker tag infinite-backrooms:v$VERSION infinite-backrooms:latest

# Push to registry
echo "📤 Pushing to production registry..."
docker push infinite-backrooms:v$VERSION
docker push infinite-backrooms:latest

# Deploy with blue-green strategy
echo "🔵 Deploying to green environment..."
railway up --service production-green --environment production

# Wait for green deployment
sleep 30

# Health check green environment
echo "🏥 Health checking green environment..."
for i in {1..10}; do
    if curl -f "$PRODUCTION_URL-green/healthz" > /dev/null 2>&1; then
        echo "✅ Green environment healthy!"
        break
    fi

    if [ $i -eq 10 ]; then
        echo "❌ Green environment failed health check"
        echo "Rolling back..."
        exit 1
    fi

    echo "Waiting... ($i/10)"
    sleep 10
done

# Run production smoke tests
echo "💨 Running production smoke tests..."
pytest tests/smoke/ --base-url="$PRODUCTION_URL-green" -v

if [ $? -ne 0 ]; then
    echo "❌ Smoke tests failed. Not switching traffic."
    exit 1
fi

# Switch traffic to green
echo "🔀 Switching production traffic to green..."
railway env set ACTIVE_DEPLOYMENT=green --service production-router

# Monitor for 5 minutes
echo "📊 Monitoring new deployment..."
sleep 300

# Final health check
if curl -f "$PRODUCTION_URL/healthz" > /dev/null 2>&1; then
    echo "✅ Production deployment successful!"
    echo "🟢 Green environment is now active"
    echo ""
    echo "Cleaning up blue environment in 1 hour..."
else
    echo "❌ Production health check failed after traffic switch!"
    echo "🔙 Rolling back to blue environment..."
    railway env set ACTIVE_DEPLOYMENT=blue --service production-router
    exit 1
fi

# Notify stakeholders
echo "📧 Sending deployment notifications..."
# Add notification logic here

echo ""
echo "✅ Production deployment complete!"
echo "Version: v$VERSION"
echo "Deployed at: $(date)"
echo "URL: $PRODUCTION_URL"
```

### Step 7: Hotfix Workflow (30-45 min)

**Pattern: Emergency Hotfix**:
```bash
#!/bin/bash
# scripts/create_hotfix.sh

set -e

HOTFIX_NAME=$1
VERSION=$2

if [ -z "$HOTFIX_NAME" ] || [ -z "$VERSION" ]; then
    echo "Usage: $0 <hotfix-description> <version>"
    echo "Example: $0 security-patch 1.2.1"
    exit 1
fi

echo "🚨 Creating hotfix: $HOTFIX_NAME (v$VERSION)"

# Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b "hotfix/v$VERSION-$HOTFIX_NAME"

echo "🔧 Implement your hotfix now"
echo "When complete, run: ./scripts/finalize_hotfix.sh $HOTFIX_NAME $VERSION"
```

**Pattern: Finalize Hotfix**:
```bash
#!/bin/bash
# scripts/finalize_hotfix.sh

set -e

HOTFIX_NAME=$1
VERSION=$2

echo "🚀 Finalizing hotfix v$VERSION"

# Update version and changelog
sed -i '' "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml

# Run validation
pytest -v
python scripts/validate_production.py

# Commit changes
git add .
git commit -m "hotfix: $HOTFIX_NAME (v$VERSION)"

# Merge to main
git checkout main
git merge --no-ff "hotfix/v$VERSION-$HOTFIX_NAME"

# Tag
git tag -a "v$VERSION" -m "Hotfix v$VERSION: $HOTFIX_NAME"

# Push
git push origin main
git push origin "v$VERSION"

# Merge back to develop
git checkout develop
git merge --no-ff "hotfix/v$VERSION-$HOTFIX_NAME"
git push origin develop

# Cleanup
git branch -d "hotfix/v$VERSION-$HOTFIX_NAME"

echo "✅ Hotfix v$VERSION complete!"
echo "Deploy immediately with: ./scripts/deploy_production.sh $VERSION"
```

---

## Best Practices

### Git Flow
1. Never commit directly to main or develop
2. Use descriptive branch names
3. Keep feature branches small and focused
4. Rebase feature branches regularly
5. Use conventional commits

### Release Management
1. Always validate before releasing
2. Update changelog comprehensively
3. Tag releases semantically (semver)
4. Create GitHub releases with notes
5. Maintain release branches until deployed

### Deployment Strategy
1. Use blue-green or canary deployments
2. Always have rollback plan ready
3. Monitor during and after deployment
4. Run smoke tests post-deployment
5. Notify stakeholders

### Hotfix Process
1. Only for critical production issues
2. Keep changes minimal
3. Fast-track testing and deployment
4. Merge back to both main and develop
5. Document incident and resolution

---

## Success Criteria

- [ ] Git Flow workflow documented and implemented
- [ ] Release preparation automated
- [ ] Production validation comprehensive
- [ ] Staging deployment working
- [ ] Blue-green deployment configured
- [ ] Hotfix process defined
- [ ] Rollback procedure tested
- [ ] All scripts version controlled

---

## Tools Available
- Bash: Execute Git and deployment commands
- Read: Read configuration files
- Write: Create deployment scripts
- Grep: Find version references

---

## Validation Commands

```bash
# Check current branch and status
git status
git branch -vv

# Validate release preparation
./scripts/validate_release.sh 1.2.0

# Deploy to staging
./scripts/deploy_staging.sh 1.2.0

# Finalize release
./scripts/finalize_release.sh 1.2.0

# Deploy to production
./scripts/deploy_production.sh 1.2.0

# Create hotfix
./scripts/create_hotfix.sh security-patch 1.2.1

# Rollback deployment
./scripts/rollback_deployment.sh backup-20250114-120000
```
