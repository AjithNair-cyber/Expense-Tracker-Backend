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

# Define a Pydantic model for the response after creating a transaction
class TransactionValidation(BaseModel):
    is_transaction: bool

# Define a Pydantic model for the response after parsing a transaction message
class TelegramIntent(BaseModel):
    intent: str
    category: CategoryType | None = None
    merchant: str | None = None
    month: int | None = None
    year: int | None = None
    amount: float | None = None
    limit: int | None = 5
    transaction_type: str | None = None
    transaction_date: datetime | None = None
    clarification_message: str | None