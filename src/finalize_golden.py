from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "golden" / "golden_set.csv"

ALLOWED_INTENTS = {
    "delivery_issue",
    "item_damaged",
    "item_missing",
    "refund_return",
    "payment_issue",
    "account_access",
    "prime_issue",
    "general_unclear",
    "thank_you",
}


def main():
    print("Loading golden set...")

    if not INPUT_FILE.exists():
        print("ERROR: golden_set.csv not found.")
        return

    df = pd.read_csv(INPUT_FILE)

    print(f"Rows loaded: {len(df)}")

    errors = []

    if len(df) != 200:
        errors.append(f"Expected 200 rows, found {len(df)}.")

    if df["id"].duplicated().any():
        errors.append("Duplicate IDs found.")

    missing = (
        df["gold_intent"].isna()
        | (df["gold_intent"].astype(str).str.strip() == "")
    )

    if missing.any():
        errors.append(
            f"Missing gold_intent labels: {missing.sum()}"
        )

    invalid = ~df["gold_intent"].isin(ALLOWED_INTENTS)

    if invalid.any():
        errors.append(
            f"Invalid intent labels: {invalid.sum()}"
        )

    if errors:
        print()
        print("VALIDATION FAILED")

        for error in errors:
            print(f"- {error}")

        return

    print()
    print("VALIDATION PASSED")
    print()
    print("Golden set distribution:")
    print(df["gold_intent"].value_counts())

    print()
    print("No labels were modified.")
    print("Golden set validation completed.")


if __name__ == "__main__":
    main()