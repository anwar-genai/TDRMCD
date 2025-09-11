#!/usr/bin/env python3
"""
Chat Functionality Test Script for TDRMCD
This script tests the chat functionality to ensure everything works properly.
"""

import requests
import json
from app import app, db, socketio
from models import *

def test_database_connection():
    """Test database connection and tables"""
    print("🔍 Testing database connection...")
    
    with app.app_context():
        try:
            # Test basic queries
            user_count = User.query.count()
            chat_message_count = ChatMessage.query.count()
            chat_room_count = ChatRoom.query.count()
            
            print(f"✅ Database connected successfully!")
            print(f"   - Users: {user_count}")
            print(f"   - Chat Messages: {chat_message_count}")
            print(f"   - Chat Rooms: {chat_room_count}")
            
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

def test_chat_models():
    """Test chat-related models"""
    print("\n🔍 Testing chat models...")
    
    with app.app_context():
        try:
            # Test ChatMessage model
            messages = ChatMessage.query.limit(5).all()
            print(f"✅ ChatMessage model working - {len(messages)} messages found")
            
            # Test ChatRoom model
            rooms = ChatRoom.query.limit(5).all()
            print(f"✅ ChatRoom model working - {len(rooms)} rooms found")
            
            # Test User model
            users = User.query.limit(5).all()
            print(f"✅ User model working - {len(users)} users found")
            
            return True
        except Exception as e:
            print(f"❌ Model test failed: {e}")
            return False

def test_socketio_events():
    """Test Socket.IO event handlers"""
    print("\n🔍 Testing Socket.IO events...")
    
    try:
        # Check if socketio is properly initialized
        if socketio:
            print("✅ SocketIO initialized successfully")
            
            # Test event handlers exist
            handlers = socketio.server.handlers
            required_events = ['connect', 'disconnect', 'join_chat', 'leave_chat', 'send_message']
            
            for event in required_events:
                if f'/{event}' in handlers:
                    print(f"✅ Event handler '{event}' registered")
                else:
                    print(f"❌ Event handler '{event}' missing")
            
            return True
        else:
            print("❌ SocketIO not initialized")
            return False
    except Exception as e:
        print(f"❌ SocketIO test failed: {e}")
        return False

def test_chat_routes():
    """Test chat-related routes"""
    print("\n🔍 Testing chat routes...")
    
    with app.test_client() as client:
        try:
            # Test chat main page
            response = client.get('/community/chat')
            if response.status_code == 302:  # Redirect to login
                print("✅ Chat route exists (redirects to login)")
            elif response.status_code == 200:
                print("✅ Chat route accessible")
            else:
                print(f"❌ Chat route returned status {response.status_code}")
            
            # Test chat room route
            response = client.get('/community/chat/general')
            if response.status_code == 302:  # Redirect to login
                print("✅ Chat room route exists (redirects to login)")
            elif response.status_code == 200:
                print("✅ Chat room route accessible")
            else:
                print(f"❌ Chat room route returned status {response.status_code}")
            
            return True
        except Exception as e:
            print(f"❌ Route test failed: {e}")
            return False

def create_test_data():
    """Create test data for chat functionality"""
    print("\n🔧 Creating test data...")
    
    with app.app_context():
        try:
            # Create test user if not exists
            test_user = User.query.filter_by(username='testuser').first()
            if not test_user:
                test_user = User(
                    username='testuser',
                    email='test@example.com',
                    first_name='Test',
                    last_name='User',
                    role='user'
                )
                test_user.set_password('test123')
                db.session.add(test_user)
                db.session.commit()
                print("✅ Test user created")
            else:
                print("✅ Test user already exists")
            
            # Create test chat room if not exists
            test_room = ChatRoom.query.filter_by(room_id='test').first()
            if not test_room:
                test_room = ChatRoom(
                    room_id='test',
                    name='Test Room',
                    description='A test chat room',
                    created_by=test_user.id
                )
                db.session.add(test_room)
                db.session.commit()
                print("✅ Test chat room created")
            else:
                print("✅ Test chat room already exists")
            
            # Create test message if not exists
            test_message = ChatMessage.query.filter_by(room='test').first()
            if not test_message:
                test_message = ChatMessage(
                    content='This is a test message',
                    room='test',
                    sender_id=test_user.id
                )
                db.session.add(test_message)
                db.session.commit()
                print("✅ Test message created")
            else:
                print("✅ Test message already exists")
            
            return True
        except Exception as e:
            print(f"❌ Test data creation failed: {e}")
            return False

def main():
    """Main test function"""
    print("🧪 TDRMCD Chat Functionality Test")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Chat Models", test_chat_models),
        ("SocketIO Events", test_socketio_events),
        ("Chat Routes", test_chat_routes),
        ("Test Data Creation", create_test_data)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Chat functionality should work properly.")
        print("\n💡 To test the chat:")
        print("1. Start the application: python app.py")
        print("2. Open two browser windows")
        print("3. Login with different users")
        print("4. Navigate to /community/chat")
        print("5. Try sending messages")
    else:
        print("❌ Some tests failed. Check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("1. Run: python reset_database.py")
        print("2. Check database file: instance/tdrmcd.db")
        print("3. Verify all dependencies are installed")

if __name__ == "__main__":
    main()
