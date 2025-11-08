# API Usage: Deepgram and AssemblyAI

## Current Implementation Status

### ✅ **Deepgram - ACTIVELY USED**
- **Status**: Required and actively used in the processing pipeline
- **Purpose**: Handles both transcription AND speaker diarization
- **Location**: `backend/app/services/deepgram.py`
- **Used in**: `backend/app/tasks/process_recording.py` (line 34-35)

#### How Deepgram is Used:
1. **Called during processing**: When a recording is uploaded, the `process_recording_task` function calls Deepgram
2. **Single API call**: One call handles both transcription and diarization
3. **Configuration**:
   - Model: `nova-2`
   - Features enabled:
     - `diarize: true` - Speaker separation
     - `punctuate: true` - Automatic punctuation
     - `utterances: true` - Returns segmented utterances with speaker labels

#### Deepgram Response Structure:
```python
{
    "transcript": "Full text transcript",
    "diarized_segments": [
        {
            "speaker": "speaker_0",
            "text": "Hello, thank you for calling...",
            "start": 0.0,
            "end": 3.5
        },
        {
            "speaker": "speaker_1",
            "text": "Hi, I need help with...",
            "start": 3.5,
            "end": 7.2
        }
    ],
    "confidence": 0.95
}
```

#### Environment Variable:
```env
DEEPGRAM_API_KEY=your-deepgram-api-key  # REQUIRED
```

---

### ⚠️ **AssemblyAI - NOT CURRENTLY USED**
- **Status**: Implemented but not called anywhere in the codebase
- **Purpose**: Was intended as an alternative diarization service
- **Location**: `backend/app/services/assemblyai.py`
- **Used in**: ❌ Nowhere (service exists but is never imported or called)

#### Why AssemblyAI is Not Used:
1. **Redundancy**: Deepgram already handles diarization, making AssemblyAI unnecessary
2. **Cost**: Using both services would double the transcription cost
3. **Design**: The architecture uses Deepgram as the primary transcription service

#### AssemblyAI Implementation Details:
- **Async polling**: Uses polling pattern (submits job, then polls for completion)
- **Speaker labels**: Can separate speakers (A, B, C, etc.)
- **Optional**: API key is optional in config - won't break if not provided

#### Environment Variable:
```env
ASSEMBLYAI_API_KEY=your-assemblyai-key  # OPTIONAL (currently unused)
```

---

## Current Processing Flow

```
1. File Uploaded to GCP Storage
   ↓
2. process_recording_task triggered
   ↓
3. Deepgram.transcribe() called
   ├─ Transcribes audio
   ├─ Separates speakers (diarization)
   ├─ Adds punctuation
   └─ Returns structured data
   ↓
4. Transcript saved to database
   ↓
5. Gemini evaluates transcript
   ↓
6. Scores calculated and saved
```

---

## Recommendations

### Option 1: Keep Current Setup (Recommended)
- **Use only Deepgram** for transcription + diarization
- **Remove AssemblyAI** to reduce complexity (or keep as optional fallback)
- **Cost**: Lower (one service instead of two)
- **Simplicity**: Easier to maintain

### Option 2: Use Both Services
- **Deepgram**: Primary transcription
- **AssemblyAI**: Fallback if Deepgram fails, or for comparison/validation
- **Cost**: Higher (paying for two services)
- **Complexity**: More code to maintain

### Option 3: Switch to AssemblyAI Only
- **Remove Deepgram**, use only AssemblyAI
- **Pros**: AssemblyAI has good accuracy
- **Cons**: Requires refactoring code, AssemblyAI uses polling (slower)

---

## Code References

### Where Deepgram is Called:
```python
# backend/app/tasks/process_recording.py (line 32-35)
logger.info(f"Transcribing {recording_id}...")
deepgram = DeepgramService()
transcript_data = await deepgram.transcribe(recording.file_url)
```

### Where AssemblyAI Would Be Called (currently unused):
```python
# This code doesn't exist - AssemblyAI is never called
# assemblyai = AssemblyAIService()
# diarized_data = await assemblyai.diarize(recording.file_url)
```

---

## Cost Implications

### Current Setup (Deepgram only):
- **Deepgram Nova-2**: ~$0.0043 per minute
- **Example**: 50-minute call = $0.22

### If Using Both:
- **Deepgram**: $0.22
- **AssemblyAI**: ~$0.01 per minute = $0.50
- **Total**: $0.72 per call (3x more expensive)

---

## Summary

- **Deepgram**: ✅ Required, actively used for transcription + diarization
- **AssemblyAI**: ❌ Not used, optional service (can be removed or used as fallback)
- **Recommendation**: Keep Deepgram, remove or keep AssemblyAI as optional fallback only

