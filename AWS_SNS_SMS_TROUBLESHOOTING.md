# AWS SNS SMS Troubleshooting Guide

## Issue: SMS Not Being Received

If AWS SNS accepts the SMS (returns a MessageId) but you're not receiving it, the most common cause is **AWS SNS Sandbox Mode**.

## Solution 1: Verify Phone Number in AWS SNS (Sandbox Mode)

### Steps:

1. **Go to AWS SNS Console**
   - Navigate to: https://console.aws.amazon.com/sns
   - Make sure you're in the correct region (ap-south-1 for Mumbai)

2. **Verify Your Phone Number**
   - Click on "Text messaging (SMS)" in the left sidebar
   - Click on "Phone numbers" tab
   - Click "Create phone number" button
   - Select your country (India)
   - Enter your phone number: `+919121696189` (or `9121696189`)
   - Click "Create phone number"
   - AWS will send a verification code to your phone
   - Enter the verification code to verify the number

3. **Test Again**
   - After verification, try sending the OTP again
   - The SMS should now be delivered

## Solution 2: Move Out of Sandbox Mode (Production)

If you want to send SMS to any phone number without verification:

1. **Request Production Access**
   - Go to AWS SNS Console
   - Click "Text messaging (SMS)" → "Account preferences"
   - Scroll to "Account spending limit"
   - Click "Request production access"
   - Fill out the form:
     - Use case: "OTP verification for user authentication"
     - Website URL: Your application URL
     - Sample message: "Your GRC Platform OTP for profile editing is 123456. This OTP is valid for 5 minutes."
   - Submit the request
   - AWS will review (usually takes 24-48 hours)

2. **After Approval**
   - You can send SMS to any phone number
   - No need to verify each number individually

## Solution 3: Check SMS Delivery Status

1. **Check CloudWatch Logs**
   - Go to AWS CloudWatch Console
   - Navigate to "Logs" → "Log groups"
   - Look for SNS-related logs
   - Check for delivery failures

2. **Check SNS Metrics**
   - Go to SNS Console → "Text messaging (SMS)" → "Metrics"
   - Check "Number of SMS messages sent" and "Number of SMS messages failed"

## Solution 4: Verify Phone Number Format

The phone number should be in E.164 format:
- ✅ Correct: `+919121696189`
- ❌ Wrong: `9121696189` (missing +)
- ❌ Wrong: `09121696189` (leading zero)

Our code automatically normalizes to E.164 format, so this should be handled automatically.

## Current Status

Based on your logs:
- ✅ SMS was accepted by AWS SNS
- ✅ MessageId: `b91fdfd0-a47b-5962-a822-be693bb6f97d`
- ✅ Phone number normalized correctly: `+919121696189`
- ⚠️ SMS not received (likely sandbox mode issue)

## Quick Fix

**Immediate Solution:**
1. Go to: https://console.aws.amazon.com/sns/v3/home?region=ap-south-1#/mobile/text-messaging/phone-numbers
2. Click "Create phone number"
3. Enter: `+919121696189`
4. Verify the code sent to your phone
5. Try sending OTP again

## Alternative: Use Email Fallback

If SMS continues to fail, the system will automatically fall back to email. The OTP will be sent to the user's email address as a backup.

## Need Help?

- AWS SNS Documentation: https://docs.aws.amazon.com/sns/latest/dg/sns-sms.html
- AWS Support: https://aws.amazon.com/support/

