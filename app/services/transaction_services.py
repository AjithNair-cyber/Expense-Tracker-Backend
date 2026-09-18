from datetime import date, timedelta

from sqlalchemy import func, text

from  app.models.transactions import Transaction
from sqlalchemy.orm import Session


async def get_latest_transaction(db: Session):
    return (
        db.query(Transaction)
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc(),
        )
        .first()
    )


async def summarize_transactions_for_last_month(db: Session):
    """
    Summarize transactions by category and type for the previous calendar month.
 
    Returns a list of rows: (category, transaction_type, total_amount).
    """
    today = date.today()
    first_of_this_month = today.replace(day=1)
    last_day_of_previous_month = first_of_this_month - timedelta(days=1)
    first_day_of_previous_month = last_day_of_previous_month.replace(day=1)
 
    summary = (
        db.query(
            Transaction.category,
            Transaction.transaction_type,
            func.sum(Transaction.amount).label("total_amount"),
        )
        .filter(
            Transaction.transaction_date >= first_day_of_previous_month,
            Transaction.transaction_date <= last_day_of_previous_month,
        )
        .group_by(Transaction.category, Transaction.transaction_type)
        .order_by(Transaction.category)
        .all()
    )
 
    return summary

async def summarize_all_transactions(db: Session):
    """
    Summarize transactions by category and type for all time.
 
    Returns a list of rows: (category, transaction_type, total_amount).
    """
    summary = (
        db.query(
            Transaction.category,
            Transaction.transaction_type,
            func.sum(Transaction.amount).label("total_amount"),
        )
        .group_by(Transaction.category, Transaction.transaction_type)
        .order_by(Transaction.category)
        .all()
    )
 
    return summary

async def get_monthly_summary(db: Session, month: int | None = None, year: int | None = None):
    """
    Summarize transactions by category and type for a specific month and year.
    If month or year is not provided, defaults to the previous calendar month.
 
    Returns a list of rows: (category, transaction_type, total_amount).
    """
    today = date.today()
 
    if month is None or year is None:
        first_of_this_month = today.replace(day=1)
        last_day_of_previous_month = first_of_this_month - timedelta(days=1)
        first_day_of_previous_month = last_day_of_previous_month.replace(day=1)
        month = first_day_of_previous_month.month
        year = first_day_of_previous_month.year
 
    summary = (
        db.query(
            Transaction.category,
            Transaction.transaction_type,
            func.sum(Transaction.amount).label("total_amount"),
        )
        .filter(
            func.extract("month", Transaction.transaction_date) == month,
            func.extract("year", Transaction.transaction_date) == year,
        )
        .group_by(Transaction.category, Transaction.transaction_type)
        .order_by(Transaction.category)
        .all()
    )
 
    return summary

async def get_category_summary(db: Session, category: str):
    """
    Summarize transactions by type for a specific category.
 
    Returns a list of rows: (transaction_type, total_amount).
    """
    summary = (
        db.query(
            Transaction.category,
            Transaction.transaction_type,
            func.sum(Transaction.amount).label("total_amount"),
        )
        .filter(Transaction.category == category)
        .group_by(Transaction.category, Transaction.transaction_type)
        .order_by(Transaction.transaction_type)
        .all()
    )
 
    return summary

async def get_transaction_type_summary(db: Session, transaction_type: str):
    """
    Summarize transactions by category for a specific transaction type.
 
    Returns a list of rows: (category, total_amount).
    """
    summary = (
        db.query(
            Transaction.transaction_type,
            Transaction.category,
            func.sum(Transaction.amount).label("total_amount"),
        )
        .filter(Transaction.transaction_type == transaction_type)
        .group_by(Transaction.category, Transaction.transaction_type)
        .order_by(Transaction.category)
        .all()
    )
 
    return summary

async def get_merchant_summary(db: Session, merchant: str):
    """
    Summarize transactions by type for a specific merchant.
 
    Returns a list of rows: (transaction_type, total_amount).
    """
    summary = (
        db.query(
            Transaction.merchant,
            Transaction.transaction_type,
            func.sum(Transaction.amount).label("total_amount"),
        )
        .filter(Transaction.merchant == merchant)
        .group_by(Transaction.merchant, Transaction.transaction_type)
        .order_by(Transaction.transaction_type)
        .all()
    )
 
    return summary

async def get_recent_transactions(db: Session, limit: int = 5):
    """
    Get the most recent transactions, limited to a specified number.
 
    Returns a list of Transaction objects.
    """
    recent_transactions = (
        db.query(Transaction)
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc(),
        )
        .limit(limit)
        .all()
    )
 
    return recent_transactions

async def add_transaction(db: Session, amount: float, merchant: str | None = None, category: str | None = None):
    """
    Add a new transaction to the database.
 
    Returns the newly created Transaction object.
    """
    new_transaction = Transaction(
        amount=amount,
        currency="INR",
        merchant=merchant,
        category=category,
        transaction_type="expense",  # Assuming all added transactions are expenses
        transaction_date=date.today(),
        source="telegram",
        raw_message=f"Added via Telegram: {amount} {merchant or ''} {category or ''}",
    )
 
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
 
    return new_transaction