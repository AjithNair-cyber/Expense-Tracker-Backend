from datetime import datetime


DIVIDER = "─" * 24

MONTH_NAMES = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
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
            lines.append(
                f"  {icon} {txn_type}: ₹{amount:,.2f}"
            )

    return "\n".join(lines), total_income, total_expense


# ----------------------------------------------------------------------
# Existing formatters
# ----------------------------------------------------------------------

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

    return _wrap(
        f"Last {len(transactions)} Transactions",
        body,
        emoji="🧾",
    )


# Formatter for welcome message
def format_welcome() -> str:
    body = (
        "Track your spending right from Telegram.\n\n"
        "<b>Commands</b>\n"
        "💰 /summary — Monthly spending summary\n"
        "🧾 /recent — Most recent transaction\n\n"
        "Or just message me naturally, e.g. "
        "<i>\"spent 450 on lunch at Truffles\"</i> "
        "or <i>\"how much did I spend at Zomato?\"</i>"
    )

    return _wrap(
        "Welcome to Expense Tracker",
        body,
        emoji="👋",
    )


# Formatter for monthly summary
def format_monthly_summary(
    summary,
    month: int | None = None,
    year: int | None = None,
) -> str:
    title = "Monthly Summary"

    if month:
        title = (
            f"Summary — {MONTH_NAMES[month]} {year}"
            if year
            else f"Summary — {MONTH_NAMES[month]}"
        )

    if not summary:
        return _wrap(
            title,
            "No transactions found for that period. 🎉",
            emoji="📊",
        )

    body, total_income, total_expense = _format_grouped_rows(summary)

    body += (
        f"\n{DIVIDER}\n"
        f"💵 <b>Total Income:</b> ₹{total_income:,.2f}\n"
        f"💸 <b>Total Expense:</b> ₹{total_expense:,.2f}"
    )

    return _wrap(
        title,
        body,
        emoji="📊",
    )


def format_category_summary(category: str, summary) -> str:
    title = f"Category: {category}"

    if not summary:
        return _wrap(
            title,
            f"No transactions found for <b>{category}</b>. 🤷",
            emoji="🏷️",
        )

    body, total_income, total_expense = _format_grouped_rows(summary)

    body += (
        f"\n{DIVIDER}\n"
        f"💵 <b>Total Income:</b> ₹{total_income:,.2f}\n"
        f"💸 <b>Total Expense:</b> ₹{total_expense:,.2f}"
    )

    return _wrap(
        title,
        body,
        emoji="🏷️",
    )


def format_merchant_summary(merchant: str, summary) -> str:
    title = f"Merchant: {merchant}"

    if not summary:
        return _wrap(
            title,
            f"No transactions found for <b>{merchant}</b>. 🤷",
            emoji="🏪",
        )

    body, total_income, total_expense = _format_grouped_rows(summary)

    body += (
        f"\n{DIVIDER}\n"
        f"💵 <b>Total Income:</b> ₹{total_income:,.2f}\n"
        f"💸 <b>Total Expense:</b> ₹{total_expense:,.2f}"
    )

    return _wrap(
        title,
        body,
        emoji="🏪",
    )


def format_recent_transaction(transaction) -> str:
    body = (
        f"🏪 <b>Merchant:</b> {transaction.merchant}\n"
        f"💵 <b>Amount:</b> ₹{transaction.amount}\n"
        f"🏷️ <b>Category:</b> {transaction.category}\n"
        f"🔄 <b>Type:</b> {transaction.transaction_type}\n"
        f"📅 <b>Date:</b> {transaction.transaction_date}"
    )

    return _wrap(
        "Latest Transaction",
        body,
        emoji="🧾",
    )


def format_transaction_added(transaction) -> str:
    body = (
        f"🏪 <b>Merchant:</b> {transaction.merchant}\n"
        f"💵 <b>Amount:</b> ₹{transaction.amount}\n"
        f"🏷️ <b>Category:</b> {transaction.category}\n"
        f"🔄 <b>Type:</b> {transaction.transaction_type}"
    )

    return _wrap(
        "Transaction Added",
        body,
        emoji="✅",
    )


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

    return _wrap(
        "Unknown Command",
        body,
        emoji="❓",
    )


