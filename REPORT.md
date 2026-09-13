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

The retrieval evaluation returned at least one historical match for all 200 golden examples, giving a **100% retrieval rate**, with an average top-1 cosine similarity of **0.370**. However, only **53.5%** of top-1 retrieved examples matched the expected intent. This shows that text similarity does not guarantee that the retrieved historical response represents an appropriate resolution.

The prototype also evaluates grounded replies and escalation behavior. These evaluations exposed important failure modes including stale historical responses, wrong-intent retrieval, multilingual cases, and auto-handling when the evidence is insufficient.

The complete end-to-end evaluation achieved **61.0% intent accuracy** on the 200-example golden set. The prototype auto-handled **17.5%** of examples and escalated **82.5%**, reflecting its conservative design.

A 50-example LLM-as-judge evaluation was also completed. For overall reply quality, the judge achieved **34% exact agreement** and **74% agreement within one score point** with human ratings, with a weighted Cohen's kappa of **0.408**.

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
* or the historical response does not provide enough confidence for safe automation.

The prototype intentionally favors conservative escalation over aggressive automation.

---

## 4. Dataset and Brand Selection

The project uses the Kaggle **Customer Support on Twitter** dataset from ThoughtVector.

The raw dataset contains approximately **2.81 million tweets**.

The selected brand is **AmazonHelp** because it has a large number of support interactions and provides sufficient variety for building and evaluating a support agent.

Dataset statistics used during preprocessing:

| Statistic | Value |
| --------- | ----: |
| Total tweets | 2,811,774 |
| AmazonHelp support tweets | 169,840 |
| Customer tweets linked to AmazonHelp | 154,976 |
| AmazonHelp conversation tweets | 324,816 |
| Customer share of connected interactions | 47.71% |

AmazonHelp support tweets were identified using the dataset's `author_id` and `inbound` fields. Customer messages were linked to AmazonHelp responses using `response_tweet_id`.

The raw dataset is not committed to the repository. It is excluded through `.gitignore`.

---

## 5. Intent Taxonomy

The final taxonomy contains nine intents.

| Intent | Definition |
| ------ | ---------- |
| `delivery_issue` | Package late, not delivered, tracking or delivery-date problem |
| `item_damaged` | Product physically damaged or defective when received |
| `item_missing` | Package arrived but expected contents are missing |
| `refund_return` | Return or refund request/process |
| `payment_issue` | Payment, charge, billing, or gift-card payment problem |
| `account_access` | Login, password, account lock, or account-security access problem |
| `prime_issue` | Prime membership, Prime billing, or Prime Video/Prime service issue |
| `general_unclear` | Vague, unsupported, or out-of-taxonomy customer issue |
| `thank_you` | Genuine gratitude or positive resolution with no unresolved request |

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

The examples were sampled from AmazonHelp customer interactions and then manually reviewed. The final gold intents were confirmed using the locked taxonomy.

Final distribution:

| Intent | Count |
| ------ | ----: |
| `general_unclear` | 103 |
| `delivery_issue` | 44 |
| `thank_you` | 20 |
| `refund_return` | 10 |
| `prime_issue` | 9 |
| `payment_issue` | 6 |
| `account_access` | 4 |
| `item_damaged` | 3 |
| `item_missing` | 1 |
| **Total** | **200** |

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
6. Filters conflicting and potentially unsafe evidence.
7. Returns the highest-ranked historical examples.

The system retains the top three evidence examples for response generation.

The reference corpus contains **20,000 historical customer/support pairs** from **17,644 unique conversations** after leakage removal.

---

## 10. Retrieval Evaluation

The retriever was evaluated against all 200 golden examples.

Results:

| Metric | Result |
| ------ | -----: |
| Retrieval rate | **100.0%** |
| Average top-1 cosine similarity | **0.370** |
| Top-1 intent alignment | **53.5%** |

The retrieval rate of 100% means that the system found at least one historical match for every golden example.

However, only 53.5% of top-1 retrieved examples aligned with the expected intent.

Per-intent top-1 alignment:

| Intent | Examples | Alignment |
| ------ | -------: | --------: |
| `general_unclear` | 103 | 74.8% |
| `delivery_issue` | 44 | 47.7% |
| `thank_you` | 20 | 5.0% |
| `refund_return` | 10 | 30.0% |
| `prime_issue` | 9 | 44.4% |
| `payment_issue` | 6 | 0.0% |
| `account_access` | 4 | 25.0% |
| `item_damaged` | 3 | 0.0% |
| `item_missing` | 1 | 0.0% |

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

The generator applies additional relevance and safety checks and cleans common Twitter artifacts such as:

* leading user handles,
* trailing support-agent signatures,
* URLs and tracking links when appropriate,
* formatting artifacts.

Historical responses are treated as **evidence of previous support behavior**, not as guaranteed current policy.

The system does not intentionally invent:

* refund amounts,
* deadlines,
* compensation,
* account actions,
* policies,
* or guaranteed outcomes.

If historical evidence contains potentially unsafe or case-specific information, the system can reject it and use a conservative fallback response.

### Example

Customer message:

> My package has not arrived yet.

