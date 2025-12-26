# Fix "No Space Left on Device" Error

## Problem
Docker build is failing because EC2 instance has run out of disk space.

## Quick Fix - Run on EC2

### 1. Check Disk Space
```bash
df -h
```

### 2. Clean Up Docker (IMPORTANT)
```bash
# Remove stopped containers
docker container prune -f

# Remove unused images
docker image prune -a -f

# Remove unused volumes
docker volume prune -f

# Remove build cache
docker builder prune -a -f

# Check space after cleanup
df -h
```

### 3. Clean Up System
```bash
# Clean package cache
sudo yum clean all

# Remove old logs
sudo journalctl --vacuum-time=7d

# Check what's using space
du -sh /var/* | sort -h
```

### 4. Verify Space Available
```bash
# Should show at least 5GB free
df -h /
```

## Permanent Solution

I've updated the workflow to automatically clean up before building. The workflow now:
1. Cleans Docker before each build
2. Removes old images/containers
3. Cleans build cache

## If Still Not Enough Space

### Option 1: Increase EC2 Volume Size
1. Go to AWS Console → EC2 → Volumes
2. Select your volume
3. Actions → Modify Volume
4. Increase size (e.g., 20GB → 40GB)
5. Extend filesystem:
```bash
sudo growpart /dev/xvda 1
sudo resize2fs /dev/xvda1
# OR for newer systems:
sudo xfs_growfs /
```

### Option 2: Use ECR Instead of Local Build
- Pull pre-built images from ECR
- Skip local builds
- Much less disk space needed



