import pandas as pd
from pathlib import Path

RAW_PATH = Path("data/raw/twcs/twcs.csv")
GOLDEN_PATH = Path("data/golden/golden_set.csv")
OUTPUT_PATH = Path("data/processed/amazonhelp_reference_pairs.csv")

BRAND = "AmazonHelp"


def find_root(tweet_id, parent_map):
    """Follow reply links back to the root tweet."""

    current = str(tweet_id)
    visited = set()

    while current in parent_map:

        if current in visited:
            break

        visited.add(current)

        parent = parent_map[current]

        if not parent or parent == "nan":
            break

        if parent not in parent_map:
            break

        current = parent

    return current


def main():

    print("Loading dataset...")

    df = pd.read_csv(
        RAW_PATH,
        usecols=[
            "tweet_id",
            "author_id",
            "inbound",
            "created_at",
            "text",
            "response_tweet_id",
            "in_response_to_tweet_id"
        ],
        dtype={
            "tweet_id": str,
            "author_id": str,
            "response_tweet_id": str,
            "in_response_to_tweet_id": str
        }
    )

    # Clean IDs
    for column in [
        "tweet_id",
        "response_tweet_id",
        "in_response_to_tweet_id"
    ]:
        df[column] = df[column].fillna("").str.strip()

    print(f"Total tweets: {len(df):,}")

    # --------------------------------------------------
    # BUILD CONVERSATION MAP
    # --------------------------------------------------

    print("Building conversation map...")

    parent_map = dict(
        zip(
            df["tweet_id"],
            df["in_response_to_tweet_id"]
        )
    )

    # --------------------------------------------------
    # LOAD GOLDEN SET
    # --------------------------------------------------

    golden = pd.read_csv(
        GOLDEN_PATH,
        dtype={"tweet_id": str}
    )

    golden["tweet_id"] = (
        golden["tweet_id"]
        .astype(str)
        .str.strip()
    )

    print(f"Golden examples: {len(golden)}")

    # Find root conversation for every golden example
    golden_conversations = set(
        golden["tweet_id"].apply(
            lambda x: find_root(x, parent_map)
        )
    )

    print(
        f"Golden conversations to exclude: "
        f"{len(golden_conversations)}"
    )

    # --------------------------------------------------
    # CUSTOMER TWEETS
    # --------------------------------------------------

    customer = df[
        (df["inbound"] == True) &
        (df["text"].notna()) &
        (df["text"].str.strip() != "")
    ].copy()

    print(f"Customer tweets: {len(customer):,}")

    # --------------------------------------------------
    # AMAZONHELP SUPPORT TWEETS
    # --------------------------------------------------

    support = df[
        (df["author_id"] == BRAND) &
        (df["inbound"] == False) &
        (df["text"].notna()) &
        (df["text"].str.strip() != "") &
        (df["in_response_to_tweet_id"] != "")
    ].copy()

    print(
        f"AmazonHelp support replies: "
        f"{len(support):,}"
    )

    # --------------------------------------------------
    # MATCH CUSTOMER → AMAZONHELP RESPONSE
    # --------------------------------------------------

    customer_map = dict(
        zip(
            customer["tweet_id"],
            customer["text"]
        )
    )

    support["customer_tweet_id"] = (
        support["in_response_to_tweet_id"]
    )

    support["customer_text"] = (
        support["customer_tweet_id"].map(customer_map)
    )

    matched = support[
        support["customer_text"].notna()
    ].copy()

    print(
        f"Matched customer/support pairs: "
        f"{len(matched):,}"
    )

    # --------------------------------------------------
    # CALCULATE CONVERSATION ID
    # --------------------------------------------------

    print("Calculating conversation IDs...")

    matched["conversation_id"] = (
        matched["customer_tweet_id"].apply(
            lambda x: find_root(x, parent_map)
        )
    )

    # --------------------------------------------------
    # REMOVE GOLDEN CONVERSATIONS
    # --------------------------------------------------

    before_filter = len(matched)

    matched = matched[
        ~matched["conversation_id"].isin(
            golden_conversations
        )
    ].copy()

    removed = before_filter - len(matched)

    print(
        f"Pairs removed because they belong to "
        f"golden conversations: {removed:,}"
    )

    print(
        f"Pairs remaining after conversation-level "
        f"leakage removal: {len(matched):,}"
    )

    # --------------------------------------------------
    # KEEP REQUIRED COLUMNS
    # --------------------------------------------------

    pairs = matched[
        [
            "customer_tweet_id",
            "customer_text",
            "tweet_id",
            "text",
            "created_at",
            "conversation_id"
        ]
    ].copy()

    pairs = pairs.rename(
        columns={
            "tweet_id": "support_tweet_id",
            "text": "response_text"
        }
    )

    # One response per customer message
    pairs = pairs.drop_duplicates(
        subset=["customer_tweet_id"]
    )

    # --------------------------------------------------
    # SAMPLE 20,000 FOR FAST RETRIEVAL
    # --------------------------------------------------

    if len(pairs) > 20000:

        pairs = pairs.sample(
            n=20000,
            random_state=42
        )

    pairs = pairs.reset_index(drop=True)

    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    pairs.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print()
    print("======================================")
    print("REFERENCE DATASET CREATED")
    print("======================================")

    print(f"Reference pairs: {len(pairs):,}")
    print(f"Unique conversations: {pairs['conversation_id'].nunique():,}")
    print(f"Saved to: {OUTPUT_PATH}")

    if len(pairs) > 0:

        print()
        print("Example")
        print("----------------------------------------")

        row = pairs.iloc[0]

        print("Customer:")
        print(row["customer_text"])

        print("\nAmazonHelp response:")
        print(row["response_text"])

        print("----------------------------------------")


if __name__ == "__main__":
    main()