The current prototype uses historical AmazonHelp responses as evidence but applies safety and relevance checks before returning a response.

If the historical evidence contains potentially case-specific details such as deadlines, URLs, or unsupported commitments, the system can reject that evidence and use a conservative fallback instead.

For example, a conservative fallback is:

> I'm sorry your package hasn't arrived yet. Please check the latest tracking information, and contact Amazon support if the issue continues.

This demonstrates the intended design: historical support behavior is used as evidence, while potentially stale or case-specific details are filtered rather than treated as guaranteed policy.

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

| Decision | Count | Percentage |
| -------- | ----: | ---------: |
| `AUTO_HANDLE` | 35 | 17.5% |
| `ESCALATE` | 165 | 82.5% |

This relatively high escalation rate reflects the prototype's conservative design.

---

## 13. End-to-End Reply Evaluation

The complete pipeline was evaluated on all 200 golden examples.

Results:

| Metric | Result |
| ------ | -----: |
| Examples evaluated | **200** |
| Intent accuracy | **61.0%** |
| AUTO_HANDLE | **17.5%** |
| ESCALATE | **82.5%** |
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

| Dimension | Average / 5 |
| --------- | ----------: |
| Correctness | **2.70** |
| Groundedness | **2.70** |
| Helpfulness | **2.76** |
| Tone | **3.70** |
| Overall | **2.74** |

The results show that the prototype's tone was stronger than its correctness and grounding.

The main reason is that historical responses can be superficially similar while still being inappropriate for the current case.

The human review included manual scoring of the selected examples. Examples 7–50 used rubric-based scoring suggestions during the review process, while the first six examples were explicitly scored by the reviewer. Therefore, these results should be interpreted as an internal prototype evaluation rather than a fully independent blind human annotation study.

---

## 15. LLM-as-Judge Evaluation

The assignment asks for an LLM-as-judge evaluation and evidence of agreement between the LLM judge and human ratings.

A hosted OpenAI GPT-5.6 Luna judge was used to evaluate 50 examples on:

* correctness,
* groundedness,
* helpfulness,
* tone,
* overall quality.

The judge was given the customer message, predicted intent, generated reply, and evaluation rubric. It was instructed not to assume unsupported policies or reward politeness alone.

### Human-vs-LLM agreement

The 50-example human review was compared with the LLM judge scores.

| Dimension | Exact Agreement | Within ±1 | Weighted Cohen's κ |
| --------- | --------------: | --------: | -----------------: |
| Correctness | 36.0% | 78.0% | 0.461 |
| Groundedness | 38.0% | 68.0% | 0.336 |
| Helpfulness | 30.0% | 66.0% | 0.350 |
| Tone | 46.0% | 88.0% | 0.398 |
| Overall | 34.0% | 74.0% | 0.408 |

For overall quality, the LLM judge achieved **34% exact agreement** and **74% agreement within one score point** with human ratings. The weighted Cohen's κ was **0.408**, indicating moderate agreement.

Agreement was strongest for tone and weaker for helpfulness, showing that LLM-judge scores should be treated as an additional evaluation signal rather than a replacement for human review.

### Important annotation caveat

The 50-example human review was manually scored, but examples 7–50 used rubric-based scoring suggestions during the review process. Therefore, this should be interpreted as a limited internal agreement check rather than a fully independent blind human annotation study.

The first six examples were explicitly scored by the reviewer.

### Judge limitations

The LLM judge can still make subjective scoring decisions and may share biases with the generated system. The agreement analysis therefore provides supporting evidence rather than definitive proof of reply quality.

---

## 16. Failure Analysis

The failure analysis was performed on the 200-example end-to-end evaluation.

The main failure categories were:

| Failure Category | Count |
| ---------------- | ----: |
| Correct intent but escalated | 98 |
| Wrong intent classification | 78 |
| Minority-intent reliability risk | 14 |
| Auto-handled unclear request | 9 |
| Potentially case-specific or stale information | 6 |

These categories can overlap and therefore should not be summed.

### Failure Mode 1: Wrong Intent Classification

Ambiguous customer messages are difficult for a small deterministic taxonomy.

Example:

**Customer:**
"My account login link is not working."

**Gold:** `account_access`

**Predicted:** `general_unclear`

The keyword classifier did not recognize the account-access meaning reliably.

**Hypothesis:**
The classifier depends too heavily on explicit keywords and does not understand paraphrases or multilingual expressions well.

---

### Failure Mode 2: Retrieval Selects the Wrong Historical Resolution

A message can be textually similar to several different support cases.

For example, a delivery-related message may retrieve a historical refund response because both contain words such as "order", "problem", or "delivery".

This can result in a response that is grammatically appropriate but operationally wrong.

**Hypothesis:**
TF-IDF similarity does not understand the underlying support intent. Intent-aware filtering helps, but the taxonomy and retrieval corpus still contain overlapping cases.

---

### Failure Mode 3: Auto-Handling Unclear Requests

Some unclear or negative messages were incorrectly handled automatically.

Example:

**Customer:**
"Thanks for nothing."

**Gold:** `general_unclear`

**Predicted:** `thank_you`

