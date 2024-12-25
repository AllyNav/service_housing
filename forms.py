from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from models import Customer, ServiceProfessional

class ServiceProfessionalLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(message='Invalid email.')])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')
    
class CustomerLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(message='Invalid email.')])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')
        
class ServiceProfessionalRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(message='Username is required.')])
    address = StringField('Address', validators=[DataRequired(message='Address is required.')])
    phone = StringField('Phone', validators=[DataRequired(message='Phone is required.')])
    service_type = SelectField(
    'Service Type',
    choices=[
        ('Cleaning', 'House Cleaning'),
        ('Electrical', 'Gadgets Service'),
        ('Salon', 'HairCut'),
        ('Electrican', 'Electrician'),
        ('Clothing', 'Tailor'),
        ('Others', 'Other Services')
    ],
    default='option1',  # Pre-select Option 1
    validators=[DataRequired(message='Service Type is required.')]
)
    email = StringField('Email', validators=[DataRequired(), Email(message='Invalid email.')])
    password = PasswordField('Password', validators=[DataRequired(message='Password is required.')])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = ServiceProfessional.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists.')
        
    def validate_email(self, email):
        user = ServiceProfessional.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')
        
class CustomerRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(message='Username is required.')])
    address = StringField('Address', validators=[DataRequired(message='Address is required.')])
    phone = StringField('Phone', validators=[DataRequired(message='Phone is required.')])
    pincode = StringField('Pincode', validators=[DataRequired(message='Pincode is required.')])
    email = StringField('Email', validators=[DataRequired(), Email(message='Invalid email.')])
    password = PasswordField('Password', validators=[DataRequired(message='Password is required.')])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = Customer.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists.')
        
    def validate_email(self, email):
        user = Customer.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')

class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(message='Username is required.')])
    password = PasswordField('Password', validators=[DataRequired(message='Password is required.')])
    submit = SubmitField('Log In')
