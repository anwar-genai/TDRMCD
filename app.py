from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
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
socketio = SocketIO(app, cors_allowed_origins="*")

# Import models after db initialization
from models import User, Resource, CommunityPost, ChatMessage, FileSubmission, Notification, Campaign, VideoCall

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

# Socket.IO events for real-time chat
@socketio.on('connect')
def on_connect():
    if current_user.is_authenticated:
        join_room(f"user_{current_user.id}")
        emit('status', {'msg': f'{current_user.username} has connected'})

@socketio.on('disconnect')
def on_disconnect():
    if current_user.is_authenticated:
        leave_room(f"user_{current_user.id}")
        emit('status', {'msg': f'{current_user.username} has disconnected'})

@socketio.on('join_chat')
def on_join_chat(data):
    room = data['room']
    join_room(room)
    emit('status', {'msg': f'{current_user.username} has joined the chat'}, room=room)

@socketio.on('leave_chat')
def on_leave_chat(data):
    room = data['room']
    leave_room(room)
    emit('status', {'msg': f'{current_user.username} has left the chat'}, room=room)

@socketio.on('send_message')
def handle_message(data):
    room = data['room']
    message = data['message']
    
    # Save message to database
    chat_message = ChatMessage(
        content=message,
        sender_id=current_user.id,
        room=room,
        timestamp=datetime.utcnow()
    )
    db.session.add(chat_message)
    db.session.commit()
    
    # Emit message to room
    emit('receive_message', {
        'message': message,
        'username': current_user.username,
        'timestamp': chat_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    }, room=room)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
