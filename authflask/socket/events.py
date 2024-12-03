from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from authflask.extensions import socketio, db, active_rooms
from authflask.models.chat_message import ChatMessage
from datetime import datetime, timedelta


# Background task to check for inactive users
def check_inactive_users(room_id):
    current_time = datetime.now()
    inactive_threshold = timedelta(minutes=1)

    for username in list(active_rooms[room_id]['users']):
        last_heartbeat = active_rooms[room_id]['users'][username]['last_heartbeat']
        if current_time - last_heartbeat > inactive_threshold:
            # User has been inactive, remove them from the room
            active_rooms[room_id]['users'].pop(username)

            emit('user_left', {
                'username': username,
                'room_id': room_id
            }, to=f"room_{room_id}")

            emit('room_users_update', {
                'users': list(active_rooms[room_id]['users'])
            }, to=f"room_{room_id}")

            # Clean up empty rooms
            if not active_rooms[room_id]['users']:
                active_rooms.pop(room_id)
            print(f'Removing {username} due to heartbeat')
            print(list(active_rooms[room_id]['users']))


@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        emit('connection_response', {'status': 'connected'})


@socketio.on('join_room')
def handle_join_room(data):
    if current_user.is_authenticated:
        room_id = data['room_id']

        # Remove user from any previous room
        for r_id in active_rooms:
            if current_user.username in active_rooms[r_id]['users']:
                leave_room(f"room_{r_id}")
                active_rooms[r_id]['users'].pop(current_user.username)
                # Notify previous room that user left
                emit('user_left', {
                    'username': current_user.username,
                    'room_id': r_id
                }, to=f"room_{r_id}")
                # Update previous room's user list
                emit('room_users_update', {
                    'users': list(active_rooms[r_id]['users'])
                }, to=f"room_{r_id}")
                print('join_room cleanup')
                print(list(active_rooms[room_id]['users']))

        # Join new room
        join_room(f"room_{room_id}")
        active_rooms[room_id]['users'][current_user.username] = {
            'sid': request.sid,
            'last_heartbeat': datetime.now(),
            'joined_at': datetime.now()
        }

        # Notify room of new user
        emit('user_joined', {
            'username': current_user.username,
            'room_id': room_id
        }, to=f"room_{room_id}")

        # Send updated user list for this room
        emit('room_users_update', {
            'users': list(active_rooms[room_id]['users'])
        }, to=f"room_{room_id}")
        print('join_room')
        print(list(active_rooms[room_id]['users']))


@socketio.on('leave_room')
def handle_leave_room(data):
    if current_user.is_authenticated:
        room_id = data['room_id']
        if room_id in active_rooms and current_user.username in active_rooms[room_id]['users']:
            leave_room(f"room_{room_id}")
            active_rooms[room_id]['users'].pop(current_user.username)

            # Notify room that user left
            emit('user_left', {
                'username': current_user.username,
                'room_id': room_id
            }, to=f"room_{room_id}")

            # Update room's user list
            emit('room_users_update', {
                'users': list(active_rooms[room_id]['users'])
            }, to=f"room_{room_id}")

            # Clean up empty rooms
            if not active_rooms[room_id]['users']:
                active_rooms.pop(room_id)
            print('leave_room')
            print(list(active_rooms[room_id]['users']))


@socketio.on('heartbeat')
def handle_heartbeat(data):
    if current_user.is_authenticated:
        for room_id in active_rooms:
            if current_user.username in active_rooms[room_id]['users']:
                active_rooms[room_id]['users'][current_user.username]['last_heartbeat'] = datetime.now()
                check_inactive_users(data['room_id'])


@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        for room_id in list(active_rooms):  # Use list to avoid runtime modification issues
            room_data = active_rooms[room_id]
            if current_user.username in room_data['users']:
                room_data['users'].pop(current_user.username)

                # Notify room that user left
                emit('user_left', {
                    'username': current_user.username,
                    'room_id': room_id
                }, to=f"room_{room_id}")

                # Update room's user list
                emit('room_users_update', {
                    'users': list(active_rooms[room_id]['users'])
                }, to=f"room_{room_id}")

                # Clean up empty rooms
                if not active_rooms[room_id]['users']:
                    active_rooms.pop(room_id)
                print('disconnect')
                print(list(active_rooms[room_id]['users']))


@socketio.on('send_message')
def handle_message(data):
    if current_user.is_authenticated:
        # Find which room the user is in
        room_id = None
        for r_id in active_rooms:
            if current_user.username in active_rooms[r_id]['users']:
                room_id = r_id
                break

        if room_id:
            message = ChatMessage(
                content=data['message'],
                user_id=current_user.id,
                room_id=room_id
            )
            db.session.add(message)
            db.session.commit()

            emit('new_message', {
                'username': current_user.username,
                'message': message.content,
                'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }, to=f"room_{room_id}")