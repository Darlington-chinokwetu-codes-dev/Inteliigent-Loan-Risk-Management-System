"""Retrain the project model using data/raw/loan_risk_demo.csv.

Replace that CSV with your approved academic dataset using the same column
names, then run: python -m src.train
"""

from pathlib import Path
import json
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "raw" / "loan_risk_demo.csv"
MODEL_PATH = ROOT / "models" / "loan_risk_pipeline.joblib"
METRICS_PATH = ROOT / "outputs" / "model_metrics.csv"
META_PATH = ROOT / "models" / "metadata.json"

TARGET = "loan_status"

NUMERIC = [
    "person_age", "person_income", "person_emp_length", "loan_amnt",
    "loan_int_rate", "loan_percent_income", "cb_person_cred_hist_length",
    "credit_score", "existing_debt"
]
CATEGORICAL = [
    "person_home_ownership", "loan_intent", "loan_grade",
    "cb_person_default_on_file"
]

def build_preprocessor():
    numeric = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    return ColumnTransformer([
        ("num", numeric, NUMERIC),
        ("cat", categorical, CATEGORICAL),
    ])

def main():
    df = pd.read_csv(DATA_PATH)
    X = df.drop(columns=[TARGET])
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    candidates = {
        "Logistic Regression": LogisticRegression(max_iter=1500, class_weight="balanced", random_state=42),
        "Decision Tree": DecisionTreeClassifier(max_depth=7, min_samples_leaf=8, class_weight="balanced", random_state=42),
        "Random Forest": RandomForestClassifier(
            n_estimators=250, max_depth=12, min_samples_leaf=4,
            class_weight="balanced", random_state=42, n_jobs=-1
        ),
        "XGBoost": XGBClassifier(
            n_estimators=250, max_depth=5, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.9,
            eval_metric="logloss", random_state=42, n_jobs=2
        ),
    }

    results = []
    trained = {}

    for name, estimator in candidates.items():
        pipe = Pipeline([
            ("preprocessor", build_preprocessor()),
            ("model", estimator),
        ])
        pipe.fit(X_train, y_train)
        preds = pipe.predict(X_test)
        probs = pipe.predict_proba(X_test)[:, 1]

        results.append({
            "model": name,
            "accuracy": accuracy_score(y_test, preds),
            "precision": precision_score(y_test, preds, zero_division=0),
            "recall": recall_score(y_test, preds, zero_division=0),
            "f1_score": f1_score(y_test, preds, zero_division=0),
            "roc_auc": roc_auc_score(y_test, probs),
        })
        trained[name] = pipe

    metrics = pd.DataFrame(results).sort_values("roc_auc", ascending=False)
    metrics.to_csv(METRICS_PATH, index=False)

    best_name = metrics.iloc[0]["model"]
    joblib.dump(trained[best_name], MODEL_PATH)

    metadata = {
        "best_model": best_name,
        "selection_metric": "roc_auc",
        "records": len(df),
        "metrics": metrics.to_dict(orient="records"),
    }
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("\nTraining complete.")
    print(metrics.to_string(index=False))
    print(f"\nBest model: {best_name}")
    print(f"Saved to: {MODEL_PATH}")

if __name__ == "__main__":
    main()
