from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SelectField, FloatField, DateTimeField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, NumberRange, ValidationError
from wtforms.widgets import TextArea

def validate_kpk_coordinates(form, field):
    """Validate that coordinates are within Khyber Pakhtunkhwa region"""
    if field.data is None:
        return  # Optional field, no validation needed if empty
    
    lat = form.latitude.data
    lng = form.longitude.data
    
    # Both lat and lng must be provided together
    if (lat is None) != (lng is None):
        raise ValidationError('Both latitude and longitude must be provided together.')
    
    if lat is not None and lng is not None:
        # KPK approximate boundaries
        # North: 36.75, South: 31.17, East: 74.35, West: 70.10
        if not (31.17 <= lat <= 36.75):
            raise ValidationError('Latitude must be within Khyber Pakhtunkhwa region (31.17° to 36.75°).')
        
        if not (70.10 <= lng <= 74.35):
            raise ValidationError('Longitude must be within Khyber Pakhtunkhwa region (70.10° to 74.35°).')

def validate_attachment_reference(form, field):
    """Validate that if attachment is provided, reference must also be provided"""
    if form.attachment.data and not field.data:
        raise ValidationError('Reference/Source is required when uploading a supporting document.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=50)])
    location = StringField('Location', validators=[Optional(), Length(max=100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match')
    ])

class EditProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=50)])
    location = StringField('Location', validators=[Optional(), Length(max=100)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=500)])
    avatar = FileField('Profile Picture', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])

class ResourceForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=200)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10, max=2000)])
    category = SelectField('Category', validators=[DataRequired()], choices=[
        ('minerals', 'Minerals'),
        ('agriculture', 'Agriculture'),
        ('wildlife', 'Wildlife'),
        ('cultural', 'Cultural Heritage')
    ])
    subcategory = StringField('Subcategory', validators=[Optional(), Length(max=50)])
    location = StringField('Location', validators=[Optional(), Length(max=200)])
    latitude = FloatField('Latitude', validators=[Optional(), NumberRange(min=-90, max=90), validate_kpk_coordinates])
    longitude = FloatField('Longitude', validators=[Optional(), NumberRange(min=-180, max=180), validate_kpk_coordinates])
    economic_value = StringField('Economic Value', validators=[Optional(), Length(max=100)])
    sustainability_info = TextAreaField('Sustainability Information', validators=[Optional(), Length(max=1000)])
    image = FileField('Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    # File attachment fields
    attachment = FileField('Supporting Document', validators=[
        Optional(),
        FileAllowed(['pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx', 'ppt', 'pptx'], 
                   'Only documents allowed! (PDF, DOC, DOCX, TXT, XLS, XLSX, PPT, PPTX)')
    ])
    attachment_reference = TextAreaField('Reference/Source', validators=[
        Optional(),
        Length(max=500),
        validate_attachment_reference
    ], description='Please provide a valid reference or source for your supporting document (required if file is uploaded)')

class CommunityPostForm(FlaskForm):
    title = StringField('Title', validators=[Optional(), Length(min=0, max=200)])
    content = TextAreaField('Content', validators=[DataRequired(), Length(min=10, max=5000)])
    category = SelectField('Category', validators=[DataRequired()], choices=[
        ('discussion', 'Discussion'),
        ('question', 'Question'),
        ('announcement', 'Announcement'),
        ('news', 'News')
    ])
    tags = StringField('Tags (comma-separated)', validators=[Optional(), Length(max=200)])
    image = FileField('Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired(), Length(min=1, max=1000)])
    parent_id = HiddenField('Parent ID', validators=[Optional()])

class FileSubmissionForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=200)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10, max=1000)])
    category = SelectField('Category', validators=[DataRequired()], choices=[
        ('research', 'Research Paper'),
        ('report', 'Report'),
        ('documentation', 'Documentation'),
        ('image', 'Image/Photo'),
        ('other', 'Other')
    ])
    reference = TextAreaField('Reference/Source', validators=[
        DataRequired(), 
        Length(min=10, max=500)
    ], description='Please provide a valid reference or source for your submission')
    file = FileField('File', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'xls', 'xlsx'], 
                   'Only documents and images allowed!')
    ])

class CampaignForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=200)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10, max=500)])
    content = TextAreaField('Content', validators=[DataRequired(), Length(min=50, max=5000)])
    campaign_type = SelectField('Campaign Type', validators=[DataRequired()], choices=[
        ('education', 'Education'),
        ('health', 'Health'),
        ('sustainability', 'Sustainability'),
        ('awareness', 'General Awareness')
    ])
    target_audience = StringField('Target Audience', validators=[Optional(), Length(max=100)])
    start_date = DateTimeField('Start Date', validators=[Optional()], format='%Y-%m-%d')
    end_date = DateTimeField('End Date', validators=[Optional()], format='%Y-%m-%d')
    image = FileField('Campaign Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired(), Length(min=1, max=100)])
    category = SelectField('Category', choices=[
        ('all', 'All Categories'),
        ('resources', 'Resources'),
        ('posts', 'Community Posts'),
        ('files', 'Files')
    ], default='all')

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired(), Length(min=5, max=200)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=10, max=1000)])

class VideoCallForm(FlaskForm):
    title = StringField('Call Title', validators=[DataRequired(), Length(min=5, max=200)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    max_participants = SelectField('Max Participants', choices=[
        ('5', '5 participants'),
        ('10', '10 participants'),
        ('20', '20 participants'),
        ('50', '50 participants')
    ], default='10')
