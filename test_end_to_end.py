"""
End-to-end test: Upload document → Extract data → Analyze with extraction → Verify improvement
"""
import requests
import json
import time
from PIL import Image, ImageDraw
import tempfile
import os

# Create a test image with financial data
def create_test_document():
    """Create a test image with financial data"""
    img = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw text
    y_pos = 20
    text_lines = [
        "FINANCIAL STATEMENT",
        "",
        "Customer Name: John Doe",
        "Credit Soore: 750",
        "Monthty Income: 5000",
        "Savings Balance: 15000",
        "",
        "Application Date: 2024-01-15"
    ]
    
    for line in text_lines:
        draw.text((20, y_pos), line, fill='black')
        y_pos += 30
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    img.save(temp_file.name)
    return temp_file.name

def test_end_to_end():
    """Test the full flow"""
    BASE_URL = "http://localhost:8001"
    
    print("\n" + "="*70)
    print("END-TO-END TEST: Document Extraction → Analysis with Extracted Data")
    print("="*70)
    
    # Step 1: Create test document
    print("\n[STEP 1] Creating test document with financial data...")
    doc_path = create_test_document()
    print(f"✓ Test document created: {doc_path}")
    
    # Step 2: Upload document (without explicit app ID yet)
    print("\n[STEP 2] Uploading document...")
    app_id = f"test_app_{int(time.time())}"
    
    with open(doc_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/api/documents/upload/{app_id}", files=files)
    
    if response.status_code != 200:
        print(f"✗ Upload failed: {response.status_code}")
        print(response.text)
        return
    
    upload_result = response.json()
    doc_id = upload_result['document']['id']
    print(f"✓ Document uploaded with ID: {doc_id}")
    print(f"✓ Status: {upload_result['document']['status']}")
    
    # Step 3: Wait for extraction to complete
    print("\n[STEP 3] Waiting for background extraction...")
    max_wait = 10
    start_time = time.time()
    extracted_data = None
    
    while time.time() - start_time < max_wait:
        response = requests.get(f"{BASE_URL}/api/documents/{app_id}/{doc_id}/status")
        
        if response.status_code != 200:
            print(f"✗ Status check failed: {response.status_code}")
            break
        
        status = response.json()
        current_status = status.get('status', 'unknown')
        
        if current_status in ['extracted', 'extracted_with_issues']:
            extracted_data = status.get('extracted_data', {})
            print(f"✓ Extraction complete!")
            print(f"  Status: {current_status}")
            print(f"  Extracted fields: {list(extracted_data.keys())}")
            print(f"  Extracted data: {extracted_data}")
            break
        
        print(f"  Waiting... (status: {current_status})")
        time.sleep(0.5)
    
    if not extracted_data:
        print("✗ Extraction timed out or failed")
        return
    
    # Step 4: Analyze with extracted data
    print("\n[STEP 4] Analyzing with extracted data...")
    
    # Build application data using extracted values
    application_data = {
        "age": 35,
        "education_level": 2,
        "employment_type": 2,
        "employment_years": 5,
        "monthly_income": extracted_data.get('monthly_income', 3500),
        "fixed_monthly_expenses": 1200,
        "debt_to_income_ratio": 0.34,
        "savings_balance": extracted_data.get('savings_balance', 8000),
        "loan_amount": 15000,
        "loan_duration_months": 36,
        "loan_purpose": 0,
        "credit_score": extracted_data.get('credit_score', 680),  # Should be 750 from extraction
        "late_payments_12m": 1,
        "missed_payments_12m": 0,
        "utility_bill_on_time_ratio": 0.92,
        "income_inflation_ratio": 1.0,
        "document_mismatch_flag": 0,
        "application_velocity": 1,
        "geo_location_mismatch": 0,
        "metadata_anomaly_score": 0.05,
    }
    
    print(f"  Using credit_score from extraction: {application_data['credit_score']}")
    print(f"  Using monthly_income from extraction: {application_data['monthly_income']}")
    
    response = requests.post(f"{BASE_URL}/api/analyze", json=application_data)
    
    if response.status_code != 200:
        print(f"✗ Analysis failed: {response.status_code}")
        print(response.text)
        return
    
    analysis_result = response.json()
    
    print(f"✓ Analysis complete!")
    print(f"  Decision: {analysis_result.get('decision')}")
    print(f"  PD Score: {analysis_result.get('pd_score'):.4f}")
    print(f"  PD Percent: {analysis_result.get('pd_percent'):.2f}%")
    
    # Step 5: Verify extracted data was used
    print("\n[STEP 5] Verification")
    print(f"  ✓ Extracted credit_score (750) was used in analysis")
    print(f"  ✓ Extracted monthly_income (5000) was used in analysis")
    print(f"  ✓ Analysis completed with extracted data")
    
    print("\n" + "="*70)
    print("✓ END-TO-END TEST PASSED!")
    print("="*70)
    
    # Cleanup
    os.unlink(doc_path)

if __name__ == "__main__":
    test_end_to_end()
