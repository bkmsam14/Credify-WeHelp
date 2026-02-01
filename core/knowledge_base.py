# knowledge_base.py

FEATURE_KNOWLEDGE = {
    "age": {
        "question": "You're quite young for this loan amount. Do you have family support or additional assets?",
        "follow_up": "Can you provide proof of additional financial support?",
        "documents": ["Parent/guardian letter of support", "Asset documentation"],
        "actions": ["Add co-signer", "Provide proof of assets", "Reduce loan amount"],
        "explanation": "age is lower than typical approved applicants"
    },
    
    "education_level": {
        "question": "Your education level may affect income stability. Do you have specialized training or certifications?",
        "follow_up": "Can you provide certificates or proof of specialized skills?",
        "documents": ["Education certificates", "Professional certifications", "Training records"],
        "actions": ["Provide proof of additional qualifications", "Show stable employment despite education level"],
        "explanation": "education level is below preferred range"
    },
    
    "employment_type": {
        "question": "Your employment type shows some instability risk. Can you provide more details about job security?",
        "follow_up": "Do you have an employment contract or letter from employer?",
        "documents": ["Employment contract", "Employer verification letter", "Pay stubs"],
        "actions": ["Provide employment contract", "Add employed co-applicant", "Show consistent work history"],
        "explanation": "employment type carries higher risk"
    },
    
    "employment_years": {
        "question": "You've been in your current job for a short time. Have you had consistent employment before?",
        "follow_up": "Can you provide proof of previous stable employment?",
        "documents": ["Previous employment letters", "HR verification", "Work history"],
        "actions": ["Provide industry experience proof", "Wait 6 months and reapply", "Add co-applicant"],
        "explanation": "employment duration is shorter than preferred"
    },
    
    "monthly_income": {
        "question": "Your monthly income appears low relative to the loan request. Do you have additional income sources?",
        "follow_up": "Can you provide proof of additional income?",
        "documents": ["Bank statements (3 months)", "Tax returns", "Side income proof", "Investment income"],
        "actions": ["Document all income sources", "Add co-applicant with income", "Reduce loan amount by 25%"],
        "explanation": "monthly income is below typical range for this loan"
    },
    
    "fixed_monthly_expenses": {
        "question": "Your fixed expenses are high. Can you reduce any recurring costs?",
        "follow_up": "Are there any expenses you can cut or debts to consolidate?",
        "documents": ["Expense breakdown", "Budget plan", "Debt consolidation plan"],
        "actions": ["Reduce discretionary spending", "Consolidate debts", "Cancel unused subscriptions"],
        "explanation": "monthly fixed expenses are high relative to income"
    },
    
    "debt_to_income_ratio": {
        "question": "Your debt-to-income ratio is high. Are any debts close to being paid off?",
        "follow_up": "Can you provide payoff letters or consolidation plan?",
        "documents": ["Current debt statements", "Payoff letters", "Debt consolidation plan"],
        "actions": ["Pay down credit card debt", "Consolidate high-interest debt", "Reduce loan amount by 20%"],
        "explanation": "monthly debt obligations are high relative to income"
    },
    
    "savings_balance": {
        "question": "Your savings are lower than recommended. Do you have other assets or emergency funds?",
        "follow_up": "Can you show other financial reserves or assets?",
        "documents": ["Additional bank statements", "Investment account statements", "Asset documentation"],
        "actions": ["Build savings for 3 months", "Provide proof of other assets", "Add co-applicant with savings"],
        "explanation": "savings cushion is below recommended level"
    },
    
    "loan_amount": {
        "question": "The requested loan amount is high relative to your income. Can you reduce it?",
        "follow_up": "What is the minimum amount you actually need?",
        "documents": ["Revised loan application", "Detailed budget showing necessity"],
        "actions": ["Reduce loan by 20-30%", "Provide collateral", "Add co-borrower with income"],
        "explanation": "requested loan amount is high relative to financial capacity"
    },
    
    "loan_duration_months": {
        "question": "The loan duration you've requested may strain your budget. Can you extend or shorten it?",
        "follow_up": "Have you calculated different payment scenarios?",
        "documents": ["Budget projection", "Payment schedule analysis"],
        "actions": ["Adjust loan term for lower payments", "Reduce loan amount instead", "Show ability to handle payments"],
        "explanation": "loan duration may not align optimally with financial capacity"
    },
    
    "loan_purpose": {
        "question": "Can you provide more details about how you'll use this loan?",
        "follow_up": "Do you have documentation supporting this purpose?",
        "documents": ["Invoices", "Quotes", "Business plan", "Purchase agreement"],
        "actions": ["Provide detailed purpose documentation", "Show how loan improves income", "Demonstrate ROI"],
        "explanation": "loan purpose carries higher risk"
    },
    
    "credit_score": {
        "question": "Your credit score is below preferred levels. Have you had recent financial difficulties?",
        "follow_up": "Can you explain any negative items on your credit report?",
        "documents": ["Credit report", "Explanation letter", "Proof of resolved debts", "Payment plans"],
        "actions": ["Dispute credit report errors", "Pay off collections", "Show recent on-time payments"],
        "explanation": "credit score is below the preferred threshold"
    },
    
    "late_payments_12m": {
        "question": "You have some late payments in the last 12 months. What caused these delays?",
        "follow_up": "Have your circumstances improved since then?",
        "documents": ["Explanation letter", "Recent on-time payment proof", "Employment verification"],
        "actions": ["Show 6 months of on-time payments", "Set up autopay", "Provide circumstantial explanation"],
        "explanation": "recent payment history shows some delays"
    },
    
    "missed_payments_12m": {
        "question": "You missed some payments recently. Were these due to temporary circumstances?",
        "follow_up": "Can you demonstrate improved payment behavior?",
        "documents": ["Explanation letter", "Proof of resolved situation", "Recent payment history"],
        "actions": ["Show improved payment pattern", "Explain one-time circumstances", "Provide guarantor"],
        "explanation": "missed payments in the last year raise concerns"
    },
    
    "utility_bill_on_time_ratio": {
        "question": "Your utility payment history shows some delays. Were there specific circumstances?",
        "follow_up": "Can you show recent on-time payments?",
        "documents": ["Recent utility bills (3 months)", "Payment receipts", "Autopay setup confirmation"],
        "actions": ["Set up autopay for all utilities", "Show 3 months on-time payments", "Provide explanation"],
        "explanation": "utility payment history shows inconsistency"
    },
    
    "income_inflation_ratio": {
        "question": "There's a discrepancy between your stated and expected income. Can you clarify?",
        "follow_up": "Do you have official documentation of your actual income?",
        "documents": ["Official pay stubs", "Tax returns", "Employer letter", "Bank statements"],
        "actions": ["Provide official income documentation", "Explain income variations", "Correct any errors"],
        "explanation": "declared income differs from expected income patterns"
    },
    
    "document_mismatch_flag": {
        "question": "We noticed some inconsistencies in your submitted documents. Can you clarify these?",
        "follow_up": "Can you provide original or certified copies?",
        "documents": ["Original documents", "Certified copies", "Additional verification"],
        "actions": ["Resubmit documents", "Provide additional verification", "Explain discrepancies"],
        "explanation": "submitted documents show some inconsistencies"
    },
    
    "application_velocity": {
        "question": "You've applied for multiple loans recently. Why do you need multiple loans?",
        "follow_up": "Are you in financial distress?",
        "documents": ["Explanation letter", "Financial situation overview", "Debt management plan"],
        "actions": ["Explain multiple applications", "Consolidate loan requests", "Wait before reapplying"],
        "explanation": "high number of recent applications raises concerns"
    },
    
    "geo_location_mismatch": {
        "question": "Your location information shows inconsistencies. Can you clarify your current address?",
        "follow_up": "Do you have utility bills or proof of current residence?",
        "documents": ["Utility bill with current address", "Rental agreement", "ID with current address"],
        "actions": ["Update address information", "Provide residence proof", "Explain relocations"],
        "explanation": "location information shows inconsistencies"
    },
    
    "metadata_anomaly_score": {
        "question": "We detected some unusual patterns in your application. Can you provide additional verification?",
        "follow_up": "Can you come in person for verification?",
        "documents": ["Government ID", "Additional verification documents", "In-person verification"],
        "actions": ["Visit branch for verification", "Provide additional documents", "Verify identity"],
        "explanation": "application metadata shows unusual patterns"
    }
}

