# create_dummy_data.py - Creates dummy model and dataset

import pandas as pd
import os
import numpy as np
import pickle
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import sys
sys.path.append('..')
from core.loan_model import LoanModel

print("Creating dummy loan approval dataset and model...")

# Set random seed for reproducibility
np.random.seed(42)

# Number of samples
n_samples = 1000

# Feature names
feature_names = [
    'age',
    'education_level',
    'employment_type',
    'employment_years',
    'monthly_income',
    'fixed_monthly_expenses',
    'debt_to_income_ratio',
    'savings_balance',
    'loan_amount',
    'loan_duration_months',
    'loan_purpose',
    'credit_score',
    'late_payments_12m',
    'missed_payments_12m',
    'utility_bill_on_time_ratio',
    'income_inflation_ratio',
    'document_mismatch_flag',
    'application_velocity',
    'geo_location_mismatch',
    'metadata_anomaly_score'
]

# Generate realistic dummy data
data = {
    # Personal
    'age': np.random.randint(18, 65, n_samples),
    'education_level': np.random.choice([0, 1, 2, 3], n_samples),  # 0=no degree, 1=high school, 2=bachelor, 3=master+
    
    # Employment
    'employment_type': np.random.choice([0, 1, 2, 3], n_samples),  # 0=unemployed, 1=part-time, 2=full-time, 3=self-employed
    'employment_years': np.random.uniform(0, 20, n_samples),
    
    # Income and Expenses
    'monthly_income': np.random.uniform(20000, 150000, n_samples),
    'fixed_monthly_expenses': np.random.uniform(10000, 100000, n_samples),
    'debt_to_income_ratio': np.random.uniform(0.1, 0.8, n_samples),
    'savings_balance': np.random.uniform(0, 500000, n_samples),
    
    # Loan details
    'loan_amount': np.random.uniform(10000, 500000, n_samples),
    'loan_duration_months': np.random.choice([12, 24, 36, 48, 60], n_samples),
    'loan_purpose': np.random.choice([0, 1, 2, 3, 4], n_samples),  # 0=personal, 1=business, 2=education, 3=home, 4=vehicle
    
    # Credit history
    'credit_score': np.random.randint(300, 850, n_samples),
    'late_payments_12m': np.random.randint(0, 10, n_samples),
    'missed_payments_12m': np.random.randint(0, 5, n_samples),
    'utility_bill_on_time_ratio': np.random.uniform(0.5, 1.0, n_samples),
    
    # Fraud signals
    'income_inflation_ratio': np.random.uniform(0.8, 1.5, n_samples),
    'document_mismatch_flag': np.random.choice([0, 1], n_samples, p=[0.9, 0.1]),
    'application_velocity': np.random.randint(1, 10, n_samples),
    'geo_location_mismatch': np.random.choice([0, 1], n_samples, p=[0.95, 0.05]),
    'metadata_anomaly_score': np.random.uniform(0, 1, n_samples)
}

# Create DataFrame
df = pd.DataFrame(data)

# Generate target variable (loan_approved) based on logical rules
# This creates a realistic approval pattern
df['loan_approved'] = 1  # Start with all approved

# Rejection rules (logical)
df.loc[df['debt_to_income_ratio'] > 0.6, 'loan_approved'] = 0
df.loc[df['credit_score'] < 500, 'loan_approved'] = 0
df.loc[df['missed_payments_12m'] > 3, 'loan_approved'] = 0
df.loc[df['employment_years'] < 0.5, 'loan_approved'] = 0
df.loc[(df['monthly_income'] < 30000) & (df['loan_amount'] > 100000), 'loan_approved'] = 0
df.loc[df['document_mismatch_flag'] == 1, 'loan_approved'] = 0
df.loc[df['utility_bill_on_time_ratio'] < 0.6, 'loan_approved'] = 0

