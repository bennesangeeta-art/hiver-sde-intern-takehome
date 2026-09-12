# Sampling Notes — AmazonHelp Golden Evaluation Set

**Phase**: 4  
**Date**: September 2026  
**Status**: Candidates sampled. Labels NOT yet assigned.

---

## Source

- **Dataset**: Kaggle `thoughtvector/customer-support-on-twitter`
- **File**: `data/raw/twcs/twcs.csv`
- **Total tweets in dataset**: ~2,811,774
- **Brand selected**: AmazonHelp
- **AmazonHelp support tweets**: 169,840
- **Customer tweets connected to AmazonHelp**: 154,976

---

## Sampling Method

### Step 1 — Extract AmazonHelp customer tweets
We extracted all tweets whose `tweet_id` appears in AmazonHelp's `in_response_to_tweet_id` field.  
This ensures we only use tweets that AmazonHelp actually responded to — real, actionable customer messages.

### Step 2 — Filter
We removed:
- Tweets with empty or null text
- Tweets shorter than 15 characters (too short to label meaningfully)
- Tweets longer than 500 characters (outliers, often machine-generated)
- Exact duplicate tweet texts

### Step 3 — Conversation-aware sampling
To reduce leakage between the golden set and the training/retrieval corpus:
- We group tweets by `in_response_to_tweet_id` (conversation thread identifier).
- We sample **exactly one tweet per unique conversation**.
- This means no two golden examples come from the same thread.
- This substantially reduces the risk of a retrieved training example being the golden example's conversation partner.

### Step 4 — Random shuffle and selection
- Random seed: **42** (fixed, fully reproducible)
- After shuffling conversation IDs, we select the first 200 conversations.
- From each selected conversation, exactly one customer tweet is sampled.

---

## Target Size

**200 examples**

Rationale:
- The assignment requires 150–250 hand-labelled examples.
- 200 is the target midpoint.
- 200 examples across 9 intents provides adequate coverage without being too burdensome to label manually.
- The imbalanced nature of real data means some intents will have more examples than others — this is expected and honest.

---

## Duplicate Handling

- Exact text duplicates are removed before sampling.
- Near-duplicates (same conversation, different wording) are prevented by the conversation-level split.

---

## Leakage Prevention

| Risk | Mitigation |
|---|---|
| Golden example in training corpus | Conversation-level split: one tweet per thread |
| Retrieved example = evaluation example | Evaluation retrieval uses only training corpus (enforced in code) |
| LLM judge seeing gold label | Judge prompt does not include gold_intent |
| Same conversation in train and eval | Conversation-aware split minimises this |

---

## Label Assignment

> **CRITICAL:** The `gold_intent` column in `data/golden/golden_set.csv` is intentionally **BLANK**.

Labels must be manually assigned by a human annotator using:
- `data/golden/annotation_guidelines.md` — the labeling guide
- `src/annotate_golden.py` — the terminal annotation tool

**No LLM-generated labels are used for ground truth.**  
**No automatic labels are used for ground truth.**  

If AI assistance is used to suggest a label during annotation, the human annotator must independently verify and confirm or override each suggestion before it is recorded as gold.

---

## Validation

After annotation, run:
```
python src/validate_golden.py
```

This checks:
- Exactly 200 rows
- No duplicate tweet IDs or texts
- All gold_intent values are valid (one of the 9 locked intents or blank)
- All tweet IDs exist in the source dataset
