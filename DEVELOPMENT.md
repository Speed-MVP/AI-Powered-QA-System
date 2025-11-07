# Development Guide - AI QA MVP

## Getting Started

This guide covers the step-by-step process for setting up and developing the AI-powered Batch QA System MVP.

---

## 1. Prerequisites

Before starting, ensure you have:

- **Node.js 18+** installed
- **Git** installed
- **Supabase account** (free tier works for MVP)
- **API Keys:**
  - Deepgram API key (https://deepgram.com)
  - AssemblyAI API key (https://assemblyai.com)
  - Google Gemini API key (https://ai.google.dev) OR Claude API key (https://anthropic.com)

---

## 2. Project Structure

```
ai-qa-mvp/
├── supabase/                 # Supabase configuration
│   ├── migrations/           # SQL migration files
│   │   ├── 001_companies.sql
│   │   ├── 002_users.sql
│   │   ├── 003_policy_templates.sql
│   │   ├── 004_evaluation_criteria.sql
│   │   ├── 005_recordings.sql
│   │   ├── 006_transcripts.sql
│   │   ├── 007_evaluations.sql
│   │   ├── 008_category_scores.sql
│   │   ├── 009_policy_violations.sql
│   │   └── 010_rls_policies.sql
│   ├── functions/            # Edge Functions
│   │   ├── process-recording/
│   │   ├── transcribe-audio/
│   │   ├── evaluate-with-llm/
│   │   └── calculate-scores/
│   └── config.toml
├── src/
│   ├── components/
│   │   ├── ui/               # shadcn/ui components
│   │   ├── FileUpload.tsx
│   │   ├── RecordingsList.tsx
│   │   ├── EvaluationResults.tsx
│   │   └── PolicyTemplateEditor.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Upload.tsx
│   │   ├── Results.tsx
│   │   └── PolicyTemplates.tsx
│   ├── hooks/
│   │   ├── useRecordings.ts
│   │   ├── useEvaluations.ts
│   │   └── useRealtime.ts
│   ├── lib/
│   │   ├── supabase.ts
│   │   ├── types.ts
│   │   └── utils.ts
│   ├── App.tsx
│   └── main.tsx
├── public/
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

---

## 3. Installation Steps

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd ai-qa-mvp
```

### Step 2: Install Supabase CLI (Global)
```bash
npm install -g supabase
```

### Step 3: Create Supabase Project
Go to https://supabase.com, create new project, get your:
- Project URL
- Anon Key
- Service Role Key (keep secret!)

### Step 4: Link Local Project to Supabase
```bash
supabase login
supabase link --project-id <your-project-id>
```

### Step 5: Install Node Dependencies
```bash
npm install
```

### Step 6: Set Environment Variables
Create `.env.local`:
```
VITE_SUPABASE_URL=https://[project-id].supabase.co
VITE_SUPABASE_ANON_KEY=eyJ0eXAiOiJKV1QiLCJhbGc...
VITE_DEEPGRAM_API_KEY=your-deepgram-key
VITE_ASSEMBLYAI_API_KEY=your-assemblyai-key
VITE_GEMINI_API_KEY=your-gemini-key
# OR
VITE_CLAUDE_API_KEY=your-claude-key
```

### Step 7: Run Database Migrations
```bash
# Start local Supabase (runs PostgreSQL, Auth, etc. locally)
supabase start

# In another terminal, push migrations
supabase db push
```

### Step 8: Generate TypeScript Types
```bash
supabase gen types typescript --project-id <your-project-id> > src/lib/types.ts
```

### Step 9: Start Development Server
```bash
npm run dev
```

Open http://localhost:5173

---

## 4. Key Development Tasks

### Task 1: Create Database Tables (Week 1-2)

Create migration file `supabase/migrations/001_companies.sql`:

```sql
CREATE TABLE companies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_name VARCHAR(255) NOT NULL,
  industry VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE companies ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see their company"
  ON companies FOR SELECT
  USING (id = auth.jwt() ->> 'company_id');
```

Repeat for all 9 tables (see README for schema).

Deploy:
```bash
supabase db push
```

### Task 2: Build File Upload Component (Week 3-4)

`src/components/FileUpload.tsx`:

```typescript
import { useDropzone } from 'react-dropzone'
import { supabase } from '@/lib/supabase'

export function FileUpload({ companyId }: { companyId: string }) {
  const onDrop = async (files: File[]) => {
    const file = files[0]
    
    // Upload to Supabase Storage
    const { data, error } = await supabase.storage
      .from('recordings')
      .upload(`${companyId}/${Date.now()}_${file.name}`, file)
    
    if (error) {
      console.error('Upload failed:', error)
      return
    }
    
    // Get public URL
    const { data: { publicUrl } } = supabase.storage
      .from('recordings')
      .getPublicUrl(data.path)
    
    // Create database record
    const { data: recording, error: dbError } = await supabase
      .from('recordings')
      .insert({
        company_id: companyId,
        file_name: file.name,
        file_url: publicUrl,
        status: 'queued'
      })
      .select()
      .single()
    
    if (dbError) {
      console.error('DB insert failed:', dbError)
      return
    }
    
    // Trigger Edge Function
    await supabase.functions.invoke('process-recording', {
      body: { recording_id: recording.id }
    })
  }
  
  const { getRootProps, getInputProps } = useDropzone({ onDrop })
  
  return (
    <div {...getRootProps()} className="border-2 border-dashed p-8 rounded">
      <input {...getInputProps()} />
      <p>Drag & drop audio files here</p>
    </div>
  )
}
```

### Task 3: Build Edge Function for Processing (Week 5-6)

`supabase/functions/process-recording/index.ts`:

```typescript
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from '@supabase/supabase-js'

serve(async (req) => {
  const { recording_id } = await req.json()
  
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL'),
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')
  )
  
  try {
    // 1. Update status to processing
    await supabase
      .from('recordings')
      .update({ status: 'processing' })
      .eq('id', recording_id)
    
    // 2. Get recording details
    const { data: recording } = await supabase
      .from('recordings')
      .select('*')
      .eq('id', recording_id)
      .single()
    
    // 3. Transcribe with Deepgram
    const transcriptResponse = await fetch(
      'https://api.deepgram.com/v1/listen?model=nova-3&diarize=true',
      {
        method: 'POST',
        headers: {
          'Authorization': `Token ${Deno.env.get('DEEPGRAM_API_KEY')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: recording.file_url })
      }
    )
    
    const transcript = await transcriptResponse.json()
    
    // 4. Save transcript
    await supabase
      .from('transcripts')
      .insert({
        recording_id: recording_id,
        transcript_text: transcript.results.channels[0].alternatives[0].transcript,
        diarized_segments: transcript.results.channels[0].alternatives[0].words
      })
    
    // 5. Evaluate with LLM
    const evaluation = await evaluateWithLLM(
      transcript,
      recording.policy_template_id,
      supabase
    )
    
    // 6. Save evaluation
    await supabase
      .from('evaluations')
      .insert(evaluation)
    
    // 7. Update status to completed
    await supabase
      .from('recordings')
      .update({ status: 'completed' })
      .eq('id', recording_id)
    
    return new Response(JSON.stringify({ success: true }))
  } catch (error) {
    console.error('Processing failed:', error)
    
    await supabase
      .from('recordings')
      .update({ status: 'failed' })
      .eq('id', recording_id)
    
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500 }
    )
  }
})
```

Deploy:
```bash
supabase functions deploy process-recording
```

### Task 4: Build Results Viewer (Week 7-8)

`src/components/EvaluationResults.tsx`:

```typescript
import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import { Database } from '@/lib/types'

