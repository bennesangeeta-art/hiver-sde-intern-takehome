import pandas as pd
import numpy as np
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


REFERENCE_PATH = Path(
    "data/processed/amazonhelp_reference_pairs.csv"
)


INTENT_KEYWORDS = {

    "delivery_issue": [
        "delivery",
        "delivered",
        "package",
        "parcel",
        "shipment",
        "shipping",
        "tracking",
        "arrive",
        "arrived",
        "late",
        "delivery date"
    ],

    "item_damaged": [
        "damaged",
        "damage",
        "broken",
        "defective",
        "cracked"
    ],

    "item_missing": [
        "missing",
        "empty",
        "nothing inside"
    ],

    "refund_return": [
        "refund",
        "return",
        "returned",
        "money back",
        "reimburse"
    ],

    "payment_issue": [
        "payment",
        "charged",
        "charge",
        "billing",
        "card",
        "gift card"
    ],

    "account_access": [
        "login",
        "password",
        "account",
        "hacked",
        "locked",
        "access"
    ],

    "prime_issue": [
        "prime",
        "membership",
        "prime video",
        "amazon music"
    ],

    "thank_you": [
        "thank",
        "thanks",
        "appreciate",
        "grateful"
    ]
}


def detect_intent(text):

    text = str(text).lower()

    # Check strong/specific intents first.
    # This prevents a word such as "package" from
    # overriding a clearly damaged/refund/payment issue.

    strong_intents = [
        "item_damaged",
        "item_missing",
        "refund_return",
        "payment_issue",
        "account_access",
        "prime_issue",
        "thank_you",
        "delivery_issue"
    ]

    for intent in strong_intents:

        keywords = INTENT_KEYWORDS[intent]

        if any(
            keyword in text
            for keyword in keywords
        ):
            return intent

    return "general_unclear"


def count_keyword_matches(text, keywords):

    text = str(text).lower()

    return sum(
        1
        for keyword in keywords
        if keyword in text
    )


def has_conflicting_intent(text, target_intent):

    """
    Prevent clearly unrelated historical examples
    from being retrieved for the target intent.
    """

    text = str(text).lower()

    conflict_map = {

        "delivery_issue": [
            "damaged",
            "damage",
            "broken",
            "defective",
            "cracked",
            "refund",
            "money back",
            "charged twice",
            "payment problem",
            "hacked",
            "password"
        ],

        "item_damaged": [
            "refund only",
            "charged twice",
            "payment problem",
            "login problem",
            "password"
        ],

        "item_missing": [
            "damaged",
            "broken",
            "refund only",
            "charged twice",
            "login problem"
        ],

        "refund_return": [
            "delivery only",
            "tracking only",
            "package is late",
            "has not arrived",
            "damaged product only"
        ],

        "payment_issue": [
            "package has not arrived",
            "delivery only",
            "tracking only",
            "damaged product only"
        ],

        "account_access": [
            "delivery only",
            "package only",
            "damaged product only"
        ],

        "prime_issue": [
            "delivery only",
            "package only",
            "tracking only"
        ],

        "thank_you": [
            "package has not arrived",
            "refund",
            "damaged",
            "charged",
            "payment",
            "login",
            "hacked"
        ]
    }

    conflicts = conflict_map.get(
        target_intent,
        []
    )

    return any(
        phrase in text
        for phrase in conflicts
    )


