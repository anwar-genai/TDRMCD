# TDRMCD — Tribal Districts Resource Management and Community Development

A full‑stack Flask application for managing and sharing information about natural and cultural resources in the tribal districts of Khyber Pakhtunkhwa (KPK), Pakistan. It combines a resource catalog, community collaboration (chat, forums, file sharing), interactive mapping, and authenticated video calls.

## 🌟 What’s Inside

- **Resource Catalog**: Detailed resource profiles with categories, tags, geo locations, and attachments
- **Community**: Real‑time chat rooms, posts, comments, reactions, and file sharing
- **Video Calling**: Secure, authenticated meetings via JaaS (Jitsi as a Service)
- **Mapping**: Interactive map with resource markers and layers
- **Admin & Analytics**: Admin dashboard, moderation, and basic analytics

See `OFFERS.md` for optional enhancements and roadmap items across search, GIS, moderation, API, performance, and more.

## 🧠 How It Works (Architecture)

- **Flask Blueprints**: Feature areas live under `routes/` (`auth.py`, `main.py`, `resources.py`, `community.py`, `admin.py`)
- **Templates**: Jinja2 templates under `templates/` with a shared `base.html`
- **Database**: SQLAlchemy models in `models.py`, migrations via Alembic/Flask‑Migrate (see `migrations/`)
- **Realtime**: Flask‑Socket.IO powers live chat and notifications
- **Video**: JaaS token signing on the server authorizes users to join video meetings
- **Static & Uploads**: Static assets in `static/`; user uploads in `static/uploads/` and project‑level `uploads/`

## 🚀 Quick Start (Windows Friendly)

### Option A: One-command setup + run (recommended)

1. Run the guided setup script:
   ```bash
   python start.py
   ```
   This creates venv, installs dependencies, sets up `.env`, and starts the app automatically.

### Option B: Use provided scripts (Windows)

1. Double‑click `setup.bat` to create a virtual environment and install dependencies
2. Double‑click `start_app.bat` to launch the app
3. Open `http://127.0.0.1:5000` in your browser

### Option C: Manual setup

1. Install Python 3.8+ and ensure `python` is on PATH
2. Create a virtual environment and activate it
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment (see next section) and run the app
   ```bash
   python run.py
   ```

**Note**: Use `python run.py` (not `python app.py`) for automatic setup of folders, database, and admin user.

## 🛠️ Configuration

Use the template in `env.template` to create your environment file (e.g., `.env`):

```env
# Flask Configuration
SECRET_KEY=change-this-in-production
DATABASE_URL=sqlite:///tdrmcd.db

# Mail (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=

# JaaS (Jitsi as a Service)
# Obtain values from your JaaS console
JITSI_APP_ID=
JITSI_KEY_ID=
JITSI_APP_SECRET=
```

Notes:
- `JITSI_APP_SECRET` accepts a multi‑line PEM or a single line with `\n`
- For production, consider PostgreSQL: `DATABASE_URL=postgresql://user:pass@host/dbname`

## 🎥 Video Calls (JaaS)

The app can generate signed tokens to join authenticated JaaS rooms.

High‑level setup:
1. Create RSA keys and upload your public key in the JaaS Console to get a Key ID
2. Set `JITSI_APP_ID`, `JITSI_KEY_ID`, and `JITSI_APP_SECRET` in your env
3. Restart the app and start/join calls from the community pages

Helpful guides: see `JAAS_SETUP.md` and `JAAS_SETUP_CORRECT.md` in the repo.

Troubleshooting:
- “Not allowed to join”: verify all 3 JaaS variables and key format
- No controls: ensure the Key ID includes the `vpaas-magic-cookie-...` prefix
- Crypto errors: install `cryptography` and restart the app

## 📁 Project Structure

```
tdrmcd/
├── app.py                 # Flask app/bootstrap
├── run.py                 # App runner
├── config.py              # Settings & env loading
├── models.py              # SQLAlchemy models
├── forms.py               # WTForms
├── routes/                # Feature blueprints
│   ├── auth.py
│   ├── main.py
│   ├── resources.py
│   ├── community.py
│   └── admin.py
├── templates/             # Jinja templates
├── static/                # CSS/JS/images and uploads
├── uploads/               # Project-level uploads (if used)
├── migrations/            # Alembic migrations
└── instance/tdrmcd.db     # SQLite database (if created here)
```

## 💡 Using the App

1. Open `http://127.0.0.1:5000`
2. Log in with the default admin account:
   - Username: `admin`
   - Password: `admin123`
   - **⚠️ Change this password immediately after first login!**
3. Explore:
   - Resources: browse, search, view details, and attachments
   - Community: chat rooms, posts, comments, and file submissions
   - Video Calls: start/join meetings from community pages
4. Admin: visit `/admin` for full system management

**Note**: The default admin user is automatically created when you run `python run.py` or `python start.py`.

## 🔧 Development

### Database migrations
```bash
# First time only
flask db init

# Generate migration from model changes
flask db migrate -m "Describe changes"

# Apply migrations
flask db upgrade
```

### Running in production
```bash
set FLASK_ENV=production
set FLASK_DEBUG=False
```
Use a production server such as:
```bash
gunicorn -k eventlet -w 1 --bind 0.0.0.0:5000 app:app
```

## 📋 Common Routes

### Authentication
- `POST /auth/login` — Login
- `POST /auth/register` — Register
- `GET /auth/logout` — Logout

### Resources
- `GET /resources` — List resources
- `GET /resources/<id>` — Resource details
- `POST /resources/add` — Add resource
- `PUT /resources/<id>/edit` — Edit resource

### Community
- `GET /community` — Forum
- `POST /community/create_post` — Create post
- `GET /community/chat` — Chat interface
- `POST /community/files/submit` — Submit file

### Admin
- `GET /admin` — Dashboard
- `GET /admin/users` — Manage users
- `GET /admin/resources` — Manage resources

## 🔒 Security Checklist

- Set a strong `SECRET_KEY`
- Change any default credentials immediately
- Enable mail to support password reset and verification
- Serve behind HTTPS (terminate TLS at a proxy)
- Keep dependencies updated

## 🧭 Data & Storage Locations

- SQLite DB: as configured by `DATABASE_URL` (example: `sqlite:///tdrmcd.db`)
- Uploads: `static/uploads/*` and project `uploads/*` directories

## 🎨 UI/UX Highlights

- Responsive Bootstrap 5 UI, dark mode support
- Real‑time updates via Socket.IO
- Interactive mapping with Leaflet.js

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/xyz`)
3. Commit (`git commit -m "Add xyz"`)
4. Push (`git push origin feature/xyz`)
5. Open a Pull Request

## 👨‍💻 Team

- **Rizwan Ullah** (Reg#: 2021-USTB-125660) — rizwanwazir601@gmail.com
- **Manzor Ahmad** (Reg#: 2021-USTB-125649) — manzorwazir12@gmail.com
- **Talha** (Reg#: 2021-USTB-125637) — talhawazir02@gmail.com

Supervisor: M Zahid Khan, Department of Software Engineering, UST Bannu

## 🆘 Support

- Open an issue in the repository
- Contact the development team
- See `OFFERS.md` for planned enhancements

## 🎯 Goals

- Centralize reliable resource information
- Enable informed conservation and development decisions
- Facilitate real‑time collaboration and knowledge sharing
- Promote awareness for education, health, and sustainability
- Empower local communities and improve socioeconomic outcomes

---

Built with ❤️ for the tribal communities of Khyber Pakhtunkhwa
