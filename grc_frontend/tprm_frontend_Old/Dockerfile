# Multi-stage build for TPRM Frontend
# Stage 1: Build the application
# Note: Build context should be from grc_frontend directory
FROM node:20-alpine AS builder

WORKDIR /app

# Copy parent package.json first (for dependency resolution if needed)
COPY package*.json ./

# Copy TPRM package files
COPY tprm_frontend/package*.json ./tprm_frontend/

# Install parent dependencies (skip if not needed, TPRM might work without it)
RUN npm ci || echo "Parent dependencies skipped"

# Install TPRM dependencies
WORKDIR /app/tprm_frontend
RUN npm ci --legacy-peer-deps || npm ci

# Copy TPRM source code
COPY tprm_frontend/ ./tprm_frontend/

# Build TPRM frontend
WORKDIR /app/tprm_frontend
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy built files from builder stage
COPY --from=builder /app/tprm_frontend/dist /usr/share/nginx/html

# Copy nginx configuration for Docker
COPY tprm_frontend/nginx.docker.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

