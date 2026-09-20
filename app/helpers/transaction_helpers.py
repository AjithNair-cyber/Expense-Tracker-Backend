import json

# ---------------------------------------------------------------------------
# SYSTEM PROMPT
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """
You are an expense transaction parser.

You receive one message in this format:

SMS: <sms text>
SENDER: <sender id>

Extract transaction information from the SMS.

Rules:

- Identify the transaction amount as a number (remove commas, e.g. "26,035.00" -> 26035.0).
- Identify the merchant or recipient. Normalise the name to clean title case
  (e.g. "SWIGGY FOOD" -> "Swiggy", "PYU*Swiggy" -> "Swiggy"). Remove payment-gateway prefixes such as "PYU*".
  If only a UPI ID is available, use the UPI ID as the merchant.
- Determine whether this is an "expense" (money leaving) or "income" (money received).
- Extract the transaction date if present and return it as YYYY-MM-DD.
  Indian banks write dates day-first (DD/MM/YY, DD-MM-YYYY, DD-Mon-YY, DDMMYYYY).
  Two-digit years are 20YY. If the SMS has no date, return null. Never use today's date.
- Use "INR" when the message indicates Indian Rupees (Rs, Rs., INR).
- Identify the appropriate category based on the merchant or transaction.
- Do not invent information.
- If a field cannot be determined, return null.

Non-transaction messages:

- OTPs, balance alerts, promotional messages, and credit card bill payment acknowledgements
  ("payment received towards your credit card") are NOT transactions.
  The bill payment is already recorded from the bank debit SMS, so recording it again would double count.
  For these, return null for every field.

transaction_mode (one of):

- "upi": message mentions UPI, a VPA, or a UPI handle (e.g. @okaxis, @okhdfcbank).
- "card": a debit or credit card spend.
- "netbanking": NetBanking / IMPS / NEFT / RTGS.
- "auto_debit": ACH / NACH / standing instruction debits that are not UPI.
- "wallet": wallet or pay-balance payments (e.g. Amazon Pay balance).
- "other": it is clearly a transaction but the channel is not stated.

bank_name and card_name:

- Bank account transaction (upi, netbanking, auto_debit, or account debit/credit):
  set bank_name to the bank's full name and set card_name to null.
- Card transaction: set card_name to "<Bank name> Card <last 4 digits>" (e.g. "HDFC Bank Card 7018")
  and set bank_name to null.
- Wallet or unknown source: set both to null.
- Take the bank from the SMS text first. Use the SENDER id only as a fallback.
- Use full official bank names, e.g. "HDFC Bank", "HSBC", "Axis Bank", "ICICI Bank", "Central Bank of India"
  (expand abbreviations such as CBoI).

Category rules:

- food: restaurants, cafes, food delivery, fast food, bakeries, snacks
- grocery: supermarkets, grocery stores, vegetables, fruits, household groceries
- shopping: Amazon, Flipkart, clothing, electronics, retail purchases
- transport: Uber, Ola, taxis, metro, buses, parking, auto-rickshaws
- fuel: petrol, diesel, CNG, EV charging, fuel stations
- travel: flights, hotels, trains, travel bookings
- entertainment: movies, games, events, amusement parks
- subscriptions: Netflix, Spotify, YouTube Premium, Google Play, software subscriptions
- utilities: electricity, water, gas, internet, mobile bills and recharges
- healthcare: hospitals, doctors, pharmacies, medical labs
- education: schools, colleges, courses, tuition, educational services
- finance: bank charges, credit card bill payments (e.g. CRED), investments, insurance, EMIs, EMIs payments
- loan:  personal loans, loan payments,
- rent: house rent, office rent, property rent
- government: taxes, government fees, fines, government services
- personal: money transfers to or from individuals, gifts, personal payments
- other: use when the transaction cannot reasonably be classified

Important:

- Categorize based on the actual merchant or recipient, not the bank.
- For example, if an HDFC Bank SMS says a payment was made to Swiggy, the merchant is Swiggy and the category is "food".
- Amazon should generally be categorized as "shopping".
- Uber and Ola should be categorized as "transport".
- Indian Oil, HPCL, BPCL and similar fuel stations should be categorized as "fuel".
- Netflix and Spotify should be categorized as "subscriptions".
- Transfers to or from an individual should generally be categorized as "personal".
- For income, categorize by the source. Money received from an individual is "personal".
- Do not assume a category when there is insufficient information. Use "other".

Study the examples that follow and match their output style exactly.
""".strip()


# ---------------------------------------------------------------------------
# FEW-SHOT EXAMPLES
# Field names below are assumed. Rename them to match TransactionCreate.
# NOTE: sender ids are realistic placeholders; replace with the real ones from your data.
# ---------------------------------------------------------------------------
NULL_TXN = {
    "amount": None, "currency": None, "merchant": None, "transaction_type": None,
    "category": None, "date": None, "transaction_mode": None,
    "bank_name": None, "card_name": None,
}

