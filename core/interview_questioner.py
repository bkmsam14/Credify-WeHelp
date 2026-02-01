"""
AI Interview Question Generator
Creates personalized interview questions for loan officers based on model insights
Questions are tailored to LIME feature importance and applicant data
"""

from typing import Dict, List, Any


def generate_interview_questions(
    raw_data: Dict[str, Any],
    lime_features: List[Dict[str, Any]],
    pd_score: float
) -> List[Dict[str, Any]]:
    """
    Generate personalized interview questions based on model insights
    
    Args:
        raw_data: Applicant's data
        lime_features: LIME feature importance results
        pd_score: Current PD score
    
    Returns:
        List of interview questions with context
    """
    
    questions = []
    
    print(f"\n🎤 Generating personalized interview questions...")
    print(f"   PD Score: {pd_score:.4f}, Top risk factors: {[f['feature'] for f in lime_features[:3]]}")
    print(f"   Raw data keys present: {list(raw_data.keys())}")
    
    # Categorize LIME features by impact
    high_impact = [f for f in lime_features if abs(f.get("weight", 0)) > 0.05]
    medium_impact = [f for f in lime_features if 0.02 <= abs(f.get("weight", 0)) <= 0.05]
    
    print(f"   High impact features: {[f['feature'] for f in high_impact]}")
    print(f"   Medium impact features: {[f['feature'] for f in medium_impact]}")
    
    # Question priority order
    question_order = 0
    
    # ===== INCOME & EMPLOYMENT QUESTIONS =====
    if "monthly_income" in raw_data:
        monthly_income = raw_data["monthly_income"]
        employment_years = raw_data.get("employment_years", 0)
        
        print(f"   ✓ Found monthly_income: {monthly_income}")
        
        # Always ask about income source
        questions.append({
            "order": question_order,
            "feature": "monthly_income",
            "category": "Income",
            "question": f"Your monthly income is listed as {monthly_income}. Can you walk us through your primary and secondary income sources? Are there any seasonal variations or bonuses we should consider?",
            "purpose": "Understand income stability, sources, and growth potential",
            "follow_up": "Verify income sources and assess stability",
            "priority": "HIGH" if "monthly_income" in [f["feature"] for f in high_impact] else "MEDIUM"
        })
        question_order += 1
        
        if employment_years < 2:
            questions.append({
                "order": question_order,
                "feature": "employment_years",
                "category": "Employment",
                "question": f"You've been in your current employment for {employment_years} year(s). How stable is your position? Have you changed jobs frequently in the past?",
                "purpose": "Assess employment stability and career progression",
                "follow_up": "Evaluate job stability and tenure reliability",
                "priority": "HIGH" if "employment_years" in [f["feature"] for f in high_impact] else "MEDIUM"
            })
            question_order += 1
    
    # ===== EXPENSE & DEBT QUESTIONS =====
    if "fixed_monthly_expenses" in raw_data:
        expenses = raw_data["fixed_monthly_expenses"]
        income = raw_data.get("monthly_income", 1)
        
        print(f"   ✓ Found fixed_monthly_expenses: {expenses}")
        
        expense_ratio = expenses / income if income > 0 else 0
        
        # Always ask about expenses breakdown
        questions.append({
            "order": question_order,
            "feature": "fixed_monthly_expenses",
            "category": "Expenses",
            "question": f"Your monthly expenses are {expenses}, which is {expense_ratio:.0%} of your income. Can you break down your major expense categories? Are there any expenses that could be reduced?",
            "purpose": "Understand expense burden and identify reduction opportunities",
            "follow_up": "Identify essential vs. discretionary spending",
            "priority": "HIGH" if "fixed_monthly_expenses" in [f["feature"] for f in high_impact] else "MEDIUM"
        })
        question_order += 1
    
    if "debt_to_income_ratio" in raw_data:
        dti = raw_data["debt_to_income_ratio"]
        
        print(f"   ✓ Found debt_to_income_ratio: {dti}")
        
        questions.append({
            "order": question_order,
            "feature": "debt_to_income_ratio",
            "category": "Debt",
            "question": f"Your debt-to-income ratio is {dti:.2f}. What are your existing debts (credit cards, loans, mortgages)? What's your strategy for managing this debt?",
            "purpose": "Understand existing debt obligations and repayment capacity",
            "follow_up": "Assess debt management and repayment plans",
            "priority": "HIGH" if "debt_to_income_ratio" in [f["feature"] for f in high_impact] else "MEDIUM"
        })
        question_order += 1
    
    # ===== CREDIT SCORE QUESTIONS =====
    if "credit_score" in raw_data:
        credit = raw_data["credit_score"]
        
        print(f"   ✓ Found credit_score: {credit}")
        
        if credit < 700:
            questions.append({
                "order": question_order,
                "feature": "credit_score",
                "category": "Credit History",
                "question": f"Your credit score is {credit}. Can you explain any late payments, defaults, or negative items on your credit report? What steps have you taken to improve your score?",
                "purpose": "Understand credit history issues and remediation efforts",
                "follow_up": "Identify credit issues and recovery timeline",
                "priority": "HIGH" if "credit_score" in [f["feature"] for f in high_impact] else "MEDIUM"
            })
            question_order += 1
    
    # ===== PAYMENT HISTORY QUESTIONS =====
    if "utility_bill_on_time_ratio" in raw_data:
        on_time_ratio = raw_data["utility_bill_on_time_ratio"]
        
        print(f"   ✓ Found utility_bill_on_time_ratio: {on_time_ratio}")
        
        if on_time_ratio < 0.98:
            questions.append({
                "order": question_order,
                "feature": "utility_bill_on_time_ratio",
                "category": "Payment History",
                "question": f"Your utility bill payment history shows {on_time_ratio:.0%} on-time payments. What caused the late payments? Do you have systems in place to prevent late payments going forward?",
                "purpose": "Understand payment discipline and reliability",
                "follow_up": "Assess payment reliability and commitment",
                "priority": "MEDIUM"
            })
            question_order += 1
    
    # ===== SAVINGS & EMERGENCY FUND =====
    if "savings_balance" in raw_data:
        savings = raw_data["savings_balance"]
        income = raw_data.get("monthly_income", 1)
        
        print(f"   ✓ Found savings_balance: {savings}")
        
        months_of_savings = savings / income if income > 0 else 0
        
        questions.append({
            "order": question_order,
            "feature": "savings_balance",
            "category": "Financial Stability",
            "question": f"Your savings balance is {savings}. How many months of expenses can this cover? Do you have an emergency fund? What's your savings plan going forward?",
            "purpose": "Assess financial cushion and emergency preparedness",
            "follow_up": "Evaluate financial resilience and safety buffer",
            "priority": "MEDIUM" if months_of_savings < 3 else "LOW"
        })
        question_order += 1
    
    # ===== LOAN PURPOSE & USAGE =====
    if "loan_amount" in raw_data:
        loan_amount = raw_data["loan_amount"]
        income = raw_data.get("monthly_income", 1)
        
        print(f"   ✓ Found loan_amount: {loan_amount}")
        
        loan_to_income = loan_amount / (income * 12) if income > 0 else 0
        
        questions.append({
            "order": question_order,
            "feature": "loan_amount",
            "category": "Loan Purpose",
            "question": f"You're requesting a loan of {loan_amount}, which is {loan_to_income:.1f}x your annual income. What is the purpose of this loan? How will this loan improve your financial situation?",
            "purpose": "Understand loan purpose and expected ROI",
            "follow_up": "Assess loan necessity and intended use",
            "priority": "HIGH"
        })
        question_order += 1
    
    # ===== LOAN DURATION QUESTIONS =====
    if "loan_duration_months" in raw_data:
        duration = raw_data["loan_duration_months"]
        amount = raw_data.get("loan_amount", 1)
        
        print(f"   ✓ Found loan_duration_months: {duration}")
        
        monthly_payment = amount / duration if duration > 0 else 0
        income = raw_data.get("monthly_income", 1)
        payment_ratio = monthly_payment / income if income > 0 else 0
        
        questions.append({
            "order": question_order,
            "feature": "loan_duration_months",
            "category": "Loan Terms",
            "question": f"With a {duration}-month loan term, your estimated monthly payment would be {monthly_payment:.0f}, which is {payment_ratio:.0%} of your income. Can you comfortably afford this payment?",
            "purpose": "Verify affordability and repayment capacity",
            "follow_up": "Confirm payment affordability and commitment",
            "priority": "HIGH"
        })
        question_order += 1
    
    # ===== GENERAL CLOSING QUESTIONS =====
    if pd_score > 0.25:  # High risk
        questions.append({
            "order": question_order,
            "feature": "overall_risk",
            "category": "Risk Mitigation",
            "question": "Based on our analysis, there are some financial risks we've identified. What would make you feel confident about taking on this loan? Are there any co-signers or collateral options you'd consider?",
            "purpose": "Explore risk mitigation strategies",
            "follow_up": "Assess willingness to mitigate identified risks",
            "priority": "HIGH"
        })
        question_order += 1
    
    questions.append({
        "order": question_order,
        "feature": "overall",
        "category": "Additional Information",
        "question": "Is there anything else about your financial situation, employment, or personal circumstances that we should know about? Any changes coming up in the next 12 months?",
        "purpose": "Capture any relevant information not covered by the form",
        "follow_up": "Uncover additional context or upcoming changes",
        "priority": "MEDIUM"
    })
    
    print(f"✅ Generated {len(questions)} personalized interview questions total")
    
    return questions[:10]  # Top 10 questions


def format_questions_for_display(questions: List[Dict[str, Any]]) -> str:
    """
    Format interview questions for display
    
    Args:
        questions: List of interview questions
    
    Returns:
        Formatted string for display
    """
    
    if not questions:
        return "No interview questions generated."
    
    formatted = []
    for q in questions:
        formatted.append(
            f"Q{q['order']+1} ({q['category']}):\n"
            f"   {q['question']}\n"
            f"   💡 Purpose: {q['purpose']}"
        )
    
    return "\n\n".join(formatted)
