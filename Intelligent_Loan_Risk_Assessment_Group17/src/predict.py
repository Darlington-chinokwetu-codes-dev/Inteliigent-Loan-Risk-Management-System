from pathlib import Path
import joblib
import pandas as pd
from .risk_utils import risk_category, confidence_score

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "loan_risk_pipeline.joblib"

_model = None

def get_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model

def prepare_record(data: dict) -> pd.DataFrame:
    record = {
        "person_age": float(data["person_age"]),
        "person_income": float(data["person_income"]),
        "person_home_ownership": data["person_home_ownership"],
        "person_emp_length": float(data["person_emp_length"]),
        "loan_intent": data["loan_intent"],
        "loan_grade": data["loan_grade"],
        "loan_amnt": float(data["loan_amnt"]),
        "loan_int_rate": float(data["loan_int_rate"]),
        "loan_percent_income": float(data["loan_amnt"]) / max(float(data["person_income"]), 1.0),
        "cb_person_default_on_file": data["cb_person_default_on_file"],
        "cb_person_cred_hist_length": float(data["cb_person_cred_hist_length"]),
        "credit_score": float(data["credit_score"]),
        "existing_debt": float(data["existing_debt"]),
    }
    return pd.DataFrame([record])

def predict_risk(data: dict) -> dict:
    model = get_model()
    record = prepare_record(data)
    probability = float(model.predict_proba(record)[0, 1])
    predicted_class = int(probability >= 0.5)
    category = risk_category(probability)

    return {
        "predicted_class": predicted_class,
        "predicted_label": "POSSIBLE DEFAULT" if predicted_class else "NON-DEFAULT",
        "default_probability": round(probability * 100, 2),
        "risk_category": category,
        "confidence": round(confidence_score(probability) * 100, 2),
        "loan_to_income_ratio": round(float(record["loan_percent_income"].iloc[0]), 3),
    }
