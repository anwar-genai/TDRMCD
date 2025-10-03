from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, abort
from flask_login import login_required, current_user
from models import db, CommunityPost, Comment, ChatMessage, FileSubmission, VideoCall, PostLike, ChatRoom, CommentLike, Notification
from forms import CommunityPostForm, CommentForm, FileSubmissionForm
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime, timedelta
import jwt
from sqlalchemy import func

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

    # Recent shared files widget (approved or own)
    files_query = FileSubmission.query
    if not current_user.is_authenticated or not current_user.is_admin():
        # Non-admins: show approved files only
        files_query = files_query.filter_by(status='approved')
    recent_files = files_query.order_by(FileSubmission.created_at.desc()).limit(6).all()
    
    return render_template('community/index.html',
                         posts=posts,
                         categories=categories,
                         current_category=category,
                         current_sort=sort_by,
                         liked_post_ids=liked_post_ids,
                         recent_files=recent_files)

@community_bp.route('/post/<int:id>')
def post_detail(id):
    post = CommunityPost.query.get_or_404(id)
    
    # Increment view count
    post.views += 1
    db.session.commit()
    
    # Get comments (top-level first)
    comments = Comment.query.filter_by(post_id=id, parent_id=None).order_by(Comment.created_at.asc()).all()
    
    # Build list of all comment IDs (including replies) for like aggregation
    all_comment_ids = []
    for c in comments:
        all_comment_ids.append(c.id)
        for r in (c.replies or []):
            all_comment_ids.append(r.id)
    
    # Aggregate like counts per comment
    comment_like_counts = {}
    if all_comment_ids:
        rows = db.session.query(CommentLike.comment_id, func.count(CommentLike.id)) \
            .filter(CommentLike.comment_id.in_(all_comment_ids)) \
            .group_by(CommentLike.comment_id).all()
        comment_like_counts = {cid: cnt for cid, cnt in rows}
    
    # Determine which comments current user liked
    comments_liked_by_me = set()
    if current_user.is_authenticated and all_comment_ids:
        liked_rows = CommentLike.query.filter(
            CommentLike.user_id == current_user.id,
            CommentLike.comment_id.in_(all_comment_ids)
        ).with_entities(CommentLike.comment_id).all()
        comments_liked_by_me = {cid for (cid,) in liked_rows}
    
    comment_form = CommentForm()
    # Determine if current user liked this post
    liked_by_me = False
    if current_user.is_authenticated:
        liked_by_me = PostLike.query.filter_by(user_id=current_user.id, post_id=post.id).first() is not None

    return render_template('community/post_detail.html',
                         post=post,
                         comments=comments,
                         comment_form=comment_form,
                         liked_by_me=liked_by_me,
                         comment_like_counts=comment_like_counts,
                         comments_liked_by_me=comments_liked_by_me)

@community_bp.route('/post/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = CommunityPost.query.get_or_404(id)
    # Only the author can edit
    if current_user.id != post.author_id:
        abort(403)

    form = CommunityPostForm(obj=post)

    if form.validate_on_submit():
        # Respect content-only (quick) mode when updating
        post_type = (request.form.get('post_type') or '').strip()
        is_quick = (post_type == 'quick')

        # Update fields
        post.content = form.content.data
        post.category = form.category.data
        post.tags = form.tags.data
        post.title = '' if is_quick else (form.title.data or '').strip()

        # Optional: replace image if a new one is uploaded (skip in quick mode)
        if (not is_quick) and form.image.data:
            filename = secure_filename(form.image.data.filename)
            if filename:
                file_ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4()}.{file_ext}"
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts', unique_filename)
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                form.image.data.save(image_path)
                post.image_url = f"posts/{unique_filename}"

        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('community.post_detail', id=post.id))

    # Preselect content-only mode in UI if post has no title
    is_content_only = (not (post.title or '').strip())
    return render_template('community/edit_post.html', form=form, post=post, is_content_only=is_content_only)

