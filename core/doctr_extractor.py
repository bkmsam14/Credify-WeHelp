"""
DocTR-based Document Extraction Module
Extracts structured data from Tunisian financial documents using OCR
Supports: SONEDE bills, STEG bills, D17 forms, Bank statements
"""

import re
import json
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
import tempfile
import os

try:
    from doctr.io import DocumentFile
    from doctr.models import ocr_predictor
    DOCTR_AVAILABLE = True
except ImportError:
    DOCTR_AVAILABLE = False
    print("⚠️  DocTR not installed. Run: pip install python-doctr")


# Initialize OCR model globally to avoid reloading
ocr_model = None
model_loading = False


def initialize_ocr():
    """Initialize the DocTR OCR model (loaded once at startup)"""
    global ocr_model, model_loading
    if ocr_model is None and DOCTR_AVAILABLE:
        if not model_loading:
            model_loading = True
            print("📦 Loading DocTR OCR model (this may take a moment)...")
            ocr_model = ocr_predictor(pretrained=True)
            print("✅ DocTR model loaded successfully")
        else:
            print("⏳ Waiting for OCR model to load...")
    return ocr_model


# Document type patterns for detection
DOCUMENT_PATTERNS = {
    "STEG_BILL": {
        "keywords": ["STEG", "électricité", "electricity", "consommation", "kwh", "شركة التوزيع"],
        "fields": {
            "customer_name": r"(?:nom|name|client)[\s:]*([A-Za-z\s\u0600-\u06FF]+?)(?:\n|compte)",
            "customer_address": r"(?:adresse|address|rue)[\s:]*([A-Za-z\d\s,.\u0600-\u06FF]+?)(?:\n|client)",
            "account_number": r"(?:compte|account|numéro)[\s:]*(\d+)",
            "bill_date": r"(?:date|du|depuis)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            "due_date": r"(?:échéance|due|avant)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            "amount_due": r"(?:montant|total|amount|à payer)[\s:]*(\d+[.,]\d{2})\s*(?:TND|DT|₦)",
            "consumption": r"(?:consommation|consumption|kwh)[\s:]*(\d+(?:[.,]\d+)?)\s*(?:kwh|kWh)",
            "period": r"(?:période|period|mois)[\s:]*([A-Za-z\d\s/-]+?)(?:\n|date)"
        }
    },
    "SONEDE_BILL": {
        "keywords": ["SONEDE", "eau", "water", "m³", "consommation d'eau", "شركة المياه"],
        "fields": {
            "customer_name": r"(?:nom|name|client)[\s:]*([A-Za-z\s\u0600-\u06FF]+?)(?:\n|compte)",
            "customer_address": r"(?:adresse|address|rue)[\s:]*([A-Za-z\d\s,.\u0600-\u06FF]+?)(?:\n|client)",
            "account_number": r"(?:compte|account|numéro)[\s:]*(\d+)",
            "bill_date": r"(?:date|du|depuis)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            "due_date": r"(?:échéance|due|avant)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            "amount_due": r"(?:montant|total|amount|à payer)[\s:]*(\d+[.,]\d{2})\s*(?:TND|DT|₦)",
            "consumption": r"(?:consommation|consumption|m³)[\s:]*(\d+(?:[.,]\d+)?)\s*(?:m³|m3)",
            "period": r"(?:période|period|du)[\s:]*([A-Za-z\d\s/-]+?)(?:\n|date)"
        }
    },
    "D17_FORM": {
        "keywords": ["D17", "déclaration", "impôts", "revenus", "tax declaration", "النموذج"],
        "fields": {
            "taxpayer_name": r"(?:nom|name|déclarant)[\s:]*([A-Za-z\s\u0600-\u06FF]+?)(?:\n|prenom)",
            "taxpayer_id": r"(?:cin|id|numéro)[\s:]*([A-Za-z\d]+)",
            "year": r"(?:année|year|exercice)[\s:]*(\d{4})",
            "total_income": r"(?:revenu|income|total)[\s:]*(\d+[.,]\d{2})\s*(?:TND|DT|₦)?",
            "tax_amount": r"(?:impôt|tax|montant)[\s:]*(\d+[.,]\d{2})\s*(?:TND|DT|₦)?",
            "filing_date": r"(?:date|filed|déposée)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
        }
    },
    "BANK_STATEMENT": {
        "keywords": ["banque", "bank", "compte", "account", "transaction", "solde", "balance"],
        "fields": {
            "bank_name": r"(?:banque|bank)[\s:]*([A-Za-z\s\u0600-\u06FF]+?)(?:\n|compte)",
            "account_number": r"(?:compte|account|numéro)[\s:]*([A-Za-z\d]+)",
            "account_holder": r"(?:titulaire|holder|client)[\s:]*([A-Za-z\s\u0600-\u06FF]+?)(?:\n|date)",
            "statement_period": r"(?:période|period|du)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*(?:au|to)\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            "opening_balance": r"(?:solde|balance|ouverture)[\s:]*(\d+[.,]\d{2})",
            "closing_balance": r"(?:clôture|closing|final)[\s:]*(\d+[.,]\d{2})",
            "total_debits": r"(?:débits|debits|dépenses)[\s:]*(\d+[.,]\d{2})",
            "total_credits": r"(?:crédits|credits|revenus)[\s:]*(\d+[.,]\d{2})"
        }
    },
    "GENERIC": {
        "keywords": [""],  # Match any document
        "fields": {
            "name": r"(?:nom|name|client|applicant)[\s:]*([A-Za-z\s\u0600-\u06FF]+?)(?:\n|$)",
            "credit_score": r"(?:score|crédit|credit)[\s:]*(\d+)",
            "monthly_income": r"(?:revenu|income|salary|salaire)[\s:]*(\d+[.,]\d{0,2})",
            "savings_balance": r"(?:savings|épargne|balance|solde)[\s:]*(\d+[.,]\d{0,2})",
            "email": r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})",
            "phone": r"(?:phone|téléphone|mobile)[\s:]*(\+?[\d\s\-\.()]{7,})",
            "address": r"(?:address|adresse|rue|street)[\s:]*([A-Za-z\d\s,.\-\u0600-\u06FF]+?)(?:\n|$)"
        }
    }
}


