# Two Image Docker Setup - GRC & TPRM

## Overview

This setup uses **2 Docker images**:
1. **Frontend Image** - Contains GRC + TPRM frontends + Nginx (serves both and proxies API)
2. **Backend Image** - Django backend API

## Architecture

```
Internet → Port 80 (Frontend Container with Nginx)
              ├── / → GRC Frontend (static files)
              ├── /tprm → TPRM Frontend (static files)
              └── /api/ → Backend Container (grc_tprm_backend:8000)
```

## Files Structure

### Frontend Image (`grc_frontend/Dockerfile`)
- **Stage 1**: Builds GRC frontend (Vue.js)
- **Stage 2**: Builds TPRM frontend (Vite/Vue.js)
- **Stage 3**: Serves both with Nginx + proxies `/api/` to backend

### Backend Image (`grc_backend/Dockerfile`)
- Django application
- Runs on port 8000
- Connected to frontend via Docker network

## Deployment

### Automatic (GitHub Actions)

The workflow (`.github/workflows/main.yml`) will:
1. Create Docker network
2. Build and deploy Frontend container (port 80)
3. Build and deploy Backend container (port 8000, internal)
4. Verify all services

### Manual Deployment

```bash
# 1. Create Docker network
docker network create grc_tprm_network

# 2. Build and run Frontend (GRC + TPRM)
cd grc_frontend
docker build -t grc_tprm_frontend:latest .
docker run -d \
  --name grc_tprm_frontend \
  --network grc_tprm_network \
  -p 80:80 \
  --restart unless-stopped \
  grc_tprm_frontend:latest

# 3. Build and run Backend
cd grc_backend
docker build -t grc_tprm_backend:latest .
docker run -d \
  --name grc_tprm_backend \
  --network grc_tprm_network \
  --env-file /home/ec2-user/config.env \
  -v /home/ec2-user/MEDIA_ROOT:/app/MEDIA_ROOT \
  -v /home/ec2-user/TEMP_MEDIA_ROOT:/app/TEMP_MEDIA_ROOT \
  -v /home/ec2-user/Reports:/app/Reports \
  --restart unless-stopped \
  grc_tprm_backend:latest
```

## Container Communication

- Frontend container proxies `/api/` requests to `grc_tprm_backend:8000`
- Both containers are on the same Docker network (`grc_tprm_network`)
- Frontend exposes port 80 to the internet
- Backend is only accessible via Docker network (not exposed externally)

## Benefits of 2-Image Setup

✅ **Simpler than 4 images** - Only 2 containers to manage
✅ **Independent Updates** - Update frontend or backend separately
✅ **Clear Separation** - Frontend and backend are distinct
✅ **Efficient** - Frontend image contains both GRC and TPRM
✅ **Easy to Scale** - Can scale frontend or backend independently if needed

## Testing

After deployment:

```bash
# Check containers
docker ps

# Test endpoints
curl http://localhost/          # GRC Frontend
curl http://localhost/tprm      # TPRM Frontend
curl http://localhost/api/      # Backend API

# Check logs
docker logs grc_tprm_frontend
docker logs grc_tprm_backend
```

## Troubleshooting

### Frontend can't reach backend
- Verify both containers are on the same network: `docker network inspect grc_tprm_network`
- Check backend container name matches nginx config: `grc_tprm_backend`
- Verify backend is running: `docker ps | grep grc_tprm_backend`

### Port 80 already in use
- Change `FRONTEND_PORT: 80` in workflow to another port (e.g., 8080)
- Update firewall/security group rules

### Build fails
- Check Node.js version (should be 20)
- Verify all package.json files exist
- Check TPRM dependencies (may need `--legacy-peer-deps`)



