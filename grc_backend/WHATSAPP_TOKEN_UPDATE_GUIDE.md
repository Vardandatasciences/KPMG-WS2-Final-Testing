# WhatsApp Access Token Update Guide

## Problem
Your WhatsApp access token has expired. Error code 190 indicates the token session has expired and needs to be regenerated.

## Solution: Generate New Access Token

### Step 1: Access Meta Developer Console

1. Go to [https://developers.facebook.com/apps/](https://developers.facebook.com/apps/)
2. Log in with your Meta/Facebook developer account
3. Select your **WhatsApp Business App** from the list

### Step 2: Navigate to API Setup

1. In your app dashboard, go to **WhatsApp** in the left sidebar
2. Click on **API Setup** (or **Getting Started**)
3. You'll see your **Temporary Access Token** or **System User Token**

### Step 3: Generate Permanent Token (Recommended)

For production use, you should create a **System User Token** which doesn't expire:

1. Go to **WhatsApp** > **API Setup**
2. Scroll down to **"Step 1: Get started"**
3. Under **"Access tokens"**, you'll see options:
   - **Temporary token** (expires in 24 hours) - Not recommended for production
   - **System User Token** (permanent) - Recommended

#### To Create System User Token:

1. Go to **Business Settings** > **Users** > **System Users**
2. Click **Add** to create a new system user (if you don't have one)
3. Assign the system user to your WhatsApp Business App
4. Generate a token for the system user with these permissions:
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
5. Copy the generated token (it will be long, starting with something like `EAAZAFlVKZ...`)

### Step 4: Get Phone Number ID (if needed)

While you're in the API Setup page:
1. Look for **"Phone number ID"** - it's a long numeric ID
2. Copy this ID as well (you may need to update `Phone_Number_ID` in `sys_params`)

### Step 5: Update Token in Database

You have two options to update the token:

#### Option A: Using Python Script (Recommended)

Run the provided script:
```bash
cd grc_backend
python update_whatsapp_token.py
```

The script will prompt you for:
- New access token
- Product name (optional, if you have multiple WhatsApp configurations)
- Phone Number ID (optional, will try to auto-detect if not provided)

#### Option B: Manual SQL Update

1. Connect to your MySQL database
2. Run the following SQL:

```sql
-- If you know the Product_Name
UPDATE sys_params 
SET Access_Token = 'YOUR_NEW_TOKEN_HERE' 
WHERE Product_Name = 'YOUR_PRODUCT_NAME';

-- OR if you want to update by existing token
UPDATE sys_params 
SET Access_Token = 'YOUR_NEW_TOKEN_HERE' 
WHERE Access_Token = 'OLD_TOKEN_HERE'
LIMIT 1;

-- Also update Phone Number ID if you have it
UPDATE sys_params 
SET Phone_Number_ID = 'YOUR_PHONE_NUMBER_ID' 
WHERE Product_Name = 'YOUR_PRODUCT_NAME';
```

3. Verify the update:
```sql
SELECT Product_Name, Access_Token, Phone_Number_ID, Phone_Number 
FROM sys_params 
WHERE Access_Token IS NOT NULL;
```

### Step 6: Verify Token Works

1. Restart your Django application (if needed)
2. Try sending a WhatsApp message/OTP again
3. Check the logs - you should see:
   ```
   ✅ Template sent successfully: wamid.xxx
   ```

## Troubleshooting

### Token Still Not Working?

1. **Check token format**: Should be a long string (200+ characters), starting with `EAA...`
2. **Verify permissions**: Token must have `whatsapp_business_messaging` permission
3. **Check Phone Number ID**: Ensure `Phone_Number_ID` in `sys_params` matches your WhatsApp Business Account
4. **Token expiration**: System User Tokens don't expire, but temporary tokens expire in 24 hours

### Phone Number ID Issues?

If you get error code 100 with subcode 33:
1. Go to [Meta Business Manager](https://business.facebook.com/)
2. Select your WhatsApp Business Account
3. Go to **Settings** > **Phone Numbers**
4. Click on your phone number
5. Copy the **Phone Number ID** (numeric ID)
6. Update `Phone_Number_ID` in `sys_params` table

### Still Having Issues?

1. Check application logs for detailed error messages
2. Verify your WhatsApp Business App is in production mode (not development)
3. Ensure your phone number is verified in Meta Business Manager
4. Check that your app has the necessary permissions approved

## Security Notes

⚠️ **Important**: 
- Never commit access tokens to version control
- Store tokens securely in the database
- Use System User Tokens for production (they don't expire)
- Rotate tokens periodically for security best practices
