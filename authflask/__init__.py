from flask import Flask
from config import Config
from authflask.extensions import db, socketio, mail, login_manager
from authflask.models import User

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    socketio.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from .routes.api import api_bp
    from .routes.api_keys import api_keys_bp
    from .routes.auth import auth_bp
    from .routes.main import main_bp
    from .routes.rooms import rooms_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(api_keys_bp, url_prefix='/api_keys')
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(rooms_bp)

    from authflask.socket import events

    return app