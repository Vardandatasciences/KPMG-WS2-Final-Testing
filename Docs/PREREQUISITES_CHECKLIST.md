# Pre-Deployment Prerequisites Checklist

## ✅ Complete this checklist BEFORE pushing to git

---

## 1. AWS ECR REPOSITORIES

### Question: Do you want to push images to ECR?

**Option A: Use ECR (Recommended for production)**
- ✅ Create 2 ECR repositories in AWS:
  - `grc_tprm_frontend`
  - `grc_tprm_backend`
- ✅ Repository region: `ap-south-1` (or update in workflow)
- ✅ Repository URI format: `480940871468.dkr.ecr.ap-south-1.amazonaws.com/grc_tprm_frontend:latest`

**Option B: Build locally only (No ECR)**
- ✅ Images built on EC2 instance
- ✅ No ECR push needed
- ✅ Workflow will still tag images for ECR but won't push (commented out)

**Action Required:**
- [ ] Confirm: Do you want to use ECR? (Yes/No)
- [ ] If Yes: Create ECR repositories and confirm names
- [ ] If No: We'll keep ECR push steps commented out

---

## 2. EC2 INSTANCE CONFIGURATION FILES

### Required Files on EC2 Instance:

#### A. Backend Environment File
**Location:** `/home/ec2-user/config.env`

**Required Variables:**
```bash
# Database
DATABASE_URL=mysql://user:password@host:3306/dbname
# OR separate variables:
DB_NAME=grc_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=your_host
DB_PORT=3306

# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,43.205.117.41

# AWS (if using S3)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_STORAGE_BUCKET_NAME=your-bucket
AWS_S3_REGION_NAME=ap-south-1

# Other Django settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-password
```

**Action Required:**
- [ ] Create `/home/ec2-user/config.env` on EC2 instance
- [ ] Add all required environment variables
- [ ] Verify file permissions: `chmod 600 /home/ec2-user/config.env`

#### B. Volume Directories
**Create these directories on EC2:**

```bash
mkdir -p /home/ec2-user/MEDIA_ROOT
mkdir -p /home/ec2-user/TEMP_MEDIA_ROOT
mkdir -p /home/ec2-user/Reports

# Set proper permissions
chmod -R 755 /home/ec2-user/MEDIA_ROOT
chmod -R 755 /home/ec2-user/TEMP_MEDIA_ROOT
chmod -R 755 /home/ec2-user/Reports
```

**Action Required:**
- [ ] Create all 3 directories on EC2
- [ ] Set proper permissions
- [ ] Verify directories exist

---

## 3. EC2 INSTANCE PREREQUISITES

### A. Docker Installation
```bash
# Check if Docker is installed
docker --version

# If not installed, install Docker:
sudo yum update -y
sudo yum install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user
```

**Action Required:**
- [ ] Docker is installed and running
- [ ] Docker daemon is active: `sudo systemctl status docker`
- [ ] User has Docker permissions

### B. Port 80 Availability
```bash
# Check if port 80 is free
sudo netstat -tulpn | grep :80
# OR
sudo lsof -i :80
```

**If port 80 is in use:**
- Option 1: Stop the service using port 80
- Option 2: Change `FRONTEND_PORT: 80` to another port (e.g., 8080) in workflow

**Action Required:**
- [ ] Port 80 is available
- [ ] If not, decide which port to use

### C. GitHub Actions Runner
```bash
# Verify self-hosted runner is running
cd ~/actions-runner
./run.sh
# OR check service status
sudo systemctl status actions.runner.*
```

**Action Required:**
- [ ] Self-hosted runner is configured
- [ ] Runner is online in GitHub Actions
- [ ] Runner has label: `self-hosted`

### D. AWS Credentials (if using ECR)
```bash
# Configure AWS credentials on EC2
aws configure
# OR set environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=ap-south-1
```

**Action Required:**
- [ ] AWS credentials configured (if using ECR)
- [ ] Can access ECR: `aws ecr describe-repositories --region ap-south-1`

---

## 4. GITHUB WORKFLOW CONFIGURATION

### A. ECR Registry Settings
**File:** `.github/workflows/main.yml`

**Current Settings:**
```yaml
AWS_REGION: ap-south-1
ECR_REGISTRY: 480940871468.dkr.ecr.ap-south-1.amazonaws.com
FRONTEND_IMAGE: ${ECR_REGISTRY}/grc_tprm_frontend:latest
BACKEND_IMAGE: ${ECR_REGISTRY}/grc_tprm_backend:latest
```

