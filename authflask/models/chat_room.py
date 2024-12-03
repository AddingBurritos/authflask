from datetime import datetime, UTC
from authflask.extensions import db

class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    messages = db.relationship('ChatMessage', backref='room', lazy=True, cascade='all, delete-orphan')