def format_could_not_understand() -> str:
    body = (
        "I couldn't figure out what you meant. Try something like:\n\n"
        "• <i>\"spent 200 on coffee\"</i>\n"
        "• <i>\"how much did I spend on groceries?\"</i>\n"
        "• <i>\"show me my Swiggy spending\"</i>\n\n"
        "Or use /start to see the available commands."
    )

    return _wrap(
        "Didn't Quite Catch That",
        body,
        emoji="🤔",
    )


def format_error() -> str:
    return _wrap(
        "Something Went Wrong",
        "There was a problem processing that request. Please try again.",
        emoji="⚠️",
    )


def format_needs_clarification(message: str | None) -> str:
    body = message or "Could you share a bit more detail and resend that?"

    return _wrap(
        "Just Need a Bit More Info",
        body,
        emoji="✍️",
    )


# ----------------------------------------------------------------------
# New formatters
# ----------------------------------------------------------------------

# Formatter for a single transaction
def format_transaction(transaction) -> str:
    body = (
        f"🏪 <b>Merchant:</b> {transaction.merchant or 'Unknown'}\n"
        f"💵 <b>Amount:</b> ₹{transaction.amount:,.2f}\n"
        f"🏷️ <b>Category:</b> {transaction.category or 'OTHER'}\n"
        f"🔄 <b>Type:</b> {transaction.transaction_type}\n"
        f"📅 <b>Date:</b> {transaction.transaction_date}"
    )

    return _wrap(
        "Transaction",
        body,
        emoji="🧾",
    )


# Formatter for transactions by category
def format_transactions_by_category(
    category: str,
    transactions,
) -> str:
    if not transactions:
        return _wrap(
            f"Category: {category}",
            f"No transactions found for <b>{category}</b>. 🤷",
            emoji="🏷️",
        )

    lines = []

    for i, txn in enumerate(transactions, start=1):
        icon = (
            "🟢"
            if txn.transaction_type.lower() == "income"
            else "🔴"
        )

        lines.append(
            f"{i}. {icon} <b>{txn.merchant or 'Unknown'}</b> — "
            f"₹{txn.amount:,.2f}\n"
            f"   📅 {txn.transaction_date}"
        )

    body = "\n\n".join(lines)

    return _wrap(
        f"{category} Transactions",
        body,
        emoji="🏷️",
    )


# Formatter for transactions by merchant
def format_transactions_by_merchant(
    merchant: str,
    transactions,
) -> str:
    if not transactions:
        return _wrap(
            f"Merchant: {merchant}",
            f"No transactions found for <b>{merchant}</b>. 🤷",
            emoji="🏪",
        )

    lines = []

    for i, txn in enumerate(transactions, start=1):
        icon = (
            "🟢"
            if txn.transaction_type.lower() == "income"
            else "🔴"
        )

        lines.append(
            f"{i}. {icon} <b>{txn.merchant or merchant}</b> — "
            f"₹{txn.amount:,.2f}\n"
            f"   🏷️ {txn.category or 'OTHER'} · "
            f"📅 {txn.transaction_date}"
        )

    body = "\n\n".join(lines)

    return _wrap(
        f"{merchant} Transactions",
        body,
        emoji="🏪",
    )


# Formatter for transactions by type
def format_transactions_by_type(
    transaction_type: str,
    transactions,
) -> str:
    title = (
        "Income Transactions"
        if transaction_type.lower() == "income"
        else "Expense Transactions"
    )

    if not transactions:
        return _wrap(
            title,
            "No transactions found. 🤷",
            emoji="🧾",
        )

    lines = []

    for i, txn in enumerate(transactions, start=1):
        icon = (
            "🟢"
            if txn.transaction_type.lower() == "income"
            else "🔴"
        )

        lines.append(
            f"{i}. {icon} <b>{txn.merchant or 'Unknown'}</b> — "
            f"₹{txn.amount:,.2f}\n"
            f"   🏷️ {txn.category or 'OTHER'} · "
            f"📅 {txn.transaction_date}"
        )

    body = "\n\n".join(lines)

    return _wrap(
        title,
        body,
        emoji="💰",
    )