def extract_text_from_pdf(pdf_path: str) -> Tuple[str, float]:
    """
    Extract text from PDF using DocTR OCR
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        (extracted_text, confidence_score)
    """
    
    if not DOCTR_AVAILABLE:
        raise ImportError("DocTR not installed. Run: pip install python-doctr")
    
    try:
        model = initialize_ocr()
        
        print(f"📄 Processing PDF: {pdf_path}")
        
        # Load and process the document
        doc = DocumentFile.from_pdf(pdf_path)
        result = model(doc)
        
        # Extract text from all pages
        extracted_text = ""
        confidence_scores = []
        
        for page in result.pages:
            for block in page.blocks:
                for line in block.lines:
                    for word in line.words:
                        extracted_text += word.value + " "
                        if hasattr(word, 'confidence'):
                            confidence_scores.append(word.confidence)
        
        # Calculate average confidence
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        
        print(f"✅ Text extracted: {len(extracted_text)} characters")
        print(f"📊 Average confidence: {avg_confidence:.2%}")
        
        return extracted_text.strip(), avg_confidence
        
    except Exception as e:
        print(f"❌ Error extracting text from PDF: {e}")
        raise


def detect_document_type(text: str) -> Tuple[str, float]:
    """
    Detect document type based on keywords
    
    Args:
        text: Extracted text from document
    
    Returns:
        (document_type, confidence_score)
    """
    
    text_lower = text.lower()
    scores = {}
    
    for doc_type, config in DOCUMENT_PATTERNS.items():
        matches = 0
        for keyword in config["keywords"]:
            if keyword.lower() in text_lower:
                matches += 1
        
        if matches > 0:
            # Confidence based on number of keyword matches
            scores[doc_type] = matches / len(config["keywords"])
    
    if not scores:
        print("⚠️  Could not detect document type. Using generic extraction.")
        return "UNKNOWN", 0.0
    
    # Return the document type with highest confidence
    best_match = max(scores.items(), key=lambda x: x[1])
    print(f"🔍 Detected document type: {best_match[0]} (confidence: {best_match[1]:.2%})")
    
    return best_match[0], best_match[1]


