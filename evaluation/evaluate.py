import pandas as pd
import numpy as np
from pathlib import Path

from sklearn.model_selection import GroupShuffleSplit
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix
)

GOLDEN_PATH = Path("data/golden/golden_set.csv")
REPORT_DIR = Path("reports/generated")


def majority_baseline(y_train, y_test):
    majority_class = y_train.value_counts().idxmax()
    predictions = [majority_class] * len(y_test)

    return {
        "name": "Majority Class Baseline",
        "accuracy": accuracy_score(y_test, predictions),
        "predictions": predictions
    }


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


def evaluate_predictions(y_true, predictions, name):
    accuracy = accuracy_score(y_true, predictions)

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true,
        predictions,
        average="macro",
        zero_division=0
    )

    print(f"\n{'=' * 60}")
    print(name)
    print(f"{'=' * 60}")
    print(f"Accuracy : {accuracy:.4f}")
    print(f"Macro Precision : {precision:.4f}")
    print(f"Macro Recall    : {recall:.4f}")
    print(f"Macro F1        : {f1:.4f}")

    print("\nClassification Report:")
    print(
        classification_report(
            y_true,
            predictions,
            zero_division=0
        )
    )

    return {
        "accuracy": accuracy,
        "macro_precision": precision,
        "macro_recall": recall,
        "macro_f1": f1
    }


def main():

    print("Loading golden set...")

    df = pd.read_csv(GOLDEN_PATH)

    print(f"Golden examples: {len(df)}")

    # Remove empty rows
    df = df.dropna(subset=["text", "gold_intent", "conversation_id"])

    X = df["text"].astype(str)
    y = df["gold_intent"].astype(str)
    groups = df["conversation_id"].astype(str)

    print("\nIntent distribution:")
    print(y.value_counts())

    # --------------------------------------------------
    # CONVERSATION-LEVEL TRAIN / TEST SPLIT
    # --------------------------------------------------
    # This prevents examples from the same conversation
    # appearing in both train and test sets.

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.30,
        random_state=42
    )

    train_indices, test_indices = next(
        splitter.split(X, y, groups=groups)
    )

    X_train = X.iloc[train_indices]
    X_test = X.iloc[test_indices]

    y_train = y.iloc[train_indices]
    y_test = y.iloc[test_indices]

    groups_train = groups.iloc[train_indices]
    groups_test = groups.iloc[test_indices]

    print("\nTrain examples:", len(X_train))
    print("Test examples :", len(X_test))

    print("Train conversations:", groups_train.nunique())
    print("Test conversations :", groups_test.nunique())

    # Verify no conversation appears in both sets
    overlap = set(groups_train) & set(groups_test)

    if overlap:
        raise ValueError(
            f"Conversation leakage detected: {len(overlap)} overlapping conversations."
        )

    print("Conversation overlap : 0")
    print("PASS: No conversation leakage.")

    # --------------------------------------------------
    # 1. MAJORITY BASELINE
    # --------------------------------------------------

    majority_result = majority_baseline(y_train, y_test)

    majority_metrics = evaluate_predictions(
        y_test,
        majority_result["predictions"],
        "BASELINE 1 — MAJORITY CLASS"
    )

    # --------------------------------------------------
    # 2. KEYWORD BASELINE
    # --------------------------------------------------

    keyword_predictions = [
        keyword_classifier(text)
        for text in X_test
    ]

    keyword_metrics = evaluate_predictions(
        y_test,
        keyword_predictions,
        "BASELINE 2 — KEYWORD RULES"
    )

    # --------------------------------------------------
    # 3. TF-IDF + LOGISTIC REGRESSION
    # --------------------------------------------------

    print("\nTraining TF-IDF + Logistic Regression...")

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        max_features=10000
    )

    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    model = LogisticRegression(
        max_iter=1000,
        random_state=42
    )

    model.fit(X_train_tfidf, y_train)

    tfidf_predictions = model.predict(X_test_tfidf)

    tfidf_metrics = evaluate_predictions(
        y_test,
        tfidf_predictions,
        "MAIN SIMPLE MODEL — TF-IDF + LOGISTIC REGRESSION"
    )

    # --------------------------------------------------
    # CONFUSION MATRIX
    # --------------------------------------------------

    labels = sorted(y.unique())

    matrix = confusion_matrix(
        y_test,
        tfidf_predictions,
        labels=labels
    )

    confusion_df = pd.DataFrame(
        matrix,
        index=labels,
        columns=labels
    )

    print("\nConfusion Matrix:")
    print(confusion_df)

    # --------------------------------------------------
    # SAVE RESULTS
    # --------------------------------------------------

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    results = {
        "dataset_size": len(df),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "train_conversations": int(groups_train.nunique()),
        "test_conversations": int(groups_test.nunique()),
        "conversation_overlap": len(overlap),
        "split_method": "GroupShuffleSplit by conversation_id",
        "random_state": 42,
        "test_size_fraction": 0.30,
        "majority_baseline": majority_metrics,
        "keyword_baseline": keyword_metrics,
        "tfidf_logistic_regression": tfidf_metrics,
        "intent_distribution": y.value_counts().to_dict(),
        "confusion_matrix": confusion_df.to_dict()
    }

    output_file = REPORT_DIR / "classification_results.json"

    import json

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to:")
    print(output_file)

    print("\nEvaluation completed successfully.")


if __name__ == "__main__":
    main()