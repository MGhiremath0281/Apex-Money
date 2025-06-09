# personal_finance_manager_web/routes/reports.py (REVISED)

from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from personal_finance_manager_web.database import db
from personal_finance_manager_web.models import Transaction, Category

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
def generate_reports():
    user_id = current_user.id
    report_type = request.args.get('type', 'monthly_summary') # Default report type
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)

    # All categories for the 'expense_breakdown_report.html' category filter
    all_expense_categories = Category.query.filter_by(user_id=user_id, type='expense').order_by(Category.name).all()

    # --- Data for Monthly Summary Report (monthly_summary_report.html) ---
    monthly_data = []
    if report_type == 'monthly_summary':
        # Get data for the last 12 months (or customizable range)
        for i in range(12): # Last 12 months
            current_month_start = datetime(year, month, 1) - timedelta(days=(30 * i)) # Approximate month start
            current_month_start = current_month_start.replace(day=1) # Accurate month start

            current_month_end = (current_month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            month_income = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.type == 'income',
                Transaction.date >= current_month_start,
                Transaction.date <= current_month_end
            ).scalar() or 0.00

            month_expense = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.type == 'expense',
                Transaction.date >= current_month_start,
                Transaction.date <= current_month_end
            ).scalar() or 0.00

            monthly_data.append({
                'month': current_month_start.strftime('%b %Y'),
                'income': month_income,
                'expense': month_expense,
                'net': month_income - month_expense
            })
        # Reverse to show most recent month first
        monthly_data.reverse()

    # --- Data for Expense Breakdown Report (expense_breakdown_report.html) ---
    expense_breakdown_data = []
    selected_expense_category_id = request.args.get('expense_category_id', type=int)

    if report_type == 'expense_breakdown':
        # Default to current month for breakdown, or use selected month/year
        breakdown_month_start = datetime(year, month, 1).date()
        breakdown_month_end = (breakdown_month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

        base_expense_query = db.session.query(
            Category.name,
            func.sum(Transaction.amount).label('total_spent')
        ).join(Transaction, Category.id == Transaction.category_id).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'expense',
            Transaction.date >= breakdown_month_start,
            Transaction.date <= breakdown_month_end
        )

        if selected_expense_category_id:
            base_expense_query = base_expense_query.filter(Category.id == selected_expense_category_id)
            selected_category_obj = Category.query.get(selected_expense_category_id)
            if not selected_category_obj or selected_category_obj.user_id != user_id or selected_category_obj.type != 'expense':
                flash("Invalid expense category selected.", 'danger')
                selected_expense_category_id = None # Reset if invalid
                # Re-run query without specific category
                expense_breakdown_data = db.session.query(
                    Category.name,
                    func.sum(Transaction.amount).label('total_spent')
                ).join(Transaction, Category.id == Transaction.category_id).filter(
                    Transaction.user_id == user_id,
                    Transaction.type == 'expense',
                    Transaction.date >= breakdown_month_start,
                    Transaction.date <= breakdown_month_end
                ).group_by(Category.name).order_by(desc(func.sum(Transaction.amount))).all()
            else:
                # If specific category, just query for that category, no group_by for breakdown
                expense_breakdown_data = base_expense_query.group_by(Category.name).order_by(desc(func.sum(Transaction.amount))).all()
                # For a single category, maybe show individual transactions here, not just sum
                # For now, we'll stick to sums for simplicity in this report.
        else:
            expense_breakdown_data = base_expense_query.group_by(Category.name).order_by(desc(func.sum(Transaction.amount))).all()

        # Calculate total for the breakdown period
        total_breakdown_expense = sum(item.total_spent for item in expense_breakdown_data if item.total_spent)
    else:
        total_breakdown_expense = 0.00


    # Render the appropriate report template based on `report_type`
    if report_type == 'monthly_summary':
        return render_template(
            'reports/monthly_summary_report.html',
            user=current_user,
            monthly_data=monthly_data,
            selected_year=year,
            selected_month=month,
            current_year=datetime.now().year
        )
    elif report_type == 'expense_breakdown':
        return render_template(
            'reports/expense_breakdown_report.html',
            user=current_user,
            expense_breakdown_data=expense_breakdown_data,
            total_breakdown_expense=total_breakdown_expense,
            selected_year=year,
            selected_month=month,
            selected_expense_category_id=selected_expense_category_id,
            all_expense_categories=all_expense_categories,
            current_year=datetime.now().year
        )
    else:
        # Default fallback or error
        flash("Invalid report type selected.", "danger")
        return redirect(url_for('reports.generate_reports', type='monthly_summary'))