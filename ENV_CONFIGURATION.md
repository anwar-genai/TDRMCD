# Environment Configuration

Create a `.env` file in the root directory with the following configuration:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///tdrmcd.db

# Mail Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Jitsi Video Call Configuration (Optional)
# To enable JWT authentication and moderation features in video calls,
# you need to set up a Jitsi server with JWT authentication or use 
# Jitsi as a Service (JaaS) from 8x8.
# 
# For JaaS: Sign up at https://jaas.8x8.vc/ to get your App ID and Secret
# For self-hosted: Configure your Jitsi server with JWT authentication
#
# Leave these empty to use public Jitsi Meet rooms without authentication
JITSI_APP_ID=
JITSI_APP_SECRET=
```

## Video Call Configuration

The video call feature uses Jitsi Meet for WebRTC video conferencing. It works in two modes:

1. **Public Mode (Default)**: No configuration needed. Uses public Jitsi Meet servers.
2. **Authenticated Mode**: Requires JITSI_APP_ID and JITSI_APP_SECRET for JWT authentication.

### Benefits of Authenticated Mode:
- Host moderation controls
- Better security and privacy
- Custom branding options
- Meeting recording capabilities (if enabled on your Jitsi server)

### How to Get Jitsi Credentials:

#### Option 1: Jitsi as a Service (JaaS) - Recommended
1. Visit https://jaas.8x8.vc/
2. Sign up for a free account
3. Create an application
4. Copy your App ID and Secret to the .env file

#### Option 2: Self-Hosted Jitsi Server
1. Deploy your own Jitsi Meet server
2. Configure JWT authentication
3. Use your server's App ID and Secret

The application will work without these credentials, but some features like host moderation will be limited.
