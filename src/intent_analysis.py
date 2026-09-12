import pandas as pd
import re
import os
import random

# Paths
DATA_RAW_DIR = r"C:\Users\benne\OneDrive\Desktop\Hiver SDE Intern Assisment\data\raw\twcs"
TWCS_PATH = os.path.join(DATA_RAW_DIR, "twcs.csv")
PROCESSED_DIR = r"C:\Users\benne\OneDrive\Desktop\Hiver SDE Intern Assisment\data\processed"
REPORTS_DIR = r"C:\Users\benne\OneDrive\Desktop\Hiver SDE Intern Assisment\reports"
OUTPUT_MD = os.path.join(REPORTS_DIR, "intent_analysis.md")

def ensure_directories():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

def load_data():
    print("Loading dataset...")
    df = pd.read_csv(TWCS_PATH, dtype={'tweet_id': str, 'in_response_to_tweet_id': str, 'response_tweet_id': str})
    return df

def get_amazon_customer_tweets(df):
    print("Extracting AmazonHelp customer tweets...")
    amazon_tweets = df[df['author_id'] == 'AmazonHelp']
    responded_to_ids = amazon_tweets['in_response_to_tweet_id'].dropna().unique()
    customer_tweets = df[df['tweet_id'].isin(responded_to_ids)].copy()
    customer_tweets = customer_tweets[customer_tweets['author_id'] != 'AmazonHelp']
    print(f"Found {len(customer_tweets)} customer tweets.")
    return customer_tweets

