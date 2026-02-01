# Document Data Extraction Setup Guide

## Overview
The system now supports intelligent data extraction from documents (bills, bank statements, payslips, etc.) using OpenAI's Vision and Claude APIs.

## Setup Instructions

### 1. Install Dependencies

```bash
pip install python-dotenv openai anthropic
```

### 2. Get API Keys

#### Option A: OpenAI Vision API (Recommended for images)
1. Visit https://platform.openai.com/account/api-keys
2. Create a new API key
3. Add to `.env` file:
```
OPENAI_API_KEY=sk-...
```

#### Option B: Anthropic Claude API (Better for structured extraction)
1. Visit https://console.anthropic.com/
2. Create API key
3. Add to `.env` file:
```
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Optional: Local OCR (Tesseract)
If you don't want to use cloud APIs, install Tesseract locally:

**Windows:**
```bash
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
# Then install pytesseract
pip install pytesseract pillow
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
pip install pytesseract pillow
```

**macOS:**
```bash
brew install tesseract
pip install pytesseract pillow
```

## API Endpoints

### 1. Extract Data from Document
```
POST /api/documents/{application_id}/extract

Content-Type: multipart/form-data

Body:
- file: <uploaded document>

Response:
{
  "application_id": "CR-2026-ABC12",
  "document_type": "bill|bank_statement|payslip|id|auto",
  "extracted_data": {
    "monthly_income": 2500.0,
    "fixed_monthly_expenses": 850.0,
    "savings_balance": 5000.0,
    "employment_years": 5.5,
    "credit_score": 720,
    "utility_bill_on_time_ratio": 0.95,
    "_document_source": "steg_bill",
    "_document_date": "2026-01-28",
    "_extracted_fields": ["monthly_income", "fixed_monthly_expenses"]
  },
  "validation": {
    "is_valid": true,
    "issues": []
  },
  "message": "Data extracted successfully"
}
```

### 2. Auto-Fill Application Form
```
POST /api/applications/auto-fill

Body:
{
  "application_id": "CR-2026-ABC12",
  "extracted_data": {
    "monthly_income": 2500.0,
    "fixed_monthly_expenses": 850.0,
    ...
  }
}

Response:
{
  "application_id": "CR-2026-ABC12",
  "merged_data": { ... },
  "message": "Application auto-filled successfully"
}
```

## Supported Document Types

### Automatically Detected:
1. **STEG Bills** (Electricity - Tunisia)
   - Extracts: monthly charges, account number, payment date
   - Maps to: fixed_monthly_expenses, utility_bill_on_time_ratio

2. **Bank Statements**
   - Extracts: balance, transaction history, account type
   - Maps to: savings_balance, income_inflation_ratio

3. **Payslips / Salary Certificates**
   - Extracts: gross salary, deductions, employment years
   - Maps to: monthly_income, employment_years

4. **ID Documents (CIN, Passport)**
   - Extracts: name, date of birth, address
   - Maps to: age, geo_location_mismatch validation

## Extracted Fields

The system automatically extracts and maps:

| Document Field | Model Field | Range |
|---|---|---|
| Monthly salary/income | `monthly_income` | 0 - 50000 |
| Bill amount / expenses | `fixed_monthly_expenses` | 0 - 10000 |
| Account balance | `savings_balance` | 0 - 1000000 |
| Years of employment | `employment_years` | 0 - 70 |
| Credit score | `credit_score` | 300 - 850 |
| On-time payment ratio | `utility_bill_on_time_ratio` | 0 - 1 |
| Income inflation indicator | `income_inflation_ratio` | 0 - 3 |

## Usage Flow

```
1. User uploads document in "Documents" tab
2. System calls /api/documents/{application_id}/extract
3. Document is OCR'd and AI extracts structured data
4. System validates extracted data
5. User reviews extracted fields
6. User clicks "Auto-Fill Form" to populate the loan application
7. User can manually adjust any extracted values
8. Form is submitted for analysis
```

## Error Handling

The system handles:
- Invalid file formats (converts to supported format)
- Missing required fields (returns warnings)
- OCR failures (falls back to manual input)
- API rate limits (queues requests)
- Poor image quality (requests document rescan)

## Cost Estimation

### Per Document:
- **OpenAI Vision**: ~$0.01 per image
- **Claude API**: ~$0.005 per extraction
- **Tesseract (Local)**: FREE

### Monthly (1000 documents):
- OpenAI: ~$10/month
- Claude: ~$5/month
- Tesseract: $0 (self-hosted)

## Next Steps

1. Add to frontend: Document upload UI in "Documents" tab
2. Implement auto-fill preview UI
3. Add document quality validation (minimum DPI, clarity check)
4. Add manual field mapping UI for edge cases
5. Implement document template learning (improve accuracy over time)

## Troubleshooting

**"OPENAI_API_KEY not set"**
- Add key to `.env` file
- Restart backend: `python api.py`

**"Poor OCR quality"**
- Ensure document image is clear and well-lit
- Try higher resolution image
- Manually input sensitive fields

**"Extraction takes too long"**
- Use Tesseract locally instead of cloud API
- Compress image before upload
- Queue requests if batch processing

**"Wrong field extracted"**
- Review AI prompt in `document_extractor.py`
- Provide example documents for training
- Use manual field mapping as fallback
