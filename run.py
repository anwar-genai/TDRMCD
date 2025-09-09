#!/usr/bin/env python3
"""
TDRMCD - Tribal Districts Resource Management and Community Development
Flask Application Runner

This script initializes and runs the Flask application.
"""

import os
from app import app, db, socketio

def create_directories():
    """Create necessary directories for file uploads"""
    upload_dirs = [
        'static/uploads/resources',
        'static/uploads/posts', 
        'static/uploads/submissions',
        'static/uploads/avatars',
        'static/uploads/campaigns'
    ]
    
    for directory in upload_dirs:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def init_database():
    """Initialize the database with tables"""
    with app.app_context():
        try:
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Create default admin user if it doesn't exist
            from models import User
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin = User(
                    username='admin',
                    email='admin@tdrmcd.com',
                    first_name='System',
                    last_name='Administrator',
                    role='admin',
                    location='Khyber Pakhtunkhwa'
                )
                admin.set_password('admin123')  # Change this in production!
                db.session.add(admin)
                db.session.commit()
                print("✓ Default admin user created (username: admin, password: admin123)")
            else:
                print("✓ Admin user already exists")
                
        except Exception as e:
            print(f"✗ Error initializing database: {e}")

def main():
    """Main function to run the application"""
    print("🚀 Starting TDRMCD Application...")
    print("=" * 50)
    
    # Create necessary directories
    create_directories()
    
    # Initialize database
    init_database()
    
    print("=" * 50)
    print("📊 Application Information:")
    print(f"   Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"   Debug Mode: {os.getenv('FLASK_DEBUG', 'True')}")
    print(f"   Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')}")
    print("=" * 50)
    print("🌐 Starting server...")
    print("   Local URL: http://127.0.0.1:5000")
    print("   Network URL: http://0.0.0.0:5000")
    print("=" * 50)
    print("💡 Default Admin Credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    print("   ⚠️  Please change the admin password after first login!")
    print("=" * 50)
    
    # Run the application
    try:
        socketio.run(
            app, 
            debug=True, 
            host='0.0.0.0', 
            port=5000,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error running application: {e}")

if __name__ == '__main__':
    main()
