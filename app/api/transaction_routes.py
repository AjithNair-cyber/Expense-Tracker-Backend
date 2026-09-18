
# Transaction Routes 
from fastapi import APIRouter, Depends, Request
from app.ai.ai_functions import is_valid_transaction_message, parse_transaction_message
from app.models.transactions import Transaction
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schema.transaction_schema import TransactionCreate

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

    message = body.decode("utf-8")

    print(f"Received message: {message}")
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
)   
    print(f"Parsed transaction: {new_transaction.model_dump()}")

    # Save the new transaction to the database
    db_transaction = Transaction(**new_transaction.model_dump())

    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    return {
        "status": "received",
        "message": message,
        "parsed": parsed
    }