# test_system.py - Test the complete decision intelligence system

import json
import pandas as pd
from core.lime_explainer import LoanLimeExplainer
from core.borderline_advisor import analyze_borderline_application

print("="*60)
print("LOAN DECISION INTELLIGENCE - TEST SYSTEM")
print("="*60)

# Initialize LIME
print("\n[1/4] Initializing LIME explainer...")
explainer = LoanLimeExplainer(
    model_path='models/loan_model.pkl',
    training_data_path='data/training_data.csv'
)

# Load a real borderline case from the dataset
print("\n[2/4] Loading a borderline test case...")
df = pd.read_csv('data/training_data.csv')

# Find a borderline case (high DTI, moderate credit score)
borderline_cases = df[
    (df['debt_to_income_ratio'] > 0.45) & 
    (df['debt_to_income_ratio'] < 0.55) &
    (df['credit_score'] > 550) &
    (df['credit_score'] < 650)
]

if len(borderline_cases) == 0:
    print("No perfect borderline case found, using first available...")
    test_row = df.iloc[10]
else:
    test_row = borderline_cases.iloc[0]

# Convert to dictionary
test_customer = test_row[explainer.feature_names].to_dict()

print(f"\nTest Customer Profile:")
print(f"  Age: {test_customer['age']:.0f}")
print(f"  Monthly Income: {test_customer['monthly_income']:.0f}")
print(f"  DTI Ratio: {test_customer['debt_to_income_ratio']:.2f}")
print(f"  Credit Score: {test_customer['credit_score']:.0f}")
print(f"  Employment Years: {test_customer['employment_years']:.1f}")
print(f"  Loan Amount: {test_customer['loan_amount']:.0f}")

# Get actual PD from model
import pickle
with open('models/loan_model.pkl', 'rb') as f:
    model = pickle.load(f)

feature_df = pd.DataFrame([test_customer])
prob = model.predict_proba(feature_df)
pd_score = 1 - prob[0][1]  # Probability of default = 1 - probability of approval

print(f"\nModel PD Score: {pd_score*100:.1f}%")

# Fraud flags (simulate)
fraud_flags = {
    "severity": "soft" if test_customer['document_mismatch_flag'] == 1 else "none",
    "details": "Minor document inconsistency detected" if test_customer['document_mismatch_flag'] == 1 else ""
}

print("\n[3/4] Generating LIME explanations...")
lime_features = explainer.explain(test_customer, num_features=15)

print("\n📊 Top 5 LIME Features:")
for i, f in enumerate(lime_features[:5], 1):
    direction = "↓ NEGATIVE" if f['contribution'] < 0 else "↑ POSITIVE"
    print(f"  {i}. {f['feature']:<30} {f['contribution']:>7.4f}  {direction}")

print("\n[4/4] Running decision intelligence analysis...")
result = analyze_borderline_application(
    pd_score=pd_score,
    lime_features=lime_features,
    fraud_flags=fraud_flags
)

print("\n" + "="*60)
print("DECISION INTELLIGENCE OUTPUT")
print("="*60)

print(f"\n📋 RECOMMENDATION: {result['recommendation']}")

print(f"\n💡 EXPLANATION:")
print(f"   {result['explanation']}")

print(f"\n❓ INTERVIEW QUESTIONS ({len(result['interview_questions'])}):")
for q in result['interview_questions']:
    print(f"   {q['order']}. {q['question']}")
    print(f"      → Follow-up: {q['follow_up']}")
    print()

print(f"📄 DOCUMENTS NEEDED ({len(result['documents_needed'])}):")
for i, doc in enumerate(result['documents_needed'], 1):
    print(f"   {i}. {doc}")

print(f"\n✅ IMPROVEMENT ACTIONS ({len(result['improvement_actions'])}):")
for action in result['improvement_actions']:
    print(f"   • [{action['feasibility'].upper()}] {action['action']}")

print(f"\n📈 PD IMPROVEMENT ESTIMATE:")
print(f"   Current PD:    {result['pd_improvement_estimate']['current_pd']}")
print(f"   Potential PD:  {result['pd_improvement_estimate']['potential_pd']}")
print(f"   Improvement:   {result['pd_improvement_estimate']['improvement']}")
print(f"   Note: {result['pd_improvement_estimate']['note']}")

print("\n" + "="*60)
print("✅ TEST COMPLETE - SYSTEM WORKING!")
print("="*60)

# Save full output to JSON
import os
os.makedirs('outputs', exist_ok=True)
with open('outputs/test_output.json', 'w') as f:
    json.dump(result, f, indent=2)

print("\n💾 Full output saved to: outputs/test_output.json")
