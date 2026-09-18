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
    summarize_transactions_for_last_month,
    get_transaction_type_summary
)

logger = logging.getLogger(__name__)

DIVIDER = "─" * 24
MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


# ----------------------------------------------------------------------
# Formatting helpers
# ----------------------------------------------------------------------

def _wrap(title: str, body: str, emoji: str = "") -> str:
    """Standard message shell: emoji title, divider, body."""
    header = f"{emoji} <b>{title}</b>".strip()
    return f"{header}\n{DIVIDER}\n{body}"

# Formatter for grouped rows, used in summaries
def _format_grouped_rows(rows) -> tuple[str, float, float]:
    """
    Shared renderer for rows shaped like (category_or_group, txn_type, amount).
    Returns (body_text, total_income, total_expense).
    """
    grouped: dict[str, list[tuple[str, float]]] = {}
    total_income = 0.0
    total_expense = 0.0

    for group, txn_type, amount in rows:
        grouped.setdefault(group, []).append((txn_type, amount))
        if txn_type.lower() == "income":
            total_income += float(amount)
        else:
            total_expense += float(amount)

    lines = []
    for group, entries in grouped.items():
        lines.append(f"<b>{group}</b>")
        for txn_type, amount in entries:
            icon = "🟢" if txn_type.lower() == "income" else "🔴"
            lines.append(f"  {icon} {txn_type}: ₹{amount:,.2f}")

    return "\n".join(lines), total_income, total_expense

# Formatter for welcome message
def format_welcome() -> str:
    body = (
        "Track your spending right from Telegram.\n\n"
        "<b>Commands</b>\n"
        "💰 /summary — Monthly spending summary\n"
        "🧾 /recent — Most recent transaction\n\n"
        "Or just message me naturally, e.g. <i>\"spent 450 on lunch at Truffles\"</i> "
        "or <i>\"how much did I spend at Zomato?\"</i>"
    )
    return _wrap("Welcome to Expense Tracker", body, emoji="👋")

# Formatter for monthly summary
def format_monthly_summary(summary, month: int | None = None, year: int | None = None) -> str:
    title = "Monthly Summary"
    if month:
        title = f"Summary — {MONTH_NAMES[month]} {year}" if year else f"Summary — {MONTH_NAMES[month]}"

    if not summary:
        return _wrap(title, "No transactions found for that period. 🎉", emoji="📊")

    body, total_income, total_expense = _format_grouped_rows(summary)
    body += (
        f"\n{DIVIDER}\n"
        f"💵 <b>Total Income:</b> ₹{total_income:,.2f}\n"
        f"💸 <b>Total Expense:</b> ₹{total_expense:,.2f}"
    )
    return _wrap(title, body, emoji="📊")


def format_category_summary(category: str, summary) -> str:
    title = f"Category: {category}"

    if not summary:
        return _wrap(title, f"No transactions found for <b>{category}</b>. 🤷", emoji="🏷️")

    body, total_income, total_expense = _format_grouped_rows(summary)
    body += (
        f"\n{DIVIDER}\n"
        f"💵 <b>Total Income:</b> ₹{total_income:,.2f}\n"
        f"💸 <b>Total Expense:</b> ₹{total_expense:,.2f}"
    )
    return _wrap(title, body, emoji="🏷️")


def format_merchant_summary(merchant: str, summary) -> str:
    title = f"Merchant: {merchant}"

    if not summary:
        return _wrap(title, f"No transactions found for <b>{merchant}</b>. 🤷", emoji="🏪")

    body, total_income, total_expense = _format_grouped_rows(summary)
    body += (
        f"\n{DIVIDER}\n"
        f"💵 <b>Total Income:</b> ₹{total_income:,.2f}\n"
        f"💸 <b>Total Expense:</b> ₹{total_expense:,.2f}"
    )
    return _wrap(title, body, emoji="🏪")


def format_recent_transaction(transaction) -> str:
    body = (
        f"🏪 <b>Merchant:</b> {transaction.merchant}\n"
        f"💵 <b>Amount:</b> ₹{transaction.amount}\n"
        f"🏷️ <b>Category:</b> {transaction.category}\n"
        f"🔄 <b>Type:</b> {transaction.transaction_type}\n"
        f"📅 <b>Date:</b> {transaction.transaction_date}"
    )
    return _wrap("Latest Transaction", body, emoji="🧾")


def format_transaction_added(transaction) -> str:
    body = (
        f"🏪 <b>Merchant:</b> {transaction.merchant}\n"
        f"💵 <b>Amount:</b> ₹{transaction.amount}\n"
        f"🏷️ <b>Category:</b> {transaction.category}\n"
        f"🔄 <b>Type:</b> {transaction.transaction_type}"
    )
    return _wrap("Transaction Added", body, emoji="✅")


def format_no_transactions() -> str:
    return _wrap(
        "No Transactions",
        "We couldn't find any transactions yet. 🤷",
        emoji="🧾",
    )


def format_unknown_command(command: str) -> str:
    body = (
        f"<code>{command}</code> isn't a command I recognize.\n\n"
        "Try /start to see what's available."
    )
    return _wrap("Unknown Command", body, emoji="❓")


def format_could_not_understand() -> str:
    body = (
        "I couldn't figure out what you meant. Try something like:\n\n"
        "• <i>\"spent 200 on coffee\"</i>\n"
        "• <i>\"how much did I spend on groceries?\"</i>\n"
        "• <i>\"show me my Swiggy spending\"</i>\n\n"
        "Or use /start to see the available commands."
    )
    return _wrap("Didn't Quite Catch That", body, emoji="🤔")


def format_error() -> str:
    return _wrap(
        "Something Went Wrong",
        "There was a problem processing that request. Please try again.",
        emoji="⚠️",
    )


# ----------------------------------------------------------------------
# Slash command handling
# ----------------------------------------------------------------------

async def handle_command(command: str, db: Session) -> str:
    command = command.strip().lower()

    if command == "/start":
        return format_welcome()

    if command == "/summary":
        try:
            summary = await summarize_transactions_for_last_month(db)
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
            print("Fetching most recent transaction")
            transaction = await get_latest_transaction(db)
            if not transaction:
                return format_no_transactions()
            return format_recent_transaction(transaction)

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