from flask import Blueprint, request, redirect, url_for, flash
from flask_login import login_required, current_user
from authflask.extensions import db
from authflask.models import ApiKey

api_keys_bp = Blueprint('api_keys', __name__)

@api_keys_bp.route('/generate', methods=['POST'])
@login_required
def generate_api_key():
    key_name = request.form.get('key_name', 'New API Key')
    api_key = ApiKey(user_id=current_user.id, name=key_name)
    db.session.add(api_key)
    db.session.commit()
    flash(f'New API key generated: {api_key.key}')
    return redirect(url_for('main.api_keys'))


@api_keys_bp.route('/<int:key_id>/delete', methods=['POST'])
@login_required
def delete_api_key(key_id):
    api_key = ApiKey.query.get_or_404(key_id)
    if api_key.user_id != current_user.id:
        flash('Unauthorized')
        return redirect(url_for('main.api_keys'))

    db.session.delete(api_key)
    db.session.commit()
    flash('API key deleted')
    return redirect(url_for('main.api_keys'))