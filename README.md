# TDRMCD - Tribal Districts Resource Management and Community Development

A comprehensive Flask web application for managing and sharing information about natural and cultural resources in the tribal districts of Khyber Pakhtunkhwa (KPK), Pakistan.

## 🌟 Features

### 🏛️ Core Features
- **Resource Database**: Centralized information about minerals, agriculture, wildlife, and cultural heritage
- **Community Platform**: Real-time chat, video calling, and discussion forums
- **File Sharing**: Secure file submission system with reference validation
- **Interactive Mapping**: Live map showing resource locations
- **Awareness Campaigns**: Educational content about health, education, and sustainability
- **User Management**: Role-based access control (Users, Researchers, Admins)

### 💬 Community Features
- **Real-time Chat**: Multiple chat rooms with Socket.IO for instant messaging
- **Video Calling**: JaaS-powered video conferencing with authentication
- **Discussion Forums**: Community posts with comments and reactions
- **File Sharing**: Upload and share documents, images, and research papers
- **Notifications**: Real-time updates and alerts

### 🗺️ Resource Management
- **Detailed Resource Profiles**: Complete information about local resources
- **Geographic Mapping**: Interactive maps with resource locations
- **Search & Filter**: Advanced search capabilities
- **Category Organization**: Resources organized by type (Minerals, Agriculture, etc.)
- **Economic Data**: Information about economic value and sustainability

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tdrmcd
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env file with your configuration
   # At minimum, set a secure SECRET_KEY
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

6. **Access the application**
   - Open your browser and go to `http://127.0.0.1:5000`
   - Default admin credentials:
     - Username: `admin`
     - Password: `admin123`
   - **⚠️ Change the admin password immediately after first login!**

## 🎥 Video Call Setup (JaaS Integration)

The application supports professional video calling through JaaS (Jitsi as a Service). This provides authenticated, secure video conferences with moderation controls.

### 🔧 JaaS Configuration

