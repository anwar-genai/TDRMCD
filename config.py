import os
from dotenv import load_dotenv

# Load environment variables, try both .env and env files
try:
    # Try loading from .env first
    if os.path.exists('.env'):
        load_dotenv('.env')
    elif os.path.exists('env'):
        load_dotenv('env')
    else:
        print("Warning: No environment file found (.env or env)")
except Exception as e:
    print(f"Warning: Could not load environment file: {e}")

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///tdrmcd.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}
    
    # Mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Pagination
    POSTS_PER_PAGE = 10
    RESOURCES_PER_PAGE = 12
    
    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Jitsi Video Call Configuration
    JITSI_APP_ID = os.environ.get('JITSI_APP_ID')
    JITSI_APP_SECRET = os.environ.get('JITSI_APP_SECRET')
    if JITSI_APP_SECRET:
        # Replace \n with actual newlines for multi-line private key
        JITSI_APP_SECRET = JITSI_APP_SECRET.replace('\\n', '\n')
    JITSI_KEY_ID = os.environ.get('JITSI_KEY_ID')  # Key ID from JaaS console