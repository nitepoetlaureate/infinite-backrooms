# Production CI/CD Pipeline Documentation

This document describes the comprehensive CI/CD pipeline implemented for the Infinite AI Backrooms application.

## Overview

The CI/CD pipeline provides automated testing, security scanning, container building, and deployment to staging and production environments. It follows DevOps best practices with proper validation, monitoring, and rollback capabilities.

## Pipeline Architecture

### Pipeline Files

- **`.github/workflows/ci-cd.yml`**: Main CI/CD pipeline
- **`.github/dependabot.yml`**: Automated dependency updates
- **`scripts/health_check.py`**: Health monitoring and validation
- **`scripts/deploy_check.sh`**: Pre-deployment validation
- **`.streamlit/config.toml`**: Production Streamlit configuration

### Environments

- **Staging**: Automated deployment from `develop` branch
- **Production**: Controlled deployment from `main/master` branches

## Pipeline Stages

### 1. Security Scanning
- **Tools**: Bandit, Safety, Semgrep, Trivy
- **Scope**: Python code, dependencies, container images
- **Output**: Security reports uploaded as artifacts
- **Integration**: GitHub Security tab for vulnerability tracking

### 2. Code Quality & Testing
- **Matrix Testing**: Python 3.11, 3.12
- **Quality Checks**: MyPy type checking, Ruff linting, Black formatting
- **Testing**: Unit tests with coverage, integration tests
- **Coverage**: Codecov integration for coverage tracking

### 3. Performance Testing
- **Tools**: Locust, pytest-benchmark
- **Scope**: Load testing, performance benchmarks
- **Environment**: Staging only
- **Thresholds**: Configurable performance SLAs

### 4. Container Building
- **Platform**: Multi-arch (linux/amd64, linux/arm64)
- **Registry**: GitHub Container Registry (ghcr.io)
- **Security**: Vulnerability scanning with Trivy
- **Metadata**: Automated tagging and provenance

### 5. Deployment
- **Strategy**: Blue-green deployment for production
- **Platforms**: Railway, Render
- **Validation**: Health checks, smoke tests
- **Monitoring**: Deployment notifications via Slack

## Configuration

### Required Secrets

See `docs/GITHUB_SECRETS.md` for complete secret configuration.

### Environment Variables

#### Production Environment
```bash
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://user:pass@host:port
OLLAMA_BASE_URL=https://your-ollama-service.com
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ENABLE_CORS=true
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true
```

#### Staging Environment
```bash
OLLAMA_BASE_URL=http://localhost:11434
NODE_ENV=staging
LOG_LEVEL=INFO
```

## Deployment Process

### Staging Deployment (Automated)

1. **Trigger**: Push to `develop` branch
2. **Validation**: All pipeline stages must pass
3. **Deployment**: Automatic deployment to Railway and Render
4. **Monitoring**: Health checks and smoke tests
5. **Notification**: Status updates via configured channels

### Production Deployment (Controlled)

1. **Trigger**: Push to `main/master` branch OR manual workflow dispatch
2. **Pre-deployment**: Comprehensive validation
3. **Blue-green deployment**: Zero-downtime deployment strategy
4. **Health validation**: Post-deployment health checks
5. **Rollback capability**: Automatic rollback on failure

## Monitoring and Observability

### Health Checks
- **Endpoint**: `/_stcore/health`
- **Frequency**: Every 30 seconds
- **Timeout**: 10 seconds
- **Metrics**: Response time, status codes

### Performance Monitoring
- **Response time**: 95th percentile < 500ms
- **Error rate**: < 1%
- **Availability**: > 99.9%
- **Throughput**: Configured based on traffic patterns

### Security Monitoring
- **Vulnerability scanning**: Automated on every build
- **Secret scanning**: Git commit history monitoring
- **Dependency updates**: Daily security patches via Dependabot

## Rollback Procedures

### Automatic Rollback
- **Trigger**: Health check failures
- **Timeout**: 5 minutes after deployment
- **Process**: Switch traffic back to previous version
- **Notification**: Immediate alerts on rollback

### Manual Rollback
```bash
# Using Railway CLI
railway rollback

# Using Render webhook
curl -X POST PREVIOUS_VERSION_WEBHOOK

# Using git
git revert <commit_hash>
git push origin main
```

## Performance Optimization

### Container Optimization
- **Multi-stage builds**: Reduce image size
- **Layer caching**: GitHub Actions cache
- **Platform support**: AMD64 and ARM64
- **Security**: Minimal attack surface

### Deployment Optimization
- **Parallel testing**: Matrix strategy for speed
- **Artifact caching**: Reuse between builds
- **Selective deployment**: Environment-based triggers
- **Resource limits**: Configurable per environment

## Security Best Practices

### Secret Management
- **No secrets in code**: All secrets in environment variables
- **Rotation**: Regular secret rotation (90 days)
- **Audit**: Secret access monitoring
- **Scope**: Minimum required permissions

### Container Security
- **Base images**: Minimal, official images
- **Scanning**: Trivy vulnerability scanning
- **Signing**: Container image provenance
- **Patching**: Automated security updates

### Application Security
- **CORS**: Configured for production domains
- **XSRF**: Protection enabled
- **Rate limiting**: Request throttling
- **Input validation**: Sanitization layers

## Troubleshooting

### Common Issues

#### Pipeline Failures
1. **Check logs**: GitHub Actions tab
2. **Validate secrets**: Ensure all required secrets are set
3. **Verify syntax**: Python and configuration file validation
4. **Check dependencies**: Package conflicts and versions

#### Deployment Issues
1. **Health checks**: Verify application responds to health endpoints
2. **Environment variables**: Confirm all required variables are set
3. **Resource limits**: Check memory and CPU allocations
4. **Network**: Verify external service connectivity

#### Performance Issues
1. **Bottlenecks**: Use application monitoring tools
2. **Database**: Check query performance and indexing
3. **External APIs**: Verify Ollama service performance
4. **Resources**: Scale resources based on demand

### Debug Commands

```bash
# Local health check
python scripts/health_check.py --base-url http://localhost:8501

# Pre-deployment validation
bash scripts/deploy_check.sh --environment production --verbose

# Container image inspection
docker inspect ghcr.io/nitepoetlaureate/infinite-backrooms:latest

# Log analysis
kubectl logs -f deployment/infinite-backrooms
```

## Maintenance

### Regular Tasks
- **Secret rotation**: Every 90 days
- **Dependency updates**: Weekly via Dependabot
- **Security patches**: Daily automated updates
- **Performance review**: Monthly analysis

### Monitoring Setup
- **Alerts**: Slack/email notifications
- **Dashboards**: Grafana/CloudWatch metrics
- **Logging**: Centralized log aggregation
- **Auditing**: Change tracking and compliance

## Development Workflow

### Feature Development
1. **Branch**: Create feature branch from `develop`
2. **Testing**: Run tests locally
3. **PR**: Create pull request to `develop`
4. **CI**: Automated testing and validation
5. **Merge**: Merge to `develop` for staging deployment

### Production Release
1. **Testing**: Verify staging deployment
2. **PR**: Create pull request to `main`
3. **Review**: Code review and approval
4. **Deployment**: Automated production deployment
5. **Monitoring**: Post-deployment validation

This comprehensive CI/CD pipeline ensures reliable, secure, and performant deployments with proper monitoring and rollback capabilities.