"""Generate a synthetic loan-risk dataset for demonstration/testing only."""

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "raw" / "loan_risk_demo.csv"

def main(n=3500, seed=42):
    rng = np.random.default_rng(seed)

    age = rng.integers(21, 66, n)
    income = np.clip(rng.lognormal(np.log(650000), 0.5, n), 180000, 4000000)
    home = rng.choice(["RENT", "MORTGAGE", "OWN", "OTHER"], n, p=[0.46, 0.30, 0.20, 0.04])
    emp = np.minimum(rng.gamma(2.5, 3, n), age - 18)
    intent = rng.choice(
        ["EDUCATION", "MEDICAL", "VENTURE", "PERSONAL", "DEBTCONSOLIDATION", "HOMEIMPROVEMENT"], n
    )
    grade = rng.choice(list("ABCDEFG"), n, p=[0.20, 0.25, 0.22, 0.15, 0.09, 0.06, 0.03])
    grade_idx = np.array([ord(g) - 65 for g in grade])
    loan = np.clip(rng.lognormal(np.log(240000), 0.6, n), 30000, 1500000)
    rate = np.clip(7 + grade_idx * 2.2 + rng.normal(0, 1.2, n), 5.5, 27)
    prev_default = rng.choice(["Y", "N"], n, p=[0.12, 0.88])
    hist = np.clip((age - 18) * rng.uniform(0.2, 0.7, n) + rng.normal(1, 2, n), 1, 35)
    credit = np.clip(760 - grade_idx * 35 - (prev_default == "Y") * 80 + rng.normal(0, 35, n), 300, 850)
    existing_debt = np.clip(income * rng.beta(1.5, 5, n) * 1.2, 0, 1500000)
    loan_percent_income = loan / income
    dti = existing_debt / income

    logit = (
        -3.8
        + 3.0 * np.clip(loan_percent_income, 0, 2)
        + 2.3 * (prev_default == "Y")
        + 2.0 * np.clip((650 - credit) / 250, -1, 1.5)
        + 0.11 * (rate - 10)
        + 0.8 * dti
        + 0.45 * (home == "RENT")
        + 0.35 * (emp < 2)
        + 0.18 * grade_idx
    )

    p = 1 / (1 + np.exp(-logit))
    status = (rng.random(n) < p).astype(int)

    df = pd.DataFrame({
        "person_age": age,
        "person_income": np.round(income, 2),
        "person_home_ownership": home,
        "person_emp_length": np.round(emp, 1),
        "loan_intent": intent,
        "loan_grade": grade,
        "loan_amnt": np.round(loan, 2),
        "loan_int_rate": np.round(rate, 2),
        "loan_percent_income": np.round(loan_percent_income, 4),
        "cb_person_default_on_file": prev_default,
        "cb_person_cred_hist_length": np.round(hist, 1),
        "credit_score": np.round(credit).astype(int),
        "existing_debt": np.round(existing_debt, 2),
        "loan_status": status,
    })

    df.to_csv(OUTPUT, index=False)
    print(f"Generated {len(df)} rows -> {OUTPUT}")

if __name__ == "__main__":
    main()
