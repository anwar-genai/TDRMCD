# JaaS (Jitsi as a Service) Setup Instructions

## Quick Setup

1. **Create a `.env` file** in the root directory (D:\clients\)

2. **Copy this content to your `.env` file:**

```env
# Flask Configuration
SECRET_KEY=dev-secret-key-change-in-production-2024
DATABASE_URL=sqlite:///tdrmcd.db

# Mail Configuration (Optional - leave empty if not using email)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=

# JaaS Configuration - REPLACE THESE WITH YOUR ACTUAL VALUES
JITSI_APP_ID=YOUR_JAAS_APP_ID_HERE
JITSI_APP_SECRET=YOUR_JAAS_PRIVATE_KEY_HERE
```

3. **Replace the JaaS values:**
   - Replace `YOUR_JAAS_APP_ID_HERE` with your actual JaaS App ID
   - Replace `YOUR_JAAS_PRIVATE_KEY_HERE` with your actual JaaS Private Key

## Getting Your JaaS Credentials

1. Go to https://jaas.8x8.vc/
2. Sign in to your account
3. Go to your app settings
4. You'll find:
   - **App ID**: Something like `vpaas-magic-cookie-1234567890abcdef/`
   - **Private Key**: A long string used for JWT signing

## Example .env with Real Values

```env
JITSI_APP_ID=vpaas-magic-cookie-1234567890abcdef
JITSI_APP_SECRET=your-long-private-key-from-jaas-dashboard
```

## Important Notes

- The App ID should NOT include the trailing slash
- The Private Key is used to sign JWT tokens for authentication
- Keep your Private Key secret - never commit it to version control
- The app will automatically detect JaaS configuration and use it

## Features Enabled with JaaS

When properly configured, you'll get:
- ✅ Secure, authenticated meetings
- ✅ Host moderation controls
- ✅ Better video quality
- ✅ Meeting analytics (in JaaS dashboard)
- ✅ Custom branding options
- ✅ Recording capabilities (if enabled in JaaS)

## Troubleshooting

If video calls aren't working after setup:

1. **Check the browser console** for errors
2. **Verify your App ID** doesn't have trailing slashes or spaces
3. **Ensure the Private Key** is copied completely
4. **Restart the Flask application** after updating .env

## Testing

After setting up:
1. Restart your Flask application
2. Create a new video call
3. Check the browser console - it should show "Initializing Jitsi Meet (JaaS mode)..."
4. The room name should start with `vpaas-magic-cookie-YOUR_APP_ID/`

If you see "Initializing Jitsi Meet (Public mode)..." instead, the JaaS configuration wasn't detected.
