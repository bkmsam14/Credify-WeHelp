# borderline_advisor.py

from core.knowledge_base import FEATURE_KNOWLEDGE, PD_IMPROVEMENT_RULES

def check_fraud_severity(fraud_flags):
    """Check fraud and return action"""
    severity = fraud_flags.get("severity", "none")
    
    if severity == "hard":
        return "REJECT", "Hard fraud detected - recommend rejection"
    elif severity == "soft":
        return "VERIFY", "Document inconsistencies require verification"
    else:
        return "PROCEED", None

def generate_explanation(lime_features, fraud_status):
    """Generate explanation of borderline status"""
    
    if fraud_status == "VERIFY":
        return "This application requires verification due to document inconsistencies and credit risk factors."
    
    # Get top 2 negative features
    negative = [f for f in lime_features if f["contribution"] < 0]
    
    if len(negative) >= 2:
        f1 = negative[0]["feature"]
        f2 = negative[1]["feature"]
        reason1 = FEATURE_KNOWLEDGE.get(f1, {}).get("explanation", f1)
        reason2 = FEATURE_KNOWLEDGE.get(f2, {}).get("explanation", f2)
        return f"This application is borderline because {reason1} and {reason2}."
    elif len(negative) == 1:
        f1 = negative[0]["feature"]
        reason1 = FEATURE_KNOWLEDGE.get(f1, {}).get("explanation", f1)
        return f"This application is borderline primarily because {reason1}."
    else:
        return "This application is borderline and requires manual review."

def generate_questions(lime_features, fraud_flags):
    """Generate interview questions"""
    
    questions = []
    order = 1
    
    # Fraud questions first
    if fraud_flags.get("severity") == "soft":
        questions.append({
            "order": order,
            "question": f"We noticed some document inconsistencies: {fraud_flags.get('details', 'Please clarify')}",
            "feature": "fraud_verification",
            "follow_up": "Please provide original or certified documents for verification."
        })
        order += 1
    
    # Feature-based questions (top 5 negative features)
    negative = [f for f in lime_features if f["contribution"] < 0]
    
    for feature_data in negative[:5]:
        fname = feature_data["feature"]
        
        if fname in FEATURE_KNOWLEDGE:
            kb = FEATURE_KNOWLEDGE[fname]
            questions.append({
                "order": order,
                "question": kb["question"],
                "feature": fname,
                "follow_up": kb["follow_up"],
                "contribution": feature_data["contribution"]
            })
            order += 1
            
            if order > 7:  # Max 7 questions
                break
    
    return questions

def generate_documents(lime_features):
    """Generate document requests"""
    
    docs = []
    negative = [f for f in lime_features if f["contribution"] < 0]
    
    for feature_data in negative[:4]:  # Top 4 features
        fname = feature_data["feature"]
        if fname in FEATURE_KNOWLEDGE:
            docs.extend(FEATURE_KNOWLEDGE[fname]["documents"])
    
    # Remove duplicates, keep order
    seen = set()
    unique = []
    for doc in docs:
        if doc not in seen:
            seen.add(doc)
            unique.append(doc)
    
    return unique[:6]  # Max 6 documents

def generate_actions(lime_features):
    """Generate improvement actions"""
    
    actions = []
    negative = [f for f in lime_features if f["contribution"] < 0]
    
    for feature_data in negative[:4]:
        fname = feature_data["feature"]
        if fname in FEATURE_KNOWLEDGE:
            for action in FEATURE_KNOWLEDGE[fname]["actions"]:
                
                # Determine feasibility
                if any(word in action.lower() for word in ["reduce", "add co", "provide proof"]):
                    feasibility = "immediate"
                elif "wait" in action.lower() or "month" in action.lower():
                    feasibility = "long-term"
                else:
                    feasibility = "short-term"
                
                actions.append({
                    "action": action,
                    "feasibility": feasibility,
                    "feature": fname,
                    "impact": feature_data["contribution"]
                })
    
    # Remove duplicates
    seen = set()
    unique = []
    for action in actions:
        key = action["action"]
        if key not in seen:
            seen.add(key)
            unique.append(action)
    
    # Sort by impact (most negative first)
    unique.sort(key=lambda x: x["impact"])
    
    return unique[:6]  # Top 6 actions

def estimate_pd_improvement(lime_features, current_pd):
    """Estimate PD improvement if actions taken"""
    
    total_improvement = 0
    negative = [f for f in lime_features if f["contribution"] < 0]
    
    for feature_data in negative[:5]:  # Top 5
        fname = feature_data["feature"]
        if fname in PD_IMPROVEMENT_RULES:
            total_improvement += PD_IMPROVEMENT_RULES[fname]
    
    potential_pd = max(0.03, current_pd - total_improvement)
    
    return {
        "current_pd": f"{current_pd*100:.1f}%",
        "potential_pd": f"{potential_pd*100:.1f}%",
        "improvement": f"{total_improvement*100:.1f}%",
        "note": "Estimate assumes all recommended actions are completed. Actual improvement may vary."
    }

def analyze_borderline_application(pd_score, lime_features, fraud_flags):
    """
    MAIN FUNCTION - Analyze borderline application
    
    Args:
        pd_score: float (e.g., 0.12 for 12%)
        lime_features: list from LIME explainer
        fraud_flags: dict with severity and details
    
    Returns:
        Complete analysis with questions, docs, actions
    """
    
    print(f"\n=== Analyzing Borderline Application (PD: {pd_score*100:.1f}%) ===")
    
    # Check fraud
    fraud_status, fraud_msg = check_fraud_severity(fraud_flags)
    
    if fraud_status == "REJECT":
        return {
            "recommendation": "REJECT",
            "explanation": fraud_msg,
            "interview_questions": [],
            "documents_needed": [],
            "improvement_actions": [],
            "pd_improvement_estimate": {}
        }
    
    # Generate all outputs
    explanation = generate_explanation(lime_features, fraud_status)
    questions = generate_questions(lime_features, fraud_flags)
    documents = generate_documents(lime_features)
    actions = generate_actions(lime_features)
    pd_estimate = estimate_pd_improvement(lime_features, pd_score)
    
    result = {
        "recommendation": "MANUAL_REVIEW",
        "explanation": explanation,
        "interview_questions": questions,
        "documents_needed": documents,
        "improvement_actions": actions,
        "pd_improvement_estimate": pd_estimate
    }
    
    print(f"Generated {len(questions)} questions, {len(documents)} documents, {len(actions)} actions")
    
    return result
