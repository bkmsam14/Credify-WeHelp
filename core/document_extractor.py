"""
Document Data Extraction Module - COMPLETELY FREE VERSION
Extracts structured data from uploaded documents using:
- Tesseract OCR (local, free)
- Regex patterns (free, no API calls)

No API keys needed!
"""

import json
import base64
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple


def document_to_text(file_path: str, use_openai: bool = False) -> str:
    """
    Extract text from document using:
    - pdfplumber for PDFs (pure Python, no Poppler needed)
    - Tesseract OCR for images (completely free, local)
    
    Args:
        file_path: Path to document file (PDF, PNG, JPG, TIFF, etc.)
        use_openai: Ignored (not using OpenAI, keeping for compatibility)
    
    Returns:
        Extracted text from document
    """
    try:
        from PIL import Image
        import pytesseract
    except ImportError:
        raise ImportError("Required packages missing. Install with: pip install pytesseract pillow")
    
    try:
        file_path = Path(file_path)
        
        # Handle PDF files - extract text directly using pdfplumber
        if file_path.suffix.lower() == '.pdf':
            try:
                import pdfplumber
            except ImportError:
                raise ImportError("PDF support requires pdfplumber. Install with: pip install pdfplumber")
            
            all_text = []
            with pdfplumber.open(str(file_path)) as pdf:
                if not pdf.pages:
                    raise RuntimeError(f"No pages found in PDF: {file_path}")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    # Try to extract text from PDF
                    text = page.extract_text()
                    if text:
                        all_text.append(text)
                    else:
                        # If PDF has no extractable text, try OCR on the image
                        try:
                            img = page.to_image()
                            text = pytesseract.image_to_string(img.original, lang='ara+eng')
                            all_text.append(text)
                        except:
                            pass
            
            if not all_text:
                raise RuntimeError(f"Could not extract text from PDF: {file_path}")
            
            return "\n---PAGE BREAK---\n".join(all_text)
        
        # Handle image files directly
        else:
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang='ara+eng')
            return text
            
    except Exception as e:
        raise RuntimeError(f"Document OCR failed: {e}")


