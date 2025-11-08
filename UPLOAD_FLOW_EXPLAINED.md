# What Happens When You Upload an Audio File

## Complete Step-by-Step Flow

### **Phase 1: Frontend Upload (Test Page)**

#### Step 1: File Selection
- You drag & drop or select an audio file
- File is added to the upload queue
- Status: `uploading`, Progress: 0%

#### Step 2: Get Signed URL (10% progress)
```
Frontend → POST /api/recordings/signed-url?file_name=recording.mp3
Backend → Generates signed URL for GCP Cloud Storage
Backend → Returns: { signed_url, file_url, file_name }
```
- Backend creates a time-limited signed URL
- File will be stored at: `{company_id}/{file_name}`

#### Step 3: Upload to GCP Storage (30% progress)
```
Frontend → PUT {signed_url} (file binary)
GCP Cloud Storage → Stores file
```
- File uploaded directly to GCP (bypasses backend)
- Upload happens in browser
- Progress: 30%

#### Step 4: Create Recording Entry (60% progress)
```
Frontend → POST /api/recordings/upload
Body: { file_name, file_url }
Backend → Creates Recording record in database
Backend → Status: "queued"
Backend → Triggers background task
```
- Recording saved to Neon PostgreSQL database
- Status set to `queued`
- Background processing task starts
- Progress: 60% → 100%

#### Step 5: Upload Complete
- File status: `uploaded`
- Recording ID stored
- "Process" button becomes available

---

### **Phase 2: Background Processing (Automatic)**

When you click "Process" (or it auto-processes), the backend starts:

#### Step 6: Status Check (Frontend Polling)
```
Frontend → GET /api/recordings/{recording_id} (every 5 seconds)
Backend → Returns current status
```
- Frontend polls every 5 seconds
- Status changes: `queued` → `processing` → `completed` or `failed`

#### Step 7: Transcription (Backend)
```
Background Task → Deepgram API
Input: GCP Storage URL of audio file
Output: {
  transcript: "Full text...",
  diarized_segments: [
    { speaker: "speaker_0", text: "...", start: 0, end: 3.5 },
    { speaker: "speaker_1", text: "...", start: 3.5, end: 7.2 }
  ],
  confidence: 0.95
}
```
- Deepgram transcribes audio
- Separates speakers (agent vs customer)
- Adds punctuation
- Saves transcript to database

#### Step 8: Get Policy Template (Backend)
```
Background Task → Database Query
SELECT * FROM policy_templates 
WHERE company_id = ? AND is_active = TRUE
```
- Finds your active template from database
- Gets all evaluation criteria for that template
- **Uses the template you created in the UI!**

#### Step 9: LLM Evaluation (Backend)
```
Background Task → Gemini API
Input: 
  - Transcript text
  - Your evaluation criteria (from database)
  - Your custom prompts (from database)
  
Prompt Built:
"Evaluate this customer service call transcript based on:
- Compliance (Weight: 40%, Passing: 90/100)
  Evaluate if agent followed compliance guidelines...
- Empathy (Weight: 30%, Passing: 70/100)
  Assess agent's empathy...
- Resolution (Weight: 30%, Passing: 80/100)
  Determine if issue was resolved..."

TRANSCRIPT:
[Full transcript text here]"

Output: {
  category_scores: {
    "Compliance": { score: 85, feedback: "..." },
    "Empathy": { score: 72, feedback: "..." },
    "Resolution": { score: 88, feedback: "..." }
  },
  resolution_detected: true,
  resolution_confidence: 0.92,
  violations: [...]
}
```
- Gemini evaluates transcript using YOUR criteria
- Uses YOUR custom prompts for each category
- Returns scores and feedback for each category
- Detects policy violations

#### Step 10: Calculate Final Scores (Backend)
```
Background Task → Scoring Service
Input: 
  - LLM evaluation results
  - Criteria weights (from database)
  
Calculation:
- Overall Score = Weighted average
  = (Compliance × 0.40) + (Empathy × 0.30) + (Resolution × 0.30)
  = (85 × 0.40) + (72 × 0.30) + (88 × 0.30)
  = 34 + 21.6 + 26.4
  = 82.0

- Category Scores: Saved individually
- Violations: Saved with severity levels
```
- Uses YOUR weights from the template
- Calculates weighted overall score
- Saves all scores to database

