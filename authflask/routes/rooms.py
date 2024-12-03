from flask import render_template, request, redirect, url_for, flash, Blueprint
from flask_login import login_required, current_user
from authflask.extensions import db
from authflask.models import ChatRoom, ChatMessage

rooms_bp = Blueprint('rooms', __name__)

@rooms_bp.route('/room/<int:room_id>')
@login_required
def chat_room(room_id):
    room = ChatRoom.query.get_or_404(room_id)
    messages = ChatMessage.query.filter_by(room_id=room_id).order_by(ChatMessage.timestamp.desc()).limit(50).all()
    return render_template('chat.html', room=room, messages=messages)


@rooms_bp.route('/room/create', methods=['POST'])
@login_required
def create_room():
    name = request.form.get('room_name')
    if not name:
        flash('Room name is required')
        return redirect(url_for('main.rooms'))

    room = ChatRoom(name=name, creator_id=current_user.id)
    db.session.add(room)
    db.session.commit()

    flash(f'Room "{name}" created successfully')
    return redirect(url_for('rooms.chat_room', room_id=room.id))


@rooms_bp.route('/room/<int:room_id>/delete', methods=['POST'])
@login_required
def delete_room(room_id):
    room = ChatRoom.query.get_or_404(room_id)
    if room.creator_id != current_user.id:
        flash('You can only delete rooms you created')
        return redirect(url_for('main.rooms'))

    db.session.delete(room)
    db.session.commit()
    flash('Room deleted successfully')
    return redirect(url_for('main.rooms'))