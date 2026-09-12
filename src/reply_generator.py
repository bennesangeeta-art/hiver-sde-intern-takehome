from typing import List, Dict
import re


class ReplyGenerator:

    def __init__(self):
        pass

    def _clean_response(self, response: str) -> str:
        """Clean historical Twitter-style responses."""

        reply = str(response).strip()

        # Remove leading Twitter handle.
        if reply.startswith("@"):
            parts = reply.split(" ", 1)

            if len(parts) == 2:
                reply = parts[1]

        # Remove Twitter agent signatures such as ^KS, ^BL, ^CR.
        reply = re.sub(
            r"\s*\^[A-Za-z]{1,4}(?:\s+\d+/\d+)?\s*$",
            "",
            reply
        )

        # Remove URLs.
        reply = re.sub(
            r"https?://\S+",
            "",
            reply
        )

        # Remove common Twitter-style link fragments.
        reply = re.sub(
            r"\bt\.co/\S+",
            "",
            reply
        )

        # Remove specific historical deadlines.
        reply = re.sub(
            r"\b(?:in|within|after)\s+\d+\s+"
            r"(?:hours?|days?|minutes?)\b",
            "",
            reply,
            flags=re.IGNORECASE
        )

        # Replace one common historical delivery phrase
        # with a safer current-status phrase.
        reply = re.sub(
            r"\b(?:please\s+)?let\s+us\s+know\s+"
            r"if\s+you\s+don't\s+receive\s+it\b",
            "Please check your latest delivery status",
            reply,
            flags=re.IGNORECASE
        )

        # Remove extra whitespace.
        reply = " ".join(reply.split())

        # Clean awkward punctuation left after removing content.
        reply = re.sub(
            r"\s+([,.!?])",
            r"\1",
            reply
        )

        return reply.strip()

    def _relevance_score(
        self,
        customer_message: str,
        evidence: Dict
    ) -> float:
        """Estimate whether historical evidence matches the request."""

        message = customer_message.lower()

        historical_customer = str(
            evidence.get("customer_text", "")
        ).lower()

        response = str(
            evidence.get("response_text", "")
        ).lower()

        score = float(
            evidence.get("adjusted_score", 0)
        )

        intent_terms = {

            "delivery_issue": [
                "delivery",
                "delivered",
                "package",
                "parcel",
                "arrived",
                "shipping",
                "tracking",
                "late",
                "shipment"
            ],

            "item_damaged": [
                "damaged",
                "damage",
                "broken",
                "defective",
                "cracked"
            ],

            "item_missing": [
                "missing",
                "empty",
                "not included"
            ],

            "refund_return": [
                "refund",
                "return",
                "returned",
                "money back",
                "reimburse"
            ],

            "payment_issue": [
                "payment",
                "charged",
                "charge",
                "billing",
                "card",
                "paid"
            ],

            "account_access": [
                "login",
                "password",
                "account",
                "hacked",
                "locked",
                "access"
            ],

            "prime_issue": [
                "prime",
                "membership",
                "prime video",
                "amazon music"
            ],

            "thank_you": [
                "thank",
                "thanks",
                "appreciate",
                "grateful"
            ]
        }

        intent = evidence.get(
            "intent",
            ""
        )

        keywords = intent_terms.get(
            intent,
            []
        )

        customer_matches = sum(
            1
            for word in keywords
            if word in historical_customer
        )

        response_matches = sum(
            1
            for word in keywords
            if word in response
        )

        query_matches = sum(
            1
            for word in keywords
            if word in message
        )

        # Reward evidence where the historical
        # customer message matches the issue.
        if (
            query_matches > 0
            and customer_matches > 0
        ):
            score += 0.20

        # Reward responses that contain relevant
        # issue terminology.
        if response_matches > 0:
            score += 0.15

        # Penalize privacy-only responses.
        privacy_terms = [
            "personal information",
            "twitter page is visible",
            "don't provide your order details"
        ]

        if any(
            term in response
            for term in privacy_terms
        ):

            if intent != "account_access":
                score -= 0.25

        return score

    def _is_unsafe_historical_response(
        self,
        response: str
    ) -> bool:
        """
        Identify historical responses that should not be
        copied directly into a current customer reply.
        """

        text = str(response).lower()

        unsafe_patterns = [

            # Old deadlines.
            r"\b\d+\s+hours?\b",
            r"\b\d+\s+days?\b",
            r"\b\d+\s+minutes?\b",

            # Historical URLs.
            r"https?://",
            r"\bt\.co/",

            # Order-specific/private references.
            r"order details",
            r"tracking number",
            r"order number",

            # Potentially case-specific promises.
            r"we'll refund",
            r"we will refund",
            r"refund.*within",
            r"credit.*within",

            # Case-specific delivery wording.
            r"delivery date provided",
            r"confirmation e-mail",
            r"confirmation email"
        ]

        return any(
            re.search(
                pattern,
                text
            )
            for pattern in unsafe_patterns
        )

    def _safe_fallback(
        self,
        customer_message: str,
        intent: str
    ) -> str:
        """
        Produce a conservative response when the historical
        response contains stale or case-specific information.
        """

        if intent == "delivery_issue":

            return (
                "I'm sorry your package hasn't arrived yet. "
                "Please check the latest tracking information, "
                "and contact Amazon support if the issue continues."
            )

        if intent == "item_damaged":

            return (
                "I'm sorry your item arrived damaged. "
                "Please contact Amazon support so they can "
                "help with the next steps."
            )

        if intent == "item_missing":

            return (
                "I'm sorry that an item is missing from your package. "
                "Please contact Amazon support so they can "
                "look into the issue."
            )

        if intent == "refund_return":

            return (
                "I understand you need help with a return or refund. "
                "Please contact Amazon support so they can "
                "review the request."
            )

        if intent == "payment_issue":

            return (
                "I understand there is an issue with your payment "
                "or charge. Please contact Amazon support so they "
                "can securely review the account."
            )

        if intent == "account_access":

            return (
                "I'm sorry you're having trouble accessing your "
                "account. Please contact Amazon support for "
                "secure account assistance."
            )

        if intent == "prime_issue":

            return (
                "I understand you're having an issue with your "
                "Prime service. Please contact Amazon support "
                "so they can review the issue."
            )

        if intent == "thank_you":

            return (
                "You're welcome! We're glad we could help."
            )

        return (
            "Thanks for contacting us. "
            "Please share more details so we can help."
        )

    def generate(
        self,
        customer_message: str,
        evidence: List[Dict]
    ) -> str:

        # No evidence means we should not invent
        # a specific historical resolution.
        if not evidence:

            return (
                "Thanks for contacting us. "
                "Please share more details so we can help."
            )

        # Rank historical responses using both
        # retrieval score and issue relevance.
        ranked = sorted(
            evidence,
            key=lambda item:
                self._relevance_score(
                    customer_message,
                    item
                ),
            reverse=True
        )

        best = ranked[0]

        historical_response = str(
            best.get(
                "response_text",
                ""
            )
        ).strip()

        intent = best.get(
            "intent",
            "general_unclear"
        )

        if not historical_response:

            return self._safe_fallback(
                customer_message,
                intent
            )

        # Do not copy stale or case-specific
        # historical information into the current reply.
        if self._is_unsafe_historical_response(
            historical_response
        ):

            return self._safe_fallback(
                customer_message,
                intent
            )

        reply = self._clean_response(
            historical_response
        )

        if not reply:

            return self._safe_fallback(
                customer_message,
                intent
            )

        return reply


def main():

    generator = ReplyGenerator()

    customer_message = (
        "My package has not arrived yet."
    )

    evidence = [
        {
            "customer_text":
                "@AmazonHelp Yes, has not arrived yet",

            "response_text":
                "@566298 Oh no! Have we missed the delivery "
                "date provided in your confirmation e-mail? "
                "Let us know- we're here to help! ^BL",

            "similarity": 0.5346,

            "adjusted_score": 0.5346,

            "intent": "delivery_issue"
        }
    ]

    reply = generator.generate(
        customer_message,
        evidence
    )

    print("\nCustomer:")
    print(customer_message)

    print("\nGenerated grounded reply:")
    print(reply)


if __name__ == "__main__":
    main()