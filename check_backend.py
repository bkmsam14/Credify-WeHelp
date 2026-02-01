"""
Debug: Check what documents are actually stored on the backend
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def debug_backend_state():
    """Check what the backend has"""
    print("\n" + "="*70)
    print("BACKEND DEBUG STATE")
    print("="*70)
    
    # Get all documents
    response = requests.get(f"{BASE_URL}/api/debug/documents")
    if response.status_code != 200:
        print(f"✗ Failed to get debug info: {response.status_code}")
        return
    
    data = response.json()
    print(f"\nTotal applications: {data.get('total_apps', 0)}")
    print(f"\nApplications and their documents:")
    
    for app_id, docs_summary in data.get('documents', {}).items():
        print(f"\n  App ID: {app_id}")
        for doc_summary in docs_summary:
            print(f"    - Document: {doc_summary.get('id')}")
            print(f"      Filename: {doc_summary.get('filename')}")
            print(f"      Status: {doc_summary.get('status')}")
            print(f"      Extracted fields: {doc_summary.get('extracted_fields')}")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    debug_backend_state()
