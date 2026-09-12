import pandas as pd
from pathlib import Path

INPUT_FILE = Path("reports/generated/judge_template.csv")
OUTPUT_FILE = Path("reports/generated/human_review.csv")

# Examples 7-50 = exactly 44 scores
scores = [
    (1, 1, 1, 2, 1, 'Reply misunderstands negative feedback and says "Anytime!".'),
    (2, 2, 2, 3, 2, 'Too vague for potentially serious product-registration issue.'),
    (1, 1, 1, 3, 1, 'Incorrectly assures delivery instead of addressing delayed order/complaint.'),
    (3, 3, 3, 4, 3, 'Relevant shipping question but does not directly solve tracking issue.'),
    (1, 1, 1, 4, 1, 'Completely unrelated to delivery complaint.'),
    (4, 4, 4, 4, 4, 'Appropriately acknowledges possible scam and escalates concern.'),
    (1, 1, 1, 3, 1, 'Unrelated to third-party authentication problem.'),
    (4, 4, 4, 4, 4, 'Correctly recognizes Prime-related problem and asks clarification.'),
    (2, 2, 2, 3, 2, 'Discusses packaging generally but does not address damaged replacement/refund.'),
    (2, 2, 2, 4, 2, 'About Prime services but does not answer whether existing HBO subscription can be used.'),
    (2, 2, 2, 4, 2, 'Offers support but does not address multiple delivery failures specifically.'),
    (2, 2, 2, 3, 2, 'Refers to update instead of directly addressing €760 refund.'),
    (4, 4, 4, 4, 4, 'Acknowledges complaint and promises follow-up.'),
    (3, 3, 3, 4, 3, 'Asks whether issue was reported but gives little direct assistance.'),
    (1, 1, 1, 3, 1, 'About seller shipping rather than packaging-waste complaint.'),
    (3, 3, 3, 4, 3, 'Provides follow-up process but does not address suggestion.'),
    (3, 3, 3, 4, 3, 'Friendly but does not clearly respond to positive comment.'),
    (4, 3, 4, 4, 4, 'Invites explanation; appropriate but generic.'),
    (5, 4, 5, 5, 5, 'Confirms receipt and provides appropriate follow-up.'),
    (4, 4, 4, 4, 4, 'Directs to appropriate customer service for account/payment verification.'),
    (4, 4, 4, 4, 4, 'Acknowledges repeated problem and provides support channel.'),
    (3, 3, 3, 4, 3, 'Offers support but does not identify or resolve unclear complaint.'),
    (2, 3, 2, 4, 2, 'Asks unrelated question instead of addressing delivery situation.'),
    (4, 4, 4, 4, 4, 'Apologizes and directs to correspondence.'),
    (3, 3, 3, 4, 3, 'Polite but does not meaningfully address feedback.'),
    (1, 1, 1, 3, 1, 'Incorrectly discusses return instead of missing response.'),
    (2, 2, 2, 4, 2, 'Asks about contacting seller but does not fit message.'),
    (4, 4, 4, 4, 4, 'Asks carrier, relevant to locating delivery.'),
    (4, 4, 4, 4, 4, 'Carrier question is relevant though it does not resolve delay.'),
    (2, 2, 2, 4, 2, 'Feedback link does not address package delivered to wrong location.'),
    (4, 4, 4, 4, 4, 'Acknowledges delivery problem and provides support route.'),
    (2, 2, 2, 4, 2, 'Flex app suggestion does not clearly address missing order history/camera issue.'),
    (3, 3, 3, 4, 3, 'Asks details; reasonable but not specific to defective powerbank.'),
    (5, 5, 5, 5, 5, 'Appropriate friendly response to gratitude.'),
    (3, 3, 3, 4, 3, 'Asks details/offers assistance but does not address specific complaint.'),
    (1, 1, 1, 2, 1, 'Completely unrelated to Prime complaint.'),
    (5, 5, 5, 5, 5, 'Polite and appropriate to positive feedback.'),
    (3, 3, 3, 4, 3, 'Friendly but does not provide requested deal link.'),
    (1, 1, 1, 3, 1, 'Ignores EMI/device problems and focuses on delivery.'),
    (3, 3, 3, 4, 3, 'Related to contest but gives potentially stale specific announcement date.'),
    (3, 3, 3, 4, 3, 'Asks for more information but does not directly address cancellation/refund.'),
    (1, 1, 1, 3, 1, 'Completely unrelated to positive delivery feedback.'),
    (1, 1, 1, 3, 1, 'Discusses Kindle sorting instead of Fire HD performance.'),
    (1, 1, 1, 3, 1, 'Does not address piracy/seller violation issue.')
]


def main():

    print("=" * 70)
    print("HUMAN REVIEW")
    print("=" * 70)

    template = pd.read_csv(INPUT_FILE, dtype=str).fillna("")

    print(f"Template rows: {len(template)}")
    print(f"Prepared scores: {len(scores)}")

    if len(template) != 50:
        raise ValueError(
            f"Expected 50 template rows, found {len(template)}"
        )

    if len(scores) != 44:
        raise ValueError(
            f"Expected 44 scores for Examples 7-50, found {len(scores)}"
        )

    df = template.copy()

    # Example numbers 1-50
    df["example_number"] = range(1, 51)

    # Create review columns as object dtype
    # This prevents pandas string/integer assignment errors.
    review_columns = [
        "human_correctness",
        "human_groundedness",
        "human_helpfulness",
        "human_tone",
        "human_overall",
        "human_reason"
    ]

    for column in review_columns:
        df[column] = pd.Series(
            [None] * len(df),
            dtype="object"
        )

    # Original user-entered ratings for Examples 1-6
    original_scores = [
        (2, 3, 4, 1, 3, ""),
        (5, 5, 5, 5, 5, ""),
        (1, 1, 1, 3, 1,
         "The reply does not answer the customer's Prime Video question."),
        (3, 3, 3, 4, 3, ""),
        (3, 4, 4, 4, 4, ""),
        (4, 3, 4, 4, 4, "")
    ]

    for example_number, score in enumerate(original_scores, start=1):

        index = example_number - 1

        df.at[index, "human_correctness"] = score[0]
        df.at[index, "human_groundedness"] = score[1]
        df.at[index, "human_helpfulness"] = score[2]
        df.at[index, "human_tone"] = score[3]
        df.at[index, "human_overall"] = score[4]
        df.at[index, "human_reason"] = score[5]

    # Scores for Examples 7-50
    for example_number, score in zip(range(7, 51), scores):

        index = example_number - 1

        df.at[index, "human_correctness"] = score[0]
        df.at[index, "human_groundedness"] = score[1]
        df.at[index, "human_helpfulness"] = score[2]
        df.at[index, "human_tone"] = score[3]
        df.at[index, "human_overall"] = score[4]
        df.at[index, "human_reason"] = score[5]

    # Safety checks before saving
    if len(df) != 50:
        raise ValueError(f"Final file should have 50 rows, found {len(df)}")

    if df["example_number"].nunique() != 50:
        raise ValueError("Example numbers are not unique.")

    if df["human_overall"].isna().sum() != 0:
        raise ValueError("Some examples are missing overall scores.")

    # Save
    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)

    print(f"Examples reviewed: {len(df)}")
    print(
        f"Example numbers: "
        f"{int(df['example_number'].min())} to "
        f"{int(df['example_number'].max())}"
    )
    print(f"Missing overall scores: {df['human_overall'].isna().sum()}")
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()