type Evaluation = Database['public']['Tables']['evaluations']['Row']

export function EvaluationResults({ recordingId }: { recordingId: string }) {
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null)
  const [transcript, setTranscript] = useState<string>('')
  
  useEffect(() => {
    fetchResults()
  }, [recordingId])
  
  const fetchResults = async () => {
    // Fetch evaluation
    const { data: eval } = await supabase
      .from('evaluations')
      .select('*')
      .eq('recording_id', recordingId)
      .single()
    
    setEvaluation(eval)
    
    // Fetch transcript
    const { data: trans } = await supabase
      .from('transcripts')
      .select('transcript_text')
      .eq('recording_id', recordingId)
      .single()
    
    setTranscript(trans?.transcript_text || '')
  }
  
  if (!evaluation) return <div>Loading...</div>
  
  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-2xl font-bold">Overall Score: {evaluation.overall_score}/100</h2>
        <p>Resolution: {evaluation.resolution_detected ? 'Yes' : 'No'}</p>
        <p>Confidence: {(evaluation.resolution_confidence * 100).toFixed(0)}%</p>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-xl font-bold">Transcript</h3>
        <p className="text-gray-700">{transcript}</p>
      </div>
    </div>
  )
}
```

---

## 5. Testing Locally

### Test File Upload
1. Go to http://localhost:5173/upload
2. Drag-drop a test MP3 file
3. Check Supabase dashboard → recordings table
4. Verify file in Storage

### Test Processing
1. Check Supabase logs: `supabase functions logs process-recording`
2. Watch for errors in Edge Function
3. Verify transcript saved in database

### Test Results Display
1. After processing completes, click recording
2. View evaluation scores, transcript, violations
3. Check CSV export works

---

## 6. Debugging Tips

### Check Supabase Logs
```bash
supabase functions logs process-recording --follow
```

### View Database (Local)
```bash
supabase db inspect
# or use pgAdmin via Supabase Dashboard
```

### Test API Directly
```bash
curl -X POST http://localhost:54321/functions/v1/process-recording \
  -H "Content-Type: application/json" \
  -d '{"recording_id": "your-uuid"}'
