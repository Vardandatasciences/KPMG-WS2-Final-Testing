# AWS ECR Setup Guide

## Create ECR Repositories

Since you confirmed you want to use ECR, follow these steps:

---

## STEP 1: Create ECR Repositories

### Option A: Using AWS Console

1. **Login to AWS Console**
2. **Navigate to ECR:**
   - Go to **Services** → **ECR** (Elastic Container Registry)
   - Select region: **ap-south-1** (Mumbai)

3. **Create First Repository (Frontend):**
   - Click **Create repository**
   - **Visibility settings:** Private
   - **Repository name:** `grc_tprm_frontend`
   - **Tag immutability:** Enable (recommended)
   - **Scan on push:** Enable (recommended)
   - Click **Create repository**

4. **Create Second Repository (Backend):**
   - Click **Create repository**
   - **Repository name:** `grc_tprm_backend`
   - **Tag immutability:** Enable
   - **Scan on push:** Enable
   - Click **Create repository**

### Option B: Using AWS CLI

```bash
# Set region
export AWS_REGION=ap-south-1

# Create frontend repository
aws ecr create-repository \
    --repository-name grc_tprm_frontend \
    --region ${AWS_REGION} \
    --image-scanning-configuration scanOnPush=true \
    --image-tag-mutability MUTABLE

# Create backend repository
aws ecr create-repository \
    --repository-name grc_tprm_backend \
    --region ${AWS_REGION} \
    --image-scanning-configuration scanOnPush=true \
    --image-tag-mutability MUTABLE
```

---

## STEP 2: Verify Repository URIs

After creating repositories, note the **Repository URI**:

- Frontend: `480940871468.dkr.ecr.ap-south-1.amazonaws.com/grc_tprm_frontend`
- Backend: `480940871468.dkr.ecr.ap-south-1.amazonaws.com/grc_tprm_backend`

**Verify these match your workflow file:**
- `.github/workflows/main.yml` lines 27-28

---

## STEP 3: Configure AWS Credentials on EC2

### Option A: Using AWS CLI Configure

```bash
# On EC2 instance
aws configure

# Enter:
# AWS Access Key ID: [your-access-key]
# AWS Secret Access Key: [your-secret-key]
# Default region name: ap-south-1
# Default output format: json
```

### Option B: Using IAM Role (Recommended)

1. **Create IAM Role:**
   - Go to **IAM** → **Roles** → **Create role**
   - Select **EC2** as trusted entity
   - Attach policy: `AmazonEC2ContainerRegistryFullAccess`
   - Name: `EC2-ECR-Access-Role`

2. **Attach Role to EC2:**
   - Go to **EC2** → Select your instance
   - **Actions** → **Security** → **Modify IAM role**
   - Select the role you created
   - Click **Update IAM role**

### Option C: Environment Variables

```bash
# Add to ~/.bashrc or ~/.bash_profile
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=ap-south-1

# Reload
source ~/.bashrc
```

---

## STEP 4: Test ECR Access

```bash
# Test ECR login
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 480940871468.dkr.ecr.ap-south-1.amazonaws.com

# Should see: "Login Succeeded"

# List repositories
aws ecr describe-repositories --region ap-south-1
```

---

## STEP 5: Verify Workflow Configuration

Check `.github/workflows/main.yml`:

```yaml
AWS_REGION: ap-south-1
ECR_REGISTRY: 480940871468.dkr.ecr.ap-south-1.amazonaws.com
FRONTEND_IMAGE: ${ECR_REGISTRY}/grc_tprm_frontend:latest
BACKEND_IMAGE: ${ECR_REGISTRY}/grc_tprm_backend:latest
```

**Confirm:**
- ✅ Region matches: `ap-south-1`
- ✅ Account ID matches: `480940871468`
- ✅ Repository names match: `grc_tprm_frontend` and `grc_tprm_backend`

---

## STEP 6: ECR Push is Now Enabled

The workflow has been updated to push images to ECR automatically.

**What happens:**
1. Builds Docker images
2. Tags them for ECR
3. Logs into ECR
4. Pushes images to ECR
5. Deploys containers from local images (or can pull from ECR)

---

## Troubleshooting

### "Access Denied" Error

```bash
# Check IAM permissions
aws iam get-user

# Verify ECR access
aws ecr describe-repositories --region ap-south-1
```

**Fix:** Ensure IAM user/role has `AmazonEC2ContainerRegistryFullAccess` policy

### "Repository does not exist"

- Verify repository names match exactly
- Check region is correct
- Verify account ID in URI

### "Login failed"

```bash
# Try manual login
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 480940871468.dkr.ecr.ap-south-1.amazonaws.com
```

---

## Security Best Practices

1. **Use IAM Roles** instead of access keys (more secure)
2. **Enable image scanning** for security vulnerabilities
3. **Use tag immutability** to prevent overwriting images
4. **Set lifecycle policies** to clean up old images
5. **Limit ECR access** to specific IAM users/roles

---

## Lifecycle Policy (Optional)

To automatically delete old images:

```bash
# Create lifecycle policy JSON
cat > lifecycle-policy.json <<EOF
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Keep last 10 images",
      "selection": {
        "tagStatus": "any",
        "countType": "imageCountMoreThan",
        "countNumber": 10
      },
      "action": {
        "type": "expire"
      }
    }
  ]
}
EOF

# Apply to repositories
aws ecr put-lifecycle-policy \
    --repository-name grc_tprm_frontend \
    --lifecycle-policy-text file://lifecycle-policy.json \
    --region ap-south-1

aws ecr put-lifecycle-policy \
    --repository-name grc_tprm_backend \
    --lifecycle-policy-text file://lifecycle-policy.json \
    --region ap-south-1
```

---

## Next Steps

After ECR setup:
1. ✅ Repositories created
2. ✅ AWS credentials configured on EC2
3. ✅ ECR access tested
4. ✅ Workflow updated to push to ECR
5. ✅ Ready to deploy!



