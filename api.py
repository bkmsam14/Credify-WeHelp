"""
Credify API - FastAPI Backend for Loan Decision Intelligence System
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import pickle
import pandas as pd
import os
import uuid
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
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

# Import OCR integration (with fallback support)
try:
    from core.doctr_integration import extract_document_with_doctr, validate_extracted_data_advanced, format_extraction_for_display
    OCR_AVAILABLE = True
    print("[OK] OCR integration loaded (using Tesseract)")
except ImportError as e:
    OCR_AVAILABLE = False
    print(f"[WARNING] OCR not available: {e}")
    print("   Falling back to pdfplumber extraction")

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
        
        print("\n" + "="*60)
        print("🔍 ANALYZING APPLICATION")
        print("="*60)
        print(f"\nApplication ID: {app_id}")
        print("\n[INFO] RECEIVED DATA FROM FRONTEND:")
        print(f"  monthly_income: {customer_data.get('monthly_income')}")
        print(f"  savings_balance: {customer_data.get('savings_balance')}")
        print(f"  fixed_monthly_expenses: {customer_data.get('fixed_monthly_expenses')}")
        print(f"  employment_years: {customer_data.get('employment_years')}")
        print(f"  credit_score: {customer_data.get('credit_score')}")
        print(f"  [Note: Check if these look like extracted data or defaults]")
        
        # Try to find and use extracted document data if available
        print("\n[INFO] CHECKING FOR EXTRACTED DOCUMENT DATA...")
        extracted_data_used = False
        
        # Copy documents from temporary IDs to the new application ID
        if app_id not in documents_store:
            documents_store[app_id] = []
        
        # Look for documents in any temp or other app IDs (any non-CR app IDs)
        temp_app_ids = [key for key in documents_store.keys() if not key.startswith('CR-')]
        print(f"\n  Found {len(temp_app_ids)} temporary applications: {temp_app_ids}")
        
        if temp_app_ids:
            for temp_app_id in temp_app_ids:
                if documents_store[temp_app_id]:
                    doc_count = len(documents_store[temp_app_id])
                    doc_ids = [doc['id'] for doc in documents_store[temp_app_id]]
                    print(f"  [✓] Moving {doc_count} documents from {temp_app_id}")
                    print(f"      Document IDs: {doc_ids}")
                    # Copy all documents to the new app ID
                    documents_store[app_id].extend(documents_store[temp_app_id])
                    # Clear the temp ID
                    documents_store[temp_app_id] = []
        else:
            print(f"  [INFO] No temporary documents found")
        
        # Look for documents in the NEW application ID first (where we just moved them)
        docs_to_check = documents_store.get(app_id, [])
        print(f"\n  Total documents for this application: {len(docs_to_check)}")
        
        # Find documents with extracted data
        for doc in docs_to_check:
            if doc.get("status") in ["extracted", "extracted_with_issues"]:
                extracted_fields = doc.get("extracted_data", {})
                doc_type = doc.get("extraction_info", {}).get("document_type", "UNKNOWN")
                
                if not extracted_fields:
                    print(f"  [INFO] Document has status '{doc.get('status')}' but no extracted fields")
                    continue
                
                print(f"\n  Found extracted {doc_type} with fields: {list(extracted_fields.keys())}")
                
                # Try to map extracted fields to application fields
                field_mapping = {
                    # Generic mappings (work with GENERIC documents too)
                    "name": None,  # Don't map name to any model field
                    "credit_score": "credit_score",
                    "monthly_income": "monthly_income",
                    "income": "monthly_income",
                    "salary": "monthly_income",
                    "salaire": "monthly_income",
                    "total_income": "monthly_income",
                    "savings": "savings_balance",
                    "savings_balance": "savings_balance",
                    "balance": "savings_balance",
                    "account_balance": "savings_balance",
                    "closing_balance": "savings_balance",
                    "amount_due": "loan_amount",
                    "consumption": "fixed_monthly_expenses",  # utility consumption
                    "expenses": "fixed_monthly_expenses",
                }
                
                # Try to use extracted data to update fields
                for extracted_field, extracted_value in extracted_fields.items():
                    mapped_field = field_mapping.get(extracted_field.lower())
                    
                    # Skip fields that explicitly map to None
                    if mapped_field is None:
                        print(f"    [INFO] Extracted {extracted_field}: {extracted_value} (not used for modeling)")
                        continue
                    
                    if mapped_field:
                        # Try to use extracted value regardless of current value
                        try:
                            # Convert extracted value to number if needed
                            if isinstance(extracted_value, str):
                                extracted_num = float(extracted_value.replace(',', '.'))
                            else:
                                extracted_num = float(extracted_value)
                            
                            # Use extracted value
                            old_value = customer_data.get(mapped_field)
                            customer_data[mapped_field] = extracted_num
                            print(f"    [✓] Using extracted {extracted_field}: {extracted_num} -> {mapped_field} (was: {old_value})")
                            extracted_data_used = True
                        except (ValueError, TypeError):
                            print(f"    [✗] Could not parse extracted {extracted_field}: {extracted_value}")
        
        if not extracted_data_used:
            print("\n    [!] No extracted data was used. Using provided values only.")
        else:
            print("\n    [✓] Extracted data successfully integrated into analysis.")
        
        print("\n[INFO] FINAL DATA FOR ANALYSIS:")
        print(f"  monthly_income: {customer_data.get('monthly_income')}")
        print(f"  savings_balance: {customer_data.get('savings_balance')}")
        print(f"  credit_score: {customer_data.get('credit_score')}")
        print(f"  fixed_monthly_expenses: {customer_data.get('fixed_monthly_expenses')}")
        print(f"  loan_amount: {customer_data.get('loan_amount')}")
        print("="*60 + "\n")

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
        
        print(f"\n[INFO] Generated {len(interview_questions)} personalized interview questions")

        # Generate AI suggestions based on actual feature impact
        ai_suggestions = generate_ai_suggestions(
            raw_data=customer_data,
            model=model,
            current_pd=analysis["pd_score"],
            lime_features=analysis["lime_features"]
        )
        
        print(f"\n[OK] Generated {len(ai_suggestions)} AI improvement suggestions")
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


def _extract_document_background(file_path: str, application_id: str, file_id: str, filename: str):
    """
    Background task to extract document data using OCR without blocking the HTTP response
    """
    try:
        print(f"[INFO] Background extraction started for {filename}")
        
        # Extract data from document using OCR (with fallback)
        if OCR_AVAILABLE:
            print(f"   Using Tesseract OCR extraction for {file_id}...")
            from core.ocr_extractor import process_document
            extraction_result = process_document(file_path)
            
            # Validate extraction
            validation_result = validate_extracted_data_advanced(extraction_result)
            
            # Format for display
            display_info = format_extraction_for_display(extraction_result)
            
            extracted_data = extraction_result.get("extracted_fields", {})
            extracted_fields = list(extracted_data.keys())
            is_valid = validation_result.get("is_valid", False)
            extraction_status = "extracted" if is_valid else "extracted_with_issues"
            validation_issues = validation_result.get("issues", [])
            warnings = validation_result.get("warnings", [])
            
            extraction_info = {
                "method": extraction_result.get("extraction_method", "tesseract_ocr"),
                "document_type": extraction_result.get("document_type", "UNKNOWN"),
                "confidence_score": extraction_result.get("confidence_score", 0),
                "ocr_confidence": extraction_result.get("ocr_confidence", 0),
                "type_confidence": extraction_result.get("type_confidence", 0),
                "field_count": extraction_result.get("field_count", 0),
                "display_info": display_info
            }
        else:
            print(f"   Using pdfplumber fallback for {file_id}...")
            extracted_data = process_uploaded_document(file_path, 'auto')
            is_valid, validation_issues = validate_extracted_data(extracted_data)
            extracted_fields = extracted_data.get('_extracted_fields', [])
            extraction_status = "extracted" if is_valid else "extracted_with_issues"
            warnings = []
            extraction_info = {
                "method": "pdfplumber_fallback",
                "document_type": "AUTO",
                "confidence_score": 0.5,
                "display_info": None
            }
            
    except Exception as extract_err:
        print(f"   [ERROR] Error extracting data: {str(extract_err)}")
        import traceback
        traceback.print_exc()
        
        extracted_data = {}
        is_valid = False
        extraction_status = "failed"
        extracted_fields = []
        validation_issues = [str(extract_err)]
        warnings = []
        extraction_info = {
            "method": "error",
            "document_type": "ERROR",
            "confidence_score": 0.0,
            "error": str(extract_err)
        }

    # Update document in store with extraction results
    if application_id in documents_store:
        for doc in documents_store[application_id]:
            if doc["id"] == file_id:
                doc["status"] = extraction_status
                doc["extracted_data"] = extracted_data
                doc["extracted_fields"] = extracted_fields
                doc["validation"] = {
                    "is_valid": is_valid,
                    "issues": validation_issues,
                    "warnings": warnings
                }
                doc["extraction_info"] = extraction_info
                
                print(f"   [OK] Extraction complete for {file_id}")
                print(f"      Document type: {extraction_info.get('document_type')}")
                print(f"      Status: {extraction_status}")
                print(f"      Fields extracted: {len(extracted_fields)}")
                print(f"      Document stored in app: {application_id}")
                break
    else:
        print(f"   [WARNING] App {application_id} not in documents_store!")
        print(f"      Available apps: {list(documents_store.keys())}")
        print(f"      Creating app entry and storing document...")
        # Ensure app exists
        if application_id not in documents_store:
            documents_store[application_id] = []
        documents_store[application_id].append({
            "id": file_id,
            "status": extraction_status,
            "extracted_data": extracted_data,
            "extracted_fields": extracted_fields,
            "validation": {
                "is_valid": is_valid,
                "issues": validation_issues,
                "warnings": warnings
            },
            "extraction_info": extraction_info
        })


@app.post("/api/documents/upload/{application_id}")
async def upload_document(application_id: str, file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    """
    Upload a document for an application and start background extraction
    Returns immediately while extraction happens in background
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

        print(f"\n[INFO] Document uploaded: {file.filename}")
        print(f"   File ID: {file_id}")
        print(f"   Size: {len(content)} bytes")
        print(f"   Status: Queued for extraction")

        # Store document with "pending" status
        if application_id not in documents_store:
            documents_store[application_id] = []

        doc_info = {
            "id": file_id,
            "filename": file.filename,
            "stored_filename": safe_filename,
            "size": len(content),
            "uploaded_at": datetime.now().isoformat(),
            "status": "pending",
            "verified": False,
            "extracted_data": {},
            "extracted_fields": [],
            "validation": {
                "is_valid": False,
                "issues": [],
                "warnings": []
            },
            "extraction_info": {
                "method": "pending",
                "document_type": "UNKNOWN",
                "confidence_score": 0.0
            }
        }
        documents_store[application_id].append(doc_info)

        # Start background extraction task (non-blocking)
        background_tasks.add_task(_extract_document_background, file_path, application_id, file_id, file.filename)

        return {
            "message": "Document uploaded successfully. Extraction in progress...",
            "document": doc_info
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"   [ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/debug/documents")
async def debug_get_all_documents():
    """
    DEBUG ENDPOINT: Show all documents in store with full details
    """
    result = {}
    for app_id, docs in documents_store.items():
        result[app_id] = [
            {
                "id": doc["id"],
                "filename": doc["filename"],
                "status": doc["status"],
                "extracted_fields": doc.get("extracted_fields", []),
                "extracted_data": doc.get("extracted_data", {}),
                "extraction_info": doc.get("extraction_info", {})
            }
            for doc in docs
        ]
    return {"total_apps": len(documents_store), "documents": result}


