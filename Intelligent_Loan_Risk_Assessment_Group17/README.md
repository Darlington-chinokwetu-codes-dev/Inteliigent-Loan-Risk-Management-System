# Intelligent Loan Risk Assessment System
## End-to-End Machine Learning Pipeline — Group 17

A complete academic Machine Learning project for estimating loan default risk from applicant and loan information.

## What is already included

- Synthetic demonstration dataset with 3,500 records
- Data preprocessing pipeline
- Missing-value handling
- Numerical scaling
- Categorical one-hot encoding
- Logistic Regression
- Decision Tree
- Random Forest
- XGBoost
- Model comparison using Accuracy, Precision, Recall, F1 and ROC-AUC
- Automatically selected best model
- Serialized trained pipeline
- Flask web application
- JSON prediction API
- Input validation
- Low / Medium / High risk categories
- Portfolio-pattern charts based on grouped historical loan-to-income outcomes
- Applicant-level loan/income distribution chart with human-review suggestions
- No-account assessment history with browser-local charts and a clear-history control
- Persistent light/dark theme toggle with high-contrast color palettes
- Separate primary and secondary applicant estimates for education/fees loans
- Custom loan-type intake with a required description; no risk score is shown for types the model has not learned
- Confusion matrix
- ROC curve
- Feature-importance chart when supported
- EDA charts
- Unit test
- Windows and Linux/macOS launch scripts

## Important academic note

The included dataset is **synthetic demo data**, generated only so the project can be opened and run immediately.

Do **not** describe the bundled performance figures as real-world lending performance in your final report. Before final submission, replace the demo CSV with the approved project dataset and retrain the pipeline.

The portfolio overview groups historical outcomes by loan-to-income band; the bundled CSV has no dates, so it does not show changes over time. Assessment charts display grouped counts only, not individual historical records.

Assessment history is saved in the current browser's local storage and limited to the most recent 100 assessments. It contains assessment dates, applicant roles, loan-to-income ratios, predicted default probabilities and risk categories only—not names, incomes, credit scores or other entered applicant details. The history is not synced between devices and can be removed from the My history page.

Education/fees assessments require primary and secondary applicant information. The secondary applicant form appears after Education/fees is selected; no other purpose currently requires one. Both applicants are assessed independently against the same loan terms; their model scores are not combined. Selecting Other reveals a required field for the specific loan type. The web form records the provided details for the current response only, does not send or persist them, and does not generate a score; the prediction API returns an unsupported-model error for custom types. The age input accepts 18–100 as a model input range, not as a guarantee of eligibility. Actual age requirements vary by country, lender, product, and sometimes the age at loan maturity; applicants should check the selected lender's published criteria. Historical assessment graphs show model estimates and must not be interpreted as actual repayment or default outcomes. The model's supported purposes do not include medical loans.

## Current demo training result

Best model selected by ROC-AUC: **Logistic Regression**

| Metric | Demo result |
|---|---:|
| Accuracy | 0.803 |
| Precision | 0.629 |
| Recall | 0.737 |
| F1 Score | 0.679 |
| ROC-AUC | 0.868 |

These values come from the included synthetic data and are for software demonstration only.

## Project structure

```text
Intelligent_Loan_Risk_Assessment_Group17/
├── app.py
├── requirements.txt
├── run_windows.bat
├── run_linux_mac.sh
├── data/
│   ├── raw/
│   │   └── loan_risk_demo.csv
│   └── processed/
├── models/
│   ├── loan_risk_pipeline.joblib
│   └── metadata.json
├── notebooks/
├── outputs/
│   ├── model_metrics.csv
│   ├── confusion_matrix.png
│   ├── roc_curve.png
│   ├── feature_importance.png
│   └── EDA plots
├── src/
│   ├── generate_demo_data.py
│   ├── predict.py
│   ├── risk_utils.py
│   └── train.py
├── static/
├── templates/
└── tests/
```

## Run in VS Code on Windows

1. Extract the ZIP.
2. Open the extracted folder in VS Code.
3. Open the integrated terminal.
4. Run:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Or simply double-click:

```text
run_windows.bat
```

Then open:

```text
http://127.0.0.1:5000
```

## Retrain the ML model

The current training dataset is:

```text
data/raw/loan_risk_demo.csv
```

Retrain using:

```powershell
python -m src.train
```

The script will:
1. Load the dataset.
2. Split it into training and testing sets.
3. Preprocess numerical and categorical columns.
4. Train four models.
5. Calculate evaluation metrics.
6. Select the model with the highest ROC-AUC.
7. Save it to `models/loan_risk_pipeline.joblib`.

## Prediction API

Endpoint:

```text
POST /api/predict
```

Example JSON:

```json
{
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
  "existing_debt": 85000
}
```

## Risk categories

- LOW RISK: default probability below 30%
- MEDIUM RISK: 30% to below 60%
- HIGH RISK: 60% and above

The 50% threshold is used for the binary predicted class. The three-level risk category is an application-layer interpretation.

## Responsible-use statement

This project is a decision-support academic prototype. A real financial institution would additionally require:
- approved and representative datasets,
- fairness and bias evaluation,
- privacy controls,
- model monitoring,
- regulatory compliance,
- explainability,
- human review,
- controlled deployment.

## Group 17

Project: **Intelligent Loan Risk Assessment System — End-to-End ML Pipeline**
