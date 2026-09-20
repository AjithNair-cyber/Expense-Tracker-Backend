
# Transaction Routes 
from fastapi import APIRouter, Depends, Request
from app.ai.ai_functions import is_valid_transaction_message, parse_transaction_message
from app.models.transactions import Transaction
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schema.transaction_schema import TransactionCreate
from app.config.config import settings
from app.services.telegram_services import send_message

# Create a router for transaction-related endpoints
transaction_router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
)

@transaction_router.get("/health")
async def health_check():
    return {"status": "healthy"}

# Define a POST endpoint for ingesting transaction messages
# This endpoint will receive a bank SMS message, validate it, and parse it into a transaction
@transaction_router.post("/ingest")
async def ingest_transaction(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    header = request.headers.get('authentication' or None)

    # if (header is None) or (header != settings.AUTH_TOKEN):
    #     return {"status": "unauthorized", "message": "Invalid authentication header"}

    message = body.decode("utf-8")

    # Validate if the message is a valid transaction
    if not await is_valid_transaction_message(message):
        print(f"Invalid transaction message: {message}")
        return {"status": "invalid", "message": message}


    # Parse the transaction message to extract details
    parsed = await parse_transaction_message(message)

    # Create a new TransactionCreate object with the parsed details
    new_transaction = TransactionCreate(
    amount=parsed.amount,
    currency=parsed.currency,
    merchant=parsed.merchant,
    category=parsed.category,
    transaction_type=parsed.transaction_type,
    transaction_date=parsed.transaction_date,
    source="sms",
    raw_message=message,
    transaction_mode=parsed.transaction_mode,
    bank_name=parsed.bank_name,
    card_name=parsed.card_name
)   
    print(f"Parsed transaction: {new_transaction.model_dump()}")

    # Save the new transaction to the database
    db_transaction = Transaction(**new_transaction.model_dump())

    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    await send_message(
        chat_id=settings.USER_ID,
        text=f"New transaction received: {new_transaction.amount} {new_transaction.currency} at {new_transaction.merchant or 'Unknown Merchant'} on {new_transaction.transaction_date.strftime('%Y-%m-%d %H:%M:%S') } for merchant {new_transaction.merchant or 'Unknown Merchant'} in category {new_transaction.category or 'Uncategorized'} via {new_transaction.transaction_mode or 'Unknown Mode'} via {new_transaction.source or 'Unknown Source'}",
    )

    return {
        "status": "received",
        "message": message,
    }