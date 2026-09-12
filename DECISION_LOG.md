# Decision Log

## Hiver SDE Intern Take-Home Assignment

This document records the main non-obvious design decisions made during the project and the reasoning behind them.

---

### 1. Selected AmazonHelp as the target brand

**Decision:** Use AmazonHelp as the single support brand.

**Why:** AmazonHelp has a large number of customer-support interactions and enough variety to support intent analysis, historical retrieval, reply generation, and evaluation.

---

### 2. Used a small nine-intent taxonomy

**Decision:** Use nine intents instead of creating a very large taxonomy.

**Why:** A small taxonomy is easier to define consistently and evaluate on a limited golden set.

The final intents are:

- `delivery_issue`
- `item_damaged`
- `item_missing`
- `refund_return`
- `payment_issue`
- `account_access`
- `prime_issue`
- `general_unclear`
- `thank_you`

---

### 3. Kept `general_unclear` and defined a primary actionable issue

**Decision:** Use `general_unclear` for genuinely vague or unsupported requests, and assign the primary actionable intent when a message contains multiple issues.

**Why:** The dataset contains many issues outside the selected taxonomy. Forcing every message into an actionable intent would create misleading labels.

For multi-intent messages, selecting the primary actionable issue keeps evaluation deterministic and avoids competing labels.

---

### 4. Separated delivery, damaged, and missing-item issues

**Decision:** Treat delivery problems, physical damage, and missing contents as separate intents.

**Why:** These issues can look similar but may require different support resolutions.

Examples:

- package never arrived → `delivery_issue`
- product arrived broken → `item_damaged`
- package arrived but product is missing → `item_missing`

This distinction was important during manual review of the golden set.

---

### 5. Used conversation-level evaluation splitting and leakage prevention

**Decision:** Split evaluation data at the conversation level and exclude golden-set conversations from the retrieval corpus.

**Why:** Individual tweets from the same conversation could otherwise appear in both training and test data or be retrieved as evidence, producing overly optimistic results.

The primary split contains:

- 140 training examples
- 60 test examples
- 140 training conversations
- 60 test conversations
- 0 conversation overlap

---

### 6. Used TF-IDF as the retrieval baseline

**Decision:** Start historical retrieval with TF-IDF cosine similarity.

**Why:** TF-IDF is simple, transparent, reproducible, and provides a strong enough baseline for inspecting retrieval behavior before adding more complex embedding infrastructure.

---

### 7. Added intent-aware retrieval scoring

**Decision:** Add intent compatibility signals on top of TF-IDF similarity.

**Why:** Pure textual similarity can retrieve messages containing similar words but belonging to different support intents.

The retrieval score therefore combines similarity with intent-related customer and response signals.

---

### 8. Added retrieval conflict and safety filtering

**Decision:** Filter or penalize retrieved examples when they conflict with the detected intent or contain potentially unsuitable historical information.

**Why:** A highly similar historical message is not necessarily appropriate evidence.

Examples include:

- conflicting intents,
- privacy/account-specific content for unrelated intents,
- URLs,
- tracking numbers,
- order numbers,
- unsupported refund promises,
- numeric deadlines,
- case-specific instructions.

This reduces the chance that the reply generator copies an inappropriate historical resolution.

---

### 9. Retained the top three historical examples

**Decision:** Retrieve three historical examples instead of relying on only one.

**Why:** Multiple examples provide more evidence and make it possible to inspect whether historical support behavior is consistent.

The top three examples are passed to the reply-generation stage.

---

### 10. Treated historical responses as evidence, not guaranteed policy

**Decision:** Do not assume that a historical response represents the current Amazon policy.

**Why:** Historical support messages can contain stale URLs, deadlines, promotions, carrier-specific instructions, or case-specific actions.

Historical examples therefore show previous support behavior rather than authoritative current policy.

---

### 11. Added conservative reply generation

**Decision:** Prefer a conservative fallback when historical evidence contains potentially unsafe or case-specific information.

**Why:** Directly copying historical support responses could introduce unsupported commitments.

The reply generator avoids or removes information such as:

- URLs,
- tracking numbers,
- order numbers,
- numeric deadlines,
- refund commitments,
- credit commitments,
- confirmation-specific instructions.

If suitable historical evidence is unavailable, an intent-specific conservative fallback is used.

---

### 12. Added conservative escalation and grounding warnings

**Decision:** Prefer `ESCALATE` when evidence is weak or the request may require customer-specific handling, and flag potentially risky historical content for review.

**Why:** Incorrect automated support can be more harmful than human review.

The system is particularly conservative for:

- unclear requests,
- account-specific or security-sensitive issues,
- weak retrieval evidence,
- potentially case-specific historical responses.

The latest end-to-end evaluation produced:

- `AUTO_HANDLE`: 17.5%
- `ESCALATE`: 82.5%
- grounding warnings: 3.0%

The grounding-warning rate is a review signal and **must not be interpreted as a hallucination rate**.

---

### 13. Used a 200-example manually reviewed golden set

**Decision:** Use 200 real AmazonHelp customer messages for the main evaluation.

**Why:** The set is small enough for detailed manual review while still covering the main taxonomy.

The final labels were manually reviewed and confirmed using the annotation guidelines.

The set is intentionally imbalanced, so both accuracy and macro-averaged metrics are reported.

---

### 14. Added explicit evaluation and reproducibility checks

**Decision:** Include duplicate/leakage checks, automated tests, deterministic fallbacks, and reproducible evaluation scripts.

**Why:** Evaluation results should be repeatable and should not depend completely on an external model or hidden state.

The final leakage check reported:

- duplicate tweet IDs: 0
- duplicate texts: 0
- duplicate conversation IDs: 0

The test suite passes all **17 tests**.

---

### 15. Did not fabricate LLM-as-judge results

**Decision:** Do not report LLM-judge or human-vs-LLM agreement numbers when the complete judge evaluation could not be run reliably.

**Why:** A smaller honest evaluation is preferable to reporting unsupported metrics.

A local Ollama model was tested, but inference speed was not practical for completing the required 50-example judge workflow.

Therefore, no fabricated LLM-judge scores, agreement percentages, or Cohen's kappa values are reported.

---

## Summary of the main design principles

1. Keep the taxonomy small and understandable.
2. Prevent conversation-level evaluation leakage.
3. Use historical support behavior as evidence, not current policy.
4. Combine similarity with intent compatibility during retrieval.
5. Filter potentially unsafe historical information.
6. Prefer conservative escalation when confidence is insufficient.
7. Report class imbalance and limitations instead of relying only on headline accuracy.
8. Do not fabricate missing evaluation results.