class HistoricalRetriever:

    def __init__(
        self,
        reference_path=REFERENCE_PATH,
        top_k=3
    ):

        self.top_k = top_k

        print(
            "Loading historical reference pairs..."
        )

        self.df = pd.read_csv(
            reference_path
        )

        self.df["customer_text"] = (
            self.df["customer_text"]
            .fillna("")
            .astype(str)
        )

        self.df["response_text"] = (
            self.df["response_text"]
            .fillna("")
            .astype(str)
        )

        print(
            f"Reference examples loaded: "
            f"{len(self.df)}"
        )

        self.customer_ids = (
            self.df["customer_tweet_id"]
            .astype(str)
            .to_numpy()
        )

        self.customer_texts = (
            self.df["customer_text"]
            .to_numpy()
        )

        self.response_texts = (
            self.df["response_text"]
            .to_numpy()
        )

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            min_df=2,
            max_features=30000
        )

        self.matrix = (
            self.vectorizer.fit_transform(
                self.customer_texts
            )
        )

        print(
            "TF-IDF index created successfully."
        )

    def search(
        self,
        query,
        exclude_tweet_ids=None,
        exclude_texts=None,
        target_intent=None
    ):

        if exclude_tweet_ids is None:
            exclude_tweet_ids = set()

        if exclude_texts is None:
            exclude_texts = set()

        exclude_tweet_ids = {
            str(x)
            for x in exclude_tweet_ids
        }

        exclude_texts = {
            str(x).strip().lower()
            for x in exclude_texts
        }

        query_vector = (
            self.vectorizer.transform(
                [query]
            )
        )

        similarities = cosine_similarity(
            query_vector,
            self.matrix
        )[0]

        # Inspect many candidates so that filtering
        # does not leave us with too few results.
        candidate_count = min(
            len(similarities),
            max(self.top_k * 100, 300)
        )

        candidate_indices = np.argpartition(
            similarities,
            -candidate_count
        )[-candidate_count:]

        candidate_indices = candidate_indices[
            np.argsort(
                similarities[candidate_indices]
            )[::-1]
        ]

        if target_intent is None:
            target_intent = detect_intent(query)

        keywords = INTENT_KEYWORDS.get(
            target_intent,
            []
        )

        results = []

        privacy_terms = [
            "personal information",
            "twitter page is visible",
            "don't provide your order details"
        ]

        for index in candidate_indices:

            customer_id = (
                self.customer_ids[index]
            )

            customer_text = (
                self.customer_texts[index]
            )

            response_text = (
                self.response_texts[index]
            )

            normalized_text = (
                str(customer_text)
                .strip()
                .lower()
            )

            # -----------------------------------------
            # Leakage protection
            # -----------------------------------------

            if customer_id in exclude_tweet_ids:
                continue

            if normalized_text in exclude_texts:
                continue

            # Never retrieve an identical customer message.
            if normalized_text == str(query).strip().lower():
                continue

            # -----------------------------------------
            # Intent compatibility filtering
            # -----------------------------------------

            if has_conflicting_intent(
                customer_text,
                target_intent
            ):
                continue

            # Privacy-only historical responses are
            # not useful resolution evidence for normal
            # customer-support intents.
            privacy_response = any(
                term in response_text.lower()
                for term in privacy_terms
            )

            if (
                privacy_response
                and target_intent != "account_access"
            ):
                continue

            similarity = float(
                similarities[index]
            )

            customer_keyword_matches = (
                count_keyword_matches(
                    customer_text,
                    keywords
                )
            )

            response_keyword_matches = (
                count_keyword_matches(
                    response_text,
                    keywords
                )
            )

            # -----------------------------------------
            # Adjusted relevance score
            # -----------------------------------------

            adjusted_score = similarity

            # Customer-message intent evidence.
            adjusted_score += min(
                customer_keyword_matches * 0.04,
                0.16
            )

            # Response intent evidence.
            adjusted_score += min(
                response_keyword_matches * 0.10,
                0.30
            )

            # Strongly reward exact target-intent
            # matches in the historical customer message.
            detected_historical_intent = (
                detect_intent(customer_text)
            )

            if (
                target_intent != "general_unclear"
                and detected_historical_intent
                == target_intent
            ):
                adjusted_score += 0.15

            results.append({
                "customer_tweet_id": customer_id,
                "customer_text": customer_text,
                "response_text": response_text,
                "similarity": similarity,
                "intent": target_intent,
                "intent_keyword_matches":
                    customer_keyword_matches,
                "response_keyword_matches":
                    response_keyword_matches,
                "adjusted_score":
                    adjusted_score
            })

            # Important:
            # Only stop AFTER enough valid results
            # have passed the filters.
            if len(results) >= self.top_k:
                break

        results.sort(
            key=lambda x: x["adjusted_score"],
            reverse=True
        )

        return results


def main():

    retriever = HistoricalRetriever(
        top_k=3
    )

    test_message = (
        "My package has not arrived yet "
        "and the delivery date has passed."
    )

    intent = detect_intent(
        test_message
    )

    print("\nTest customer message:")
    print(test_message)

    print("\nDetected intent:")
    print(intent)

    matches = retriever.search(
        test_message,
        target_intent=intent
    )

    print("\nTop historical matches:")
    print("=" * 70)

    for i, match in enumerate(
        matches,
        start=1
    ):

        print(f"\nMatch {i}")

        print(
            f"TF-IDF similarity: "
            f"{match['similarity']:.4f}"
        )

        print(
            f"Customer keyword matches: "
            f"{match['intent_keyword_matches']}"
        )

        print(
            f"Response keyword matches: "
            f"{match['response_keyword_matches']}"
        )

        print(
            f"Adjusted score: "
            f"{match['adjusted_score']:.4f}"
        )

        print("\nCustomer:")
        print(match["customer_text"])

        print("\nAmazonHelp response:")
        print(match["response_text"])

        print("-" * 70)


if __name__ == "__main__":
    main()