# Intent Analysis Report: AmazonHelp

> **Source**: Kaggle `thoughtvector/customer-support-on-twitter` (twcs.csv)
> **Brand**: AmazonHelp

---

## Final Labeling Guidelines

### Important Rules for Human Labelers

- Label based on the customer's **PRIMARY support need**, not simply keyword presence.
- A keyword match must **NOT** automatically determine the intent.
- If a message contains "thanks" but also an unresolved support request, label the **actual support issue** — not `thank_you`.
- Sarcastic "thanks" is **NOT** `thank_you`.
- `thank_you` = primary purpose is gratitude/resolution with **zero** unresolved requests.
- `general_unclear` = only when the customer's actual problem **cannot reasonably be determined**.
- If a specific issue is visible, **do NOT** use `general_unclear`.
- For multiple competing intents, choose the **primary actionable** issue.

### Quick Reference: Intent Distinctions

| Signal | Correct Intent |
|--------|---------------|
| Package never arrived / late / tracking | `delivery_issue` |
| Package arrived, contents missing/empty | `item_missing` |
| Received product is broken/defective | `item_damaged` |
| Wants to return/exchange or asks refund status | `refund_return` |
| Charge/payment/gift-card billing problem | `payment_issue` |
| Cannot log in / password / account locked/hacked | `account_access` |
| Prime membership / Prime billing / Prime Video | `prime_issue` |
| Truly vague — no specific issue determinable | `general_unclear` |
| Pure gratitude / resolved — no open request | `thank_you` |

---

### `delivery_issue`
- **Definition**: Package never arrived, delivery is late, or there is a tracking problem.
- **Include**: Late packages, missing packages (never arrived), tracking issues for active orders.
- **Exclude**: Do not include if the package arrived but an item was missing from inside it.

**3 Real Examples from AmazonHelp dataset:**
> @AmazonHelp Already contacted 3-4 times in the last month. But all I got was assurance that matter is escalated &amp; new status will be provided in 1 day!
> I ordered a game from Amazon and it was supposed to get here today... Now it's not coming till Friday Can't wait for it to be delayed again
> @AmazonHelp No, estimate delivery date is 23rd. But order was placed on 14th. It's okay for me but I was wondering, isn't it a long duration?

**Confusing Example and Correct Decision:**
> @AmazonHelp I just spoke with customer service last week (and have a 5 or 6 times before regarding this) and all they do is try and do a password reset. I'm still waiting for the account specialist to contact me to disable the 2-step. It's been 3 months when it should have been 1-2 days.

- Competing: `delivery_issue` vs `account_access`. Correct intent: `delivery_issue`. Reason: The customer's primary actionable need is `delivery_issue`; the `account_access` keyword appears only as context, not as the main issue.

---

### `item_damaged`
- **Definition**: The received product is physically damaged, broken, or defective.
- **Include**: Physically damaged products, broken upon arrival, defective hardware.
- **Exclude**: Do not include delivery delays, tracking, cancellations, app issues, or generic complaints.

**3 Real Examples from AmazonHelp dataset:**
> @115850 worst service .we are waiting for 4 days to pickup damaged product. Blue dart is 2km away from me they msg me everyday we r coming
> @AmazonHelp - order delivered defective, seller not responding, lots of time on the phone...help
> @AmazonHelp Why won't you let me post a review stating I received two damaged/tampered with items?

**Confusing Example and Correct Decision:**
> @AmazonHelp yes it’s a problem! And they ruined my package ( one of them at least) and that of course delayed everything and I️ had to reorder

- Competing: `item_damaged` vs `delivery_issue`. Correct intent: `item_damaged`. Reason: The customer's primary actionable need is `item_damaged`; the `delivery_issue` keyword appears only as context, not as the main issue.

---

### `item_missing`
- **Definition**: Package arrived but expected contents are missing or the box is empty.
- **Include**: Received package but incomplete contents, empty box arrived.
- **Exclude**: Do not include entire packages that were not delivered (use delivery_issue for that).

