# Hiver SDE Intern Take-Home Assignment

## AI Customer Support Agent for AmazonHelp

---

## 1. Executive Summary

This project builds an AI-assisted customer support agent for AmazonHelp using the Customer Support on Twitter dataset.

The agent takes a customer message and performs four main steps:

1. Classifies the customer's primary intent.
2. Retrieves similar historical AmazonHelp interactions.
3. Drafts a response grounded in historical support behavior.
4. Decides whether to `AUTO_HANDLE` or `ESCALATE` the request.

The prototype focuses on evaluation, leakage prevention, and conservative support behavior rather than production deployment.

The evaluation uses a 200-example golden set of AmazonHelp customer messages. The examples were manually reviewed and their gold intents were confirmed.

On the primary conversation-level test split (seed 42), the keyword baseline achieved:

* Accuracy: **66.7%**
* Macro Precision: **47.1%**
* Macro Recall: **35.1%**
* Macro F1: **35.8%**

For comparison:

* Majority baseline: **58.3% accuracy**, **10.5% macro F1**
* TF-IDF + Logistic Regression: **60.0% accuracy**, **13.2% macro F1**

The results show that simple keyword matching is a useful baseline for this small and imbalanced evaluation set. However, accuracy alone is misleading because `general_unclear` is the largest class. The lower macro F1 shows that performance is substantially weaker across minority intents.

The retrieval evaluation returned at least one historical match for all 200 golden examples, giving a **100% retrieval rate**, with an average top-1 cosine similarity of **0.370**. However, only **53.5%** of top-1 retrieved examples matched the expected intent. This shows that semantic similarity does not guarantee that the retrieved historical response represents an appropriate resolution.

The prototype also evaluates grounded replies and escalation behavior. These evaluations exposed important failure modes including stale historical responses, wrong-intent retrieval, multilingual cases, and auto-handling when the evidence is insufficient.

The system is therefore presented as an evaluation-focused prototype rather than a production-ready autonomous support agent.

---

## 2. Problem Framing

A customer-support agent should not only classify a request. It should also produce a useful response and know when it should not answer automatically.

For this prototype, a successful system should:

* identify the customer's primary issue,
* retrieve relevant historical support behavior,
* produce a grounded response,
* avoid inventing policies or actions,
* escalate uncertain or sensitive requests.

The system separates these responsibilities:

```text
Customer Message
        |
        v
Intent Classification
        |
        v
Historical Retrieval
        |
        v
Grounded Reply
        |
        v
Escalation Decision
```

The key design principle is that **retrieval and response generation should be evidence-based**. Historical responses are treated as examples of past support behavior, not as guaranteed current policies.

---

## 3. What Good Means

The prototype defines "good" across four dimensions.

### 3.1 Intent quality

The system should identify the customer's primary intent using a small taxonomy derived from the AmazonHelp data.

Important intent distinctions include:

* delivery problem versus missing item,
* physical damage versus delivery delay,
* payment problem versus refund/return,
* account access versus general support,
* Prime-related issue versus general Amazon issue,
* genuine gratitude versus an unresolved request.

### 3.2 Retrieval quality

A useful historical example should be:

* relevant to the customer's problem,
* from AmazonHelp,
* from a different conversation than the evaluation example,
* associated with a response that is useful for the current request.

High text similarity alone is not sufficient.

### 3.3 Reply quality

A good reply should:

* address the customer's actual problem,
* use historical evidence,
* avoid unsupported promises,
* avoid inventing refunds, deadlines, credits, policies, or actions,
* maintain a professional support tone.

### 3.4 Escalation quality

The system should escalate when:

* the evidence is weak,
* the request is unclear,
* the issue appears sensitive or account-specific,
* the historical response does not provide enough confidence for safe automation.

The prototype intentionally favors conservative escalation over aggressive automation.

---

## 4. Dataset and Brand Selection

The project uses the Kaggle **Customer Support on Twitter** dataset from ThoughtVector.

The raw dataset contains approximately **2.81 million tweets**.

The selected brand is **AmazonHelp** because it has a large number of support interactions and provides sufficient variety for building and evaluating a support agent.

Dataset statistics used during preprocessing:

| Statistic                                |     Value |
| ---------------------------------------- | --------: |
| Total tweets                             | 2,811,774 |
| AmazonHelp support tweets                |   169,840 |
| Customer tweets linked to AmazonHelp     |   154,976 |
| AmazonHelp conversation tweets           |   324,816 |
| Customer share of connected interactions |    47.71% |

