import pandas as pd

GOLDEN_FILE = "data/golden/golden_set.csv"

print("Loading golden set...")

df = pd.read_csv(GOLDEN_FILE)

print(f"Rows: {len(df)}")

print()
print("Leakage checks:")

# Check duplicate tweet IDs
duplicate_tweet_ids = df["tweet_id"].duplicated().sum()

# Check duplicate texts
duplicate_texts = df["text"].duplicated().sum()

# Check duplicate conversation IDs
duplicate_conversations = df["conversation_id"].duplicated().sum()

print(f"Duplicate tweet IDs: {duplicate_tweet_ids}")
print(f"Duplicate texts: {duplicate_texts}")
print(f"Duplicate conversation IDs: {duplicate_conversations}")

print()

if duplicate_tweet_ids == 0:
    print("PASS: No duplicate tweet IDs.")
else:
    print("FAIL: Duplicate tweet IDs found.")

if duplicate_texts == 0:
    print("PASS: No duplicate texts.")
else:
    print("FAIL: Duplicate texts found.")

if duplicate_conversations == 0:
    print("PASS: No duplicate conversation IDs.")
else:
    print("WARNING: Multiple golden examples belong to the same conversation.")

print()
print("Conversation IDs are based on the root tweet of each reply chain.")
print("This supports conversation-level leakage checks.")

print()
print("Leakage check completed.")