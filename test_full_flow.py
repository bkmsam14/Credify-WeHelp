"""
Test: Full flow - Initial analysis → Upload doc → Extract → Re-analyze
"""
import requests
import json
import time
from PIL import Image, ImageDraw
import tempfile
import os

BASE_URL = "http://localhost:8001"

def create_low_credit_doc():
    img = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(img)
    lines = ["FINANCIAL STATEMENT", "Customer Name: Test", "Credit Soore: 600", "Monthty Income: 4500", "Savings Balance: 12000"]
    y = 30
    for line in lines:
        draw.text((20, y), line, fill='black')
        y += 50
    temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    img.save(temp.name)
    return temp.name

def test_full_flow():
    print("\n" + "="*70)
    print("FULL FLOW TEST: Initial → Upload → Extract → Re-analyze")
    print("="*70)
    
    # Step 1: Initial analysis
    print("\n[1] Initial analysis with credit_score=680...")
    initial_data = {
        "age": 35, "education_level": 2, "employment_type": 2, "employment_years": 5,
        "monthly_income": 3500, "fixed_monthly_expenses": 1200, "debt_to_income_ratio": 0.34,
        "savings_balance": 8000, "loan_amount": 15000, "loan_duration_months": 36,
        "loan_purpose": 0, "credit_score": 680, "late_payments_12m": 1,
        "missed_payments_12m": 0, "utility_bill_on_time_ratio": 0.92,
        "income_inflation_ratio": 1.0, "document_mismatch_flag": 0,
        "application_velocity": 1, "geo_location_mismatch": 0, "metadata_anomaly_score": 0.05,
    }
    
    r1 = requests.post(f"{BASE_URL}/api/analyze", json=initial_data)
    if r1.status_code != 200:
        print(f"✗ Analysis 1 failed: {r1.status_code}")
        return False
    
    result1 = r1.json()
    app_id = result1['application_id']
    pd1 = result1['pd_percent']
    
    print(f"✓ Initial PD: {pd1}%")
    print(f"✓ App ID: {app_id}")
    
    # Step 2: Upload document
    print(f"\n[2] Uploading document with lower credit_score (600)...")
    doc_path = create_low_credit_doc()
    
    with open(doc_path, 'rb') as f:
        r2 = requests.post(f"{BASE_URL}/api/documents/upload/{app_id}", files={'file': f})
    
    if r2.status_code != 200:
        print(f"✗ Upload failed: {r2.status_code}")
        os.unlink(doc_path)
        return False
    
    doc_id = r2.json()['document']['id']
    print(f"✓ Document uploaded: {doc_id}")
    
    # Step 3: Wait for extraction
    print(f"\n[3] Waiting for extraction...")
    extracted_data = None
    
    for i in range(15):
        r3 = requests.get(f"{BASE_URL}/api/documents/{app_id}/{doc_id}/status")
        status = r3.json()
        
        if status['status'] in ['extracted', 'extracted_with_issues']:
            extracted_data = status.get('extracted_data', {})
            print(f"✓ Extracted: {extracted_data}")
            break
        
        print(f"  Waiting... ({status['status']})")
        time.sleep(0.5)
    
    if not extracted_data:
        print(f"✗ Extraction timeout")
        os.unlink(doc_path)
        return False
    
    # Step 4: Re-analyze with extracted data
    print(f"\n[4] Re-analyzing with extracted credit_score={extracted_data.get('credit_score')}...")
    
    # This is what the frontend does - merge extracted with original
    reanalysis_data = {
        **initial_data,
        "credit_score": extracted_data.get('credit_score', initial_data['credit_score']),
        "monthly_income": extracted_data.get('monthly_income', initial_data['monthly_income']),
    }
    
    r4 = requests.post(f"{BASE_URL}/api/analyze", json=reanalysis_data)
    if r4.status_code != 200:
        print(f"✗ Re-analysis failed: {r4.status_code}")
        os.unlink(doc_path)
        return False
    
    result2 = r4.json()
    pd2 = result2['pd_percent']
    
    print(f"✓ Re-analyzed PD: {pd2}%")
    
    # Step 5: Compare
    print(f"\n[5] Comparison:")
    print(f"  Initial (cs=680): PD = {pd1}%")
    print(f"  Re-analyzed (cs={extracted_data.get('credit_score')}): PD = {pd2}%")
    print(f"  Change: {pd2 - pd1:+.1f}%")
    
    if extracted_data.get('credit_score') < 680 and pd2 > pd1:
        print(f"\n✅ SUCCESS: PD increased when credit_score decreased!")
        os.unlink(doc_path)
        return True
    else:
        print(f"\n❌ FAILURE: Expected PD to increase")
        os.unlink(doc_path)
        return False

if __name__ == "__main__":
    success = test_full_flow()
    print("\n" + "="*70)
    if success:
        print("✅ FULL FLOW TEST PASSED")
    else:
        print("❌ FULL FLOW TEST FAILED")
    print("="*70)
