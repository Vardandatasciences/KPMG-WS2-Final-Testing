# How to Generate WhatsApp Access Token in Meta Developer Console

## Quick Steps Overview

1. Go to Meta Developer Console
2. Select your WhatsApp Business App
3. Navigate to WhatsApp > API Setup
4. Generate a System User Token (permanent) or use Temporary Token
5. Copy the token and Phone Number ID
6. Update in your `sys_params` database table

---

## Detailed Step-by-Step Instructions

### Step 1: Access Meta Developer Console

1. Open your web browser and go to: **https://developers.facebook.com/apps/**
2. Log in with your Meta/Facebook developer account credentials
3. You'll see a list of all your apps

### Step 2: Select Your WhatsApp Business App

1. Find and click on your **WhatsApp Business App** from the list
2. If you don't have an app yet:
   - Click **"Create App"** button
   - Select **"Business"** as the app type
   - Follow the setup wizard to create a WhatsApp Business App

### Step 3: Navigate to WhatsApp API Setup

1. In your app dashboard, look at the left sidebar menu
2. Click on **"WhatsApp"** (under "Products" section)
3. Click on **"API Setup"** (or **"Getting Started"** if it's a new app)

### Step 4: View Your Access Token

On the API Setup page, you'll see:

#### Option A: Temporary Access Token (Quick but Expires)
- Located in **"Step 1: Get started"** section
- Shows a **"Temporary access token"** field
- ⚠️ **Warning**: This token expires in **24 hours** - not recommended for production
- Click **"Copy"** to copy the token

#### Option B: System User Token (Recommended - Permanent)

For a permanent token that doesn't expire, create a System User Token:

1. **Go to Business Settings**:
   - Click on **"Business Settings"** in the top right (or go to https://business.facebook.com/)
   - Or use the dropdown menu in your app dashboard

2. **Navigate to System Users**:
   - In the left sidebar, go to **"Users"** > **"System Users"**
   - Click **"Add"** button to create a new system user (if you don't have one)
   - Give it a name (e.g., "WhatsApp API User")
   - Click **"Create System User"**

3. **Assign System User to Your App**:
   - Click on the system user you just created
   - Go to **"Assign Assets"** tab
   - Click **"Assign Assets"** button
   - Select **"Apps"** from the dropdown
   - Check your WhatsApp Business App
   - Click **"Save Changes"**

4. **Generate Token for System User**:
   - Still in the System User page, go to **"Generate New Token"** button
   - Select your **WhatsApp Business App** from the dropdown
   - Select the following permissions (scopes):
     - ✅ `whatsapp_business_messaging`
     - ✅ `whatsapp_business_management`
   - Click **"Generate Token"**
   - **⚠️ IMPORTANT**: Copy the token immediately - you won't be able to see it again!
   - The token will be a long string starting with `EAAZAFlVKZ...` (200+ characters)

### Step 5: Get Phone Number ID

While you're on the **WhatsApp > API Setup** page:

1. Look for the **"Phone number ID"** field
   - It's a long numeric ID (e.g., `521803094347148`)
   - This is different from your actual phone number
2. Click **"Copy"** to copy the Phone Number ID
3. You'll need this to update the `Phone_Number_ID` field in your `sys_params` table

### Step 6: Update Token in Your Database

You need to update the `Access_Token` and optionally `Phone_Number_ID` in your `sys_params` table.

#### Method 1: Using SQL (Direct Database Update)

```sql
-- Update Access Token (replace YOUR_NEW_TOKEN_HERE with the token you copied)
UPDATE sys_params 
SET Access_Token = 'YOUR_NEW_TOKEN_HERE' 
WHERE Product_Name = 'YOUR_PRODUCT_NAME';

-- Also update Phone Number ID if you have it
UPDATE sys_params 
SET Phone_Number_ID = 'YOUR_PHONE_NUMBER_ID' 
WHERE Product_Name = 'YOUR_PRODUCT_NAME';

-- Verify the update
SELECT Product_Name, 
       LEFT(Access_Token, 20) as Token_Preview, 
       Phone_Number_ID, 
       Phone_Number 
FROM sys_params 
WHERE Access_Token IS NOT NULL;
```

#### Method 2: Using Django Admin or Your Application's Admin Panel

1. Log into your Django admin panel
2. Navigate to `sys_params` table
3. Find the row with your product name
4. Update the `Access_Token` field with the new token
5. Update the `Phone_Number_ID` field if needed
6. Save the changes

### Step 7: Verify the Token Works

1. **Restart your Django application** (if it's running):
   ```bash
   # Stop the server (Ctrl+C) and restart
   python manage.py runserver
   ```

2. **Test sending a WhatsApp message/OTP**:
   - Try the operation that was failing before
   - Check your application logs

3. **Look for success messages**:
   ```
   ✅ Template sent successfully: wamid.xxx
   ```

---

## Visual Guide - What You'll See

### On API Setup Page:
```
┌─────────────────────────────────────────┐
│ WhatsApp > API Setup                    │
├─────────────────────────────────────────┤
│ Step 1: Get started                     │
│                                         │
│ Access tokens                           │
│ ┌─────────────────────────────────────┐ │
│ │ Temporary access token              │ │
│ │ EAAZAFlVKZ...idtsFPon36  [Copy]    │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Phone number ID                          │
│ ┌─────────────────────────────────────┐ │
│ │ 521803094347148            [Copy]   │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### In Business Settings > System Users:
```
┌─────────────────────────────────────────┐
│ System Users                            │
├─────────────────────────────────────────┤
│ [+ Add]                                 │
│                                         │
│ WhatsApp API User                       │
│   [Generate New Token]                  │
│                                         │
│ When generating token:                  │
│   App: Your WhatsApp Business App      │
│   Permissions:                          │
│     ☑ whatsapp_business_messaging      │
│     ☑ whatsapp_business_management     │
│   [Generate Token]                      │
└─────────────────────────────────────────┘
```

---

## Troubleshooting

### ❌ "Error validating access token" (Error 190)
- **Cause**: Token has expired or is invalid
- **Solution**: Generate a new token using the steps above

### ❌ "Token is expired" 
- **Cause**: You're using a temporary token (expires in 24 hours)
- **Solution**: Create a System User Token (permanent) as described in Step 4, Option B

### ❌ "Phone Number ID not found" (Error 100, subcode 33)
- **Cause**: Phone Number ID in database doesn't match your WhatsApp Business Account
- **Solution**: 
  1. Go to WhatsApp > API Setup
  2. Copy the correct Phone Number ID
  3. Update `Phone_Number_ID` in `sys_params` table

### ❌ Can't find "System Users" option
- **Cause**: You might not have Business Manager access
- **Solution**: 
  1. Make sure you're logged into Business Manager: https://business.facebook.com/
  2. You need to be an admin of the Business Account
  3. If you don't have access, ask your Business Manager admin to create the System User Token

### ❌ Token doesn't have required permissions
- **Cause**: Missing WhatsApp permissions
- **Solution**: When generating System User Token, make sure to select:
  - `whatsapp_business_messaging`
  - `whatsapp_business_management`

---

## Security Best Practices

⚠️ **Important Security Notes**:

1. **Never commit tokens to Git**: Access tokens should never be in your code repository
2. **Use System User Tokens for production**: They don't expire, reducing downtime
3. **Store tokens securely**: Keep them in the database (`sys_params` table), not in code
4. **Rotate tokens periodically**: Even permanent tokens should be rotated for security
5. **Limit token access**: Only give token access to trusted team members
6. **Monitor token usage**: Check Meta Developer Console for unusual activity

---

## Quick Reference

| Item | Where to Find |
|------|---------------|
| **Temporary Token** | WhatsApp > API Setup > Step 1 > Temporary access token |
| **System User Token** | Business Settings > Users > System Users > Generate New Token |
| **Phone Number ID** | WhatsApp > API Setup > Phone number ID |
| **Database Table** | `sys_params` table, fields: `Access_Token`, `Phone_Number_ID` |

---

## Need More Help?

- **Meta Developer Documentation**: https://developers.facebook.com/docs/whatsapp/cloud-api/get-started
- **WhatsApp Business API Guide**: https://developers.facebook.com/docs/whatsapp/cloud-api/overview
- **Check your application logs** for detailed error messages
