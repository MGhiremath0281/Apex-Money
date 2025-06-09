# routes/categories.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from database import db
from models import Category # Import the Category model

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/add_category', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        name = request.form.get('name').strip()
        type = request.form.get('type') # 'income' or 'expense'

        if not name or not type:
            flash('Category name and type are required!', 'danger')
            return redirect(url_for('categories.add_category'))
        
        if type not in ['income', 'expense']:
            flash('Invalid category type.', 'danger')
            return redirect(url_for('categories.add_category'))

        # Check if category name already exists for the user
        existing_category = Category.query.filter_by(user_id=current_user.id, name=name).first()
        if existing_category:
            flash(f'Category "{name}" already exists for you.', 'warning')
            return redirect(url_for('categories.add_category'))

        new_category = Category(user_id=current_user.id, name=name, type=type)
        db.session.add(new_category)
        try:
            db.session.commit()
            flash(f'Category "{name}" ({type}) added successfully!', 'success')
            # After adding, you might want to redirect to a list of categories or dashboard
            return redirect(url_for('categories.view_categories')) # We'll create this route next
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            print(f"Database error during category add: {e}") # For debugging
            return redirect(url_for('categories.add_category'))

    return render_template('categories/add_category.html', user=current_user)

@categories_bp.route('/view_categories')
@login_required
def view_categories():
    user_categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.type, Category.name).all()
    return render_template('categories/view_categories.html', user=current_user, categories=user_categories)

# You can add edit/delete routes here later