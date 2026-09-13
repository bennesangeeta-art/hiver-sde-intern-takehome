import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "reports" / "generated" / "judge_template.csv"
OUTPUT_FILE = PROJECT_ROOT / "reports" / "generated" / "llm_judge_results.csv"

load_dotenv(PROJECT_ROOT / ".env")

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

client = OpenAI()


def build_prompt(row):

    return f"""
You are an expert evaluator of an AI customer-support agent.

Evaluate the generated customer-support reply using ONLY the information
provided below.

Customer message:
{row["customer_message"]}

Gold intent:
{row["gold_intent"]}

Predicted intent:
{row["predicted_intent"]}

Generated reply:
{row["reply"]}

Agent decision:
{row["decision"]}

Evaluate the reply on five dimensions.

Correctness:
1 = completely wrong or does not address the customer
2 = mostly incorrect
3 = partially correct
4 = mostly correct
5 = fully correct

Groundedness:
1 = unsupported or clearly invented information
2 = mostly unsupported
3 = partially grounded
4 = mostly grounded
5 = fully grounded in the available evidence

Helpfulness:
1 = not useful
2 = slightly useful
3 = moderately useful
4 = helpful
5 = very helpful

Tone:
1 = inappropriate or unprofessional
2 = poor tone
3 = acceptable
4 = good
5 = excellent

Overall:
1 = very poor
2 = weak
3 = acceptable
4 = good
5 = excellent

Important:
- Do not assume information that is not provided.
- Do not reward a reply simply because it is polite.
- A reply that avoids answering the customer's actual question should score low.
- Escalation can be appropriate, but the reply should still acknowledge and address the customer's issue.
- Do not treat URLs as automatically grounded or helpful.
- Do not invent policies, refunds, deadlines, or actions.

Return ONLY valid JSON in exactly this structure:

{{
  "correctness": 1,
  "groundedness": 1,
  "helpfulness": 1,
  "tone": 1,
  "overall": 1,
  "reason": "Brief explanation of the scores."
}}

All five scores must be integers from 1 to 5.
"""


def validate_result(result):

    required = [
        "correctness",
        "groundedness",
        "helpfulness",
        "tone",
        "overall",
        "reason"
    ]

    for field in required:
        if field not in result:
            raise ValueError(f"Missing field: {field}")

    for field in required[:-1]:

        value = int(result[field])

        if value < 1 or value > 5:
            raise ValueError(
                f"{field} must be between 1 and 5"
            )

        result[field] = value

    result["reason"] = str(result["reason"])

    return result


def ask_openai(prompt):

    response = client.responses.create(
        model=MODEL,
        input=prompt
    )

    text = response.output_text.strip()

    return text

def main():

    print("=" * 70)
    print("OPENAI LLM JUDGE")
    print("=" * 70)

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(
        INPUT_FILE,
        dtype=str
    ).fillna("")

    print(f"\nExamples to judge: {len(df)}")
    print(f"Model: {MODEL}")

    results = []

    for index, row in df.iterrows():

        print(
            f"\nJudging example {index + 1}/{len(df)} "
            f"(ID {row['id']})..."
        )

        try:

            prompt = build_prompt(row)

            raw_response = ask_openai(prompt)

            result = json.loads(raw_response)

            result = validate_result(result)

            results.append({

                "id": row["id"],
                "tweet_id": row["tweet_id"],
                "customer_message": row["customer_message"],
                "gold_intent": row["gold_intent"],
                "predicted_intent": row["predicted_intent"],
                "reply": row["reply"],
                "decision": row["decision"],

                "llm_correctness":
                    result["correctness"],

                "llm_groundedness":
                    result["groundedness"],

                "llm_helpfulness":
                    result["helpfulness"],

                "llm_tone":
                    result["tone"],

                "llm_overall":
                    result["overall"],

                "llm_reason":
                    result["reason"],

                "judge_model":
                    MODEL
            })

            print(
                f"Scores: "
                f"C={result['correctness']} "
                f"G={result['groundedness']} "
                f"H={result['helpfulness']} "
                f"T={result['tone']} "
                f"O={result['overall']}"
            )

        except Exception as error:

            print(f"ERROR: {error}")

            results.append({

                "id": row["id"],
                "tweet_id": row["tweet_id"],
                "customer_message": row["customer_message"],
                "gold_intent": row["gold_intent"],
                "predicted_intent": row["predicted_intent"],
                "reply": row["reply"],
                "decision": row["decision"],

                "llm_correctness": "",
                "llm_groundedness": "",
                "llm_helpfulness": "",
                "llm_tone": "",
                "llm_overall": "",

                "llm_reason":
                    f"Judge error: {error}",

                "judge_model":
                    MODEL
            })

    output_df = pd.DataFrame(results)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    successful = (
        output_df["llm_overall"]
        .astype(str)
        .str.match(r"^[1-5]$")
        .sum()
    )

    print("\n" + "=" * 70)
    print("LLM JUDGE COMPLETED")
    print("=" * 70)

    print(
        f"Total examples: {len(output_df)}"
    )

    print(
        f"Successfully judged: {successful}"
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()