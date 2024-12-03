from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_mail import Mail
from flask_login import LoginManager
from collections import defaultdict
from datetime import datetime

db = SQLAlchemy()
socketio = SocketIO()
mail = Mail()
login_manager = LoginManager()

# Active rooms data structure
active_rooms = defaultdict(lambda: {
    'users': {},
    'created_at': datetime.now()
})

# User data will look like:
# active_rooms[room_id]['users'][username] = {
#     'sid': session_id,
#     'last_heartbeat': timestamp,
#     'joined_at': timestamp
# }