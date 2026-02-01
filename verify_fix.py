#!/usr/bin/env python3
"""
QUICK START: Verify the extracted data fix is working

Run this script to quickly check if the system is working correctly.
"""
import subprocess
import time
import sys

def run_test():
    print("\n" + "="*80)
    print("QUICK TEST: Extracted Data Flow (3-step verification)")
    print("="*80)
    
    # Step 1: Check if backend is running
    print("\n[STEP 1] Checking if API is running...")
    try:
        import requests
        r = requests.get("http://localhost:8001/api/status", timeout=2)
        if r.status_code == 200:
            print("✓ API is running on port 8001")
        else:
            print("✗ API responded with error. Check terminal for issues.")
            print("  Run: python api.py")
            return False
    except:
        print("✗ API is not running on port 8001")
        print("\n  To start the API:")
        print("  1. Open a terminal")
        print("  2. Navigate to: c:\\Users\\dell\\Documents\\cardibih")
        print("  3. Run: python api.py")
        print("  4. Wait for message: [OK] OCR integration loaded")
        print("\n  Then run this script again.")
        return False
    
    # Step 2: Run the automated test
    print("\n[STEP 2] Running automated extracted data flow test...")
    print("  (Testing: initial analysis → extracted data → re-analysis with extracted values)")
    
    try:
        result = subprocess.run(
            [sys.executable, "test_extracted_flow.py"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if "TEST PASSED" in result.stdout:
            print("✓ Extracted data flow test PASSED")
            print("\n  Details:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(f"  {line}")
            return True
        else:
            print("✗ Extracted data flow test FAILED")
            print("\n  Output:")
            print(result.stdout)
            if result.stderr:
                print("\n  Errors:")
                print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Test timed out (API not responding)")
        return False
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return False

def show_next_steps(success):
    print("\n" + "="*80)
    
    if success:
        print("✅ VERIFICATION PASSED - Fix is working!")
        print("="*80)
        print("\nYou can now:")
        print("  1. Test manually in the frontend (http://localhost:3000)")
        print("  2. Upload a document with different credit score")
        print("  3. Verify PD score changes when re-analyzing")
        print("\nFor detailed testing guide, see: manual_test.md")
        
    else:
        print("⚠️  VERIFICATION FAILED - Debugging needed")
        print("="*80)
        print("\nTroubleshooting steps:")
        print("\n1. Verify API is running correctly:")
        print("   - Check that terminal shows: [OK] OCR integration loaded")
        print("   - If not, check for errors and fix them")
        print("\n2. Check backend state:")
        print("   python diagnose.py")
        print("   -> Should show applications and documents")
        print("\n3. Check for extraction errors:")
        print("   - Are documents status='extracted' or 'pending'?")
        print("   - If pending, wait 10+ more seconds")
        print("   - If pending_error, check OCR extraction in core/ocr_extractor.py")
        print("\n4. Check browser console:")
        print("   - Open DevTools (F12)")
        print("   - Look for [DOCS] messages (pink/cyan colored logs)")
        print("   - Should see extracted_data content")
        print("\n5. Manual debugging:")
        print("   python check_backend.py")
        print("   -> Shows full backend state with extracted values")

if __name__ == "__main__":
    success = run_test()
    show_next_steps(success)
    sys.exit(0 if success else 1)
