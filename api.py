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
import pytesseract 
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
import sys

# Add root directory to path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import core modules
from core.lime_explainer import LoanLimeExplainer
from core.borderline_advisor import analyze_borderline_application
from core.decision_engine import analyze_application_complete
from core.document_extractor import process_uploaded_document, validate_extracted_data
from core.improvement_suggester import generate_ai_suggestions
from core.interview_questioner import generate_interview_questions

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
    Analyze a loan application using the complete decision engine from hackathon_final.ipynb
    """
    try:
        # Generate application ID
        app_id = f"CR-{datetime.now().strftime('%Y')}-{str(uuid.uuid4())[:5].upper()}"

        # Convert to dict for processing
        customer_data = application.dict()
        
        # DEBUG: Log the received data
        print("\n" + "="*50)
        print("ANALYZE ENDPOINT RECEIVED:")
        print(f"  monthly_income: {customer_data.get('monthly_income')}")
        print(f"  savings_balance: {customer_data.get('savings_balance')}")
        print(f"  fixed_monthly_expenses: {customer_data.get('fixed_monthly_expenses')}")
        print(f"  employment_years: {customer_data.get('employment_years')}")
        print(f"  credit_score: {customer_data.get('credit_score')}")
        print("="*50 + "\n")

        # Load model and explainer
        model = load_model()
        exp = get_explainer()

        # Use complete decision engine from hackathon_final.ipynb
        analysis = analyze_application_complete(
            raw=customer_data,
            model=model,
            explainer=exp,
            pipeline=None
        )

        # Run borderline advisor for additional details (interview questions, documents, etc.)
        borderline_result = analyze_borderline_application(
            pd_score=analysis["pd_score"],
            lime_features=analysis["lime_features"],
            fraud_flags={
                "severity": "hard" if analysis["fraud_decision"] == "BLOCK" else ("soft" if analysis["fraud_score"] >= 0.25 else "none"),
                "details": analysis["fraud"]
            }
        )

        # Generate AI personalized interview questions based on model insights
        interview_questions = generate_interview_questions(
            raw_data=customer_data,
            lime_features=analysis["lime_features"],
            pd_score=analysis["pd_score"]
        )
        
        print(f"\n📋 Generated {len(interview_questions)} personalized interview questions")

        # Generate AI suggestions based on actual feature impact
        ai_suggestions = generate_ai_suggestions(
            raw_data=customer_data,
            model=model,
            current_pd=analysis["pd_score"],
            lime_features=analysis["lime_features"]
        )
        
        print(f"\n✨ Generated {len(ai_suggestions)} AI improvement suggestions")
        for sugg in ai_suggestions:
            print(f"  - {sugg['user_friendly']}: {sugg['pd_reduction']} reduction")

        # Calculate combined PD improvement from suggestions
        # Extract the best PD we can achieve if all suggestions are implemented
        if ai_suggestions:
            # Get the lowest PD from the best suggestion
            best_new_pd = float(ai_suggestions[0]["new_estimated_pd"].rstrip('%')) / 100
            current_pd_decimal = analysis["pd_percent"] / 100
            total_improvement = current_pd_decimal - best_new_pd
            improvement_percent = (total_improvement / current_pd_decimal * 100) if current_pd_decimal > 0 else 0
            
            pd_improvement_estimate = {
                "current_pd": f"{analysis['pd_percent']:.1f}%",
                "potential_pd": f"{best_new_pd * 100:.1f}%",
                "improvement": f"{improvement_percent:.1f}%",
                "note": "Estimate assumes the top-ranked improvement action is completed. Actual improvement may vary."
            }
        else:
            pd_improvement_estimate = {
                "current_pd": f"{analysis['pd_percent']:.1f}%",
                "potential_pd": f"{analysis['pd_percent']:.1f}%",
                "improvement": "0.0%",
                "note": "No significant improvement opportunities identified at this time."
            }

        # Map decision to recommendation
        decision_map = {
            "APPROVED": "APPROVE",
            "REJECTED": "REJECT",
            "MIDDLE": "MANUAL_REVIEW",
            "BLOCKED_FRAUD": "REJECT"
        }
        
        recommendation = decision_map.get(analysis["decision"], "MANUAL_REVIEW")

        # Store application
        applications_store[app_id] = {
            "application": customer_data,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }

        # Build response with AI suggestions
        response = AnalysisResponse(
            application_id=app_id,
            pd_score=analysis["pd_percent"],
            risk_band=analysis["risk_band"],
            fraud_flag=analysis["fraud_decision"] == "BLOCK",
            fraud_severity="hard" if analysis["fraud_decision"] == "BLOCK" else ("soft" if analysis["fraud_score"] >= 0.25 else "none"),
            recommendation=recommendation,
            explanation=analysis["summary"],
            interview_questions=[
                {
                    "order": q["order"],
                    "question": q["question"],
                    "feature": q["feature"],
                    "purpose": q["purpose"],
                    "follow_up": q["follow_up"],
                    "category": q.get("category", "General")
                }
                for q in interview_questions
            ],
            documents_needed=borderline_result.get("documents_needed", []),
            improvement_actions=[
                {
                    "action": sugg["suggestion"],
                    "feasibility": sugg["feasibility"],
                    "feature": sugg["feature"],
                    "impact": sugg["pd_reduction"]
                }
                for sugg in ai_suggestions
            ],
            pd_improvement_estimate=pd_improvement_estimate,
            timestamp=datetime.now().isoformat(),
            model_version="v1.4.0-hackathon"
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/upload/{application_id}")
async def upload_document(application_id: str, file: UploadFile = File(...)):
    """
    Upload a document for an application and extract data automatically
    """
    try:
        # Validate file type - support PDF and images
        filename_lower = file.filename.lower()
        supported_types = ('.pdf', '.png', '.jpg', '.jpeg', '.tiff')
        if not any(filename_lower.endswith(ext) for ext in supported_types):
            raise HTTPException(status_code=400, detail="Only PDF and image files are allowed (.pdf, .png, .jpg, .jpeg, .tiff)")

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

        # Determine document type from filename
        if 'steg' in filename_lower or 'electricity' in filename_lower:
            doc_type = 'bill'
        elif 'bank' in filename_lower or 'statement' in filename_lower:
            doc_type = 'bank_statement'
        elif 'payslip' in filename_lower or 'salary' in filename_lower:
            doc_type = 'payslip'
        elif 'id' in filename_lower or 'cin' in filename_lower:
            doc_type = 'id'
        else:
            doc_type = 'auto'

        # Extract data from document
        try:
            extracted_data = process_uploaded_document(file_path, doc_type)
            is_valid, validation_issues = validate_extracted_data(extracted_data)
            extraction_status = "extracted" if is_valid else "extracted_with_issues"
            extracted_fields = extracted_data.get('_extracted_fields', [])
        except Exception as extract_err:
            print(f"Error extracting data from {file.filename}: {str(extract_err)}")
            extracted_data = {}
            is_valid = False
            extraction_status = "failed"
            extracted_fields = []
            validation_issues = [str(extract_err)]

        # Store document metadata
        if application_id not in documents_store:
            documents_store[application_id] = []

        doc_info = {
            "id": file_id,
            "filename": file.filename,
            "stored_filename": safe_filename,
            "size": len(content),
            "uploaded_at": datetime.now().isoformat(),
            "status": extraction_status,
            "verified": False,
            "extracted_data": extracted_data,
            "extracted_fields": extracted_fields,
            "validation": {
                "is_valid": is_valid,
                "issues": validation_issues
            }
        }
        documents_store[application_id].append(doc_info)

        return {
            "message": "Document uploaded and extracted successfully" if is_valid else "Document uploaded with extraction issues",
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


@app.post("/api/documents/{application_id}/extract")
async def extract_document_data(application_id: str, file: UploadFile = File(...)):
    """
    Extract data from uploaded document (bill, bank statement, payslip, etc.)
    Returns extracted data in model-ready format
    """
    try:
        if application_id not in applications_store:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Save uploaded file temporarily
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        
        file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Determine document type from filename
        filename_lower = file.filename.lower()
        if 'steg' in filename_lower or 'electricity' in filename_lower:
            doc_type = 'bill'
        elif 'bank' in filename_lower or 'statement' in filename_lower:
            doc_type = 'bank_statement'
        elif 'payslip' in filename_lower or 'salary' in filename_lower:
            doc_type = 'payslip'
        elif 'id' in filename_lower or 'cin' in filename_lower:
            doc_type = 'id'
        else:
            doc_type = 'auto'
        
        # Extract data from document
        extracted_data = process_uploaded_document(file_path, doc_type)
        
        # Validate extracted data
        is_valid, validation_issues = validate_extracted_data(extracted_data)
        
        # Clean up temp file
        os.remove(file_path)
        
        return {
            "application_id": application_id,
            "document_type": doc_type,
            "extracted_data": extracted_data,
            "validation": {
                "is_valid": is_valid,
                "issues": validation_issues
            },
            "extracted_fields": extracted_data.get('_extracted_fields', []),
            "message": "Data extracted successfully" if is_valid else "Data extracted with warnings"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document extraction failed: {str(e)}")


@app.post("/api/applications/auto-fill")
async def auto_fill_application(application_id: str, extracted_data: Dict[str, Any]):
    """
    Auto-fill application form with extracted document data
    Merges extracted data with any existing form data
    """
    try:
        if application_id not in applications_store:
            raise HTTPException(status_code=404, detail="Application not found")
        
        app_data = applications_store[application_id]["application"]
        
        # Merge extracted data with form data (extracted takes precedence)
        merged = {**app_data}
        
        # Only update fields that were successfully extracted
        for key, value in extracted_data.items():
            if not key.startswith('_') and value is not None:  # Skip metadata
                if key in merged:
                    merged[key] = value
        
        # Store merged data
        applications_store[application_id]["application"] = merged
        applications_store[application_id]["auto_filled_from"] = extracted_data.get('_document_source')
        applications_store[application_id]["auto_fill_date"] = datetime.now().isoformat()
        
        return {
            "application_id": application_id,
            "merged_data": merged,
            "message": "Application auto-filled successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
