import json
import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


ALLOWED_INTENTS = [
    "delivery_issue",
    "item_damaged",
    "item_missing",
    "refund_return",
    "payment_issue",
    "account_access",
    "prime_issue",
    "general_unclear",
    "thank_you",
]


def keyword_fallback(text):
    """
    Simple offline fallback classifier.
    Used when the LLM is unavailable.
    """

    text_lower = text.lower()

    if any(word in text_lower for word in [
        "refund",
        "return",
        "returning",
        "money back"
    ]):
        return "refund_return"

    if any(word in text_lower for word in [
        "damaged",
        "broken",
        "defective",
        "cracked"
    ]):
        return "item_damaged"

    if any(word in text_lower for word in [
        "missing",
        "empty package",
        "item missing"
    ]):
        return "item_missing"

    if any(word in text_lower for word in [
        "charged twice",
        "payment",
        "charged",
        "billing",
        "gift card"
    ]):
        return "payment_issue"

    if any(word in text_lower for word in [
        "password",
        "login",
        "log in",
        "hacked",
        "account locked"
    ]):
        return "account_access"

    if any(word in text_lower for word in [
        "prime video",
        "prime membership",
        "prime subscription"
    ]):
        return "prime_issue"

    if any(word in text_lower for word in [
        "not arrived",
        "late",
        "delivery",
        "package",
        "parcel",
        "tracking",
        "shipped"
    ]):
        return "delivery_issue"

    if any(word in text_lower for word in [
        "thank you",
        "thanks",
        "thank u"
    ]):
        return "thank_you"

    return "general_unclear"


class AIClassifier:

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL")

        self.model = model

        if api_key and model:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None

    def classify(self, text):

        # Offline fallback
        if self.client is None:
            intent = keyword_fallback(text)

            return {
                "intent": intent,
                "confidence": 0.50,
                "reason": "LLM unavailable; used keyword fallback.",
                "method": "keyword_fallback"
            }

        prompt = f"""
You are a customer support intent classifier.

Classify the customer message into exactly ONE of these intents:

{json.dumps(ALLOWED_INTENTS)}

Intent definitions:

delivery_issue:
Package has not arrived, is late, delivery/tracking problem.

item_damaged:
Customer received a physically damaged or defective product.

item_missing:
Customer received a package but an item/content is missing.

refund_return:
Customer wants to return an item or asks about refund/return.

payment_issue:
Payment, charge, billing, or gift-card payment problem.

account_access:
Login, password, locked, hacked, or account-access problem.

prime_issue:
Prime membership, Prime subscription, or Prime Video issue.

general_unclear:
Message is vague, outside the defined categories, or cannot be confidently classified.

thank_you:
Genuine gratitude/resolution message with no unresolved support request.

Customer message:
{text}

Return ONLY valid JSON in this format:

{{
  "intent": "one_allowed_intent",
  "confidence": 0.0,
  "reason": "short explanation"
}}
"""

        try:
            response = self.client.responses.create(
                model=self.model,
                input=prompt
            )

            raw = response.output_text.strip()

            result = json.loads(raw)

            intent = result.get("intent")

            if intent not in ALLOWED_INTENTS:
                raise ValueError("Invalid intent returned by model")

            confidence = float(result.get("confidence", 0.5))

            confidence = max(0.0, min(1.0, confidence))

            return {
                "intent": intent,
                "confidence": confidence,
                "reason": result.get(
                    "reason",
                    "LLM classification"
                ),
                "method": "llm"
            }

        except Exception as error:

            intent = keyword_fallback(text)

            return {
                "intent": intent,
                "confidence": 0.50,
                "reason": f"LLM failed; used keyword fallback. Error: {error}",
                "method": "keyword_fallback"
            }


if __name__ == "__main__":

    classifier = AIClassifier()

    test_messages = [
        "My package has not arrived yet.",
        "I want a refund for this order.",
        "My Amazon account has been hacked.",
        "I was charged twice.",
        "Thanks for helping me!"
    ]

    for message in test_messages:

        result = classifier.classify(message)

        print("\nCustomer:")
        print(message)

        print("Result:")
        print(json.dumps(result, indent=2))