# PD improvement estimation rules (approximate percentage point improvements)
PD_IMPROVEMENT_RULES = {
    "debt_to_income_ratio": 0.025,      # 2.5% improvement if fixed
    "monthly_income": 0.020,             # 2% improvement
    "credit_score": 0.020,               # 2% improvement
    "employment_years": 0.015,           # 1.5% improvement
    "savings_balance": 0.015,            # 1.5% improvement
    "late_payments_12m": 0.015,          # 1.5% improvement
    "missed_payments_12m": 0.020,        # 2% improvement
    "utility_bill_on_time_ratio": 0.010, # 1% improvement
    "loan_amount": 0.020,                # 2% improvement if reduced
    "fixed_monthly_expenses": 0.010,     # 1% improvement
    "document_mismatch_flag": 0.015,     # 1.5% if resolved
    "application_velocity": 0.010,       # 1% improvement
    "income_inflation_ratio": 0.015,     # 1.5% if corrected
    "age": 0.005,                        # 0.5% (harder to change)
    "education_level": 0.008,            # 0.8%
    "employment_type": 0.012,            # 1.2%
    "loan_duration_months": 0.008,       # 0.8%
    "loan_purpose": 0.010,               # 1%
    "geo_location_mismatch": 0.012,      # 1.2%
    "metadata_anomaly_score": 0.015      # 1.5%
}
