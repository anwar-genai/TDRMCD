from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from models import db, CommunityPost, Comment, ChatMessage, FileSubmission, VideoCall, PostLike, ChatRoom, CommentLike
from forms import CommunityPostForm, CommentForm, FileSubmissionForm
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime, timedelta
import jwt

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
    
    # Liked state for posts on this page
    liked_post_ids = set()
    if current_user.is_authenticated and posts.items:
        from models import PostLike
        page_post_ids = [p.id for p in posts.items]
        likes = PostLike.query.filter(
            PostLike.user_id == current_user.id,
            PostLike.post_id.in_(page_post_ids)
        ).with_entities(PostLike.post_id).all()
        liked_post_ids = {pid for (pid,) in likes}
    
    return render_template('community/index.html',
                         posts=posts,
                         categories=categories,
                         current_category=category,
                         current_sort=sort_by,
                         liked_post_ids=liked_post_ids)

@community_bp.route('/post/<int:id>')
def post_detail(id):
    post = CommunityPost.query.get_or_404(id)
    
    # Increment view count
    post.views += 1
    db.session.commit()
    
    # Get comments
    comments = Comment.query.filter_by(post_id=id, parent_id=None).order_by(Comment.created_at.asc()).all()
    
    comment_form = CommentForm()
    # Determine if current user liked this post
    liked_by_me = False
    if current_user.is_authenticated:
        liked_by_me = PostLike.query.filter_by(user_id=current_user.id, post_id=post.id).first() is not None

    return render_template('community/post_detail.html',
                         post=post,
                         comments=comments,
                         comment_form=comment_form,
                         liked_by_me=liked_by_me)

@community_bp.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    form = CommunityPostForm()
    if form.validate_on_submit():
        # Auto-generate title if blank (first 60 chars of content)
        auto_title = (form.content.data or '').strip().split('\n')[0][:60]
        post = CommunityPost(
            title=(form.title.data.strip() if form.title.data else auto_title) or 'Untitled',
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
        # Robustly parse parent_id from form data (handle duplicate inputs)
        parent_id = None
        parent_candidates = request.form.getlist('parent_id') or []
        for val in reversed(parent_candidates):
            try:
                if val and int(val) > 0:
                    parent_id = int(val)
                    break
            except ValueError:
                continue
        comment = Comment(
            content=form.content.data,
            author_id=current_user.id,
            post_id=id,
            parent_id=parent_id
        )
        
        db.session.add(comment)
        db.session.commit()
        
        flash('Comment added successfully!', 'success')
    else:
        flash('Error adding comment. Please try again.', 'error')
    
    return redirect(url_for('community.post_detail', id=id))

@community_bp.route('/comment/<int:comment_id>/like', methods=['POST'])
@login_required
def like_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    existing = CommentLike.query.filter_by(user_id=current_user.id, comment_id=comment.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        liked = False
    else:
        db.session.add(CommentLike(user_id=current_user.id, comment_id=comment.id))
        db.session.commit()
        liked = True
    # Return new like count
    likes_count = CommentLike.query.filter_by(comment_id=comment.id).count()
    return jsonify({'likes': likes_count, 'liked': liked})

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
        # Handle both form and JSON requests
        if request.is_json:
            data = request.get_json()
            title = data.get('title')
            description = data.get('description')
            max_participants = data.get('max_participants', 10)
        else:
            title = request.form.get('title')
            description = request.form.get('description')
            max_participants = request.form.get('max_participants', 10, type=int)
        
        room_id = str(uuid.uuid4())
        
        chat_room = data.get('chat_room') if request.is_json else request.form.get('chat_room')
        
        video_call = VideoCall(
            room_id=room_id,
            title=title,
            description=description,
            host_id=current_user.id,
            chat_room=chat_room,
            max_participants=max_participants
        )
        
        db.session.add(video_call)
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'success': True,
                'room_id': room_id,
                'room_url': url_for('community.video_call_room', room_id=room_id)
            })
        else:
            flash('Video call room created successfully!', 'success')
            return redirect(url_for('community.video_call_room', room_id=room_id))
    
    return render_template('community/create_video_call.html')

@community_bp.route('/video_call/check/<chat_room>')
@login_required
def check_video_call(chat_room):
    """Check if there's an active video call for a chat room"""
    video_call = VideoCall.query.filter_by(chat_room=chat_room, is_active=True).first()
    
    if video_call:
        return jsonify({
            'exists': True,
            'room_id': video_call.room_id,
            'room_url': url_for('community.video_call_room', room_id=video_call.room_id)
        })
    else:
        return jsonify({'exists': False})

