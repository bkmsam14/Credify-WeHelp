"""
DocTR Installation and Setup Guide
Run this script to install and verify DocTR for the loan application system
"""

import subprocess
import sys
import os


def install_doctr():
    """Install python-doctr and dependencies"""
    
    print("\n" + "="*70)
    print("📦 Installing DocTR for Document Extraction")
    print("="*70)
    
    packages = [
        "python-doctr",
        "torch",
        "torchvision",
        "torchaudio",
    ]
    
    for package in packages:
        print(f"\n⏳ Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Failed to install {package}: {e}")
            if "torch" in package:
                print("   Note: PyTorch installation may require specific instructions.")
                print("   Visit https://pytorch.org for platform-specific installation.")
    
    print("\n" + "="*70)
    print("✅ Installation complete!")
    print("="*70)


def verify_doctr():
    """Verify DocTR is properly installed"""
    
    print("\n" + "="*70)
    print("🔍 Verifying DocTR Installation")
    print("="*70)
    
    try:
        from doctr.io import DocumentFile
        from doctr.models import ocr_predictor
        print("✅ DocTR imported successfully")
        
        print("⏳ Loading OCR model (this may take a moment)...")
        ocr = ocr_predictor(pretrained=True)
        print("✅ OCR model loaded successfully")
        
        print("\n" + "="*70)
        print("🎉 DocTR is ready to use!")
        print("="*70)
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n⚙️  Troubleshooting:")
        print("  1. Run: python -m pip install python-doctr")
        print("  2. For PyTorch, visit: https://pytorch.org")
        print("  3. Ensure Python 3.8+ is installed")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Main setup routine"""
    
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  DocTR Setup for Loan Application System".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    # Check if DocTR is already installed
    print("\n1️⃣  Checking current installation...")
    try:
        from doctr.models import ocr_predictor
        print("   ✅ DocTR is already installed")
        print("\n   Skipping installation. Running verification...")
    except ImportError:
        print("   ℹ️  DocTR not found")
        print("\n2️⃣  Installing DocTR...")
        install_doctr()
    
    # Verify installation
    print("\n3️⃣  Verifying installation...")
    success = verify_doctr()
    
    if success:
        print("\n" + "="*70)
        print("📖 Usage Instructions:")
        print("="*70)
        print("""
from core.doctr_extractor import process_document

# Process a single PDF
result = process_document("path/to/document.pdf")
print(result)

# Result format:
{
    "document_type": "STEG_BILL",
    "extracted_fields": {
        "customer_name": "...",
        "amount_due": 45.50,
        "consumption": 150.0,
        ...
    },
    "confidence_score": 0.85,
    "status": "success"
}

Supported documents:
  • STEG bills (electricity)
  • SONEDE bills (water)
  • D17 forms (tax declaration)
  • Bank statements
        """)
        print("="*70)
        return 0
    else:
        print("\n⚠️  Installation verification failed.")
        print("Please resolve the issues above and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
