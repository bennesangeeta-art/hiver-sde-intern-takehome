"""
src/validate_golden.py

Phase 4 — Validation script for the golden evaluation set.

Checks:
1. File exists and is readable
2. Exactly 200 rows
3. Required columns present
4. No duplicate tweet_id
5. No duplicate text
6. No empty text
7. All tweet_ids exist in the source dataset
8. All non-blank gold_intent values are valid (one of 9 locked intents or SKIP)
9. Reports labelling progress

Usage:
    python src/validate_golden.py
"""

import pandas as pd
import os
import sys

# ---- Paths ---------------------------------------------------------------
TWCS_PATH = r"data\raw\twcs\twcs.csv"
GOLDEN_CSV = r"data\golden\golden_set.csv"

# ---- Locked intents (must match taxonomy exactly) ------------------------
VALID_INTENTS = {
    "delivery_issue",
    "item_damaged",
    "item_missing",
    "refund_return",
    "payment_issue",
    "account_access",
    "prime_issue",
    "general_unclear",
    "thank_you",
    "SKIP",   # allowed as a skip marker, not a real label
    "",       # blank = not yet labelled
}

REQUIRED_COLUMNS = {"id", "tweet_id", "text", "created_at", "conversation_id", "gold_intent"}
EXPECTED_ROWS = 200

def separator(title=""):
    if title:
        print(f"\n{'-' * 60}")
        print(f"  {title}")
        print(f"{'-' * 60}")
    else:
        print("-" * 60)

