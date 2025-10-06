from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, CommunityPost, Notification
from sqlalchemy import desc
from forms import LoginForm, RegistrationForm, EditProfileForm
from datetime import datetime
from urllib.parse import urlparse as url_parse
import re

auth_bp = Blueprint('auth', __name__)

# Normalize and sanitize next URL so we never redirect to POST-only endpoints
# and never redirect off-site.
def _safe_next_url(next_url: str) -> str:
    try:
        if not next_url:
            return url_for('main.dashboard')
        parsed = url_parse(next_url)
        # Disallow external hosts
        if parsed.netloc:
            return url_for('main.dashboard')
        path = parsed.path or '/'
        # Map common POST-only community endpoints to safe GET pages
        # 1) Comment on post → post detail with comments anchor
        m = re.match(r'^/community/post/(\d+)/comment$', path)
        if m:
            post_id = int(m.group(1))
            return url_for('community.post_detail', id=post_id) + '#comments'
        # 2) Like post → post detail
        m = re.match(r'^/community/post/(\d+)/like$', path)
        if m:
            post_id = int(m.group(1))
            return url_for('community.post_detail', id=post_id)
        # 3) Like comment → resolve to that comment's post then go to comments
        m = re.match(r'^/community/comment/(\d+)/like$', path)
        if m:
            try:
                from models import Comment  # local import to avoid cycles
                comment_id = int(m.group(1))
                comment = Comment.query.get(comment_id)
                if comment:
                    return url_for('community.post_detail', id=comment.post_id) + '#comments'
            except Exception:
                pass
            return url_for('community.index')
        # 4) Chat room create (POST) → chat landing
        if path == '/community/chat/create':
            return url_for('community.chat')
        # 5) End video call (POST) → video call room
        m = re.match(r'^/community/video_call/([^/]+)/end$', path)
        if m:
            room_id = m.group(1)
            return url_for('community.video_call_room', room_id=room_id)
        # Fallback: if path looks like a normal page, keep it as-is
        # but ensure it starts with '/'
        if not path.startswith('/'):
            path = '/' + path
        # Re-append query string if present
        if parsed.query:
            return f"{path}?{parsed.query}"
        return path
    except Exception:
        return url_for('main.dashboard')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            user.last_seen = datetime.utcnow()
            db.session.commit()
            
            # Preserve intended destination from query string or hidden form field
            raw_next = request.args.get('next') or request.form.get('next')
            next_page = _safe_next_url(raw_next)
            return redirect(next_page)
        flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.email.data)
        ).first()
        
        if existing_user:
            if existing_user.username == form.username.data:
                flash('Username already exists. Please choose a different one.', 'error')
            else:
                flash('Email already registered. Please use a different email.', 'error')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            location=form.location.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    # Show recent posts by the logged-in user
    posts = CommunityPost.query.filter_by(author_id=current_user.id).order_by(desc(CommunityPost.created_at)).limit(10).all()
    return render_template('auth/profile.html', user=current_user, posts=posts)

@auth_bp.route('/u/<string:username>')
def public_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = CommunityPost.query.filter_by(author_id=user.id).order_by(desc(CommunityPost.created_at)).limit(10).all()
    return render_template('auth/public_profile.html', user=user, posts=posts)

@auth_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.location = form.location.data
        current_user.bio = form.bio.data
        # Handle avatar upload
        if form.avatar.data:
            from werkzeug.utils import secure_filename
            import os, uuid
            filename = secure_filename(form.avatar.data.filename)
            if filename:
                file_ext = filename.rsplit('.', 1)[-1].lower()
                unique_filename = f"{uuid.uuid4()}.{file_ext}"
                avatar_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
                os.makedirs(avatar_dir, exist_ok=True)
                path = os.path.join(avatar_dir, unique_filename)
                form.avatar.data.save(path)
                current_user.avatar = unique_filename
        
        db.session.commit()
        flash('Your profile has been updated successfully.', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html', form=form)

@auth_bp.route('/terms-of-service')
def terms_of_service():
    return render_template('auth/terms_of_service.html')

@auth_bp.route('/privacy-policy')
def privacy_policy():
    return render_template('auth/privacy_policy.html')

@auth_bp.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow_user(user_id):
    """Follow a user"""
    user_to_follow = User.query.get_or_404(user_id)
    
    if current_user == user_to_follow:
        flash('You cannot follow yourself.', 'error')
        return redirect(url_for('auth.public_profile', username=user_to_follow.username))
    
    if current_user.follow(user_to_follow):
        # Create notification for the followed user
        notification = Notification(
            user_id=user_to_follow.id,
            title='New Follower',
            message=f'{current_user.get_full_name()} started following you.',
            notification_type='info',
            url=url_for('auth.user_followers', user_id=user_to_follow.id)
        )
        db.session.add(notification)
        db.session.commit()
        
        flash(f'You are now following {user_to_follow.get_full_name()}.', 'success')
    else:
        flash(f'You are already following {user_to_follow.get_full_name()}.', 'info')
    
    return redirect(url_for('auth.public_profile', username=user_to_follow.username))

@auth_bp.route('/unfollow/<int:user_id>', methods=['POST'])
@login_required
def unfollow_user(user_id):
    """Unfollow a user"""
    user_to_unfollow = User.query.get_or_404(user_id)
    
    if current_user.unfollow(user_to_unfollow):
        flash(f'You have unfollowed {user_to_unfollow.get_full_name()}.', 'success')
    else:
        flash(f'You were not following {user_to_unfollow.get_full_name()}.', 'info')
    
    return redirect(url_for('auth.public_profile', username=user_to_unfollow.username))

@auth_bp.route('/profile/<int:user_id>/followers')
@login_required
def user_followers(user_id):
    """Show user's followers"""
    user = User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    
    followers = user.followers.paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('auth/followers.html', user=user, followers=followers)

@auth_bp.route('/profile/<int:user_id>/following')
@login_required
def user_following(user_id):
    """Show users that this user is following"""
    user = User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    
    following = user.following.paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('auth/following.html', user=user, following=following)