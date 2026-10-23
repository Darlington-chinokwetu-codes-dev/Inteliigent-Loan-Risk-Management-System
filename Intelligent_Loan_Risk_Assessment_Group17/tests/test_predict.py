from src.predict import predict_risk

def test_prediction_shape():
    sample = {
        "person_age": 31,
        "person_income": 750000,
        "person_home_ownership": "RENT",
        "person_emp_length": 5,
        "loan_intent": "EDUCATION",
        "loan_grade": "B",
        "loan_amnt": 220000,
        "loan_int_rate": 10.5,
        "cb_person_default_on_file": "N",
        "cb_person_cred_hist_length": 8,
        "credit_score": 720,
        "existing_debt": 85000,
    }

    result = predict_risk(sample)
    assert 0 <= result["default_probability"] <= 100
    assert result["risk_category"] in {"LOW RISK", "MEDIUM RISK", "HIGH RISK"}
    assert result["predicted_class"] in {0, 1}
