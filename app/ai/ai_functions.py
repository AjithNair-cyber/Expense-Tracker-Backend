from openai import OpenAI
from app.config.config import settings
from app.schema.transaction_schema import TransactionCreate, TransactionValidation, TelegramIntent

# Initialize the OpenAI client with the API key from settings
client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)

# Function to validate if a message is a valid transaction
async def is_valid_transaction_message(message: str) -> bool:
    """
    Validate whether the given message is a valid bank transaction.
    Returns True for actual financial transactions and False for non-transaction messages.
    """

    response = client.responses.parse(
        model=settings.OPENAI_MODEL,
        input=[
            {
                "role": "system",
                "content": """
You are a bank SMS transaction validator.

Determine whether the given message is a valid bank transaction.

Return is_transaction=true for actual financial transactions
such as payments, debits, credits, withdrawals, deposits, and transfers.

Return is_transaction=false for promotional messages, advertisements,
OTPs, security alerts, balance-only messages, general bank announcements,
or messages without evidence of an actual transaction.

Do not infer a transaction when there is insufficient evidence.
"""
            },
            {
                "role": "user",
                "content": message
            }
        ],
        text_format=TransactionValidation,
    )

    return response.output_parsed.is_transaction
    

# Function to parse a bank SMS message and extract transaction details
async def parse_transaction_message(message: str):
    """
    Parse a bank SMS message to extract transaction details.
    Returns a TransactionCreate object with the extracted information.
    """
    response = client.responses.parse(
        model=settings.OPENAI_MODEL,
        input=[
            {
                "role": "system",
                "content": """
You are an expense transaction parser.

Extract transaction information from bank SMS messages.

Rules:

- Identify the transaction amount.
- Identify the merchant or recipient.
- Determine whether this is an "expense" or "income".
- Extract the transaction date if present.
- Use "INR" when the message indicates Indian Rupees.
- Identify the appropriate category based on the merchant or transaction.
- Do not invent information.
- Return the extracted date in a uniform format (YYYY-MM-DD).
- If a field cannot be determined, return null.

Category rules:

- food: restaurants, cafes, food delivery, fast food, bakeries, snacks
- grocery: supermarkets, grocery stores, vegetables, fruits, household groceries
- shopping: Amazon, Flipkart, clothing, electronics, retail purchases
- transport: Uber, Ola, taxis, metro, buses, parking, auto-rickshaws
- fuel: petrol, diesel, CNG, EV charging, fuel stations
- travel: flights, hotels, trains, travel bookings
- entertainment: movies, games, events, amusement parks
- subscriptions: Netflix, Spotify, YouTube Premium, software subscriptions
- utilities: electricity, water, gas, internet, mobile bills and recharges
- healthcare: hospitals, doctors, pharmacies, medical labs
- education: schools, colleges, courses, tuition, educational services
- finance: bank charges, loan payments, investments, insurance
- rent: house rent, office rent, property rent
- government: taxes, government fees, fines, government services
- personal: money transfers to individuals, gifts, personal payments
- other: use when the transaction cannot reasonably be classified

Important:

- Categorize based on the actual merchant or recipient, not the bank.
- For example, if an HDFC Bank SMS says a payment was made to Swiggy, the merchant is Swiggy and the category is "food".
- Amazon should generally be categorized as "shopping".
- Uber and Ola should be categorized as "transport".
- Indian Oil, HPCL, BPCL and similar fuel stations should be categorized as "fuel".
- Netflix and Spotify should be categorized as "subscriptions".
- Transfers to an individual should generally be categorized as "personal".
- Do not assume a category when there is insufficient information. Use "other".
"""
            },
            {
                "role": "user",
                "content": message
            }
        ],
        text_format=TransactionCreate
    )

    return response.output_parsed


# Function to parse a Telegram message and determine the user's intent
async def parse_telegram_message(message: str):
    """
    Parse a Telegram message to determine the user's intent and extract relevant information.
    Returns a TelegramIntent object with the extracted information.
    """
    response = client.responses.parse(
        model=settings.OPENAI_MODEL,
        input=[
            {
                "role": "system",
                "content": """
You are an expense tracker assistant.

Determine what the user wants to do with their expense tracker.

Possible intents:

- monthly_summary
- category_summary
- merchant_summary
- recent_transactions
- add_transaction
- transaction_type_summary
- unknown

Extract any relevant information from the message.

For category_summary:
- Extract the requested expense category.

For merchant_summary:
- Extract the merchant name.

For transaction_type_summary:
- Extract the transaction type. Return "expense" or "income" when possible. Return null when not specified.

For add_transaction:
- Extract the amount, merchant, transaction_type, transaction_date and category when available. Return OTHER for category when it cannot be determined.

For monthly_summary:
- Extract the requested month and year when explicitly provided.

Do not invent values.
Return null when information is not available.
"""
            },
            {
                "role": "user",
                "content": message
            }
        ],
        text_format=TelegramIntent,
    ) 

    return response.output_parsed