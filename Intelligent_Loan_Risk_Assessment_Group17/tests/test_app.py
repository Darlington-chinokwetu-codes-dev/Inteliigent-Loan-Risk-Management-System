from unittest.mock import patch

from app import SAMPLE, app, validate_payload


def education_payload():
    return {
        **SAMPLE,
        "secondary_person_age": "54",
        "secondary_person_income": "620000",
        "secondary_person_home_ownership": "OWN",
        "secondary_person_emp_length": "12",
        "secondary_cb_person_default_on_file": "N",
        "secondary_cb_person_cred_hist_length": "18",
        "secondary_credit_score": "735",
        "secondary_existing_debt": "120000",
    }


def primary_only_payload():
    return {
        key: value
        for key, value in SAMPLE.items()
        if not key.startswith("secondary_")
    }


def prediction_result():
    return {
        "predicted_class": 0,
        "predicted_label": "NON-DEFAULT",
        "default_probability": 18.5,
        "risk_category": "LOW RISK",
        "confidence": 81.5,
        "loan_to_income_ratio": 0.293,
    }


def test_education_assessment_requires_secondary_applicant():
    payload = primary_only_payload()

    assert "secondary applicant details" in validate_payload(payload)


def test_supported_non_education_loan_does_not_require_secondary_applicant():
    payload = {**SAMPLE, "loan_intent": "PERSONAL"}
    for key in list(payload):
        if key.startswith("secondary_"):
            del payload[key]

    assert validate_payload(payload) is None


def test_medical_loan_purpose_is_rejected():
    payload = {**SAMPLE, "loan_intent": "MEDICAL"}

    assert validate_payload(payload) == "Select a supported loan purpose."


def test_other_loan_type_requires_a_specific_description():
    payload = {**primary_only_payload(), "loan_intent": "OTHER"}

    assert validate_payload(payload) == "Specify the other loan type."


def test_other_loan_type_accepts_common_details_without_model_only_fields():
    payload = {
        **primary_only_payload(),
        "loan_intent": "OTHER",
        "other_loan_type": "Vehicle loan",
    }
    payload.pop("loan_int_rate")
    payload.pop("loan_grade")

    assert validate_payload(payload) is None


def test_other_loan_type_rejects_a_description_over_100_characters():
    payload = {
        **primary_only_payload(),
        "loan_intent": "OTHER",
        "other_loan_type": "x" * 101,
    }

    assert validate_payload(payload) == "The other loan type must be 100 characters or fewer."


def test_assessment_form_omits_medical_loan_option_and_has_history_link():
    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b">MEDICAL<" not in response.data
    assert b'value="OTHER"' in response.data
    assert b"specify</option>" in response.data
    assert b"My history" in response.data
    assert b'<option value="" selected>Select loan purpose</option>' in response.data
    assert b'id="secondary-applicant" hidden' in response.data
    assert b'id="other-loan-details" hidden' in response.data
    assert b'id="theme-toggle" type="button" aria-pressed="false"' in response.data
    assert b'class="theme-toggle-label">Dark mode</span>' in response.data
    assert b'class="field-accent-green">Annual Income' in response.data
    assert b'class="field-accent-orange">Existing Debt' in response.data


def test_age_field_explains_that_actual_eligibility_is_lender_specific():
    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b"Actual eligibility varies by country, lender, and loan type" in response.data


def test_education_assessment_shows_separate_applicant_estimates():
    with patch("app.predict_risk", return_value=prediction_result()) as predict:
        response = app.test_client().post("/", data=education_payload())

    assert response.status_code == 200
    assert b"Primary applicant" in response.data
    assert b"Secondary applicant" in response.data
    assert predict.call_count == 2


def test_api_requires_secondary_applicant_for_education():
    response = app.test_client().post("/api/predict", json=primary_only_payload())

    assert response.status_code == 400
    assert b"secondary applicant details" in response.data


def test_api_returns_a_separate_secondary_applicant_estimate():
    with patch(
        "app.predict_risk",
        side_effect=[prediction_result(), prediction_result()],
    ) as predict:
        response = app.test_client().post("/api/predict", json=education_payload())

    assert response.status_code == 200
    assert response.json["secondary_applicant"]["risk_category"] == "LOW RISK"
    assert predict.call_count == 2


def test_api_rejects_medical_loan_purpose():
    payload = {**SAMPLE, "loan_intent": "MEDICAL"}

    response = app.test_client().post("/api/predict", json=payload)

    assert response.status_code == 400


def test_other_loan_type_is_recorded_without_running_the_model():
    payload = {
        **primary_only_payload(),
        "loan_intent": "OTHER",
        "other_loan_type": "Vehicle loan",
    }
    payload.pop("loan_int_rate")
    payload.pop("loan_grade")

    with patch("app.predict_risk") as predict:
        response = app.test_client().post("/", data=payload)

    assert response.status_code == 200
    assert b"Vehicle loan" in response.data
    assert b"no risk score was generated" in response.data
    predict.assert_not_called()


def test_api_does_not_score_custom_loan_types():
    payload = {
        **primary_only_payload(),
        "loan_intent": "OTHER",
        "other_loan_type": "Vehicle loan",
    }

    with patch("app.predict_risk") as predict:
        response = app.test_client().post("/api/predict", json=payload)

    assert response.status_code == 422
    assert b"Custom loan types are not supported" in response.data
    predict.assert_not_called()


def test_edit_assessment_preserves_values_and_submits_to_prediction_route():
    with patch("app.predict_risk") as predict:
        response = app.test_client().post("/assessment/edit", data=education_payload())
    assert response.status_code == 200
    assert b'value="750000"' in response.data
    assert b'method="post" action="/"' in response.data
    predict.assert_not_called()


def test_new_assessment_does_not_prefill_sample_income():
    response = app.test_client().get("/")
    assert b'name="person_income" min="1" step="0.01" required value=""' in response.data


def test_result_omits_confidence_and_keeps_edit_action():
    with patch("app.predict_risk", return_value=prediction_result()):
        response = app.test_client().post("/", data=education_payload())
    assert b"Model Confidence" not in response.data
    assert b"Predicted Class" not in response.data
    assert b'action="/assessment/edit"' in response.data
