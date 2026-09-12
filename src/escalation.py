from typing import Dict


def decide_escalation(
    intent: str,
    customer_message: str,
    evidence: list
) -> Dict:

    text = customer_message.lower()

    # ---------------------------------------------------------
    # 1. Safety-sensitive situations
    # ---------------------------------------------------------

    high_risk_keywords = [
        "hacked",
        "stolen",
        "fraud",
        "scam",
        "unauthorized",
        "security",
        "police",
        "legal",
        "lawsuit"
    ]

    if any(word in text for word in high_risk_keywords):
        return {
            "decision": "ESCALATE",
            "reason": (
                "Potential security, fraud, legal, "
                "or safety issue."
            )
        }

    # ---------------------------------------------------------
    # 2. Account issues need human assistance
    # ---------------------------------------------------------

    if intent == "account_access":
        return {
            "decision": "ESCALATE",
            "reason": (
                "Account access issues may require identity "
                "verification or secure account actions."
            )
        }

    # ---------------------------------------------------------
    # 3. Payment issues need human assistance
    # ---------------------------------------------------------

    if intent == "payment_issue":
        return {
            "decision": "ESCALATE",
            "reason": (
                "Payment-related issues may require secure "
                "account or transaction verification."
            )
        }

    # ---------------------------------------------------------
    # 4. Unclear requests should not be auto-handled
    # ---------------------------------------------------------

    if intent == "general_unclear":
        return {
            "decision": "ESCALATE",
            "reason": (
                "The customer's request is unclear and "
                "cannot be safely resolved automatically."
            )
        }

    # ---------------------------------------------------------
    # 5. No historical evidence
    # ---------------------------------------------------------

    if not evidence:
        return {
            "decision": "ESCALATE",
            "reason": (
                "No sufficiently similar historical "
                "resolution was found."
            )
        }

    # ---------------------------------------------------------
    # 6. Check quality of historical evidence
    # ---------------------------------------------------------

    top_evidence = evidence[0]

    similarity = float(
        top_evidence.get("similarity", 0)
    )

    adjusted_score = float(
        top_evidence.get("adjusted_score", similarity)
    )

    # Conservative threshold.
    # If historical evidence is weak, ask a human to review.
    if similarity < 0.20 or adjusted_score < 0.25:
        return {
            "decision": "ESCALATE",
            "reason": (
                "Historical evidence is not sufficiently "
                "strong for safe automatic handling."
            )
        }

    # ---------------------------------------------------------
    # 7. Auto-handle only when evidence is reasonably strong
    # ---------------------------------------------------------

    return {
        "decision": "AUTO_HANDLE",
        "reason": (
            "The issue matches a known intent and sufficiently "
            "similar historical support evidence is available."
        )
    }


def main():

    examples = [
        {
            "intent": "delivery_issue",
            "message": "My package is late.",
            "evidence": [
                {
                    "response_text": "Let's check your delivery.",
                    "similarity": 0.50,
                    "adjusted_score": 0.70
                }
            ]
        },
        {
            "intent": "account_access",
            "message": "My account was hacked.",
            "evidence": [
                {
                    "response_text": "Please contact support.",
                    "similarity": 0.80,
                    "adjusted_score": 0.90
                }
            ]
        },
        {
            "intent": "general_unclear",
            "message": "I have a problem.",
            "evidence": []
        }
    ]

    for example in examples:

        result = decide_escalation(
            example["intent"],
            example["message"],
            example["evidence"]
        )

        print("\nCustomer:")
        print(example["message"])

        print("Intent:")
        print(example["intent"])

        print("Decision:")
        print(result["decision"])

        print("Reason:")
        print(result["reason"])


if __name__ == "__main__":
    main()