**3 Real Examples from AmazonHelp dataset:**
> @115850 - why are you delivering empty boxes?? Where is the content of the box that I paid for!! Your customer service takes for ever to resolve a problem. Not fair ! Not cool !
> @115821 You cheap out on tape and empty boxes get delivered. Not a good start to the season. https://t.co/OEFTAX8R5J
> @AmazonHelp I did not received my order @115850

**Confusing Example and Correct Decision:**
> So @115821 customer service is now on my shit list! Unbelievable! An empty box and refuse to refund....

- Competing: `item_missing` vs `refund_return`. Correct intent: `item_missing`. Reason: The customer's primary actionable need is `item_missing`; the `refund_return` keyword appears only as context, not as the main issue.

---

### `refund_return`
- **Definition**: Return or refund process for an item.
- **Include**: Requests for refunds, return labels, exchange requests.
- **Exclude**: Do not use if the primary request is about an unauthorized charge (use payment_issue).

**3 Real Examples from AmazonHelp dataset:**
> If @115830 keep sending out funko pops in Jiffy bags, you gonna go out of business quick with all the refunds and replacements! 👍
> @115850 I ordered based on info on your manufacturer section which was wrong and thats why I dont want replacement but refund. Pls help
> @AmazonHelp I’m confused. My issue: I’m pregnant &amp; we don’t know if we’re having a girl or boy. And it’ll be due anytime between this week and end of dec. I’d like to get two Xmas outfits to be safe. If baby is born after Xmas do I have Til Jan 31 to return it ?

**Confusing Example and Correct Decision:**
> @AmazonHelp Still not resolved how long does it take for a refund to go on to a gift card on my account because I'm being told so much rubbish it's unreal

- Competing: `refund_return, payment_issue, thank_you`. Correct intent: `refund_return`. Reason: The message contains 'thanks' but also an unresolved `refund_return` request. An unresolved actionable support request always takes priority over a gratitude keyword.

---

### `payment_issue`
- **Definition**: Payment/charge/gift-card payment problem.
- **Include**: Double charges, unrecognized charges, declined cards, gift card redemption errors.
- **Exclude**: Do not include simple refunds for returned items (refund_return) or Prime fees (prime_issue).

**3 Real Examples from AmazonHelp dataset:**
> @115821 I need help! I scanned a $50 gift card on my phone 11/23 and it’s not noted on my account. I noticed yesterday when I went to make a purchase. I sent emails and to no avail. Please help.
> When I select "Amazon.in Gift Card - In a White Box" for 500 INR, I am getting error "Required details are invalid" @115850
> @AmazonHelp So, am I now going to keep getting a payment declined email everyday and an extra day added on to my items? It's three days early access for Battlefront II, not two.

**Confusing Example and Correct Decision:**
> Figures it never hurts to ask......Yo @115821 , can a prime membership having fella get a free gift card? $25, $50, $1000? Eh....it's a shot in the dark but let's see what happens #YouNeverKnow #EitherWayAmazonIsStillBae

- Competing: `payment_issue` vs `prime_issue`. Correct intent: `payment_issue`. Reason: The customer's primary actionable need is `payment_issue`; the `prime_issue` keyword appears only as context, not as the main issue.

---

### `account_access`
- **Definition**: Login, password, account lock, hacked account, or access problem.
- **Include**: Genuine login, password resets, suspended accounts, hacked accounts.
- **Exclude**: Do not include COD/payment/order problems.

**3 Real Examples from AmazonHelp dataset:**
> @AmazonHelp hello, my prime account got blocked. no apparent reason and no instructions to fix. waiting on an urgent package.
> @AmazonHelp Still waiting for the password reset maybe by #cybermonday https://t.co/4hX6ZAHHZi
> @AmazonHelp I haven’t received any emails from Amazon except the automated ones telling that I successfully changed my password

**Confusing Example and Correct Decision:**
> @AmazonHelp It took 11 days still package has not arrived . It showing attempt was failed. If I contact costumer care it showing ur number was blocked. Wat is this @115850 ??? https://t.co/Df5fDXvsVM

