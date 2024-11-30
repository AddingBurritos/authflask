from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from config import Config
import secrets
import datetime

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Token serializer for reset links
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])


# API Key model
class ApiKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_used = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, user_id, name):
        self.key = secrets.token_urlsafe(32)
        self.user_id = user_id
        self.name = name


# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    api_keys = db.relationship('ApiKey', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def auth_with_api_key():
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return None

    key = ApiKey.query.filter_by(key=api_key).first()
    if key:
        key.last_used = datetime.datetime.utcnow()
        db.session.commit()
        return key.user
    return None


# API Routes
@app.route('/api/test', methods=['GET'])
def api_test():
    user = auth_with_api_key()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401
    return jsonify({'message': f'Hello {user.username}! Your API key is valid.'})


# Web Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form  # Check if remember-me checkbox is checked

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))

        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/api-keys')
@login_required
def api_keys():
    return render_template('api_keys.html', api_keys=current_user.api_keys)


@app.route('/api-keys/generate', methods=['POST'])
@login_required
def generate_api_key():
    key_name = request.form.get('key_name', 'New API Key')
    api_key = ApiKey(user_id=current_user.id, name=key_name)
    db.session.add(api_key)
    db.session.commit()
    flash(f'New API key generated: {api_key.key}')
    return redirect(url_for('api_keys'))


@app.route('/api-keys/<int:key_id>/delete', methods=['POST'])
@login_required
def delete_api_key(key_id):
    api_key = ApiKey.query.get_or_404(key_id)
    if api_key.user_id != current_user.id:
        flash('Unauthorized')
        return redirect(url_for('api_keys'))

    db.session.delete(api_key)
    db.session.commit()
    flash('API key deleted')
    return redirect(url_for('api_keys'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


def send_reset_email(user):
    # Generate timed token
    token = serializer.dumps(user.email, salt='password-reset-salt')

    # Create reset link
    reset_url = url_for('reset_password', token=token, _external=True)

    # Send email
    msg = Message('Password Reset Request',
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[user.email])

    msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request, please ignore this email.
'''
    mail.send(msg)


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if user:
            send_reset_email(user)
            flash('An email has been sent with instructions to reset your password.')
            return redirect(url_for('login'))
        else:
            flash('Email address not found')

    return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        # Verify token and get email (expires after 1 hour)
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        flash('The password reset link has expired.')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        user = User.query.filter_by(email=email).first()

        if user:
            new_password = request.form['password']
            user.set_password(new_password)
            db.session.commit()
            flash('Your password has been updated! Please login.')
            return redirect(url_for('login'))

    return render_template('reset_password.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
