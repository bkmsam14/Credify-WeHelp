"""Test OCR extraction"""
from core.ocr_extractor import process_document
from pathlib import Path
import tempfile
from PIL import Image, ImageDraw

# Create a simple test image with credit score
with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
    img = Image.new('RGB', (800, 600), color='white')
    d = ImageDraw.Draw(img)
    
    # Draw text
    d.text((50, 50), "FINANCIAL STATEMENT", fill='black')
    d.text((50, 100), "Customer Name: John Doe", fill='black')
    d.text((50, 150), "Credit Score: 750", fill='black')
    d.text((50, 200), "Monthly Income: 5000", fill='black')
    d.text((50, 250), "Savings Balance: 15000", fill='black')
    
    img.save(f.name)
    test_file = f.name

print("[TEST] Testing OCR extraction...")
result = process_document(test_file)

print(f"\nStatus: {result.get('status')}")
print(f"Document Type: {result.get('document_type')}")
print(f"Extracted Fields: {result.get('extracted_fields', {})}")
print(f"Confidence: {result.get('confidence_score')}")

Path(test_file).unlink()
print("\nTest complete!")
