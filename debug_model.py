
import pickle
import sys
import pandas as pd

try:
    with open('models/loan_model.pkl', 'rb') as f:
        model = pickle.load(f)
    
    print("Model loaded successfully")
    print("Model type:", type(model))
    if hasattr(model, 'feature_names'):
        print("Feature names:", model.feature_names)
    else:
        print("Model has no feature_names attribute")

except Exception as e:
    print(f"Error loading model: {e}")
