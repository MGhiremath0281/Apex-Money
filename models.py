# personal_finance_manager_web/models.py

from database import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Base model for common fields like ID and creation/update timestamps
class Base(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


# --- User Model ---
class User(UserMixin, Base):
    __tablename__ = 'users'

    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True) # Changed to nullable=True as email might not always be required initially
    password_hash = db.Column(db.String(256), nullable=False)

    # Relationships to other models (cascade ensures associated data is deleted if user is deleted)
    categories = db.relationship('Category', backref='user', lazy=True, cascade="all, delete-orphan")
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade="all, delete-orphan")
    budgets = db.relationship('Budget', backref='user', lazy=True, cascade="all, delete-orphan") # Link to Budget model

    def __repr__(self):
        return f"<User {self.username}>"

    def get_id(self):
        return str(self.id)

    def set_password(self, password):
        # Using scrypt for modern password hashing (requires 'passlib[scrypt]' installed)
        # pip install passlib[scrypt]
        self.password_hash = generate_password_hash(password, method='scrypt')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# --- Category Model ---
class Category(Base):
    __tablename__ = 'categories'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(10), nullable=False) # e.g., 'expense' or 'income'

    # Ensure a user cannot have two categories with the exact same name
    __table_args__ = (db.UniqueConstraint('user_id', 'name', name='_user_name_uc'),)

    transactions = db.relationship('Transaction', backref='category', lazy=True)

    # If you choose to link Budget to Category via a foreign key (see Budget model below),
    # you might add a backref here if needed:
    # budgets_associated = db.relationship('Budget', backref='associated_category', lazy=True)

    def __repr__(self):
        return f"<Category {self.name} (Type: {self.type}, User: {self.user_id})>"


# --- Transaction Model (for both Income and Expenses) ---
class Transaction(Base):
    __tablename__ = 'transactions'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False) # Stores values like 100.00, 50.50
    description = db.Column(db.Text, nullable=True) # Made nullable=True, description can be optional
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    type = db.Column(db.String(10), nullable=False) # 'income' or 'expense'

    # Foreign key to Category model
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False) # Category is required for a transaction

    def __repr__(self):
        return f"<Transaction {self.type}: {self.amount} on {self.date} (Category: {self.category.name if self.category else 'N/A'})>"


# --- Budget Model ---
class Budget(Base):
    __tablename__ = 'budgets'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    start_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date()) # Changed to Date for consistency
    end_date = db.Column(db.Date, nullable=True) # Changed to Date for consistency, nullable=True for open-ended budgets

    # --- CHOOSE ONE OF THE FOLLOWING TWO APPROACHES FOR CATEGORY LINKING ---

    # APPROACH 1: Store category name as a string (YOUR CURRENT IMPLEMENTATION)
    # Pros: Simpler, no strict foreign key constraint.
    # Cons: No direct relational integrity; if category name changes, budgets aren't updated.
    #       Cannot easily query Category object from Budget directly.
    category_name = db.Column(db.String(100), nullable=False) # Renamed to 'category_name' for clarity

    # APPROACH 2: Link to Category via Foreign Key (RECOMMENDED FOR RELATIONAL INTEGRITY)
    # Pros: Enforces referential integrity; can easily navigate to Category object.
    # Cons: Requires careful handling of Category deletions (though cascade='all, delete-orphan' helps).
    #
    # If you choose this, UNCOMMENT the lines below and COMMENT OUT 'category_name' above.
    # category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    # associated_category = db.relationship('Category', backref='budgets_link', lazy=True) # Rename backref if needed

    # Add a unique constraint to prevent duplicate budgets for the same user, category, and time period
    # This might need adjustment based on how precise your budget periods are.
    # For example, a user shouldn't have two 'Groceries' budgets for the exact same month.
    # __table_args__ = (db.UniqueConstraint('user_id', 'category_id', 'start_date', name='_user_category_date_uc'),)
    # (If using category_name, replace category_id with category_name in the unique constraint)
    __table_args__ = (db.UniqueConstraint('user_id', 'category_name', 'start_date', name='_user_category_start_date_uc'),)


    def __repr__(self):
        # Adjust repr based on chosen category linking approach
        # If using category_name:
        return f"<Budget for {self.category_name} (User: {self.user_id}, Amount: {self.amount})>"
        # If using category_id and associated_category:
        # return f"<Budget for {self.associated_category.name if self.associated_category else 'N/A'} (User: {self.user_id}, Amount: {self.amount})>"