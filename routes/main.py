from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, Resource, CommunityPost, Campaign, Notification, User
from sqlalchemy import or_, desc

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Get featured resources
    featured_resources = Resource.query.filter_by(status='active').order_by(desc(Resource.created_at)).limit(6).all()
    
    # Get recent community posts
    recent_posts = CommunityPost.query.order_by(desc(CommunityPost.created_at)).limit(5).all()
    
    # Get active campaigns
    active_campaigns = Campaign.query.filter_by(is_active=True).limit(3).all()
    
    # Real-time stats
    total_resources = Resource.query.filter_by(status='active').count()
    total_members = User.query.count()
    active_discussions = CommunityPost.query.count()
    active_campaigns_count = Campaign.query.filter_by(is_active=True).count()
    
    return render_template('main/index.html', 
                         featured_resources=featured_resources,
                         recent_posts=recent_posts,
                         active_campaigns=active_campaigns,
                         total_resources=total_resources,
                         total_members=total_members,
                         active_discussions=active_discussions,
                         active_campaigns_count=active_campaigns_count)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Update last_seen timestamp
    from datetime import datetime
    current_user.last_seen = datetime.utcnow()
    db.session.commit()
    
    # Get user's recent activities
    user_resources = current_user.resources.limit(5).all()
    user_posts = current_user.posts.limit(5).all()
    
    # Get notifications
    notifications = current_user.notifications.filter_by(is_read=False).limit(10).all()
    
    # Get statistics
    stats = {
        'total_resources': Resource.query.filter_by(status='active').count(),
        'user_resources': current_user.resources.count(),
        'user_posts': current_user.posts.count(),
        'unread_notifications': current_user.notifications.filter_by(is_read=False).count()
    }
    
    # Check if this is a new user (created within last 24 hours)
    from datetime import timedelta
    is_new_user = current_user.created_at > datetime.utcnow() - timedelta(hours=24)
    
    # Check if user hasn't been seen in a while (more than 7 days)
    is_long_absence = current_user.last_seen < datetime.utcnow() - timedelta(days=7)
    
    return render_template('main/dashboard.html',
                         user_resources=user_resources,
                         user_posts=user_posts,
                         notifications=notifications,
                         stats=stats,
                         is_new_user=is_new_user,
                         is_long_absence=is_long_absence)

@main_bp.route('/search')
def search():
    query = request.args.get('q', '')
    category = request.args.get('category', 'all')
    page = request.args.get('page', 1, type=int)
    
    if not query or not query.strip():
        # Redirect home or render search page with guidance
        return render_template('main/search.html', results=[], query='')
    
    # Search in resources
    resource_query = Resource.query.filter_by(status='active')
    if category != 'all':
        resource_query = resource_query.filter_by(category=category)
    
    resources = resource_query.filter(
        or_(
            Resource.title.contains(query),
            Resource.description.contains(query),
            Resource.location.contains(query)
        )
    ).paginate(
        page=page, per_page=12, error_out=False
    )
    
    # Search in community posts
    posts = CommunityPost.query.filter(
        or_(
            CommunityPost.title.contains(query),
            CommunityPost.content.contains(query),
            CommunityPost.tags.contains(query)
        )
    ).limit(10).all()
    
    # Search in users
    users = User.query.filter(
        or_(
            User.username.contains(query),
            User.first_name.contains(query),
            User.last_name.contains(query),
            User.location.contains(query),
            User.bio.contains(query)
        )
    ).limit(10).all()
    
    return render_template('main/search.html',
                         resources=resources,
                         posts=posts,
                         users=users,
                         query=query,
                         category=category)

@main_bp.route('/about')
def about():
    return render_template('main/about.html')

@main_bp.route('/contact')
def contact():
    return render_template('main/contact.html')

@main_bp.route('/map')
def map_view():
    # Get all resources with coordinates
    resources_with_coords = Resource.query.filter(
        Resource.latitude.isnot(None),
        Resource.longitude.isnot(None),
        Resource.status == 'active'
    ).all()
    
    # Convert to JSON format for map
    map_data = []
    for resource in resources_with_coords:
        map_data.append({
            'id': resource.id,
            'title': resource.title,
            'description': resource.description[:100] + '...' if len(resource.description) > 100 else resource.description,
            'category': resource.category,
            'latitude': resource.latitude,
            'longitude': resource.longitude,
            'location': resource.location
        })
    
    return render_template('main/map.html', map_data=map_data)

# Campaigns - public listing by type
@main_bp.route('/campaigns/<string:campaign_type>')
def campaigns_by_type(campaign_type):
    valid_types = {'education', 'health', 'sustainability'}
    if campaign_type not in valid_types:
        # Fallback to showing all active campaigns if invalid type
        campaigns = Campaign.query.filter_by(is_active=True).order_by(desc(Campaign.created_at)).all()
        current_type = 'all'
    else:
        campaigns = Campaign.query.filter_by(is_active=True, campaign_type=campaign_type).order_by(desc(Campaign.created_at)).all()
        current_type = campaign_type
    return render_template('main/campaigns.html', campaigns=campaigns, current_type=current_type)

# Campaign detail page
@main_bp.route('/campaign/<int:campaign_id>')
def campaign_detail(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if not campaign.is_active:
        # Optional: could 404 or show a notice
        return render_template('main/campaign_detail.html', campaign=campaign, inactive=True)
    return render_template('main/campaign_detail.html', campaign=campaign, inactive=False)

@main_bp.route('/api/notifications/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first_or_404()
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'status': 'success'})

@main_bp.route('/api/notifications/mark_all_read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    
    db.session.commit()
    return jsonify({'status': 'success'})

@main_bp.route('/api/notifications')
@login_required
def get_notifications():
    """Return recent notifications for the current user"""
    limit = request.args.get('limit', 10, type=int)
    items = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(limit).all()
    return jsonify({
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.notification_type,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat(),
            'url': n.url or ''
        } for n in items]
    })
