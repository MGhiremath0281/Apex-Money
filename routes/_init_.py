# route/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'  # or use PostgreSQL on Render

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Import and register your blueprints here
    # from .views import views
    # app.register_blueprint(views)

    return app
