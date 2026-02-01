"""
OCR-based Document Extraction Module
Uses Tesseract OCR to extract text from documents and regex to parse fields
Supports: Simple documents, bills, forms, statements
"""

import re
import json
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
import pytesseract
from PIL import Image
import pdf2image
import os

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Document type patterns for detection and field extraction
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
            "account_number": r"(?:compte|account|numéro)[\s:]*(\d+)",
            "bill_date": r"(?:date|du|depuis)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            "amount_due": r"(?:montant|total|amount|à payer)[\s:]*(\d+[.,]\d{2})\s*(?:TND|DT|₦)",
            "consumption": r"(?:consommation|consumption|m³)[\s:]*(\d+(?:[.,]\d+)?)\s*(?:m³|m3)",
        }
    },
    "D17_FORM": {
        "keywords": ["D17", "déclaration", "impôts", "revenus", "tax declaration", "النموذج"],
        "fields": {
            "taxpayer_name": r"(?:nom|name|déclarant)[\s:]*([A-Za-z\s\u0600-\u06FF]+?)(?:\n|prenom)",
            "taxpayer_id": r"(?:cin|id|numéro)[\s:]*([A-Za-z\d]+)",
            "year": r"(?:année|year|exercice)[\s:]*(\d{4})",
            "total_income": r"(?:revenu|income|total)[\s:]*(\d+[.,]\d{2})\s*(?:TND|DT|₦)?",
        }
    },
    "BANK_STATEMENT": {
        "keywords": ["banque", "bank", "compte", "account", "transaction", "solde", "balance"],
        "fields": {
            "bank_name": r"(?:banque|bank)[\s:]*([A-Za-z\s\u0600-\u06FF]+?)(?:\n|compte)",
            "account_number": r"(?:compte|account|numéro)[\s:]*([A-Za-z\d]+)",
            "account_holder": r"(?:titulaire|holder|client)[\s:]*([A-Za-z\s\u0600-\u06FF]+?)(?:\n|date)",
            "closing_balance": r"(?:clôture|closing|final|solde)[\s:]*(\d+[.,]\d{2})",
        }
    },
    "GENERIC": {
        "keywords": [""],  # Match any document
        "fields": {
            "name": r"(?:nom|name|client|applicant|customer)[\s:]*([A-Za-z\s\u0600-\u06FF]+?)(?:\n|$)",
            "credit_score": r"(?:credit|crédit)[\s:]*s?o+r+e?[\s:]*(\d{2,3})",  # Handle OCR typos: score, soore, etc
            "monthly_income": r"(?:revenu|income|salary|salaire|month)[\s:]*(?:ly)?[\s:]*(\d+[.,]\d{0,2})",
            "savings_balance": r"(?:savings|épargne|balance|solde)[\s:]*(\d+[.,]\d{0,2})",
            "email": r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})",
            "phone": r"(?:phone|téléphone|mobile)[\s:]*(\+?[\d\s\-\.()]{7,})",
            "address": r"(?:address|adresse|rue|street)[\s:]*([A-Za-z\d\s,.\-\u0600-\u06FF]+?)(?:\n|$)"
        }
    }
}


def extract_text_from_pdf(pdf_path: str) -> Tuple[str, float]:
    """
    Extract text from PDF using Tesseract OCR
    Falls back to PyPDF2 if poppler is not available
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        (extracted_text, confidence_score)
    """
    try:
        print(f"📄 Processing PDF with Tesseract OCR: {Path(pdf_path).name}")
        
        # Try using pdf2image with poppler first
        try:
            images = pdf2image.convert_from_path(pdf_path)
            print(f"   Converted to {len(images)} page(s)")
            
            all_text = ""
            confidences = []
            
            # OCR each page
            for idx, image in enumerate(images):
                print(f"   📖 Processing page {idx + 1}/{len(images)}...")
                
                # Extract text with Tesseract
                text = pytesseract.image_to_string(image, lang='eng+fra+ara')
                all_text += text + "\n"
                
                # Get confidence data
                data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, lang='eng+fra+ara')
                confidences.extend([int(conf) for conf in data['conf'] if int(conf) > 0])
            
            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) / 100 if confidences else 0.5
            
            print(f"✅ Text extracted: {len(all_text)} characters")
            print(f"📊 Average OCR confidence: {avg_confidence:.2%}")
            
            return all_text.strip(), avg_confidence
            
        except Exception as pdf2img_err:
            # Fallback: Use PyPDF2 for text extraction without images
            print(f"   ⚠️  pdf2image failed ({str(pdf2img_err)[:50]}...)")
            print(f"   Falling back to PyPDF2 text extraction...")
            
            try:
                from PyPDF2 import PdfReader
                
                reader = PdfReader(pdf_path)
                all_text = ""
                
                for page_num, page in enumerate(reader.pages):
                    print(f"   📖 Extracting text from page {page_num + 1}/{len(reader.pages)}...")
                    page_text = page.extract_text()
                    if page_text:
                        all_text += page_text + "\n"
                
                # PyPDF2 text extraction is native, so confidence is higher
                # But it may miss some formatting/images, so we rate it 0.8
                confidence = 0.8 if all_text else 0.0
                
                print(f"✅ Text extracted: {len(all_text)} characters")
                print(f"📊 Fallback extraction confidence: {confidence:.2%}")
                
                return all_text.strip(), confidence
                
            except ImportError:
                print(f"   ⚠️  PyPDF2 not installed, trying alternative method...")
                # Last resort: Return empty text with error note
                return f"[PDF_EXTRACTION_FALLBACK_ERROR: {str(pdf2img_err)[:100]}]", 0.0
        
    except Exception as e:
        print(f"❌ Error extracting text from PDF: {e}")
        raise


