# personal_finance_manager_web/routes/transactions.py (REVISED)

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from personal_finance_manager_web.database import db
from personal_finance_manager_web.models import Transaction, Category, User
from sqlalchemy import desc

transactions_bp = Blueprint('transactions', __name__)

# Helper to get user categories by type
def get_user_categories_by_type(user_id, category_type):
    return Category.query.filter_by(user_id=user_id, type=category_type).all()

# --- ADD EXPENSE ---
@transactions_bp.route('/transactions/add/expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    expense_categories = get_user_categories_by_type(current_user.id, 'expense')
    if not expense_categories:
        flash('Please add some "expense" categories first (e.g., "Groceries", "Rent") before adding an expense.', 'warning')
        return redirect(url_for('categories.add_category')) # Assuming categories blueprint has add_category

    if request.method == 'POST':
        description = request.form.get('description')
        amount = request.form.get('amount')
        category_id = request.form.get('category_id')
        transaction_date_str = request.form.get('date')

        if not description or not amount or not category_id or not transaction_date_str:
            flash('All fields are required.', 'danger')
            return render_template('transactions/add_expense.html', user=current_user, categories=expense_categories)

        try:
            amount = float(amount)
            if amount <= 0:
                flash('Amount must be positive.', 'danger')
                return render_template('transactions/add_expense.html', user=current_user, categories=expense_categories)
            transaction_date = datetime.strptime(transaction_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid amount or date format. Please use YYYY-MM-DD.', 'danger')
            return render_template('transactions/add_expense.html', user=current_user, categories=expense_categories)

        # Validate category belongs to user and is of type 'expense'
        category = Category.query.filter_by(id=category_id, user_id=current_user.id, type='expense').first()
        if not category:
            flash('Invalid expense category selected.', 'danger')
            return render_template('transactions/add_expense.html', user=current_user, categories=expense_categories)

        new_expense = Transaction(
            user_id=current_user.id,
            description=description,
            amount=amount,
            type='expense',
            category_id=category_id,
            date=transaction_date
        )
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('transactions.view_expenses'))

    return render_template('transactions/add_expense.html', user=current_user, categories=expense_categories)


# --- ADD INCOME ---
@transactions_bp.route('/transactions/add/income', methods=['GET', 'POST'])
@login_required
def add_income():
    income_categories = get_user_categories_by_type(current_user.id, 'income')
    if not income_categories:
        flash('Please add some "income" categories first (e.g., "Salary", "Freelance") before adding income.', 'warning')
        return redirect(url_for('categories.add_category')) # Assuming categories blueprint has add_category

    if request.method == 'POST':
        description = request.form.get('description')
        amount = request.form.get('amount')
        category_id = request.form.get('category_id')
        transaction_date_str = request.form.get('date')

        if not description or not amount or not category_id or not transaction_date_str:
            flash('All fields are required.', 'danger')
            return render_template('transactions/add_income.html', user=current_user, categories=income_categories)

        try:
            amount = float(amount)
            if amount <= 0:
                flash('Amount must be positive.', 'danger')
                return render_template('transactions/add_income.html', user=current_user, categories=income_categories)
            transaction_date = datetime.strptime(transaction_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid amount or date format. Please use YYYY-MM-DD.', 'danger')
            return render_template('transactions/add_income.html', user=current_user, categories=income_categories)

        # Validate category belongs to user and is of type 'income'
        category = Category.query.filter_by(id=category_id, user_id=current_user.id, type='income').first()
        if not category:
            flash('Invalid income category selected.', 'danger')
            return render_template('transactions/add_income.html', user=current_user, categories=income_categories)

        new_income = Transaction(
            user_id=current_user.id,
            description=description,
            amount=amount,
            type='income',
            category_id=category_id,
            date=transaction_date
        )
        db.session.add(new_income)
        db.session.commit()
        flash('Income added successfully!', 'success')
        return redirect(url_for('transactions.view_income'))

    return render_template('transactions/add_income.html', user=current_user, categories=income_categories)

# --- VIEW EXPENSES ---
@transactions_bp.route('/transactions/expenses')
@login_required
def view_expenses():
    user_expenses = Transaction.query.filter_by(user_id=current_user.id, type='expense').order_by(desc(Transaction.date)).all()
    return render_template('transactions/view_expense.html', user=current_user, expenses=user_expenses)

# --- VIEW INCOME ---
@transactions_bp.route('/transactions/income')
@login_required
def view_income():
    user_income = Transaction.query.filter_by(user_id=current_user.id, type='income').order_by(desc(Transaction.date)).all()
    return render_template('transactions/view_income.html', user=current_user, income_transactions=user_income)


# --- EDIT TRANSACTION (remains unified, it's an 'edit_transaction.html') ---
@transactions_bp.route('/transactions/edit/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)

    if transaction.user_id != current_user.id:
        flash('You do not have permission to edit this transaction.', 'danger')
        # Redirect to the appropriate view page based on transaction type
        if transaction.type == 'expense':
            return redirect(url_for('transactions.view_expenses'))
        else:
            return redirect(url_for('transactions.view_income'))


    # Get categories of the same type as the transaction being edited
    relevant_categories = get_user_categories_by_type(current_user.id, transaction.type)

    if request.method == 'POST':
        description = request.form.get('description')
        amount = request.form.get('amount')
        category_id = request.form.get('category_id')
        transaction_date_str = request.form.get('date')

        if not description or not amount or not category_id or not transaction_date_str:
            flash('All fields are required.', 'danger')
            return render_template('transactions/edit_transaction.html', user=current_user, categories=relevant_categories, transaction=transaction)

        try:
            amount = float(amount)
            if amount <= 0:
                flash('Amount must be positive.', 'danger')
                return render_template('transactions/edit_transaction.html', user=current_user, categories=relevant_categories, transaction=transaction)
            transaction_date = datetime.strptime(transaction_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid amount or date format. Please use YYYY-MM-DD.', 'danger')
            return render_template('transactions/edit_transaction.html', user=current_user, categories=relevant_categories, transaction=transaction)

        # Validate category belongs to user and is of the correct type
        category = Category.query.filter_by(id=category_id, user_id=current_user.id, type=transaction.type).first()
        if not category:
            flash('Invalid category selected for this transaction type.', 'danger')
            return render_template('transactions/edit_transaction.html', user=current_user, categories=relevant_categories, transaction=transaction)

        transaction.description = description
        transaction.amount = amount
        transaction.category_id = category_id
        # transaction.type is already set based on the original transaction
        transaction.date = transaction_date

        db.session.commit()
        flash('Transaction updated successfully!', 'success')
        # Redirect to the view page based on transaction type
        if transaction.type == 'expense':
            return redirect(url_for('transactions.view_expenses'))
        else:
            return redirect(url_for('transactions.view_income'))

    # GET request: pre-populate form with existing transaction data
    return render_template('transactions/edit_transaction.html', user=current_user, categories=relevant_categories, transaction=transaction)


# --- DELETE TRANSACTION (remains unified) ---
@transactions_bp.route('/transactions/delete/<int:transaction_id>', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)

    if transaction.user_id != current_user.id:
        flash('You do not have permission to delete this transaction.', 'danger')
        # Redirect to the appropriate view page based on transaction type
        if transaction.type == 'expense':
            return redirect(url_for('transactions.view_expenses'))
        else:
            return redirect(url_for('transactions.view_income'))

    transaction_type = transaction.type # Store type before deleting
    db.session.delete(transaction)
    db.session.commit()
    flash('Transaction deleted successfully!', 'success')

    # Redirect to the appropriate view page based on original transaction type
    if transaction_type == 'expense':
        return redirect(url_for('transactions.view_expenses'))
    else:
        return redirect(url_for('transactions.view_income'))