import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

from .extensions import db, bcrypt, login_manager
from .routes import bp as main_bp


def create_app(config=None):
    app = Flask(__name__, template_folder='templates', static_folder='../image')
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DATA_DIR'] = os.environ.get('DATA_DIR', '/data')
    if config:
        app.config.update(config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    return app
