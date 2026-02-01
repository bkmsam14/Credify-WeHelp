"""
Advanced Fraud Detection System
Provides rule-based fraud detection with hard and soft flags
"""


def fraud_check(raw: dict) -> dict:
    """
    Comprehensive fraud detection logic
    
    Returns:
        dict: {
            "decision": "PASS" or "BLOCK",
            "fraud_score": float (0.0 to 1.0),
            "flags": list of {"name": str, "severity": str} dicts
        }
    """
    flags = []
    score = 0.0

    # -------------------------
    # HARD flags (auto block)
    # -------------------------
    if int(raw.get("is_fraud", 0)) == 1:
        flags.append({"name": "explicit_fraud_label", "severity": "hard"})
        score += 0.60

    if int(raw.get("document_mismatch_flag", 0)) == 1:
        flags.append({"name": "document_mismatch", "severity": "hard"})
        score += 0.35

    if float(raw.get("metadata_anomaly_score", 0.0)) >= 0.80:
        flags.append({"name": "metadata_anomaly_high", "severity": "hard"})
        score += 0.35

    if float(raw.get("income_inflation_ratio", 1.0)) >= 2.50:
        flags.append({"name": "income_inflation_extreme", "severity": "hard"})
        score += 0.35

    # -------------------------
    # SOFT flags (review)
    # -------------------------
    if int(raw.get("geo_location_mismatch", 0)) == 1:
        flags.append({"name": "geo_location_mismatch", "severity": "soft"})
        score += 0.15

    # Financial inconsistency
    income = raw.get("monthly_income", None)
    expenses = raw.get("fixed_monthly_expenses", None)
    if income is not None and expenses is not None:
        try:
            income = float(income)
            expenses = float(expenses)
            if income > 0 and expenses > income:
                flags.append({"name": "expenses_gt_income", "severity": "soft"})
                score += 0.15
        except (ValueError, TypeError):
            pass

    # Unusual application behavior
    if int(raw.get("application_velocity", 0)) >= 3:
        flags.append({"name": "rapid_multiple_applications", "severity": "soft"})
        score += 0.15

    # Payment behavior red flags (soft)
    if int(raw.get("missed_payments_12m", 0)) >= 3:
        flags.append({"name": "many_missed_payments_12m", "severity": "soft"})
        score += 0.12

    if float(raw.get("utility_bill_on_time_ratio", 1.0)) < 0.30:
        flags.append({"name": "low_utility_on_time_ratio", "severity": "soft"})
        score += 0.12

    # Moderate income inflation (soft)
    infl = float(raw.get("income_inflation_ratio", 1.0))
    if 1.50 <= infl < 2.50:
        flags.append({"name": "income_inflation_moderate", "severity": "soft"})
        score += 0.12

    score = float(min(score, 1.0))
    decision = "BLOCK" if any(f["severity"] == "hard" for f in flags) else "PASS"

    return {
        "decision": decision,
        "fraud_score": round(score, 3),
        "flags": flags
    }


def get_risk_band(pd_score: float, approve_threshold: float = 0.70, reject_threshold: float = 0.40) -> str:
    """
    Determine risk band based on PD score
    
    Args:
        pd_score: Probability of Default (0.0 to 1.0)
        approve_threshold: PD score above which approval is recommended
        reject_threshold: PD score below which rejection is recommended
    
    Returns:
        str: "High" (rejected), "Middle" (review), or "Low" (approved)
    """
    if pd_score >= approve_threshold:
        return "High"
    elif pd_score <= reject_threshold:
        return "Low"
    else:
        return "Middle"
