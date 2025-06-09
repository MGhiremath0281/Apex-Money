# routes/budgets.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from database import db
from models import User, Budget, Category 
from datetime import datetime
from decimal import Decimal 

budgets_bp = Blueprint('budgets', __name__)

@budgets_bp.route('/set_budget', methods=['GET', 'POST'])
@login_required
def set_budget():
    user_categories = Category.query.filter_by(user_id=current_user.id, type='expense').order_by(Category.name).all()

    if request.method == 'POST':
        category_id = request.form.get('category_id')
        amount_str = request.form.get('amount').strip()

        if not category_id or not amount_str:
            flash('Category and Amount are required.', 'danger')
            return redirect(url_for('budgets.set_budget'))

        try:
            amount = Decimal(amount_str) 
            if amount <= 0:
                flash('Budget amount must be positive.', 'danger')
                return redirect(url_for('budgets.set_budget'))
        except ValueError:
            flash('Invalid amount. Please enter a number.', 'danger')
            return redirect(url_for('budgets.set_budget'))

        selected_category = Category.query.get(category_id)
        if not selected_category or selected_category.user_id != current_user.id:
            flash('Invalid category selected.', 'danger')
            return redirect(url_for('budgets.set_budget'))

        # Check if a budget already exists for this category for the current user
        # You might want to allow multiple budgets per category, or monthly budgets.
        # For simplicity now, let's assume one active budget per category.
        existing_budget = Budget.query.filter_by(
            user_id=current_user.id,
            category=selected_category.name # Match by name as we store name
        ).first()

        if existing_budget:
            flash(f'A budget for "{selected_category.name}" already exists. Please edit it instead.', 'warning')
            return redirect(url_for('budgets.set_budget'))

        new_budget = Budget(
            user_id=current_user.id,
            category=selected_category.name,
            amount=amount,
            start_date=datetime.utcnow()
        )
        
        db.session.add(new_budget)
        try:
            db.session.commit()
            flash(f'Budget of ₹{amount:.2f} set for "{selected_category.name}" successfully!', 'success')
            return redirect(url_for('budgets.view_budgets'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while setting the budget: {str(e)}', 'danger')
            print(f"Database error during budget save: {e}")
            return redirect(url_for('budgets.set_budget'))

    return render_template('budgets/set_budget.html', user=current_user, categories=user_categories)

@budgets_bp.route('/view_budgets')
@login_required
def view_budgets():
    user_budgets = Budget.query.filter_by(user_id=current_user.id).order_by(Budget.category).all()
    
    budgets_with_summary = []
    for budget in user_budgets:
        simulated_spent = Decimal('0.00') # Placeholder. Integrate with Transaction model later.
        remaining = budget.amount - simulated_spent
        
        budgets_with_summary.append({
            'id': budget.id,
            'category': budget.category,
            'amount': budget.amount,
            'spent': simulated_spent,
            'remaining': remaining,
            'start_date': budget.start_date
        })

    return render_template('budgets/view_budgets.html', user=current_user, budgets=budgets_with_summary)


@budgets_bp.route('/edit_budget/<int:budget_id>', methods=['GET', 'POST'])
@login_required
def edit_budget(budget_id):
    budget = Budget.query.get_or_404(budget_id)

    # Ensure the budget belongs to the current user
    if budget.user_id != current_user.id:
        flash('You are not authorized to edit this budget.', 'danger')
        abort(403) # Forbidden

    # Fetch categories for the dropdown (only 'expense' type for budgeting)
    user_categories = Category.query.filter_by(user_id=current_user.id, type='expense').order_by(Category.name).all()

    if request.method == 'POST':
        category_id = request.form.get('category_id')
        amount_str = request.form.get('amount').strip()

        if not category_id or not amount_str:
            flash('Category and Amount are required.', 'danger')
            return redirect(url_for('budgets.edit_budget', budget_id=budget.id))

        try:
            amount = Decimal(amount_str)
            if amount <= 0:
                flash('Budget amount must be positive.', 'danger')
                return redirect(url_for('budgets.edit_budget', budget_id=budget.id))
        except ValueError:
            flash('Invalid amount. Please enter a number.', 'danger')
            return redirect(url_for('budgets.edit_budget', budget_id=budget.id))

        selected_category = Category.query.get(category_id)
        if not selected_category or selected_category.user_id != current_user.id:
            flash('Invalid category selected.', 'danger')
            return redirect(url_for('budgets.edit_budget', budget_id=budget.id))

        # Check for unique category name if the category itself is changing
        # This prevents setting a budget for a category name that already has another budget
        if selected_category.name != budget.category:
            existing_budget_for_new_category = Budget.query.filter_by(
                user_id=current_user.id,
                category=selected_category.name
            ).filter(Budget.id != budget.id).first()
            
            if existing_budget_for_new_category:
                flash(f'A budget already exists for "{selected_category.name}".', 'warning')
                return redirect(url_for('budgets.edit_budget', budget_id=budget.id))

        budget.category = selected_category.name # Update category name
        budget.amount = amount
        budget.updated_at = datetime.utcnow() # Update the timestamp

        try:
            db.session.commit()
            flash('Budget updated successfully!', 'success')
            return redirect(url_for('budgets.view_budgets'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while updating the budget: {str(e)}', 'danger')
            print(f"Database error during budget update: {e}")
            return redirect(url_for('budgets.edit_budget', budget_id=budget.id))

    # For GET request, pre-fill the form with existing budget data
    # Find the category_id matching the budget.category name for pre-selection in dropdown
    current_category_obj = Category.query.filter_by(user_id=current_user.id, name=budget.category).first()
    selected_category_id = current_category_obj.id if current_category_obj else None

    return render_template(
        'budgets/edit_budget.html',
        user=current_user,
        budget=budget,
        categories=user_categories,
        selected_category_id=selected_category_id
    )


@budgets_bp.route('/delete_budget/<int:budget_id>', methods=['POST'])
@login_required
def delete_budget(budget_id):
    budget = Budget.query.get_or_404(budget_id)

    # Ensure the budget belongs to the current user
    if budget.user_id != current_user.id:
        flash('You are not authorized to delete this budget.', 'danger')
        abort(403) # Forbidden

    db.session.delete(budget)
    try:
        db.session.commit()
        flash('Budget deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting the budget: {str(e)}', 'danger')
        print(f"Database error during budget delete: {e}")

    return redirect(url_for('budgets.view_budgets'))