import streamlit as st
import pandas as pd
import pickle
import sys
import os

# Add root directory to path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import core modules
from core.loan_model import LoanModel
from core.lime_explainer import LoanLimeExplainer
from ui.components.documents_panel import render_documents_panel


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="AI Credit Risk Tool",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# CACHED RESOURCES
# =========================
@st.cache_resource
def load_model():
    try:
        with open('models/loan_model.pkl', 'rb') as f:
            model = pickle.load(f)
        return model
    except Exception as e:
        st.error(f"Error loading model: {str(e)}")
        return None

@st.cache_resource
def load_explainer():
    try:
        # Check if explainer supports the current model structure
        # For now, we'll initialize a fresh one if needed or just load the class
        explainer = LoanLimeExplainer('models/loan_model.pkl', 'data/training_data.csv')
        return explainer
    except Exception as e:
        st.error(f"Error loading explainer: {str(e)}")
        return None

# Load resources
model = load_model()
explainer = load_explainer()

# Initialize session state for prediction results if not exists
if 'prediction_result' not in st.session_state:
    st.session_state.prediction_result = None
if 'explanation' not in st.session_state:
    st.session_state.explanation = None


# =========================
# ENTERPRISE BANKING THEME
# =========================
st.markdown("""
<style>
/* ===== IMPORTS ===== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ===== BASE STYLES ===== */
.stApp {
    background-color: #F8F9FA;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ===== TYPOGRAPHY ===== */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #1a1a2e;
    font-weight: 600;
}

p, span, div {
    color: #374151;
}

/* ===== HEADER STYLING ===== */
.main-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    padding: 1.5rem 2rem;
    margin: -1rem -1rem 2rem -1rem;
    border-bottom: 3px solid #0f3460;
}

.main-header h1 {
    color: #FFFFFF;
    font-size: 1.5rem;
    font-weight: 600;
    margin: 0;
    letter-spacing: -0.025em;
}

.main-header .subtitle {
    color: #94a3b8;
    font-size: 0.875rem;
    font-weight: 400;
    margin-top: 0.25rem;
}

/* ===== SIDEBAR STYLING ===== */
[data-testid="stSidebar"] {
    background-color: #1a1a2e;
    border-right: 1px solid #2d2d44;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
    color: #e2e8f0;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #FFFFFF;
    font-weight: 500;
}

[data-testid="stSidebar"] .stRadio > label {
    color: #e2e8f0;
}

[data-testid="stSidebar"] .stRadio > div {
    background-color: transparent;
}

[data-testid="stSidebar"] .stRadio > div > label {
    background-color: transparent;
    color: #cbd5e1;
    padding: 0.75rem 1rem;
    border-radius: 6px;
    margin-bottom: 0.25rem;
    transition: all 0.15s ease;
}

[data-testid="stSidebar"] .stRadio > div > label:hover {
    background-color: #2d2d44;
    color: #FFFFFF;
}

[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
    background-color: #0f3460;
    color: #FFFFFF;
    border-left: 3px solid #3b82f6;
}

/* ===== CARD STYLING ===== */
.card {
    background-color: #FFFFFF;
    padding: 1.5rem;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.card-header {
    font-size: 0.875rem;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid #f3f4f6;
}

.card p {
    margin: 0.5rem 0;
    color: #374151;
    font-size: 0.9375rem;
    line-height: 1.6;
}

.card strong {
    color: #1f2937;
    font-weight: 500;
}

/* ===== METRICS STYLING ===== */
[data-testid="stMetricValue"] {
    font-family: 'Inter', sans-serif;
    font-size: 1.75rem;
    font-weight: 600;
    color: #1a1a2e;
}

[data-testid="stMetricLabel"] {
    font-size: 0.8125rem;
    font-weight: 500;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.025em;
}

/* Metric Cards */
.metric-card {
    background: #FFFFFF;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 1.25rem;
    text-align: center;
}

.metric-card.risk-low {
    border-left: 4px solid #059669;
}

.metric-card.risk-medium {
    border-left: 4px solid #d97706;
}

.metric-card.risk-high {
    border-left: 4px solid #dc2626;
}

/* ===== STATUS BADGES ===== */
.status-badge {
    display: inline-flex;
    align-items: center;
    padding: 0.375rem 0.875rem;
    border-radius: 4px;
    font-size: 0.8125rem;
    font-weight: 500;
    letter-spacing: 0.01em;
}

.status-approved {
    background-color: #ecfdf5;
    color: #047857;
    border: 1px solid #a7f3d0;
}

.status-review {
    background-color: #fffbeb;
    color: #b45309;
    border: 1px solid #fde68a;
}

.status-rejected {
    background-color: #fef2f2;
    color: #b91c1c;
    border: 1px solid #fecaca;
}

/* ===== ALERT STYLING ===== */
.alert-banner {
    background-color: #fffbeb;
    border: 1px solid #fde68a;
    border-left: 4px solid #d97706;
    border-radius: 6px;
    padding: 1rem 1.25rem;
    margin: 1rem 0;
}

.alert-banner-title {
    font-weight: 600;
    color: #92400e;
    font-size: 0.9375rem;
    margin-bottom: 0.25rem;
}

.alert-banner-text {
    color: #a16207;
    font-size: 0.875rem;
}

/* ===== BUTTON STYLING ===== */
.stButton > button {
    background-color: #1a1a2e;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1.25rem;
    font-weight: 500;
    font-size: 0.875rem;
    transition: all 0.15s ease;
}

.stButton > button:hover {
    background-color: #0f3460;
    border: none;
}

.stButton > button:active {
    background-color: #16213e;
}

/* Secondary Button Style */
.secondary-btn > button {
    background-color: #FFFFFF;
    color: #374151;
    border: 1px solid #d1d5db;
}

.secondary-btn > button:hover {
    background-color: #f9fafb;
    color: #1f2937;
    border: 1px solid #9ca3af;
}

/* ===== CHECKBOX STYLING ===== */
.stCheckbox > label {
    color: #374151;
    font-size: 0.9375rem;
}

/* ===== DIVIDER STYLING ===== */
hr {
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 1.5rem 0;
}

/* ===== AUDIT LOG STYLING ===== */
.audit-log {
    background-color: #FFFFFF;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 1.5rem;
    font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
}

.audit-row {
    display: flex;
    padding: 0.625rem 0;
    border-bottom: 1px solid #f3f4f6;
    font-size: 0.875rem;
}

.audit-row:last-child {
    border-bottom: none;
}

.audit-label {
    width: 180px;
    color: #6b7280;
    font-weight: 500;
}

.audit-value {
    color: #1f2937;
    flex: 1;
}

/* ===== EXPLAINABILITY STYLING ===== */
.explainability-section {
    background-color: #FFFFFF;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}

.explainability-header {
    font-size: 0.8125rem;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 1rem;
}

.risk-item {
    display: flex;
    align-items: flex-start;
    padding: 0.75rem 0;
    border-bottom: 1px solid #f3f4f6;
}

.risk-item:last-child {
    border-bottom: none;
}

.risk-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 0.75rem;
    margin-top: 0.375rem;
    flex-shrink: 0;
}

.risk-indicator.negative {
    background-color: #dc2626;
}

.risk-indicator.positive {
    background-color: #059669;
}

.risk-indicator.neutral {
    background-color: #6b7280;
}

.risk-text {
    color: #374151;
    font-size: 0.9375rem;
    line-height: 1.5;
}

/* ===== DOCUMENT LIST STYLING ===== */
.document-item {
    display: flex;
    align-items: center;
    padding: 0.75rem 0;
    border-bottom: 1px solid #f3f4f6;
    font-size: 0.9375rem;
    color: #374151;
}

.document-item:last-child {
    border-bottom: none;
}

.document-check {
    color: #059669;
    margin-right: 0.75rem;
    font-weight: 600;
}

/* ===== HIDE STREAMLIT BRANDING ===== */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ===== RESPONSIVE ADJUSTMENTS ===== */
@media (max-width: 768px) {
    .card {
        padding: 1rem;
    }

    .main-header {
        padding: 1rem;
    }

    .main-header h1 {
        font-size: 1.25rem;
    }
}
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown("""
<div class="main-header">
    <h1>AI-Assisted Credit Decision Tool</h1>
    <div class="subtitle">Internal Decision Support System</div>
</div>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR NAVIGATION
# =========================
with st.sidebar:
    st.markdown("### Navigation")

    section = st.radio(
        "Select module",
        [
            "Application Overview",
            "Documents & Consent",
            "Risk & Decision",
            "Explainability",
            "Audit Log"
        ],
        label_visibility="collapsed"
    )

# =========================
# CARD HELPER
# =========================
def card(title, content):
    st.markdown(f"""
    <div class="card">
        <div class="card-header">{title}</div>
        {content}
    </div>
    """, unsafe_allow_html=True)

# =========================
# APPLICATION OVERVIEW
# =========================
if section == "Application Overview":
    col1, col2 = st.columns(2)

    with col1:
        card("Customer Profile", """
            <p><strong>Age:</strong> 34</p>
            <p><strong>Education Level:</strong> University</p>
            <p><strong>Employment Type:</strong> Salaried</p>
            <p><strong>Employment Years:</strong> 6</p>
            <p><strong>Monthly Income:</strong> 2,800 TND</p>
        """)

    with col2:
        card("Loan Request", """
            <p><strong>Loan Amount:</strong> 12,000 TND</p>
            <p><strong>Duration:</strong> 36 months</p>
            <p><strong>Purpose:</strong> Personal</p>
            <p><strong>Debt-to-Income Ratio:</strong> 32%</p>
        """)

# =========================
# DOCUMENTS & CONSENT
# =========================
elif section == "Documents & Consent":
    # Define required documents based on rules (mock logic for now)
    required_docs = [
        "National ID (Verified)",
        "Payslip (Verified)", 
        "STEG Bill (Verified)",
        "SONEDE Bill (Verified)",
        "D17 Mobile Money Statement (Verified)"
    ]
    
    # Use the new component
    render_documents_panel(required_docs)


    st.checkbox("Customer consent verified", value=True)
    st.checkbox("Documents validated by system", value=True)

# =========================
# RISK & DECISION
# =========================
    # Prepare customer data for prediction
    # Mapping hardcoded values to features expected by model (best guess approximations for categorical)
    customer_data = {
        "age": 34,
        "education_level": 2,  # Assuming 2 is University
        "employment_type": 1,  # Assuming 1 is Salaried
        "employment_years": 6,
        "monthly_income": 2800,
        "fixed_monthly_expenses": 1200, # Estimated
        "debt_to_income_ratio": 0.32,
        "savings_balance": 5000, # Estimated
        "loan_amount": 12000,
        "loan_duration_months": 36,
        "loan_purpose": 1, # Assuming 1 is Personal
        "credit_score": 680, # Estimated
        "late_payments_12m": 1, # From risk section text
        "missed_payments_12m": 0,
        "utility_bill_on_time_ratio": 0.8, # Explanation mentions late utility bills
        "income_inflation_ratio": 1.0, 
        "document_mismatch_flag": 0,
        "application_velocity": 1,
        "geo_location_mismatch": 0,
        "metadata_anomaly_score": 0.1
    }

    if st.button("Run Credit Decision"):
        if model:
            with st.spinner("Analyzing credit risk..."):
                # Make prediction
                # Create DataFrame for prediction to match feature names
                input_df = pd.DataFrame([customer_data])
                
                # Get probability
                prob = model.predict_proba(input_df)[0][1] # Probability of Approval? Or Default?
                # Usually loan models predict Default (1) or Approval (1)? 
                # Let's assume class 1 is "Approved" based on common logic, or check code.
                # loan_model.py says: class_names=['Rejected', 'Approved']
                # So index 1 is Approved. 
                # But wait, the metric was "Probability of Default". 
                # If model predicts Approval, then PD = 1 - Prob(Approved).
                
                pd_score = 1 - prob # Probability of Default
                
                # Risk Band Logic
                risk_band = "Medium"
                if pd_score < 0.05:
                    risk_band = "Low"
                elif pd_score > 0.15:
                    risk_band = "High"
                
                # Fraud Check
                fraud_flag = "No" # Determine from is_fraud model if available, or heuristic
                if customer_data.get("metadata_anomaly_score", 0) > 0.8:
                    fraud_flag = "Check"
                
                # Store results
                st.session_state.prediction_result = {
                    "pd": pd_score,
                    "risk_band": risk_band,
                    "fraud": fraud_flag,
                    "approved": prob > 0.6 # Threshold
                }
                
                # Generate explanation
                if explainer:
                    exp = explainer.explain(customer_data)
                    st.session_state.explanation = exp
                
                st.rerun()
        else:
            st.error("Model not loaded.")

    # Display Results
    if st.session_state.prediction_result:
        res = st.session_state.prediction_result
        
        col1, col2, col3 = st.columns(3)
        
        risk_color = "#d97706" # Medium/Orange
        if res['risk_band'] == "Low": risk_color = "#059669"
        if res['risk_band'] == "High": risk_color = "#dc2626"

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.75rem; font-weight: 600; color: #6b7280; text-transform: uppercase;">Probability of Default</div>
                <div style="font-size: 1.75rem; font-weight: 600; color: {risk_color};">{res['pd']:.1%}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.75rem; font-weight: 600; color: #6b7280; text-transform: uppercase;">Risk Band</div>
                <div style="font-size: 1.75rem; font-weight: 600; color: {risk_color};">{res['risk_band']}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            fraud_color = "#059669" if res['fraud'] == "No" else "#dc2626"
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.75rem; font-weight: 600; color: #6b7280; text-transform: uppercase;">Fraud Flag</div>
                <div style="font-size: 1.75rem; font-weight: 600; color: {fraud_color};">{res['fraud']}</div>
            </div>
            """, unsafe_allow_html=True)

        # Decision Logic Display
        if res['approved']:
             st.success("✅ Application Recommended for Approval")
        else:
             st.warning("⚠️ Application Requires Manual Review or Rejection")
             
        card("System Decision Summary", f"""
            <div class="risk-item">
                <div class="risk-indicator" style="background-color: {risk_color};"></div>
                <div class="risk-text">Application falls into the <strong>{res['risk_band']} risk band</strong></div>
            </div>
            <div class="risk-item">
                <div class="risk-indicator {'positive' if res['approved'] else 'negative'}"></div>
                <div class="risk-text">Automatic approval is <strong>{'Granted' if res['approved'] else 'Not Granted'}</strong></div>
            </div>
        """)
    else:
        st.info("Click 'Run Credit Decision' to analyze the application.")


# =========================
# EXPLAINABILITY
# =========================
elif section == "Explainability":
    if 'explanation' in st.session_state and st.session_state.explanation:
        lime_feat = st.session_state.explanation
        
        # Split into positive and negative contributors
        # In LIME: positive contribution means pushing towards class 1 (Approved).
        # Negative contribution means pushing towards class 0 (Rejected).
        
        neg_contributors = [f for f in lime_feat if f['contribution'] < 0]
        pos_contributors = [f for f in lime_feat if f['contribution'] > 0]
        
        # Sort by magnitude
        neg_contributors.sort(key=lambda x: x['contribution']) # Most negative first
        pos_contributors.sort(key=lambda x: x['contribution'], reverse=True) # Most positive first
        
        st.markdown("""
        <div class="explainability-section">
            <div class="explainability-header">Top Negative Risk Contributors</div>
        """, unsafe_allow_html=True)
        
        for item in neg_contributors[:3]:
            st.markdown(f"""
            <div class="risk-item">
                <div class="risk-indicator negative"></div>
                <div class="risk-text"><strong>{item['feature']}</strong>: {item['description']}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
        <div class="explainability-section">
            <div class="explainability-header">Top Positive Contributors</div>
        """, unsafe_allow_html=True)
        
        for item in pos_contributors[:3]:
            st.markdown(f"""
            <div class="risk-item">
                <div class="risk-indicator positive"></div>
                <div class="risk-text"><strong>{item['feature']}</strong>: {item['description']}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)
        
    else:
        st.info("Run the Credit Decision to see Explainability factor analysis.")


# =========================
# AUDIT LOG
# =========================
elif section == "Audit Log":
    st.markdown("""
    <div class="audit-log">
        <div class="explainability-header">Decision Audit Trail</div>
        <div class="audit-row">
            <div class="audit-label">Application ID</div>
            <div class="audit-value">CR-2026-00142</div>
        </div>
        <div class="audit-row">
            <div class="audit-label">PD Model Version</div>
            <div class="audit-value">v1.2.3</div>
        </div>
        <div class="audit-row">
            <div class="audit-label">Fraud Engine</div>
            <div class="audit-value">Active</div>
        </div>
        <div class="audit-row">
            <div class="audit-label">Decision Timestamp</div>
            <div class="audit-value">2026-01-31 17:42</div>
        </div>
        <div class="audit-row">
            <div class="audit-label">Officer Override</div>
            <div class="audit-value">None</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
