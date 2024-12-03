from flask import Blueprint, render_template
from flask_login import login_required, current_user
from authflask.models import ChatRoom

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@main_bp.route('/rooms')
@login_required
def rooms():
    available_rooms = ChatRoom.query.all()
    return render_template('rooms.html', rooms=available_rooms)


@main_bp.route('/api_keys')
@login_required
def api_keys():
    return render_template('api_keys.html', api_keys=current_user.api_keys)
