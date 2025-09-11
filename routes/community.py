from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from models import db, CommunityPost, Comment, ChatMessage, FileSubmission, VideoCall, PostLike, ChatRoom
from forms import CommunityPostForm, CommentForm, FileSubmissionForm
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

community_bp = Blueprint('community', __name__)

@community_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', 'all')
    sort_by = request.args.get('sort', 'newest')
    
    query = CommunityPost.query
    
    if category != 'all':
        query = query.filter_by(category=category)
    
    if sort_by == 'newest':
        query = query.order_by(CommunityPost.created_at.desc())
    elif sort_by == 'oldest':
        query = query.order_by(CommunityPost.created_at.asc())
    elif sort_by == 'popular':
        query = query.order_by(CommunityPost.likes.desc())
    elif sort_by == 'most_viewed':
        query = query.order_by(CommunityPost.views.desc())
    
    posts = query.paginate(
        page=page, per_page=10, error_out=False
    )
    
    # Get categories for filter
    categories = ['discussion', 'question', 'announcement', 'news']
    
    return render_template('community/index.html',
                         posts=posts,
                         categories=categories,
                         current_category=category,
                         current_sort=sort_by)

@community_bp.route('/post/<int:id>')
def post_detail(id):
    post = CommunityPost.query.get_or_404(id)
    
    # Increment view count
    post.views += 1
    db.session.commit()
    
    # Get comments
    comments = Comment.query.filter_by(post_id=id, parent_id=None).order_by(Comment.created_at.asc()).all()
    
    comment_form = CommentForm()
    
    return render_template('community/post_detail.html',
                         post=post,
                         comments=comments,
                         comment_form=comment_form)

@community_bp.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    form = CommunityPostForm()
    if form.validate_on_submit():
        post = CommunityPost(
            title=form.title.data,
            content=form.content.data,
            category=form.category.data,
            tags=form.tags.data,
            author_id=current_user.id
        )
        
        # Handle image upload
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            if filename:
                file_ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4()}.{file_ext}"
                
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts', unique_filename)
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                form.image.data.save(image_path)
                post.image_url = f"posts/{unique_filename}"
        
        db.session.add(post)
        db.session.commit()
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('community.post_detail', id=post.id))
    
    return render_template('community/create_post.html', form=form)

@community_bp.route('/post/<int:id>/comment', methods=['POST'])
@login_required
def add_comment(id):
    post = CommunityPost.query.get_or_404(id)
    form = CommentForm()
    
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            author_id=current_user.id,
            post_id=id,
            parent_id=form.parent_id.data if form.parent_id.data else None
        )
        
        db.session.add(comment)
        db.session.commit()
        
        flash('Comment added successfully!', 'success')
    else:
        flash('Error adding comment. Please try again.', 'error')
    
    return redirect(url_for('community.post_detail', id=id))

@community_bp.route('/post/<int:id>/like', methods=['POST'])
@login_required
def like_post(id):
    post = CommunityPost.query.get_or_404(id)
    existing = PostLike.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if existing:
        # Unlike: remove like and decrement count (floor at 0)
        db.session.delete(existing)
        post.likes = max(0, (post.likes or 0) - 1)
        db.session.commit()
        return jsonify({'likes': post.likes, 'liked': False})
    else:
        # Like: add association and increment count
        new_like = PostLike(user_id=current_user.id, post_id=post.id)
        db.session.add(new_like)
        post.likes = (post.likes or 0) + 1
        db.session.commit()
        return jsonify({'likes': post.likes, 'liked': True})

@community_bp.route('/chat')
@login_required
def chat():
    # Optional: redirect to a specific room via query params
    room_param = request.args.get('room')
    room_name_param = request.args.get('room_name')
    if room_param:
        return redirect(url_for('community.chat_room', room_id=room_param))
    if room_name_param:
        slug = ''.join(c.lower() if c.isalnum() else '-' for c in room_name_param).strip('-') or f"room-{uuid.uuid4().hex[:6]}"
        return redirect(url_for('community.chat_room', room_id=slug))

    # Get available chat rooms (default + persisted)
    default_rooms = [
        {'id': 'general', 'name': 'General Discussion'},
        {'id': 'resources', 'name': 'Resource Discussion'},
        {'id': 'help', 'name': 'Help & Support'},
        {'id': 'announcements', 'name': 'Announcements'}
    ]
    db_rooms = ChatRoom.query.order_by(ChatRoom.created_at.desc()).all()
    return render_template('community/chat.html', rooms=default_rooms, db_rooms=db_rooms)

