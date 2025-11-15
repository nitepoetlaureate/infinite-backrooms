# GitHub Secrets Configuration

This document outlines the required GitHub secrets for the production CI/CD pipeline to function properly.

## Required Secrets

### Infrastructure & Deployment
- **`RAILWAY_TOKEN`**: Railway API token for deployment
  - Obtain from: https://railway.app/account/tokens
  - Required for: Deploying to Railway staging/production

- **`RAILWAY_STAGING_SERVICE`**: Railway service ID for staging environment
  - Format: service-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  - Required for: Staging deployments

- **`RAILWAY_PRODUCTION_SERVICE`**: Railway service ID for production environment
  - Format: service-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  - Required for: Production deployments

- **`RENDER_DEPLOY_HOOK`**: Render deployment webhook for production
  - Obtain from: Render dashboard → Service → Settings → Deploy Hooks
  - Required for: Production deployments

- **`RENDER_STAGING_DEPLOY_HOOK`**: Render deployment webhook for staging
  - Obtain from: Render dashboard → Service → Settings → Deploy Hooks
  - Required for: Staging deployments

### Security & Monitoring
- **`SEMGREP_APP_TOKEN`**: Semgrep token for security scanning
  - Obtain from: https://semgrep.dev/orgs/-/settings/tokens
  - Required for: Static security analysis

- **`SLACK_WEBHOOK`**: Slack webhook for deployment notifications
  - Obtain from: Slack app settings → Incoming Webhooks
  - Required for: Deployment status notifications

### Environment Variables (Optional but Recommended)
- **`DATABASE_URL`**: Production database connection string
  - Format: postgresql://user:password@host:port/database
  - Required for: Production database connections

- **`REDIS_URL`**: Redis connection string for caching
  - Format: redis://user:password@host:port
  - Required for: Production caching

- **`OLLAMA_BASE_URL`**: Ollama service URL for production
  - Format: https://your-ollama-service.com
  - Required for: AI model connections

## Setup Instructions

### 1. Navigate to Repository Settings
1. Go to your GitHub repository
2. Click "Settings" tab
3. Click "Secrets and variables" in the left sidebar
4. Click "Actions" to access secrets

### 2. Add Repository Secrets
For each secret above:
1. Click "New repository secret"
2. Enter the secret name (exact match required)
3. Paste the secret value
4. Click "Add secret"

### 3. Environment-Specific Secrets
The pipeline uses GitHub environments for staging and production:

#### Staging Environment
1. Go to Settings → Environments
2. Create "staging" environment if not exists
3. Add environment-specific secrets

#### Production Environment
1. Go to Settings → Environments
2. Create "production" environment if not exists
3. Add environment-specific secrets
4. Enable required protection rules:
   - Require reviewers
   - Wait timer (recommended: 5 minutes)

## Security Best Practices

### Secret Management
- **Never** commit secrets to version control
- Use least-privilege access tokens
- Regularly rotate secrets (every 90 days recommended)
- Monitor secret usage and access logs

### Token Scopes
Ensure tokens have minimal required permissions:

#### Railway Token
- Scope: Full access (required for deployment)

#### Render Webhook
- Scope: Deploy hook access only

#### Semgrep Token
- Scope: Read access to security policies

### Monitoring and Alerts
1. Set up alerts for secret usage
2. Monitor failed deployments
3. Track security scan results
4. Monitor performance metrics

## Testing Configuration

### Local Testing
To test the pipeline locally before setting up secrets:

```bash
# Mock secrets for local testing
export RAILWAY_TOKEN="test-token"
export RAILWAY_STAGING_SERVICE="test-service-id"
export RAILWAY_PRODUCTION_SERVICE="test-service-id"
```

### CI/CD Testing
1. Create a test branch
2. Push changes to trigger the pipeline
3. Monitor job execution
4. Verify each step completes successfully
5. Check deployment status

## Troubleshooting

### Common Issues
1. **Missing Secrets**: Jobs will fail with "secret not found" errors
2. **Invalid Tokens**: Deployment steps will fail authentication
3. **Incorrect Permissions**: Environment deployments will be blocked
4. **Expired Tokens**: API calls will return unauthorized errors

### Debug Steps
1. Check job logs for specific error messages
2. Verify secret names match exactly
3. Confirm token permissions and validity
4. Test deployment manually using same credentials

### Support Resources
- GitHub Actions Documentation: https://docs.github.com/en/actions
- Railway Deployment Guide: https://docs.railway.app/deploy
- Render Deployment Guide: https://render.com/docs/deploy-node-express
- Semgrep Documentation: https://semgrep.dev/docs

## Example Configuration

### Environment Protection Rules (Production)
```yaml
deployment_branch_policy:
  protected_branches: true
  custom_branch_policies:
    - name: main
      type: branch
```

### Approval Rules
- Require at least 1 reviewer
- Wait 5 minutes before deployment
- Dismiss stale PR approvals when new commits are pushed

### Notification Setup
Configure Slack notifications for:
- Deployment start
- Deployment success/failure
- Security scan results
- Performance test results

This configuration ensures secure, automated deployments with proper oversight and monitoring.