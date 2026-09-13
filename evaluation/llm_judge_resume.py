import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "reports" / "generated" / "judge_template.csv"
EXISTING_FILE = PROJECT_ROOT / "reports" / "generated" / "llm_judge_results.csv"
OUTPUT_FILE = PROJECT_ROOT / "reports" / "generated" / "llm_judge_results.csv"

load_dotenv(PROJECT_ROOT / ".env")

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

client = OpenAI()


def build_prompt(row):
    return f"""
You are evaluating an AI customer-support agent.

Evaluate the generated reply using the rubric below.

Customer message:
{row['customer_message']}

Gold intent:
{row['gold_intent']}

Predicted intent:
{row['predicted_intent']}

Generated reply:
{row['reply']}

Agent decision:
{row['decision']}

Score each dimension from 1 to 5.

correctness:
1 = completely wrong or does not address the issue
5 = correctly addresses the customer's issue

groundedness:
1 = unsupported or fabricated information
5 = fully grounded in the provided information/evidence

helpfulness:
1 = not useful to the customer
5 = directly useful and appropriate

tone:
1 = inappropriate/unprofessional
5 = professional, polite, and appropriate

overall:
1 = very poor response
5 = excellent response

Important:
- Do not assume facts that are not provided.
- Do not reward politeness if the answer is incorrect.
- An escalation decision can be appropriate.
- URLs are not automatically evidence of grounding.
- Do not reward invented refunds, deadlines, policies, actions, or guarantees.

Return ONLY valid JSON in exactly this format:

{{
  "correctness": 1,
  "groundedness": 1,
  "helpfulness": 1,
  "tone": 1,
  "overall": 1,
  "reason": "brief explanation"
}}
"""


def validate_result(data):
    required = [
        "correctness",
        "groundedness",
        "helpfulness",
        "tone",
        "overall",
        "reason",
    ]

    for field in required:
        if field not in data:
            return False

    for field in required[:-1]:
        if not isinstance(data[field], int) or not 1 <= data[field] <= 5:
            return False

    return True


def ask_openai(prompt):
    response = client.responses.create(
        model=MODEL,
        input=prompt
    )

    return response.output_text.strip()


def main():

    template = pd.read_csv(INPUT_FILE, dtype=str).fillna("")
    existing = pd.read_csv(EXISTING_FILE, dtype=str).fillna("")

    # Find rows that already have valid LLM scores.
    completed_ids = set(
        existing.loc[
            existing["llm_overall"].str.match(r"^[1-5]$"),
            "id"
        ]
    )

    missing = template[~template["id"].isin(completed_ids)].copy()

    print(f"Already completed: {len(completed_ids)}")
    print(f"Remaining: {len(missing)}")
    print("Remaining IDs:", ", ".join(missing["id"].tolist()))

    if len(missing) == 0:
        print("Nothing to do.")
        return

    results = []

    for _, row in missing.iterrows():

        print(f"\nJudging ID {row['id']}...")

        try:
            prompt = build_prompt(row)

            raw = ask_openai(prompt)

            data = json.loads(raw)

            if not validate_result(data):
                raise ValueError("Invalid JSON score format")

            results.append({
                "id": row["id"],
                "llm_correctness": data["correctness"],
                "llm_groundedness": data["groundedness"],
                "llm_helpfulness": data["helpfulness"],
                "llm_tone": data["tone"],
                "llm_overall": data["overall"],
                "llm_reason": data["reason"],
            })

            print(
                f"Success: overall={data['overall']}"
            )

        except Exception as e:

            print(f"ERROR for ID {row['id']}: {e}")

            results.append({
                "id": row["id"],
                "llm_correctness": "",
                "llm_groundedness": "",
                "llm_helpfulness": "",
                "llm_tone": "",
                "llm_overall": "",
                "llm_reason": f"judge error: {e}",
            })

    new_results = pd.DataFrame(results)

    # Remove old rows for these IDs, then add the newly judged rows.
    existing = existing[
        ~existing["id"].isin(new_results["id"])
    ].copy()

    combined = pd.concat(
        [existing, new_results],
        ignore_index=True
    )

    # Keep the same general column order.
    combined.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nFinished.")
    print(f"Total rows in output: {len(combined)}")
    print(f"Newly processed: {len(results)}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()