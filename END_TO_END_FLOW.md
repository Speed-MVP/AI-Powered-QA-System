# End-to-End Flow Analysis

## Current Flow When You Upload an Audio File

### ✅ What Works:

1. **File Upload** (Test Page)
   - ✅ File uploads to GCP Storage via signed URL
   - ✅ Recording entry created in database
   - ✅ Background task triggered

2. **Transcription** (Backend)
   - ✅ Deepgram transcribes audio
   - ✅ Speaker diarization happens
   - ✅ Transcript saved to database

3. **Policy Template Lookup** (Backend)
   - ✅ Backend queries database for active policy template
   - ✅ Gets template by `company_id` and `is_active = True`

4. **Criteria Retrieval** (Backend)
   - ✅ Backend gets evaluation criteria from database
   - ✅ Criteria linked to the policy template

5. **LLM Evaluation** (Backend)
   - ✅ Gemini receives transcript + criteria
   - ✅ Prompt built with your custom criteria
   - ✅ Each category evaluated with your prompts
   - ✅ Weights and passing scores used

6. **Scoring** (Backend)
   - ✅ Scores calculated using criteria weights
   - ✅ Overall score computed
   - ✅ Violations detected based on criteria

7. **Results Display** (Test Page)
   - ✅ Results fetched from backend
   - ✅ Category scores displayed
   - ✅ Violations shown

---

## ❌ **CRITICAL PROBLEM**

### Policy Templates Are NOT Synced!

**The Issue:**
- **Frontend (Policy Templates page)**: Uses `localStorage` (Zustand store)
- **Backend (Processing)**: Queries **database** for templates
- **They're completely separate!**

**What This Means:**
1. You create a template in the frontend → Saved to `localStorage` only
2. You upload a file → Backend looks in **database** for templates
3. Backend finds **NO templates** → Processing **FAILS** with error:
   ```
   "No active policy template found for company {company_id}"
   ```

**The templates you create in the UI are NOT being used by the backend!**

---

## 🔍 Detailed Flow Breakdown

### Step-by-Step When You Upload:

```
1. User uploads file on Test page
   ↓
2. File goes to GCP Storage ✅
   ↓
3. Recording created in database ✅
   ↓
4. Background task starts
   ↓
5. Deepgram transcribes ✅
   ↓
6. Backend queries database for policy template:
   SELECT * FROM policy_templates 
   WHERE company_id = ? AND is_active = TRUE
   
   ❌ PROBLEM: Database is EMPTY!
   (Templates are in localStorage, not database)
   ↓
7. Error: "No active policy template found" ❌
   ↓
8. Processing FAILS ❌
```

---

## ✅ What You Need to Do

### Option 1: Create Templates via Backend API (Quick Fix)

Use the backend API directly to create templates:

```bash
# 1. Login first
POST /api/auth/login
{
  "email": "your@email.com",
  "password": "password"
}

# 2. Create template with criteria
POST /api/templates
{
  "template_name": "Customer Service QA",
  "description": "Standard QA template",
  "is_active": true,
  "criteria": [
    {
      "category_name": "Compliance",
      "weight": 40.0,
      "passing_score": 90,
      "evaluation_prompt": "Evaluate compliance..."
    },
    {
      "category_name": "Empathy",
      "weight": 30.0,
      "passing_score": 70,
      "evaluation_prompt": "Evaluate empathy..."
    },
    {
      "category_name": "Resolution",
      "weight": 30.0,
      "passing_score": 80,
      "evaluation_prompt": "Evaluate resolution..."
    }
  ]
}
```

### Option 2: Integrate Policy Templates Page (Proper Fix)

Connect the Policy Templates page to the backend API so templates are saved to the database.

---

## 🎯 Current State Summary

| Component | Status | Location |
|-----------|--------|----------|
| File Upload | ✅ Works | Test page → GCP Storage |
| Transcription | ✅ Works | Deepgram API |
| Policy Template Lookup | ❌ **BROKEN** | Backend queries empty database |
| Criteria Usage | ✅ Would work | If templates existed in DB |
| LLM Evaluation | ✅ Would work | If templates existed in DB |
| Scoring | ✅ Would work | If templates existed in DB |
| Results Display | ✅ Works | Test page shows results |

---

## 🚨 Bottom Line

**Can you upload and process?** 
- ✅ Upload: YES
- ✅ Transcription: YES  
- ❌ **Evaluation: NO** (fails because no templates in database)

**Does it use your policies/criteria?**
- ❌ **NO** - Templates created in frontend are not in database
- ✅ **YES** - If you create templates via backend API, it WILL use them

---

## 🔧 Quick Test

To verify if it works:

1. **Create a template via backend API** (using Postman or curl)
2. **Upload a file** via Test page
3. **Check if processing completes**

If you do this, the flow WILL work and use your custom criteria!

---

## 💡 Recommendation

**IMMEDIATE**: Create templates via backend API to test the flow

**PROPER FIX**: Integrate Policy Templates page with backend API (I can do this)

Would you like me to:
1. ✅ Show you how to create templates via API?
2. ✅ Integrate the Policy Templates page with backend?
3. ✅ Both?

