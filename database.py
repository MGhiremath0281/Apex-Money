# database.py
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy here, but tie it to the Flask app later in app.py
db = SQLAlchemy()

# You might add a function here later to create tables if you're not using migrations
# def init_db(app):
#     with app.app_context():
#         db.create_all()