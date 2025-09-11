from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from flask_mail import Mail, Message
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
from models import db
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
mail = Mail(app)
socketio = SocketIO(app, cors_allowed_origins="*", manage_session=True, logger=True, engineio_logger=True, async_mode="threading")

# Import models after db initialization
from models import User, Resource, CommunityPost, ChatMessage, FileSubmission, Notification, Campaign, VideoCall, ChatRoom

# Import blueprints
from routes.auth import auth_bp
from routes.main import main_bp
from routes.resources import resources_bp
from routes.community import community_bp
from routes.admin import admin_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(main_bp)
app.register_blueprint(resources_bp, url_prefix='/resources')
app.register_blueprint(community_bp, url_prefix='/community')
app.register_blueprint(admin_bp, url_prefix='/admin')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Socket.IO session handler
@socketio.on('connect')
def handle_connect():
    print(f"Socket.IO connection attempt from user: {current_user}")
    print(f"User authenticated: {current_user.is_authenticated}")
    if current_user.is_authenticated:
        join_room(f"user_{current_user.id}")
        emit('status', {'msg': f'{current_user.username} has connected'})
        print(f"User {current_user.username} connected successfully")
    else:
        print("Unauthenticated connection attempt - allowing connection anyway for testing")
        # For now, allow unauthenticated connections to test
        # return False

# Socket.IO events for real-time chat and WebRTC signaling

@socketio.on('disconnect')
def on_disconnect():
    if current_user.is_authenticated:
        leave_room(f"user_{current_user.id}")
        emit('status', {'msg': f'{current_user.username} has disconnected'})

@socketio.on('join_chat')
def on_join_chat(data):
    print(f"Join chat request from user: {current_user}")
    print(f"User authenticated: {current_user.is_authenticated}")
    room = data['room']
    print(f"Joining room: {room}")
    join_room(room)
    username = current_user.username if current_user.is_authenticated else "Anonymous"
    emit('user_joined', {'username': username}, room=room)
    print(f"User {username} joined room {room}")

@socketio.on('leave_chat')
def on_leave_chat(data):
    print(f"Leave chat request from user: {current_user}")
    room = data['room']
    print(f"Leaving room: {room}")
    leave_room(room)
    username = current_user.username if current_user.is_authenticated else "Anonymous"
    emit('user_left', {'username': username}, room=room)
    print(f"User {username} left room {room}")

@socketio.on('send_message')
def handle_message(data):
    print(f"Message received from user: {current_user}")
    print(f"User authenticated: {current_user.is_authenticated}")
    room = data['room']
    message = data['message']
    print(f"Saving message: {message} in room: {room}")
    
    # For testing, allow messages even from unauthenticated users
    if current_user.is_authenticated:
        # Save message to database
        chat_message = ChatMessage(
            content=message,
            sender_id=current_user.id,
            room=room,
            timestamp=datetime.utcnow()
        )
        db.session.add(chat_message)
        db.session.commit()
        print(f"Message saved with ID: {chat_message.id}")
        username = current_user.username
        timestamp = chat_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    else:
        # For unauthenticated users, just broadcast without saving
        username = "Anonymous"
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print("Message not saved (unauthenticated user)")
    
    # Emit message to room
    emit('receive_message', {
        'message': message,
        'username': username,
        'timestamp': timestamp
    }, room=room)
    print(f"Message emitted to room: {room}")
    print(f"Message data: {{'message': '{message}', 'username': '{username}', 'timestamp': '{timestamp}'}}")

# --- WebRTC signaling for video calls ---
@socketio.on('join_call')
def on_join_call(data):
    room_id = data.get('room_id')
    if not room_id:
        return
    join_room(room_id)
    emit('call_event', {
        'type': 'user-joined',
        'user': current_user.get_id()
    }, room=room_id, include_self=False)

@socketio.on('leave_call')
def on_leave_call(data):
    room_id = data.get('room_id')
    if not room_id:
        return
    leave_room(room_id)
    emit('call_event', {
        'type': 'user-left',
        'user': current_user.get_id()
    }, room=room_id, include_self=False)

@socketio.on('webrtc_offer')
def on_webrtc_offer(data):
    room_id = data.get('room_id')
    offer = data.get('offer')
    to = data.get('to')
    payload = {
        'type': 'offer',
        'from': current_user.get_id(),
        'offer': offer
    }
    if to:
        emit('call_event', payload, to=to)
    else:
        emit('call_event', payload, room=room_id, include_self=False)

# Serve uploaded files (e.g., submissions) safely
@app.route('/uploads/<path:subdir>/<path:filename>')
@login_required
def serve_uploaded_file(subdir, filename):
    uploads_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    directory = os.path.join(uploads_root, subdir)
    
    # Security check - ensure the path is within uploads directory
    if not os.path.isdir(directory) or not os.path.commonpath([uploads_root, directory]) == uploads_root:
        abort(404)
    
    file_path = os.path.join(directory, filename)
    if not os.path.exists(file_path):
        abort(404)
    
    try:
        return send_from_directory(directory, filename, as_attachment=True)
    except Exception as e:
        print(f"Error serving file {filename}: {e}")
        abort(404)

@socketio.on('webrtc_answer')
def on_webrtc_answer(data):
    room_id = data.get('room_id')
    answer = data.get('answer')
    to = data.get('to')
    payload = {
        'type': 'answer',
        'from': current_user.get_id(),
        'answer': answer
    }
    if to:
        emit('call_event', payload, to=to)
    else:
        emit('call_event', payload, room=room_id, include_self=False)

@socketio.on('webrtc_ice_candidate')
def on_webrtc_ice_candidate(data):
    room_id = data.get('room_id')
    candidate = data.get('candidate')
    to = data.get('to')
    payload = {
        'type': 'ice-candidate',
        'from': current_user.get_id(),
        'candidate': candidate
    }
    if to:
        emit('call_event', payload, to=to)
    else:
        emit('call_event', payload, room=room_id, include_self=False)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
