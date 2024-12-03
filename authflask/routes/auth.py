from flask import render_template, request, redirect, url_for, flash, Blueprint, current_app
from flask_login import login_required, current_user, login_user, logout_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Message
from authflask.extensions import db, mail
from authflask.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form  # Check if remember-me checkbox is checked

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('auth.register'))

        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


def get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


def send_reset_email(user):
    # Generate timed token
    token = get_serializer().dumps(user.email, salt='password-reset-salt')

    # Create reset link
    reset_url = url_for('auth.reset_password', token=token, _external=True)

    # Send email
    msg = Message('Password Reset Request',
                      sender=current_app.config['MAIL_USERNAME'],
                      recipients=[user.email])

    msg.body = f'To reset your password, visit the following link:\n{reset_url}\n\nIf you did not make this request, please ignore this email.'
    mail.send(msg)


@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if user:
            send_reset_email(user)
            flash('An email has been sent with instructions to reset your password.')
            return redirect(url_for('auth.login'))
        else:
            flash('Email address not found')

    return render_template('forgot_password.html')


@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        # Verify token and get email (expires after 1 hour)
        email = get_serializer().loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        flash('The password reset link has expired.')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        user = User.query.filter_by(email=email).first()

        if user:
            new_password = request.form['password']
            user.set_password(new_password)
            db.session.commit()
            flash('Your password has been updated! Please login.')
            return redirect(url_for('auth.login'))

    return render_template('reset_password.html')