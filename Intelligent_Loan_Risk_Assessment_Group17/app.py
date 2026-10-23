import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from flask import Flask, render_template, request, jsonify
from src.loan_history import chart_position, load_loan_history
from src.predict import predict_risk
from src.risk_utils import risk_message, risk_suggestions

app = Flask(__name__)
ROOT = Path(__file__).resolve().parent
HISTORY_PATH = ROOT / "data" / "raw" / "loan_risk_demo.csv"
METADATA_PATH = ROOT / "models" / "metadata.json"

REQUIRED_FIELDS = [
    "person_age", "person_income", "person_home_ownership",
    "person_emp_length", "loan_intent", "loan_grade",
    "loan_amnt", "loan_int_rate", "cb_person_default_on_file",
    "cb_person_cred_hist_length", "credit_score", "existing_debt"
]
APPLICANT_FIELDS = [
    "person_age", "person_income", "person_home_ownership",
    "person_emp_length", "cb_person_default_on_file",
    "cb_person_cred_hist_length", "credit_score", "existing_debt",
]
SUPPORTED_LOAN_INTENTS = {
    "EDUCATION", "VENTURE", "PERSONAL", "DEBTCONSOLIDATION", "HOMEIMPROVEMENT"
}
OTHER_LOAN_INTENT = "OTHER"
SHARED_LOAN_FIELDS = ["loan_intent", "loan_grade", "loan_amnt", "loan_int_rate"]

SAMPLE = {
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
    "secondary_person_age": 54,
    "secondary_person_income": 620000,
    "secondary_person_home_ownership": "OWN",
    "secondary_person_emp_length": 12,
    "secondary_cb_person_default_on_file": "N",
    "secondary_cb_person_cred_hist_length": 18,
    "secondary_credit_score": 735,
    "secondary_existing_debt": 120000,
}

def validate_payload(data):
    loan_intent = data.get("loan_intent")
    required_fields = REQUIRED_FIELDS
    if loan_intent == OTHER_LOAN_INTENT:
        required_fields = [
            field for field in REQUIRED_FIELDS
            if field not in {"loan_grade", "loan_int_rate"}
        ]
    missing = [
        field for field in required_fields
        if field not in data or data[field] in ("", None)
    ]
    if missing:
        return f"Missing required field(s): {', '.join(missing)}"
    if loan_intent not in SUPPORTED_LOAN_INTENTS | {OTHER_LOAN_INTENT}:
        return "Select a supported loan purpose."
    if loan_intent == OTHER_LOAN_INTENT:
        other_loan_type = data.get("other_loan_type")
        if not isinstance(other_loan_type, str) or not other_loan_type.strip():
            return "Specify the other loan type."
        if len(other_loan_type.strip()) > 100:
            return "The other loan type must be 100 characters or fewer."

    applicant_data = [data]
    if data["loan_intent"] == "EDUCATION":
        secondary_missing = [
            f"secondary_{field}"
            for field in APPLICANT_FIELDS
            if f"secondary_{field}" not in data
            or data[f"secondary_{field}"] in ("", None)
        ]
        if secondary_missing:
            return (
                "Education/fees loans require secondary applicant details: "
                + ", ".join(secondary_missing)
            )
        secondary_data = {
            field: data[f"secondary_{field}"] for field in APPLICANT_FIELDS
        }
        secondary_data.update({field: data[field] for field in SHARED_LOAN_FIELDS})
        applicant_data.append(secondary_data)

    try:
        for applicant in applicant_data:
            age = float(applicant["person_age"])
            income = float(applicant["person_income"])
            emp = float(applicant["person_emp_length"])
            loan = float(applicant["loan_amnt"])
            rate = (
                float(applicant["loan_int_rate"])
                if loan_intent != OTHER_LOAN_INTENT
                else 0
            )
            hist = float(applicant["cb_person_cred_hist_length"])
            score = float(applicant["credit_score"])
            debt = float(applicant["existing_debt"])

            if not (18 <= age <= 100):
                return "Age must be between 18 and 100."
            if income <= 0:
                return "Income must be greater than zero."
            if emp < 0 or loan <= 0 or rate < 0 or hist < 0 or debt < 0:
                return "Numeric values cannot be negative."
            if not (300 <= score <= 850):
                return "Credit score must be between 300 and 850."
    except ValueError:
        return "One or more numeric fields contain invalid values."
    return None


