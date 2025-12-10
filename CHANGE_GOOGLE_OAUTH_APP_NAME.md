# Change Google OAuth Application Name from "ProSync" to "RiskaVaire"

## Issue
The Google OAuth flow is showing "ProSync" instead of "RiskaVaire" when users sign in.

## Solution: Update in Google Cloud Console

The application name is configured in Google Cloud Console, not in the code. Here's how to change it:

### Step-by-Step Instructions:

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Select your project (the one with "ProSync")

2. **Navigate to OAuth Consent Screen**
   - Go to: **APIs & Services** → **OAuth consent screen**
   - This is different from the Credentials page

3. **Edit the Application Information**
   - Find the **"App name"** field
   - Change it from "ProSync" to **"RiskaVaire"**
   - You can also update:
     - **User support email**: Your support email
     - **App logo**: Upload RiskaVaire logo (optional)
     - **Application home page**: Your website URL
     - **Application privacy policy link**: Privacy policy URL
     - **Application terms of service link**: Terms of service URL

4. **Save Changes**
   - Click **"SAVE AND CONTINUE"** at the bottom
   - Go through the remaining steps (Scopes, Test users, etc.)
   - Click **"BACK TO DASHBOARD"** when done

5. **Wait for Changes to Propagate**
   - Changes can take a few minutes to propagate
   - Clear browser cache or use incognito mode
   - Try the Google login again

### Alternative: Create a New OAuth Client

If you want to keep "ProSync" for another project, you can create a new OAuth client:

1. **Go to Credentials**
   - **APIs & Services** → **Credentials**
   - Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**

2. **Create New Client**
   - **Application type**: Web application
   - **Name**: RiskaVaire
   - **Authorized redirect URIs**: 
     - `http://localhost:8000/api/google/oauth-callback/`
     - `https://grc-backend.vardaands.com/api/google/oauth-callback/`

3. **Update Your Environment Variables**
   - Get the new **Client ID** and **Client Secret**
   - Update your `.env` file:
     ```bash
     GOOGLE_CLIENT_ID=your_new_client_id
     GOOGLE_CLIENT_SECRET=your_new_client_secret
     ```

4. **Restart Django Server**
   ```bash
   # Stop and restart
   python manage.py runserver
   ```

## Quick Check: Verify Current App Name

To see what app name is currently configured:

1. Go to: **APIs & Services** → **OAuth consent screen**
2. Look at the **"App name"** field
3. This is what users will see during Google sign-in

## Important Notes

- The app name in the OAuth consent screen is what users see
- You can also customize the logo, privacy policy, and terms of service
- Changes may take a few minutes to appear
- For production, make sure your OAuth consent screen is published (not in testing mode)

## After Making Changes

1. **Wait 2-3 minutes** for Google to update
2. **Clear browser cache** or use incognito mode
3. **Try Google login again**
4. You should now see "RiskaVaire" instead of "ProSync"

