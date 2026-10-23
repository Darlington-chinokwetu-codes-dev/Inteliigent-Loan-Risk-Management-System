# Project Report / Review Notes

## Title
Intelligent Loan Risk Assessment System (End-to-End ML Pipeline)

## Domain
Machine Learning / Data Science / FinTech

## Problem
Estimate the probability that a loan applicant may default based on applicant, credit and loan characteristics.

## Core ML Task
Binary classification:
- 0 = Non-default
- 1 = Default

## Models
- Logistic Regression
- Decision Tree
- Random Forest
- XGBoost

## Evaluation Metrics
- Accuracy
- Precision
- Recall
- F1 Score
- ROC-AUC
- Confusion Matrix
- ROC Curve

## End-to-End Flow
Dataset
→ Validation
→ Missing-value handling
→ Categorical encoding
→ Numerical scaling
→ Train/test split
→ Model training
→ Model evaluation
→ Model comparison
→ Best-model selection
→ Model serialization
→ Flask web application
→ Risk prediction

## Application Output
- Binary prediction
- Default probability
- Low / Medium / High risk category
- Confidence score
- Loan-to-income ratio

## Important
The bundled dataset is synthetic and intended for development demonstration. Replace it with the approved academic dataset before presenting final real-world findings.