**Action Required:**
- [ ] Verify ECR registry URL is correct
- [ ] Verify AWS region is correct
- [ ] Confirm repository names match ECR repositories

### B. Enable/Disable ECR Push
**In workflow file, lines with ECR push:**

**To ENABLE ECR push (uncomment):**
```yaml
- name: Push Frontend to ECR
  run: |
    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
    docker push "${FRONTEND_IMAGE}"
```

**To DISABLE ECR push (keep commented):**
```yaml
- name: Push Frontend to ECR (optional)
  run: |
    # aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
    # docker push "${FRONTEND_IMAGE}"
    echo "Frontend image built successfully"
```

**Action Required:**
- [ ] Decide: Enable or disable ECR push?
- [ ] Update workflow file accordingly

---

## 5. NETWORK & SECURITY

### A. Security Group Rules
**EC2 Security Group should allow:**
- Inbound: Port 80 (HTTP) from 0.0.0.0/0 or your IP
- Inbound: Port 443 (HTTPS) if using SSL
- Outbound: All traffic (for Docker pulls, ECR access)

**Action Required:**
- [ ] Security group allows port 80 inbound
- [ ] Security group allows outbound traffic

### B. Firewall (if enabled)
```bash
# Check firewall status
sudo systemctl status firewalld

# If active, allow port 80
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --reload
```

**Action Required:**
- [ ] Firewall allows port 80 (if firewall is active)

---

## 6. DOCKER NETWORK

### Network Creation
The workflow will create the network automatically, but verify:

```bash
# Check existing networks
docker network ls

# If network exists from previous deployment, it's OK
# Workflow will reuse it
```

**Action Required:**
- [ ] No action needed (workflow handles this)

---

## 7. EXISTING CONTAINERS (if any)

### Clean Up Old Containers
```bash
# List running containers
docker ps -a

# Stop and remove old containers (if any)
docker stop grc_tprm_frontend grc_tprm_backend || true
docker rm grc_tprm_frontend grc_tprm_backend || true
```

**Action Required:**
- [ ] Check for existing containers
- [ ] Remove old containers if they exist

---

## 8. CODE VERIFICATION

### Verify Files Exist
- [ ] `grc_frontend/Dockerfile` exists
- [ ] `grc_frontend/nginx.docker.conf` exists
- [ ] `grc_backend/Dockerfile` exists
- [ ] `.github/workflows/main.yml` exists

**Action Required:**
- [ ] All required files are in repository

---

## 9. TESTING BEFORE DEPLOYMENT

### Manual Build Test (Optional but Recommended)
```bash
# Test frontend build locally on EC2
cd grc_frontend
docker build -t test_frontend .
docker run -d --name test_frontend -p 8080:80 test_frontend
curl http://localhost:8080/

# Test backend build
cd grc_backend
docker build -t test_backend .
```

**Action Required:**
- [ ] Optional: Test builds manually first

---

## 10. FINAL CHECKLIST

Before pushing to git, confirm:

- [ ] ECR repositories created (if using ECR)
- [ ] `/home/ec2-user/config.env` exists with all variables
- [ ] Volume directories created on EC2
- [ ] Docker installed and running on EC2
- [ ] Port 80 available on EC2
- [ ] GitHub Actions runner is online
- [ ] AWS credentials configured (if using ECR)
- [ ] Security group allows port 80
- [ ] Workflow file has correct ECR settings
- [ ] ECR push enabled/disabled as desired
- [ ] All code files committed to git

---

## AFTER PUSHING TO GIT

1. **Monitor GitHub Actions:**
   - Go to GitHub → Actions tab
   - Watch the workflow run
   - Check for any errors

2. **Verify Deployment:**
   ```bash
   # On EC2, check containers
   docker ps
   
   # Test endpoints
   curl http://localhost/
   curl http://localhost/tprm
   curl http://localhost/api/
   ```

3. **Check Logs if Issues:**
   ```bash
   docker logs grc_tprm_frontend
   docker logs grc_tprm_backend
   ```

---

## QUICK REFERENCE COMMANDS

```bash
# Create config.env
nano /home/ec2-user/config.env

# Create directories
mkdir -p /home/ec2-user/{MEDIA_ROOT,TEMP_MEDIA_ROOT,Reports}

# Check Docker
docker --version
sudo systemctl status docker

# Check port 80
sudo netstat -tulpn | grep :80

# Check GitHub runner
cd ~/actions-runner && ./run.sh

# Test after deployment
docker ps
curl http://localhost/
```

---

## CONFIRMATION REQUIRED

Please confirm each item above, then we'll finalize the configuration and you can push to git!



