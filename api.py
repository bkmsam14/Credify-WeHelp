"""
Credify API - FastAPI Backend for Loan Decision Intelligence System
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import pickle
import pandas as pd
import os
import uuid
from datetime import datetime
import sys

# Add root directory to path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import core modules
from core.lime_explainer import LoanLimeExplainer
from core.borderline_advisor import analyze_borderline_application

app = FastAPI(
    title="Credify API",
    description="Loan Decision Intelligence System API",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
explainer = None
model = None

# Store for uploaded documents and applications
applications_store: Dict[str, Dict] = {}
documents_store: Dict[str, List[Dict]] = {}


class CustomerApplication(BaseModel):
    age: int
    education_level: int
    employment_type: int
    employment_years: float
    monthly_income: float
    fixed_monthly_expenses: float
    debt_to_income_ratio: float
    savings_balance: float
    loan_amount: float
    loan_duration_months: int
    loan_purpose: int
    credit_score: int
    late_payments_12m: int
    missed_payments_12m: int
    utility_bill_on_time_ratio: float
    income_inflation_ratio: float
    document_mismatch_flag: int
    application_velocity: int
    geo_location_mismatch: int
    metadata_anomaly_score: float


class AnalysisResponse(BaseModel):
    application_id: str
    pd_score: float
    risk_band: str
    fraud_flag: bool
    fraud_severity: str
    recommendation: str
    explanation: str
    interview_questions: List[Dict[str, Any]]
    documents_needed: List[str]
    improvement_actions: List[Dict[str, Any]]
    pd_improvement_estimate: Dict[str, Any]
    timestamp: str
    model_version: str


def get_risk_band(pd_score: float) -> str:
    """Determine risk band based on PD score"""
    if pd_score < 0.05:
        return "Low"
    elif pd_score < 0.15:
        return "Middle"
    else:
        return "High"


def load_model():
    """Load the ML model"""
    global model
    if model is None:
        model_path = os.path.join(os.path.dirname(__file__), 'models', 'loan_model.pkl')
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
    return model


def get_explainer():
    """Get or create the LIME explainer"""
    global explainer
    if explainer is None:
        explainer = LoanLimeExplainer(
            model_path=os.path.join(os.path.dirname(__file__), 'models', 'loan_model.pkl'),
            training_data_path=os.path.join(os.path.dirname(__file__), 'data', 'training_data.csv')
        )
    return explainer


@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    load_model()
    get_explainer()
    print("Models loaded successfully")


@app.get("/")
async def root():
    return {"message": "Credify API is running", "version": "1.0.0"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "model_loaded": model is not None}


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_application(application: CustomerApplication):
    """
    Analyze a loan application and return comprehensive decision intelligence
    """
    try:
        # Generate application ID
        app_id = f"CR-{datetime.now().strftime('%Y')}-{str(uuid.uuid4())[:5].upper()}"

        # Convert to dict for processing
        customer_data = application.dict()

        # Load model and get prediction
        model = load_model()
        feature_names = model.feature_names

        # Create DataFrame with correct feature order
        row_data = {f: customer_data.get(f, 0) for f in feature_names}
        feature_df = pd.DataFrame([row_data])

        # Get prediction probabilities
        prob = model.predict_proba(feature_df)
        pd_score = 1 - prob[0][1]  # PD = 1 - P(approve)

        # Get LIME explanations
        exp = get_explainer()
        lime_features = exp.explain(customer_data, num_features=15)

        # Determine fraud flags
        fraud_severity = "none"
        if customer_data.get('document_mismatch_flag', 0) == 1:
            fraud_severity = "soft"
        if customer_data.get('geo_location_mismatch', 0) == 1 and customer_data.get('income_inflation_ratio', 1.0) > 1.3:
            fraud_severity = "hard"

        fraud_flags = {
            "severity": fraud_severity,
            "details": "Document or location inconsistencies detected" if fraud_severity != "none" else ""
        }

        # Run borderline advisor
        result = analyze_borderline_application(
            pd_score=pd_score,
            lime_features=lime_features,
            fraud_flags=fraud_flags
        )

        # Store application
        applications_store[app_id] = {
            "application": customer_data,
            "result": result,
            "pd_score": pd_score,
            "timestamp": datetime.now().isoformat()
        }

        # Build response
        response = AnalysisResponse(
            application_id=app_id,
            pd_score=round(pd_score * 100, 2),
            risk_band=get_risk_band(pd_score),
            fraud_flag=fraud_severity != "none",
            fraud_severity=fraud_severity,
            recommendation=result["recommendation"],
            explanation=result["explanation"],
            interview_questions=result["interview_questions"],
            documents_needed=result["documents_needed"],
            improvement_actions=result["improvement_actions"],
            pd_improvement_estimate=result["pd_improvement_estimate"],
            timestamp=datetime.now().isoformat(),
            model_version="v1.2.3"
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/upload/{application_id}")
async def upload_document(application_id: str, file: UploadFile = File(...)):
    """
    Upload a document for an application
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads', application_id)
        os.makedirs(uploads_dir, exist_ok=True)

        # Generate unique filename
        file_id = str(uuid.uuid4())[:8]
        safe_filename = f"{file_id}_{file.filename}"
        file_path = os.path.join(uploads_dir, safe_filename)

        # Save file
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)

        # Store document metadata
        if application_id not in documents_store:
            documents_store[application_id] = []

        doc_info = {
            "id": file_id,
            "filename": file.filename,
            "stored_filename": safe_filename,
            "size": len(content),
            "uploaded_at": datetime.now().isoformat(),
            "status": "uploaded",
            "verified": False
        }
        documents_store[application_id].append(doc_info)

        return {
            "message": "Document uploaded successfully",
            "document": doc_info
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{application_id}")
async def get_documents(application_id: str):
    """
    Get all documents for an application
    """
    docs = documents_store.get(application_id, [])
    return {"application_id": application_id, "documents": docs}


@app.put("/api/documents/{application_id}/{document_id}/verify")
async def verify_document(application_id: str, document_id: str):
    """
    Mark a document as verified
    """
    if application_id not in documents_store:
        raise HTTPException(status_code=404, detail="Application not found")

    for doc in documents_store[application_id]:
        if doc["id"] == document_id:
            doc["verified"] = True
            doc["verified_at"] = datetime.now().isoformat()
            return {"message": "Document verified", "document": doc}

    raise HTTPException(status_code=404, detail="Document not found")


@app.get("/api/applications/{application_id}")
async def get_application(application_id: str):
    """
    Get a stored application and its analysis
    """
    if application_id not in applications_store:
        raise HTTPException(status_code=404, detail="Application not found")

    app_data = applications_store[application_id]
    docs = documents_store.get(application_id, [])

    return {
        "application_id": application_id,
        "data": app_data,
        "documents": docs
    }


@app.get("/api/feature-descriptions")
async def get_feature_descriptions():
    """
    Get descriptions and metadata for all features
    """
    from core.knowledge_base import FEATURE_KNOWLEDGE
    return {"features": FEATURE_KNOWLEDGE}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