- Competing: `account_access` vs `delivery_issue`. Correct intent: `account_access`. Reason: The customer's primary actionable need is `account_access`; the `delivery_issue` keyword appears only as context, not as the main issue.

---

### `prime_issue`
- **Definition**: Prime membership, Prime billing, cancellation, or Prime-specific service problems.
- **Include**: Prime billing, cancelling Prime, Prime Video issues.
- **Exclude**: If Prime is mentioned but the real problem is delivery or payment, use that intent instead.

**3 Real Examples from AmazonHelp dataset:**
> Amazon prime video non mi fa vedere i film.   Perché @120540 ?
> .@AmazonHelp is there anyway to block certain programs from Amazon Prime Video? Some of the kids shows on there are terrible.
> @AmazonHelp glad I pay for my Prime Membership and don't get my 2 day guaranteed shipping. Doubting if prime is even worth it anymore... https://t.co/7E0nUcAUIl

**Confusing Example and Correct Decision:**
> .@115821 Ordered sth on Thursday with guaranteed 1 day shipping. Got delayed. On Sunday I chatted with a rep who promised it would arrive on Tuesday by noon. Now my order shows 'lost in transit'. Why promise sth if you cannot keep it? Bad business practices. Time to cancel prime?

- Competing: `prime_issue` vs `delivery_issue`. Correct intent: `delivery_issue`. Reason: The customer mentions Prime membership, but the actionable problem is a late/missing delivery. We classify based on the primary support problem, not membership status.

---

### `thank_you`
- **Definition**: Genuine gratitude/resolution with NO unresolved support request.
- **Include**: Genuine thanks, confirmation of resolution.
- **Exclude**: Do NOT use if there is any unresolved request, question, or complaint. Sarcastic thanks is NOT thank_you.

**3 Real Examples from AmazonHelp dataset:**
> Week made 😀😀😀 thank you @115830 https://t.co/ns2d4QimQr
> @117795 you sent me old SunChips thanks
> @AmazonHelp Thanks for the info.

**Confusing Example and Correct Decision:**
> @AmazonHelp I ordered x2 items were due on Tues but had to rearrange redelivery. Looked at tracking on the app at 12 and it said delayed then at 3.30 said refused at 1.15 its a shop office with a lot of staff and nobody would do that! Then trying to call yesterday nothing was resolved?

- Competing: `delivery_issue, thank_you`. Correct intent: `delivery_issue`. Reason: The message contains 'thanks' but also an unresolved `delivery_issue` request. An unresolved actionable support request always takes priority over a gratitude keyword.

---

### `general_unclear`
- **Definition**: Truly vague support problem where the actual support issue cannot reasonably be determined.
- **Include**: Genuinely vague complaints or generic requests with no specific actionable detail.
- **Exclude**: If a specific issue is visible (delivery, refund, damage, etc.), do NOT use general_unclear.

**3 Real Examples from AmazonHelp dataset:**
> @AmazonHelp Terrible. You suggest me to use cheaper service costing me 900. Wish @146911 launches soon
> Hi @AmazonHelp @116618 HDR/4K content looks incredibly washed/out dull on my new TCL/Roku TV. Is that (picture attached) the "normal" look or it or is there a problem with the TV or the app (HDR looks great and vibrant on some apps, terrible on others) https://t.co/OCSfLnAK2K
> @AmazonHelp Terrible is the situation! You all biggest frauds and criminals of the world!

**Confusing Example and Correct Decision:**
> @AmazonHelp I complained about not receiving my amazon package in late October. Since then I have had nothing but terrible delivery experiences and items not arriving. My last package was “delivered” but it never was. Then they told me it was misscanned. Then they told me it never sent. ??

- Competing: `general_unclear` vs `delivery_issue`. Correct intent: `delivery_issue`. Reason: Although the message sounds vague, a specific actionable issue (`delivery_issue`) is identifiable. `general_unclear` is reserved for messages where NO specific issue can be determined.

---