1. **Sign up for JaaS**
   - Visit [JaaS Console](https://jaas.8x8.vc/)
   - Create a free account
   - Create a new application

2. **Generate API Key**
   ```bash
   # Generate RSA key pair
   ssh-keygen -t rsa -b 4096 -m PEM -f jaasauth.key
   
   # Generate public key in PEM format
   openssl rsa -in jaasauth.key -pubout -outform PEM -out jaasauth.key.pub
   ```

3. **Upload Public Key**
   - Go to JaaS Console → API Keys
   - Upload the **public key** (`jaasauth.key.pub`)
   - Copy the generated **Key ID** (e.g., `vpaas-magic-cookie-abc123/def456`)

4. **Configure Environment Variables**
   
   Create a `.env` file in the project root with:
   ```env
   # Flask Configuration
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///tdrmcd.db
   
   # JaaS Configuration
   JITSI_APP_ID=your-app-id-here
   JITSI_KEY_ID=vpaas-magic-cookie-your-app-id/key-id
   JITSI_APP_SECRET=-----BEGIN PRIVATE KEY-----
   your-private-key-content-here
   -----END PRIVATE KEY-----
   
   # Mail Configuration (Optional)
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=your-email@example.com
   MAIL_PASSWORD=your-app-password
   ```

5. **Install Additional Dependencies**
   ```bash
   pip install cryptography python-dotenv
   ```

6. **Restart Application**
   ```bash
   python run.py
   ```

### ✅ Video Call Features

With JaaS configured, you get:
- **Authenticated Meetings**: Secure JWT-based authentication
- **Host Moderation**: Meeting hosts have full control
- **High-Quality Video**: Professional-grade video conferencing
- **Virtual Backgrounds**: Built-in background replacement
- **Screen Sharing**: Share your screen with participants
- **Chat Integration**: Video calls linked to chat rooms
- **Recording Support**: Meeting recording capabilities (if enabled)

### 🔍 Troubleshooting Video Calls

- **"Not allowed to join"**: Check that all three JaaS variables are correctly set
- **Video not loading**: Ensure cryptography library is installed
- **No moderation controls**: Verify the Key ID format includes the full `vpaas-magic-cookie-` prefix
- **Connection issues**: Check browser console for JWT token errors

### 📱 Using Video Calls

1. **From Chat Rooms**: Click the video button in any chat room
2. **Direct Access**: Visit `/community/video_call` to see all active calls
3. **Create Meetings**: Start new video calls from the community section
4. **Join Existing**: Click "Join Video Call" when others start meetings

## 📁 Project Structure

```
tdrmcd/
├── app.py                 # Main Flask application
├── run.py                 # Application runner with initialization
├── config.py              # Configuration settings
├── models.py              # Database models
├── forms.py               # WTForms for form handling
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── routes/               # Application routes
│   ├── __init__.py
│   ├── auth.py           # Authentication routes
│   ├── main.py           # Main application routes
│   ├── resources.py      # Resource management routes
│   ├── community.py      # Community features routes
│   └── admin.py          # Admin panel routes
├── templates/            # Jinja2 templates
│   ├── base.html         # Base template
│   ├── main/             # Main page templates
│   ├── auth/             # Authentication templates
│   ├── resources/        # Resource templates
│   ├── community/        # Community templates
│   └── admin/            # Admin panel templates
├── static/               # Static files
│   ├── css/              # Stylesheets
│   ├── js/               # JavaScript files
│   ├── images/           # Images
│   └── uploads/          # User uploaded files
└── migrations/           # Database migrations (auto-generated)
```

## 🛠️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Flask Configuration
SECRET_KEY=your-very-secure-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True

# Database
DATABASE_URL=sqlite:///tdrmcd.db

# Mail Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

### Database Configuration

The application uses SQLite by default, which is perfect for development and small deployments. For production, consider using PostgreSQL:

```env
DATABASE_URL=postgresql://username:password@localhost/tdrmcd
```

## 👥 User Roles

1. **Regular Users**: Can view resources, participate in community discussions, submit files
2. **Researchers**: Enhanced access to detailed resource data and analytics
3. **Administrators**: Full access to manage users, moderate content, and system settings

## 🔧 Development

### Adding New Features

1. **Database Models**: Add new models in `models.py`
2. **Routes**: Create new routes in the appropriate blueprint
3. **Templates**: Add corresponding HTML templates
4. **Forms**: Create forms in `forms.py` for user input
5. **Static Files**: Add CSS/JS in the `static/` directory

### Database Migrations

```bash
# Initialize migrations (first time only)
flask db init

# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade
```

### Running in Production

1. **Set environment variables**:
   ```bash
   export FLASK_ENV=production
   export FLASK_DEBUG=False
   ```

2. **Use a production WSGI server**:
   ```bash
   gunicorn -k eventlet -w 1 --bind 0.0.0.0:5000 app:app
   ```

## 📋 API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/logout` - User logout

### Resources
- `GET /resources` - List all resources
- `GET /resources/<id>` - Get resource details
- `POST /resources/add` - Add new resource
- `PUT /resources/<id>/edit` - Update resource

### Community
- `GET /community` - Community forum
- `POST /community/create_post` - Create new post
- `GET /community/chat` - Chat interface
- `POST /community/files/submit` - Submit file

### Admin
- `GET /admin` - Admin dashboard
- `GET /admin/users` - Manage users
- `GET /admin/resources` - Manage resources

## 🔒 Security Features

- **User Authentication**: Secure login/logout system
- **Password Hashing**: Werkzeug password hashing
- **File Upload Validation**: Secure file handling
- **CSRF Protection**: Cross-site request forgery protection
- **Role-based Access**: Different permission levels
- **Input Validation**: Form validation and sanitization

## 🎨 UI/UX Features

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Modern Interface**: Bootstrap 5 with custom styling
- **Real-time Updates**: Socket.IO for live features
- **Interactive Maps**: Leaflet.js integration
- **File Drag & Drop**: Intuitive file upload
- **Dark Mode Support**: Automatic dark mode detection

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Development Team

- **Rizwan Ullah** (Reg#: 2021-USTB-125660) - rizwanwazir601@gmail.com
- **Manzor Ahmad** (Reg#: 2021-USTB-125649) - manzorwazir12@gmail.com  
- **Talha** (Reg#: 2021-USTB-125637) - talhawazir02@gmail.com

**Supervisor**: M Zahid Khan, Department of Software Engineering, UST Bannu

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation in the `/docs` folder

## 🎯 Project Goals

This platform aims to:
- Centralize reliable information about local resources
- Enable informed decision-making on resource use and conservation
- Facilitate real-time collaboration and knowledge sharing
- Promote awareness about education, health, and sustainable practices
- Empower local residents and improve socioeconomic outcomes
- Create a safe and trusted environment for community interaction

---

**Built with ❤️ for the tribal communities of Khyber Pakhtunkhwa**
