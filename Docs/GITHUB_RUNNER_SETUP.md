# GitHub Actions Self-Hosted Runner Setup Guide

## Step-by-Step Instructions for EC2 Instance

---

## STEP 1: Connect to EC2 Instance

```bash
# SSH into your EC2 instance
ssh -i your-key.pem ec2-user@your-ec2-ip
```

---

## STEP 2: Download and Install Runner

### A. Create a folder for the runner

```bash
# Create directory for runner
mkdir -p ~/actions-runner
cd ~/actions-runner
```

### B. Download the latest runner package

**For Linux x64:**
```bash
# Download the latest runner package
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract the installer
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz
```

**Note:** Check for the latest version at: https://github.com/actions/runner/releases

---

## STEP 3: Configure the Runner

### A. Get Runner Registration Token

1. Go to your GitHub repository
2. Click **Settings** → **Actions** → **Runners**
3. Click **New self-hosted runner**
4. Select **Linux** and **x64**
5. Copy the **registration token** (looks like: `AXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`)

### B. Configure the runner

```bash
# Run the configuration script
./config.sh --url https://github.com/YOUR_USERNAME/YOUR_REPO --token YOUR_REGISTRATION_TOKEN
```

**Replace:**
- `YOUR_USERNAME` - Your GitHub username or organization
- `YOUR_REPO` - Your repository name (e.g., `GRC_TPRM`)
- `YOUR_REGISTRATION_TOKEN` - The token you copied

**Example:**
```bash
./config.sh --url https://github.com/yourusername/GRC_TPRM --token AXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### C. Configuration Questions

You'll be asked several questions:

1. **Enter the name of the runner:**
   ```
   [Press Enter for default: EC2-Instance]
   ```
   Or type a custom name like: `grc-tprm-ec2`

2. **Enter the name of the work folder:**
   ```
   [Press Enter for default: _work]
   ```

3. **Enter additional labels (press Enter for none):**
   ```
   [Press Enter for none, or add custom labels]
   ```

4. **Enter name of the runner group:**
   ```
   [Press Enter for default]
   ```

---

## STEP 4: Install Runner as a Service (Recommended)

This ensures the runner starts automatically and runs in the background.

### A. Install as a service

```bash
# Install the service
sudo ./svc.sh install

# Start the service
sudo ./svc.sh start

# Check status
sudo ./svc.sh status
```

### B. Verify service is running

```bash
# Check service status
sudo systemctl status actions.runner.*
```

You should see:
```
● actions.runner.*.service - GitHub Actions Runner
   Loaded: loaded
   Active: active (running)
```

---

## STEP 5: Verify Runner is Online

1. Go to GitHub repository
2. Click **Settings** → **Actions** → **Runners**
3. You should see your runner listed with a **green dot** (online)

---

## STEP 6: Test the Runner

### Option A: Manual Test Run

```bash
# Run the runner manually (for testing)
cd ~/actions-runner
./run.sh
```

**Note:** This runs in foreground. Press `Ctrl+C` to stop. For production, use the service.

### Option B: Trigger a Workflow

1. Push a small change to your repository
2. Go to **Actions** tab in GitHub
3. Watch the workflow run
4. Check if it uses your self-hosted runner

---

## STEP 7: Configure Runner Permissions (if needed)

### A. Ensure Docker access

```bash
# Add runner user to docker group (if not already)
sudo usermod -aG docker $USER

# If runner runs as different user, add that user:
sudo usermod -aG docker actions-runner
```

### B. Verify Docker access

```bash
# Test Docker access
docker ps
```

---

## Common Commands

### Start/Stop/Status

```bash
# Start service
sudo ./svc.sh start

# Stop service
sudo ./svc.sh stop

# Restart service
sudo ./svc.sh restart

# Check status
sudo ./svc.sh status

# View logs
sudo journalctl -u actions.runner.* -f
```

### Uninstall Runner

```bash
# Stop service
sudo ./svc.sh stop
sudo ./svc.sh uninstall

# Remove files
cd ~
rm -rf actions-runner
```

---

## Troubleshooting

### Runner not showing as online

1. **Check service status:**
   ```bash
   sudo systemctl status actions.runner.*
   ```

2. **Check logs:**
   ```bash
   sudo journalctl -u actions.runner.* -n 50
   ```

3. **Restart service:**
   ```bash
   sudo ./svc.sh stop
   sudo ./svc.sh start
   ```

### Runner can't access Docker

```bash
# Check Docker group membership
groups

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and log back in, or:
newgrp docker

# Verify
docker ps
```

### Runner can't access files

```bash
# Check permissions
ls -la ~/actions-runner

# Fix permissions if needed
chmod +x ~/actions-runner/*.sh
```

### Workflow fails with "runs-on: self-hosted"

- Verify runner label matches: `runs-on: self-hosted`
- Check runner is online in GitHub
- Check runner logs for errors

---

## Security Best Practices

1. **Limit runner to specific repositories** (if using organization)
2. **Use least privilege** for runner user
3. **Keep runner updated:**
   ```bash
   cd ~/actions-runner
   ./run.sh --update
   ```
4. **Monitor runner logs regularly**
5. **Use secrets for sensitive data** (don't hardcode in workflows)

---

## Quick Setup Script

Save this as `setup-runner.sh` and run it:

```bash
#!/bin/bash

# GitHub Runner Setup Script
REPO_URL="https://github.com/YOUR_USERNAME/YOUR_REPO"
TOKEN="YOUR_REGISTRATION_TOKEN"

# Create directory
mkdir -p ~/actions-runner
cd ~/actions-runner

# Download runner
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Configure
./config.sh --url $REPO_URL --token $TOKEN

# Install service
sudo ./svc.sh install
sudo ./svc.sh start

# Check status
sudo ./svc.sh status

echo "Runner setup complete! Check GitHub repository → Settings → Actions → Runners"
```

**Make it executable and run:**
```bash
chmod +x setup-runner.sh
./setup-runner.sh
```

---

## Next Steps After Runner Setup

1. ✅ Verify runner is online in GitHub
2. ✅ Test with a simple workflow
3. ✅ Ensure Docker is accessible
4. ✅ Create ECR repositories (if using ECR)
5. ✅ Create `/home/ec2-user/config.env`
6. ✅ Create volume directories
7. ✅ Push to git and watch deployment!

---

## Need Help?

- Check runner logs: `sudo journalctl -u actions.runner.* -f`
- GitHub Actions docs: https://docs.github.com/en/actions/hosting-your-own-runners
- Runner releases: https://github.com/actions/runner/releases



