import pandas as pd
from pathlib import Path


INPUT_FILE = Path("reports/generated/reply_evaluation.csv")
OUTPUT_FILE = Path("reports/generated/judge_template.csv")


def main():
    print("=" * 70)
    print("LLM-AS-JUDGE EVALUATION TEMPLATE")
    print("=" * 70)

    df = pd.read_csv(INPUT_FILE)

    print("Columns found:")
    print(list(df.columns))
    print()

    # Select 50 examples using a fixed seed.
    sample = df.sample(n=50, random_state=42).copy()

    # Add clear evaluation example numbers from 1 to 50.
    sample.insert(0, "example_number", range(1, len(sample) + 1))

    # Keep only columns that actually exist in the evaluation file.
    wanted_columns = [
        "example_number",
        "id",
        "tweet_id",
        "conversation_id",
        "customer_message",
        "gold_intent",
        "predicted_intent",
        "reply",
        "decision",
    ]

    available_columns = [
        column for column in wanted_columns
        if column in sample.columns
    ]

    sample = sample[available_columns].copy()

    # Human / judge scoring fields.
    sample["judge_correctness"] = ""
    sample["judge_groundedness"] = ""
    sample["judge_helpfulness"] = ""
    sample["judge_tone"] = ""
    sample["judge_overall"] = ""
    sample["judge_reason"] = ""

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    sample.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("=" * 70)
    print("RESULT")
    print("=" * 70)

    print(f"Total reply examples available: {len(df)}")
    print(f"Examples selected: {len(sample)}")
    print()
    print("Example numbers: 1 to 50")
    print()
    print("Saved:")
    print(OUTPUT_FILE)
    print()
    print("Scoring scale:")
    print("1 = Poor")
    print("2 = Weak")
    print("3 = Acceptable")
    print("4 = Good")
    print("5 = Excellent")
    print()
    print("No LLM scores have been fabricated.")


if __name__ == "__main__":
    main()