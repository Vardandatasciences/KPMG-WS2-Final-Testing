# Production Deployment Safety Guide ⚠️

## Understanding the Risk

**Production deployment means:**
- Your live users will experience 2-5 minutes downtime
- If something goes wrong, your site could be broken
- Database errors could occur
- Need rollback plan ready

## Safe Deployment Options

### Option 1: Manual Deployment Only (Recommended for now)
```bash
# Disable automatic deployment
# Rename .github/workflows/deploy.yml to .github/workflows/deploy.yml.disabled
```

Now you control when to deploy:
1. Push code to test in CI
2. When ready, manually run deployment from Actions tab

### Option 2: Branch Protection (Safer)
Require pull requests before merging to main:
1. Go to **Settings → Branches → Add rule**
2. Protect `main` branch
3. Require PRs and approvals
4. Require CI checks to pass

### Option 3: Staging Environment (Safest)
Deploy to staging first:
```bash
# Create staging branch
git checkout -b staging
git push origin staging
```

## Current Deployment Flow with Safety

### 1. Automatic (Push to Main)
```
Push to main → CI runs → Auto-deploys → 2-5 min downtime
```

### 2. Manual (Recommended)
```
Push to main → CI runs → You manually deploy → Controlled downtime
```

## Manual Deployment Steps

### Step 1: Push Code
```bash
git add .
git commit -m "your changes"
git push origin main
```

### Step 2: Wait for CI
- Go to **Actions** tab
- Wait for "CI - Backend & Frontend" to complete ✅
- Fix any CI failures before deploying

### Step 3: Manual Deploy
1. Go to **Actions** tab
2. Click **"Deploy to Hostinger"** workflow
3. Click **"Run workflow"**
4. Type **"DEPLOY"** to confirm
5. Watch deployment progress

### Step 4: Verify
- Check your site: `http://YOUR_HOSTINGER_IP:8081`
- Check backend: `http://YOUR_HOSTINGER_IP:8001`
- Test key functionality

## Emergency Rollback Plan

### If Deployment Fails:
```bash
# SSH into your server
ssh your_username@YOUR_HOSTINGER_IP

# Go to deployment directory
cd /home/grc-app

# Check recent commits
git log --oneline -10

# Rollback to previous working commit
git checkout PREVIOUS_COMMIT_HASH

# Rebuild and restart
docker compose -f deploy/docker-compose.production.yml down
docker compose -f deploy/docker-compose.production.yml up -d --build
```

### Quick Rollback Commands:
```bash
# Get previous commit hash
git log --oneline -2

# Rollback (replace HASH with previous commit)
git checkout abc1234
docker compose -f deploy/docker-compose.production.yml down
docker compose -f deploy/docker-compose.production.yml up -d --build
```

## Pre-Deployment Checklist

Before deploying to production:

### Code Quality:
- [ ] CI checks pass
- [ ] No critical bugs in code
- [ ] Tested locally

### Database Safety:
- [ ] Database backups enabled
- [ ] Migration scripts tested
- [ ] Rollback plan ready

### Communication:
- [ ] Notify users about maintenance
- [ ] Schedule deployment during low traffic
- [ ] Have contact info ready

### Technical:
- [ ] Server disk space available
- [ ] Docker images can build
- [ ] Ports 8001/8081 available

## What Gets Preserved During Deployment

✅ **Safe (won't be lost):**
- Database data
- User uploads (MEDIA_ROOT)
- Reports
- Environment variables (.env)

❌ **Updated (will change):**
- Application code
- Docker images
- Frontend build
- Backend logic

## Monitoring During Deployment

### Watch these logs:
```bash
# On your server
cd /home/grc-app
docker compose -f deploy/docker-compose.production.yml logs -f
```

### Check these URLs:
- Frontend: `http://YOUR_IP:8081`
- Backend health: `http://YOUR_IP:8001/health/`

## Recommended Safe Workflow

### For Now (Recommended):
1. **Disable auto-deploy**: Rename `deploy.yml` to `deploy.yml.disabled`
2. **Push code**: Test with CI only
3. **Manual deploy**: Use Actions tab when ready
4. **Monitor**: Watch logs and test functionality

### Later (When comfortable):
1. Enable auto-deploy with manual approval
2. Add staging environment
3. Implement blue-green deployment

## Emergency Contacts

Keep this info handy:
- Hostinger support
- Database credentials
- Server SSH access
- Rollback commands

## Quick Decision Tree

```
Is this a critical bug fix?
├─ Yes → Deploy immediately (manual)
└─ No → Wait for maintenance window

Has CI passed?
├─ Yes → Proceed to deployment
└─ No → Fix CI issues first

Is it peak traffic time?
├─ Yes → Wait for low traffic
└─ No → Deploy now
```

## Final Safety Tips

1. **Always test locally first**
2. **Never deploy on Friday afternoon**
3. **Keep previous commit hash handy**
4. **Have rollback commands ready**
5. **Monitor after deployment**
6. **Communicate with users**

## Your Current Setup

- ✅ CI checks code quality
- ⚠️ Manual approval required for workflow dispatch
- ⚠️ Auto-deploy on push to main (can be disabled)
- ✅ Simple rollback with git checkout

**Recommendation**: Start with manual deployment only, enable auto-deploy when comfortable.