def normalize_text(text):
    """Lowercase, remove mentions/URLs/punctuation, keep question marks."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'@[a-z0-9_]+', '', text)
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[^a-z0-9\s\?]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def passes_all_checks(clean_text, required_keywords, anti_keywords, extra_validators=None):
    """
    A tweet is accepted only if:
    - It contains at least one required_keyword
    - It contains NONE of the anti_keywords
    - It passes all extra validator functions (each returns True if OK)
    """
    if not any(kw in clean_text for kw in required_keywords):
        return False
    if any(akw in clean_text for akw in anti_keywords):
        return False
    if extra_validators:
        for validator in extra_validators:
            if not validator(clean_text):
                return False
    return True

def sample_valid_examples(pool, required_keywords, anti_keywords, extra_validators=None, n=3, seed=42):
    """Shuffle pool with fixed seed and return first n valid examples."""
    random.seed(seed)
    shuffled = list(pool)
    random.shuffle(shuffled)
    results = []
    for row in shuffled:
        clean = row['clean_text']
        if passes_all_checks(clean, required_keywords, anti_keywords, extra_validators):
            results.append(row['text'].replace('\n', ' ').strip())
            if len(results) >= n:
                break
    return results

def build_taxonomy_and_examples(customer_tweets):
    print("Building taxonomy examples...")
    customer_tweets['clean_text'] = customer_tweets['text'].apply(normalize_text)
    rows = customer_tweets.to_dict('records')

    # ------------------------------------------------------------------ #
    #  Strict validators for problematic intents                          #
    # ------------------------------------------------------------------ #

    def no_question(text):
        """No question marks and no question words."""
        bad = ['?', 'how', 'can you', 'why', 'what', 'where', 'when', 'could you']
        return not any(b in text for b in bad)

    def has_gratitude_word(text):
        """Must contain an explicit gratitude/resolution word."""
        good = ['thank you', 'thanks', 'resolved', 'appreciate', 'all good', 'sorted', 'great help']
        return any(g in text for g in good)

    def no_unresolved_action(text):
        """No indication of an outstanding problem."""
        bad = ['still', 'not yet', 'waiting', 'please', 'need', 'want', 'help', 'order', 'delivery',
               'package', 'refund', 'return', 'issue', 'problem', 'never', 'again', 'terrible',
               'worst', 'buy', 'purchase', 'fitbit', 'iphone', 'compatible']
        return not any(b in text for b in bad)

    def clearly_physical_damage(text):
        """Must mention physical damage clearly, not app/delivery/payment."""
        must_have = ['broken', 'damaged', 'smashed', 'defective', 'torn', 'ruined', 'cracked']
        physical_context = ['received', 'arrived', 'delivered', 'item', 'product', 'box', 'package',
                            'bought', 'ordered', 'kindle', 'tablet', 'device', 'book', 'toy', 'sent']
        has_damage = any(m in text for m in must_have)
        has_physical = any(p in text for p in physical_context)
        return has_damage and has_physical

    def truly_vague(text):
        """Must not contain any identifiable specific issue."""
        specific = ['order', 'delivery', 'package', 'refund', 'return', 'charge', 'prime',
                    'login', 'password', 'mattress', 'late', 'arrived', 'missing', 'damaged',
                    'broken', 'account', 'payment', 'shipping', 'item', 'product', 'not received',
                    'not delivered', 'waiting', 'track', 'cancel', 'gift card', 'gift', 'time',
                    'deliver', '?', 'where', 'how', 'when', 'what', 'why', 'could', 'pick up',
                    'picked up', 'unacceptable', 'if you cannot']
        return not any(s in text for s in specific)

    # ------------------------------------------------------------------ #
    #  Intent definitions                                                 #
    # ------------------------------------------------------------------ #

    taxonomy = {
        "delivery_issue": {
            "definition": "Package never arrived, delivery is late, or there is a tracking problem.",
            "include": "Late packages, missing packages (never arrived), tracking issues for active orders.",
            "exclude": "Do not include if the package arrived but an item was missing from inside it.",
            "required_keywords": ["late", "delayed", "not arrived", "still waiting", "where is my order",
                                   "where is my package", "delivery date", "was supposed to arrive",
                                   "not delivered", "tracking"],
            "anti_keywords": ["broken", "damaged", "missing item"],
            "extra_validators": None,
        },
        "item_damaged": {
            "definition": "The received product is physically damaged, broken, or defective.",
            "include": "Physically damaged products, broken upon arrival, defective hardware.",
            "exclude": "Do not include delivery delays, tracking, cancellations, app issues, or generic complaints.",
            "required_keywords": ["broken", "damaged", "smashed", "ruined", "arrived broken", "torn", "defective"],
            "anti_keywords": ["app", "late", "where", "refund", "payment", "delivery", "tracking",
                               "cancellation", "never arrived", "not arrived", "still waiting", "package delay"],
            "extra_validators": [clearly_physical_damage],
        },
        "item_missing": {
            "definition": "Package arrived but expected contents are missing or the box is empty.",
            "include": "Received package but incomplete contents, empty box arrived.",
            "exclude": "Do not include entire packages that were not delivered (use delivery_issue for that).",
            "required_keywords": ["missing item", "empty box", "not in the box", "didn't receive", "did not receive"],
            "anti_keywords": ["broken", "damaged", "late", "tracking", "where is my order"],
            "extra_validators": None,
        },
        "refund_return": {
            "definition": "Return or refund process for an item.",
            "include": "Requests for refunds, return labels, exchange requests.",
            "exclude": "Do not use if the primary request is about an unauthorized charge (use payment_issue).",
            "required_keywords": ["refund", "return", "send back", "money back", "returning", "exchange"],
            "anti_keywords": ["unauthorized", "hacked", "late", "where"],
            "extra_validators": None,
        },
        "payment_issue": {
            "definition": "Payment/charge/gift-card payment problem.",
            "include": "Double charges, unrecognized charges, declined cards, gift card redemption errors.",
            "exclude": "Do not include simple refunds for returned items (refund_return) or Prime fees (prime_issue).",
            "required_keywords": ["charged twice", "unauthorized charge", "payment declined",
                                   "gift card", "promo code", "overcharged", "card charged"],
            "anti_keywords": ["refund", "return", "prime", "password", "login"],
            "extra_validators": None,
        },
        "account_access": {
            "definition": "Login, password, account lock, hacked account, or access problem.",
            "include": "Genuine login, password resets, suspended accounts, hacked accounts.",
            "exclude": "Do not include COD/payment/order problems.",
            "required_keywords": ["locked out", "password", "can't login", "cannot log in",
                                   "hacked", "blocked", "account closed", "locked my account"],
            "anti_keywords": ["order", "delivery", "payment", "late", "where", "cod",
                               "cash on delivery", "refund", "card", "charge"],
            "extra_validators": None,
        },
        "prime_issue": {
            "definition": "Prime membership, Prime billing, cancellation, or Prime-specific service problems.",
            "include": "Prime billing, cancelling Prime, Prime Video issues.",
            "exclude": "If Prime is mentioned but the real problem is delivery or payment, use that intent instead.",
            "required_keywords": ["prime membership", "prime video", "cancel prime",
                                   "charged for prime", "prime subscription"],
            "anti_keywords": ["delivery", "order", "package", "late", "where"],
            "extra_validators": None,
        },
        "thank_you": {
            "definition": "Genuine gratitude/resolution with NO unresolved support request.",
            "include": "Genuine thanks, confirmation of resolution.",
            "exclude": "Do NOT use if there is any unresolved request, question, or complaint. Sarcastic thanks is NOT thank_you.",
            "required_keywords": ["thank you", "thanks", "resolved", "appreciate it", "all good", "sorted"],
            "anti_keywords": ["but", "help", "where", "still", "not", "issue", "problem",
                               "iphone", "compatible", "how", "what", "can you", "why",
                               "fitbit", "buy", "order", "delivery", "package", "refund",
                               "return", "charge", "prime", "login", "password"],
            "extra_validators": [no_question, has_gratitude_word, no_unresolved_action],
        },
        "general_unclear": {
            "definition": "Truly vague support problem where the actual support issue cannot reasonably be determined.",
            "include": "Genuinely vague complaints or generic requests with no specific actionable detail.",
            "exclude": "If a specific issue is visible (delivery, refund, damage, etc.), do NOT use general_unclear.",
            "required_keywords": ["terrible", "worst customer service", "awful", "horrible service",
                                   "very disappointed", "so disappointed"],
            "anti_keywords": ["order", "delivery", "package", "refund", "return", "charge", "prime",
                               "login", "password", "mattress", "late", "arrived", "missing",
                               "damaged", "broken", "account", "payment", "shipping", "item",
                               "product", "not received", "not delivered", "waiting", "track",
                               "cancel", "gift", "time", "deliver", "where", "how", "when",
                               "what", "why", "could", "pick up", "picked up",
                               "unacceptable", "if you cannot", "on time", "1 out of 3"],
            "extra_validators": [truly_vague],
        },
    }

    # ------------------------------------------------------------------ #
    #  Collect matches for confusing-example detection                   #
    # ------------------------------------------------------------------ #
    tweet_matches = []
    for row in rows:
        clean = row['clean_text']
        matched = [intent for intent, data in taxonomy.items()
                   if any(kw in clean for kw in data['required_keywords'])]
        if len(matched) > 1:
            tweet_matches.append({"text": row['text'], "matches": matched})

    # ------------------------------------------------------------------ #
    #  Build final report data                                            #
    # ------------------------------------------------------------------ #
    report_data = []

    for intent, data in taxonomy.items():
        examples = sample_valid_examples(
            rows,
            required_keywords=data['required_keywords'],
            anti_keywords=data['anti_keywords'],
            extra_validators=data.get('extra_validators'),
            n=3,
            seed=42
        )

        print(f"  {intent}: found {len(examples)} valid examples")

        # Confusing example
        intent_overlaps = [ov for ov in tweet_matches if intent in ov['matches']]
        random.seed(42)
        if intent_overlaps:
            conf_ov = random.choice(intent_overlaps)
            confusing_text = conf_ov['text'].replace('\n', ' ').strip()
            competing = [m for m in conf_ov['matches'] if m != intent]
            other = competing[0]

            # Deterministic decision logic
            if 'thank_you' in conf_ov['matches']:
                winner = [m for m in conf_ov['matches'] if m != 'thank_you'][0]
                reason = (f"Competing: `{', '.join(conf_ov['matches'])}`. "
                          f"Correct intent: `{winner}`. "
                          f"Reason: The message contains 'thanks' but also an unresolved `{winner}` request. "
                          f"An unresolved actionable support request always takes priority over a gratitude keyword.")
            elif 'prime_issue' in conf_ov['matches'] and 'delivery_issue' in conf_ov['matches']:
                winner = 'delivery_issue'
                reason = (f"Competing: `prime_issue` vs `delivery_issue`. "
                          f"Correct intent: `delivery_issue`. "
                          f"Reason: The customer mentions Prime membership, but the actionable problem is a late/missing delivery. "
                          f"We classify based on the primary support problem, not membership status.")
            elif 'refund_return' in conf_ov['matches'] and 'item_damaged' in conf_ov['matches']:
                winner = 'item_damaged'
                reason = (f"Competing: `refund_return` vs `item_damaged`. "
                          f"Correct intent: `item_damaged`. "
                          f"Reason: The refund is requested BECAUSE the item is physically damaged. "
                          f"The root cause (damage) is the primary issue, not the refund mechanism.")
            elif 'general_unclear' in conf_ov['matches']:
                winner = [m for m in conf_ov['matches'] if m != 'general_unclear'][0]
                reason = (f"Competing: `general_unclear` vs `{winner}`. "
                          f"Correct intent: `{winner}`. "
                          f"Reason: Although the message sounds vague, a specific actionable issue (`{winner}`) is identifiable. "
                          f"`general_unclear` is reserved for messages where NO specific issue can be determined.")
            else:
                winner = intent
                reason = (f"Competing: `{intent}` vs `{other}`. "
                          f"Correct intent: `{winner}`. "
                          f"Reason: The customer's primary actionable need is `{intent}`; "
                          f"the `{other}` keyword appears only as context, not as the main issue.")
        else:
            confusing_text = "(No confusing example found in dataset for this intent)"
            reason = "N/A"

        report_data.append({
            "intent": intent,
            "definition": data['definition'],
            "include": data['include'],
            "exclude": data['exclude'],
            "examples": examples,
            "confusing_example": confusing_text,
            "confusing_reason": reason,
        })

    return report_data


def generate_markdown_report(report_data):
    lines = [
        "# Intent Analysis Report: AmazonHelp",
        "",
        "> **Source**: Kaggle `thoughtvector/customer-support-on-twitter` (twcs.csv)",
        "> **Brand**: AmazonHelp",
        "",
        "---",
        "",
        "## Final Labeling Guidelines",
        "",
        "### Important Rules for Human Labelers",
        "",
        "- Label based on the customer's **PRIMARY support need**, not simply keyword presence.",
        "- A keyword match must **NOT** automatically determine the intent.",
        "- If a message contains \"thanks\" but also an unresolved support request, label the **actual support issue** — not `thank_you`.",
        "- Sarcastic \"thanks\" is **NOT** `thank_you`.",
        "- `thank_you` = primary purpose is gratitude/resolution with **zero** unresolved requests.",
        "- `general_unclear` = only when the customer's actual problem **cannot reasonably be determined**.",
        "- If a specific issue is visible, **do NOT** use `general_unclear`.",
        "- For multiple competing intents, choose the **primary actionable** issue.",
        "",
        "### Quick Reference: Intent Distinctions",
        "",
        "| Signal | Correct Intent |",
        "|--------|---------------|",
        "| Package never arrived / late / tracking | `delivery_issue` |",
        "| Package arrived, contents missing/empty | `item_missing` |",
        "| Received product is broken/defective | `item_damaged` |",
        "| Wants to return/exchange or asks refund status | `refund_return` |",
        "| Charge/payment/gift-card billing problem | `payment_issue` |",
        "| Cannot log in / password / account locked/hacked | `account_access` |",
        "| Prime membership / Prime billing / Prime Video | `prime_issue` |",
        "| Truly vague — no specific issue determinable | `general_unclear` |",
        "| Pure gratitude / resolved — no open request | `thank_you` |",
        "",
        "---",
        "",
    ]

    for item in report_data:
        intent = item['intent']
        lines.append(f"### `{intent}`")
        lines.append(f"- **Definition**: {item['definition']}")
        lines.append(f"- **Include**: {item['include']}")
        lines.append(f"- **Exclude**: {item['exclude']}")
        lines.append("")
        lines.append("**3 Real Examples from AmazonHelp dataset:**")
        if not item['examples']:
            lines.append("> *(No valid examples found after strict filtering — manual review needed)*")
        for ex in item['examples']:
            lines.append(f"> {ex}")
        lines.append("")
        lines.append("**Confusing Example and Correct Decision:**")
        lines.append(f"> {item['confusing_example']}")
        lines.append("")
        lines.append(f"- {item['confusing_reason']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print(f"\nReport saved to {OUTPUT_MD}")


def main():
    ensure_directories()
    df = load_data()
    customer_tweets = get_amazon_customer_tweets(df)
    report_data = build_taxonomy_and_examples(customer_tweets)
    generate_markdown_report(report_data)


if __name__ == "__main__":
    main()
