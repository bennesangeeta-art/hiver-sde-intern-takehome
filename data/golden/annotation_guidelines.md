# Annotation Guidelines — AmazonHelp Golden Evaluation Set

**Version**: 1.0  
**Taxonomy Status**: LOCKED  
**Source**: `reports/intent_analysis.md`

---

## Before You Start

- Label based on the customer's **PRIMARY support need**.
- Do NOT label based on keyword presence alone.
- If you are unsure, use the distinction rules below before choosing `general_unclear`.
- Every label must reflect what the customer actually needs help with.

---

## The 9 Locked Intents

### Quick Reference Table

| Signal in the message | Correct Intent |
|---|---|
| Package never arrived / late / tracking problem | `delivery_issue` |
| Package arrived, but contents missing / empty box | `item_missing` |
| Received product is broken / defective / damaged | `item_damaged` |
| Wants to return item or asks about refund status | `refund_return` |
| Billing error / double charge / gift card / payment failure | `payment_issue` |
| Cannot log in / password / account locked or hacked | `account_access` |
| Prime membership / Prime billing / Prime Video issue | `prime_issue` |
| Genuinely vague — no specific issue determinable | `general_unclear` |
| Pure gratitude / resolved — no open support request | `thank_you` |

---

## Intent-by-Intent Definitions

---

### `delivery_issue`

**Definition**: The customer is waiting for a delivery that has not arrived, is late, or has a tracking problem.

**When to use**:
- Package hasn't arrived by the promised date
- Customer asks "where is my order?"
- Tracking shows no update or is stuck
- Package appears lost in transit

**When NOT to use**:
- Package arrived but an item inside is missing → use `item_missing`
- Package arrived but the product is broken → use `item_damaged`
- Customer is a Prime member but the issue is something else → use that other intent

---

### `item_missing`

**Definition**: The package or order was delivered, but an expected item or content is missing from inside it.

**When to use**:
- "I got the box but the item wasn't inside"
- "Empty box arrived"
- "One of the two items I ordered wasn't in the package"

**When NOT to use**:
- The whole package never arrived → use `delivery_issue`
- The item arrived but is physically broken → use `item_damaged`

---

### `item_damaged`

**Definition**: The customer received the product but it is physically broken, damaged, or defective.

**When to use**:
- "The tablet arrived cracked"
- "The toy was smashed inside the box"
- "The device is defective and doesn't turn on"

**When NOT to use**:
- The package never arrived → use `delivery_issue`
- The customer wants to return an undamaged item → use `refund_return`
- There is a technical/app issue unrelated to physical damage → use `general_unclear` or the appropriate intent

---

### `refund_return`

**Definition**: The customer wants to return an item or is asking about the status of a refund.

**When to use**:
- "How do I return this item?"
- "I sent back my order last week, where is my refund?"
- "I want to exchange this for a different size"

**When NOT to use**:
- The primary problem is an unauthorized charge → use `payment_issue`
- The item is physically damaged (damage is the root cause) → consider `item_damaged`

---

### `payment_issue`

**Definition**: Problems with payments, charges, billing methods, or gift cards.

**When to use**:
- "I was charged twice for the same order"
- "My gift card won't apply at checkout"
- "There is an unauthorized charge on my account"
- "My payment method was declined"

**When NOT to use**:
- Customer is simply requesting a refund for a returned item → use `refund_return`
- The charge is specifically for Prime membership → use `prime_issue`

---

### `account_access`

**Definition**: The customer cannot access their Amazon account due to login, password, account lock, security, or hacking issues.

**When to use**:
- "I can't log into my account"
- "My account has been hacked"
- "Amazon locked my account"
- "I need to reset my password"

**When NOT to use**:
- The customer is logged in and has a payment or order problem → use the appropriate intent
- COD / cash-on-delivery problems → use `payment_issue`

---

### `prime_issue`

**Definition**: Problems specifically related to Amazon Prime membership, Prime billing, cancellation, or Prime-specific services (e.g. Prime Video).

**When to use**:
- "I want to cancel my Prime membership"
- "I was charged for Prime but didn't sign up"
- "Prime Video isn't working"

**When NOT to use**:
- Customer mentions being a Prime member, but the real issue is a late delivery → use `delivery_issue`
- Customer mentions Prime, but the real issue is a payment charge → use `payment_issue`

---

### `thank_you`

**Definition**: The message's PRIMARY purpose is genuine gratitude or confirmation that the issue has been resolved. There is NO unresolved support request anywhere in the message.

**When to use**:
- "Thanks so much, issue sorted!"
- "Really appreciate your help, all resolved now"
- "Thank you, that worked!"

**When NOT to use** (these are the most common mistakes):
- "Thanks, but I still haven't received my order" → use `delivery_issue`
- "Thanks. Can you also help me with my refund?" → use `refund_return`
- Sarcastic "Thanks for nothing" → use `general_unclear`
- Any message containing a question mark → almost certainly NOT `thank_you`
- Any message containing "still", "but", "not yet", "help", "issue", "problem" → NOT `thank_you`

---

### `general_unclear`

**Definition**: The customer's actual support problem cannot reasonably be determined from the message.

**When to use**:
- "This is terrible" (no specifics)
- "Amazon customer service is awful" (no actionable issue)
- Very short vague complaints with no context

**When NOT to use**:
- Any message where a specific problem (delivery, refund, damage, etc.) is visible, even if stated briefly → use that specific intent
- Messages where the customer mentions a product, order, package, charge, login, or Prime → use the appropriate intent

---

## Multi-Intent Messages — Decision Rule

When a message contains signals for multiple intents, always choose the **primary actionable support need** — the root problem the customer needs resolved first.

**Examples:**

| Message summary | Competing intents | Correct label | Reason |
|---|---|---|---|
| "Thanks but where is my package?" | `thank_you`, `delivery_issue` | `delivery_issue` | Unresolved delivery issue takes priority over gratitude |
| "My Prime order arrived damaged, I want a refund" | `item_damaged`, `refund_return`, `prime_issue` | `item_damaged` | The damage is the root cause; refund is the consequence |
| "I'm a Prime member and my package is late" | `prime_issue`, `delivery_issue` | `delivery_issue` | Prime membership is context, not the issue |
| "Charged twice, please refund me" | `payment_issue`, `refund_return` | `payment_issue` | The duplicate charge is the root problem |

---

## Annotation Rules Summary

1. Read the full message carefully.
2. Identify the customer's PRIMARY support need.
3. Apply the correct intent definition, not just a keyword match.
4. If genuinely unsure between two intents, choose the more specific one.
5. Only use `general_unclear` when no specific issue is identifiable.
6. Only use `thank_you` when there is absolutely no open request.
7. If a message is too garbled or irrelevant to label meaningfully, skip it.