def extract_structured_data(document_text: str, doc_type: str = "auto") -> Dict[str, Any]:
    """
    Parse OCR text into structured fields using REGEX PATTERNS (completely free, no API calls).
    
    Args:
        document_text: Raw OCR text from document
        doc_type: Type of document (bill, bank_statement, payslip, id, auto)
    
    Returns:
        Dictionary with extracted fields
    """
    data = {
        "monthly_income": None,
        "fixed_monthly_expenses": None,
        "savings_balance": None,
        "employment_years": None,
        "credit_score": None,
        "utility_bill_on_time_ratio": None,
        "income_inflation_ratio": None,
        "document_type": doc_type,
        "document_date": None,
        "extracted_fields": []
    }
    
    text = document_text.lower()
    
    # === Extract dates (YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY) ===
    date_match = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4})', document_text)
    if date_match:
        data["document_date"] = date_match.group(1)
    
    # === INCOME PATTERNS ===
    income_patterns = [
        r'(?:monthly\s+)?(?:salary|income|revenu)[\s:]*(\d+(?:[,\.]\d{2})?)\s*(?:tnd|td|\$|€)?',
        r'(?:salaire|revenu)\s+(?:mensuel|brut)[\s:]*(\d+(?:[,\.]\d{2})?)',
        r'(?:net\s+)?(?:salary|income)[\s:]*(\d+(?:[,\.]\d{2})?)',
        r'(\d+(?:[,\.]\d{2})?)\s*(?:tnd|td|dinar)',
    ]
    
    for pattern in income_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and data["monthly_income"] is None:
            amount_str = match.group(1).replace(',', '.')
            try:
                data["monthly_income"] = float(amount_str)
                data["extracted_fields"].append("monthly_income")
                break
            except ValueError:
                pass
    
    # === EXPENSE PATTERNS ===
    expense_patterns = [
        r'(?:fixed\s+)?(?:monthly\s+)?expense[\s:]*(\d+(?:[,\.]\d{2})?)',
        r'(?:dépense|charge|frais)\s+(?:mensuel|fixe)[\s:]*(\d+(?:[,\.]\d{2})?)',
        r'(?:loan\s+)?(?:payment|installment|paiement)[\s:]*(\d+(?:[,\.]\d{2})?)',
    ]
    
    for pattern in expense_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and data["fixed_monthly_expenses"] is None:
            amount_str = match.group(1).replace(',', '.')
            try:
                data["fixed_monthly_expenses"] = float(amount_str)
                data["extracted_fields"].append("fixed_monthly_expenses")
                break
            except ValueError:
                pass
    
    # === SAVINGS PATTERNS ===
    savings_patterns = [
        r'(?:savings?|balance|solde)[\s:]*(\d+(?:[,\.]\d{2})?)\s*(?:tnd|td|\$|€)?',
        r'(?:account\s+)?balance[\s:]*(\d+(?:[,\.]\d{2})?)',
        r'(?:épargne|disponible)[\s:]*(\d+(?:[,\.]\d{2})?)',
    ]
    
    for pattern in savings_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and data["savings_balance"] is None:
            amount_str = match.group(1).replace(',', '.')
            try:
                data["savings_balance"] = float(amount_str)
                data["extracted_fields"].append("savings_balance")
                break
            except ValueError:
                pass
    
    # === EMPLOYMENT YEARS PATTERNS ===
    employment_patterns = [
        r'(?:employment\s+)?(?:since|for|years?)[\s:]*(\d+(?:\.\d)?)\s*(?:year)?',
        r'(?:ancienneté|expérience)[\s:]*(\d+(?:\.\d)?)\s*(?:ans?)?',
        r'(?:years\s+of\s+)?(?:experience|employment)[\s:]*(\d+(?:\.\d)?)',
    ]
    
    for pattern in employment_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and data["employment_years"] is None:
            years_str = match.group(1)
            try:
                data["employment_years"] = float(years_str)
                data["extracted_fields"].append("employment_years")
                break
            except ValueError:
                pass
    
    # === CREDIT SCORE PATTERNS ===
    credit_patterns = [
        r'(?:credit\s+)?score[\s:]*(\d{3,4})',
        r'(?:score\s+)?crédit[\s:]*(\d{3,4})',
        r'(?:fico|credit\s+rating)[\s:]*(\d{3,4})',
    ]
    
    for pattern in credit_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and data["credit_score"] is None:
            score_str = match.group(1)
            try:
                score = int(score_str)
                if 300 <= score <= 850:  # Valid credit score range
                    data["credit_score"] = score
                    data["extracted_fields"].append("credit_score")
                    break
            except ValueError:
                pass
    
    # === UTILITY BILL ON-TIME RATIO PATTERNS ===
    # Look for payment history or on-time indicators
    if re.search(r'(?:paid|paid on time|on-time|payment)?[\s:]*(\d+)%?\s*(?:on.time|paid|paid\s+on\s+time)', text):
        match = re.search(r'(\d+)%?\s*(?:on.time|paid|paid\s+on\s+time)', text)
        if match:
            try:
                percentage = int(match.group(1)) / 100.0
                data["utility_bill_on_time_ratio"] = max(0.0, min(1.0, percentage))
                data["extracted_fields"].append("utility_bill_on_time_ratio")
            except ValueError:
                pass
    
    # Fallback: estimate from late/missed payments
    if data["utility_bill_on_time_ratio"] is None:
        late_match = re.search(r'(?:late|missed)\s+(?:payment)?[\s:]*(\d+)', text)
        if late_match:
            try:
                missed = int(late_match.group(1))
                # Assume 12 months, estimate on-time ratio
                if missed <= 2:
                    data["utility_bill_on_time_ratio"] = 0.85
                elif missed <= 5:
                    data["utility_bill_on_time_ratio"] = 0.60
                else:
                    data["utility_bill_on_time_ratio"] = 0.40
                if data["utility_bill_on_time_ratio"]:
                    data["extracted_fields"].append("utility_bill_on_time_ratio")
            except ValueError:
                pass
    
    # === INCOME INFLATION RATIO PATTERNS ===
    # Look for stated vs declared income discrepancy
    declared_match = re.search(r'(?:declared|stated|claimed)\s+(?:income|salary)[\s:]*(\d+(?:[,\.]\d{2})?)', text)
    expected_match = re.search(r'(?:expected|average)\s+(?:income|salary)[\s:]*(\d+(?:[,\.]\d{2})?)', text)
    
    if declared_match and expected_match:
        try:
            declared = float(declared_match.group(1).replace(',', '.'))
            expected = float(expected_match.group(1).replace(',', '.'))
            if expected > 0:
                data["income_inflation_ratio"] = declared / expected
                data["extracted_fields"].append("income_inflation_ratio")
        except ValueError:
            pass
    else:
        # Default to 1.0 if not found (no inflation)
        data["income_inflation_ratio"] = 1.0
    
    return data



