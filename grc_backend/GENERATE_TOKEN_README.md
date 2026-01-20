# Session Token Generator for Postman Testing

This script generates JWT session tokens for API testing in Postman by authenticating with username and password.

## Location
`grc_backend/generate_session_token.py`

## Usage

### Step 1: Configure Credentials
Open `generate_session_token.py` and edit the configuration variables at the top:

```python
# ============================================================================
# CONFIGURATION - Edit these variables with your credentials
# ============================================================================
USERNAME = "your_username_here"  # Enter your username or email
PASSWORD = "your_password_here"   # Enter your password
LOGIN_TYPE = "username"           # Use "username" or "userid"
# ============================================================================
```

**Example:**
```python
USERNAME = "priya.gupta"
PASSWORD = "mypassword123"
LOGIN_TYPE = "username"  # or "userid" if using User ID
```

### Step 2: Run the Script
```bash
cd grc_backend
python generate_session_token.py
```

## What It Does

1. **Authenticates** the user with username/email and password
2. **Generates JWT tokens**:
   - Access Token (for API requests)
   - Refresh Token (for token refresh)
   - Session Token (UUID)
3. **Prints tokens** in a Postman-friendly format

## Output

The script will output:
- ✅ Access Token (use in Authorization header)
- ✅ Refresh Token
- ✅ Session Token (UUID)
- ✅ Token expiry information
- ✅ Postman setup instructions

## Using in Postman

1. Copy the **Access Token** from the output
2. In Postman, go to your request
3. Click on the **Authorization** tab
4. Select **Bearer Token** as the Type
5. Paste the access token in the Token field

Or manually add header:
- **Key**: `Authorization`
- **Value**: `Bearer <access_token>`

## Notes

- ⚠️ This script bypasses CAPTCHA, rate limiting, MFA, and license checks for testing purposes
- ⚠️ **Security Note**: Credentials are stored in plain text in the script file. Do not commit this file to version control with real credentials!
- ✅ The script handles both hashed and plain-text passwords (migrates plain-text to hashed)
- ✅ Works with encrypted usernames in the database
- ✅ Simple configuration - just edit the variables at the top of the file

## Troubleshooting

**Authentication Failed**
- Check username/password is correct
- Verify user exists in database
- Check if user account is active

**Import Errors**
- Make sure you're running from `grc_backend` directory
- Ensure Django settings are configured correctly
- Check that all dependencies are installed

**Token Generation Errors**
- Verify user has required fields (UserId, UserName, etc.)
- Check database connection
- Review error messages for specific issues
