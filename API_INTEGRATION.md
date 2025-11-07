# API Integration Guide - AI QA MVP

## Overview

This document outlines all external API integrations and how to use them in the MVP.

---

## 1. Deepgram Speech-to-Text API

### Purpose
Convert audio to text with speaker diarization.

### Pricing
- **Batch API:** $0.0043/min (cheaper, for post-recorded audio)
- **Streaming API:** $0.0059/min (real-time, not used in MVP)

### Setup

1. Create account at https://deepgram.com
2. Get API key from dashboard
3. Add to `.env.local`:
```
VITE_DEEPGRAM_API_KEY=your-key-here
```

### Usage in Edge Function

```typescript
// supabase/functions/transcribe-audio/index.ts

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'

serve(async (req) => {
  const { fileUrl } = await req.json()
  const apiKey = Deno.env.get('DEEPGRAM_API_KEY')
  
  const response = await fetch(
    'https://api.deepgram.com/v1/listen?model=nova-3&diarize=true',
    {
      method: 'POST',
      headers: {
        'Authorization': `Token ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ url: fileUrl })
    }
  )
  
  if (!response.ok) {
    throw new Error(`Deepgram error: ${response.statusText}`)
  }
  
  const result = await response.json()
  
  // Extract transcript
  const transcript = result.results.channels[0].alternatives[0].transcript
  
  // Extract word-level details
  const words = result.results.channels[0].alternatives[0].words
  // Each word: {word, start, end, confidence, speaker}
  
  return new Response(JSON.stringify({ 
    transcript,
    words,
    confidence: result.metadata.confidence
  }))
})
```

### Diarization Output Format

```json
{
  "results": {
    "channels": [
      {
        "alternatives": [
          {
            "transcript": "Thank you for calling...",
            "words": [
              {
                "word": "Thank",
                "start": 0.0,
                "end": 0.5,
                "confidence": 0.95,
                "speaker": 0
              },
              {
                "word": "you",
                "start": 0.5,
                "end": 0.8,
                "confidence": 0.98,
                "speaker": 0
              },
              {
                "word": "Hello",
                "start": 2.0,
                "end": 2.3,
                "confidence": 0.96,
                "speaker": 1
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### Error Handling

```typescript
try {
  const response = await fetch(deepgramUrl, options)
  
  if (response.status === 401) {
    throw new Error('Invalid Deepgram API key')
  }
  if (response.status === 429) {
    throw new Error('Rate limit exceeded. Retry after 60s.')
  }
  if (!response.ok) {
    throw new Error(`Deepgram error: ${response.statusText}`)
  }
  
  return await response.json()
} catch (error) {
  console.error('Transcription failed:', error)
  // Mark job as failed in database
}
```

---

## 2. AssemblyAI Speaker Diarization

### Purpose
Advanced speaker identification (alternative to Deepgram's built-in diarization).

### Pricing
- $0.01 per minute of audio

### Setup

1. Create account at https://assemblyai.com
2. Get API key
3. Add to `.env.local`:
```
VITE_ASSEMBLYAI_API_KEY=your-key-here
```

### Usage

```typescript
// supabase/functions/diarize-audio/index.ts

serve(async (req) => {
  const { audioUrl } = await req.json()
  const apiKey = Deno.env.get('ASSEMBLYAI_API_KEY')
  
  // Step 1: Submit transcription job
  const submitResponse = await fetch('https://api.assemblyai.com/v2/transcript', {
    method: 'POST',
    headers: {
      'Authorization': apiKey,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      audio_url: audioUrl,
      speaker_labels: true,
      speaker_count: 2 // Agent + Customer
    })
  })
  
  const submitData = await submitResponse.json()
  const transcriptId = submitData.id
  
  // Step 2: Poll until complete
  let transcript = null
  while (!transcript || transcript.status === 'processing') {
    const pollResponse = await fetch(
      `https://api.assemblyai.com/v2/transcript/${transcriptId}`,
      { headers: { 'Authorization': apiKey } }
    )
    transcript = await pollResponse.json()
    
    if (transcript.status === 'processing') {
      await new Promise(resolve => setTimeout(resolve, 1000)) // Wait 1s
    }
  }
  
  // Step 3: Parse speaker segments
  const segments = transcript.utterances.map(u => ({
    speaker: u.speaker, // 'A' or 'B'
    text: u.text,
    start: u.start / 1000, // Convert ms to seconds
    end: u.end / 1000,
    confidence: u.confidence
  }))
  
  return new Response(JSON.stringify({ segments }))
})
```

### Response Format

```json
{
  "utterances": [
    {
      "confidence": 0.95,
      "end": 5000,
      "speaker": "A",
      "start": 0,
      "text": "Hello, how can I help you?"
    },
    {
      "confidence": 0.92,
      "end": 8000,
      "speaker": "B",
      "start": 5000,
      "text": "I need help with my account."
    }
  ]
}
```

---

## 3. Google Gemini API

### Purpose
LLM-based evaluation of conversations against company policies.

### Pricing
- **Gemini 2.0 Flash:** $0.15/1M input tokens, $0.60/1M output tokens
- **Estimate:** ~$15 per 100 evaluations (avg 1000 tokens per call)

### Setup

1. Get API key from https://ai.google.dev
2. Add to `.env.local`:
```
VITE_GEMINI_API_KEY=your-key-here
```

### Usage

```typescript
// supabase/functions/evaluate-with-llm/index.ts

import Anthropic from '@anthropic-ai/sdk' // Or use Gemini SDK

serve(async (req) => {
  const { transcript, policyTemplate, criteria } = await req.json()
  
  // Build LLM prompt from company's criteria
  const prompt = buildEvaluationPrompt(transcript, criteria)
  
  const response = await fetch('https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-goog-api-key': Deno.env.get('GEMINI_API_KEY')
    },
    body: JSON.stringify({
      contents: [{
        parts: [{
          text: prompt
        }]
      }],
      generationConfig: {
        temperature: 0.3, // Lower = more deterministic
        topK: 40,
        topP: 0.95,
        maxOutputTokens: 1000
      }
    })
  })
  
  const result = await response.json()
  const evaluationText = result.contents[0].parts[0].text
  
  // Parse LLM response
  const parsed = parseEvaluationResponse(evaluationText, criteria)
  
  return new Response(JSON.stringify(parsed))
})

function buildEvaluationPrompt(transcript, criteria) {
  return `
Evaluate this customer service call transcript based on the following criteria:

${criteria.map(c => `
- ${c.category_name} (Weight: ${c.weight}%, Passing: ${c.passing_score})
  Evaluation: ${c.evaluation_prompt}
`).join('\n')}

TRANSCRIPT:
${transcript}

Provide evaluation in JSON format:
{
  "compliance": {
    "score": 85,
    "feedback": "..."
  },
  "empathy": {
    "score": 90,
    "feedback": "..."
  },
  "resolution": {
    "score": 88,
    "feedback": "...",
    "resolved": true
  }
}
  `
}

function parseEvaluationResponse(text, criteria) {
  // Extract JSON from LLM response
  const jsonMatch = text.match(/\{[\s\S]*\}/)
  const parsed = JSON.parse(jsonMatch[0])
  
  // Calculate weighted score
  let totalScore = 0
  let totalWeight = 0
  
  for (const [key, value] of Object.entries(parsed)) {
    const criteria = allCriteria.find(c => c.category_name.toLowerCase() === key)
    if (criteria) {
      totalScore += value.score * criteria.weight
      totalWeight += criteria.weight
    }
  }
  
  const overallScore = Math.round(totalScore / totalWeight)
  
  return {
    category_scores: parsed,
    overall_score: overallScore,
    resolution_detected: parsed.resolution?.resolved || false
  }
}
```

### Example Evaluation Prompt

```
Evaluate this customer service call transcript based on the following criteria:

- Compliance (Weight: 40%, Passing: 90)
  Evaluation: Check if agent provided required TCPA disclosures. Specifically look for:
  1. Company name disclosure
  2. Purpose of call disclosure
  3. DNC registry check mention

- Empathy (Weight: 30%, Passing: 70)
  Evaluation: Evaluate how well agent acknowledged customer frustration and concerns. Score higher if agent uses phrases like "I understand", "That must be frustrating", etc.

- Resolution (Weight: 30%, Passing: 80)
  Evaluation: Determine if customer's problem was actually resolved. Did customer confirm satisfaction? Was there a clear action plan?

TRANSCRIPT:
Agent: Thank you for calling Acme Financial. This is Sarah speaking. May I ask who I'm speaking with?
Customer: Hi, I'm calling about my credit card interest rate going up.
Agent: I completely understand how frustrating that must be. Let me pull up your account and see what's going on...
[... more transcript ...]
Agent: Is there anything else I can help you with today?
Customer: No, that's it. Thanks for your help.

Provide evaluation in JSON format:
{
  "compliance": {
    "score": 85,
    "feedback": "Agent disclosed company name and purpose. Did not explicitly mention DNC check."
  },
  "empathy": {
    "score": 88,
    "feedback": "Agent used empathetic language ('I understand how frustrating'). Good acknowledgment of customer concern."
  },
  "resolution": {
    "score": 92,
    "feedback": "Customer explicitly confirmed satisfaction. Clear resolution achieved.",
    "resolved": true
  }
}
```

---

## 4. Anthropic Claude API (Alternative to Gemini)

### Setup

```
VITE_CLAUDE_API_KEY=sk-ant-...
```

### Usage

```typescript
import Anthropic from '@anthropic-ai/sdk'

const client = new Anthropic({
  apiKey: Deno.env.get('CLAUDE_API_KEY')
})

const response = await client.messages.create({
  model: 'claude-3-5-sonnet-20241022',
  max_tokens: 1000,
  messages: [
    {
      role: 'user',
      content: evaluationPrompt
    }
  ]
})

const evaluation = response.content[0].text
```

---

## 5. Supabase Storage API

### Upload File

```typescript
const { data, error } = await supabase.storage
  .from('recordings')
  .upload(`${companyId}/${filename}`, file, {
    cacheControl: '3600',
    upsert: false
  })

if (error) console.error('Upload failed:', error)
const signedUrl = supabase.storage
  .from('recordings')
  .getPublicUrl(data.path)
```

### Delete File

```typescript
const { error } = await supabase.storage
  .from('recordings')
  .remove([`${companyId}/${filename}`])
```

---

## 6. Rate Limiting & Retry Logic

### Implement Exponential Backoff

```typescript
async function callAPIWithRetry(
  fn: () => Promise<any>,
  maxRetries: number = 3
) {
  let lastError
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error
      
      // Only retry on specific errors
      if (error.status === 429) { // Rate limited
        const delay = Math.pow(2, i) * 1000 // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, delay))
      } else if (error.status >= 500) { // Server error
        const delay = Math.pow(2, i) * 1000
        await new Promise(resolve => setTimeout(resolve, delay))
      } else {
        throw error // Don't retry on 4xx errors (except 429)
      }
    }
  }
  
  throw lastError
}

// Usage
const transcript = await callAPIWithRetry(
  () => transcribeWithDeepgram(fileUrl)
)
```

---

## 7. Cost Optimization

### Batch Processing
- Process multiple files in parallel (Supabase handles parallelization)
- Use batch APIs when available (Deepgram batch vs streaming)

### Caching
- Cache policy templates to avoid repeated LLM evaluation
- Cache company evaluation criteria

### Token Optimization
- Trim transcript to relevant portions
- Use concise LLM prompts
- Request only necessary fields

### Cost Breakdown (per 100 calls)

```
Deepgram transcription:   $21.50 (100 calls × 15min × $0.0043/min)
AssemblyAI diarization:   $15.00 (100 calls × 15min × $0.01/min) [Optional]
Gemini evaluation:        $15.00 (100 calls × 1000 tokens × $0.15/M)
Supabase storage:         $0.00 (free tier: 1GB, then $5/100GB)
Total:                    ~$51.50 per 100 calls
```

---

## 8. Monitoring & Logging

### Log API Calls

```typescript
function logAPICall(service, method, url, status, duration, cost) {
  console.log(`[${service}] ${method} ${url} - ${status} (${duration}ms, $${cost})`)
  
  // Store in database for analytics
  await supabase.from('api_logs').insert({
    service,
    method,
    url,
    status,
    duration,
    cost,
    timestamp: new Date()
  })
}
```

### Monitor Errors

```typescript
async function callDeepgram(url) {
  try {
    const response = await fetch(deepgramUrl)
    logAPICall('Deepgram', 'POST', url, response.status, duration, cost)
    return response.json()
  } catch (error) {
    logAPICall('Deepgram', 'POST', url, 'ERROR', duration, cost)
    // Send alert
    await sendAlert('Deepgram API error', error.message)
  }
}
```

---

## 9. Testing APIs Locally

### Test Deepgram

```bash
curl -X POST https://api.deepgram.com/v1/listen?model=nova-3 \
  -H "Authorization: Token YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://sample-audio.com/file.mp3"}'
```

### Test Gemini

```bash
curl -X POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=YOUR_KEY \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "parts": [{"text": "Hello, how are you?"}]
    }]
  }'
```

---

## 10. Troubleshooting

### Issue: "Invalid API key"
- Verify key is correct in `.env.local`
- Check API key hasn't expired
- Ensure no extra spaces/characters

### Issue: Rate limit exceeded
- Implement exponential backoff (see section 6)
- Spread requests across time
- Check service quota limits

### Issue: Timeout errors
- Increase timeout duration for long files
- Consider chunking very long audio
- Check network connectivity

### Issue: Wrong evaluation results
- Review LLM prompt for clarity
- Add examples to prompt
- Test with simpler criteria first

---

**Last Updated:** November 8, 2025