#### Step 11: Save Results (Backend)
```
Background Task → Database
- Evaluation record created
- Category scores saved (one per criteria)
- Policy violations saved
- Recording status → "completed"
```
- All results saved to Neon PostgreSQL
- Status updated to `completed`

#### Step 12: Email Notification (Optional)
```
Background Task → Email Service
Sends email to user:
"Your recording 'recording.mp3' has been processed.
Overall Score: 82.0"
```
- Email sent if configured
- Includes score summary

---

### **Phase 3: Results Display (Frontend)**

#### Step 13: Polling Detects Completion
```
Frontend → GET /api/recordings/{recording_id}
Status: "completed" ✅
```
- Frontend detects status change
- Stops polling

#### Step 14: Fetch Evaluation Results
```
Frontend → GET /api/evaluations/{recording_id}
Response: {
  overall_score: 82.0,
  resolution_detected: true,
  resolution_confidence: 0.92,
  category_scores: [
    { category_name: "Compliance", score: 85, feedback: "..." },
    { category_name: "Empathy", score: 72, feedback: "..." },
    { category_name: "Resolution", score: 88, feedback: "..." }
  ],
  policy_violations: [...]
}
```

#### Step 15: Fetch Transcript
```
Frontend → GET /api/evaluations/{recording_id}/transcript
Response: {
  transcript_text: "Full transcript...",
  diarized_segments: [...],
  confidence: 0.95
}
```

#### Step 16: Display Results
- Overall score shown (82.0)
- Category scores displayed with feedback
- Transcript shown with speaker attribution
- Violations listed
- All using YOUR custom categories!

---

## Timeline Example

```
00:00 - You upload file
00:02 - File in GCP Storage
00:03 - Recording created, status: "queued"
00:04 - Background task starts
00:05 - Status: "processing"
00:30 - Deepgram transcription complete
00:32 - Template loaded from database
00:35 - Gemini evaluation complete
00:36 - Scores calculated
00:37 - Results saved, status: "completed"
00:38 - Frontend detects completion
00:39 - Results displayed to you
```

**Total Time**: ~30-60 seconds (depends on file length)

---

## What Gets Used From Your Template

✅ **Template Name** - Identifies which template was used
✅ **Category Names** - "Compliance", "Empathy", "Resolution"
✅ **Weights** - 40%, 30%, 30% (used for overall score calculation)
✅ **Passing Scores** - 90, 70, 80 (used for validation)
✅ **Evaluation Prompts** - Your custom LLM instructions
✅ **Active Status** - Only active template is used

---

## Database Records Created

1. **Recording** - File metadata, status, timestamps
2. **Transcript** - Full text, diarized segments, confidence
3. **Evaluation** - Overall score, resolution detection, LLM analysis
4. **CategoryScore** - One per criteria (score + feedback)
5. **PolicyViolation** - Any violations detected

---

## Error Handling

### If No Template Found:
```
Error: "No active policy template found for company {id}"
Status: "failed"
Solution: Create and activate a template first
```

### If Transcription Fails:
```
Error: "Deepgram error: ..."
Status: "failed"
Solution: Check Deepgram API key, file format
```

### If LLM Evaluation Fails:
```
Error: "Gemini API error: ..."
Status: "failed"
Solution: Check Gemini API key, quota
```

---

## Summary

**When you upload:**
1. ✅ File goes to GCP Storage
2. ✅ Recording created in database
3. ✅ Background task starts automatically
4. ✅ Deepgram transcribes audio
5. ✅ Backend finds YOUR active template
6. ✅ Gemini evaluates using YOUR criteria
7. ✅ Scores calculated using YOUR weights
8. ✅ Results saved to database
9. ✅ Frontend displays YOUR custom results

**Everything uses the template and criteria you created in the UI!** 🎉