AmazonHelp support tweets were identified using the dataset's `author_id` and `inbound` fields. Customer messages were linked to AmazonHelp responses using `response_tweet_id`.

The raw dataset is not intended to be committed to the repository. It is excluded through `.gitignore`.

---

## 5. Intent Taxonomy

The final taxonomy contains nine intents.

| Intent            | Definition                                                          |
| ----------------- | ------------------------------------------------------------------- |
| `delivery_issue`  | Package late, not delivered, tracking or delivery-date problem      |
| `item_damaged`    | Product physically damaged or defective when received               |
| `item_missing`    | Package arrived but expected contents are missing                   |
| `refund_return`   | Return or refund request/process                                    |
| `payment_issue`   | Payment, charge, billing, or gift-card payment problem              |
| `account_access`  | Login, password, account lock, or account-security access problem   |
| `prime_issue`     | Prime membership, Prime billing, or Prime Video/Prime service issue |
| `general_unclear` | Vague, unsupported, or out-of-taxonomy customer issue               |
| `thank_you`       | Genuine gratitude or positive resolution with no unresolved request |

### Important classification rules

The primary actionable issue is used when a message contains multiple topics.

Examples:

* "My package never arrived" → `delivery_issue`
* "The box arrived but the phone is missing" → `item_missing`
* "The phone arrived broken" → `item_damaged`
* "I want to return this and get a refund" → `refund_return`
* "Why was I charged twice?" → `payment_issue`
* "I cannot log in to my account" → `account_access`
* "Prime Video is not working" → `prime_issue`
* "Thanks for helping me" → `thank_you`

The taxonomy intentionally does not contain separate labels for every possible Amazon support issue. For example, wrong-item, seller, technical-device, privacy, scam, and several other cases may fall into `general_unclear`.

This limitation is documented as an important source of classification error.

---

## 6. Golden Evaluation Set

A golden set of **200 real AmazonHelp customer messages** was created for evaluation.

The examples were sampled from AmazonHelp customer interactions and then manually reviewed. The final gold intents were confirmed using the annotation guidelines and the locked taxonomy.

Final distribution:

| Intent            |   Count |
| ----------------- | ------: |
| `general_unclear` |     103 |
| `delivery_issue`  |      44 |
| `thank_you`       |      20 |
| `refund_return`   |      10 |
| `prime_issue`     |       9 |
| `payment_issue`   |       6 |
| `account_access`  |       4 |
| `item_damaged`    |       3 |
| `item_missing`    |       1 |
| **Total**         | **200** |

The dataset is intentionally small enough for detailed review but is highly imbalanced.

### Sampling and annotation

Sampling and annotation details are documented in:

* `data/golden/sampling_notes.md`
* `data/golden/annotation_guidelines.md`

The golden examples were manually reviewed and their final labels were confirmed before evaluation.

---

## 7. Leakage Prevention

Evaluation leakage was treated as a first-class concern.

The evaluation uses a **conversation-level split**, rather than randomly splitting individual tweets.

The primary split uses:

* `GroupShuffleSplit`
* test size: 30%
* random seed: 42
* grouping key: `conversation_id`

The primary split produced:

* Training examples: **140**
* Test examples: **60**
* Training conversations: **140**
* Test conversations: **60**
* Conversation overlap: **0**

The historical retrieval corpus also excludes the conversations represented in the golden evaluation set.

The reference-pair construction produced:

* AmazonHelp support replies available for pairing: **169,287**
* Matched customer/support pairs before leakage removal: **168,814**
* Pairs removed because they belonged to golden conversations: **635**
* Remaining pairs after conversation-level leakage removal: **168,179**
* Historical reference pairs retained: **20,000**
* Unique historical conversations: **17,644**

The leakage check verifies duplicate tweet IDs, duplicate texts, and conversation overlap.

This prevents the retrieval component from simply finding the evaluation example itself or another message from the same evaluation conversation.

---

## 8. Baselines

Three classification approaches were evaluated.

### 8.1 Majority baseline

The majority baseline always predicts the most frequent class.

Results:

* Accuracy: **58.3%**
* Macro Precision: **8.3%**
* Macro Recall: **14.3%**
* Macro F1: **10.5%**

This demonstrates why accuracy alone is not sufficient for the task.

