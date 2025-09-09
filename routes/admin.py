from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, User, Resource, CommunityPost, FileSubmission, Campaign, Notification
from forms import CampaignForm
from functools import wraps
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    # Get statistics
    stats = {
        'total_users': User.query.count(),
        'total_resources': Resource.query.count(),
        'pending_resources': Resource.query.filter_by(status='under_review').count(),
        'total_posts': CommunityPost.query.count(),
        'pending_files': FileSubmission.query.filter_by(status='pending').count(),
        'active_campaigns': Campaign.query.filter_by(is_active=True).count()
    }
    
    # Get recent activities
    recent_resources = Resource.query.order_by(Resource.created_at.desc()).limit(5).all()
    recent_posts = CommunityPost.query.order_by(CommunityPost.created_at.desc()).limit(5).all()
    pending_files = FileSubmission.query.filter_by(status='pending').limit(5).all()
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_resources=recent_resources,
                         recent_posts=recent_posts,
                         pending_files=pending_files)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role = request.args.get('role', 'all')
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.email.contains(search)) |
            (User.first_name.contains(search)) |
            (User.last_name.contains(search))
        )
    
    if role != 'all':
        query = query.filter_by(role=role)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', users=users, search=search, role=role)

@admin_bp.route('/users/<int:user_id>/toggle_status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/change_role', methods=['POST'])
@login_required
@admin_required
def change_user_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    
    if new_role in ['user', 'admin', 'researcher']:
        user.role = new_role
        db.session.commit()
        flash(f'User {user.username} role changed to {new_role}.', 'success')
    else:
        flash('Invalid role specified.', 'error')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/resources')
@login_required
@admin_required
def resources():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    category = request.args.get('category', 'all')
    
    query = Resource.query
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    if category != 'all':
        query = query.filter_by(category=category)
    
    resources = query.order_by(Resource.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/resources.html', resources=resources, status=status, category=category)

@admin_bp.route('/resources/<int:resource_id>/change_status', methods=['POST'])
@login_required
@admin_required
def change_resource_status(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    new_status = request.form.get('status')
    
    if new_status in ['active', 'inactive', 'under_review']:
        resource.status = new_status
        db.session.commit()
        
        # Create notification for resource author
        notification = Notification(
            title=f'Resource Status Update',
            message=f'Your resource "{resource.title}" status has been changed to {new_status}.',
            notification_type='info',
            user_id=resource.author_id
        )
        db.session.add(notification)
        db.session.commit()
        
        flash(f'Resource status changed to {new_status}.', 'success')
    else:
        flash('Invalid status specified.', 'error')
    
    return redirect(url_for('admin.resources'))

@admin_bp.route('/file_submissions')
@login_required
@admin_required
def file_submissions():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'pending')
    
    query = FileSubmission.query
    if status != 'all':
        query = query.filter_by(status=status)
    
    submissions = query.order_by(FileSubmission.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/file_submissions.html', submissions=submissions, status=status)

@admin_bp.route('/file_submissions/<int:submission_id>/review', methods=['POST'])
@login_required
@admin_required
def review_file_submission(submission_id):
    submission = FileSubmission.query.get_or_404(submission_id)
    action = request.form.get('action')
    review_notes = request.form.get('review_notes', '')
    
    if action in ['approve', 'reject']:
        submission.status = 'approved' if action == 'approve' else 'rejected'
        submission.reviewed_by = current_user.id
        submission.review_notes = review_notes
        submission.reviewed_at = datetime.utcnow()
        
        # Create notification for submitter
        notification = Notification(
            title=f'File Submission {action.title()}d',
            message=f'Your file submission "{submission.title}" has been {action}d. {review_notes}',
            notification_type='success' if action == 'approve' else 'warning',
            user_id=submission.submitter_id
        )
        db.session.add(notification)
        db.session.commit()
        
        flash(f'File submission {action}d successfully.', 'success')
    else:
        flash('Invalid action specified.', 'error')
    
    return redirect(url_for('admin.file_submissions'))

@admin_bp.route('/campaigns')
@login_required
@admin_required
def campaigns():
    page = request.args.get('page', 1, type=int)
    campaigns = Campaign.query.order_by(Campaign.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/campaigns.html', campaigns=campaigns)

@admin_bp.route('/campaigns/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_campaign():
    form = CampaignForm()
    if form.validate_on_submit():
        campaign = Campaign(
            title=form.title.data,
            description=form.description.data,
            content=form.content.data,
            campaign_type=form.campaign_type.data,
            target_audience=form.target_audience.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            created_by=current_user.id
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        flash('Campaign created successfully!', 'success')
        return redirect(url_for('admin.campaigns'))
    
    return render_template('admin/create_campaign.html', form=form)

@admin_bp.route('/campaigns/<int:campaign_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    campaign.is_active = not campaign.is_active
    db.session.commit()
    
    status = 'activated' if campaign.is_active else 'deactivated'
    flash(f'Campaign "{campaign.title}" has been {status}.', 'success')
    return redirect(url_for('admin.campaigns'))

@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    # Get analytics data
    analytics_data = {
        'user_registrations': get_user_registration_stats(),
        'resource_submissions': get_resource_submission_stats(),
        'community_activity': get_community_activity_stats(),
        'popular_resources': get_popular_resources(),
        'active_users': get_active_users_stats()
    }
    
    return render_template('admin/analytics.html', analytics=analytics_data)

def get_user_registration_stats():
    # Implementation for user registration statistics
    # This would typically involve querying the database for user counts by date
    return {}

def get_resource_submission_stats():
    # Implementation for resource submission statistics
    return {}

def get_community_activity_stats():
    # Implementation for community activity statistics
    return {}

def get_popular_resources():
    # Implementation for popular resources
    return Resource.query.order_by(Resource.created_at.desc()).limit(10).all()

def get_active_users_stats():
    # Implementation for active users statistics
    return {}
