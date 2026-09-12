# Hiver SDE Intern Take-Home Assignment

## AI Customer Support Agent for AmazonHelp

This project builds an AI-assisted customer support agent using the **Customer Support on Twitter** dataset.

The selected support brand is **AmazonHelp**.

The agent performs four main steps:

1. Classifies the customer's message into a predefined intent.
2. Retrieves historically similar AmazonHelp customer-support interactions.
3. Generates a reply grounded in historical support responses.
4. Decides whether to `AUTO_HANDLE` or `ESCALATE` the request.

This is an evaluation-oriented prototype, not a production customer-support system.

---

## 1. Problem Framing

Customer support teams receive a large number of repetitive requests.

The goal is to build a small support agent that can:

- understand the customer's primary issue,
- find similar historical support interactions,
- draft a historically grounded response,
- avoid inventing unsupported policies or actions,
- decide whether the request can be safely handled automatically.

The system follows this pipeline:

```text
Customer Message
       |
       v
Intent Classification
       |
       v
Historical Retrieval
(TF-IDF + intent-aware ranking)
       |
       v
Grounded Reply Generation
       |
       v
Escalation Decision
       |
       +------------------+
       |                  |
       v                  v
 AUTO_HANDLE          ESCALATE