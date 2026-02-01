
import sys
import os
import pandas as pd
import pickle
import numpy as np

# Mock Streamlit for CLI run
class MockSt:
    def error(self, msg):
        print(f"ERROR: {msg}")

sys.modules['streamlit'] = MockSt()

# Add root
sys.path.append(os.getcwd())

try:
    from core.lime_explainer import LoanLimeExplainer
    
    print("Core modules imported.")
    
    model_path = 'models/loan_model.pkl'
    data_path = 'data/training_data.csv'
    
    if not os.path.exists(model_path):
        print(f"Model not found at {model_path}")
    if not os.path.exists(data_path):
        print(f"Data not found at {data_path}")
        
    print("Initializing Explainer...")
    explainer = LoanLimeExplainer(model_path, data_path)
    print("Explainer initialized successfully.")
    
    # Test explanation
    customer_data = {
        "age": 34,
        "education_level": 2,
        "employment_type": 1,
        "employment_years": 6,
        "monthly_income": 2800,
        "fixed_monthly_expenses": 1200,
        "debt_to_income_ratio": 0.32,
        "savings_balance": 5000,
        "loan_amount": 12000,
        "loan_duration_months": 36,
        "loan_purpose": 1,
        "credit_score": 680,
        "late_payments_12m": 1,
        "missed_payments_12m": 0,
        "utility_bill_on_time_ratio": 0.8,
        "income_inflation_ratio": 1.0, 
        "document_mismatch_flag": 0,
        "application_velocity": 1,
        "geo_location_mismatch": 0,
        "metadata_anomaly_score": 0.1
    }
    
    print("Generating explanation...")
    exp = explainer.explain(customer_data)
    print("Explanation generated.")
    
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
