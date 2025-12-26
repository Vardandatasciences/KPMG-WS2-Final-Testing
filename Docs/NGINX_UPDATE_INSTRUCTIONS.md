# Nginx Configuration Update Instructions

## What Changed

Your host nginx now **proxies all traffic** to the Docker container on port 8080. The Docker container's nginx handles:
- `/` → GRC Frontend
- `/tprm` → TPRM Frontend  
- `/api/` → Backend (via Docker network)

## Steps to Update

### 1. Backup Current Config

```bash
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup
```

### 2. Update Config File

**Option A: Copy the new file**

```bash
# Copy the modified config
sudo cp nginx.conf.modified /etc/nginx/nginx.conf
```

**Option B: Edit manually**

```bash
sudo nano /etc/nginx/nginx.conf
```

Replace the entire `server { ... }` block (from `server {` to `}`) with:

```nginx
server {
    listen 80;
    server_name _;

    # ============================
    # PROXY ALL TRAFFIC TO DOCKER CONTAINER
    # Docker container handles:
    # - / → GRC Frontend
    # - /tprm → TPRM Frontend
    # - /api/ → Backend (via Docker network)
    # ============================
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
    }

    # Deny access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    location ~ ~$ {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

### 3. Test Configuration

```bash
sudo nginx -t
```

Should see:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 4. Reload Nginx

```bash
sudo systemctl reload nginx
```

### 5. Verify It's Working

```bash
# Check nginx is running
sudo systemctl status nginx

# Test from EC2
curl http://localhost/
curl http://localhost/tprm
curl http://localhost/api/
```

## What Was Removed

The following location blocks were removed because Docker container handles them:
- `location /api/` - Now handled by Docker nginx → backend container
- `location /tprm` - Now handled by Docker nginx
- `location /` with `root /var/www/html/grc` - Now handled by Docker nginx
- Static file locations (`/css/`, `/js/`, `/assets/`, `/fonts/`) - Now handled by Docker nginx

## Rollback (If Needed)

If something goes wrong:

```bash
sudo cp /etc/nginx/nginx.conf.backup /etc/nginx/nginx.conf
sudo nginx -t
sudo systemctl reload nginx
```

## After Deployment

Once your GitHub Actions workflow completes and Docker containers are running:

1. **Verify containers are up:**
   ```bash
   docker ps
   ```

2. **Test endpoints:**
   ```bash
   curl http://localhost/        # Should show GRC frontend
   curl http://localhost/tprm    # Should show TPRM frontend
   curl http://localhost/api/    # Should show backend API
   ```

3. **Check logs if issues:**
   ```bash
   docker logs grc_tprm_frontend
   docker logs grc_tprm_backend
   sudo tail -f /var/log/nginx/error.log
   ```



