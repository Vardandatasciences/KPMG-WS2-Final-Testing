# Hostinger Auto-Deployment Setup Guide

This guide helps you set up automatic deployment to your Hostinger server using GitHub Actions CI/CD.

## Overview

When you push to `main` or `master` branch:
1. GitHub Actions will automatically deploy to Hostinger
2. Creates backup before deployment
3. Builds and starts Docker containers
4. Runs Django migrations
5. Performs health checks

## Prerequisites

1. **Hostinger Server** with:
   - Docker and Docker Compose installed
   - SSH access enabled
   - Git installed

2. **GitHub Repository** with your code

## Step 1: Setup Hostinger Server

### 1.1 Create deployment user (optional but recommended)
```bash
# On your Hostinger server
sudo adduser grc-app
sudo usermod -aG docker grc-app
```

### 1.2 Create deployment directory
```bash
# On your Hostinger server
sudo mkdir -p /home/grc-app
sudo chown grc-app:grc-app /home/grc-app
cd /home/grc-app
```

### 1.3 Clone your repository
```bash
# On your Hostinger server
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git .
```

### 1.4 Setup environment file
```bash
# On your Hostinger server
cp grc_backend/.env.example grc_backend/.env
# Edit .env with your production values
nano grc_backend/.env
```

## Step 2: Generate SSH Keys

### 2.1 Generate SSH key pair on Hostinger
```bash
# On your Hostinger server (as grc-app user)
ssh-keygen -t rsa -b 4096 -C "github-actions-deploy" -f ~/.ssh/github_actions
```

### 2.2 Add public key to authorized_keys
```bash
# On your Hostinger server
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### 2.3 Test SSH connection
```bash
# On your local machine to test
ssh -i ~/.ssh/github_actions grc-app@YOUR_HOSTINGER_IP
```

## Step 3: Add GitHub Secrets

Go to your GitHub repository:
1. **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"** for each:

| Secret Name | Value |
|---|---|
| `HOSTINGER_HOST` | Your Hostinger IP or domain |
| `HOSTINGER_USER` | `grc-app` (or your username) |
| `HOSTINGER_SSH_PRIVATE_KEY` | Private key content (see below) |

### Getting the private key:
```bash
# On your Hostinger server
cat ~/.ssh/github_actions
# Copy the entire output (including -----BEGIN RSA PRIVATE KEY----- and -----END RSA PRIVATE KEY-----)
```

## Step 4: Manual First Deployment

Before enabling CI/CD, do a manual deployment to ensure everything works:

```bash
# On your Hostinger server
cd /home/grc-app

# Pull latest code
git pull origin main

# Build and start containers
docker compose -f deploy/docker-compose.production.yml up -d --build

# Check status
docker compose -f deploy/docker-compose.production.yml ps

# Run migrations
docker exec grc_tprm_backend_v2 python manage.py migrate
```

## Step 5: Test CI/CD Deployment

1. Push any change to main/master branch
2. Go to **Actions** tab in GitHub
3. Watch the deployment workflow run
4. Check if deployment succeeds

## What the Deployment Does

### Backup Process
- Creates timestamped backup in `/home/grc-app/backups/`
- Backs up database (if MySQL)
- Backs up Docker volumes (media, temp media, reports)
- Keeps only last 5 backups

### Deployment Process
1. Syncs code to server (excluding node_modules, .git, etc.)
2. Stops existing containers
3. Builds new Docker images
4. Starts containers with docker-compose
5. Runs Django migrations
6. Collects static files
7. Performs health checks

### Health Checks
- Waits for services to start
- Checks backend health endpoint
- Checks frontend accessibility
- Reports success/failure

## Troubleshooting

### Common Issues

#### 1. SSH Connection Failed
```bash
# Check SSH key permissions
chmod 600 ~/.ssh/github_actions
chmod 644 ~/.ssh/github_actions.pub
```

#### 2. Docker Build Fails
```bash
# Check Docker is running
sudo systemctl status docker

# Check disk space
df -h

# Clean Docker if needed
docker system prune -a
```

#### 3. Database Connection Issues
- Verify `.env` file has correct database credentials
- Check if database server is running
- Ensure database exists and user has permissions

#### 4. Port Conflicts
- The deployment uses ports 8001 (backend) and 8081 (frontend)
- Ensure these ports are not in use by other services

### Viewing Logs

#### On Hostinger Server:
```bash
# View all logs
cd /home/grc-app
docker compose -f deploy/docker-compose.production.yml logs -f

# View specific service logs
docker compose -f deploy/docker-compose.production.yml logs -f grc_tprm_backend
docker compose -f deploy/docker-compose.production.yml logs -f frontend
```

#### In GitHub Actions:
- Go to Actions tab
- Click on the deployment run
- Expand each step to see detailed logs

### Manual Rollback

If deployment fails, you can rollback:

```bash
# On Hostinger server
cd /home/grc-app/backups
ls -la  # List available backups

# Restore from latest backup
BACKUP_DIR=$(ls -t | head -n 1)
cd /home/grc-app
docker compose -f deploy/docker-compose.production.yml down

# Restore volumes
docker run --rm -v grc_media:/data -v /home/grc-app/backups/$BACKUP_DIR:/backup alpine tar xzf /backup/grc_media.tar.gz -C /data
docker run --rm -v grc_temp_media:/data -v /home/grc-app/backups/$BACKUP_DIR:/backup alpine tar xzf /backup/grc_temp_media.tar.gz -C /data
docker run --rm -v grc_reports:/data -v /home/grc-app/backups/$BACKUP_DIR:/backup alpine tar xzf /backup/grc_reports.tar.gz -C /data

# Restart containers
docker compose -f deploy/docker-compose.production.yml up -d
```

## Customization

### Changing Ports
Edit `deploy/docker-compose.production.yml`:
```yaml
ports:
  - "YOUR_BACKEND_PORT:8000"  # Backend
  - "YOUR_FRONTEND_PORT:80"   # Frontend
```

### Adding Environment-Specific Config
Create separate docker-compose files:
- `docker-compose.staging.yml`
- `docker-compose.production.yml`

### Custom Health Checks
Add health checks to docker-compose:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Security Notes

1. **SSH Keys**: Keep the private key secure - only share with GitHub Actions
2. **Environment Variables**: Never commit `.env` file to git
3. **Backups**: Regularly download backups from server
4. **Updates**: Keep Docker and system packages updated
5. **Firewall**: Configure firewall to only allow necessary ports

## Monitoring

### Set up monitoring (optional):
1. Use Uptime monitoring services
2. Set up log aggregation (ELK stack, etc.)
3. Configure email alerts for deployment failures
4. Monitor disk space and resource usage

## Next Steps

1. ✅ Complete the setup above
2. ✅ Test manual deployment
3. ✅ Add GitHub secrets
4. ✅ Push to trigger CI/CD
5. ✅ Verify automatic deployment works

After setup, every push to main/master will automatically deploy to Hostinger!
