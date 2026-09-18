

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
    Shared renderer for summary rows.
 
    Accepts 3-tuples in either (category, transaction_type, amount) or
    (transaction_type, category, amount) order — different queries return
    them differently, so we detect which field is the type by value
    rather than by position.
 
    Returns (body_text, total_income, total_expense).
    """
    KNOWN_TYPES = {"income", "expense"}
 
    grouped: dict[str, list[tuple[str, float]]] = {}
    total_income = 0.0
    total_expense = 0.0
 
    for first, second, amount in rows:
        if str(first).lower() in KNOWN_TYPES:
            txn_type, group = first, second
        else:
            group, txn_type = first, second
 
        amount = float(amount)
        grouped.setdefault(group, []).append((txn_type, amount))
 
        if txn_type.lower() == "income":
            total_income += amount
        else:
            total_expense += amount
 
    lines = []
    for group, entries in grouped.items():
        lines.append(f"<b>{group}</b>")
        for txn_type, amount in entries:
            icon = "🟢" if txn_type.lower() == "income" else "🔴"
            lines.append(f"  {icon} {txn_type}: ₹{amount:,.2f}")
 
    return "\n".join(lines), total_income, total_expense



# Formatter for recent transactions
def format_recent_transactions(transactions) -> str:
    if not transactions:
        return format_no_transactions()
 
    lines = []
    for i, txn in enumerate(transactions, start=1):
        icon = "🟢" if txn.transaction_type.lower() == "income" else "🔴"
        lines.append(
            f"{i}. {icon} <b>{txn.merchant}</b> — ₹{txn.amount:,.2f}\n"
            f"   🏷️ {txn.category} · 📅 {txn.transaction_date}"
        )
 
    body = "\n\n".join(lines)
    return _wrap(f"Last {len(transactions)} Transactions", body, emoji="🧾")


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

def format_needs_clarification(message: str | None) -> str:
    body = message or "Could you share a bit more detail and resend that?"
    return _wrap("Just Need a Bit More Info", body, emoji="✍️")
