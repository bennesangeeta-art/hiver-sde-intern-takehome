import pandas as pd
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "generated"
    / "reply_evaluation.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "generated"
    / "failure_analysis.csv"
)


def main():

    print("=" * 70)
    print("TOP FAILURE ANALYSIS")
    print("=" * 70)

    df = pd.read_csv(INPUT_FILE)

    print(
        f"\nExamples loaded: {len(df)}"
    )

    # --------------------------------------------------
    # FAILURE TYPE 1:
    # WRONG INTENT
    # --------------------------------------------------

    wrong_intent = df[
        df["intent_correct"] == False
    ].copy()

    wrong_intent["failure_type"] = (
        "Wrong intent classification"
    )

    # --------------------------------------------------
    # FAILURE TYPE 2:
    # POTENTIALLY UNSAFE / CASE-SPECIFIC REPLY
    # --------------------------------------------------

    grounding = df[
        df["has_grounding_warning"] == True
    ].copy()

    grounding["failure_type"] = (
        "Potentially case-specific or stale information"
    )

    # --------------------------------------------------
    # FAILURE TYPE 3:
    # UNCLEAR INTENT + AUTO HANDLE
    # --------------------------------------------------

    unclear_auto = df[
        (df["gold_intent"] == "general_unclear")
        &
        (df["decision"] == "AUTO_HANDLE")
    ].copy()

    unclear_auto["failure_type"] = (
        "Auto-handled unclear request"
    )

    # --------------------------------------------------
    # FAILURE TYPE 4:
    # MINORITY INTENTS
    # --------------------------------------------------

    minority_intents = [
        "item_missing",
        "item_damaged",
        "account_access",
        "payment_issue"
    ]

    minority = df[
        df["gold_intent"].isin(
            minority_intents
        )
    ].copy()

    minority["failure_type"] = (
        "Minority-intent reliability risk"
    )

    # --------------------------------------------------
    # FAILURE TYPE 5:
    # INTENT CORRECT BUT ESCALATED
    # --------------------------------------------------

    correct_escalated = df[
        (df["intent_correct"] == True)
        &
        (df["decision"] == "ESCALATE")
    ].copy()

    correct_escalated["failure_type"] = (
        "Correct intent but escalated"
    )

    # --------------------------------------------------
    # COMBINE
    # --------------------------------------------------

    frames = [
        wrong_intent,
        grounding,
        unclear_auto,
        minority,
        correct_escalated
    ]

    combined = pd.concat(
        frames,
        ignore_index=True
    )

    # Remove exact duplicate examples
    combined = combined.drop_duplicates(
        subset=[
            "id",
            "failure_type"
        ]
    )

    combined = combined[
        [
            "id",
            "failure_type",
            "gold_intent",
            "predicted_intent",
            "customer_message",
            "reply",
            "decision",
            "decision_reason",
            "grounding_warnings"
        ]
    ]

    combined.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    print("\nFailure counts:")

    print(
        combined["failure_type"]
        .value_counts()
    )

    print("\n" + "=" * 70)
    print("EXAMPLE FAILURES")
    print("=" * 70)

    for failure_type in [
        "Wrong intent classification",
        "Potentially case-specific or stale information",
        "Auto-handled unclear request",
        "Minority-intent reliability risk",
        "Correct intent but escalated"
    ]:

        examples = combined[
            combined["failure_type"]
            == failure_type
        ]

        print(
            f"\n--- {failure_type} ---"
        )

        for _, row in examples.head(3).iterrows():

            print(
                f"\nID: {row['id']}"
            )

            print(
                f"Gold intent: "
                f"{row['gold_intent']}"
            )

            print(
                f"Predicted: "
                f"{row['predicted_intent']}"
            )

            print(
                f"Customer: "
                f"{row['customer_message']}"
            )

            print(
                f"Reply: "
                f"{row['reply']}"
            )

            if str(
                row["grounding_warnings"]
            ) != "":

                print(
                    f"Warning: "
                    f"{row['grounding_warnings']}"
                )

    print("\nSaved to:")
    print(OUTPUT_FILE)

    print("\nFailure analysis completed.")


if __name__ == "__main__":
    main()