def get_secondary_applicant(data):
    applicant = {
        field: data[f"secondary_{field}"] for field in APPLICANT_FIELDS
    }
    applicant.update({field: data[field] for field in SHARED_LOAN_FIELDS})
    return applicant


def evaluate_applicant(data):
    result = predict_risk(data)
    result["message"] = risk_message(result["risk_category"])
    result["suggestions"] = risk_suggestions(data, result)
    return result

def get_history():
    if not HISTORY_PATH.is_file():
        app.logger.warning("Historical loan data is unavailable: %s", HISTORY_PATH)
        return None

    history = load_loan_history(HISTORY_PATH)
    if METADATA_PATH.is_file():
        with METADATA_PATH.open(encoding="utf-8") as metadata_file:
            metadata = json.load(metadata_file)
        history["dataset_type"] = metadata.get("dataset_type", "Training dataset")
    else:
        history["dataset_type"] = "Training dataset"
    return history

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.form.to_dict()
        error = validate_payload(data)
        if error:
            return render_template("index.html", error=error, form=data, sample=SAMPLE)

        if data["loan_intent"] == OTHER_LOAN_INTENT:
            return render_template(
                "other_loan_received.html",
                other_loan_type=data["other_loan_type"].strip(),
            )

        result = evaluate_applicant(data)
        secondary_result = None
        applicants = [{
            "label": "Primary applicant",
            "loan_to_income_ratio": result["loan_to_income_ratio"],
            "default_probability": result["default_probability"],
            "risk_category": result["risk_category"],
        }]
        if data["loan_intent"] == "EDUCATION":
            secondary_result = evaluate_applicant(get_secondary_applicant(data))
            applicants.append({
                "label": "Secondary applicant",
                "loan_to_income_ratio": secondary_result["loan_to_income_ratio"],
                "default_probability": secondary_result["default_probability"],
                "risk_category": secondary_result["risk_category"],
            })
        assessment_history_entry = {
            "id": str(uuid4()),
            "assessed_at": datetime.now(timezone.utc).isoformat(),
            "applicants": applicants,
        }
        history = get_history()
        applicant_point = chart_position(
            float(data["person_income"]),
            float(data["loan_amnt"]),
            history,
        ) if history else None
        return render_template(
            "result.html",
            result=result,
            applicant=data,
            history=history,
            applicant_point=applicant_point,
            secondary_result=secondary_result,
            assessment_history_entry=assessment_history_entry,
        )

    initial_form = {}
    return render_template("index.html", form=initial_form, sample=SAMPLE)

@app.route("/assessment/edit", methods=["POST"])
def edit_assessment():
    return render_template("index.html", form=request.form.to_dict(), sample=SAMPLE)

@app.route("/trends")
def trends():
    return render_template("trends.html", history=get_history())


@app.route("/history")
def assessment_history():
    return render_template("history.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json(silent=True) or {}
    error = validate_payload(data)
    if error:
        return jsonify({"error": error}), 400
    if data["loan_intent"] == OTHER_LOAN_INTENT:
        return jsonify({
            "error": (
                "Custom loan types are not supported by the risk model. "
                "Use the web form to record the application details without a risk score."
            )
        }), 422
    result = evaluate_applicant(data)
    if data["loan_intent"] == "EDUCATION":
        result["secondary_applicant"] = evaluate_applicant(
            get_secondary_applicant(data)
        )
    return jsonify(result)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "Intelligent Loan Risk Assessment System"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
