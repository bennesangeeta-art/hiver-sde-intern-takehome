import pandas as pd
import os

# Paths
INPUT_FILE = r"data\raw\twcs\twcs.csv"
OUTPUT_DIR = r"data\golden"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "golden_set.csv")

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("Loading dataset...")

# Load only required columns
df = pd.read_csv(
    INPUT_FILE,
    usecols=[
        "tweet_id",
        "author_id",
        "inbound",
        "created_at",
        "text",
        "response_tweet_id",
        "in_response_to_tweet_id"
    ]
)

print(f"Total tweets: {len(df):,}")

# ---------------------------------------------------------
# Identify AmazonHelp support tweets
# ---------------------------------------------------------

amazon_support = df[
    (df["author_id"] == "AmazonHelp") &
    (df["inbound"] == False)
].copy()

print(f"AmazonHelp support tweets: {len(amazon_support):,}")

# Support tweet IDs
support_ids = set(amazon_support["tweet_id"].astype(str))

# ---------------------------------------------------------
# Find customer tweets connected to AmazonHelp
# ---------------------------------------------------------

customer = df[
    (df["inbound"] == True) &
    (df["response_tweet_id"].astype(str).isin(support_ids))
].copy()

print(f"Connected AmazonHelp customer tweets: {len(customer):,}")

# ---------------------------------------------------------
# Create conversation ID
# ---------------------------------------------------------

customer["conversation_id"] = customer["response_tweet_id"].astype(str)

# ---------------------------------------------------------
# Remove empty text
# ---------------------------------------------------------

customer = customer[
    customer["text"].notna() &
    (customer["text"].astype(str).str.strip() != "")
].copy()

# Remove duplicate tweet IDs
customer = customer.drop_duplicates(subset=["tweet_id"])

# Remove duplicate text
customer = customer.drop_duplicates(subset=["text"])

# ---------------------------------------------------------
# Randomly sample 200 real messages
# ---------------------------------------------------------

golden = customer.sample(
    n=200,
    random_state=42
).copy()

# Sort by ID for easier manual labelling
golden = golden.sort_values("tweet_id")

# ---------------------------------------------------------
# Create final columns
# ---------------------------------------------------------

golden["id"] = range(1, len(golden) + 1)

golden["gold_intent"] = ""

golden = golden[
    [
        "id",
        "tweet_id",
        "text",
        "created_at",
        "conversation_id",
        "gold_intent"
    ]
]

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

golden.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print()
print("======================================")
print("GOLDEN SET CREATED")
print("======================================")
print(f"Rows: {len(golden)}")
print(f"File: {OUTPUT_FILE}")
print()
print("First 10 examples:")
print(golden.head(10).to_string(index=False))
print()
print("IMPORTANT:")
print("gold_intent is intentionally blank.")
print("You must manually assign the labels.")