@app.get("/api/documents/{application_id}")
async def get_documents(application_id: str):
    """
    Get all documents for an application
    """
    docs = documents_store.get(application_id, [])
    return {"application_id": application_id, "documents": docs}


@app.get("/api/documents/{application_id}/{document_id}/status")
async def get_document_status(application_id: str, document_id: str):
    """
    Get extraction status of a specific document
    Search across all applications if not found in the specified one
    """
    # First try the specified application
    if application_id in documents_store:
        for doc in documents_store[application_id]:
            if doc["id"] == document_id:
                return {
                    "id": document_id,
                    "status": doc["status"],
                    "extracted_fields": doc.get("extracted_fields", []),
                    "extracted_data": doc.get("extracted_data", {}),
                    "extraction_info": doc.get("extraction_info", {}),
                    "validation": doc.get("validation", {})
                }
    
    # If not found, search all applications (for cross-app document lookup)
    for app_id, docs in documents_store.items():
        for doc in docs:
            if doc["id"] == document_id:
                return {
                    "id": document_id,
                    "status": doc["status"],
                    "extracted_fields": doc.get("extracted_fields", []),
                    "extracted_data": doc.get("extracted_data", {}),
                    "extraction_info": doc.get("extraction_info", {}),
                    "validation": doc.get("validation", {})
                }
    
    raise HTTPException(status_code=404, detail="Document not found")


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
