# Manual Testing Guide - Extracted Data PD Update Fix

## Prerequisites
- Backend (API) running on http://localhost:8001
- Frontend running on http://localhost:3000  
- Browser DevTools open (F12) on the frontend
- Console tab visible to see `[DOCS]` logs

## Step-by-Step Test

### Step 1: Create Initial Analysis
1. Navigate to "Application Input" tab
2. Fill in form with:
   - **Age**: 35
   - **Credit Score**: 680
   - **Monthly Income**: 3500
   - **Savings Balance**: 8000
   - **Other fields**: Keep defaults
3. Click "Analyze Application"
4. **Check Result**: 
   - ✓ Analysis should show **PD Score: ~30%**
   - ✓ Console should show `[DOCS]` messages
   - Note the exact PD score for comparison

### Step 2: Verify Backend State
In a terminal/PowerShell, run:
```
python diagnose.py
```

**Expected Output**:
```
Total applications in backend: 1
App: CR-XXXX (or temp-XXXX)
  [No documents yet]
```

### Step 3: Upload Document
1. Go to "Documents" tab
2. Create a test document:
   - **PDF**: With text "Credit Score: 600" 
   - **OR Image**: Screenshot/photo with "Credit Score: 600"
3. Upload the file
4. **Wait 5-10 seconds** for extraction to complete
5. **Check Console**: Should see `[DOCS] Document uploaded...` messages

### Step 4: Verify Extraction
1. Run diagnose again:
```
python diagnose.py
```

**Expected Output**:
```
App: CR-XXXX
  📄 doc-XXXX
    Status: extracted
    Extracted fields: ['credit_score']
    • credit_score: 600
```

**If Status is "pending"**: Extraction still running. Wait more.
**If Status is "pending_error"**: Check OCR extraction - see `core/ocr_extractor.py`
**If No extracted fields**: Document text not containing "credit score"

### Step 5: Re-Analyze with Extracted Data
1. In "Documents" tab, look for the document with green checkmark
2. Click the **"Analyze with This Data"** button
3. **Check Console**: Should see:
   ```
   [DOCS] Building re-analysis with extracted data
   [DOCS] Current analysis data: {...}
   [DOCS] Extracted data: {credit_score: 600}
   [DOCS] Final application data for re-analysis: {...}
   ```
4. **Check Result**: 
   - ✓ New analysis should show **PD Score: ~40% or higher** (since credit_score went from 680→600)
   - ✓ Score should be DIFFERENT from Step 1

### Step 6: API Logs Verification
In the API terminal window, you should see:
```
[INFO] RECEIVED DATA FROM FRONTEND for app CR-XXXX
[INFO] Processing analysis with extracted credit_score: 600 -> credit_score (was: 680)
```

## Success Criteria

✅ **Test Passes If**:
1. Initial analysis shows PD Score ~30% (Step 1)
2. Extraction completes and shows credit_score: 600 (Step 4)
3. Re-analysis shows different PD Score, higher than 30% (Step 5)
4. Console shows `[DOCS]` messages (Steps 1, 3, 5)
5. API logs show extracted data being used (Step 6)

❌ **Test Fails If**:
- PD score doesn't change after re-analysis
- "Analyze with This Data" button is disabled/grayed out
- Console shows no `[DOCS]` messages
- API logs show no "RECEIVED DATA FROM FRONTEND" message
- Extraction shows "pending" or "pending_error" for more than 10 seconds

## Debugging Failed Test

### If extraction doesn't complete
```
python diagnose.py
```
Check document status. If "pending_error", check:
- Is the document text readable?
- Does it contain "credit score" or "credit" keyword?
- Check API logs for OCR errors

### If PD score doesn't change
1. Check console for `[DOCS]` messages - if missing, frontend issue
2. Check API logs for "RECEIVED DATA" - if missing, network issue
3. Run `check_backend.py` to see what data backend received
4. Verify `analysis.raw_data` contains expected fields

### If "Analyze with This Data" button is disabled
- Check browser console for warnings
- Make sure document status is "extracted" (not "pending")
- Make sure `doc.extracted_data` is not empty
- Reload page if stuck

## Expected PD Scores

When **credit_score changes from 680 → 600**:
- ✓ Credit score is a strong predictor
- ✓ Lower credit score = higher default risk
- ✓ PD should increase approximately 10-15 percentage points
- Expected: 30% → 40-45%

When **credit_score changes from 680 → 750**:
- ✓ Higher credit score = lower default risk  
- ✓ PD should decrease
- Expected: 30% → 20-25%

## Quick Commands

```bash
# Terminal 1: Start API
cd c:\Users\dell\Documents\cardibih
python api.py

# Terminal 2: Check status
python diagnose.py

# Terminal 3: Debug state
python check_backend.py
```

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "No extracted data found" error | Wait 10+ seconds for extraction, document text must contain "credit" keyword |
| PD doesn't change | Check console for `[DOCS]` messages, check API logs for "RECEIVED DATA" |
| Button is gray/disabled | Make sure status is "extracted", extracted_data not empty, refresh page |
| 502 Bad Gateway | API crashed, check terminal for errors, restart with `python api.py` |
| No documents showing | Check network tab (F12) for upload errors, file size limit 50MB |

