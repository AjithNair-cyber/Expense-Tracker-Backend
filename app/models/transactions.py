from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base

# Define the Transaction model representing a bank transaction in the database
class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="INR",
        nullable=False,
    )

    merchant: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    transaction_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    transaction_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    raw_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # To store whether is transaction is made from Credit card, Debit card, UPI, Netbanking, Cash, etc.
    transaction_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # To store the bank name from which the transaction is made
    bank_name: Mapped[str] = mapped_column(String(50), nullable=True)

    # To store the card name from which the transaction is made
    card_name: Mapped[str] = mapped_column(String(50), nullable=True)
