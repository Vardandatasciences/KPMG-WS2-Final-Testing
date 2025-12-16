# AWS SNS SMS Setup Guide

This guide will help you set up AWS SNS (Simple Notification Service) to send SMS messages for OTP verification.

## Prerequisites

1. An AWS account (create one at https://aws.amazon.com if you don't have one)
2. Access to AWS Console

## Step 1: Create an IAM User for SMS Access

1. **Log in to AWS Console**
   - Go to https://console.aws.amazon.com
   - Sign in with your AWS account

2. **Navigate to IAM (Identity and Access Management)**
   - Search for "IAM" in the AWS services search bar
   - Click on "IAM"

3. **Create a New User**
   - Click on "Users" in the left sidebar
   - Click "Create user" button
   - Enter a username (e.g., `grc-sms-service`)
   - Click "Next"

4. **Set Permissions**
   - Select "Attach policies directly"
   - Search for and select: `AmazonSNSFullAccess` (or create a custom policy with only SMS permissions)
   - Click "Next"
   - Review and click "Create user"

5. **Create Access Keys**
   - Click on the newly created user
   - Go to the "Security credentials" tab
   - Scroll down to "Access keys" section
   - Click "Create access key"
   - Select "Application running outside AWS" as the use case
   - Click "Next"
   - Optionally add a description tag
   - Click "Create access key"
   - **IMPORTANT**: Copy both:
     - **Access key ID** (this is your `AWS_ACCESS_KEY_ID`)
     - **Secret access key** (this is your `AWS_SECRET_ACCESS_KEY`)
   - ⚠️ **Save these immediately** - you won't be able to see the secret key again!

## Step 2: Configure AWS SNS for SMS

1. **Navigate to SNS (Simple Notification Service)**
   - Search for "SNS" in AWS services
   - Click on "Simple Notification Service"

2. **Set SMS Preferences (Optional but Recommended)**
   - Click on "Text messaging (SMS)" in the left sidebar
   - Click on "Preferences"
   - Configure:
     - **Default message type**: Transactional
     - **Default sender ID**: Your company name (optional)
     - **Spending limit**: Set a monthly limit to prevent unexpected charges
   - Click "Save changes"

3. **Verify Phone Number (For Testing)**
   - Go to "Text messaging (SMS)" → "Phone numbers"
   - Click "Create phone number"
   - Select your country and phone number type
   - Follow the verification process

## Step 3: Get Your AWS Region

Your AWS region is typically:
- **ap-south-1** (Mumbai, India) - if you're in India
- **us-east-1** (N. Virginia, USA) - default region
- **eu-west-1** (Ireland) - for Europe
- **ap-southeast-1** (Singapore) - for Southeast Asia

You can find your region in the top-right corner of the AWS Console.

## Step 4: Set Environment Variables

### Option A: Set in your `.env` file (Recommended for Development)

Create or edit `.env` file in your project root:

```env
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=ap-south-1
```

### Option B: Set in Windows Environment Variables

1. Press `Win + R`, type `sysdm.cpl`, press Enter
2. Click "Environment Variables"
3. Under "User variables", click "New"
4. Add each variable:
   - Variable name: `AWS_ACCESS_KEY_ID`
   - Variable value: `your_access_key_id`
5. Repeat for `AWS_SECRET_ACCESS_KEY` and `AWS_REGION`

### Option C: Set in Django Settings (Not Recommended for Production)

Edit `grc_backend/backend/settings.py`:

```python
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', 'your_access_key_here')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', 'your_secret_key_here')
AWS_REGION = os.environ.get('AWS_REGION', 'ap-south-1')
```

## Step 5: Install Required Python Package

```bash
pip install boto3
```

Or add to `requirements.txt`:
```
boto3>=1.26.0
```

## Step 6: Test SMS Sending

After setting up, restart your Django server and test the OTP functionality. The SMS should be sent to the user's phone number.

## Cost Information

- **AWS SNS SMS Pricing**: 
  - India: ~₹0.50-1.00 per SMS
  - USA: ~$0.00645 per SMS
  - Prices vary by country
  - Check current pricing: https://aws.amazon.com/sns/sms/pricing/

## Security Best Practices

1. **Never commit credentials to Git**
   - Add `.env` to `.gitignore`
   - Use environment variables or AWS Secrets Manager

2. **Use IAM Roles in Production**
   - For production, use IAM roles instead of access keys
   - Access keys should only be used for development

3. **Set Spending Limits**
   - Configure spending limits in SNS to prevent unexpected charges
   - Monitor usage in AWS CloudWatch

4. **Rotate Access Keys Regularly**
   - Change access keys every 90 days
   - Delete unused access keys

## Troubleshooting

### Error: "Unable to locate credentials"
- Check that environment variables are set correctly
- Restart your Django server after setting environment variables
- Verify the credentials in AWS IAM

### Error: "User is not authorized to perform: SNS:Publish"
- Ensure the IAM user has `AmazonSNSFullAccess` policy or appropriate SNS permissions

### SMS Not Received
- Check phone number format (should be in E.164 format: +919876543210)
- Verify the phone number in SNS console
- Check AWS CloudWatch logs for errors
- Ensure you're not in SMS sandbox mode (if applicable)

## Alternative: Use AWS Secrets Manager (Production)

For production, consider using AWS Secrets Manager:

```python
import boto3
import json

def get_aws_credentials():
    client = boto3.client('secretsmanager', region_name='ap-south-1')
    secret = client.get_secret_value(SecretId='grc-sms-credentials')
    return json.loads(secret['SecretString'])
```

## Support

- AWS SNS Documentation: https://docs.aws.amazon.com/sns/
- AWS Support: https://aws.amazon.com/support/

