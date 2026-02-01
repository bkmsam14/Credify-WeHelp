# loan_model.py - LoanModel wrapper class

import pandas as pd

class LoanModel:
    """Wrapper class for loan approval model with integrated preprocessing"""
    
    def __init__(self, model, scaler, feature_names):
        self.model = model
        self.scaler = scaler
        self.feature_names = feature_names
    
    def predict_proba(self, X):
        """Predict probability - works with raw features"""
        if isinstance(X, pd.DataFrame):
            X = X[self.feature_names].values
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
    
    def predict(self, X):
        """Predict class - works with raw features"""
        if isinstance(X, pd.DataFrame):
            X = X[self.feature_names].values
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
