from datetime import date, timedelta, datetime
from decimal import Decimal
from sqlalchemy import func, text, extract
from  app.models.transactions import Transaction
from sqlalchemy.orm import Session

# Function to get the latest transaction from the database
async def get_latest_transaction(db: Session):
    return (
        db.query(Transaction)
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc(),
        )
        .first()
    )

# Function to summarize transactions for the last month by category and type
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

# Function to summarize all the transactions ever
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

# Function to summarize transactions for a specific month and year
async def get_monthly_summary(db: Session, month: int | None = None, year: int | None = None):
    """
    Summarize transactions by category and type for a specific month and year.
    If month or year is not provided, defaults to the current calendar month.
 
    Returns a list of rows: (category, transaction_type, total_amount).
    """
    today = date.today()
 
    if month is None or year is None:
        first_of_this_month = today.replace(day=1)
        last_day_of_this_month = first_of_this_month.replace(day=1) + timedelta(days=32)
        last_day_of_this_month = last_day_of_this_month.replace(day=1) - timedelta(days=1)
        month = first_of_this_month.month
        year = first_of_this_month.year
 
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

# Function to summarize transactions for a specific category
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

# Function to summarize transactions for a specific transaction type
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

# Function to summarize transactions for a specific merchant
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

# Function to get recent transactions, limited to a specified number
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


# Function to add a new transaction to the database
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

async def get_transaction_by_id(
    db: Session,
    transaction_id: int,
):
    return (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id)
        .first()
    )

async def get_recent_transactions(
    db: Session,
    limit: int = 5,
):
    return (
        db.query(Transaction)
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc(),
        )
        .limit(limit)
        .all()
    )

async def get_transactions_between_dates(
    db: Session,
    start_date: datetime,
    end_date: datetime,
):
    return (
        db.query(Transaction)
        .filter(
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc(),
        )
        .all()
    )

async def get_transactions_between_dates(
    db: Session,
    start_date: datetime,
    end_date: datetime,
):
    return (
        db.query(Transaction)
        .filter(
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc(),
        )
        .all()
    )

async def get_transactions_by_category(
    db: Session,
    category: str,
):
    return (
        db.query(Transaction)
        .filter(Transaction.category == category)
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc(),
        )
        .all()
    )



async def get_transactions_by_merchant(
    db: Session,
    merchant: str,
):
    return (
        db.query(Transaction)
        .filter(Transaction.merchant.ilike(f"%{merchant}%"))
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc(),
        )
        .all()
    )

async def get_transactions_by_type(
    db: Session,
    transaction_type: str,
):
    return (
        db.query(Transaction)
        .filter(Transaction.transaction_type == transaction_type)
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc(),
        )
        .all()
    )

async def get_daily_summary(
    db: Session,
    date: datetime,
):
    transactions = (
        db.query(Transaction)
        .filter(
            Transaction.transaction_date >= date.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            ),
            Transaction.transaction_date < (
                date.replace(
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                ) + timedelta(days=1)
            ),
        )
        .all()
    )

    total_expense = sum(
        transaction.amount
        for transaction in transactions
        if transaction.transaction_type == "expense"
    )

    total_income = sum(
        transaction.amount
        for transaction in transactions
        if transaction.transaction_type == "income"
    )

    return {
        "total_expense": total_expense,
        "total_income": total_income,
        "balance": total_income - total_expense,
        "transaction_count": len(transactions),
    }

async def get_yearly_summary(
    db: Session,
    year: int,
):
    transactions = (
        db.query(Transaction)
        .filter(
            extract("year", Transaction.transaction_date) == year
        )
        .all()
    )

    total_expense = sum(
        transaction.amount
        for transaction in transactions
        if transaction.transaction_type == "expense"
    )

    total_income = sum(
        transaction.amount
        for transaction in transactions
        if transaction.transaction_type == "income"
    )

    return {
        "year": year,
        "total_expense": total_expense,
        "total_income": total_income,
        "balance": total_income - total_expense,
        "transaction_count": len(transactions),
    }

async def get_largest_transactions(
    db: Session,
    limit: int = 5,
):
    return (
        db.query(Transaction)
        .filter(Transaction.transaction_type == "expense")
        .order_by(
            Transaction.amount.desc(),
            Transaction.transaction_date.desc(),
        )
        .limit(limit)
        .all()
    )

async def find_duplicate_transactions(
    db: Session,
    amount: Decimal,
    merchant: str | None,
    transaction_date: datetime,
):
    query = (
        db.query(Transaction)
        .filter(
            Transaction.amount == amount,
            Transaction.transaction_date == transaction_date,
        )
    )

    if merchant:
        query = query.filter(
            Transaction.merchant.ilike(merchant)
        )

    return query.all()