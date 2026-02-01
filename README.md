# WeHelp 3.0 - Loan Decision Intelligence System

A decision intelligence system for analyzing borderline loan applications using LIME explainability and knowledge-based recommendations.

## 📁 Project Structure

```
wehelp-3.0-organized/
├── core/                          # Core modules
│   ├── __init__.py
│   ├── loan_model.py              # LoanModel wrapper class
│   ├── knowledge_base.py          # Feature knowledge and improvement rules
│   ├── lime_explainer.py          # LIME explainer wrapper
│   └── borderline_advisor.py      # Decision intelligence advisor
├── scripts/                       # Utility scripts
│   └── create_dummy_data.py       # Generate training data and model
├── data/                          # Data files (generated)
│   └── training_data.csv          # Training dataset
├── models/                        # Trained models (generated)
│   └── loan_model.pkl             # Pickled loan approval model
├── outputs/                       # Generated outputs
│   └── test_output.json           # Test results
├── test_system.py                 # Main test script
├── README.md                      # This file
└── .gitignore                     # Git ignore file
```

## 🚀 Setup

### 1. Install Required Libraries

```bash
pip install pandas numpy scikit-learn lime
```

### 2. Generate Training Data and Model

```bash
cd scripts
python create_dummy_data.py
```

This will create:
- `data/training_data.csv` - 1000 synthetic loan applications
- `models/loan_model.pkl` - Trained logistic regression model

### 3. Run the Test System

```bash
python test_system.py
```

## 📚 Modules

### Core Modules

- **`loan_model.py`**: Wrapper class for the loan approval model with integrated preprocessing
- **`knowledge_base.py`**: Contains feature explanations, interview questions, document requirements, and improvement rules
- **`lime_explainer.py`**: LIME-based explainability for model predictions
- **`borderline_advisor.py`**: Generates recommendations for borderline loan applications

### Scripts

- **`create_dummy_data.py`**: Generates synthetic training data and trains the model

### Main Script

- **`test_system.py`**: End-to-end test of the decision intelligence system

## 🎯 Features

- **LIME Explainability**: Understand which features contribute to borderline decisions
- **Interview Questions**: Automatically generated questions based on risk factors
- **Document Requests**: Smart document collection based on identified issues
- **Improvement Actions**: Actionable recommendations categorized by feasibility
- **PD Improvement Estimates**: Projected probability of default improvement

## 📊 Output

The system generates:
1. **Recommendation**: MANUAL_REVIEW, REJECT, or APPROVE
2. **Explanation**: Human-readable reason for borderline status
3. **Interview Questions**: 5-7 targeted questions with follow-ups
4. **Documents Needed**: 4-6 specific documents to request
5. **Improvement Actions**: 6 actions categorized as immediate/short-term/long-term
6. **PD Improvement Estimate**: Current vs. potential PD after improvements

## 🔧 Customization

- Modify `knowledge_base.py` to adjust questions, documents, and improvement rules
- Update `PD_IMPROVEMENT_RULES` to change impact estimates
- Adjust thresholds in `create_dummy_data.py` for different approval criteria

## 📝 License

This is a demonstration project for loan decision intelligence.
