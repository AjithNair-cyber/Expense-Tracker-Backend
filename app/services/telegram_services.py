import logging
import httpx
from sqlalchemy.orm import Session
from app.ai.ai_functions import parse_telegram_message
from app.config.config import settings
from app.services.transaction_services import (
    add_transaction,
    get_category_summary,
    get_latest_transaction,
    get_merchant_summary,
    get_monthly_summary,
    summarize_all_transactions,
    get_transaction_type_summary,
    get_recent_transactions
)
from app.helpers.telegram_helpers import (
    format_needs_clarification,
    format_welcome,
    format_monthly_summary,
    format_category_summary,
    format_merchant_summary,
    format_recent_transaction,
    format_transaction_added,
    format_no_transactions,
    format_unknown_command,
    format_could_not_understand,
    format_error,
    format_recent_transactions
)

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Slash command handling
# ----------------------------------------------------------------------

async def handle_command(command: str, db: Session) -> str:
    command = command.strip().lower()

    if command == "/start":
        return format_welcome()

    if command == "/summary":
        try:
            summary = await summarize_all_transactions(db)
        except Exception:
            logger.exception("Failed to summarize transactions")
            return format_error()
        return format_monthly_summary(summary)

    if command == "/recent":
        try:
            transaction = await get_latest_transaction(db)
        except Exception:
            logger.exception("Failed to fetch latest transaction")
            return format_error()

        if not transaction:
            return format_no_transactions()

        return format_recent_transaction(transaction)

    return format_unknown_command(command)


# ----------------------------------------------------------------------
# Free-text / AI-intent handling
# ----------------------------------------------------------------------

async def handle_text(text: str, db: Session) -> str:
    logger.debug("Handling free-text message: %s", text)

    try:
        intent = await parse_telegram_message(text)
    except Exception:
        logger.exception("Failed to parse message intent")
        return format_error()

    logger.debug("Parsed intent: %s", intent)

    try:
        if intent.intent == "needs_clarification":
            return format_needs_clarification(intent.clarification_message)

        if intent.intent == "monthly_summary":
            print(f"Fetching monthly summary for month={intent.month}, year={intent.year}")
            summary = await get_monthly_summary(db=db, month=intent.month, year=intent.year)
            return format_monthly_summary(summary, month=intent.month, year=intent.year)

        if intent.intent == "category_summary":
            summary = await get_category_summary(db=db, category=intent.category)
            print(f"Category summary for {intent.category}: {summary}")
            return format_category_summary(intent.category, summary)

        if intent.intent == "merchant_summary":
            print(f"Fetching merchant summary for merchant={intent.merchant}")
            summary = await get_merchant_summary(db=db, merchant=intent.merchant)
            return format_merchant_summary(intent.merchant, summary)

        if intent.intent == "recent_transactions":
            print("Fetching most recent transaction", intent.model_dump())
            transaction = await get_recent_transactions(db, limit=intent.limit)
            if not transaction:
                return format_no_transactions()
            return format_recent_transactions(transaction)

        if intent.intent == "transaction_type_summary":
            print(f"Fetching transaction type summary for type={intent.transaction_type}")
            summary = await get_transaction_type_summary(db=db, transaction_type=intent.transaction_type)
            return format_category_summary(intent.transaction_type, summary)

        if intent.intent == "add_transaction":
            print(f"Adding new transaction: {intent.amount} {intent.merchant or ''} {intent.category or ''}")
            transaction = await add_transaction(
                db=db,
                amount=intent.amount,
                merchant=intent.merchant,
                category=intent.category,
            )
            return format_transaction_added(transaction)

    except Exception:
        logger.exception("Failed to handle intent '%s'", getattr(intent, "intent", None))
        return format_error()

    return format_could_not_understand()


# ----------------------------------------------------------------------
# Telegram send wrapper
# ----------------------------------------------------------------------

async def send_message(
    chat_id: int,
    text: str,
    parse_mode: str = "HTML",
    disable_web_page_preview: bool = True,
) -> bool:
    """
    Send a message to a Telegram chat.

    Returns True on success, False on failure (logged, never raises),
    so a formatting bug or transient network error can't crash the bot.
    """
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_web_page_preview,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
        return True

    except httpx.HTTPStatusError as e:
        logger.error(
            "Telegram API error %s for chat_id=%s: %s",
            e.response.status_code,
            chat_id,
            e.response.text,
        )
    except httpx.RequestError as e:
        logger.error("Network error sending to chat_id=%s: %s", chat_id, e)

    return False