from datetime import datetime
from enum import Enum
from pydantic import BaseModel

# Define an enumeration for transaction categories
class CategoryType(str, Enum):
    FOOD = "food"
    GROCERY = "grocery"
    SHOPPING = "shopping"
    TRANSPORT = "transport"
    FUEL = "fuel"
    TRAVEL = "travel"
    ENTERTAINMENT = "entertainment"
    SUBSCRIPTIONS = "subscriptions"
    UTILITIES = "utilities"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    FINANCE = "finance"
    RENT = "rent"
    GOVERNMENT = "government"
    PERSONAL = "personal"
    OTHER = "other"

# Define a Pydantic model for creating a new transaction
class TransactionCreate(BaseModel):
    amount: float
    currency: str = "INR"
    merchant: str | None = None
    category: CategoryType | None = None
    transaction_type: str
    transaction_date: datetime
    raw_message: str | None = None
    source: str
    transaction_mode: str = "unknown"  # To store whether the transaction is made from Credit card, Debit card, UPI, Netbanking, Cash, etc.
    bank_name: str | None = None  # To store the bank name from which the transaction is made
    card_name: str | None = None  # To store the card name from which the transaction is made

# Define a Pydantic model for the response after creating a transaction
class TransactionValidation(BaseModel):
    is_transaction: bool

# Define a Pydantic model for the response after parsing a transaction message
class TelegramIntent(BaseModel):
    # Primary action
    intent: str

    # Transaction details / filters
    category: CategoryType | None = None
    merchant: str | None = None
    transaction_type: str | None = None
    transaction_mode: str | None = None

    # Financial details
    amount: float | None = None
    currency: str | None = "INR"

    # Date filters
    month: int | None = None
    year: int | None = None
    transaction_date: datetime | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None

    # Transaction identification
    transaction_id: int | None = None

    # Account / payment information
    bank_name: str | None = None
    card_name: str | None = None

    # Result limits
    limit: int | None = 5

    # Clarification
    clarification_message: str | None = None