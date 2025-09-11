#!/usr/bin/env python3
"""
Database Reset Script for TDRMCD
This script will completely reset the database and recreate all tables.
Use this if you're experiencing database issues or want a fresh start.
"""

import os
import shutil
from datetime import datetime
from app import app, db
from models import *

def backup_database():
    """Create a backup of the current database"""
    db_path = 'instance/tdrmcd.db'
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'instance/tdrmcd_backup_{timestamp}.db'
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
    return None

def reset_database():
    """Reset the database completely"""
    print("🔄 Resetting TDRMCD Database...")
    print("=" * 50)
    
    # Create backup
    backup_path = backup_database()
    
    # Remove existing database
    db_path = 'instance/tdrmcd.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️  Removed existing database")
    
    # Create new database
    with app.app_context():
        print("🔧 Creating new database...")
        db.create_all()
        print("✅ Database created successfully!")
        
        # Create some sample data
        create_sample_data()
        
        print("\n🎉 Database reset completed!")
        print(f"📁 Backup saved at: {backup_path}")
        print("\n📋 Next steps:")
        print("1. Run the application: python app.py")
        print("2. Register a new admin user")
        print("3. Test the chat functionality")

def create_sample_data():
    """Create some sample data for testing"""
    print("📝 Creating sample data...")
    
    # Create sample users
    admin_user = User(
        username='admin',
        email='admin@tdrmcd.com',
        first_name='Admin',
        last_name='User',
        role='admin'
    )
    admin_user.set_password('admin123')
    
    test_user = User(
        username='testuser',
        email='test@tdrmcd.com',
        first_name='Test',
        last_name='User',
        role='user'
    )
    test_user.set_password('test123')
    
    db.session.add(admin_user)
    db.session.add(test_user)
    
    # Create sample chat rooms
    general_room = ChatRoom(
        room_id='general',
        name='General Discussion',
        description='General discussion about TDRMCD',
        created_by=admin_user.id
    )
    
    resources_room = ChatRoom(
        room_id='resources',
        name='Resource Discussion',
        description='Discussion about natural resources',
        created_by=admin_user.id
    )
    
    db.session.add(general_room)
    db.session.add(resources_room)
    
    # Create sample chat messages
    welcome_message = ChatMessage(
        content='Welcome to TDRMCD Chat! This is a test message.',
        room='general',
        sender_id=admin_user.id
    )
    
    db.session.add(welcome_message)
    
    # Create sample resources
    sample_resource = Resource(
        title='Copper Deposits in KPK',
        description='Rich copper deposits found in the northern regions of Khyber Pakhtunkhwa',
        category='minerals',
        subcategory='copper',
        location='Khyber Pakhtunkhwa, Pakistan',
        latitude=34.0151,
        longitude=71.5249,
        economic_value='High - Estimated $2.5 billion',
        sustainability_info='Sustainable mining practices recommended',
        author_id=admin_user.id
    )
    
    db.session.add(sample_resource)
    
    # Create sample community post
    sample_post = CommunityPost(
        title='Welcome to TDRMCD Community',
        content='Welcome to our community platform! Share your knowledge about natural resources in KPK.',
        category='announcement',
        tags='welcome,community,resources',
        author_id=admin_user.id
    )
    
    db.session.add(sample_post)
    
    db.session.commit()
    print("✅ Sample data created successfully!")

def main():
    """Main function"""
    print("🚨 TDRMCD Database Reset Tool")
    print("=" * 50)
    print("⚠️  WARNING: This will completely reset your database!")
    print("📋 This will:")
    print("   - Backup your current database")
    print("   - Delete all existing data")
    print("   - Create fresh tables")
    print("   - Add sample data for testing")
    print()
    
    response = input("Are you sure you want to continue? (yes/no): ").lower().strip()
    
    if response in ['yes', 'y']:
        reset_database()
    else:
        print("❌ Database reset cancelled.")
        print("\n💡 If you're having issues, try:")
        print("1. Check the database file: instance/tdrmcd.db")
        print("2. Run: python check_db.py")
        print("3. Check application logs for errors")

if __name__ == "__main__":
    main()
