from fastapi import FastAPI
from app.api.transaction_routes import transaction_router
from app.api.telegram_routes import telegram_router



app = FastAPI(
    title="My Expense Tracker API",
    description="An API for tracking expenses and managing budgets.",
    version="1.0.0",
)

app.include_router(transaction_router)
app.include_router(telegram_router)
