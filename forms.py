from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SelectField, FloatField, DateTimeField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, NumberRange
from wtforms.widgets import TextArea

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
    latitude = FloatField('Latitude', validators=[Optional(), NumberRange(min=-90, max=90)])
    longitude = FloatField('Longitude', validators=[Optional(), NumberRange(min=-180, max=180)])
    economic_value = StringField('Economic Value', validators=[Optional(), Length(max=100)])
    sustainability_info = TextAreaField('Sustainability Information', validators=[Optional(), Length(max=1000)])
    image = FileField('Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])

class CommunityPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=200)])
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