def validate():
    errors = []
    warnings = []

    # ---- 1. File exists --------------------------------------------------
    separator("CHECK 1: File exists")
    if not os.path.exists(GOLDEN_CSV):
        print(f"  FAIL: {GOLDEN_CSV} not found.")
        print("  Run: python src/create_golden_set.py")
        sys.exit(1)
    print(f"  OK: {GOLDEN_CSV} found.")

    # ---- 2. Load ---------------------------------------------------------
    separator("CHECK 2: Load CSV")
    try:
        df = pd.read_csv(GOLDEN_CSV, dtype={"tweet_id": str})
        print(f"  OK: Loaded {len(df)} rows.")
    except Exception as e:
        print(f"  FAIL: Could not read CSV: {e}")
        sys.exit(1)

    # ---- 3. Required columns ---------------------------------------------
    separator("CHECK 3: Required columns")
    missing_cols = REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        errors.append(f"Missing columns: {missing_cols}")
        print(f"  FAIL: Missing columns: {missing_cols}")
    else:
        print(f"  OK: All required columns present: {sorted(REQUIRED_COLUMNS)}")

    if missing_cols:
        print("\nCannot continue validation — required columns missing.")
        sys.exit(1)

    # ---- 4. Row count ----------------------------------------------------
    separator("CHECK 4: Row count")
    if len(df) == EXPECTED_ROWS:
        print(f"  OK: Exactly {EXPECTED_ROWS} rows.")
    else:
        errors.append(f"Expected {EXPECTED_ROWS} rows, found {len(df)}.")
        print(f"  FAIL: Expected {EXPECTED_ROWS} rows, found {len(df)}.")

    # ---- 5. Duplicate tweet_id -------------------------------------------
    separator("CHECK 5: Duplicate tweet_id")
    dup_ids = df[df.duplicated(subset=["tweet_id"], keep=False)]
    if dup_ids.empty:
        print("  OK: No duplicate tweet_ids.")
    else:
        errors.append(f"{len(dup_ids)} rows with duplicate tweet_id.")
        print(f"  FAIL: {len(dup_ids)} rows with duplicate tweet_id:")
        print(dup_ids[["id", "tweet_id"]].to_string(index=False))

    # ---- 6. Duplicate text -----------------------------------------------
    separator("CHECK 6: Duplicate text")
    dup_text = df[df.duplicated(subset=["text"], keep=False)]
    if dup_text.empty:
        print("  OK: No duplicate texts.")
    else:
        warnings.append(f"{len(dup_text)} rows with duplicate text (may be identical real tweets).")
        print(f"  WARN: {len(dup_text)} rows with identical text. Review manually.")

    # ---- 7. Empty text ---------------------------------------------------
    separator("CHECK 7: Empty text")
    df["text"] = df["text"].fillna("")
    empty_text = df[df["text"].str.strip() == ""]
    if empty_text.empty:
        print("  OK: No empty text fields.")
    else:
        errors.append(f"{len(empty_text)} rows with empty text.")
        print(f"  FAIL: {len(empty_text)} rows have empty text.")
        print(empty_text[["id", "tweet_id"]].to_string(index=False))

    # ---- 8. Valid gold_intent values -------------------------------------
    separator("CHECK 8: Valid gold_intent values")
    df["gold_intent"] = df["gold_intent"].fillna("")
    invalid_intents = df[~df["gold_intent"].isin(VALID_INTENTS)]
    if invalid_intents.empty:
        print("  OK: All gold_intent values are valid (or blank/SKIP).")
    else:
        errors.append(f"{len(invalid_intents)} rows with invalid gold_intent.")
        print(f"  FAIL: {len(invalid_intents)} rows with invalid gold_intent values:")
        print(invalid_intents[["id", "tweet_id", "gold_intent"]].to_string(index=False))

    # ---- 9. Tweet IDs exist in source data -------------------------------
    separator("CHECK 9: Tweet IDs in source dataset")
    if not os.path.exists(TWCS_PATH):
        warnings.append("Source dataset not found — cannot verify tweet IDs.")
        print(f"  WARN: {TWCS_PATH} not found. Skipping source-ID verification.")
    else:
        print("  Loading source dataset tweet_ids (this may take a moment)...")
        source_ids = pd.read_csv(
            TWCS_PATH,
            usecols=["tweet_id"],
            dtype={"tweet_id": str}
        )["tweet_id"].astype(str)
        source_id_set = set(source_ids)
        golden_ids = set(df["tweet_id"].astype(str))
        missing_from_source = golden_ids - source_id_set
        if not missing_from_source:
            print("  OK: All golden tweet_ids found in source dataset.")
        else:
            errors.append(f"{len(missing_from_source)} tweet_ids not found in source dataset.")
            print(f"  FAIL: {len(missing_from_source)} tweet_ids not in source:")
            for tid in list(missing_from_source)[:10]:
                print(f"    {tid}")

    # ---- 10. Labelling progress ------------------------------------------
    separator("Labelling Progress")
    total = len(df)
    labelled = df[df["gold_intent"].str.strip().isin(VALID_INTENTS - {"", "SKIP"})].shape[0]
    skipped = df[df["gold_intent"].str.strip() == "SKIP"].shape[0]
    unlabelled = df[df["gold_intent"].str.strip() == ""].shape[0]

    print(f"  Total examples  : {total}")
    print(f"  Labelled        : {labelled}")
    print(f"  Skipped         : {skipped}")
    print(f"  Not yet labelled: {unlabelled}")

    if labelled > 0:
        distribution = df[df["gold_intent"].str.strip().isin(VALID_INTENTS - {"", "SKIP"})]["gold_intent"].value_counts()
        print("\n  Intent distribution (labelled examples only):")
        for intent, count in distribution.items():
            bar = "█" * count
            print(f"    {intent:<20} {count:>4}  {bar}")

    # ---- Summary ---------------------------------------------------------
    separator("VALIDATION SUMMARY")
    if errors:
        print(f"  FAILED — {len(errors)} error(s):")
        for e in errors:
            print(f"    ✗ {e}")
    else:
        print("  PASSED — no errors found.")

    if warnings:
        print(f"\n  {len(warnings)} warning(s):")
        for w in warnings:
            print(f"    ⚠ {w}")

    print()
    return len(errors) == 0

if __name__ == "__main__":
    passed = validate()
    sys.exit(0 if passed else 1)