### 8.2 Keyword baseline

The keyword baseline uses deterministic keyword rules based on the intent taxonomy.

Results:

* Accuracy: **66.7%**
* Macro Precision: **47.1%**
* Macro Recall: **35.1%**
* Macro F1: **35.8%**

The keyword approach outperformed the majority baseline on the primary split.

### 8.3 TF-IDF + Logistic Regression

A simple machine-learning baseline was also evaluated using TF-IDF features and Logistic Regression.

Results:

* Accuracy: **60.0%**
* Macro Precision: **22.8%**
* Macro Recall: **15.7%**
* Macro F1: **13.2%**

The baseline underperformed the keyword approach on this small and highly imbalanced evaluation set.

### Interpretation

The keyword baseline is not presented as the final AI solution. It provides a transparent reference point against which more advanced classification can be evaluated.

---

## 9. Historical Retrieval

The historical retriever uses TF-IDF cosine similarity over AmazonHelp customer messages.

The retriever:

1. Builds a TF-IDF index over historical customer messages.
2. Receives a new customer message.
3. Calculates similarity against historical messages.
4. Applies a small intent-keyword bonus.
5. Excludes the current evaluation message and its conversation.
6. Returns the highest-ranked historical examples.

The system retains the top three evidence examples for response generation.

The reference corpus contains **20,000 historical customer/support pairs** from **17,644 unique conversations** after leakage removal.

---

## 10. Retrieval Evaluation

The retriever was evaluated against all 200 golden examples.

Results:

| Metric                          |     Result |
| ------------------------------- | ---------: |
| Retrieval rate                  | **100.0%** |
| Average top-1 cosine similarity |  **0.370** |
| Top-1 intent alignment          |  **53.5%** |

The retrieval rate of 100% means that the system found at least one historical match for every golden example.

However, only 53.5% of top-1 retrieved examples aligned with the expected intent.

Per-intent top-1 alignment:

| Intent            | Examples | Alignment |
| ----------------- | -------: | --------: |
| `general_unclear` |      103 |     74.8% |
| `delivery_issue`  |       44 |     47.7% |
| `thank_you`       |       20 |      5.0% |
| `refund_return`   |       10 |     30.0% |
| `prime_issue`     |        9 |     44.4% |
| `payment_issue`   |        6 |      0.0% |
| `account_access`  |        4 |     25.0% |
| `item_damaged`    |        3 |      0.0% |
| `item_missing`    |        1 |      0.0% |

These minority-intent numbers are unstable because several classes have very few labelled examples.

### Main conclusion

Retrieval success should not be measured only by whether a similar sentence exists.

A high similarity score can still retrieve a historical response that is:

* unrelated to the real issue,
* specific to an old case,
* stale,
* multilingual and poorly matched,
* or unsuitable for automation.

---

## 11. Grounded Reply Generation

The reply generator selects a historical AmazonHelp response associated with the most relevant retrieved customer example.

The generator applies additional relevance checks and cleans common Twitter artifacts such as:

* leading user handles,
* trailing support-agent signatures,
* some formatting artifacts.

The system does not intentionally invent:

* refund amounts,
* deadlines,
* compensation,
* account actions,
* policies,
* or guaranteed outcomes.

If evidence is weak, the system can produce a conservative response and/or escalate.

### Example

Customer message:

> My package has not arrived yet.

A historical evidence-based response produced by the prototype was:

> Oh no! Have we missed the delivery date provided in your confirmation e-mail? Let us know- we're here to help!

This demonstrates the intended design: use a historical support response rather than generating an unsupported policy from scratch.

However, the evaluation showed that historical responses can still be stale or mismatched, which is a major limitation.

---

## 12. Escalation Logic

The agent returns one of:

* `AUTO_HANDLE`
* `ESCALATE`

The decision is based on intent, retrieval evidence, and safety-oriented heuristics.

The system favors escalation when:

* the request is unclear,
* the retrieved evidence is weak,
* the issue is account-specific,
* the historical response contains potentially case-specific information,
* or automatic handling could create an unsupported commitment.

The current 200-example reply evaluation produced:

| Decision      | Count | Percentage |
| ------------- | ----: | ---------: |
| `AUTO_HANDLE` |    35 |      17.5% |
| `ESCALATE`    |   165 |      82.5% |

This relatively high escalation rate reflects the prototype's conservative design.

