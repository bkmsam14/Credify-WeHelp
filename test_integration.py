"""
Quick test to verify the integrated backend works
"""
import requests
import json

# Test data
test_application = {
    "age": 28,
    "education_level": 2,
    "employment_type": 1,
    "employment_years": 3,
    "monthly_income": 1800,
    "fixed_monthly_expenses": 700,
    "debt_to_income_ratio": 0.25,
    "savings_balance": 1200,
    "loan_amount": 4000,
    "loan_duration_months": 18,
    "loan_purpose": 3,
    "credit_score": 650,
    "late_payments_12m": 1,
    "missed_payments_12m": 0,
    "utility_bill_on_time_ratio": 0.9,
    "income_inflation_ratio": 1.0,
    "document_mismatch_flag": 0,
    "application_velocity": 1,
    "geo_location_mismatch": 0,
    "metadata_anomaly_score": 0.1,
    "is_fraud": 0
}

# Test the backend
try:
    response = requests.post(
        "http://localhost:8001/api/analyze",
        json=test_application,
        timeout=10
    )
    
    if response.status_code == 200:
        print("✅ SUCCESS! Backend is working")
        result = response.json()
        print("\nResponse:")
        print(json.dumps(result, indent=2))
    else:
        print(f"❌ ERROR: Status code {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("❌ ERROR: Cannot connect to backend at http://localhost:8001")
    print("Make sure the backend is running: python api.py")
except Exception as e:
    print(f"❌ ERROR: {e}")
