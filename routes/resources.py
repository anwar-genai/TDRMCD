from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_from_directory
from flask_login import login_required, current_user
from models import db, Resource
from forms import ResourceForm
from werkzeug.utils import secure_filename
import os
import uuid

resources_bp = Blueprint('resources', __name__)

@resources_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', 'all')
    sort_by = request.args.get('sort', 'newest')
    
    query = Resource.query.filter_by(status='active')
    
    if category != 'all':
        query = query.filter_by(category=category)
    
    if sort_by == 'newest':
        query = query.order_by(Resource.created_at.desc())
    elif sort_by == 'oldest':
        query = query.order_by(Resource.created_at.asc())
    elif sort_by == 'title':
        query = query.order_by(Resource.title.asc())
    
    resources = query.paginate(
        page=page, per_page=12, error_out=False
    )
    
    # Get categories for filter
    categories = db.session.query(Resource.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('resources/index.html',
                         resources=resources,
                         categories=categories,
                         current_category=category,
                         current_sort=sort_by)

@resources_bp.route('/<int:id>')
def detail(id):
    resource = Resource.query.get_or_404(id)
    
    # Get related resources (same category, excluding current)
    related_resources = Resource.query.filter(
        Resource.category == resource.category,
        Resource.id != resource.id,
        Resource.status == 'active'
    ).limit(4).all()
    
    return render_template('resources/detail.html',
                         resource=resource,
                         related_resources=related_resources)

@resources_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = ResourceForm()
    if form.validate_on_submit():
        resource = Resource(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            subcategory=form.subcategory.data,
            location=form.location.data,
            latitude=form.latitude.data if form.latitude.data else None,
            longitude=form.longitude.data if form.longitude.data else None,
            economic_value=form.economic_value.data,
            sustainability_info=form.sustainability_info.data,
            author_id=current_user.id
        )
        
        # Handle image upload
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            if filename:
                # Generate unique filename
                import uuid
                file_ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4()}.{file_ext}"
                
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'resources', unique_filename)
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                form.image.data.save(image_path)
                resource.image_url = f"resources/{unique_filename}"
        
        # Handle file attachment upload
        if form.attachment.data:
            filename = secure_filename(form.attachment.data.filename)
            if filename:
                import uuid
                file_ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4()}.{file_ext}"
                
                attachment_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'resources', 'attachments', unique_filename)
                os.makedirs(os.path.dirname(attachment_path), exist_ok=True)
                form.attachment.data.save(attachment_path)
                
                # Store attachment information
                resource.attachment_filename = f"attachments/{unique_filename}"
                resource.attachment_original_name = filename
                resource.attachment_file_type = file_ext
                resource.attachment_file_size = os.path.getsize(attachment_path)
                resource.attachment_reference = form.attachment_reference.data
        
        db.session.add(resource)
        db.session.commit()
        
        flash('Resource added successfully!', 'success')
        return redirect(url_for('resources.detail', id=resource.id))
    
    return render_template('resources/add.html', form=form)

@resources_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    resource = Resource.query.get_or_404(id)
    
    # Check if user owns this resource or is admin
    if resource.author_id != current_user.id and not current_user.is_admin():
        flash('You do not have permission to edit this resource.', 'error')
        return redirect(url_for('resources.detail', id=resource.id))
    
    form = ResourceForm(obj=resource)
    if form.validate_on_submit():
        resource.title = form.title.data
        resource.description = form.description.data
        resource.category = form.category.data
        resource.subcategory = form.subcategory.data
        resource.location = form.location.data
        resource.latitude = form.latitude.data if form.latitude.data else None
        resource.longitude = form.longitude.data if form.longitude.data else None
        resource.economic_value = form.economic_value.data
        resource.sustainability_info = form.sustainability_info.data
        
        # Handle image upload
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            if filename:
                # Generate unique filename
                import uuid
                file_ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4()}.{file_ext}"
                
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'resources', unique_filename)
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                form.image.data.save(image_path)
                resource.image_url = f"resources/{unique_filename}"
        
        # Handle file attachment upload
        if form.attachment.data:
            filename = secure_filename(form.attachment.data.filename)
            if filename:
                import uuid
                file_ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4()}.{file_ext}"
                
                attachment_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'resources', 'attachments', unique_filename)
                os.makedirs(os.path.dirname(attachment_path), exist_ok=True)
                form.attachment.data.save(attachment_path)
                
                # Store attachment information
                resource.attachment_filename = f"attachments/{unique_filename}"
                resource.attachment_original_name = filename
                resource.attachment_file_type = file_ext
                resource.attachment_file_size = os.path.getsize(attachment_path)
                resource.attachment_reference = form.attachment_reference.data
        
        db.session.commit()
        flash('Resource updated successfully!', 'success')
        return redirect(url_for('resources.detail', id=resource.id))
    
    return render_template('resources/edit.html', form=form, resource=resource)

@resources_bp.route('/<int:id>/download_attachment')
@login_required
def download_attachment(id):
    resource = Resource.query.get_or_404(id)
    
    if not resource.attachment_filename:
        flash('No attachment found for this resource.', 'error')
        return redirect(url_for('resources.detail', id=id))
    
    # Get the file path
    uploads_root = os.path.join(current_app.config['UPLOAD_FOLDER'], 'resources')
    file_path = os.path.join(uploads_root, resource.attachment_filename)
    
    if not os.path.exists(file_path):
        flash('Attachment file not found.', 'error')
        return redirect(url_for('resources.detail', id=id))
    
    try:
        return send_from_directory(
            os.path.dirname(file_path),
            os.path.basename(file_path),
            as_attachment=True,
            download_name=resource.attachment_original_name
        )
    except Exception as e:
        flash('Error downloading file.', 'error')
        return redirect(url_for('resources.detail', id=id))

@resources_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    resource = Resource.query.get_or_404(id)
    
    # Check if user owns this resource or is admin
    if resource.author_id != current_user.id and not current_user.is_admin():
        flash('You do not have permission to delete this resource.', 'error')
        return redirect(url_for('resources.detail', id=resource.id))
    
    db.session.delete(resource)
    db.session.commit()
    
    flash('Resource deleted successfully!', 'success')
    return redirect(url_for('resources.index'))

@resources_bp.route('/categories/<category>')
def by_category(category):
    page = request.args.get('page', 1, type=int)
    
    resources = Resource.query.filter_by(
        category=category,
        status='active'
    ).order_by(Resource.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    return render_template('resources/category.html',
                         resources=resources,
                         category=category)

@resources_bp.route('/api/resources/<int:id>/coordinates')
def get_coordinates(id):
    resource = Resource.query.get_or_404(id)
    if resource.latitude and resource.longitude:
        return jsonify({
            'latitude': resource.latitude,
            'longitude': resource.longitude,
            'title': resource.title,
            'location': resource.location
        })
    return jsonify({'error': 'Coordinates not available'}), 404