---

## 13. End-to-End Reply Evaluation

The complete pipeline was evaluated on all 200 golden examples.

Results:

| Metric                                 |    Result |
| -------------------------------------- | --------: |
| Examples evaluated                     |   **200** |
| Intent accuracy                        | **61.0%** |
| AUTO_HANDLE                            | **17.5%** |
| ESCALATE                               | **82.5%** |
| Examples containing grounding warnings | **3.0%** |

The 3.0% warning rate should **not** be interpreted as a hallucination rate.

Most warnings were caused by historical responses containing URLs such as:

* `https://`
* `t.co/`

There were also a small number of warnings related to terms such as refund, credit, deadlines, or tracking numbers.

These warnings are signals for human review, not proof that the generated response is hallucinated.

---

## 14. Human Reply Review

A 50-example human review set was prepared to evaluate reply quality.

The review dimensions were:

* correctness,
* groundedness,
* helpfulness,
* tone,
* overall quality.

Average scores:

| Dimension    | Average / 5 |
| ------------ | ----------: |
| Correctness  |    **2.70** |
| Groundedness |    **2.70** |
| Helpfulness  |    **2.76** |
| Tone         |    **3.70** |
| Overall      |    **2.74** |

The results show that the prototype's tone was stronger than its correctness and grounding.

The main reason is that historical responses can be superficially similar while still being inappropriate for the current case.

The human review included manual scoring of the selected examples. The scores should therefore be interpreted as an internal prototype evaluation rather than a statistically representative production-quality benchmark.

---

## 15. LLM-as-Judge Status

The assignment asks for an LLM-as-judge evaluation and evidence of agreement between the LLM judge and human ratings.

A local Ollama setup was tested using `qwen3:8b`.

The model was able to run locally, but inference was too slow for practical completion of the required 50-example judge evaluation within the project workflow.

Because the LLM judge did not produce a complete reliable evaluation set, **no fabricated LLM-judge scores or human-vs-LLM agreement statistics are reported**.

This is an explicit limitation of the submitted prototype.

If additional time or a suitable hosted inference environment were available, the next step would be to:

1. Run the same 50 examples through an LLM judge.
2. Score correctness, groundedness, helpfulness, tone, and overall quality.
3. Compare LLM scores against the human scores.
4. Report exact agreement and weighted Cohen's kappa.
5. Inspect disagreements and refine the rubric.

---

## 16. Top Failure Modes

The evaluation produced several recurring failure patterns.

### Failure Mode 1: Similar message, wrong historical resolution

TF-IDF retrieval can find a message with similar vocabulary but a different underlying problem.

For example, a delivery-related customer message can retrieve another delivery message whose historical response contains a different carrier, tracking situation, or case-specific instruction.

**Hypothesis:** lexical similarity does not fully represent customer intent or resolution requirements.

**Improvement:** combine intent classification, semantic embeddings, entity extraction, and minimum similarity/confidence thresholds.

---

### Failure Mode 2: Historical responses can be stale or case-specific

Historical support replies sometimes contain:

* old promotions,
* old URLs,
* specific deadlines,
* carrier-specific instructions,
* references to historical campaigns,
* or actions that cannot safely be assumed for a new customer.

Examples in the evaluation included old contest information, stale support links, and carrier-specific replies.

**Hypothesis:** historical support behavior is evidence of what happened before, not necessarily the current policy.

**Improvement:** add response freshness checks, policy verification, and stronger filtering of time-sensitive responses.

---

### Failure Mode 3: Minority and unsupported intents are difficult

Some intents have extremely few golden examples.

For example:

* `item_missing`: 1 example
* `item_damaged`: 3 examples
* `account_access`: 4 examples
* `payment_issue`: 6 examples

The evaluation showed weak performance for several of these categories.

The taxonomy also does not explicitly represent every Amazon support issue.

**Hypothesis:** the classifier lacks sufficient labelled examples and the taxonomy forces some real-world issues into `general_unclear`.

**Improvement:** expand the golden set, rebalance sampling, and refine the taxonomy using additional data analysis.

---

### Failure Mode 4: Multilingual messages

The dataset contains customer messages in multiple languages.

The prototype's keyword-based classification and TF-IDF retrieval are primarily dependent on English lexical overlap.

Examples included Spanish, German, French, Portuguese, and Japanese messages.

**Hypothesis:** language mismatch reduces keyword coverage and retrieval similarity.

