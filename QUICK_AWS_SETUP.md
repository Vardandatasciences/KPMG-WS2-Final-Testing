# Quick AWS SNS Setup Guide

## Step-by-Step Instructions

### 1. Create AWS Account (if you don't have one)
- Go to https://aws.amazon.com
- Click "Create an AWS Account"
- Follow the registration process

### 2. Get AWS Credentials

#### A. Create IAM User
1. Log in to AWS Console: https://console.aws.amazon.com
2. Search for "IAM" in the top search bar
3. Click "Users" → "Create user"
4. Username: `grc-sms-service` (or any name you prefer)
5. Click "Next"

#### B. Attach Permissions
1. Select "Attach policies directly"
2. Search for: `AmazonSNSFullAccess`
3. Check the box next to it
4. Click "Next" → "Create user"

#### C. Create Access Keys
1. Click on the user you just created
2. Go to "Security credentials" tab
3. Scroll to "Access keys" section
4. Click "Create access key"
5. Select "Application running outside AWS"
6. Click "Next" → "Create access key"
7. **COPY BOTH VALUES NOW** (you won't see the secret key again):
   - **Access key ID** → This is your `AWS_ACCESS_KEY_ID`
   - **Secret access key** → This is your `AWS_SECRET_ACCESS_KEY`

### 3. Get Your AWS Region
- Look at the top-right corner of AWS Console
- You'll see something like "N. Virginia" or "Mumbai"
- Common regions:
  - **ap-south-1** = Mumbai, India
  - **us-east-1** = N. Virginia, USA
  - **eu-west-1** = Ireland
  - **ap-southeast-1** = Singapore

### 4. Configure SNS for SMS
1. Search for "SNS" in AWS Console
2. Click "Simple Notification Service"
3. Click "Text messaging (SMS)" in left sidebar
4. Click "Preferences"
5. Set:
   - Default message type: **Transactional**
   - Spending limit: Set a monthly limit (e.g., $10)
6. Click "Save changes"

### 5. Add Credentials to Your Project

#### Option 1: Add to .env file (Recommended)
Create or edit `.env` file in `grc_backend/` directory:

```env
# AWS SNS Configuration for SMS
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=ap-south-1
```

**Replace the example values with your actual credentials!**

#### Option 2: Windows Environment Variables
1. Press `Win + X` → "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "User variables", click "New"
5. Add:
   - Name: `AWS_ACCESS_KEY_ID`, Value: `your_access_key`
   - Name: `AWS_SECRET_ACCESS_KEY`, Value: `your_secret_key`
   - Name: `AWS_REGION`, Value: `ap-south-1`

### 6. Install boto3 Package
```bash
cd grc_backend
pip install boto3
```

Or add to `requirements.txt`:
```
boto3>=1.26.0
```

### 7. Restart Django Server
After adding credentials, restart your Django development server:
```bash
python manage.py runserver
```

### 8. Test It!
Try sending an OTP from your application. The SMS should be sent to the phone number.

## Important Notes

⚠️ **Security:**
- Never commit `.env` file to Git
- Keep your secret key secure
- Set spending limits in AWS SNS

💰 **Cost:**
- SMS costs vary by country (~₹0.50-1.00 per SMS in India)
- Set spending limits to avoid unexpected charges

🔍 **Troubleshooting:**
- If SMS doesn't work, check AWS CloudWatch logs
- Verify phone number format: +919876543210 (E.164 format)
- Ensure IAM user has SNS permissions

## Need Help?

- AWS SNS Docs: https://docs.aws.amazon.com/sns/
- AWS Support: https://aws.amazon.com/support/

