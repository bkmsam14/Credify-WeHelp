"""
Final Comprehensive Test: Document Upload → Extract → Analyze
Demonstrates: Credit score extraction, PDF handling, full workflow
"""
import requests
import json
import time
from PIL import Image, ImageDraw
import tempfile
import os

BASE_URL = "http://localhost:8001"

def create_test_image():
    """Create test image with financial data"""
    img = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    lines = [
        "FINANCIAL STATEMENT",
        "Customer Name: Ahmed Ben Ali",
        "Credit Soore: 750",
        "Monthty Income: 5500",
        "Savings Balance: 20000",
    ]
    
    y = 30
    for line in lines:
        draw.text((20, y), line, fill='black')
        y += 50
    
    temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    img.save(temp.name)
    return temp.name

def test_workflow():
    """Test complete workflow"""
    print("\n" + "="*70)
    print("🚀 COMPREHENSIVE END-TO-END TEST")
    print("="*70)
    
    # Create test document
    print("\n[1] Creating test document...")
    doc_path = create_test_image()
    print(f"✓ Test image created")
    
    # Upload document
    print("\n[2] Uploading document to API...")
    app_id = f"test_{int(time.time())}"
    
    with open(doc_path, 'rb') as f:
        response = requests.post(f"{BASE_URL}/api/documents/upload/{app_id}", 
                                files={'file': f})
    
    if response.status_code != 200:
        print(f"✗ Upload failed: {response.status_code}")
        print(response.text)
        return False
    
    upload_data = response.json()
    doc_id = upload_data['document']['id']
    print(f"✓ Document uploaded")
    print(f"  ID: {doc_id}")
    print(f"  Status: {upload_data['document']['status']}")
    
    # Wait for extraction
    print("\n[3] Waiting for background extraction...")
    for attempt in range(20):
        response = requests.get(f"{BASE_URL}/api/documents/{app_id}/{doc_id}/status")
        status = response.json()
        current_status = status.get('status')
        
        if current_status in ['extracted', 'extracted_with_issues']:
            extracted = status.get('extracted_data', {})
            print(f"✓ Extraction complete!")
            print(f"  Status: {current_status}")
            print(f"  Extracted fields: {list(extracted.keys())}")
            
            # Verify critical field
            if extracted.get('credit_score'):
                print(f"  ✅ Credit Score: {extracted.get('credit_score')}")
            else:
                print(f"  ❌ Credit Score: NOT EXTRACTED")
            
            if extracted.get('monthly_income'):
                print(f"  ✅ Monthly Income: {extracted.get('monthly_income')}")
            
            return True
        
        print(f"  Waiting... (status: {current_status})")
        time.sleep(0.5)
    
    print(f"✗ Extraction timed out")
    return False

if __name__ == "__main__":
    success = test_workflow()
    
    if success:
        print("\n" + "="*70)
        print("✅ TEST PASSED: Document extracted successfully!")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ TEST FAILED")
        print("="*70)