def extract_fields(text: str, document_type: str) -> Dict[str, Any]:
    """
    Extract specific fields based on document type
    
    Args:
        text: Extracted text from document
        document_type: Type of document
    
    Returns:
        Dictionary of extracted fields
    """
    
    extracted_fields = {}
    
    if document_type not in DOCUMENT_PATTERNS:
        print(f"⚠️  No extraction patterns for {document_type}")
        return extracted_fields
    
    patterns = DOCUMENT_PATTERNS[document_type]["fields"]
    
    for field_name, pattern in patterns.items():
        try:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                
                # Clean up common formatting issues
                value = value.replace("  ", " ")
                
                # Try to convert to appropriate type
                if "amount" in field_name.lower() or "consumption" in field_name.lower():
                    # Convert to float
                    value_clean = re.sub(r'[^\d.,]', '', value)
                    value_clean = value_clean.replace(',', '.')
                    try:
                        value = float(value_clean)
                    except ValueError:
                        pass
                elif "date" in field_name.lower():
                    # Standardize date format
                    value = standardize_date(value)
                
                extracted_fields[field_name] = value
                print(f"   ✓ {field_name}: {value}")
            else:
                print(f"   ✗ {field_name}: Not found")
                
        except Exception as e:
            print(f"   ⚠️  Error extracting {field_name}: {e}")
    
    return extracted_fields


def standardize_date(date_str: str) -> str:
    """
    Convert various date formats to ISO format (YYYY-MM-DD)
    
    Args:
        date_str: Date string in various formats
    
    Returns:
        Standardized date string (YYYY-MM-DD) or original if parsing fails
    """
    
    # Try various date patterns
    patterns = [
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', lambda m: f"{m.group(3)}-{m.group(2)}-{m.group(1)}"),
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{2})', lambda m: f"20{m.group(3)}-{m.group(2)}-{m.group(1)}"),
        (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', lambda m: f"{m.group(1)}-{m.group(2)}-{m.group(3)}"),
    ]
    
    for pattern, converter in patterns:
        match = re.search(pattern, date_str)
        if match:
            try:
                return converter(match)
            except:
                pass
    
    return date_str  # Return original if no pattern matches


def process_document(pdf_path: str) -> Dict[str, Any]:
    """
    Complete document processing pipeline
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        Structured JSON with extracted data
    """
    
    print(f"\n📑 Processing document: {Path(pdf_path).name}")
    print("=" * 60)
    
    try:
        # Step 1: Extract text from PDF
        print("\n1️⃣  Extracting text from PDF...")
        raw_text, ocr_confidence = extract_text_from_pdf(pdf_path)
        
        # Step 2: Detect document type
        print("\n2️⃣  Detecting document type...")
        document_type, type_confidence = detect_document_type(raw_text)
        
        # Step 3: Extract fields
        print(f"\n3️⃣  Extracting fields for {document_type}...")
        extracted_fields = extract_fields(raw_text, document_type)
        
        # Calculate overall confidence
        overall_confidence = (ocr_confidence + type_confidence) / 2
        
        result = {
            "document_type": document_type,
            "extracted_fields": extracted_fields,
            "raw_text": raw_text[:1000],  # Store first 1000 chars to save space
            "confidence_score": round(overall_confidence, 3),
            "ocr_confidence": round(ocr_confidence, 3),
            "type_confidence": round(type_confidence, 3),
            "field_count": len(extracted_fields),
            "status": "success" if extracted_fields else "partial"
        }
        
        print("\n" + "=" * 60)
        print(f"✅ Processing complete!")
        print(f"   Document type: {document_type}")
        print(f"   Fields extracted: {len(extracted_fields)}")
        print(f"   Confidence: {overall_confidence:.2%}")
        print("=" * 60 + "\n")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error processing document: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "document_type": "ERROR",
            "extracted_fields": {},
            "raw_text": "",
            "confidence_score": 0.0,
            "status": "error",
            "error": str(e)
        }


def batch_process_documents(pdf_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Process multiple documents
    
    Args:
        pdf_paths: List of PDF file paths
    
    Returns:
        List of extraction results
    """
    
    results = []
    for pdf_path in pdf_paths:
        result = process_document(pdf_path)
        results.append(result)
    
    return results