# Add some borderline cases
borderline_mask = (
    (df['debt_to_income_ratio'] > 0.45) & (df['debt_to_income_ratio'] <= 0.6) |
    (df['credit_score'] >= 500) & (df['credit_score'] < 600) |
    (df['employment_years'] >= 0.5) & (df['employment_years'] < 2)
)
df.loc[borderline_mask, 'loan_approved'] = np.random.choice([0, 1], borderline_mask.sum(), p=[0.4, 0.6])

# Add fraud label
df['is_fraud'] = 0
df.loc[df['document_mismatch_flag'] == 1, 'is_fraud'] = 1
df.loc[df['geo_location_mismatch'] == 1, 'is_fraud'] = 1
df.loc[df['income_inflation_ratio'] > 1.3, 'is_fraud'] = 1
df.loc[df['metadata_anomaly_score'] > 0.8, 'is_fraud'] = 1

print(f"Dataset shape: {df.shape}")
print(f"Approval rate: {df['loan_approved'].mean():.2%}")
print(f"Fraud rate: {df['is_fraud'].mean():.2%}")

# Save dataset
os.makedirs('../data', exist_ok=True)
df.to_csv('../data/training_data.csv', index=False)
print("✅ Saved training_data.csv")

# Train a logistic regression model
print("\nTraining logistic regression model...")

X = df[feature_names]
y = df['loan_approved']

# Standardize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train model
model = LogisticRegression(random_state=42, max_iter=1000)
model.fit(X_scaled, y)

# Check model performance
train_score = model.score(X_scaled, y)
print(f"Model training accuracy: {train_score:.2%}")

# Wrap the model
wrapped_model = LoanModel(model, scaler, feature_names)

# Save model
os.makedirs('../models', exist_ok=True)
with open('../models/loan_model.pkl', 'wb') as f:
    pickle.dump(wrapped_model, f)

print("✅ Saved loan_model.pkl")

# Test the model
print("\nTesting model with a sample case...")
test_case = df.iloc[0:1][feature_names]
prob = wrapped_model.predict_proba(test_case)
print(f"Test prediction - Approval probability: {prob[0][1]:.2%}")

# Create some test cases
print("\n=== Creating Test Cases ===")

# Borderline case 1: High DTI
borderline_1 = df[(df['debt_to_income_ratio'] > 0.45) & (df['debt_to_income_ratio'] < 0.55)].iloc[0:1].copy()
prob_1 = wrapped_model.predict_proba(borderline_1[feature_names])
print(f"\nBorderline Case 1 (High DTI): PD = {prob_1[0][1]:.2%}")
print(f"  DTI: {borderline_1['debt_to_income_ratio'].values[0]:.2f}")
print(f"  Income: {borderline_1['monthly_income'].values[0]:.0f}")

# Borderline case 2: Low credit score
borderline_2 = df[(df['credit_score'] > 550) & (df['credit_score'] < 620)].iloc[0:1].copy()
prob_2 = wrapped_model.predict_proba(borderline_2[feature_names])
print(f"\nBorderline Case 2 (Low Credit): PD = {prob_2[0][1]:.2%}")
print(f"  Credit Score: {borderline_2['credit_score'].values[0]:.0f}")
print(f"  Employment Years: {borderline_2['employment_years'].values[0]:.1f}")

# Borderline case 3: Short employment
borderline_3 = df[(df['employment_years'] > 0.5) & (df['employment_years'] < 1.5)].iloc[0:1].copy()
prob_3 = wrapped_model.predict_proba(borderline_3[feature_names])
print(f"\nBorderline Case 3 (Short Employment): PD = {prob_3[0][1]:.2%}")
print(f"  Employment Years: {borderline_3['employment_years'].values[0]:.1f}")
print(f"  Age: {borderline_3['age'].values[0]:.0f}")

print("\n✅ DUMMY DATA CREATION COMPLETE!")
print("\nYou can now run the test system with:")
print("  python test_system.py")
