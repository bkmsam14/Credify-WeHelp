"""
Test: Document extraction → Analysis with extracted data updates PD score
"""
import requests
import json
import time
from PIL import Image, ImageDraw
import tempfile
import os

BASE_URL = "http://localhost:8001"

def create_test_image_with_low_credit():
    """Create test image with LOW credit score to increase PD"""
    img = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    lines = [
        "FINANCIAL STATEMENT",
        "Customer Name: Test User",
        "Credit Soore: 600",  # LOW score - should increase PD
        "Monthty Income: 5000",
        "Savings Balance: 10000",
    ]
    
    y = 30
    for line in lines:
        draw.text((20, y), line, fill='black')
        y += 50
    
    temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    img.save(temp.name)
    return temp.name

def test_pd_update_with_extracted_data():
    """Test that PD score updates based on extracted credit score"""
    print("\n" + "="*70)
    print("TEST: PD Score Update with Extracted Document Data")
    print("="*70)
    
    # Step 1: Initial analysis with default data (credit_score=680)
    print("\n[STEP 1] Initial analysis with default data (credit_score=680)...")
    
    initial_data = {
        "age": 35,
        "education_level": 2,
        "employment_type": 2,
        "employment_years": 5,
        "monthly_income": 3500,
        "fixed_monthly_expenses": 1200,
        "debt_to_income_ratio": 0.34,
        "savings_balance": 8000,
        "loan_amount": 15000,
        "loan_duration_months": 36,
        "loan_purpose": 0,
        "credit_score": 680,  # Default
        "late_payments_12m": 1,
        "missed_payments_12m": 0,
        "utility_bill_on_time_ratio": 0.92,
        "income_inflation_ratio": 1.0,
        "document_mismatch_flag": 0,
        "application_velocity": 1,
        "geo_location_mismatch": 0,
        "metadata_anomaly_score": 0.05,
    }
    
    response = requests.post(f"{BASE_URL}/api/analyze", json=initial_data)
    if response.status_code != 200:
        print(f"✗ Initial analysis failed: {response.status_code}")
        print(response.text)
        return False
    
    initial_result = response.json()
    initial_pd = initial_result.get('pd_percent', 0)
    app_id = initial_result.get('application_id', 'UNKNOWN')
    
    print(f"✓ Initial analysis complete")
    print(f"  Application ID: {app_id}")
    print(f"  Credit Score: 680 (default)")
    print(f"  PD Score: {initial_pd}%")
    
    # Step 2: Create and upload document with LOW credit score
    print("\n[STEP 2] Create and upload document with LOW credit score (600)...")
    
    doc_path = create_test_image_with_low_credit()
    
    with open(doc_path, 'rb') as f:
        response = requests.post(
            f"{BASE_URL}/api/documents/upload/{app_id}",
            files={'file': f}
        )
    
    if response.status_code != 200:
        print(f"✗ Upload failed: {response.status_code}")
        return False
    
    upload_result = response.json()
    doc_id = upload_result['document']['id']
    print(f"✓ Document uploaded")
    print(f"  Document ID: {doc_id}")
    
    # Step 3: Wait for extraction
    print("\n[STEP 3] Waiting for background extraction...")
    
    extracted_credit_score = None
    for attempt in range(15):
        response = requests.get(f"{BASE_URL}/api/documents/{app_id}/{doc_id}/status")
        status = response.json()
        current_status = status.get('status')
        
        if current_status in ['extracted', 'extracted_with_issues']:
            extracted = status.get('extracted_data', {})
            extracted_credit_score = extracted.get('credit_score')
            print(f"✓ Extraction complete")
            print(f"  Status: {current_status}")
            print(f"  Extracted credit_score: {extracted_credit_score}")
            break
        
        print(f"  Waiting... (status: {current_status})")
        time.sleep(0.5)
    
    if extracted_credit_score is None:
        print(f"✗ Extraction failed or timed out")
        return False
    
    # Step 4: Analyze with extracted data (lower credit score)
    print(f"\n[STEP 4] Re-analyze with extracted data (credit_score={extracted_credit_score})...")
    
    analysis_with_extracted = {
        **initial_data,
        "credit_score": extracted_credit_score,  # Use extracted LOW score
    }
    
    response = requests.post(f"{BASE_URL}/api/analyze", json=analysis_with_extracted)
    if response.status_code != 200:
        print(f"✗ Analysis failed: {response.status_code}")
        return False
    
    result_with_extracted = response.json()
    pd_with_extracted = result_with_extracted.get('pd_percent', 0)
    
    print(f"✓ Analysis with extracted data complete")
    print(f"  Credit Score: {extracted_credit_score} (from document)")
    print(f"  PD Score: {pd_with_extracted}%")
    
    # Step 5: Compare results
    print("\n[STEP 5] Comparison:")
    print("-" * 70)
    print(f"Initial (credit_score=680): PD = {initial_pd}%")
    print(f"Extracted (credit_score={extracted_credit_score}): PD = {pd_with_extracted}%")
    
    pd_change = pd_with_extracted - initial_pd
    print(f"\nPD Change: {pd_change:+.1f}%")
    
    if extracted_credit_score < 680:
        # Lower credit score should INCREASE PD (higher default risk)
        if pd_with_extracted > initial_pd:
            print(f"\n✅ SUCCESS: PD correctly INCREASED when credit score decreased")
            print(f"   Lower credit score ({extracted_credit_score}) → Higher default risk")
            os.unlink(doc_path)
            return True
        else:
            print(f"\n❌ FAILURE: PD did not increase despite lower credit score")
            os.unlink(doc_path)
            return False
    
    os.unlink(doc_path)
    return False

if __name__ == "__main__":
    success = test_pd_update_with_extracted_data()
    
    print("\n" + "="*70)
    if success:
        print("✅ TEST PASSED: Extracted data correctly updates PD score")
    else:
        print("❌ TEST FAILED: Extracted data not affecting PD score")
    print("="*70)
