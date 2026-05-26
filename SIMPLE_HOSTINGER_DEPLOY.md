# Simple Hostinger Auto-Deployment

## What This Does

When you push to `main` or `master` branch:
1. GitHub Actions automatically deploys to Hostinger
2. Stops existing containers
3. Syncs your code
4. Runs `docker-compose up -d` 
5. Shows deployment status

**No SSH keys needed - uses password authentication**
**No migrations - Docker compose handles everything**

## Quick Setup (5 minutes)

### 1. On your Hostinger server

```bash
# Create deployment directory
mkdir -p /home/grc-app
cd /home/grc-app

# Clone your repo
git clone https://github.com/Vardandatasciences/KPMG-WS2-Final-Testing.git .

# Make sure Docker is installed
docker --version
docker compose version
```

### 2. Add GitHub Secrets

Go to your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**

Add these 3 secrets:

| Secret Name | Value |
|---|---|
| `HOSTINGER_HOST` | Your Hostinger IP or domain |
| `HOSTINGER_USER` | Your SSH username (e.g., `root` or your username) |
| `HOSTINGER_PASSWORD` | Your SSH password |

### 3. Test It

Push any change to main branch:
```bash
git add .
git commit -m "test deployment"
git push origin main
```

Go to **Actions** tab in GitHub to watch the deployment.

## What Happens During Deployment

1. **Stops containers**: `docker-compose down`
2. **Syncs code**: Copies your latest code to server
3. **Builds images**: `docker-compose build`
4. **Starts services**: `docker-compose up -d`
5. **Shows status**: Lists running containers

## Your Docker Compose File

The deployment uses your existing file: `deploy/docker-compose.production.yml`

It will:
- Backend on port 8001
- Frontend on port 8081
- Use your `.env` file for configuration

## Check Deployment

After deployment, your app should be at:
- Frontend: `http://YOUR_HOSTINGER_IP:8081`
- Backend API: `http://YOUR_HOSTINGER_IP:8001`

## Manual Commands (if needed)

```bash
# SSH into your server
ssh your_username@YOUR_HOSTINGER_IP

# Check containers
cd /home/grc-app
docker compose -f deploy/docker-compose.production.yml ps

# View logs
docker compose -f deploy/docker-compose.production.yml logs -f

# Restart containers
docker compose -f deploy/docker-compose.production.yml restart
```

## Troubleshooting

### If deployment fails:
1. Check the **Actions** tab for error details
2. Make sure Docker is running on Hostinger
3. Verify your password is correct
4. Check if ports 8001/8081 are available

### If containers don't start:
```bash
# On Hostinger server
cd /home/grc-app
docker compose -f deploy/docker-compose.production.yml down
docker compose -f deploy/docker-compose.production.yml up -d --build
```

## That's It! 🎉

Now every push to main/master will automatically deploy to Hostinger using your existing Docker setup.
