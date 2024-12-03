from datetime import datetime, UTC
import secrets
from authflask.extensions import db

class ApiKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    last_used = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, user_id, name):
        self.key = secrets.token_urlsafe(32)
        self.user_id = user_id
        self.name = name
