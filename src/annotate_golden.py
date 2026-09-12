"""
src/annotate_golden.py

Phase 4 — Terminal annotation tool for the golden evaluation set.

Usage:
    python src/annotate_golden.py

Features:
- Shows one message at a time
- Displays all 9 intent options
- Saves label immediately after selection
- Allows skipping a difficult example (records 'SKIP')
- Allows moving forward and backward
- Preserves already completed labels
- Shows progress (e.g. 37/200)
- Never overwrites a completed label without explicit confirmation
"""

import pandas as pd
import os
import sys

# ---- Paths ---------------------------------------------------------------
GOLDEN_CSV = r"data\golden\golden_set.csv"

# ---- Locked intents (must match taxonomy exactly) -----------------------
VALID_INTENTS = [
    "delivery_issue",
    "item_damaged",
    "item_missing",
    "refund_return",
    "payment_issue",
    "account_access",
    "prime_issue",
    "general_unclear",
    "thank_you",
]

def load_golden():
    if not os.path.exists(GOLDEN_CSV):
        print(f"ERROR: Golden set not found at {GOLDEN_CSV}")
        print("Run 'python src/create_golden_set.py' first.")
        sys.exit(1)
    df = pd.read_csv(GOLDEN_CSV, dtype={"tweet_id": str})
    # Ensure gold_intent column exists
    if "gold_intent" not in df.columns:
        df["gold_intent"] = ""
    df["gold_intent"] = df["gold_intent"].fillna("")
    return df

def save_golden(df):
    df.to_csv(GOLDEN_CSV, index=False, encoding="utf-8")

def print_header():
    print("\n" + "=" * 70)
    print("  AmazonHelp Golden Set Annotation Tool")
    print("  Taxonomy: LOCKED — 9 intents only")
    print("  Type 'q' to quit and save progress.")
    print("  Type 'b' to go back one example.")
    print("  Type 's' to skip the current example.")
    print("  Type 'g' to jump to a specific example number.")
    print("=" * 70)

def print_intents():
    print("\n  Intent options:")
    for i, intent in enumerate(VALID_INTENTS, start=1):
        print(f"    {i}. {intent}")
    print("    s. SKIP this example")
    print("    b. Go BACK")
    print("    g. Jump to example number")
    print("    q. Quit and save")

def display_example(row, index, total, already_labelled):
    print("\n" + "-" * 70)
    label_indicator = f"[Already labelled: {row['gold_intent']}]" if already_labelled else "[Not yet labelled]"
    print(f"  Example {index + 1} of {total}   {label_indicator}")
    print(f"  Tweet ID   : {row['tweet_id']}")
    print(f"  Created At : {row['created_at']}")
    print(f"\n  Message:\n")
    # Wrap long messages for readability
    text = str(row["text"])
    words = text.split()
    line = "    "
    for word in words:
        if len(line) + len(word) > 72:
            print(line)
            line = "    "
        line += word + " "
    if line.strip():
        print(line)
    print()

def get_labelled_count(df):
    return df[df["gold_intent"].str.strip().ne("") & df["gold_intent"].str.strip().ne("SKIP")].shape[0]

def annotate():
    df = load_golden()
    total = len(df)
    print_header()

    # Start at first unlabelled example
    idx = 0
    for i, row in df.iterrows():
        if row["gold_intent"].strip() == "":
            idx = i
            break
    else:
        idx = 0  # All labelled — start from beginning

    while True:
        row = df.iloc[idx]
        already_labelled = row["gold_intent"].strip() != ""

        display_example(row, idx, total, already_labelled)
        labelled_count = get_labelled_count(df)
        print(f"  Progress: {labelled_count} labelled / {total} total")
        print_intents()

        user_input = input("\n  Your choice: ").strip().lower()

        # --- Quit ---
        if user_input == "q":
            save_golden(df)
            print(f"\nProgress saved. {get_labelled_count(df)} examples labelled.")
            print("Run 'python src/annotate_golden.py' to continue.")
            break

        # --- Go back ---
        if user_input == "b":
            idx = max(0, idx - 1)
            continue

        # --- Skip ---
        if user_input == "s":
            if already_labelled:
                confirm = input(f"  This example already has label '{row['gold_intent']}'. Overwrite with SKIP? (yes/no): ").strip().lower()
                if confirm != "yes":
                    print("  Skipped overwrite. Label preserved.")
                    idx = min(total - 1, idx + 1)
                    continue
            df.at[idx, "gold_intent"] = "SKIP"
            save_golden(df)
            print("  Marked as SKIP.")
            idx = min(total - 1, idx + 1)
            continue

        # --- Jump to specific example ---
        if user_input == "g":
            try:
                target = int(input("  Jump to example number (1-based): ").strip()) - 1
                if 0 <= target < total:
                    idx = target
                else:
                    print(f"  Invalid number. Must be between 1 and {total}.")
            except ValueError:
                print("  Invalid input.")
            continue

        # --- Select intent by number ---
        if user_input.isdigit():
            choice = int(user_input)
            if 1 <= choice <= len(VALID_INTENTS):
                selected_intent = VALID_INTENTS[choice - 1]

                # Warn before overwriting
                if already_labelled and row["gold_intent"] != selected_intent:
                    confirm = input(
                        f"  This example already has label '{row['gold_intent']}'. "
                        f"Overwrite with '{selected_intent}'? (yes/no): "
                    ).strip().lower()
                    if confirm != "yes":
                        print("  Label preserved.")
                        idx = min(total - 1, idx + 1)
                        continue

                df.at[idx, "gold_intent"] = selected_intent
                save_golden(df)
                print(f"  Saved: {selected_intent}")
                idx = min(total - 1, idx + 1)
            else:
                print(f"  Invalid choice. Enter a number between 1 and {len(VALID_INTENTS)}.")
            continue

        # --- Select intent by name ---
        if user_input in VALID_INTENTS:
            if already_labelled and row["gold_intent"] != user_input:
                confirm = input(
                    f"  This example already has label '{row['gold_intent']}'. "
                    f"Overwrite with '{user_input}'? (yes/no): "
                ).strip().lower()
                if confirm != "yes":
                    print("  Label preserved.")
                    idx = min(total - 1, idx + 1)
                    continue
            df.at[idx, "gold_intent"] = user_input
            save_golden(df)
            print(f"  Saved: {user_input}")
            idx = min(total - 1, idx + 1)
            continue

        print("  Unrecognized input. Please enter a number (1-9), 's', 'b', 'g', or 'q'.")

if __name__ == "__main__":
    annotate()
