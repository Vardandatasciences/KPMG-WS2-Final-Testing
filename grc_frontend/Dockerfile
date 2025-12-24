# Combined Frontend Dockerfile (GRC + TPRM)
# Multi-stage build: Build both frontends, then serve with nginx

# ============================================
# STAGE 1: Build GRC Frontend
# ============================================
FROM node:20-alpine AS grc_builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tprm_frontend/package*.json ./tprm_frontend/

# Install dependencies for both GRC and TPRM
RUN npm ci
RUN cd tprm_frontend && npm ci

# Copy source code
COPY . .

# Build GRC frontend
RUN npm run build

# ============================================
# STAGE 2: Build TPRM Frontend
# ============================================
FROM node:20-alpine AS tprm_builder

WORKDIR /app

# Copy parent package.json (for dependency resolution if needed)
COPY package*.json ./
COPY tprm_frontend/package*.json ./tprm_frontend/

# Install parent dependencies (skip if not needed)
RUN npm ci || echo "Parent deps skipped"

# Install TPRM dependencies
WORKDIR /app/tprm_frontend
RUN npm ci --legacy-peer-deps || npm ci

# Copy TPRM source code
WORKDIR /app
COPY tprm_frontend/ ./tprm_frontend/

# Build TPRM frontend
WORKDIR /app/tprm_frontend
RUN npm run build

# ============================================
# STAGE 3: Serve with Nginx
# ============================================
FROM nginx:alpine

# Copy built frontends
COPY --from=grc_builder /app/dist /var/www/html/grc
COPY --from=tprm_builder /app/tprm_frontend/dist /var/www/html/tprm

# Copy nginx configuration for Docker (proxies /api/ to backend container)
COPY nginx.docker.conf /etc/nginx/nginx.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