@community_bp.route('/post/<int:id>/delete', methods=['POST'])
@login_required
def delete_post(id):
    post = CommunityPost.query.get_or_404(id)
    # Only the author can delete
    if current_user.id != post.author_id:
        abort(403)

    try:
        db.session.delete(post)
        db.session.commit()
        # AJAX request: return JSON for smoother UX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.best == 'application/json'
        if is_ajax:
            return jsonify({'success': True})
        flash('Post deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.best == 'application/json'
        if is_ajax:
            return jsonify({'success': False, 'error': 'delete_failed'}), 400
        flash('Error deleting post. Please try again.', 'error')
    # Prefer redirect to profile if deleting from detail page
    try:
        ref = request.headers.get('Referer') or ''
        target = url_for('auth.profile') if f"/community/post/{id}" in ref else url_for('community.index')
        return redirect(target)
    except Exception:
        return redirect(url_for('community.index'))

@community_bp.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    form = CommunityPostForm()
    if form.validate_on_submit():
        # Determine category from post_type if provided
        post_type = (request.form.get('post_type') or '').strip()
        type_to_category = {
            'discussion': 'discussion',
            'question': 'question',
            'announcement': 'announcement',
            'news': 'news',
            'quick': 'discussion'  # fallback category for content-only quick update
        }
        resolved_category = type_to_category.get(post_type, (form.category.data or 'discussion'))

        # For content-only (quick), keep title empty
        is_content_only = (post_type == 'quick')
        content_text = form.content.data
        auto_title = (content_text or '').strip().split('\n')[0][:60]
        final_title = '' if is_content_only else ((form.title.data.strip() if form.title.data else auto_title) or 'Untitled')

        post = CommunityPost(
            title=final_title,
            content=content_text,
            category=resolved_category,
            tags=form.tags.data,
            author_id=current_user.id
        )
        
        # Handle image upload (skip by UI when quick type, but backend is tolerant)
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
        
        # Notifications
        try:
            # Reply to a comment
            if parent_id:
                parent_comment = Comment.query.get(parent_id)
                if parent_comment and parent_comment.author_id != current_user.id:
                    db.session.add(Notification(
                        title='New reply to your comment',
                        message=f"{current_user.get_full_name()} replied on '{post.title[:40] or 'your post'}': {comment.content[:80]}",
                        notification_type='info',
                        user_id=parent_comment.author_id,
                        url=url_for('community.post_detail', id=post.id) + '#comments'
                    ))
            # Top-level comment on a post
            else:
                if post.author_id != current_user.id:
                    db.session.add(Notification(
                        title='New comment on your post',
                        message=f"{current_user.get_full_name()} commented on '{post.title[:40] or 'your post'}'",
                        notification_type='info',
                        user_id=post.author_id,
                        url=url_for('community.post_detail', id=post.id) + '#comments'
                    ))
            db.session.commit()
        except Exception:
            db.session.rollback()
            # Fail silently for notifications
            pass
        
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
        # Notify comment author on like
        try:
            if comment.author_id != current_user.id:
                db.session.add(Notification(
                    title='Your comment was liked',
                    message=f"{current_user.get_full_name()} liked your comment",
                    notification_type='success',
                    user_id=comment.author_id,
                    url=url_for('community.post_detail', id=comment.post_id) + '#comments'
                ))
                db.session.commit()
        except Exception:
            db.session.rollback()
            pass
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
        # Notify post author on like
        try:
            if post.author_id != current_user.id:
                db.session.add(Notification(
                    title='Your post was liked',
                    message=f"{current_user.get_full_name()} liked your post '{post.title[:40] or 'post'}'",
                    notification_type='success',
                    user_id=post.author_id,
                    url=url_for('community.post_detail', id=post.id)
                ))
                db.session.commit()
        except Exception:
            db.session.rollback()
            pass
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
    # Only show rooms user can see
    if current_user.is_authenticated and current_user.is_admin():
        db_rooms = ChatRoom.query.order_by(ChatRoom.created_at.desc()).all()
    else:
        db_rooms = ChatRoom.query.filter(
            (ChatRoom.is_private == False) | (ChatRoom.created_by == (current_user.id if current_user.is_authenticated else -1))
        ).order_by(ChatRoom.created_at.desc()).all()
    return render_template('community/chat.html', rooms=default_rooms, db_rooms=db_rooms)

@community_bp.route('/chat/create', methods=['POST'])
@login_required
def create_chat_room():
    name = request.form.get('room_name', '').strip()
    description = request.form.get('room_description', '').strip()
    room_type = request.form.get('room_type', 'public')
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.best == 'application/json'
    if not name:
        flash('Room name is required', 'error')
        return redirect(url_for('community.chat'))
    slug = ''.join(c.lower() if c.isalnum() else '-' for c in name).strip('-') or f"room-{uuid.uuid4().hex[:6]}"
    # Ensure unique slug
    existing = ChatRoom.query.filter_by(room_id=slug).first()
    if existing:
        if is_ajax:
            return jsonify({
                'exists': True,
                'room_id': slug,
                'room_url': url_for('community.chat_room', room_id=slug)
            })
        else:
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
    if is_ajax:
        return jsonify({
            'success': True,
            'room_id': slug,
            'room_url': url_for('community.chat_room', room_id=slug)
        })
    else:
        return redirect(url_for('community.chat_room', room_id=slug))

@community_bp.route('/chat/<room_id>')
@login_required
def chat_room(room_id):
    # Serve the same two-column chat template so refreshes and invites hydrate in-place
    default_rooms = [
        {'id': 'general', 'name': 'General Discussion'},
        {'id': 'resources', 'name': 'Resource Discussion'},
        {'id': 'help', 'name': 'Help & Support'},
        {'id': 'announcements', 'name': 'Announcements'}
    ]
    # Only show rooms user can see
    if current_user.is_authenticated and current_user.is_admin():
        db_rooms = ChatRoom.query.order_by(ChatRoom.created_at.desc()).all()
    else:
        db_rooms = ChatRoom.query.filter(
            (ChatRoom.is_private == False) | (ChatRoom.created_by == (current_user.id if current_user.is_authenticated else -1))
        ).order_by(ChatRoom.created_at.desc()).all()
    # The chat template will auto-join based on URL path
    return render_template('community/chat.html', rooms=default_rooms, db_rooms=db_rooms)

@community_bp.route('/chat/<room_id>/messages')
@login_required
def get_room_messages(room_id):
    """API endpoint to get messages for a specific room"""
    # Enforce private room access
    room = ChatRoom.query.filter_by(room_id=room_id).first()
    if room and room.is_private:
        allowed = current_user.is_authenticated and (current_user.is_admin() or room.created_by == current_user.id)
        if not allowed:
            return jsonify({'error': 'access denied'}), 403
    messages = ChatMessage.query.filter_by(room=room_id).order_by(ChatMessage.timestamp.asc()).limit(50).all()
    
    def format_message(msg):
        message_data = {
            'id': msg.id,
            'message': msg.content,  # Use 'message' key to match client expectation
            'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),  # Match client format
            'username': msg.sender.username,
            'message_type': getattr(msg, 'message_type', None) or 'text'
        }
        
        # For file messages, include file information
        if getattr(msg, 'message_type', None) == 'file' and getattr(msg, 'file_url', None):
            message_data['file'] = {
                'name': getattr(msg, 'file_name', None) or msg.content,
                'url': getattr(msg, 'file_url', None),
                'ext': getattr(msg, 'file_ext', None) or ''
            }
        
        return message_data
    
    return jsonify({
        'messages': [format_message(msg) for msg in messages]
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
        
        # Link to chat room if provided via query, form, or JSON
        chat_room = None
        if request.is_json:
            chat_room = (data.get('chat_room') or '').strip() if data else None
        else:
            chat_room = (request.form.get('chat_room') or request.args.get('room') or '').strip()

        # If no title provided (instant call UX), auto-generate a friendly one
        if not title:
            room_display = chat_room or 'General'
            title = f"Call in #{room_display}"
        if description is None:
            description = ''
        
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
                'room_url': url_for('community.video_call_room', room_id=room_id, _external=True)
            })
        else:
            return redirect(url_for('community.video_call_room', room_id=room_id))
    
    # GET request: if coming from chat with ?room=, create instantly and redirect
    prefill_room = (request.args.get('room') or '').strip()
    if prefill_room:
        # Prevent multiple active calls per room
        existing = VideoCall.query.filter_by(chat_room=prefill_room, is_active=True).first()
        if existing:
            return redirect(url_for('community.video_call_room', room_id=existing.room_id))
        # Create instant
        room_id = str(uuid.uuid4())
        video_call = VideoCall(
            room_id=room_id,
            title=f"Call in #{prefill_room}",
            description='',
            host_id=current_user.id,
            chat_room=prefill_room,
            max_participants=10
        )
        db.session.add(video_call)
        db.session.commit()
        # Announce availability to the chat room
        try:
            from app import socketio
            socketio.emit('video_call_available', {
                'video_room_id': room_id,
                'video_room_url': url_for('community.video_call_room', room_id=room_id, _external=True),
                'started_by': (current_user.get_full_name() if hasattr(current_user, 'get_full_name') else current_user.username)
            }, room=prefill_room)
        except Exception:
            pass
        return redirect(url_for('community.video_call_room', room_id=room_id))
    return render_template('community/create_video_call.html', chat_room=prefill_room)

@community_bp.route('/video_call/check/<chat_room>')
@login_required
def check_video_call(chat_room):
    """Check if there's an active video call for a chat room"""
    # Enforce private room access for call discovery
    room = ChatRoom.query.filter_by(room_id=chat_room).first()
    if room and room.is_private:
        allowed = current_user.is_authenticated and (current_user.is_admin() or room.created_by == current_user.id)
        if not allowed:
            return jsonify({'exists': False})
    video_call = VideoCall.query.filter_by(chat_room=chat_room, is_active=True).first()
    
    if video_call:
        return jsonify({
            'exists': True,
            'room_id': video_call.room_id,
            'room_url': url_for('community.video_call_room', room_id=video_call.room_id, _external=True)
        })
    else:
        return jsonify({'exists': False})

@community_bp.route('/video_call/<room_id>')
@login_required
def video_call_room(room_id):
    video_call = VideoCall.query.filter_by(room_id=room_id).first_or_404()
    # Prevent joining ended calls
    if not video_call.is_active:
        flash('This video call has ended.', 'warning')
        if video_call.chat_room:
            return redirect(url_for('community.chat_room', room_id=video_call.chat_room))
        return redirect(url_for('community.video_calls'))
    
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
                        'sip-outbound-call': False,
                        'whiteboard': True,
                        'jaas-subscription': True,
                        'outbound-call-v2': True,
                        'room-lock': True,
                        'lobby': False,
                        'moderation': True,
                        'virtual-background': True,
                        'video-sharing': True,
                        'tile-view': True
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
    
    return jsonify({'success': True, 'message': 'Video call ended', 'room': video_call.chat_room})

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

@community_bp.route('/files/<int:file_id>')
def file_detail(file_id):
    f = FileSubmission.query.get_or_404(file_id)
    # Visibility: approved files public; otherwise owner or admin only
    is_owner = current_user.is_authenticated and f.submitter_id == current_user.id
    is_admin = current_user.is_authenticated and current_user.is_admin()
    if f.status != 'approved' and not (is_owner or is_admin):
        flash('This file is not available.', 'warning')
        return redirect(url_for('community.files'))
    download_allowed = (f.status == 'approved') or is_owner or is_admin
    return render_template('community/file_detail.html', file=f, download_allowed=download_allowed)

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


@community_bp.route('/chat/upload', methods=['POST'])
@login_required
def chat_upload():
    """Upload a file to a chat room and emit a message with attachment details."""
    room = (request.form.get('room') or 'general').strip()
    caption = (request.form.get('caption') or '').strip()
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({'error': 'no_file'}), 400

    # Private room access check
    chat_room = ChatRoom.query.filter_by(room_id=room).first()
    if chat_room and chat_room.is_private:
        if not (current_user.is_authenticated and (current_user.is_admin() or chat_room.created_by == current_user.id)):
            return jsonify({'error': 'access_denied'}), 403

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    unique_name = f"{uuid.uuid4()}.{ext}" if ext else str(uuid.uuid4())

    upload_dir = os.path.join(current_app.root_path, 'uploads', 'chat')
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(upload_dir, unique_name)
    file.save(save_path)

    public_url = url_for('serve_uploaded_file', subdir='chat', filename=unique_name)

    # Save a chat message record
    chat_message = ChatMessage(
        content=caption or filename,
        sender_id=current_user.id,
        room=room,
        timestamp=datetime.utcnow(),
        message_type='file',
        file_url=public_url,
        file_name=filename,
        file_ext=ext
    )
    db.session.add(chat_message)
    db.session.commit()

    payload = {
        'message': caption or filename,
        'username': current_user.username,
        'timestamp': chat_message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'message_type': 'file',
        'file': {
            'name': filename,
            'url': public_url,
            'ext': ext
        },
        'room': room
    }
    try:
        from app import socketio
        socketio.emit('receive_message', payload, room=room)
    except Exception:
        pass

    return jsonify({'ok': True, 'message': payload})