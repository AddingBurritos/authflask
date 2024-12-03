from flask import Blueprint, jsonify, request
from authflask.models.api_key import ApiKey
from authflask.extensions import db
from datetime import datetime, UTC

api_bp = Blueprint('api', __name__)

def auth_with_api_key():
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return None

    key = ApiKey.query.filter_by(key=api_key).first()
    if key:
        key.last_used = datetime.now(UTC)
        db.session.commit()
        return key.user
    return None


@api_bp.route('/test', methods=['GET'])
def api_test():
    user = auth_with_api_key()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401
    return jsonify({'message': f'Hello {user.username}! Your API key is valid.'})
