#!/usr/bin/env python3
"""
Quick diagnostic: Check if extracted data is properly available
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def diagnose():
    print("\n" + "="*70)
    print("DIAGNOSTIC: Extracted Data & Analysis Flow")
    print("="*70)
    
    # Check backend state
    print("\n[1] Checking backend document state...")
    try:
        r = requests.get(f"{BASE_URL}/api/debug/documents")
        data = r.json()
        
        total_apps = data.get('total_apps', 0)
        print(f"  Total applications in backend: {total_apps}")
        
        if total_apps == 0:
            print("  ⚠️  No applications yet. Create an analysis first.")
            return
        
        for app_id, docs in data.get('documents', {}).items():
            print(f"\n  App: {app_id}")
            for doc in docs:
                status = doc.get('status')
                extracted_data = doc.get('extracted_data', {})
                fields = list(extracted_data.keys()) if extracted_data else []
                
                print(f"    📄 {doc.get('id')}")
                print(f"       Status: {status}")
                print(f"       Extracted fields: {fields}")
                
                if extracted_data:
                    for k, v in extracted_data.items():
                        print(f"         • {k}: {v}")
                else:
                    print(f"         ⚠️  No extracted data")
    
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return
    
    print("\n[2] What should happen next:")
    print("  1. Make sure document status is 'extracted' (not 'pending')")
    print("  2. Verify extracted fields are shown above")
    print("  3. In the frontend Documents page:")
    print("     - Document should show the extracted fields")
    print("     - 'Analyze with This Data' button should be green and enabled")
    print("     - Click it to re-analyze with extracted data")
    print("  4. Check logs for '[DOCS]' messages in browser console")
    print("  5. Check API logs for '[INFO] RECEIVED DATA FROM FRONTEND'")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    diagnose()
