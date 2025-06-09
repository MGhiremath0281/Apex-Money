# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Use the SECRET_KEY from .env (or a fallback)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_fallback_secret_key_if_env_not_loaded'

    # Get the DATABASE_URL from .env and assign it to SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') # <--- CHANGE THIS LINE

    # --- ADD THIS LINE FOR DEBUGGING ---
    print(f"DEBUG: SQLALCHEMY_DATABASE_URI loaded: {SQLALCHEMY_DATABASE_URI}")
    # -----------------------------------

    SQLALCHEMY_TRACK_MODIFICATIONS = False