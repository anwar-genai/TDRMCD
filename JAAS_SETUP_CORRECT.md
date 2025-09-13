# ✅ CORRECT JaaS Setup Guide (Based on Official Documentation)

## 🚨 **Critical Missing Step: Key ID (`kid`)**

The "not allowed to join" error is caused by missing the **Key ID** in the JWT header, which is required by JaaS for authentication validation.

## 📋 **Complete Setup Process:**

### Step 1: Generate RSA Key Pair
```bash
# Generate private key
ssh-keygen -t rsa -b 4096 -m PEM -f jaasauth.key

# Generate public key in PEM format
openssl rsa -in jaasauth.key -pubout -outform PEM -out jaasauth.key.pub
```

### Step 2: Upload Public Key to JaaS Console
1. Go to your [JaaS Console](https://jaas.8x8.vc/) → **API Keys** section
2. Click **"Add API Key"**
3. Upload the **PUBLIC key file** (`jaasauth.key.pub`)
4. **IMPORTANT**: Copy the **Key ID** that JaaS generates (looks like: `jaas-api-key-12345678`)

### Step 3: Update Your .env File
```env
# Flask Configuration
SECRET_KEY=dev-secret-key-change-in-production-2024
DATABASE_URL=sqlite:///tdrmcd.db

# JaaS Configuration - ALL THREE ARE REQUIRED
JITSI_APP_ID=e1e3b2424c2a40e28e06456ee7ad0782
JITSI_KEY_ID=your-key-id-from-jaas-console
JITSI_APP_SECRET=-----BEGIN PRIVATE KEY-----
MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQCgLO0BANKrCmEV
SYuqnSUog53sbMOjv29urTEDxCbS4rJMzWWTRdWw+8fEJV2DfR/PfcGotLDEfZRO
EjVbtEJB3sKmowCF+NZ8d40I5WUWrMAwLMyFxHCNue12jW6HAY+KlTTr2NuRgA3h
UN1FZrctUrEuL9UESVPfIaN81N/w7oTythQntWgCagPxA+agxA6WY0eS4n+EEo+M
sp34WI6yiWOI5ExmMpNi6fAgVT81WWqZyjXBWJZzG9C0OfiGi+9Neb6+mYZb4EW+
quVqp+oroe/xi6bvlCxzxo1GpNG/J447in7qgNluPs1wB0ybyUNr1g2mjQ8ZxjP8
z6ZvYa07AgMBAAECggEBAIgF/vM2JrGX6+AvB8vJDfA87ZUEvJPHk7MSoyhGoI3A
dJhiaVtLF/DnsLry3Fo4nRYQ/q/tWpxS5Onz7ppFF2tm6Dio/l3HdyZWRFAEtvct
lzySHtGOg+LnvTBLZUyDV8nhcgLDs5r5e1AX4wD3/KEhs1O8zRKJzw8TOwpcoRyx
pRq/P2iKP+G/+WGJISCQfZJxF/wwMesOJshYPXxXWDd79MROVeFRfk3Qz9DO7NUW
F/O5MGEqGmNOMWIpFpY3OZFZNrxLzqv9vjtDStayGkpQCbdYj9kiGiX9K7ojdUNk
5XbwHZePU64AdtAOO813xPjfgHH94DXJzepjCq+nuWkCgYEA78/aqxDwi40uGxWb
VRNHY/5nCqsxfd25b64sFfgEYIo87baRobilZU47z7WPFHT6YQOqgzXMb1yFjmwy
tvqwH+nWJgrVGxKk5VGkwu0YOdFQZP7Stkl2/RoldFNlD9Qvj7xmDno5UrFqOavd
M05DAA1QeDhh7MwhiKSg4U+5GbUCgYEAqvzjlDeiyeu/ZwtyMoqTu8wQveBov4uf
iKsEaMQlcbElQVnQK6SnYJ3zUpanBzo2/LLfKFt37yYKHCzegNZ0M40UUDnX5jTg
Rc1qDOYznrl+0XFAY3JYB0pTC5rXN30SBAIH1wwNBVJZh5tQT0vXyZLbE/7Inq/n
RB7HHljDQS8CgYEArVfFbBnWhkkKprE7kodY90KRIPkV0TFQNRXk8AxSvaWu3PU2
13ssssmWGlHWlqbnxPBtdGKS33w1Xfl/vxv961OPY/g4ilUztD8LpYrUFBbk0dwQ
W4tG4zTfFfKh/osVxgQckSJwBQIREpbUUZ2keIknPX8j6ZK0Op0lXTfPSHECgYAE
tupTeOE9Lgnd/nvMlvOR1wOTKK/asC/a5dQ+S0I5C0har+5EdcrDqDdATLUYRuuj
Ng9fHn6FEohu1HHiHYegsEAiIiYoy8ZvRkWpS2Oa+cRcZAIBe/KfaNY3WLKcbg9k
GuY6cLOfNPERAyBIv2+YuDrgJ0NC1NjMkQiudoYTswKBgQC9GyiwDI4ohOonvAiC
LOg5w++FHch2CKCqdfUubHzyq/Mw1/EmSoxmE2y934mA4mhRZZVs7VuL6tDucNNy
i515XFmNmzyZvfxh5WLNKg0SJakwT7C8oAIPIMMlYgt3YD8YYWAjzUWUCxYorEfe
J4HW05NySTBcjn7p0F5Fecs7UA==
-----END PRIVATE KEY-----

# Mail Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=
```

## 🔑 **Key Points:**

1. **Upload PUBLIC key** to JaaS console (not private key)
2. **Use PRIVATE key** in your .env file for JWT signing
3. **Get Key ID** from JaaS console after uploading public key
4. **All three values required**: App ID, Key ID, Private Key

## 🎯 **What Was Missing:**

- **`kid` (Key ID)** in JWT header - this is how JaaS validates your token
- **Proper JWT header structure** with algorithm and key ID
- **Public key upload** to JaaS console to get the Key ID

## ✅ **After Setup:**

1. Install cryptography: `pip install cryptography`
2. Restart your Flask application
3. Create a video call
4. Check logs for "Generated JaaS JWT token" with Key ID
5. Should see "JaaS mode" in browser console

## 🔍 **Verification:**

Visit `/community/video_call/test-jwt` to verify JWT generation includes:
- Proper header with `kid`
- Correct payload structure
- RS256 algorithm signing

This should resolve the "not allowed to join" authentication error!

## 📚 **References:**
- [JaaS API Key Generation](https://developer.8x8.com/jaas/docs/api-keys-generate-add)
- [JaaS JWT Documentation](https://developer.8x8.com/jaas/docs/api-keys-jwt)
