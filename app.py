from flask import Flask, render_template, request, redirect, url_for, jsonify, app, flash
from flask_mysqldb import MySQL
# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy import create_engine
from flask_login import LoginManager, current_user, login_user, login_required, logout_user, UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError, EqualTo
from datetime import timedelta
import pymysql
from flask_bcrypt import Bcrypt
from flask_bcrypt import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.secret_key = 'demo_key'

app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Horatious0!'
app.config['MYSQL_DB'] = 'ecommerce_demo'
app.config['MYSQL_HOST'] = 'localhost'

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'signin'
login_manager.login_message_category = 'info'

mysql = MySQL(app)
connection = pymysql.connect(
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB'],
        host=app.config['MYSQL_HOST']
    )

bcrypt = Bcrypt(app)

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=50)])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), EqualTo('Password', message='Passwords must match')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        print(f"Validating: {username}")
        with connection.cursor() as cursor:
            cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
            existing_user = cursor.fetchone()
            if existing_user:
                flash('This username is already taken. Please choose a different one.')
                return False
        return True

    def validate_password(self, password):
        print(f"Validating: {password}")
        is_valid = True

        # Check if the password contains at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            flash('Password must contain at least one uppercase letter.')
            is_valid = False

        # Check if the password contains at least one lowercase letter
        if not re.search(r'[a-z]', password):
            flash('Password must contain at least one lowercase letter.')
            is_valid = False

        # Check if the password contains at least one special character
        if not re.search(r'[~`!@#$%^&*()-_+={}[\]|\\;:"<>,./?]', password):
            flash('Password must contain at least one special character from the following: ~`!@#$%^&*()-_+={}[]|\;:"<>,./?')
            is_valid = False

        # Check if the password contains at least one digit
        if not re.search(r'\d', password):
            flash('Password must contain at least one digit.')
            is_valid = False

        return is_valid

class User(UserMixin):
    def __init__(self, id, role):
        self.id = id
        self.role = role

    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True

    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)
    
@login_manager.unauthorized_handler
def unauthorized():
    flash('User not authenticated', 'error')
    return redirect(url_for('signin'))

def get_user_info(user_id):
    with connection.cursor() as cursor:
        cursor = connection.cursor()
        cursor.execute("SELECT id, role FROM users WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
        
    if user_data and user_data[0] == user_id:
        return user_data[0], user_data[1]
    else:
        return None, None

@login_manager.user_loader
def load_user(user_id):
    id, role = get_user_info(user_id)
    if user_id:
        return User(id, role)
    return None

def validate_credentials(username, password, cursor):
    print(f"Validating: {username}, {password}")
    cursor.execute("SELECT id, username, password, role FROM users WHERE username = %s", (username,))
    user_data = cursor.fetchone()
    
    if user_data and check_password_hash(user_data[2], password):
        user_id, role = user_data[0], user_data[3]
        print(f"Found {username} with role: {role}")
        return user_id, role
    return None, None

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"Trying to register: {username}, {password}")
        if form.validate_username(username) and form.validate_password(password):
            with connection.cursor() as cursor:
                hashed_password = generate_password_hash(password).decode('utf-8')
                print(hashed_password)
                cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, hashed_password))
                connection.commit()
                flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('signin'))
    return render_template('register.html', form=form)

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            print(request.form)
            with connection.cursor() as cursor:
                username = request.form.get('username')
                password = request.form.get('password')
                user_id, role = validate_credentials(username, password, cursor)
                
                if user_id and role:
                    user = User(user_id, role)
                    login_user(user=user, remember=True, duration=timedelta(minutes=5.0))

                    if role == 'admin':
                        return redirect(url_for('content_dashboard'))
                    else:
                        return redirect(url_for('user_dashboard'))
                flash('Invalid username or password. Please try again.', 'error')
        return render_template('signin.html', form=form)
    return render_template('signin.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# @app.route('/admin_dashboard')
# @login_required
# def admin_dashboard():
#     print(f"(In Admin Dashboard) current_user.role: {current_user.role}")
#     user_role = current_user.role
#     if user_role == 'admin':
#         print("Access Granted")
#         return content_dashboard()
#     else:
#         return redirect(url_for('signin'))

@app.route('/user_dashboard')
@login_required
def user_dashboard():
    print("In user dashboard.")
    return 'Welcome user'

@app.route('/get_content_dropdown')
@login_required
def get_content_dropdown():
    with connection.cursor() as cursor:
        cursor.execute("SELECT ID, metadata FROM content")
        data = cursor.fetchall()
    return jsonify({'content': data})

@app.route('/get_content_by_id/<int:selectedID>')
@login_required
def get_content_by_id(selectedID):
    with connection.cursor() as cursor:
        cursor.execute("SELECT text FROM content WHERE ID = %s", (selectedID,))
        data = cursor.fetchone()
    return jsonify({'content': data})

@app.route('/edit', methods=['GET', 'POST'])
@login_required
def content_dashboard():
    if request.method == 'POST':
        new_text = request.json['content']
        content_id = request.json['id']
        print(request.json)
        print(new_text)
        try:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE content SET text = %s WHERE ID = %s", (new_text, content_id))
                connection.commit()
                return jsonify({'Success': 'Success'})
        except pymysql.Error as err:
            print("Error:", err)
            return render_template('edit_content.html', error="Error occurred while updating database.")
    else:
        return render_template('edit_content.html')

@app.route('/fetch_index_content')
def fetch_index_content():
    with connection.cursor() as cursor:
        cursor.execute("SELECT text FROM content")
        data = cursor.fetchall()
        content = ""
        for row in data:
            content += f"{row[0]}<br>"
    return jsonify({'content': content})

@app.route('/')
def index():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT text FROM content")
            data = cursor.fetchall()

            content = ""
            for row in data:
                content += f"{row[0]}"

            return render_template('index.html', html_content=content)
    except Exception as e:
        print("Error executing SQL query:", e)
        return

if __name__ == '__main__':
    app.run(debug=True)