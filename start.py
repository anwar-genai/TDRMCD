#!/usr/bin/env python3
"""
TDRMCD Quick Start Script

This script sets up and runs the TDRMCD application with minimal configuration.
Perfect for development and testing.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def create_virtual_environment():
    """Create virtual environment if it doesn't exist"""
    venv_path = Path("venv")
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created")
    else:
        print("✅ Virtual environment already exists")

def install_dependencies():
    """Install required packages"""
    print("📥 Installing dependencies...")
    
    # Determine pip command based on OS
    if os.name == 'nt':  # Windows
        pip_cmd = ["venv\\Scripts\\pip.exe"]
    else:  # Unix/Linux/Mac
        pip_cmd = ["venv/bin/pip"]
    
    try:
        # Upgrade pip first
        subprocess.run(pip_cmd + ["install", "--upgrade", "pip"], check=True, capture_output=True)
        
        # Install requirements
        subprocess.run(pip_cmd + ["install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print("💡 Try running manually:")
        print("   pip install -r requirements.txt")
        sys.exit(1)

def create_env_file():
    """Create .env file with default settings"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚙️ Creating .env configuration file...")
        env_content = """# TDRMCD Configuration
SECRET_KEY=dev-secret-key-change-in-production-please
FLASK_ENV=development
FLASK_DEBUG=True

# Database
DATABASE_URL=sqlite:///tdrmcd.db

# File Upload
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=static/uploads

# Mail (Optional - for notifications)
# MAIL_SERVER=smtp.gmail.com
# MAIL_PORT=587
# MAIL_USE_TLS=True
# MAIL_USERNAME=your-email@gmail.com
# MAIL_PASSWORD=your-app-password
# MAIL_DEFAULT_SENDER=your-email@gmail.com
"""
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ .env file created with default settings")
    else:
        print("✅ .env file already exists")

def run_application():
    """Run the Flask application"""
    print("\n🚀 Starting TDRMCD Application...")
    print("=" * 60)
    
    # Determine python command based on OS
    if os.name == 'nt':  # Windows
        python_cmd = ["venv\\Scripts\\python.exe"]
    else:  # Unix/Linux/Mac
        python_cmd = ["venv/bin/python"]
    
    try:
        subprocess.run(python_cmd + ["run.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running application: {e}")

def main():
    """Main setup and run function"""
    print("🏔️ TDRMCD - Tribal Districts Resource Management Setup")
    print("=" * 60)
    
    try:
        # Check requirements
        check_python_version()
        
        # Setup environment
        create_virtual_environment()
        install_dependencies()
        create_env_file()
        
        print("\n✅ Setup completed successfully!")
        print("\n📋 Quick Info:")
        print("   • Application will run on: http://127.0.0.1:5000")
        print("   • Admin username: admin")
        print("   • Admin password: admin123")
        print("   • Database: SQLite (tdrmcd.db)")
        print("\n⚠️  Remember to change the admin password after first login!")
        
        # Ask user if they want to start the app
        response = input("\n🚀 Start the application now? (y/n): ").lower().strip()
        if response in ['y', 'yes', '']:
            run_application()
        else:
            print("\n💡 To start the application later, run:")
            print("   python run.py")
            
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        print("\n💡 Manual setup instructions:")
        print("   1. Create virtual environment: python -m venv venv")
        print("   2. Activate environment: venv\\Scripts\\activate (Windows) or source venv/bin/activate (Unix)")
        print("   3. Install dependencies: pip install -r requirements.txt")
        print("   4. Run application: python run.py")
        sys.exit(1)

if __name__ == "__main__":
    main()