@community_bp.route('/chat/create', methods=['POST'])
@login_required
def create_chat_room():
    name = request.form.get('room_name', '').strip()
    description = request.form.get('room_description', '').strip()
    room_type = request.form.get('room_type', 'public')
    if not name:
        flash('Room name is required', 'error')
        return redirect(url_for('community.chat'))
    slug = ''.join(c.lower() if c.isalnum() else '-' for c in name).strip('-') or f"room-{uuid.uuid4().hex[:6]}"
    # Ensure unique slug
    existing = ChatRoom.query.filter_by(room_id=slug).first()
    if existing:
        flash('Room already exists. Redirected to it.', 'info')
        return redirect(url_for('community.chat_room', room_id=slug))
    room = ChatRoom(
        room_id=slug,
        name=name,
        description=description,
        is_private=(room_type == 'private'),
        created_by=current_user.id
    )
    db.session.add(room)
    db.session.commit()
    return redirect(url_for('community.chat_room', room_id=slug))

@community_bp.route('/chat/<room_id>')
@login_required
def chat_room(room_id):
    # Get recent messages for the room
    messages = ChatMessage.query.filter_by(room=room_id).order_by(ChatMessage.timestamp.desc()).limit(50).all()
    messages.reverse()  # Show oldest first
    
    return render_template('community/chat_room.html',
                         room_id=room_id,
                         messages=messages)

@community_bp.route('/chat/<room_id>/messages')
@login_required
def get_room_messages(room_id):
    """API endpoint to get messages for a specific room"""
    messages = ChatMessage.query.filter_by(room=room_id).order_by(ChatMessage.timestamp.asc()).limit(50).all()
    
    return jsonify({
        'messages': [{
            'id': msg.id,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat(),
            'sender': {
                'id': msg.sender.id,
                'username': msg.sender.username
            }
        } for msg in messages]
    })

@community_bp.route('/chat/test')
@login_required
def test_chat():
    """Test endpoint to check chat functionality"""
    return jsonify({
        'status': 'success',
        'user': current_user.username,
        'authenticated': current_user.is_authenticated,
        'rooms': [{'id': room.room_id, 'name': room.name} for room in ChatRoom.query.all()],
        'messages': ChatMessage.query.count()
    })

@community_bp.route('/chat/test-socket')
@login_required
def test_socket():
    """Test Socket.IO functionality"""
    from app import socketio
    # Send a test message to all connected clients
    socketio.emit('receive_message', {
        'message': 'Test message from server',
        'username': 'Server',
        'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }, room='general')
    return jsonify({'status': 'Test message sent'})

@community_bp.route('/video_call')
@login_required
def video_calls():
    active_calls = VideoCall.query.filter_by(is_active=True).order_by(VideoCall.created_at.desc()).all()
    return render_template('community/video_calls.html', active_calls=active_calls)

@community_bp.route('/video_call/create', methods=['GET', 'POST'])
@login_required
def create_video_call():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        max_participants = request.form.get('max_participants', 10, type=int)
        
        room_id = str(uuid.uuid4())
        
        video_call = VideoCall(
            room_id=room_id,
            title=title,
            description=description,
            host_id=current_user.id,
            max_participants=max_participants
        )
        
        db.session.add(video_call)
        db.session.commit()
        
        flash('Video call room created successfully!', 'success')
        return redirect(url_for('community.video_call_room', room_id=room_id))
    
    return render_template('community/create_video_call.html')

@community_bp.route('/video_call/<room_id>')
@login_required
def video_call_room(room_id):
    video_call = VideoCall.query.filter_by(room_id=room_id).first_or_404()
    return render_template('community/video_call_room.html', video_call=video_call)

@community_bp.route('/files')
@login_required
def files():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', 'all')
    status = request.args.get('status', 'all')
    
    query = FileSubmission.query
    
    if category != 'all':
        query = query.filter_by(category=category)
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    # Non-admin users can only see approved files and their own submissions
    if not current_user.is_admin():
        query = query.filter(
            (FileSubmission.status == 'approved') |
            (FileSubmission.submitter_id == current_user.id)
        )
    
    files = query.order_by(FileSubmission.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    categories = ['research', 'report', 'documentation', 'image', 'other']
    
    return render_template('community/files.html',
                         files=files,
                         categories=categories,
                         current_category=category,
                         current_status=status)

@community_bp.route('/files/submit', methods=['GET', 'POST'])
@login_required
def submit_file():
    form = FileSubmissionForm()
    if form.validate_on_submit():
        # Handle file upload
        if form.file.data:
            filename = secure_filename(form.file.data.filename)
            if filename:
                file_ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4()}.{file_ext}"
                
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'submissions', unique_filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                form.file.data.save(file_path)
                
                file_submission = FileSubmission(
                    title=form.title.data,
                    description=form.description.data,
                    filename=unique_filename,
                    original_filename=filename,
                    file_type=file_ext,
                    file_size=os.path.getsize(file_path),
                    reference=form.reference.data,
                    category=form.category.data,
                    submitter_id=current_user.id
                )
                
                db.session.add(file_submission)
                db.session.commit()
                
                flash('File submitted successfully! It will be reviewed before being published.', 'success')
                return redirect(url_for('community.files'))
        else:
            flash('Please select a file to upload.', 'error')
    
    return render_template('community/submit_file.html', form=form)
