# Fix: Extracted Data Not Being Used in PD Score Recalculation

## The Problem

User uploads a document with extracted credit_score, clicks "Analyze with This Data", but the PD score doesn't change. It's as if the extracted data is being ignored.

## Root Cause

The issue was in how the frontend handled "Analyze with This Data":

### Before (Incorrect):
```typescript
const applicationData: CustomerApplication = {
  age: (doc.extracted_data as any).age ?? 35,  // Uses defaults if not extracted
  credit_score: (doc.extracted_data as any).credit_score ?? 680,  // default 680
  monthly_income: (doc.extracted_data as any).monthly_income ?? 3500,  // default 3500
  // ... all fields with hardcoded defaults
};
```

**Problem**: If the document only extracted `credit_score`, all other fields get hardcoded defaults, which overwrites the user's original inputs. So re-analyzing produces almost the same result.

### After (Correct):
```typescript
const applicationData: CustomerApplication = {
  age: (doc.extracted_data as any).age ?? analysis.raw_data?.age ?? 35,  // Original input > extracted > default
  credit_score: (doc.extracted_data as any).credit_score ?? analysis.raw_data?.credit_score ?? 680,
  monthly_income: (doc.extracted_data as any).monthly_income ?? analysis.raw_data?.monthly_income ?? 3500,
  // ... all fields with original values as fallback
};
```

**Solution**: Use the CURRENT analysis data as the base, overlay extracted values on top, only use defaults as last resort.

## Changes Made

### Frontend (src/pages/Documents.tsx)

1. **Added check for active analysis**:
   ```typescript
   if (!analysis) {
     alert('No active analysis. Please submit the initial application first.');
     return;
   }
   ```

2. **Changed fallback chain**:
   ```typescript
   // OLD: extracted ?? hardcoded_default
   // NEW: extracted ?? currentAnalysisData ?? hardcoded_default
   
   credit_score: (doc.extracted_data as any).credit_score ?? analysis.raw_data?.credit_score ?? 680,
   ```

3. **Added detailed logging**:
   ```typescript
   console.log('[DOCS] Building re-analysis with extracted data');
   console.log('[DOCS] Current analysis data:', analysis);
   console.log('[DOCS] Extracted data:', doc.extracted_data);
   console.log('[DOCS] Final application data for re-analysis:', applicationData);
   ```

4. **Improved document sync**:
   - Fetch documents from backend when analysis changes
   - Add new documents found on backend
   - Update changed documents

### Backend (api.py)

1. **Enhanced document movement logging**:
   - Shows which temp app IDs had documents
   - Lists document IDs being moved
   - Confirms new app location

2. **Improved debug logging**:
   - Shows received data from frontend
   - Indicates if data looks like extracted or defaults
   - Shows final data being used for analysis

3. **Enhanced debug endpoint**:
   - Returns full `extracted_data` dictionary
   - Shows document `extraction_info`
   - Better visibility into backend state

## How It Works Now

```
User's Original Analysis:
  credit_score: 680 (user input)
  monthly_income: 3500 (user input)
  PD: 30%

User uploads document with extracted data:
  credit_score: 600
  monthly_income: 4500

User clicks "Analyze with This Data":

Frontend builds:
  credit_score: 600 (from extracted) ← overrides 680
  monthly_income: 4500 (from extracted) ← overrides 3500
  [other fields stay as user originally entered]

Backend receives and analyzes:
  Uses credit_score: 600
  Uses monthly_income: 4500
  Calculates new PD: 40%

Result: PD increased from 30% to 40% as expected!
```

## Testing

To verify the fix works:

```bash
python test_full_flow.py
```

This will:
1. Do initial analysis with credit_score=680
2. Upload document with credit_score=600
3. Wait for extraction
4. Re-analyze with extracted data
5. Verify PD changed appropriately

## Expected Behavior

- **Uploaded doc has LOWER credit_score**: PD should INCREASE (higher default risk)
- **Uploaded doc has HIGHER credit_score**: PD should DECREASE (lower default risk)
- **Multiple fields extracted**: All are used to recalculate PD

## Debugging

If it's still not working:

1. Check browser console for logs starting with `[DOCS]`
2. Check API logs for `[INFO] RECEIVED DATA FROM FRONTEND`
3. Run `python check_backend.py` to see what's stored
4. Use `/api/debug/documents` endpoint to inspect raw backend state

## Summary

The fix ensures that when a user uploads a document and extracts data:
- ✅ The extracted values are properly merged with the user's original inputs
- ✅ Only extracted fields override the original; other fields stay the same
- ✅ The re-analysis properly reflects the new data
- ✅ PD score updates accordingly
