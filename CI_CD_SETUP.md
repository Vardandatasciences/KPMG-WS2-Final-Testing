# CI/CD Setup Guide

This document explains the GitHub Actions workflows for continuous integration and deployment.

## Overview

Your repository now has three GitHub Actions workflows:

### 1. **CI - Backend & Frontend** (`.github/workflows/ci.yml`)
**Triggers:** Push to any branch, Pull Requests to main/master/develop

**What it does:**
- **Backend CI:**
  - Sets up Python 3.11
  - Installs system dependencies (MySQL, Tesseract, etc.)
  - Installs Python dependencies from `grc_backend/requirements.txt`
  - Runs `flake8` for Python linting
  - Runs `black` for code formatting checks
  - Runs `isort` for import sorting checks
  - Performs Django system check
  - Runs Django tests

- **Frontend CI:**
  - Sets up Node.js 18
  - Installs npm dependencies for both main frontend and TPRM
  - Runs ESLint
  - Builds the frontend for production
  - Verifies build output
  - Builds TPRM frontend

- **Security Scanning:**
  - Runs Trivy vulnerability scanner on backend and frontend
  - Uploads results to GitHub Security tab

### 2. **PR Checks** (`.github/workflows/pr-checks.yml`)
**Triggers:** Pull Requests to main/master/develop

**What it does:**
- **Code Quality:**
  - Checks Python formatting with black
  - Checks import sorting with isort
  - Runs basic Python linting with flake8

- **Frontend Lint:**
  - Runs ESLint on the frontend code

- **Bundle Size Check:**
  - Builds the frontend
  - Reports bundle sizes to detect regressions

### 3. **CI/CD - GRC & TPRM** (`.github/workflows/main.yml`)
**Triggers:** Push to main/master branches, Manual workflow dispatch

**What it does:**
- **Setup:** Creates Docker network
- **Backend Build & Deploy:**
  - Builds Docker image for backend
  - Tags and pushes to AWS ECR
  - Deploys container to self-hosted runner
  - Performs health checks
- **Verification:** Tests API endpoints and shows container logs

## How to Use

### For Developers

#### 1. **Local Development**
Before pushing code, run these commands locally to catch issues early:

**Backend:**
```bash
cd grc_backend
# Format code
black .
isort .
# Lint code
flake8 .
# Run tests
python manage.py test
# Django check
python manage.py check --deploy
```

**Frontend:**
```bash
cd grc_frontend
# Install dependencies
npm install
# Lint code
npm run lint
# Build for production
npm run build
```

#### 2. **Creating Pull Requests**
When you create a PR:
- The **PR Checks** workflow will run automatically
- It will check code quality, linting, and bundle size
- Address any failures before merging

#### 3. **Pushing Changes**
When you push to any branch:
- The **CI** workflow will run full tests
- This includes backend tests, frontend build, and security scans
- All checks must pass for the code to be merge-ready

#### 4. **Merging to Main/Master**
When you merge to main or master:
- The **CI/CD** workflow will deploy to production
- It builds Docker images and deploys to your self-hosted runner
- You can also trigger this manually from the Actions tab

### For Administrators

#### Required GitHub Secrets
The existing `main.yml` workflow requires these secrets to be configured in GitHub:

1. **AWS Credentials** (for ECR access):
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION` (set to `ap-south-1` in workflow)

To add secrets:
1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each secret with its value

#### Self-Hosted Runner Setup
The `main.yml` workflow uses a self-hosted runner. Ensure:
1. The runner is registered in your repository settings
2. Docker is installed on the runner
3. AWS CLI is configured with ECR permissions
4. The `/home/ec2-user/config.env` file exists with environment variables
5. Volume mounts exist: `/home/ec2-user/MEDIA_ROOT`, `/home/ec2-user/TEMP_MEDIA_ROOT`, `/home/ec2-user/Reports`

## Customizing the Workflows

### Changing Python/Node Versions
Edit the `env` section in the workflow files:
```yaml
env:
  PYTHON_VERSION: '3.11'  # Change as needed
  NODE_VERSION: '18'      # Change as needed
```

### Adding More Tests
Add test commands in the backend-ci job:
```yaml
- name: Run custom tests
  working-directory: ./grc_backend
  run: |
    python manage.py test your_app.tests
```

### Skipping Linting
To skip linting checks temporarily (not recommended), add `[skip ci]` to your commit message:
```bash
git commit -m "Your message [skip ci]"
```

### Adding Branch Protection Rules
To enforce CI checks before merging:
1. Go to repository Settings → Branches
2. Add or edit a branch protection rule for main/master
3. Enable:
   - "Require status checks to pass before merging"
   - Select the required workflows (CI, PR Checks)
   - "Require branches to be up to date before merging"

## Troubleshooting

### Backend Tests Failing
- Check if all dependencies are in `requirements.txt`
- Ensure database migrations are up to date
- Verify Django settings are correct for CI environment

### Frontend Build Failing
- Check if `package.json` is correct
- Ensure all dependencies are installable
- Verify build script in `package.json`

### Security Scanning Failures
- Review the security tab in GitHub
- Update vulnerable dependencies
- False positives can be ignored if necessary

### Deployment Failures
- Check if AWS credentials are valid
- Verify ECR repository exists
- Ensure self-hosted runner is online
- Check Docker logs in the workflow output

## Monitoring

### Viewing Workflow Runs
1. Go to the "Actions" tab in your repository
2. Click on a workflow to see its history
3. Click on a run to see detailed logs

### Workflow Status Badge
Add this badge to your README.md:
```markdown
![CI](https://github.com/YOUR_USERNAME/YOUR_REPO/workflows/CI%20-%20Backend%20%26%20Frontend/badge.svg)
```

## Best Practices

1. **Run locally first:** Always run linting and tests locally before pushing
2. **Small PRs:** Keep pull requests small and focused for faster CI
3. **Descriptive commits:** Use clear commit messages to help with debugging
4. **Review logs:** Check workflow logs when something fails
5. **Keep dependencies updated:** Regularly update dependencies to avoid security issues
6. **Use branches:** Create feature branches instead of committing directly to main

## Next Steps

- Add unit tests to increase test coverage
- Set up code coverage reporting
- Add integration tests
- Configure branch protection rules
- Set up Slack/Discord notifications for workflow failures
- Add staging environment deployment
- Implement automated rollback on deployment failures
