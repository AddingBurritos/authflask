from authflask import create_app
from authflask.extensions import db, socketio

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)