import sys
from pathlib import Path

import pandas as pd

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import SupportAgent


GOLDEN_PATH = PROJECT_ROOT / "data" / "golden" / "golden_set.csv"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "generated"
OUTPUT_FILE = OUTPUT_DIR / "reply_evaluation.csv"


def looks_grounded(reply):
    """
    Basic safety check.

    Flags replies containing potentially case-specific
    instructions, URLs, or transactional claims.
    """

    reply_lower = str(reply).lower()

    warning_terms = [
        "36 hours",
        "24 hours",
        "48 hours",
        "refund",
        "refund will",
        "money back",
        "compensation",
        "credit",
        "order number",
        "tracking number",
        "http://",
        "https://",
        "t.co/"
    ]

    warnings = [
        term
        for term in warning_terms
        if term in reply_lower
    ]

    return {
        "grounding_warnings": "; ".join(warnings),
        "has_grounding_warning": len(warnings) > 0
    }


def main():

    print("=" * 70)
    print("REPLY QUALITY EVALUATION")
    print("=" * 70)

    print("\nLoading golden set...")

    golden = pd.read_csv(GOLDEN_PATH)

    golden = golden.dropna(
        subset=["text", "gold_intent"]
    ).copy()

    print(
        f"Golden examples: {len(golden)}"
    )

    print("\nInitializing support agent...")

    agent = SupportAgent()

    results = []

    print("\nProcessing golden examples...")

    for position, row in enumerate(
        golden.iterrows(),
        start=1
    ):

        _, example = row

        customer_message = str(
            example["text"]
        )

        gold_intent = str(
            example["gold_intent"]
        )

        result = agent.handle(
            customer_message
        )

        reply = str(
            result["reply"]
        )

        predicted_intent = str(
            result["intent"]
        )

        decision = str(
            result["decision"]
        )

        reason = str(
            result["reason"]
        )

        grounding = looks_grounded(
            reply
        )

        results.append({

            "id": example["id"],

            "tweet_id": example["tweet_id"],

            "conversation_id":
                example["conversation_id"],

            "customer_message":
                customer_message,

            "gold_intent":
                gold_intent,

            "predicted_intent":
                predicted_intent,

            "intent_correct":
                gold_intent == predicted_intent,

            "reply":
                reply,

            "decision":
                decision,

            "decision_reason":
                reason,

            "grounding_warnings":
                grounding["grounding_warnings"],

            "has_grounding_warning":
                grounding["has_grounding_warning"],

            "evidence_count":
                len(result["evidence"])
        })

        if position % 20 == 0:
            print(
                f"Processed {position}/{len(golden)}"
            )

    results_df = pd.DataFrame(
        results
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    results_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    intent_accuracy = (
        results_df["intent_correct"].mean()
    )

    grounding_warning_rate = (
        results_df["has_grounding_warning"].mean()
    )

    auto_handle_rate = (
        (
            results_df["decision"]
            == "AUTO_HANDLE"
        ).mean()
    )

    escalate_rate = (
        (
            results_df["decision"]
            == "ESCALATE"
        ).mean()
    )

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(
        f"Examples evaluated       : "
        f"{len(results_df)}"
    )

    print(
        f"Intent accuracy           : "
        f"{intent_accuracy:.4f}"
    )

    print(
        f"Replies with warnings    : "
        f"{grounding_warning_rate:.4f}"
    )

    print(
        f"AUTO_HANDLE rate         : "
        f"{auto_handle_rate:.4f}"
    )

    print(
        f"ESCALATE rate            : "
        f"{escalate_rate:.4f}"
    )

    print("\nGrounding warnings:")

    warning_counts = (
        results_df[
            results_df["has_grounding_warning"]
        ]["grounding_warnings"]
        .value_counts()
    )

    if len(warning_counts) == 0:

        print("None")

    else:

        print(warning_counts)

    print("\nExamples with grounding warnings:")

    warning_examples = results_df[
        results_df["has_grounding_warning"]
    ]

    for _, row in warning_examples.head(10).iterrows():

        print("\nID:", row["id"])

        print(
            "Intent:",
            row["gold_intent"]
        )

        print(
            "Customer:",
            row["customer_message"]
        )

        print(
            "Reply:",
            row["reply"]
        )

        print(
            "Warning:",
            row["grounding_warnings"]
        )

    print("\nSaved results to:")

    print(OUTPUT_FILE)

    print("\nReply evaluation completed.")


if __name__ == "__main__":
    main()