def map_to_model_format(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map extracted document fields to loan model input format.
    
    Args:
        extracted_data: Output from extract_structured_data()
    
    Returns:
        Dictionary ready for model prediction
    """
    result = {}
    
    # Map extracted fields to model features
    field_mapping = {
        "monthly_income": "monthly_income",
        "fixed_monthly_expenses": "fixed_monthly_expenses",
        "savings_balance": "savings_balance",
        "employment_years": "employment_years",
        "credit_score": "credit_score",
        "utility_bill_on_time_ratio": "utility_bill_on_time_ratio",
        "income_inflation_ratio": "income_inflation_ratio",
    }
    
    for extracted_field, model_field in field_mapping.items():
        if extracted_data.get(extracted_field) is not None:
            value = extracted_data[extracted_field]
            try:
                result[model_field] = float(value)
            except (ValueError, TypeError):
                pass
    
    # Add metadata (fields starting with _ are metadata only)
    result["_document_source"] = extracted_data.get("document_type", "unknown")
    result["_document_date"] = extracted_data.get("document_date")
    result["_extracted_fields"] = extracted_data.get("extracted_fields", [])
    
    return result


def process_uploaded_document(file_path: str, doc_type: str = "auto") -> Dict[str, Any]:
    """
    Complete pipeline: OCR → Extract → Format (all completely free)
    
    Args:
        file_path: Path to document
        doc_type: Document type (bill, bank_statement, payslip, id, auto)
    
    Returns:
        Dictionary ready for model or form auto-fill
    """
    print(f"Processing document: {file_path}")
    
    # Step 1: Extract text from image (Tesseract, free)
    print("  → Extracting text from document (Tesseract)...")
    document_text = document_to_text(file_path, use_openai=False)
    
    # Step 2: Parse into structured fields (regex, free)
    print("  → Parsing document with regex patterns...")
    extracted_data = extract_structured_data(document_text, doc_type)
    
    # Step 3: Map to model format
    print("  → Mapping to model format...")
    model_input = map_to_model_format(extracted_data)
    
    print(f"  ✓ Successfully extracted {len([f for f in model_input if not f.startswith('_')])} fields")
    
    return model_input


def validate_extracted_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate extracted data ranges (lenient - no required fields).
    
    Will accept documents with partial data. Missing fields will use defaults.
    Only validates the ranges of fields that ARE present.
    
    Args:
        data: Dictionary from map_to_model_format()
    
    Returns:
        (is_valid, list_of_issues)
    """
    issues = []
    
    # Validate ranges for fields that ARE present
    # (no required fields - extract whatever is available)
    
    if data.get("monthly_income") is not None:
        if data["monthly_income"] < 0:
            issues.append("monthly_income cannot be negative")
    
    if data.get("fixed_monthly_expenses") is not None:
        if data["fixed_monthly_expenses"] < 0:
            issues.append("fixed_monthly_expenses cannot be negative")
    
    if data.get("savings_balance") is not None:
        if data["savings_balance"] < 0:
            issues.append("savings_balance cannot be negative")
    
    if data.get("employment_years") is not None:
        if not (0 <= data["employment_years"] <= 70):
            issues.append("employment_years out of valid range (0-70)")
    
    if data.get("credit_score") is not None:
        if not (300 <= data["credit_score"] <= 850):
            issues.append("credit_score out of valid range (300-850)")
    
    # Always return True (valid) unless there are actual value range issues
    # Empty extractions are OK - they'll just use default values
    return len(issues) == 0, issues


