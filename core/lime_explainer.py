# lime_explainer.py

import pickle
import pandas as pd
import numpy as np
from lime.lime_tabular import LimeTabularExplainer

class LoanLimeExplainer:
    def __init__(self, model_path, training_data_path):
        """Initialize LIME explainer"""
        
        # Load model
        print("Loading model...")
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        
        # Load training data
        print("Loading training data...")
        df = pd.read_csv(training_data_path)
        
        # Get feature names (exclude target columns)
        target_cols = ['is_fraud', 'loan_approved']
        self.feature_names = [col for col in df.columns if col not in target_cols]
        
        # Prepare training data for LIME
        self.training_data = df[self.feature_names].values
        
        print(f"Features: {self.feature_names}")
        print(f"Training data shape: {self.training_data.shape}")
        
        # Create LIME explainer
        self.explainer = LimeTabularExplainer(
            training_data=self.training_data,
            feature_names=self.feature_names,
            class_names=['Rejected', 'Approved'],
            mode='classification',
            discretize_continuous=False
        )
    
    def explain(self, customer_features, num_features=15):
        """
        Generate LIME explanation for one customer
        
        Args:
            customer_features: dict like {"age": 25, "monthly_income": 45000, ...}
            num_features: how many features to explain
            
        Returns:
            list of dicts: [{"feature": "monthly_income", "contribution": -0.08}, ...]
        """
        
        # Convert dict to array in correct order
        feature_array = np.array([customer_features.get(f, 0) for f in self.feature_names])
        
        print(f"Explaining instance with features: {feature_array[:5]}...")
        
        # Generate LIME explanation
        exp = self.explainer.explain_instance(
            feature_array,
            self.model.predict_proba,
            num_features=num_features
        )
        
        # Convert to simple format
        lime_features = []
        explanation_list = exp.as_list()
        
        for feature_desc, contribution in explanation_list:
            # Extract clean feature name
            # LIME returns things like "monthly_income <= 50000.00"
            feature_name = feature_desc.split()[0] if ' ' in feature_desc else feature_desc
            
            lime_features.append({
                "feature": feature_name,
                "contribution": contribution,
                "description": feature_desc
            })
        
        # Sort by absolute contribution (most important first)
        lime_features.sort(key=lambda x: abs(x['contribution']), reverse=True)
        
        print(f"Top 3 features: {[(f['feature'], f['contribution']) for f in lime_features[:3]]}")
        
        return lime_features
