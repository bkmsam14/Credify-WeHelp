from core.ocr_extractor import extract_text_from_image
from PIL import Image, ImageDraw
import tempfile
from pathlib import Path

# Create a test image
with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
    img = Image.new('RGB', (800, 600), color='white')
    d = ImageDraw.Draw(img)
    
    d.text((50, 50), "FINANCIAL STATEMENT", fill='black')
    d.text((50, 100), "Customer Name: John Doe", fill='black')
    d.text((50, 150), "Credit Score: 750", fill='black')
    d.text((50, 200), "Monthly Income: 5000", fill='black')
    d.text((50, 250), "Savings Balance: 15000", fill='black')
    
    img.save(f.name)
    test_file = f.name

print("[TEST] Extracting raw text from image...")
text, confidence = extract_text_from_image(test_file)

print(f"\nExtracted text:")
print("=" * 60)
print(text)
print("=" * 60)
print(f"\nConfidence: {confidence}")

Path(test_file).unlink()
