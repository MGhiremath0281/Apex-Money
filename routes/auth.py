# routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from models import User
from database import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # If a user is already logged in, redirect them away from the registration page
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('dashboard_page')) # Redirect to the new dashboard page

    if request.method == 'POST':
        username = request.form.get('username').strip() # .strip() to remove leading/trailing whitespace
        email = request.form.get('email').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Basic validation
        if not username or not password or not confirm_password:
            flash('All fields are required (Email is optional but recommended).', 'danger')
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return redirect(url_for('auth.register'))

        # Check if username or email already exists
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('auth.register'))

        if email: # Only check if email is provided
            email_exists = User.query.filter_by(email=email).first()
            if email_exists:
                flash('Email already registered. Please use a different one or login.', 'danger')
                return redirect(url_for('auth.register'))

        # Hash the password before storing
        hashed_password = generate_password_hash(password, method='scrypt') # 'scrypt' is a strong hash method

        new_user = User(username=username, email=email if email else None, password_hash=hashed_password)
        db.session.add(new_user)
        try:
            db.session.commit()
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_page')) # UPDATED: Redirect to the new dashboard route

    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        # Check if user exists and password is correct
        if user and user.check_password(password):
            login_user(user) # Log the user in
            flash('Logged in successfully!', 'success')

            # Redirect to 'next' page if it exists (e.g., if user tried to access a protected page)
            # Otherwise, redirect to the dashboard.
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard_page')) # UPDATED: Redirect to new dashboard route
        else:
            flash('Login Unsuccessful. Please check username and password.', 'danger') # More generic error message for security

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required # Ensure only logged-in users can log out
def logout():
    logout_user() # Log the user out using Flask-Login
    flash('You have been logged out.', 'info')
    return redirect(url_for('home')) # Redirect to the public home page after logout