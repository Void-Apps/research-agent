# AI Research Agent - Deployment Guide

This guide covers the deployment of the AI Research Agent application using Docker containers in different environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [Deployment Environments](#deployment-environments)
- [Security Considerations](#security-considerations)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- Git
- OpenSSL (for generating secrets)

### API Keys Required

Before deployment, you'll need to obtain API keys from:

1. **Google Scholar API**: [Google Custom Search API](https://developers.google.com/custom-search)
2. **Google Books API**: [Google Books API](https://developers.google.com/books)
3. **ScienceDirect API**: [Elsevier Developer Portal](https://dev.elsevier.com/)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ai-research-agent
```

### 2. Configure Environment

Run the interactive setup script:

```bash
./scripts/setup-env.sh
```

This will guide you through configuring all necessary environment variables and API keys.

### 3. Validate Configuration

```bash
./scripts/validate-env.sh
```

### 4. Deploy

```bash
./scripts/deploy.sh -e development
```

### 5. Access Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Environment Configuration

### Environment Files

The application uses different environment configurations:

- **Development**: `backend/.env.development`
- **Staging**: `backend/.env.staging`
- **Production**: `backend/.env.production`
- **Root**: `.env` (created by setup script)

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_SCHOLAR_API_KEY` | Google Scholar API key | `AIza...` |
| `GOOGLE_BOOKS_API_KEY` | Google Books API key | `AIza...` |
| `SCIENCEDIRECT_API_KEY` | ScienceDirect API key | `abc123...` |
| `MONGODB_ROOT_USERNAME` | MongoDB admin username | `admin` |
| `MONGODB_ROOT_PASSWORD` | MongoDB admin password | `secure_password` |
| `SECRET_KEY` | Application secret key | `32+ character string` |
| `NEXT_PUBLIC_API_URL` | Frontend API URL | `http://localhost:8000` |

### Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use strong passwords** (minimum 12 characters)
3. **Rotate API keys regularly**
4. **Use different credentials** for each environment
5. **Set restrictive file permissions**: `chmod 600 .env`
6. **Run security checks**: `./scripts/check-secrets.sh`
7. **Install git hooks**: `./scripts/install-git-hooks.sh`

### Security Scripts

- **`scripts/check-secrets.sh`**: Scan for potential secrets in repository
- **`scripts/install-git-hooks.sh`**: Install pre-commit hooks for security
- **`scripts/validate-env.sh`**: Validate environment configuration

## Deployment Environments

### Development Environment

**File**: `docker-compose.yml`

Features:
- Hot reloading for development
- Volume mounts for code changes
- Debug logging enabled
- Local MongoDB instance

```bash
./scripts/deploy.sh -e development
```

### Staging Environment

**File**: `docker-compose.staging.yml`

Features:
- Production-like configuration
- Reduced resource allocation
- Staging database
- Performance monitoring

```bash
./scripts/deploy.sh -e staging
```

### Production Environment

**File**: `docker-compose.prod.yml`

Features:
- Multiple service replicas
- Resource limits and reservations
- Nginx reverse proxy
- SSL/TLS termination
- Health checks and monitoring

```bash
./scripts/deploy.sh -e production
```

## Docker Configuration

### Frontend Dockerfile

Multi-stage build optimized for Next.js:

1. **Dependencies stage**: Install npm packages
2. **Builder stage**: Build the application
3. **Runner stage**: Minimal production image

### Backend Dockerfile

Multi-stage build for FastAPI:

1. **Dependencies stage**: Install Python packages
2. **Production stage**: Minimal runtime image with Gunicorn

### Services Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Nginx     │    │  Frontend   │    │   Backend   │
│ (Prod only) │────│  (Next.js)  │────│  (FastAPI)  │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
                   ┌─────────────┐    ┌─────────────┐
                   │    Redis    │    │   MongoDB   │
                   │  (Optional) │    │ (Database)  │
                   └─────────────┘    └─────────────┘
```

## Deployment Scripts

### `scripts/deploy.sh`

Main deployment script with options:

```bash
# Deploy to development
./scripts/deploy.sh -e development

# Deploy to production with fresh build
./scripts/deploy.sh -e production -f

# Deploy to staging and pull latest images
./scripts/deploy.sh -e staging -p
```

Options:
- `-e, --environment`: Target environment (development|staging|production)
- `-f, --fresh`: Build from scratch (no cache)
- `-p, --pull`: Pull latest base images
- `-h, --help`: Show help

### `scripts/setup-env.sh`

Interactive environment configuration:
- Prompts for all required variables
- Generates secure secret keys
- Creates `.env` file with proper permissions
- Provides security warnings

### `scripts/validate-env.sh`

Environment validation:
- Checks all required variables
- Validates API key formats
- Verifies file permissions
- Checks Docker configuration

## Monitoring and Maintenance

### Health Checks

All services include health checks:

```bash
# Check service status
docker-compose ps

# View health check logs
docker-compose logs <service-name>
```

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend

# View last 100 lines
docker-compose logs --tail=100
```

### Database Backup

```bash
# Backup MongoDB
docker-compose exec mongodb mongodump --out /data/backup

# Restore MongoDB
docker-compose exec mongodb mongorestore /data/backup
```

### Updates

```bash
# Pull latest images
docker-compose pull

# Rebuild and restart
./scripts/deploy.sh -e production -f
```

## Security Considerations

### Network Security

- Services communicate through internal Docker network
- Only necessary ports exposed to host
- Nginx handles SSL/TLS termination in production

### Data Security

- Environment variables for sensitive data
- MongoDB authentication enabled
- API keys stored securely
- File permissions restricted

### Application Security

- CORS properly configured
- Rate limiting implemented
- Input validation on all endpoints
- Security headers in Nginx

## Troubleshooting

### Common Issues

#### 1. Services Not Starting

```bash
# Check logs
docker-compose logs

# Check service status
docker-compose ps

# Restart specific service
docker-compose restart <service-name>
```

#### 2. Database Connection Issues

```bash
# Check MongoDB logs
docker-compose logs mongodb

# Test connection
docker-compose exec backend python -c "from database.connection import get_database; print(get_database())"
```

#### 3. API Key Issues

```bash
# Validate environment
./scripts/validate-env.sh

# Check API key format
echo $GOOGLE_SCHOLAR_API_KEY | wc -c  # Should be > 30 characters
```

#### 4. Build Failures

```bash
# Clean build
docker system prune -a

# Rebuild from scratch
./scripts/deploy.sh -e development -f
```

### Performance Issues

#### 1. High Memory Usage

```bash
# Check resource usage
docker stats

# Adjust resource limits in docker-compose files
```

#### 2. Slow API Responses

```bash
# Check backend logs
docker-compose logs backend

# Monitor database performance
docker-compose exec mongodb mongostat
```

### Getting Help

1. Check the logs first: `docker-compose logs`
2. Validate your environment: `./scripts/validate-env.sh`
3. Review this documentation
4. Check Docker and Docker Compose versions
5. Ensure all required ports are available

## Production Deployment Checklist

- [ ] API keys obtained and configured
- [ ] SSL certificates generated and placed in `nginx/ssl/`
- [ ] Domain name configured and DNS updated
- [ ] Firewall rules configured (ports 80, 443)
- [ ] Monitoring and alerting set up
- [ ] Backup strategy implemented
- [ ] Load testing completed
- [ ] Security audit performed
- [ ] Documentation updated

## Maintenance Schedule

### Daily
- Monitor service health
- Check error logs
- Verify backup completion

### Weekly
- Review performance metrics
- Update dependencies if needed
- Test backup restoration

### Monthly
- Rotate API keys
- Security updates
- Performance optimization review

### Quarterly
- Full security audit
- Disaster recovery testing
- Documentation review