def extract_text_from_image(image_path: str) -> Tuple[str, float]:
    """
    Extract text from image using Tesseract OCR
    
    Args:
        image_path: Path to the image file
    
    Returns:
        (extracted_text, confidence_score)
    """
    try:
        print(f"🖼️  Processing image with Tesseract OCR: {Path(image_path).name}")
        
        # Open image
        image = Image.open(image_path)
        
        # Extract text with Tesseract
        text = pytesseract.image_to_string(image, lang='eng+fra+ara')
        
        # Get confidence data
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, lang='eng+fra+ara')
        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
        
        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) / 100 if confidences else 0.5
        
        print(f"✅ Text extracted: {len(text)} characters")
        print(f"📊 Average OCR confidence: {avg_confidence:.2%}")
        
        return text.strip(), avg_confidence
        
    except Exception as e:
        print(f"❌ Error extracting text from image: {e}")
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
            if keyword and keyword.lower() in text_lower:
                matches += 1
        
        if matches > 0:
            scores[doc_type] = matches / len([k for k in config["keywords"] if k]) if config["keywords"] else 0
    
    if not scores:
        print("⚠️  Could not detect document type. Using GENERIC extraction.")
        return "GENERIC", 0.0
    
    best_match = max(scores.items(), key=lambda x: x[1])
    print(f"🔍 Detected document type: {best_match[0]} (confidence: {best_match[1]:.2%})")
    
    return best_match[0], best_match[1]


def extract_fields(text: str, document_type: str) -> Dict[str, Any]:
    """
    Extract specific fields based on document type
    Always includes GENERIC fields as fallback
    
    Args:
        text: Extracted text from document
        document_type: Type of document
    
    Returns:
        Dictionary of extracted fields
    """
    extracted_fields = {}
    
    # First try specific document type patterns
    if document_type in DOCUMENT_PATTERNS:
        patterns = DOCUMENT_PATTERNS[document_type]["fields"]
        
        for field_name, pattern in patterns.items():
            try:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    value = value.replace("  ", " ")
                    
                    # Try to convert to appropriate type
                    if "amount" in field_name.lower() or "consumption" in field_name.lower() or "balance" in field_name.lower() or "income" in field_name.lower():
                        value_clean = re.sub(r'[^\d.,]', '', value)
                        value_clean = value_clean.replace(',', '.')
                        try:
                            value = float(value_clean)
                        except ValueError:
                            pass
                    elif "score" in field_name.lower():
                        try:
                            value = int(re.sub(r'\D', '', value))
                        except ValueError:
                            pass
                    elif "date" in field_name.lower():
                        value = standardize_date(value)
                    
                    extracted_fields[field_name] = value
                    print(f"   ✓ {field_name}: {value}")
                else:
                    print(f"   ✗ {field_name}: Not found")
                    
            except Exception as e:
                print(f"   ⚠️  Error extracting {field_name}: {e}")
    else:
        print(f"⚠️  No extraction patterns for {document_type}")
    
    # Always try GENERIC patterns as fallback for missing fields
    if document_type != "GENERIC":
        print(f"\n   Trying GENERIC patterns as fallback...")
        generic_patterns = DOCUMENT_PATTERNS.get("GENERIC", {}).get("fields", {})
        
        for field_name, pattern in generic_patterns.items():
            # Skip if already extracted
            if field_name in extracted_fields:
                continue
                
            try:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    value = value.replace("  ", " ")
                    
                    # Try to convert to appropriate type
                    if "amount" in field_name.lower() or "consumption" in field_name.lower() or "balance" in field_name.lower() or "income" in field_name.lower():
                        value_clean = re.sub(r'[^\d.,]', '', value)
                        value_clean = value_clean.replace(',', '.')
                        try:
                            value = float(value_clean)
                        except ValueError:
                            pass
                    elif "score" in field_name.lower():
                        try:
                            value = int(re.sub(r'\D', '', value))
                        except ValueError:
                            pass
                    elif "date" in field_name.lower():
                        value = standardize_date(value)
                    
                    extracted_fields[field_name] = value
                    print(f"   ✓ {field_name} (generic): {value}")
                    
            except Exception as e:
                logger.debug(f"Error extracting generic {field_name}: {e}")
    
    return extracted_fields


def standardize_date(date_str: str) -> str:
    """
    Convert various date formats to ISO format (YYYY-MM-DD)
    """
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
    
    return date_str


def process_document(file_path: str) -> Dict[str, Any]:
    """
    Complete document processing pipeline using OCR
    
    Args:
        file_path: Path to document file
    
    Returns:
        Structured JSON with extracted data
    """
    print(f"\n📑 Processing document with OCR: {Path(file_path).name}")
    print("=" * 60)
    
    try:
        # Determine file type
        file_ext = Path(file_path).suffix.lower()
        
        # Step 1: Extract text
        print("\n1️⃣  Extracting text with Tesseract OCR...")
        if file_ext == '.pdf':
            raw_text, ocr_confidence = extract_text_from_pdf(file_path)
        else:
            raw_text, ocr_confidence = extract_text_from_image(file_path)
        
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
            "raw_text": raw_text[:1000],  # Store first 1000 chars
            "confidence_score": round(overall_confidence, 3),
            "ocr_confidence": round(ocr_confidence, 3),
            "type_confidence": round(type_confidence, 3),
            "field_count": len(extracted_fields),
            "extraction_method": "tesseract_ocr",
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
            "extraction_method": "tesseract_ocr",
            "status": "error",
            "error": str(e)
        }
