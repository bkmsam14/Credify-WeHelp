"""
Integration module for OCR-based extraction in the API
Uses Tesseract OCR for document text extraction
Handles document uploads and extraction with validation
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json
import os
import tempfile

# Use OCR extractor instead of DocTR
from core.ocr_extractor import process_document as ocr_process
from core.document_extractor import process_uploaded_document as pdfplumber_process


async def extract_document_with_doctr(file_path: str, application_id: str) -> Dict[str, Any]:
    """
    Extract document using Tesseract OCR (replaces DocTR)
    Falls back to pdfplumber if OCR fails
    
    Args:
        file_path: Path to uploaded file
        application_id: Application ID for tracking
    
    Returns:
        Extraction result with structured data
    """
    
    print(f"\n🔄 Processing document for application {application_id}")
    print(f"   File: {Path(file_path).name}")
    
    try:
        print("   Using Tesseract OCR extraction...")
        result = ocr_process(file_path)
        
        # Add metadata
        result["application_id"] = application_id
        result["extraction_method"] = "tesseract_ocr"
        result["file_path"] = file_path
        
        return result
            
    except Exception as e:
        print(f"   ⚠️  OCR extraction failed: {e}")
        print("   🔄 Falling back to pdfplumber extraction...")
        
        try:
            # Fallback to pdfplumber (synchronous function, no await)
            result = pdfplumber_process(file_path)
            result["application_id"] = application_id
            result["extraction_method"] = "pdfplumber_fallback"
            result["file_path"] = file_path
            
            return result
            
        except Exception as fallback_error:
            print(f"   ❌ Both extraction methods failed: {fallback_error}")
            
            return {
                "application_id": application_id,
                "status": "error",
                "error": f"OCR failed: {str(e)}. Fallback also failed: {str(fallback_error)}",
                "extraction_method": "none",
                "document_type": "ERROR",
                "extracted_fields": {},
                "confidence_score": 0.0
            }


def validate_extracted_data_advanced(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate extracted data with document-specific rules
    
    Args:
        extracted_data: Raw extracted data
    
    Returns:
        Validation result with issues list
    """
    
    issues = []
    warnings = []
    doc_type = extracted_data.get("document_type", "UNKNOWN")
    fields = extracted_data.get("extracted_fields", {})
    confidence = extracted_data.get("confidence_score", 0)
    
    # Check confidence
    if confidence < 0.5:
        warnings.append(f"Low confidence score ({confidence:.2%}). Manual review recommended.")
    
    # Document-specific validation
    if doc_type == "STEG_BILL":
        if "amount_due" not in fields:
            issues.append("STEG bill: Amount due not found")
        if "consumption" not in fields:
            warnings.append("STEG bill: Consumption value not found")
        if "account_number" not in fields:
            warnings.append("STEG bill: Account number not found")
    
    elif doc_type == "SONEDE_BILL":
        if "amount_due" not in fields:
            issues.append("SONEDE bill: Amount due not found")
        if "consumption" not in fields:
            warnings.append("SONEDE bill: Water consumption not found")
    
    elif doc_type == "D17_FORM":
        if "total_income" not in fields:
            issues.append("D17 form: Total income not found")
        if "year" not in fields:
            warnings.append("D17 form: Tax year not found")
    
    elif doc_type == "BANK_STATEMENT":
        if "account_holder" not in fields:
            issues.append("Bank statement: Account holder not found")
        if "statement_period" not in fields:
            warnings.append("Bank statement: Statement period not found")
    
    elif doc_type == "GENERIC":
        # Generic documents just need at least one field
        if len(fields) == 0:
            issues.append("Generic document: No fields could be extracted")
        else:
            warnings.append(f"Generic document: Extracted {len(fields)} field(s)")
    
    elif doc_type == "UNKNOWN":
        if len(fields) == 0:
            issues.append("Document type could not be determined and no fields extracted. Manual review required.")
        else:
            warnings.append("Document type could not be determined. Manual review recommended.")
    
    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "field_extraction_rate": len(fields) / 8 if fields else 0,  # Estimate based on avg fields
        "recommendation": "ACCEPT" if len(issues) == 0 and confidence > 0.7 else "REVIEW"
    }


def format_extraction_for_display(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format extraction result for frontend display
    
    Args:
        result: Raw extraction result
    
    Returns:
        Formatted result for display
    """
    
    doc_type = result.get("document_type", "Unknown")
    fields = result.get("extracted_fields", {})
    confidence = result.get("confidence_score", 0)
    
    # Create human-readable field names
    display_fields = {}
    for key, value in fields.items():
        # Convert snake_case to Title Case
        display_key = key.replace("_", " ").title()
        display_fields[display_key] = value
    
    return {
        "document_type": doc_type,
        "display_name": f"{doc_type.replace('_', ' ')} - {confidence:.0%} confidence",
        "fields": display_fields,
        "confidence_percentage": f"{confidence * 100:.1f}%",
        "field_count": len(fields),
        "extraction_method": result.get("extraction_method", "unknown"),
        "status": result.get("status", "unknown")
    }
