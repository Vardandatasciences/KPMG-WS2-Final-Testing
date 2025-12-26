# Docker Deployment Guide for GRC & TPRM

## Overview
This guide explains the Docker deployment setup with 4 containers:
1. **GRC Frontend** - Vue.js application
2. **TPRM Frontend** - Vite/Vue.js application  
3. **Backend** - Django API
4. **Reverse Proxy Nginx** - Routes traffic to the above services

## Architecture

```
Internet → Port 80 (Reverse Proxy Nginx)
              ├── /api/ → Backend (grc_tprm:8000)
              ├── /tprm → TPRM Frontend (tprm_frontend:80)
              └── / → GRC Frontend (grc_frontend:80)
```

## Pre-Deployment Checklist

### ✅ Required Files & Configurations

1. **Backend Environment File**
   - Location: `/home/ec2-user/config.env`
   - Must contain all Django environment variables (DATABASE_URL, SECRET_KEY, etc.)

2. **Backend Volume Directories**
   - `/home/ec2-user/MEDIA_ROOT` - Media files
   - `/home/ec2-user/TEMP_MEDIA_ROOT` - Temporary media files
   - `/home/ec2-user/Reports` - Generated reports

3. **AWS ECR Access** (if pushing images)
   - Ensure AWS credentials are configured on the EC2 instance
   - ECR repositories should exist:
     - `grc_frontend`
     - `tprm_frontend`
     - `grc_tprm`
     - `nginx_reverse_proxy`

### ✅ Docker Prerequisites

- Docker installed on EC2 instance
- Docker daemon running
- Sufficient disk space for images
- Port 80 available (or change `REVERSE_PROXY_PORT` in workflow)

## Deployment Steps

### Automatic Deployment (GitHub Actions)

1. **Push to main/master branch** - Triggers automatic deployment
2. **Or use workflow_dispatch** - Manual trigger from GitHub Actions UI

### Manual Deployment (if needed)

```bash
# 1. Create Docker network
docker network create grc_tprm_network

# 2. Build and run GRC Frontend
cd grc_frontend
docker build -t grc_frontend:latest .
docker run -d --name grc_frontend --network grc_tprm_network --restart unless-stopped grc_frontend:latest

# 3. Build and run TPRM Frontend
cd grc_frontend
docker build -f tprm_frontend/Dockerfile -t tprm_frontend:latest .
docker run -d --name tprm_frontend --network grc_tprm_network --restart unless-stopped tprm_frontend:latest

# 4. Build and run Backend
cd grc_backend
docker build -t grc_tprm:latest .
docker run -d --name grc_tprm --network grc_tprm_network \
  --env-file /home/ec2-user/config.env \
  -v /home/ec2-user/MEDIA_ROOT:/app/MEDIA_ROOT \
  -v /home/ec2-user/TEMP_MEDIA_ROOT:/app/TEMP_MEDIA_ROOT \
  -v /home/ec2-user/Reports:/app/Reports \
  --restart unless-stopped grc_tprm:latest

# 5. Build and run Reverse Proxy
cd nginx-reverse-proxy
docker build -t nginx_reverse_proxy:latest .
docker run -d --name nginx_reverse_proxy --network grc_tprm_network \
  -p 80:80 --restart unless-stopped nginx_reverse_proxy:latest
```

## Modifications You May Need

### 1. **ECR Repository Names**
If your ECR repositories have different names, update in `.github/workflows/main.yml`:
```yaml
GRC_FRONTEND_IMAGE: ${ECR_REGISTRY}/your_grc_repo:latest
TPRM_FRONTEND_IMAGE: ${ECR_REGISTRY}/your_tprm_repo:latest
BACKEND_IMAGE: ${ECR_REGISTRY}/your_backend_repo:latest
REVERSE_PROXY_IMAGE: ${ECR_REGISTRY}/your_nginx_repo:latest
```

### 2. **Enable ECR Push** (Optional)
Uncomment the push steps in `.github/workflows/main.yml`:
```yaml
- name: Push GRC Frontend to ECR
  run: |
    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
    docker push "${GRC_FRONTEND_IMAGE}"
```

### 3. **Change Ports**
If port 80 is already in use, modify in workflow:
```yaml
REVERSE_PROXY_PORT: 8080  # Change from 80 to your preferred port
```

### 4. **Backend API Path**
If your Django API uses a different path structure, update `nginx-reverse-proxy/nginx.conf`:
```nginx
location /api/ {
    proxy_pass http://backend_api;  # Adjust if needed
    # ... rest of config
}
```

### 5. **Frontend Base Paths**
If TPRM or GRC need different base paths, update:
- `nginx-reverse-proxy/nginx.conf` - location blocks
- Frontend build configurations (if using base paths)

## Verification

After deployment, verify all services:

```bash
# Check running containers
docker ps

# Check logs
docker logs grc_frontend
docker logs tprm_frontend
docker logs grc_tprm
docker logs nginx_reverse_proxy

# Test endpoints
curl http://localhost/              # GRC Frontend
curl http://localhost/tprm          # TPRM Frontend
curl http://localhost/api/          # Backend API
```

## Troubleshooting

### Container won't start
- Check logs: `docker logs <container_name>`
- Verify network exists: `docker network ls`
- Check port conflicts: `netstat -tulpn | grep :80`

### 502 Bad Gateway
- Verify backend container is running: `docker ps | grep grc_tprm`
- Check network connectivity: `docker exec nginx_reverse_proxy ping grc_tprm`
- Verify backend is listening on port 8000

### Frontend not loading
- Check frontend container logs
- Verify reverse proxy routing in nginx logs
- Test direct container access: `curl http://grc_frontend/` (from within network)

### API calls failing
- Verify `/api/` location block in reverse proxy nginx.conf
- Check CORS settings if needed
- Verify backend container name matches upstream definition

## Rollback

To rollback to previous version:

```bash
# Stop current containers
docker stop grc_frontend tprm_frontend grc_tprm nginx_reverse_proxy

# Pull previous images from ECR (if using ECR)
docker pull ${ECR_REGISTRY}/grc_frontend:previous-tag

# Restart with previous images
docker start grc_frontend tprm_frontend grc_tprm nginx_reverse_proxy
```

## Maintenance

### Update a single service
```bash
# Example: Update only GRC Frontend
cd grc_frontend
docker build -t grc_frontend:latest .
docker stop grc_frontend
docker rm grc_frontend
docker run -d --name grc_frontend --network grc_tprm_network --restart unless-stopped grc_frontend:latest
```

### View resource usage
```bash
docker stats
```

### Clean up old images
```bash
docker image prune -a
```

## Security Considerations

1. **Environment Variables**: Never commit `config.env` to git
2. **Port Exposure**: Only reverse proxy exposes port 80 externally
3. **Network Isolation**: All containers on private Docker network
4. **Volume Permissions**: Ensure proper file permissions on host volumes

## Support

For issues or questions:
1. Check container logs first
2. Verify network connectivity
3. Review nginx reverse proxy configuration
4. Check GitHub Actions workflow logs



