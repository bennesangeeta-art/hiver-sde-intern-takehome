import pandas as pd
from pathlib import Path

# ---------------------------------------------------------
# Phase 0: AmazonHelp brand analysis
# ---------------------------------------------------------

DATA_FILE = Path("data/raw/twcs/twcs.csv")
PROCESSED_DIR = Path("data/processed")

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

print("Reading dataset...")
print("This may take a few minutes because the file is large.")

# Read only the columns we need
columns = [
    "tweet_id",
    "author_id",
    "inbound",
    "created_at",
    "text",
    "response_tweet_id",
    "in_response_to_tweet_id",
]

df = pd.read_csv(DATA_FILE, usecols=columns)

print("\nDataset loaded successfully.")
print("Total tweets:", len(df))

# ---------------------------------------------------------
# AmazonHelp analysis
# ---------------------------------------------------------

amazon_support = df[df["author_id"] == "AmazonHelp"].copy()

# Find customer tweets whose response points to AmazonHelp
amazon_support_ids = set(
    amazon_support["tweet_id"].astype(str)
)

customer_tweets = df[df["inbound"] == True].copy()

def linked_to_amazon(response_ids):
    if pd.isna(response_ids):
        return False

    ids = str(response_ids).split(",")

    return any(tweet_id in amazon_support_ids for tweet_id in ids)


amazon_customers = customer_tweets[
    customer_tweets["response_tweet_id"].apply(linked_to_amazon)
].copy()

# ---------------------------------------------------------
# Print statistics
# ---------------------------------------------------------

print("\n========== AMAZONHELP STATISTICS ==========")

print("AmazonHelp support tweets:", len(amazon_support))

print(
    "Customer tweets connected to AmazonHelp:",
    len(amazon_customers)
)

print(
    "Total AmazonHelp conversation tweets:",
    len(amazon_support) + len(amazon_customers)
)

print("\nCustomer percentage of connected conversations:")

if len(amazon_support) + len(amazon_customers) > 0:
    percentage = (
        len(amazon_customers)
        / (len(amazon_support) + len(amazon_customers))
        * 100
    )

    print(f"{percentage:.2f}%")

# ---------------------------------------------------------
# Save useful customer sample
# ---------------------------------------------------------

sample_size = min(5000, len(amazon_customers))

sample = amazon_customers.sample(
    n=sample_size,
    random_state=42
)

sample_file = PROCESSED_DIR / "amazonhelp_customer_sample.csv"

sample.to_csv(
    sample_file,
    index=False
)

print("\nSaved customer sample:")
print(sample_file)

# ---------------------------------------------------------
# Save brand statistics
# ---------------------------------------------------------

brand_statistics = pd.DataFrame(
    {
        "brand": ["AmazonHelp"],
        "support_tweets": [len(amazon_support)],
        "connected_customer_tweets": [len(amazon_customers)],
        "total_conversation_tweets": [
            len(amazon_support) + len(amazon_customers)
        ],
    }
)

statistics_file = PROCESSED_DIR / "brand_statistics.csv"

brand_statistics.to_csv(
    statistics_file,
    index=False
)

print("\nSaved brand statistics:")
print(statistics_file)

# ---------------------------------------------------------
# Show examples
# ---------------------------------------------------------

print("\n========== SAMPLE CUSTOMER MESSAGES ==========")

for _, row in amazon_customers.head(10).iterrows():
    print("\nTweet ID:", row["tweet_id"])
    print("Customer:", row["author_id"])
    print("Message:", row["text"])

print("\n========== PHASE 0 COMPLETE ==========")