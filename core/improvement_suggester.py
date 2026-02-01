"""
AI Improvement Suggester
Analyzes which features, when improved, would lower the PD score
Tests variations of features to generate actionable suggestions
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple


# Feature improvement rules - what each tweak means in real terms
FEATURE_TWEAKS = {
    "monthly_income": {
        "increase_percent": 0.15,  # Increase by 15%
        "unit": "USD",
        "get_suggestion": lambda orig_val, pct: f"Increase verified monthly income by {int(orig_val * pct)} {FEATURE_TWEAKS['monthly_income']['unit']}",
        "user_friendly": "Higher monthly income",
        "feasibility": "long-term"
    },
    "fixed_monthly_expenses": {
        "decrease_percent": 0.20,  # Decrease by 20%
        "unit": "USD",
        "get_suggestion": lambda orig_val, pct: f"Reduce monthly expenses by {int(orig_val * pct)} {FEATURE_TWEAKS['fixed_monthly_expenses']['unit']}",
        "user_friendly": "Lower monthly expenses",
        "feasibility": "short-term"
    },
    "savings_balance": {
        "increase_percent": 0.25,  # Increase by 25%
        "unit": "USD",
        "get_suggestion": lambda orig_val, pct: f"Increase savings balance by {int(orig_val * pct)} {FEATURE_TWEAKS['savings_balance']['unit']}",
        "user_friendly": "Increase savings balance",
        "feasibility": "long-term"
    },
    "employment_years": {
        "increase_years": 2,  # Add 2 years
        "unit": "years",
        "get_suggestion": lambda orig_val, inc: f"Maintain stable employment for {int(inc)} more years",
        "user_friendly": "Longer employment history",
        "feasibility": "long-term"
    },
    "credit_score": {
        "increase_points": 50,  # Add 50 points
        "unit": "points",
        "get_suggestion": lambda orig_val, inc: f"Improve credit score by {int(inc)} points",
        "user_friendly": "Higher credit score",
        "feasibility": "short-term"
    },
    "utility_bill_on_time_ratio": {
        "target": 0.98,  # Target 98% on-time payments
        "unit": "%",
        "get_suggestion": lambda orig_val, tgt: f"Ensure {int(tgt * 100)}% of utility bills are paid on time (currently {int(orig_val * 100)}%)",
        "user_friendly": "Better payment history",
        "feasibility": "short-term"
    },
    "loan_amount": {
        "decrease_percent": 0.15,  # Decrease by 15%
        "unit": "USD",
        "get_suggestion": lambda orig_val, pct: f"Reduce loan request by {int(orig_val * pct)} {FEATURE_TWEAKS['loan_amount']['unit']}",
        "user_friendly": "Lower loan amount",
        "feasibility": "immediate"
    },
    "loan_duration_months": {
        "decrease_percent": 0.20,  # Decrease by 20% (shorter duration)
        "unit": "months",
        "get_suggestion": lambda orig_val, dec: f"Choose a shorter loan term (reduce by {int(orig_val * dec)} months)",
        "user_friendly": "Shorter loan term",
        "feasibility": "immediate"
    },
    "debt_to_income_ratio": {
        "decrease_percent": 0.15,  # Decrease by 15%
        "unit": "%",
        "get_suggestion": lambda orig_val, pct: f"Reduce debt-to-income ratio by {int(orig_val * 100 * pct)}% points",
        "user_friendly": "Lower debt-to-income ratio",
        "feasibility": "short-term"
    },
}


def test_feature_improvement(
    raw_data: Dict[str, Any],
    model: Any,
    feature_name: str
) -> Tuple[float, float, str]:
    """
    Test if improving a feature reduces PD score
    
    Args:
        raw_data: Original application data
        model: Trained model
        feature_name: Name of feature to test
    
    Returns:
        (original_pd, improved_pd, improvement_percent_str)
    """
    
    try:
        # Get original PD
        X_orig = pd.DataFrame([raw_data])
        proba_orig = model.predict_proba(X_orig)[0]
        
        try:
            approve_idx = list(model.classes_).index(1)
        except (ValueError, AttributeError):
            approve_idx = 1
        
        pd_orig = 1.0 - float(proba_orig[approve_idx])
        
        # Create modified version
        X_test = raw_data.copy()
        
        if feature_name not in FEATURE_TWEAKS:
            return pd_orig, pd_orig, "0%"
        
        tweak = FEATURE_TWEAKS[feature_name]
        original_value = X_test.get(feature_name, 0)
        
        # Apply tweak based on feature type
        if "increase_percent" in tweak:
            X_test[feature_name] = original_value * (1 + tweak["increase_percent"])
        elif "decrease_percent" in tweak:
            X_test[feature_name] = original_value * (1 - tweak["decrease_percent"])
        elif "increase_years" in tweak:
            X_test[feature_name] = original_value + tweak["increase_years"]
        elif "increase_points" in tweak:
            X_test[feature_name] = original_value + tweak["increase_points"]
        elif "target" in tweak:
            X_test[feature_name] = tweak["target"]
        
        # Get new PD
        X_mod = pd.DataFrame([X_test])
        proba_mod = model.predict_proba(X_mod)[0]
        pd_mod = 1.0 - float(proba_mod[approve_idx])
        
        # Calculate improvement
        improvement = pd_orig - pd_mod
        improvement_percent = (improvement / pd_orig * 100) if pd_orig > 0 else 0
        improvement_str = f"{improvement_percent:.1f}%" if improvement > 0 else "0%"
        
        return pd_orig, pd_mod, improvement_str
        
    except Exception as e:
        print(f"      ❌ Exception in test_feature_improvement: {e}")
        import traceback
        traceback.print_exc()
        raise


def generate_ai_suggestions(
    raw_data: Dict[str, Any],
    model: Any,
    current_pd: float,
    lime_features: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Generate AI suggestions based on actual feature impact analysis
    
    Args:
        raw_data: Original application data
        model: Trained model
        current_pd: Current PD score
        lime_features: LIME feature contributions
    
    Returns:
        List of suggestions sorted by impact
    """
    
    suggestions = []
    
    print(f"\n🔍 Starting AI suggestion generation...")
    print(f"   Raw data keys: {list(raw_data.keys())}")
    print(f"   Current PD: {current_pd}")
    
    # Only test features that are actually present in the data
    for feature_name in FEATURE_TWEAKS.keys():
        if feature_name not in raw_data:
            print(f"   ⏭️  Skipping {feature_name} (not in raw_data)")
            continue
        
        try:
            pd_orig, pd_improved, improvement = test_feature_improvement(raw_data, model, feature_name)
            
            print(f"   📊 {feature_name}: PD {pd_orig:.4f} → {pd_improved:.4f}, improvement={improvement}")
            
            # Only include if there's actual improvement
            improvement_float = float(improvement.rstrip('%'))
            if improvement_float > 0.1:  # At least 0.1% improvement
                # Find the corresponding LIME contribution
                lime_contribution = next(
                    (f["weight"] for f in lime_features if f["feature"].lower().find(feature_name.lower()) >= 0),
                    None
                )
                
                # Generate specific suggestion with actual values
                tweak = FEATURE_TWEAKS[feature_name]
                original_value = raw_data[feature_name]
                
                if "increase_percent" in tweak:
                    specific_suggestion = tweak["get_suggestion"](original_value, tweak["increase_percent"])
                elif "decrease_percent" in tweak:
                    specific_suggestion = tweak["get_suggestion"](original_value, tweak["decrease_percent"])
                elif "increase_years" in tweak:
                    specific_suggestion = tweak["get_suggestion"](original_value, tweak["increase_years"])
                elif "increase_points" in tweak:
                    specific_suggestion = tweak["get_suggestion"](original_value, tweak["increase_points"])
                elif "target" in tweak:
                    specific_suggestion = tweak["get_suggestion"](original_value, tweak["target"])
                else:
                    specific_suggestion = tweak["get_suggestion"](original_value, 0)
                
                suggestions.append({
                    "feature": feature_name,
                    "current_value": raw_data[feature_name],
                    "suggestion": specific_suggestion,
                    "user_friendly": tweak["user_friendly"],
                    "pd_reduction": improvement,
                    "new_estimated_pd": f"{(pd_improved * 100):.2f}%",
                    "feasibility": tweak["feasibility"],
                    "impact_score": improvement_float,
                    "lime_weight": lime_contribution
                })
                print(f"      ✅ Added suggestion: {specific_suggestion}")
            else:
                print(f"      ⚠️  Improvement too small: {improvement} (threshold: 0.1%)")
                
        except Exception as e:
            print(f"   ❌ Error testing feature {feature_name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Sort by impact (biggest improvements first)
    suggestions.sort(key=lambda x: x["impact_score"], reverse=True)
    
    print(f"\n✨ Final: {len(suggestions)} suggestions generated (top 5 will be returned)")
    
    return suggestions[:5]  # Top 5 suggestions


def format_suggestions_for_display(suggestions: List[Dict[str, Any]]) -> str:
    """
    Format suggestions for display to user
    
    Args:
        suggestions: List of suggestions from generate_ai_suggestions
    
    Returns:
        Formatted string for display
    """
    
    if not suggestions:
        return "No improvement suggestions available at this time."
    
    formatted = []
    for i, sugg in enumerate(suggestions, 1):
        formatted.append(
            f"{i}. {sugg['user_friendly']}\n"
            f"   → {sugg['suggestion']}\n"
            f"   📊 Impact: Reduces PD by {sugg['pd_reduction']}\n"
            f"   ⏱️ Feasibility: {sugg['feasibility'].title()}"
        )
    
    return "\n\n".join(formatted)
