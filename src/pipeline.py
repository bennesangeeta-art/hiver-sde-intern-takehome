from src.classifier import keyword_fallback
from src.retrieval import HistoricalRetriever
from src.reply_generator import ReplyGenerator
from src.escalation import decide_escalation


class SupportAgent:

    def __init__(self):
        print("Initializing support agent...")

        self.retriever = HistoricalRetriever(
            top_k=3
        )

        self.reply_generator = ReplyGenerator()

        print("Support agent ready.")

    def handle(self, customer_message):
        print("\n" + "=" * 70)
        print("PROCESSING CUSTOMER MESSAGE")
        print("=" * 70)

        print("\nCustomer:")
        print(customer_message)

        # STEP 1: INTENT CLASSIFICATION
        intent = keyword_fallback(
            customer_message
        )

        print("\nDetected intent:")
        print(intent)

        # STEP 2: HISTORICAL RETRIEVAL
        evidence = self.retriever.search(
            customer_message,
            target_intent=intent
        )

        print(
            f"\nHistorical matches found: {len(evidence)}"
        )

        # Add detected intent to each evidence item
        for item in evidence:
            item["intent"] = intent

        # STEP 3: GROUNDED REPLY GENERATION
        reply = self.reply_generator.generate(
            customer_message,
            evidence
        )

        # STEP 4: ESCALATION DECISION
        decision = decide_escalation(
            intent,
            customer_message,
            evidence
        )

        # FINAL RESULT
        print("\nGenerated reply:")
        print(reply)

        print("\nDecision:")
        print(decision["decision"])

        print("\nReason:")
        print(decision["reason"])

        return {
            "customer_message": customer_message,
            "intent": intent,
            "reply": reply,
            "decision": decision["decision"],
            "reason": decision["reason"],
            "evidence": evidence
        }


def main():

    agent = SupportAgent()

    test_messages = [
        "My package has not arrived yet.",
        "I was charged twice for my order.",
        "My Amazon account has been hacked.",
        "I have a problem with my order."
    ]

    for message in test_messages:
        agent.handle(message)


if __name__ == "__main__":
    main()
