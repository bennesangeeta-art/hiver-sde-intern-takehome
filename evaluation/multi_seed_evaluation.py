import pandas as pd
import numpy as np

from pathlib import Path
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import accuracy_score, precision_recall_fscore_support


GOLDEN_PATH = Path("data/golden/golden_set.csv")

SEEDS = [42, 123, 456, 789, 2026]


def keyword_classifier(text):
    text = str(text).lower()

    if any(word in text for word in ["refund", "return", "returned"]):
        return "refund_return"

    if any(word in text for word in ["damaged", "broken", "defective", "cracked"]):
        return "item_damaged"

    if any(word in text for word in ["missing", "empty box", "nothing inside"]):
        return "item_missing"

    if any(word in text for word in [
        "payment", "charged", "charge", "card", "gift card"
    ]):
        return "payment_issue"

    if any(word in text for word in [
        "password", "login", "locked", "account hacked"
    ]):
        return "account_access"

    if any(word in text for word in [
        "prime", "prime video", "prime membership"
    ]):
        return "prime_issue"

    if any(word in text for word in [
        "delivery", "delivered", "delivery date", "package",
        "parcel", "shipment", "shipping", "tracking", "arrive"
    ]):
        return "delivery_issue"

    if any(word in text for word in [
        "thank you", "thanks", "thank u", "appreciate"
    ]):
        return "thank_you"

    return "general_unclear"


def evaluate_seed(df, seed):

    X = df["text"].astype(str)
    y = df["gold_intent"].astype(str)
    groups = df["conversation_id"].astype(str)

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.30,
        random_state=seed
    )

    train_indices, test_indices = next(
        splitter.split(X, y, groups=groups)
    )

    X_test = X.iloc[test_indices]
    y_test = y.iloc[test_indices]

    predictions = [
        keyword_classifier(text)
        for text in X_test
    ]

    accuracy = accuracy_score(y_test, predictions)

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test,
        predictions,
        average="macro",
        zero_division=0
    )

    return {
        "seed": seed,
        "test_size": len(y_test),
        "accuracy": accuracy,
        "macro_precision": precision,
        "macro_recall": recall,
        "macro_f1": f1
    }


def main():

    print("Loading golden set...")

    df = pd.read_csv(GOLDEN_PATH)

    df = df.dropna(
        subset=["text", "gold_intent", "conversation_id"]
    )

    print(f"Golden examples: {len(df)}")

    results = []

    print()
    print("=" * 70)
    print("MULTI-SEED KEYWORD BASELINE EVALUATION")
    print("=" * 70)

    for seed in SEEDS:

        result = evaluate_seed(df, seed)

        results.append(result)

        print()
        print(f"Seed: {seed}")
        print(f"Test size       : {result['test_size']}")
        print(f"Accuracy        : {result['accuracy']:.4f}")
        print(f"Macro Precision : {result['macro_precision']:.4f}")
        print(f"Macro Recall    : {result['macro_recall']:.4f}")
        print(f"Macro F1        : {result['macro_f1']:.4f}")

    results_df = pd.DataFrame(results)

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print()
    print(results_df.to_string(index=False))

    print()
    print("Mean Accuracy        :", f"{results_df['accuracy'].mean():.4f}")
    print("Std Accuracy         :", f"{results_df['accuracy'].std():.4f}")

    print("Mean Macro Precision :", f"{results_df['macro_precision'].mean():.4f}")
    print("Mean Macro Recall    :", f"{results_df['macro_recall'].mean():.4f}")
    print("Mean Macro F1        :", f"{results_df['macro_f1'].mean():.4f}")

    print()
    print("Interpretation:")
    print(
        "The results show how sensitive the keyword baseline is "
        "to the choice of conversation-level test split."
    )


if __name__ == "__main__":
    main()