```

### Enable Debug Logging in React
Add to `.env.local`:
```
VITE_DEBUG=true
```

---

## 7. Code Standards

### TypeScript
- Always use strict mode
- Use types from auto-generated `types.ts`
- No `any` types without explicit reason

### React
- Use functional components with hooks
- Extract components >100 LOC into separate files
- Use shadcn/ui for UI consistency

### SQL
- Use parameterized queries (Supabase SDK handles this)
- Comment complex logic
- Test migrations before deploying to prod

### Git Commits
```
feat: Add file upload component
fix: Handle empty transcript edge case
docs: Update setup instructions
chore: Update dependencies
```

---

## 8. Common Issues & Solutions

### Issue: "Permission denied" when uploading file
**Solution:** Check RLS policies. Ensure user has insert permission on recordings table.

```bash
# Debug RLS
SELECT * FROM pg_policies WHERE schemaname='public';
```

### Issue: Edge Function not triggering
**Solution:** Check storage trigger in Supabase dashboard. Ensure function is deployed.

```bash
supabase functions deploy process-recording
supabase functions list
```

### Issue: Deepgram API returns 400 error
**Solution:** Verify API key is correct and file URL is accessible.

```typescript
console.log('File URL:', recording.file_url)
console.log('API Key:', Deno.env.get('DEEPGRAM_API_KEY'))
```

### Issue: TypeScript types not synced
**Solution:** Regenerate types after schema changes.

```bash
supabase gen types typescript --project-id <your-project-id> > src/lib/types.ts
```

---

## 9. Next Steps

1. **Week 1-2:** Set up database, get migrations working
2. **Week 3-4:** Build upload UI, test storage integration
3. **Week 5-6:** Build Edge Functions, test processing pipeline
4. **Week 7-8:** Build results viewer, polish UX
5. **Week 9+:** Testing, deployment, documentation

---

## 10. Resources

- Supabase Docs: https://supabase.com/docs
- React TypeScript: https://react-typescript-cheatsheet.netlify.app/
- shadcn/ui: https://ui.shadcn.com/
- Deepgram API: https://developers.deepgram.com/
- Gemini API: https://ai.google.dev/tutorials

---

**Last Updated:** November 8, 2025
