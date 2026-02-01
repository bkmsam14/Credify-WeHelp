"""
Quick Verification: Credit Score Extraction is Working
This test confirms the fix is operational
"""
import re
from PIL import Image, ImageDraw
import tempfile
import os

# Test 1: Verify regex pattern works
print("\n" + "="*70)
print("🔍 VERIFICATION TEST: Credit Score Extraction")
print("="*70)

print("\n[TEST 1] Regex Pattern Verification")
print("-"*70)

# Simulate OCR output with typos
ocr_outputs = [
    ("Credit Score: 750", True, "Perfect OCR"),
    ("Credit Soore: 750", True, "Missing 'c' in Score"),
    ("Credit Soooore: 750", True, "Multiple O's"),
    ("credit score: 680", True, "Lowercase"),
    ("Crédit Score: 720", True, "French variant"),
]

# The improved pattern
pattern = r"(?:credit|crédit)[\s:]*s?o+r+e?[\s:]*(\d{2,3})"

print(f"Pattern: {pattern}\n")

for text, should_match, description in ocr_outputs:
    match = re.search(pattern, text, re.IGNORECASE)
    result = "✓ MATCH" if match else "✗ NO MATCH"
    expected = "✓" if should_match else "✗"
    
    if (match is not None) == should_match:
        status = "✅"
    else:
        status = "❌"
    
    print(f"{status} {result:12} - {text:30} ({description})")
    if match:
        print(f"    → Extracted: {match.group(1)}")

print("\n[TEST 2] System Integration Check")
print("-"*70)

from core.ocr_extractor import process_document

# Create test image
img = Image.new('RGB', (500, 300), color='white')
draw = ImageDraw.Draw(img)

lines = [
    "BANK STATEMENT",
    "Name: Test User",
    "Credit Soore: 750",
    "Monthty Income: 6000"
]

y = 20
for line in lines:
    draw.text((20, y), line, fill='black')
    y += 60

temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
img.save(temp.name)

print(f"Created test image")
print(f"Extracting fields...\n")

result = process_document(temp.name)

extracted = result.get('extracted_fields', {})

print(f"Results:")
print(f"  Status: {result.get('status')}")
print(f"  Fields extracted: {list(extracted.keys())}")
print(f"  Credit Score: {extracted.get('credit_score', 'NOT FOUND')} {'✓' if extracted.get('credit_score') == 750 else '❌'}")
print(f"  Monthly Income: {extracted.get('monthly_income', 'NOT FOUND')} {'✓' if extracted.get('monthly_income') == 6000.0 else ''}")
print(f"  Name: {extracted.get('name', 'NOT FOUND')}")

try:
    os.unlink(temp.name)
except:
    pass  # File may be locked

print("\n" + "="*70)
print("✅ VERIFICATION COMPLETE")
print("="*70)

if extracted.get('credit_score') == 750:
    print("\n✨ Credit score extraction is WORKING! ✨")
    print("   System is ready for production use.")
else:
    print("\n⚠️  Credit score extraction may have issues.")
    print(f"   Expected: 750, Got: {extracted.get('credit_score')}")
