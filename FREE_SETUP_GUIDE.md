# FREE Document Extraction Setup Guide

## ✅ What You Need (All Free!)

Your document extraction system now uses **completely free tools**:

### 1. **Tesseract OCR** (Local, Free)
Extract text from documents locally on your computer.

#### Install Tesseract:

**Windows:**
```powershell
# Option 1: Using Chocolatey (easiest)
choco install tesseract

# Option 2: Download installer
# Visit: https://github.com/UB-Mannheim/tesseract/wiki
# Download and run tesseract-ocr-w64-setup-v5.x.x.exe
```

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

### 2. **Python Libraries** (Free)
```powershell
pip install pytesseract pillow
```

---

## 🚀 Quick Start

### Step 1: Ensure Tesseract is installed
```powershell
# Verify installation
tesseract --version
```

### Step 2: No configuration needed!
The system is already set to use completely free extraction:
- **OCR**: Tesseract (local)
- **Parsing**: Regex patterns (no API calls)
- **Cost**: $0.00

### Step 3: Restart backend
```powershell
cd c:\Users\dell\Documents\cardibih
python api.py
```

### Step 4: Upload documents
In the app's **Documents** tab:
1. Upload a document (bill, bank statement, payslip)
2. System automatically extracts:
   - Monthly income
   - Monthly expenses
   - Savings balance
   - Employment years
   - Credit score
   - Utility bill payment history
3. Fields auto-fill in the loan form

---

## 📋 Supported Document Types

| Document Type | Extracted Fields |
|---|---|
| **Payslip** | monthly_income, employment_years |
| **Bank Statement** | savings_balance, income_inflation_ratio |
| **STEG Bill** (Tunisia) | fixed_monthly_expenses, utility_bill_on_time_ratio |
| **ID Document** | document_date, geo_location validation |

---

## 💰 Cost Analysis

| Method | OCR Cost | Parsing Cost | Total/Doc |
|---|---|---|---|
| **Free (This Setup)** | $0.00 | $0.00 | **$0.00** ✅ |
| Claude API | $0.00 | ~$0.005 | $0.005 |
| OpenAI Vision | ~$0.01 | ~$0.01 | $0.02 |

---

## 🔧 How It Works

1. **Document Upload** → Sent to backend as file
2. **Tesseract OCR** → Extracts raw text from image (local, free)
3. **Regex Parsing** → Matches patterns to extract numbers and fields (local, free)
4. **Field Mapping** → Converts extracted data to model format
5. **Auto-Fill** → Populates loan application form
6. **User Review** → User verifies/adjusts before analysis

---

## ⚙️ Regex Patterns Used

The system detects:

```python
# Income: "monthly income: 1500 TND", "salaire mensuel: 1500"
# Expenses: "fixed monthly expense: 300", "dépense fixe: 300"
# Savings: "balance: 5000 TND", "solde: 5000"
# Employment: "5 years of employment", "5 ans d'expérience"
# Credit Score: "credit score: 650"
# Payment History: "paid on time: 85%", "missed payments: 2"
```

Patterns support both English and French, with Tunisian currency (TND).

---

## 🐛 Troubleshooting

### "Tesseract is not installed" error
**Fix**: Install Tesseract (see Installation section above)

### "Low extraction accuracy"
**Why**: Tesseract works best on clear, well-lit documents
**Fix**: 
- Take clear photos with good lighting
- Ensure text is legible
- Straighten document before scanning

### "No income detected"
**Why**: Document format doesn't match expected patterns
**Fix**: 
- Check document has clear "Income", "Salary", or "Revenu" labels
- Try a different document type

### "Regex not capturing currency"
**Patterns supported**: TND, TD, $, €, "dinar"
**Add new pattern** in `core/document_extractor.py` if needed

---

## 📝 API Endpoints

### Upload Document
```
POST /api/documents/{application_id}/extract
Content-Type: multipart/form-data

Body:
- file: (binary document)
- document_type: "bill" | "bank_statement" | "payslip" | "id" | "auto"

Returns:
{
    "monthly_income": 1500,
    "fixed_monthly_expenses": 300,
    "savings_balance": 5000,
    "employment_years": 5,
    "credit_score": 650,
    "utility_bill_on_time_ratio": 0.95,
    "income_inflation_ratio": 1.0,
    "document_type": "payslip",
    "document_date": "2024-01-15",
    "extracted_fields": ["monthly_income", "employment_years"]
}
```

### Auto-Fill Form
```
POST /api/applications/auto-fill
Content-Type: application/json

Body:
{
    "application_id": "app_123",
    "extracted_data": {
        "monthly_income": 1500,
        ...
    }
}

Returns:
{
    "success": true,
    "merged_data": {...}
}
```

---

## 🎯 Next Steps

1. ✅ Install Tesseract
2. ✅ Install Python libraries (pytesseract, pillow)
3. ✅ Restart backend (`python api.py`)
4. ✅ Test with sample documents
5. ✅ Adjust regex patterns if needed (optional)

---

## 📞 Support

Need better accuracy? You have options:
- **Option 1 (Free)**: Adjust regex patterns in `core/document_extractor.py`
- **Option 2 (Minimal Cost)**: Switch to Claude API (~$0.005/doc)
- **Option 3 (Optimal)**: Use OpenAI Vision API (~$0.01/doc, best accuracy)

Just let me know!
