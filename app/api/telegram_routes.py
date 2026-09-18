from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.telegram_services import handle_command, send_message, handle_text
from app.config.config import settings
# Create a router for Telegram-related endpoints
telegram_router = APIRouter(
    prefix="/telegram",
    tags=["Telegram"],
)


# Define a POST endpoint for the Telegram webhook
# This endpoint will receive updates from Telegram and process them accordingly.
# Body: The request body will contain the update from Telegram, which includes the message sent by the user.
@telegram_router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    # Get the update from the request body
    update = await request.json()
    user = update.get('message', {}).get('from', {}).get('id', 'unknown')
    print(f"Received update from user {user}: user != settings.USER_ID: {user } : {settings.USER_ID} {user != settings.USER_ID}")
    if user != settings.USER_ID:
        return {"status": "ignored", "message": "Unauthorized user"}
    # Check if the update contains a message
    message = update.get("message")

    if not message:
        return {"status": "ignored"}

    # Get the text of the message
    text = message.get("text")

    if not text:
        return {"status": "ignored"}

    # Get the chat ID to send a response back to the user
    chat_id = message["chat"]["id"]

    # Handle the message based on whether it is a command or normal text
    if text.startswith("/"):
        response = await handle_command(text, db)

    # Normal text
    else:
        response = await handle_text(text, db)

    # Send the response back to the user via Telegram
    await send_message(
        chat_id=chat_id,
        text=response,
    )

    return {"status": "ok"}