**Decision:** `AUTO_HANDLE`

**Reply:**
"Anytime!"

The keyword "thanks" caused the system to treat the message as genuine gratitude even though the sentiment was negative.

**Hypothesis:**
The `thank_you` rule needs stronger contextual and sentiment checks.

---

### Failure Mode 4: Minority-Intent Reliability

Some intents have extremely few examples in the golden set.

For example:

* `item_missing`: 1 example
* `item_damaged`: 3 examples
* `account_access`: 4 examples
* `payment_issue`: 6 examples

A single error can significantly change the measured score for these classes.

**Hypothesis:**
The evaluation set needs more balanced sampling before making strong claims about minority-intent performance.

---

### Failure Mode 5: Multilingual and Limited-Taxonomy Coverage

The dataset contains customer messages in multiple languages and many support topics that are not represented by the nine-intent taxonomy.

For example, messages involving wrong products, sellers, technical problems, or other Amazon services may be forced into `general_unclear`.

**Hypothesis:**
A production system would require broader taxonomy coverage and multilingual classification support.

---

## 17. What Is Misleading About My Headline Number?

The headline end-to-end intent accuracy is **61.0%**, but this number should not be interpreted as meaning that the support agent correctly understands 61% of all possible customer problems.

There are several reasons.

### 17.1 Class imbalance

`general_unclear` represents 103 of the 200 golden examples.

Therefore, a system can obtain reasonable accuracy by performing well on the largest class while performing poorly on rare but important intents.

### 17.2 Small evaluation set

The golden set contains only 200 examples.

Some classes have only one or a few examples, making their individual metrics unstable.

### 17.3 Limited taxonomy

The nine-intent taxonomy intentionally groups many real-world support problems into `general_unclear`.

Therefore, accuracy partly reflects the chosen taxonomy rather than complete understanding of Amazon customer support.

### 17.4 Historical retrieval limitations

Finding a similar historical message does not guarantee that the associated response is correct for the current customer.

### 17.5 Reply quality is lower than intent accuracy

The human review produced an overall average reply-quality score of **2.74/5**.

Therefore, the 61.0% intent accuracy should not be interpreted as 61% successful customer resolutions.

The more honest conclusion is:

> The prototype demonstrates a reproducible support-agent pipeline and provides measurable improvement over a trivial baseline, but the current evidence is not sufficient to claim production-level support automation.

---

## 18. What Was Not Built

The assignment does not require production deployment, and this project intentionally focuses on the evaluation pipeline.

The following were **not** built:

* production deployment,
* production authentication,
* live customer-service integration,
* real-time ticketing integration,
* human-agent dashboard,
* production monitoring,
* automatic model retraining,
* enterprise-grade observability,
* multilingual model optimization,
* production-grade policy verification,
* real-time Amazon policy validation.

The system is therefore an evaluation-focused prototype.

---

## 19. One More Week: Improvement Plan

With one additional week, I would focus on improving reliability rather than simply increasing the headline accuracy.

### Day 1: Improve taxonomy

Add high-value intents such as:

* wrong item,
* seller issue,
* technical/device issue,
* account security,
* order cancellation,
* subscription/billing.

Review whether `general_unclear` can be reduced.

### Day 2: Improve classification

Replace keyword-only classification with a stronger model and compare:

* TF-IDF + Logistic Regression,
* sentence embeddings,
* few-shot LLM classification.

Use confidence thresholds and allow `general_unclear` when confidence is low.

### Day 3: Improve retrieval

Compare TF-IDF retrieval with embedding-based retrieval.

Use:

* intent filtering,
* semantic similarity,
* recency weighting where appropriate,
* response-quality filtering,
* duplicate removal.

Evaluate retrieval separately before evaluating reply generation.

### Day 4: Improve grounded generation

Use structured evidence objects instead of passing raw historical replies directly.

The generator should explicitly separate:

* customer problem,
* historical evidence,
* safe response content,
* unsupported claims.

Add stronger checks for:

* URLs,
* deadlines,
* refunds,
* credits,
* account-specific actions,
* tracking/order information.

### Day 5: Strengthen the LLM judge

The current hosted judge is complete, but the agreement study should be strengthened.

Next steps:

* recruit a second independent human reviewer,
* blind the reviewers to model outputs where possible,
* increase the agreement set,
* adjudicate disagreements,
* refine the judging rubric.

The current 50-example agreement result should therefore be viewed as an initial validation rather than a final benchmark.

### Day 6: Error-driven iteration

Use the failure cases to improve:

* intent rules,
* retrieval filters,
* escalation thresholds,
* multilingual handling,
* `thank_you` detection.

Then rerun the entire evaluation.

### Day 7: Reproducibility and documentation

Ensure a clean-machine run can reproduce:

* preprocessing,
* golden-set validation,
* classification evaluation,
* retrieval evaluation,
* reply evaluation,
* LLM-judge evaluation,
* agreement metrics.

The README should clearly state which steps require an API key and which steps can run offline.

---

## 20. Reproducibility

The repository contains runnable Python scripts for the main stages.

### Install dependencies

```bash
pip install -r requirements.txt
