
import sys
import os
import pickle
import pandas as pd

# Add root to path
sys.path.append(os.getcwd())

from core.loan_model import LoanModel

def verify_logic():
    print("Loading model...")
    try:
        with open('models/loan_model.pkl', 'rb') as f:
            model = pickle.load(f)
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    # Data from app.py
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
    
    print("Preparing input...")
    input_df = pd.DataFrame([customer_data])
    
    print("Running prediction...")
    try:
        prob = model.predict_proba(input_df)[0][1]
        pd_score = 1 - prob
        print(f"Prediction successful.")
        print(f"Probability of Approval: {prob:.4f}")
        print(f"Probability of Default: {pd_score:.4f}")
    except Exception as e:
        print(f"Prediction failed: {e}")

if __name__ == "__main__":
    verify_logic()