@community_bp.route('/video_call/<room_id>')
@login_required
def video_call_room(room_id):
    video_call = VideoCall.query.filter_by(room_id=room_id).first_or_404()
    
    # JaaS (Jitsi as a Service) Configuration
    jitsi_app_id = current_app.config.get('JITSI_APP_ID')
    jitsi_app_secret = current_app.config.get('JITSI_APP_SECRET')
    jwt_token = None
    
    # Generate JWT token for JaaS authentication using official JaaS format
    jitsi_key_id = current_app.config.get('JITSI_KEY_ID')  # New: Key ID from JaaS console
    
    if jitsi_app_id and jitsi_app_secret and jitsi_key_id and jitsi_app_id != 'your-jaas-app-id-here':
        try:
            import time
            
            # Get user display name safely
            user_name = current_user.username
            if hasattr(current_user, 'first_name') and hasattr(current_user, 'last_name'):
                if current_user.first_name and current_user.last_name:
                    user_name = f"{current_user.first_name} {current_user.last_name}"
            
            # Get avatar URL safely
            avatar_url = ""
            if hasattr(current_user, 'avatar_url') and current_user.avatar_url:
                avatar_url = url_for('static', filename=f'uploads/avatars/{current_user.avatar_url}', _external=True)
            
            # JaaS JWT payload structure matching official documentation
            is_moderator = (video_call.host_id == current_user.id)
            current_time = int(time.time())
            
            # JWT Header (required by JaaS)
            headers = {
                'alg': 'RS256',
                'kid': jitsi_key_id,  # CRITICAL: Key ID from JaaS console
                'typ': 'JWT'
            }
            
            # JWT Payload (as per official JaaS documentation)
            payload = {
                'aud': 'jitsi',
                'iss': 'chat',  # Hardcoded value as per docs
                'sub': jitsi_app_id,
                'room': '*',  # Wildcard for all rooms
                'iat': current_time,
                'exp': current_time + 7200,  # 2 hours
                'nbf': current_time - 10,    # Not before
                
                'context': {
                    'user': {
                        'id': str(current_user.id),
                        'name': user_name,
                        'email': current_user.email,
                        'avatar': avatar_url,
                        'moderator': is_moderator  # Boolean, not string
                    },
                    'features': {
                        'livestreaming': False,
                        'recording': False,
                        'transcription': False,
                        'outbound-call': False,
                        'sip-inbound-call': False,
                        'sip-outbound-call': False
                    }
                }
            }
            
            # Generate JWT token with headers (CRITICAL for JaaS)
            jwt_token = jwt.encode(payload, jitsi_app_secret, algorithm='RS256', headers=headers)
            
            current_app.logger.info(f"Generated JaaS JWT token for room: {room_id}")
            current_app.logger.info(f"User: {user_name} (ID: {current_user.id})")
            current_app.logger.info(f"Moderator: {is_moderator}")
            current_app.logger.info(f"App ID: {jitsi_app_id}")
            current_app.logger.info(f"Key ID: {jitsi_key_id}")
            
        except Exception as e:
            current_app.logger.error(f"Error generating JaaS JWT token: {e}")
            current_app.logger.error(f"App ID: {jitsi_app_id}")
            current_app.logger.error(f"Key ID: {jitsi_key_id}")
            current_app.logger.error(f"Private key format check: {jitsi_app_secret.startswith('-----BEGIN') if jitsi_app_secret else False}")
            jwt_token = None
    else:
        current_app.logger.info("JaaS not configured, using public Jitsi rooms")
        current_app.logger.info(f"App ID: {jitsi_app_id}")
        current_app.logger.info(f"App Secret configured: {bool(jitsi_app_secret)}")
    
    return render_template('community/video_call_room.html', 
                         video_call=video_call, 
                         jwt_token=jwt_token, 
                         jitsi_app_id=jitsi_app_id)

@community_bp.route('/video_call/test-jwt')
@login_required
def test_jwt():
    """Test JWT generation for debugging"""
    jitsi_app_id = current_app.config.get('JITSI_APP_ID')
    jitsi_app_secret = current_app.config.get('JITSI_APP_SECRET')
    
    if not jitsi_app_id or not jitsi_app_secret:
        return jsonify({
            'error': 'JaaS not configured',
            'app_id': jitsi_app_id,
            'has_secret': bool(jitsi_app_secret)
        })
    
    try:
        import time
        
        # JaaS-compatible test payload
        current_time = int(time.time())
        payload = {
            # Standard JWT claims
            'aud': 'jitsi',
            'iss': 'chat',
            'sub': jitsi_app_id,
            'room': '*',
            'iat': current_time,
            'exp': current_time + 3600,  # 1 hour
            'nbf': current_time - 10,    # Not before
            
            # JaaS context
            'context': {
                'user': {
                    'id': str(current_user.id),
                    'name': current_user.username,
                    'email': current_user.email,
                    'avatar': '',
                    'moderator': True
                },
                'features': {
                    'livestreaming': False,
                    'recording': False,
                    'transcription': False,
                    'outbound-call': False
                }
            }
        }
        
        # Use RS256 algorithm for JaaS
        token = jwt.encode(payload, jitsi_app_secret, algorithm='RS256')
        
        return jsonify({
            'success': True,
            'app_id': jitsi_app_id,
            'payload': payload,
            'token_preview': token[:50] + '...',
            'secret_length': len(jitsi_app_secret)
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'app_id': jitsi_app_id,
            'secret_length': len(jitsi_app_secret) if jitsi_app_secret else 0
        })

@community_bp.route('/video_call/webrtc-test')
@login_required
def webrtc_test():
    """WebRTC compatibility test page"""
    return render_template('community/webrtc_test.html')

@community_bp.route('/video_call/<room_id>/end', methods=['POST'])
@login_required
def end_video_call(room_id):
    video_call = VideoCall.query.filter_by(room_id=room_id).first_or_404()
    
    # Only the host can end the call
    if video_call.host_id != current_user.id:
        return jsonify({'success': False, 'message': 'Only the host can end the call'})
    
    video_call.is_active = False
    video_call.ended_at = datetime.utcnow()
    db.session.commit()
    
    # Notify chat room that call ended
    from app import socketio
    if video_call.chat_room:
        socketio.emit('video_call_ended', {
            'message': f'Video call "{video_call.title}" has ended',
            'video_room_id': room_id,
            'chat_room': video_call.chat_room
        }, room=video_call.chat_room)
        
        # Also emit to all connected users to ensure they get the update
        socketio.emit('video_call_ended', {
            'message': f'Video call "{video_call.title}" has ended',
            'video_room_id': room_id,
            'chat_room': video_call.chat_room
        })
        
        current_app.logger.info(f"Video call ended notification sent for room: {video_call.chat_room}")
    
    return jsonify({'success': True, 'message': 'Video call ended'})

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
