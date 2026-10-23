def risk_category(probability: float) -> str:
    if probability < 0.30:
        return "LOW RISK"
    if probability < 0.60:
        return "MEDIUM RISK"
    return "HIGH RISK"

def confidence_score(probability: float) -> float:
    return max(probability, 1.0 - probability)

def risk_message(category: str) -> str:
    messages = {
        "LOW RISK": "The model estimates a relatively low probability of default.",
        "MEDIUM RISK": "The application has a moderate estimated probability of default and may require additional review.",
        "HIGH RISK": "The model estimates a high probability of default. Human review is recommended.",
    }
    return messages.get(category, "Risk assessment completed.")

def risk_suggestions(data: dict, result: dict) -> list[str]:
    suggestions = []
    loan_to_income = float(data["loan_amnt"]) / float(data["person_income"])
    existing_debt_ratio = float(data["existing_debt"]) / float(data["person_income"])

    if result["risk_category"] == "HIGH RISK":
        suggestions.append(
            "Prioritise a qualified human review; treat the model output as a screening signal, not a decision."
        )
    elif result["risk_category"] == "MEDIUM RISK":
        suggestions.append(
            "Review supporting evidence and repayment affordability before reaching a decision."
        )
    else:
        suggestions.append(
            "Verify the application details and complete the usual affordability and policy checks."
        )

    if data["cb_person_default_on_file"] == "Y":
        suggestions.append(
            "Verify the previous-default record, its recency and context, and give the applicant a chance to correct inaccurate information."
        )
    if loan_to_income >= 0.4:
        suggestions.append(
            f"The requested loan is {loan_to_income:.0%} of annual income. Check monthly cash flow and repayment affordability."
        )
    if existing_debt_ratio >= 0.35:
        suggestions.append(
            f"Existing debt is {existing_debt_ratio:.0%} of annual income. Confirm current obligations and monthly repayment capacity."
        )
    if float(data["credit_score"]) < 650:
        suggestions.append(
            "Review the underlying credit file and check for outdated or disputed information."
        )
    if float(data["cb_person_cred_hist_length"]) < 3:
        suggestions.append(
            "Credit history is limited; consider verified complementary affordability information during human review."
        )

    general_checks = [
        "Verify income, debt, employment and credit-history details against supporting documents.",
        "Review documented monthly income, expenses and repayment capacity before reaching a decision.",
        "Consider the model estimate alongside applicable policy and qualified human review; do not use it alone.",
    ]
    for check in general_checks:
        if len(suggestions) >= 3:
            break
        suggestions.append(check)

    return suggestions[:3]
