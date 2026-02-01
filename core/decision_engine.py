"""
Complete decision intelligence system from hackathon_final.ipynb
Handles model predictions, fraud detection, LIME explanations, and decision logic
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
import pickle
import os

from core.fraud_detector import fraud_check


# Thresholds from hackathon notebook
APPROVE_TH = 0.70  # approval probability threshold
REJECT_TH = 0.40   # rejection probability threshold


def risk_band_from_pd(p_approve: float) -> str:
    """
    Determine risk band from approval probability
    
    Args:
        p_approve: Probability of approval (0.0 to 1.0)
    
    Returns:
        str: "APPROVED", "MIDDLE", or "REJECTED"
    """
    if p_approve >= APPROVE_TH:
        return "APPROVED"
    elif p_approve <= REJECT_TH:
        return "REJECTED"
    else:
        return "MIDDLE"


def build_feature_snapshot(raw: dict, snapshot_features: List[str]) -> Dict[str, Any]:
    """
    Build a snapshot of key features from raw application data
    
    Args:
        raw: Dictionary of application data
        snapshot_features: List of feature names to include
    
    Returns:
        Dictionary with feature values
    """
    snap = {}
    for f in snapshot_features:
        if f in raw:
            v = raw[f]
            # Make JSON-safe
            if isinstance(v, (np.integer, np.floating)):
                v = float(v)
            snap[f] = v
    return snap


def build_summary(decision: str, pd_percent: float, fraud_result: Dict, lime_features: List[Dict]) -> str:
    """
    Build a human-readable summary of the decision
    
    Args:
        decision: Final decision ("APPROVED", "MIDDLE", "REJECTED", "BLOCKED_FRAUD")
        pd_percent: Probability of default as percentage
        fraud_result: Fraud check result dictionary
        lime_features: List of LIME feature contributions
    
    Returns:
        str: Summary text
    """
    if decision == "BLOCKED_FRAUD":
        flags = fraud_result.get("flags", [])
        flag_names = ", ".join([f.get("name", "unknown_flag") for f in flags]) if flags else "inconsistency"
        return f"Blocked due to fraud signal: {flag_names}. Manual verification required."

    # Build short reasons from top LIME features
    top = lime_features[:3] if lime_features else []
    cleaned = []
    for t in top:
        feat = t.get("feature", "")
        feat = feat.split(":")[0]
        feat = feat.replace("num__", "").replace("cat__", "")
        cleaned.append(feat)

    reasons = ", ".join(cleaned) if cleaned else "key risk factors"

    if decision == "APPROVED":
        return f"Approved with low estimated risk (PD {pd_percent}%). Key factors: {reasons}."
    elif decision == "REJECTED":
        return f"Rejected due to high estimated risk (PD {pd_percent}%). Main drivers: {reasons}."
    else:
        return f"Manual review required (PD {pd_percent}%). Key signals: {reasons}."


def analyze_application_complete(
    raw: dict,
    model: Any,
    explainer: Any,
    pipeline: Any = None,
    snapshot_features: List[str] = None
) -> Dict[str, Any]:
    """
    Complete decision intelligence analysis (from hackathon_final.ipynb)
    
    Args:
        raw: Dictionary of application features
        model: Trained model object
        explainer: LIME explainer instance
        pipeline: Preprocessing pipeline (optional, for LIME transformations)
        snapshot_features: List of features to include in snapshot
    
    Returns:
        Complete analysis dictionary with decision, scores, fraud check, and LIME explanations
    """
    
    if snapshot_features is None:
        snapshot_features = [
            "monthly_income",
            "fixed_monthly_expenses",
            "debt_to_income_ratio",
            "employment_years",
            "employment_type",
            "loan_amount",
            "loan_duration_months",
            "utility_bill_on_time_ratio"
        ]
    
    # 1) Model prediction
    X = pd.DataFrame([raw])
    proba = model.predict_proba(X)[0]
    
    # Determine which index is approve class
    try:
        approve_idx = list(model.classes_).index(1)
    except (ValueError, AttributeError):
        approve_idx = 1
    
    p_approve = float(proba[approve_idx])
    pd_score = 1.0 - p_approve  # PD in 0..1
    
    # 2) Risk band from approve probability
    band = risk_band_from_pd(p_approve)
    
    # 3) Fraud detection
    fraud_result = fraud_check(raw)
    
    # 4) LIME explanations
    lime_features = []
    try:
        if explainer is not None:
            # Transform if pipeline provided
            if pipeline is not None:
                X_trans = pipeline.transform(X)[0]
            else:
                X_trans = X.values[0]
            
            exp = explainer.explain_instance(
                X_trans,
                model.predict_proba,
                num_features=10
            )
            lime_features = [
                {"feature": f, "weight": float(w)}
                for f, w in exp.as_list()
            ]
    except Exception:
        lime_features = []
    
    # 5) Final decision with fraud override
    final_decision = band
    if fraud_result.get("decision") == "BLOCK":
        final_decision = "BLOCKED_FRAUD"
    
    # 6) Summary text
    pd_percent = round(pd_score * 100, 2)
    summary = build_summary(final_decision, pd_percent, fraud_result, lime_features)
    
    # 7) Feature snapshot
    feature_snap = build_feature_snapshot(raw, snapshot_features)
    
    return {
        "decision": final_decision,
        "risk_band": band,
        "pd_score": pd_score,
        "pd_percent": pd_percent,
        "approve_probability_percent": round(p_approve * 100, 2),
        "thresholds": {
            "approve": float(APPROVE_TH),
            "reject": float(REJECT_TH)
        },
        "fraud": fraud_result,
        "fraud_decision": fraud_result.get("decision", "PASS"),
        "fraud_score": fraud_result.get("fraud_score", 0.0),
        "lime_features": lime_features,
        "feature_snapshot": feature_snap,
        "summary": summary,
        "input_data": raw
    }