# Formatter for daily summary
def format_daily_summary(
    summary,
    date: datetime,
) -> str:
    date_text = date.strftime("%d %B %Y")

    if not summary:
        return _wrap(
            f"Summary — {date_text}",
            "No transactions found for that day. 🎉",
            emoji="📅",
        )

    total_income = float(summary.get("total_income", 0))
    total_expense = float(summary.get("total_expense", 0))
    balance = float(summary.get("balance", 0))
    transaction_count = summary.get("transaction_count", 0)

    body = (
        f"💵 <b>Total Income:</b> ₹{total_income:,.2f}\n"
        f"💸 <b>Total Expense:</b> ₹{total_expense:,.2f}\n"
        f"💰 <b>Balance:</b> ₹{balance:,.2f}\n"
        f"🧾 <b>Transactions:</b> {transaction_count}"
    )

    return _wrap(
        f"Summary — {date_text}",
        body,
        emoji="📅",
    )


# Formatter for yearly summary
def format_yearly_summary(
    summary,
    year: int,
) -> str:
    if not summary:
        return _wrap(
            f"Summary — {year}",
            "No transactions found for that year. 🎉",
            emoji="📊",
        )

    total_income = float(summary.get("total_income", 0))
    total_expense = float(summary.get("total_expense", 0))
    balance = float(summary.get("balance", 0))
    transaction_count = summary.get("transaction_count", 0)

    body = (
        f"💵 <b>Total Income:</b> ₹{total_income:,.2f}\n"
        f"💸 <b>Total Expense:</b> ₹{total_expense:,.2f}\n"
        f"💰 <b>Balance:</b> ₹{balance:,.2f}\n"
        f"🧾 <b>Transactions:</b> {transaction_count}"
    )

    return _wrap(
        f"Summary — {year}",
        body,
        emoji="📊",
    )


# Formatter for largest transactions
def format_largest_transactions(transactions) -> str:
    if not transactions:
        return format_no_transactions()

    lines = []

    for i, txn in enumerate(transactions, start=1):
        icon = (
            "🟢"
            if txn.transaction_type.lower() == "income"
            else "🔴"
        )

        lines.append(
            f"{i}. {icon} <b>{txn.merchant or 'Unknown'}</b> — "
            f"₹{txn.amount:,.2f}\n"
            f"   🏷️ {txn.category or 'OTHER'} · "
            f"📅 {txn.transaction_date}"
        )

    body = "\n\n".join(lines)

    return _wrap(
        "Largest Transactions",
        body,
        emoji="💸",
    )


# Formatter for transactions between dates
def format_transactions_between_dates(
    transactions,
    start_date: datetime,
    end_date: datetime,
) -> str:
    if not transactions:
        return _wrap(
            "Transactions",
            "No transactions found for that period. 🤷",
            emoji="📅",
        )

    lines = []

    for i, txn in enumerate(transactions, start=1):
        icon = (
            "🟢"
            if txn.transaction_type.lower() == "income"
            else "🔴"
        )

        lines.append(
            f"{i}. {icon} <b>{txn.merchant or 'Unknown'}</b> — "
            f"₹{txn.amount:,.2f}\n"
            f"   🏷️ {txn.category or 'OTHER'} · "
            f"📅 {txn.transaction_date}"
        )

    body = "\n\n".join(lines)

    return _wrap(
        f"{start_date.strftime('%d %b')} → "
        f"{end_date.strftime('%d %b')}",
        body,
        emoji="📅",
    )


# Formatter for transaction count
def format_transaction_count(
    count: int,
    title: str = "Transactions",
) -> str:
    body = f"🧾 <b>Total:</b> {count}"

    return _wrap(
        title,
        body,
        emoji="🔢",
    )


# Formatter for duplicate transaction warning
def format_duplicate_transaction(transaction) -> str:
    body = (
        "A similar transaction already exists:\n\n"
        f"🏪 <b>Merchant:</b> "
        f"{transaction.merchant or 'Unknown'}\n"
        f"💵 <b>Amount:</b> ₹{transaction.amount:,.2f}\n"
        f"🏷️ <b>Category:</b> "
        f"{transaction.category or 'OTHER'}\n"
        f"🔄 <b>Type:</b> {transaction.transaction_type}\n"
        f"📅 <b>Date:</b> {transaction.transaction_date}\n\n"
        "I didn't add a duplicate transaction. 🔒"
    )

    return _wrap(
        "Possible Duplicate",
        body,
        emoji="⚠️",
    )