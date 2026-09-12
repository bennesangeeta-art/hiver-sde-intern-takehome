import pandas as pd
from pathlib import Path

RAW_FILE = Path("data/raw/twcs/twcs.csv")
GOLDEN_FILE = Path("data/golden/golden_set.csv")

print("Loading raw dataset...")

df = pd.read_csv(
    RAW_FILE,
    usecols=["tweet_id", "in_response_to_tweet_id"],
    dtype=str
)

print(f"Tweets loaded: {len(df):,}")

# Create mapping:
# tweet_id -> parent tweet_id
parent_map = dict(
    zip(
        df["tweet_id"].astype(str),
        df["in_response_to_tweet_id"].fillna("").astype(str)
    )
)


def find_root(tweet_id):
    """
    Follow the reply chain backwards until we reach
    the root tweet of the conversation.
    """

    current = str(tweet_id)
    visited = set()

    while current in parent_map:

        # Prevent infinite loops
        if current in visited:
            break

        visited.add(current)

        parent = parent_map[current]

        # No parent = root tweet
        if not parent or parent == "nan":
            break

        # Parent does not exist in dataset
        if parent not in parent_map:
            break

        current = parent

    return current


print("Loading golden set...")

golden = pd.read_csv(GOLDEN_FILE)

print(f"Golden rows: {len(golden)}")

print("Calculating conversation IDs...")

golden["conversation_id"] = (
    golden["tweet_id"]
    .astype(str)
    .apply(find_root)
)

print()
print("======================================")
print("CONVERSATION IDs UPDATED")
print("======================================")
print(f"Rows: {len(golden)}")
print(f"Unique conversations: {golden['conversation_id'].nunique()}")

print()
print("Sample:")
print(
    golden[
        ["id", "tweet_id", "conversation_id", "gold_intent"]
    ].head(10).to_string(index=False)
)

# Save updated golden set
golden.to_csv(
    GOLDEN_FILE,
    index=False,
    encoding="utf-8-sig"
)

print()
print(f"Saved: {GOLDEN_FILE}")