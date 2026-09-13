import pandas as pd
from pathlib import Path
from sklearn.metrics import cohen_kappa_score


PROJECT_ROOT = Path(__file__).resolve().parents[1]

HUMAN_FILE = PROJECT_ROOT / "reports" / "generated" / "human_review.csv"
LLM_FILE = PROJECT_ROOT / "reports" / "generated" / "llm_judge_results.csv"

OUTPUT_FILE = PROJECT_ROOT / "reports" / "generated" / "agreement_results.csv"


def agreement_metrics(human, llm):
    human = pd.to_numeric(human, errors="coerce")
    llm = pd.to_numeric(llm, errors="coerce")

    valid = human.notna() & llm.notna()

    human = human[valid]
    llm = llm[valid]

    exact = (human == llm).mean()
    within_one = ((human - llm).abs() <= 1).mean()

    kappa = cohen_kappa_score(
        human,
        llm,
        weights="quadratic"
    )

    return len(human), exact, within_one, kappa


def main():

    human = pd.read_csv(HUMAN_FILE, dtype=str).fillna("")
    llm = pd.read_csv(LLM_FILE, dtype=str).fillna("")

    print("Human rows:", len(human))
    print("LLM rows:", len(llm))

    merged = human.merge(
        llm,
        on="id",
        suffixes=("_human", "_llm")
    )

    print("Matched rows:", len(merged))

    dimensions = {
        "correctness": (
            "human_correctness",
            "llm_correctness"
        ),
        "groundedness": (
            "human_groundedness",
            "llm_groundedness"
        ),
        "helpfulness": (
            "human_helpfulness",
            "llm_helpfulness"
        ),
        "tone": (
            "human_tone",
            "llm_tone"
        ),
        "overall": (
            "human_overall",
            "llm_overall"
        ),
    }

    results = []

    print("\nLLM vs Human Agreement")
    print("=" * 70)

    for dimension, (human_col, llm_col) in dimensions.items():

        n, exact, within_one, kappa = agreement_metrics(
            merged[human_col],
            merged[llm_col]
        )

        results.append({
            "dimension": dimension,
            "n": n,
            "exact_agreement": exact,
            "within_one_agreement": within_one,
            "weighted_cohen_kappa": kappa,
        })

        print(f"\n{dimension}")
        print(f"  N: {n}")
        print(f"  Exact agreement: {exact:.3f}")
        print(f"  Within 1 point:  {within_one:.3f}")
        print(f"  Weighted kappa:   {kappa:.3f}")

    results_df = pd.DataFrame(results)

    results_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n" + "=" * 70)
    print(f"Saved agreement results to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()