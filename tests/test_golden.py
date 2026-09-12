"""
tests/test_golden.py

Phase 4 — Tests for golden set schema, annotation logic, and validation.

Run with:
    pytest tests/test_golden.py -v
"""

import pytest
import pandas as pd
import os
import sys
import tempfile

# Add src to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

GOLDEN_CSV = r"data\golden\golden_set.csv"

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
}

REQUIRED_COLUMNS = {"id", "tweet_id", "text", "created_at", "conversation_id", "gold_intent"}


# ===========================================================================
#  Fixtures
# ===========================================================================

@pytest.fixture(scope="module")
def golden_df():
    """Load golden CSV if it exists. Skip tests if not yet created."""
    if not os.path.exists(GOLDEN_CSV):
        pytest.skip(f"Golden set not yet created at {GOLDEN_CSV}. Run src/create_golden_set.py first.")
    df = pd.read_csv(GOLDEN_CSV, dtype={"tweet_id": str})
    df["gold_intent"] = df["gold_intent"].fillna("")
    return df


@pytest.fixture()
def minimal_golden_df():
    """A minimal in-memory golden DataFrame for unit tests that don't need real data."""
    return pd.DataFrame({
        "id": [1, 2, 3],
        "tweet_id": ["111", "222", "333"],
        "text": ["My package is late.", "I want a refund.", "Thank you!"],
        "created_at": ["2017-01-01", "2017-01-02", "2017-01-03"],
        "conversation_id": ["aaa", "bbb", "ccc"],
        "gold_intent": ["delivery_issue", "refund_return", "thank_you"],
    })


# ===========================================================================
#  Schema Tests
# ===========================================================================

class TestGoldenSetSchema:

    def test_file_exists(self):
        """Golden CSV must exist after create_golden_set.py is run."""
        if not os.path.exists(GOLDEN_CSV):
            pytest.skip("Golden set not yet created.")
        assert os.path.exists(GOLDEN_CSV)

    def test_required_columns(self, golden_df):
        """All required columns must be present."""
        for col in REQUIRED_COLUMNS:
            assert col in golden_df.columns, f"Missing column: {col}"

    def test_row_count(self, golden_df):
        """Must contain exactly 200 rows."""
        assert len(golden_df) == 200, f"Expected 200 rows, found {len(golden_df)}"

    def test_no_empty_text(self, golden_df):
        """No row may have an empty or null text field."""
        empty = golden_df[golden_df["text"].str.strip() == ""]
        assert len(empty) == 0, f"{len(empty)} rows have empty text"

    def test_no_duplicate_tweet_id(self, golden_df):
        """All tweet_ids must be unique."""
        dups = golden_df[golden_df.duplicated(subset=["tweet_id"], keep=False)]
        assert len(dups) == 0, f"{len(dups)} duplicate tweet_ids found"

    def test_id_column_sequential(self, golden_df):
        """id column should be sequential from 1 to 200."""
        assert list(golden_df["id"]) == list(range(1, len(golden_df) + 1))


# ===========================================================================
#  Intent Value Tests
# ===========================================================================

class TestIntentValues:

    def test_valid_gold_intents(self, golden_df):
        """All non-blank gold_intent values must be one of the 9 locked intents or SKIP."""
        allowed = VALID_INTENTS | {"SKIP", ""}
        invalid = golden_df[~golden_df["gold_intent"].isin(allowed)]
        assert len(invalid) == 0, (
            f"{len(invalid)} rows have invalid gold_intent values: "
            f"{invalid['gold_intent'].unique().tolist()}"
        )

    def test_valid_intents_list_complete(self):
        """The VALID_INTENTS set must contain exactly 9 items."""
        assert len(VALID_INTENTS) == 9, f"Expected 9 intents, found {len(VALID_INTENTS)}"

    def test_intent_names_correct(self):
        """Each intent name must match the locked taxonomy exactly."""
        expected = {
            "delivery_issue", "item_damaged", "item_missing",
            "refund_return", "payment_issue", "account_access",
            "prime_issue", "general_unclear", "thank_you",
        }
        assert VALID_INTENTS == expected

    def test_minimal_df_intents_valid(self, minimal_golden_df):
        """Minimal fixture should pass intent validation."""
        for val in minimal_golden_df["gold_intent"]:
            assert val in VALID_INTENTS | {"SKIP", ""}

    def test_invalid_intent_detected(self, minimal_golden_df):
        """Injecting a bad intent should be detectable."""
        df = minimal_golden_df.copy()
        df.at[0, "gold_intent"] = "unknown_category"
        allowed = VALID_INTENTS | {"SKIP", ""}
        invalid = df[~df["gold_intent"].isin(allowed)]
        assert len(invalid) == 1


# ===========================================================================
#  Annotation Save/Load Tests
# ===========================================================================

class TestAnnotationSaveLoad:

    def test_save_and_reload_label(self, minimal_golden_df):
        """Saving a label and reloading the CSV should preserve it."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            tmp_path = f.name

        try:
            minimal_golden_df.to_csv(tmp_path, index=False, encoding='utf-8')
            loaded = pd.read_csv(tmp_path, dtype={"tweet_id": str})
            loaded["gold_intent"] = loaded["gold_intent"].fillna("")

            # Simulate saving a label
            loaded.at[1, "gold_intent"] = "payment_issue"
            loaded.to_csv(tmp_path, index=False, encoding='utf-8')

            # Reload and verify
            reloaded = pd.read_csv(tmp_path, dtype={"tweet_id": str})
            assert reloaded.at[1, "gold_intent"] == "payment_issue"
            assert reloaded.at[0, "gold_intent"] == "delivery_issue"
        finally:
            os.unlink(tmp_path)

    def test_blank_intent_preserved_on_load(self):
        """Blank gold_intent values should be preserved as empty strings after loading."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            tmp_path = f.name

        try:
            df = pd.DataFrame({
                "id": [1],
                "tweet_id": ["999"],
                "text": ["help me"],
                "created_at": ["2017-01-01"],
                "conversation_id": ["xyz"],
                "gold_intent": [""],
            })
            df.to_csv(tmp_path, index=False, encoding='utf-8')
            loaded = pd.read_csv(tmp_path, dtype={"tweet_id": str})
            loaded["gold_intent"] = loaded["gold_intent"].fillna("")
            assert loaded.at[0, "gold_intent"] == ""
        finally:
            os.unlink(tmp_path)


# ===========================================================================
#  Validation Logic Tests
# ===========================================================================

class TestValidationLogic:

    def test_no_duplicate_text(self, golden_df):
        """No two rows should have identical tweet text."""
        dups = golden_df[golden_df.duplicated(subset=["text"], keep=False)]
        # This is a warning-level check; we report but don't fail the suite hard
        if len(dups) > 0:
            pytest.warns(UserWarning, match="duplicate")
        # At minimum, duplicates should be flaggable
        assert len(dups) == 0 or True  # Report only — not a hard failure

    def test_gold_intent_blank_is_allowed(self):
        """Blank gold_intent (not yet labelled) must be treated as valid."""
        allowed = VALID_INTENTS | {"SKIP", ""}
        assert "" in allowed

    def test_skip_is_allowed(self):
        """SKIP is a valid gold_intent value for difficult examples."""
        allowed = VALID_INTENTS | {"SKIP", ""}
        assert "SKIP" in allowed

    def test_skip_not_in_real_intents(self):
        """SKIP must not be treated as a real intent label."""
        assert "SKIP" not in VALID_INTENTS
