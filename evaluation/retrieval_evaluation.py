import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from src.retrieval import HistoricalRetriever


GOLDEN_PATH = PROJECT_ROOT / "data" / "golden" / "golden_set.csv"
REFERENCE_PATH = PROJECT_ROOT / "data" / "processed" / "amazonhelp_reference_pairs.csv"

REPORT_DIR = PROJECT_ROOT / "reports" / "generated"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = REPORT_DIR / "retrieval_evaluation.csv"


INTENT_KEYWORDS = {
    "delivery_issue": [
        "delivery", "delivered", "package", "parcel",
        "arrived", "shipping", "tracking", "late"
    ],

    "item_damaged": [
        "damaged", "broken", "defective", "damage"
    ],

    "item_missing": [
        "missing", "empty", "not included"
    ],

    "refund_return": [
        "refund", "return", "returned", "money back"
    ],

    "payment_issue": [
        "payment", "charged", "charge", "billing",
        "card", "paid"
    ],

    "account_access": [
        "login", "password", "account", "hacked",
        "locked", "access"
    ],

    "prime_issue": [
        "prime", "prime video", "membership", "amazon music"
    ],

    "thank_you": [
        "thank", "thanks", "thank you",
        "appreciate", "grateful"
    ],
}


def detect_intent_from_text(text):

    text = str(text).lower()

    scores = {}

    for intent, keywords in INTENT_KEYWORDS.items():

        score = 0

        for keyword in keywords:

            if keyword in text:
                score += 1

        scores[intent] = score

    best_intent = max(
        scores,
        key=scores.get
    )

    if scores[best_intent] == 0:
        return "general_unclear"

    return best_intent


def main():

    print("Loading golden set...")

    golden = pd.read_csv(
        GOLDEN_PATH
    )

    print(
        f"Golden examples: {len(golden)}"
    )

    print("\nLoading retriever...")

    retriever = HistoricalRetriever(
        reference_path=REFERENCE_PATH,
        top_k=3
    )

    results = []

    print("\nEvaluating retrieval...")
    print("=" * 70)

    for _, row in golden.iterrows():

        tweet_id = str(
            row["tweet_id"]
        )

        text = str(
            row["text"]
        )

        gold_intent = str(
            row["gold_intent"]
        )

        matches = retriever.search(
            text,
            exclude_tweet_ids={tweet_id},
            exclude_texts={text}
        )

        if matches:

            top_match = matches[0]

            top_similarity = (
                top_match["similarity"]
            )

            retrieved_intent = (
                detect_intent_from_text(
                    top_match["customer_text"]
                )
            )

            intent_aligned = (
                retrieved_intent
                == gold_intent
            )

        else:

            top_similarity = 0.0
            retrieved_intent = "none"
            intent_aligned = False

        results.append({

            "id": row["id"],

            "tweet_id": tweet_id,

            "gold_intent": gold_intent,

            "top_similarity":
                top_similarity,

            "retrieved_intent":
                retrieved_intent,

            "intent_aligned":
                intent_aligned,

            "num_matches":
                len(matches)
        })

    result_df = pd.DataFrame(
        results
    )

    retrieval_rate = (
        result_df["num_matches"].gt(0).mean()
    )

    average_similarity = (
        result_df["top_similarity"].mean()
    )

    intent_alignment_rate = (
        result_df["intent_aligned"].mean()
    )

    print("\nRETRIEVAL QUALITY")
    print("=" * 70)

    print(
        f"Retrieval rate: "
        f"{retrieval_rate:.3f}"
    )

    print(
        f"Average top similarity: "
        f"{average_similarity:.3f}"
    )

    print(
        f"Top-1 intent alignment: "
        f"{intent_alignment_rate:.3f}"
    )

    print("\nResults by intent:")
    print("=" * 70)

    by_intent = (
        result_df
        .groupby("gold_intent")
        .agg(
            examples=("gold_intent", "size"),

            avg_similarity=(
                "top_similarity",
                "mean"
            ),

            intent_alignment=(
                "intent_aligned",
                "mean"
            )
        )
        .sort_values(
            "examples",
            ascending=False
        )
    )

    print(by_intent)

    result_df.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    print("\nSaved detailed results to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()