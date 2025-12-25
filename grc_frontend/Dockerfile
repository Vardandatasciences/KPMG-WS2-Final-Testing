# Combined Frontend Dockerfile (GRC + TPRM)
# Multi-stage build: Build both frontends, then serve with nginx

# ============================================
# STAGE 1: Build GRC Frontend
# ============================================
FROM node:20-alpine AS grc_builder

# Build argument to force cache invalidation
ARG BUILD_DATE
ARG GIT_COMMIT
ARG CACHE_BUST=1

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tprm_frontend/package*.json ./tprm_frontend/

# Install dependencies for both GRC and TPRM
RUN npm ci
RUN cd tprm_frontend && npm ci

# Copy source code (this will invalidate cache when files change)
COPY . .

# Remove any existing dist folder to ensure fresh build
RUN rm -rf dist || true

# Verify api.js is present and show environment setting
RUN echo "=== Checking api.js configuration ===" && \
    cat src/config/api.js | grep -A 2 "ENVIRONMENT" || echo "WARNING: Could not find ENVIRONMENT in api.js" && \
    echo "=== Build Date: ${BUILD_DATE} ===" && \
    echo "=== Git Commit: ${GIT_COMMIT} ===" && \
    echo "=== Cache Bust: ${CACHE_BUST} ==="

# Build GRC frontend (this will always run fresh due to COPY . . above)
RUN npm run build

# Verify the built files contain the correct API URL
RUN echo "=== Verifying built API configuration ===" && \
    find dist -name "*.js" -type f | head -1 | xargs grep -o "grc-backend.vardaands.com\|127.0.0.1:8000" | head -5 || echo "Could not verify API URL in built files"

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