**Improvement:** use multilingual embeddings or a multilingual LLM classifier/retriever and evaluate each major language separately.

---

### Failure Mode 5: Auto-handling can occur with insufficient evidence

Some unclear requests were classified into an actionable intent and automatically handled even though the historical evidence was not strong enough.

A particularly risky pattern is an unclear message being mapped to an intent such as delivery or gratitude and then receiving a direct historical response.

**Hypothesis:** the escalation threshold is not strict enough when classification confidence and retrieval confidence disagree.

**Improvement:** require agreement between intent confidence and retrieval confidence before `AUTO_HANDLE`; otherwise escalate.

---

## 17. What Is Misleading About My Headline Number?

The **66.7% accuracy** of the keyword baseline is the most important number that could be misleading.

The dataset is highly imbalanced, with `general_unclear` representing **103 of 200** golden examples.

A system can therefore obtain a relatively high accuracy while performing poorly on minority intents.

This is visible in the macro F1 score of only **35.8%**.

The retrieval results tell a similar story. A **100% retrieval rate** sounds excellent, but only **53.5%** of top-1 retrieved examples aligned with the expected intent.

Therefore:

> High accuracy or successful retrieval does not mean that the support agent is reliably resolving customer issues.

The more important questions are:

* Does the system handle each intent correctly?
* Is the retrieved evidence appropriate?
* Is the response grounded?
* Does the system escalate uncertain cases?
* Does performance remain stable on minority and multilingual cases?

---

## 18. What Was Not Built

The following production capabilities were intentionally not built:

* production deployment,
* live Amazon support API integration,
* real-time policy verification,
* production authentication,
* human-agent ticketing integration,
* persistent customer account state,
* production-grade multilingual support,
* a large-scale vector database,
* automated policy freshness verification,
* fully automated human-quality annotation,
* comprehensive adversarial safety testing.

The project focuses on demonstrating the evaluation methodology and a runnable prototype.

---

## 19. What I Would Do With One More Week

With one additional week, I would prioritize the following work.

### Day 1–2: Improve retrieval

Replace or complement TF-IDF with multilingual sentence embeddings.

Use:

* semantic similarity,
* intent compatibility,
* language compatibility,
* recency,
* response-quality filtering.

The retriever should reject evidence when confidence is too low.

### Day 3: Improve classification

Create a stronger classifier using an LLM or transformer-based model.

Require structured output:

```json
{
  "intent": "delivery_issue",
  "confidence": 0.91
}
```

Invalid or unsupported intents would fall back to `general_unclear`.

### Day 4: Improve grounded generation

Instead of copying one historical response directly, generate a response using several retrieved examples.

The generator should:

* identify common resolution patterns,
* avoid copying stale links,
* avoid unsupported commitments,
* explicitly state when customer-specific action is required.

### Day 5: Complete LLM judge

Run the 50-example LLM judge evaluation using a practical hosted inference environment.

Calculate:

* average dimension scores,
* exact agreement,
* within-one-point agreement,
* weighted Cohen's kappa,
* disagreement examples.

### Day 6: Improve escalation

Introduce explicit confidence thresholds.

For example:

```text
High intent confidence
        +
High retrieval confidence
        +
Safe historical response
        |
        v
AUTO_HANDLE
```

Otherwise:

```text
ESCALATE
```

### Day 7: Expand evaluation

Increase the golden set and deliberately sample:

* minority intents,
* multilingual messages,
* ambiguous cases,
* multi-intent messages,
* unsupported intents.

This would make the benchmark more representative.

---

## 20. Reproducibility

The repository contains scripts for:

* dataset analysis,
* golden-set creation,
* golden-set validation,
* reference-pair construction,
* leakage checking,
* baseline evaluation,
* retrieval evaluation,
* end-to-end reply evaluation,
* failure analysis,
* human review preparation.

The main evaluation can be reproduced from the prepared project data without rerunning the entire 2.8M-row preprocessing pipeline.

Example commands:

```powershell
python -m evaluation.leakage_check
python -m evaluation.evaluate
python -m evaluation.retrieval_evaluation
python -m evaluation.reply_evaluation
python -m evaluation.failure_analysis
python -m pytest
```

The repository's `.gitignore` prevents secrets, raw dataset archives, extracted raw data, Python cache files, and generated evaluation outputs from being committed unintentionally.

