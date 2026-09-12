import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from src.retrieval import HistoricalRetriever


GOLDEN_PATH = PROJECT_ROOT / "data" / "golden" / "golden_set.csv"
REFERENCE_PATH = PROJECT_ROOT / "data" / "processed" / "amazonhelp_reference_pairs.csv"


def main():

    golden = pd.read_csv(GOLDEN_PATH)

    retriever = HistoricalRetriever(
        reference_path=REFERENCE_PATH,
        top_k=3
    )

    print("\nINSPECTING HIGH-SIMILARITY MATCHES")
    print("=" * 80)

    checked = 0

    for _, row in golden.iterrows():

        matches = retriever.search(
            str(row["text"]),
            exclude_tweet_ids={str(row["tweet_id"])}
        )

        if not matches:
            continue

        top = matches[0]

        if top["similarity"] >= 0.95:

            checked += 1

            print(f"\nGolden ID: {row['id']}")
            print(f"Gold intent: {row['gold_intent']}")
            print(f"Golden tweet ID: {row['tweet_id']}")

            print("\nGolden message:")
            print(row["text"])

            print("\nRetrieved tweet ID:")
            print(top["customer_tweet_id"])

            print(f"Similarity: {top['similarity']}")

            print("\nRetrieved historical message:")
            print(top["customer_text"])

            print("\nHistorical AmazonHelp response:")
            print(top["response_text"])

            print("-" * 80)

            if checked >= 10:
                break

    print(f"\nHigh-similarity examples inspected: {checked}")


if __name__ == "__main__":
    main()