FEW_SHOT_EXAMPLES = [
    # 1. HDFC credit card spend, Swiggy -> food, card_name set, bank_name null
    {
        "sms": "Spent Rs.1422 On HDFC Bank Card 7018 At SWIGGY FOOD On 2026-09-18:19:26:22.Not You? To Block+Reissue Call 18002586161/SMS BLOCK CC 7018 to 7308080808",
        "sender": "VM-HDFCBK-S",
        "output": {
            "amount": 1422.0, "currency": "INR", "merchant": "Swiggy",
            "transaction_type": "expense", "category": "food", "date": "2026-09-18",
            "transaction_mode": "card", "bank_name": None, "card_name": "HDFC Bank Card 7018",
        },
    },
    # 2. UPI credit from an individual's VPA -> income / personal
    {
        "sms": "Credit Alert!\nRs.5.00 credited to HDFC Bank A/c XX6200 on 17-09-26 from VPA nairajith1507-1@okaxis (UPI 662630120566)",
        "sender": "VM-HDFCBK-S",
        "output": {
            "amount": 5.0, "currency": "INR", "merchant": "nairajith1507-1@okaxis",
            "transaction_type": "income", "category": "personal", "date": "2026-09-17",
            "transaction_mode": "upi", "bank_name": "HDFC Bank", "card_name": None,
        },
    },
    # 3. UPI payment to CRED (credit card bill) -> finance
    {
        "sms": "Sent Rs.345.24\nFrom HDFC Bank A/C *6200\nTo CRED Club\nOn 14/09/26\nRef 662318738653\nNot You?\nCall 18002586161/SMS BLOCK UPI to 7308080808",
        "sender": "VM-HDFCBK-T",
        "output": {
            "amount": 345.24, "currency": "INR", "merchant": "CRED Club",
            "transaction_type": "expense", "category": "finance", "date": "2026-09-14",
            "transaction_mode": "upi", "bank_name": "HDFC Bank", "card_name": None,
        },
    },
    # 4. HSBC UPI credit from a UPI id, DD-Mon-YY date
    {
        "sms": "Your HSBC Acc XXXXXX1006 is credited for INR 11.00 on 18-Sep-26 from ishikakansal2222@okaxis. UPI Ref No 662781960890",
        "sender": "VM-HSBCIN-S",
        "output": {
            "amount": 11.0, "currency": "INR", "merchant": "ishikakansal2222@okaxis",
            "transaction_type": "income", "category": "personal", "date": "2026-09-18",
            "transaction_mode": "upi", "bank_name": "HSBC", "card_name": None,
        },
    },
    # 5. HSBC payment to a named individual -> personal
    {
        "sms": "INR 11.00 is paid from HSBC account XXXXXX1006 to ISHIKA KANSAL on 18-Sep-26 with ref 662786366381. If this is not done by you, call 18002673456 to report.",
        "sender": "VM-HSBCIN-S",
        "output": {
            "amount": 11.0, "currency": "INR", "merchant": "Ishika Kansal",
            "transaction_type": "expense", "category": "personal", "date": "2026-09-18",
            "transaction_mode": "upi", "bank_name": "HSBC", "card_name": None,
        },
    },
    # 6. UPI mandate to Google Play -> subscriptions
    {
        "sms": "UPI Mandate:\nSent Rs.130.00\nfrom HDFC Bank A/c 6200\nTo Google Play\n17/09/26\nRef 168974342606\nNot You? Call 18002586161/SMS BLOCK UPI to 7308080808",
        "sender": "VM-HDFCBK-T",
        "output": {
            "amount": 130.0, "currency": "INR", "merchant": "Google Play",
            "transaction_type": "expense", "category": "subscriptions", "date": "2026-09-17",
            "transaction_mode": "upi", "bank_name": "HDFC Bank", "card_name": None,
        },
    },
    # 7. ACH debit (loan EMI) with comma amount, DD-MON-YY date
    {
        "sms": "UPDATE: INR 26,035.00 debited from HDFC Bank XX6200 on 05-SEP-26. Info: ACH D- HDFC BANK LTD-475210889. Avl bal:INR 52,835.99",
        "sender": "VM-HDFCBK-S",
        "output": {
            "amount": 26035.0, "currency": "INR", "merchant": "HDFC Bank Ltd",
            "transaction_type": "expense", "category": "loan", "date": "2026-09-05",
            "transaction_mode": "auto_debit", "bank_name": "HDFC Bank", "card_name": None,
        },
    },
    # 8. NetBanking payment to HDFC Ltd, NO date in SMS -> date null
    {
        "sms": "Payment Successful! Rs. 100000.00 from A/c **********6200 to HDFC LTD via HDFC Bank NetBanking. Not you?Call 18002586161",
        "sender": "VM-HDFCBK-S",
        "output": {
            "amount": 100000.0, "currency": "INR", "merchant": "HDFC Ltd",
            "transaction_type": "expense", "category": "finance", "date": None,
            "transaction_mode": "netbanking", "bank_name": "HDFC Bank", "card_name": None,
        },
    },
    # 9. Sparse debit: no merchant, no date, channel unknown, bank from abbreviation
    {
        "sms": "A/c 3XXXXX9140 debited by Rs. 88 Total Bal: Rs.  11,473.42 CR Clr Bal: Rs. 11,473.42 CR. -CBoI",
        "sender": "AD-CBOIND-S",
        "output": {
            "amount": 88.0, "currency": "INR", "merchant": None,
            "transaction_type": "expense", "category": "other", "date": None,
            "transaction_mode": "other", "bank_name": "Central Bank of India", "card_name": None,
        },
    },
    # 10. DDMMYYYY date, named payer -> income / personal
    {
        "sms": "A/c XX9140 credited by Rs. 5.00 on 17092026 via UPI from AJITH GOPALAKRISHNAN NAIR via Ref No. 626069287410. -CBoI",
        "sender": "AD-CBOIND-S",
        "output": {
            "amount": 5.0, "currency": "INR", "merchant": "Ajith Gopalakrishnan Nair",
            "transaction_type": "income", "category": "personal", "date": "2026-09-17",
            "transaction_mode": "upi", "bank_name": "Central Bank of India", "card_name": None,
        },
    },
    # 11. Axis card spend, truncated merchant name, DD-MM-YY date
    {
        "sms": "Spent INR 630.36\nAxis Bank Card no. XX6193\n25-12-25 15:57:19 IST\nDISTRICT MO\nAvl Limit: INR 152369.64\nNot you? SMS BLOCK 6193 to 919951860002",
        "sender": "AX-AXISBK-S",
        "output": {
            "amount": 630.36, "currency": "INR", "merchant": "District",
            "transaction_type": "expense", "category": "entertainment", "date": "2025-12-25",
            "transaction_mode": "card", "bank_name": None, "card_name": "Axis Bank Card 6193",
        },
    },
    # 12. Axis card spend, gateway prefix stripped (PYU*Swiggy -> Swiggy)
    {
        "sms": "Spent INR 1060\nAxis Bank Card no. XX6193\n03-04-26 12:19:35 IST\nPYU*Swiggy\nAvl Limit: INR 151139\nNot you? SMS BLOCK 6193 to 919951860002",
        "sender": "AX-AXISBK-S",
        "output": {
            "amount": 1060.0, "currency": "INR", "merchant": "Swiggy",
            "transaction_type": "expense", "category": "food", "date": "2026-04-03",
            "transaction_mode": "card", "bank_name": None, "card_name": "Axis Bank Card 6193",
        },
    },
    # 13. Credit card bill payment received -> not a transaction
    {
        "sms": "Payment of INR 345.24 has been received towards your Axis Bank Credit Card XX4668 on 14-09-26 - Axis Bank",
        "sender": "AX-AXISBK-S",
        "output": NULL_TXN,
    },
    # 14. Wallet payment (Amazon Pay balance), cryptic merchant, no date
    {
        "sms": "Payment of Rs 197.00 using Apay balance is successful at A.in. Updated balance is Rs 3.00. If not u? Pls call 18001200163 - SMS via Pine Labs",
        "sender": "VM-PINELB-S",
        "output": {
            "amount": 197.0, "currency": "INR", "merchant": "Amazon",
            "transaction_type": "expense", "category": "shopping", "date": None,
            "transaction_mode": "wallet", "bank_name": None, "card_name": None,
        },
    },
    # 15. OTP -> not a transaction (even though it contains an amount and merchant)
    {
        "sms": "181087 is One-Time Password for INR 784.00 transaction towards AMAZON using ICICI Bank Credit Card XX9009. OTPs are SECRET. DO NOT disclose",
        "sender": "VM-ICICIB-S",
        "output": NULL_TXN,
    },
    # 16. HSBC credit card bill payment received -> not a transaction
    {
        "sms": "Dear Customer, we have received a payment of INR 4454.98 for credit card ending 8700 on 09-SEP-26. Thank you for using HSBC credit card.",
        "sender": "VM-HSBCIN-S",
        "output": NULL_TXN,
    },
]


# ---------------------------------------------------------------------------
# MESSAGE BUILDER
# ---------------------------------------------------------------------------
def format_message(sms: str, sender: str) -> str:
    """Must match exactly how your production `message` string is built."""
    return f"SMS: {sms}\n SENDER:{sender}"


def build_input(message: str) -> list[dict]:
    """System prompt + few-shot user/assistant pairs + the real message."""
    items = [{"role": "system", "content": SYSTEM_PROMPT}]
    for ex in FEW_SHOT_EXAMPLES:
        items.append({"role": "user", "content": format_message(ex["sms"], ex["sender"])})
        items.append({"role": "assistant", "content": json.dumps(ex["output"])})
    items.append({"role": "user", "content": message})
    return items


# ---------------------------------------------------------------------------
# USAGE
# ---------------------------------------------------------------------------
# If `message` arrives as bytes (b'SMS: ...'), decode it first:
#   if isinstance(message, bytes):
#       message = message.decode("utf-8")
#
# response = client.responses.parse(
#     model=settings.OPENAI_MODEL,
#     input=build_input(message),
#     text_format=TransactionCreate,
# )
#
# Optional sanity check that every example matches your schema:
#   for ex in FEW_SHOT_EXAMPLES:
#       TransactionCreate(**ex["output"])