The raw Kaggle dataset is therefore not required to be stored in GitHub.

---

## 21. Testing

The project includes automated tests using `pytest`.

The test suite covers:

* golden-set validation,
* classification behavior,
* retrieval behavior,
* pipeline behavior,
* escalation logic,
* configuration-related behavior.

The project previously achieved a passing test suite with:

```text
17 passed
```

The tests are intended to catch regressions in the core pipeline.

---

## 22. Decision Summary

Important design decisions include:

1. **AmazonHelp was selected** because it has a large and varied support dataset.
2. **Nine intents were selected** to keep the taxonomy small enough for reliable annotation.
3. **`general_unclear` was retained** for unsupported and genuinely vague requests.
4. **Physical damage and missing contents were separated** from delivery problems.
5. **Primary actionable intent** is used for multi-topic messages.
6. **Conversation-level splitting** was used to reduce evaluation leakage.
7. **Golden conversations are excluded from retrieval** during evaluation.
8. **TF-IDF retrieval** was selected as a simple, reproducible baseline.
9. **Intent-aware retrieval scoring** was added to improve lexical retrieval.
10. **Top three historical examples** are retained as evidence.
11. **Historical responses are treated as evidence rather than guaranteed policy.**
12. **Conservative escalation** is preferred when evidence is weak.
13. **URLs and potentially case-specific information are flagged** for review.
14. **The 200-example golden set was manually reviewed** before evaluation.
15. **No LLM-judge results were fabricated** when local inference proved impractical.

---

## 23. Repository Structure

```text
hiver-sde-intern/
│
├── data/
│   ├── golden/
│   │   ├── annotation_guidelines.md
│   │   ├── golden_set.csv
│   │   └── sampling_notes.md
│   │
│   ├── processed/
│   │   ├── amazonhelp_customer_sample.csv
│   │   ├── amazonhelp_reference_pairs.csv
│   │   ├── brand_statistics.csv
│   │   └── intent_analysis.csv
│   │
│   └── raw/
│       └── sample.csv
│
├── evaluation/
│   ├── evaluate.py
│   ├── failure_analysis.py
│   ├── human_review.py
│   ├── inspect_retrieval.py
│   ├── judge.py
│   ├── leakage_check.py
│   ├── llm_judge.py
│   ├── multi_seed_evaluation.py
│   ├── reply_evaluation.py
│   └── retrieval_evaluation.py
│
├── src/
│   ├── build_reference_pairs.py
│   ├── classifier.py
│   ├── create_golden_set.py
│   ├── escalation.py
│   ├── finalize_golden.py
│   ├── fix_conversation_ids.py
│   ├── intent_analysis.py
│   ├── phase0_analysis.py
│   ├── pipeline.py
│   ├── reply_generator.py
│   └── retrieval.py
│
├── tests/
│   └── test_golden.py
│
├── DECISION_LOG.md
├── README.md
├── REPORT.md
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## 24. Key Results at a Glance

| Component                             |  Main Result |
| ------------------------------------- | -----------: |
| Golden set                            | 200 examples |
| Primary keyword accuracy              |    **66.7%** |
| Primary keyword macro F1              |    **35.8%** |
| Majority accuracy                     |    **58.3%** |
| TF-IDF + Logistic Regression accuracy |    **60.0%** |
| Retrieval rate                        |   **100.0%** |
| Average top-1 similarity              |    **0.370** |
| Retrieval intent alignment            |    **53.5%** |
| End-to-end intent accuracy            |    **61.0%** |
| AUTO_HANDLE                           |    **17.5%** |
| ESCALATE                              |    **82.5%** |
| Human review overall score            | **2.74 / 5** |

---

## 25. Conclusion

This project demonstrates an evaluation-focused AI customer support agent for AmazonHelp.

The prototype shows that:

* a small intent taxonomy can provide a useful starting point,
* simple keyword rules can outperform basic TF-IDF classification on this small benchmark,
* historical retrieval can provide useful support evidence,
* retrieval success alone does not guarantee correct resolution,
* historical support responses may be stale or case-specific,
* minority and multilingual cases require additional work,
* conservative escalation is important for safe automation.

The central lesson from the evaluation is that **customer-support automation should optimize for grounded, appropriate resolution rather than headline classification accuracy**.

The current system is therefore best viewed as a strong prototype and evaluation framework, not as a production-ready autonomous support system.



