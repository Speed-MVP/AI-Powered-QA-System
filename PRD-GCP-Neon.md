# Product Requirements Document (PRD)
### AI-Powered Batch QA System MVP (GCP + Neon + React TypeScript)

---

## 1. **Overview**

Design and build a **Minimum Viable Product (MVP)** for an AI-powered call center QA system. Companies upload call audio recordings; the system transcribes, diarizes, and evaluates each call based on company-specific policies with LLM-powered (e.g., Gemini, Claude) intelligence. Results include quality scores, violation flags, and resolution detection—all delivered via a modern, easy-to-use web dashboard.

---

## 2. **Goals & Objectives**

- Enable **fast, accurate, and fully automated QA scoring** for uploaded call recordings.
- Support **custom QA rubrics and policy templates per company**.
- Leverage **external AI (LLMs)** for contextual, criteria-driven evaluation—not simple keyword matching.
- Deliver a **robust MVP**: file upload, processing pipeline, and results dashboard with real-time status.
- Use **GCP + Neon architecture** for cost-effective, scalable, vendor-neutral infrastructure.

---

## 3. **Target Users**

- QA managers and supervisors in mid-to-large call centers
- Admins who set QA policies and rubrics
- Agents and reviewers who view results and coaching feedback

---

## 4. **Functional Requirements**

### 4.1. **Authentication & User Roles**
- Users can sign up, log in, and reset password via custom auth or third-party provider (Auth0, Clerk, NextAuth, Firebase Auth).
- Roles: `admin` (full access), `qa_manager` (manage templates, view results), `reviewer` (view results only).
- Users associated with a company; database-level or application-level permissions enforce data isolation.

### 4.2. **Recording Upload**
- **Upload Page:**
    - Drag-and-drop or select files
    - Supported formats: `.mp3`, `.wav`, `.m4a`, `.mp4` (audio extracted)
    - Batch upload: Multiple files per session
    - Limit: File size up to 2GB; max 100 files per batch
    - Progress tracking with upload percentage

- **Storage:**
    - Uploaded files stored in **GCP Cloud Storage** buckets
    - Signed URLs for secure retrieval
    - Unique job ID assigned immediately upon upload
    - Status initialized to `queued`

### 4.3. **Processing Pipeline**
When file is uploaded, **GCP Cloud Function or Cloud Run job** is triggered:

1. **Update Status**: Mark recording as `processing` in Neon DB
2. **Transcribe**: Call Deepgram batch API
   - Transcription confidence score recorded
   - Handles various audio qualities and accents
3. **Diarize**: Call AssemblyAI API (or use Deepgram's built-in diarization)
   - Separate agent speech from customer speech
   - Speaker-attributed transcript stored as JSONB in Neon
4. **Evaluate**: Send diarized transcript to Gemini/Claude with:
   - Company-specific evaluation criteria
   - Policy template rules
   - Custom LLM evaluation prompts
5. **Score**: Apply company's rules engine
   - Calculate category scores (weighted)
   - Detect policy violations (flag severity)
   - Determine resolution status with confidence
   - Generate coaching feedback
6. **Store Results**: Save evaluation to Neon database
7. **Update Status**: Mark as `completed` or `failed`
8. **Notify User**: Send notification via email or push notification (optional: use Pusher, Socket.io, or polling)

### 4.4. **Dashboard & Results**
- **Dashboard Page:**
  - Real-time list of uploaded files with status badges
  - Filter by: status, date range, company, policy template
  - Sort by: upload date, duration, company, status
  - Show file name, upload time, duration, status, processed time
  - Auto-refresh or manual refresh for status updates

- **Results Viewer:**
  - Full transcript with speaker attribution (Agent/Customer)
  - Overall QA score (0-100)
  - Breakdown by category (e.g., Compliance: 95, Empathy: 82, Resolution: 88)
  - List of policy violations with:
    - Violation type
    - Description
    - Severity (critical/major/minor)
    - Timestamp of occurrence
  - Resolution detection: Yes/No with confidence (0.00-1.00)
  - LLM analysis details (full response JSON)
  - Coaching recommendations/feedback
  - Download transcript as PDF
  - Export results as CSV

### 4.5. **Policy Template & Criteria Management**
- **Policy Template Page:**
  - Create new template per company
  - Template name, description, enabled/disabled toggle
  - Manage evaluation criteria within template:
    - Category name (e.g., "Compliance", "Empathy", "Resolution")
    - Weight (%) — must sum to 100
    - Passing score (0-100)
    - LLM evaluation prompt (the instruction sent to Gemini/Claude)
  - Edit/delete existing criteria
  - Archive/activate templates
  - View version history

### 4.6. **Real-time Notifications & Updates**
- Users can refresh dashboard to see status changes
- Optional: WebSocket or polling mechanism for live updates
- Email notification when batch completes or fails (via SendGrid, AWS SES, or GCP Cloud Functions + SMTP)
- In-app toast notifications for errors, completions

### 4.7. **Security & Privacy**
- **Application-Level Security:** Middleware checks user company_id and role before returning data
- **Authentication:** JWT-based or session-based via Auth0, Clerk, Firebase Auth, or custom implementation
- **Encryption:** All data in transit (HTTPS) and at rest (GCP Storage encryption)
- **Audit Trail:** Log all uploads, evaluations, policy changes with user/timestamp in Neon DB
- **Signed URLs:** Temporary secure access to uploaded audio files in GCP Storage
- **Compliance:** Support for HIPAA, GDPR, compliance-focused deployments (future)

---

## 5. **Non-Functional Requirements**

- **Performance:**
  - Process 100 recordings in parallel
  - Total batch processing time <10 minutes for 100 files
  - Dashboard load time <2 seconds
  - Real-time notifications <500ms latency (if using WebSocket)

- **Accuracy:**
  - 85-92% resolution detection accuracy
  - LLM evaluation based on curated company criteria
  - Minimize false positives on policy violations

- **Scalability:**
  - Auto-scale Cloud Run/Cloud Functions based on queue depth
  - Support 1000+ concurrent users
  - Handle files up to 2GB

- **Reliability:**
  - 99.5% uptime
  - Automatic retry on API failures (Deepgram, Gemini, etc.)
  - Graceful error handling with user feedback

- **Accessibility:**
  - WCAG 2.1 AA compliance
  - Keyboard navigation
  - Screen reader support

---

## 6. **System Architecture**

### 6.1 High-Level Data Flow

```
User Upload
    ↓
[React Frontend] --upload file--> [GCP Cloud Storage]
    ↓
[Cloud Storage Trigger / Pub/Sub]
    ↓
[Cloud Function / Cloud Run: process-recording]
    ├─ Transcribe with Deepgram API
    ├─ Diarize with AssemblyAI API
    ├─ Evaluate with Gemini/Claude API
    ├─ Calculate Scores & Violations
    └─ Update Neon Database
    ↓
[Optional: Pusher/Socket.io/Polling for live updates]
    ↓
[Dashboard] <--refresh/poll-- [Frontend]
```

### 6.2 Tech Stack

#### **Backend**
- **Database:** Neon (serverless Postgres)
- **Storage:** GCP Cloud Storage (for audio files)
- **Compute/API:** Node.js (Express/Fastify/Next.js API routes) or Python (FastAPI/Flask) on Cloud Run
- **Background Jobs:** GCP Cloud Functions (for file processing) or Cloud Tasks/Pub/Sub for queue management
- **Authentication:** Auth0, Clerk, NextAuth (for Next.js), or custom JWT-based auth

#### **Frontend**
- **Framework:** React 18 + TypeScript + Vite
- **UI Components:** shadcn/ui + Tailwind CSS
- **State Management:** Zustand or React Query
- **API Client:** Axios or native fetch
- **File Upload:** react-dropzone
- **Real-time (optional):** Pusher, Socket.io, or polling
- **Build Tool:** Vite (fast dev server, optimized builds)

#### **External APIs**
- **Speech-to-Text:** Deepgram Nova-3 (batch API)
- **Speaker Diarization:** AssemblyAI async API or Deepgram built-in
- **LLM Evaluation:** Google Gemini 2.0 Flash API or Anthropic Claude 3.5 Sonnet
- **Email Notifications:** SendGrid, AWS SES, or SMTP via Cloud Functions

#### **DevOps & CI/CD**
- **Version Control:** GitHub / GitLab
- **Frontend Hosting:** Vercel, Netlify, or GCP Cloud Storage + CDN
- **Backend Hosting:** GCP Cloud Run (auto-scaling, containerized)
- **Database:** Neon (managed Postgres, serverless)
- **Secrets Management:** GCP Secret Manager
- **CI/CD:** GitHub Actions, GitLab CI, or Google Cloud Build

### 6.3 Component Architecture

```
Frontend (React)
├── pages/
│   ├── Dashboard.tsx       (List uploads, status tracking)
│   ├── Upload.tsx          (Drag-drop upload)
│   ├── Results.tsx         (View evaluation results)
│   └── PolicyTemplates.tsx (Manage QA criteria)
├── components/
│   ├── FileUpload.tsx      (Upload widget)
│   ├── RecordingsList.tsx  (Table of recordings)
│   ├── EvaluationResults.tsx (Score breakdown)
│   ├── PolicyTemplateEditor.tsx
│   └── ui/                 (shadcn components)
├── hooks/
│   ├── useRecordings.ts    (Fetch & updates)
│   ├── useEvaluations.ts   (Fetch results)
│   └── useAuth.ts          (Auth state)
├── lib/
│   ├── api.ts              (API client setup)
│   ├── types.ts            (TypeScript types)
│   └── utils.ts            (Helper functions)
└── App.tsx

Backend (Node.js/Express or Python/FastAPI on Cloud Run)
├── src/
│   ├── routes/
│   │   ├── auth.ts         (Login, signup, logout)
│   │   ├── recordings.ts   (Upload, list, status)
│   │   ├── evaluations.ts  (Fetch results)
│   │   └── templates.ts    (Policy CRUD)
│   ├── services/
│   │   ├── storage.ts      (GCP Storage operations)
│   │   ├── deepgram.ts     (Transcription API)
│   │   ├── assemblyai.ts   (Diarization API)
│   │   ├── gemini.ts       (LLM evaluation)
│   │   └── scoring.ts      (Rules engine)
│   ├── middleware/
│   │   ├── auth.ts         (JWT verification)
│   │   └── permissions.ts  (Role-based access)
│   ├── models/             (Database models/schemas)
│   └── index.ts            (Entry point)
├── functions/              (Cloud Functions)
│   └── process-recording/  (Async processing)
├── Dockerfile              (For Cloud Run)
└── package.json

Database (Neon PostgreSQL)
├── companies
├── users
├── policy_templates
├── evaluation_criteria
├── recordings
├── transcripts
├── evaluations
├── category_scores
└── policy_violations
```

---

## 7. **Data Model/ERD**

### 7.1 Tables

#### `companies`
- `id` (UUID, PK)
- `company_name` (VARCHAR)
- `industry` (VARCHAR)
- `created_at` (TIMESTAMP, DEFAULT NOW())

#### `users`
- `id` (UUID, PK)
- `company_id` (UUID, FK → companies)
- `email` (VARCHAR, UNIQUE)
- `password_hash` (VARCHAR) — if custom auth, else NULL
- `full_name` (VARCHAR)
- `role` (ENUM: admin | qa_manager | reviewer)
- `created_at` (TIMESTAMP)

#### `policy_templates`
- `id` (UUID, PK)
- `company_id` (UUID, FK → companies)
- `template_name` (VARCHAR)
- `description` (TEXT)
- `is_active` (BOOLEAN, DEFAULT TRUE)
- `created_at` (TIMESTAMP)

#### `evaluation_criteria`
- `id` (UUID, PK)
- `policy_template_id` (UUID, FK → policy_templates)
- `category_name` (VARCHAR)
- `weight` (DECIMAL 5,2) — sum must equal 100 per template
- `passing_score` (INTEGER, 0-100)
- `evaluation_prompt` (TEXT) — LLM instruction for this criteria
- `created_at` (TIMESTAMP)

#### `recordings`
- `id` (UUID, PK)
- `company_id` (UUID, FK → companies)
- `uploaded_by_user_id` (UUID, FK → users)
- `file_name` (VARCHAR)
- `file_url` (TEXT) — GCP Storage signed URL
- `duration_seconds` (INTEGER)
- `status` (ENUM: queued | processing | completed | failed, DEFAULT queued)
- `uploaded_at` (TIMESTAMP, DEFAULT NOW())
- `processed_at` (TIMESTAMP, nullable)

#### `transcripts`
- `id` (UUID, PK)
- `recording_id` (UUID, FK → recordings, UNIQUE 1:1)
- `transcript_text` (TEXT)
- `diarized_segments` (JSONB) — [{speaker: "agent"|"customer", text: "", timestamp: 0.0}, ...]
- `transcription_confidence` (DECIMAL 5,2)
- `created_at` (TIMESTAMP)

#### `evaluations`
- `id` (UUID, PK)
- `recording_id` (UUID, FK → recordings, UNIQUE 1:1)
- `policy_template_id` (UUID, FK → policy_templates)
- `evaluated_by_user_id` (UUID, FK → users)
- `overall_score` (INTEGER, 0-100)
- `resolution_detected` (BOOLEAN)
- `resolution_confidence` (DECIMAL 3,2, 0.00-1.00)
- `llm_analysis` (JSONB) — Full LLM response
- `status` (ENUM: pending | completed | reviewed, DEFAULT pending)
- `created_at` (TIMESTAMP)

#### `category_scores`
- `id` (UUID, PK)
- `evaluation_id` (UUID, FK → evaluations)
- `category_name` (VARCHAR)
- `score` (INTEGER, 0-100)
- `feedback` (TEXT)

#### `policy_violations`
- `id` (UUID, PK)
- `evaluation_id` (UUID, FK → evaluations)
- `criteria_id` (UUID, FK → evaluation_criteria)
- `violation_type` (VARCHAR)
- `description` (TEXT)
- `severity` (ENUM: critical | major | minor)

### 7.2 Key Relationships

```
companies (1) ────► (N) users
companies (1) ────► (N) policy_templates
companies (1) ────► (N) recordings

policy_templates (1) ────► (N) evaluation_criteria
policy_templates (1) ────► (N) evaluations

users (1) ────► (N) recordings [uploaded_by_user_id]
users (1) ────► (N) evaluations [evaluated_by_user_id]

recordings (1) ────► (1) transcripts
recordings (1) ────► (1) evaluations

evaluations (1) ────► (N) category_scores
evaluations (1) ────► (N) policy_violations

evaluation_criteria (1) ────► (N) policy_violations
```

### 7.3 Security Considerations

**Application-Level Row Security:**
- Middleware checks `user.company_id` matches resource `company_id` before queries.
- Role-based checks: only `admin` or `qa_manager` can edit policy templates.
- Example (Node.js/Express):
```javascript
app.get('/api/recordings', authenticateUser, async (req, res) => {
  const { company_id } = req.user;
  const recordings = await db.query(
    'SELECT * FROM recordings WHERE company_id = $1',
    [company_id]
  );
  res.json(recordings);
});
```

**Database Constraints:**
- Foreign keys ensure referential integrity.
- Check constraints on scores (0-100), weights (sum to 100).

---

## 8. **Acceptance Criteria**

- [ ] User can upload audio files, see them listed in dashboard, and track processing status
- [ ] Uploaded files are securely stored in GCP Cloud Storage with signed URLs
- [ ] After processing, user can view transcript, scores, results, and policy violations for each file
- [ ] QA managers can create/edit policy templates and criteria per company
- [ ] System evaluates calls using the selected policy template and criteria, not generic rules
- [ ] CSV export for complete batch results (scores, transcripts, violations)
- [ ] Email or in-app notifications on job status changes
- [ ] Application-level security prevents cross-company data access
- [ ] All critical errors and failures are logged with appropriate error messages to users
- [ ] MVP deployed to production (frontend on Vercel/Netlify, backend on GCP Cloud Run, DB on Neon)

---

## 9. **Metrics & KPIs**

- Time from upload to results (average, 95th percentile)
- % of evaluations completed without error
- QA scoring accuracy (compared with manual reviews)
- Policy violation detection rate
- User engagement (uploads, views per day)
- Uptime and reliability (target: 99.5%)
- Cost per evaluation (target: <$0.50 per call)

---

## 10. **Timeline (8 Weeks)**

### Week 1-2: Setup & Foundation
- Set up GCP project (Cloud Storage, Cloud Run, Cloud Functions, IAM)
- Set up Neon database, create schema migrations
- Initialize React + TypeScript + Vite frontend
- Set up authentication (Auth0/Clerk or custom JWT)
- Configure CI/CD pipeline (GitHub Actions or Cloud Build)

### Week 3-4: Upload & Storage
- Build file upload component (drag-drop with react-dropzone)
- Implement GCP Storage integration (signed URLs, bucket policies)
- Create recordings list view with status display
- Add status filtering and sorting
- Build authentication flow (signup, login, logout)

### Week 5-6: Processing Pipeline
- Build Cloud Function for transcription (Deepgram API)
- Build Cloud Function for evaluation (Gemini/Claude API)
- Build rules engine for scoring and violations
- Implement main orchestrator function
- Add retry logic and error handling
- Test end-to-end with sample audio files

### Week 7: Results & Policy Management
- Build evaluation results viewer
- Show transcript with speaker attribution
- Display category scores breakdown
- Show policy violations with severity
- Create policy template editor UI
- Implement evaluation criteria CRUD
- Add CSV export functionality

### Week 8: Polish, Testing & Deployment
- Polish UI/UX with shadcn/ui
- Write integration tests
- Conduct user testing with QA managers
- Set up monitoring/logging (Cloud Logging, Sentry)
- Deploy frontend to Vercel/Netlify
- Deploy backend to Cloud Run
- Create user documentation

**Total: 8 weeks to production MVP**

---

## 11. **Risks & Mitigations**

- **External API rate limits:** Design job queue with retries/exponential backoff
- **Audio format incompatibility:** Standardize supported formats, handle conversion errors
- **LLM eval cost:** Set quotas per batch, surface usage indicators in UI
- **Policy customization complexity:** Limit initial MVP to essential fields, test with real QA managers
- **GCP setup complexity:** Use Cloud Run for simplicity, avoid over-engineering with Kubernetes initially
- **Auth complexity:** Use managed auth provider (Auth0, Clerk) to avoid building from scratch

---

## 12. **Out of Scope (for MVP)**

- Real-time/live call monitoring
- Agent-side coaching/prompts during calls
- Multi-channel support (chat/email)
- Advanced reporting/analytics dashboards
- Custom branding/theming
- SAML/SSO integration
- Mobile app (iOS/Android)
- Multi-language support (initially English only)

---

## 13. **Cost Estimate (100 recordings/month)**

### GCP + Neon Stack:
- **Neon Database:** Free tier (0-10GB, 3 branches) → $0/mo initially, ~$5-10/mo at scale
- **GCP Cloud Storage:** $0.026/GB/month → ~$2/mo for 100 files (~75GB)
- **GCP Cloud Run/Functions:** First 2M requests free, then $0.40/million → ~$0-5/mo
- **Deepgram API:** $0.0043/min → $21.50 for 5,000 minutes (100 calls × 50min avg)
- **AssemblyAI API (optional):** $0.01/min → $50 for 5,000 minutes
- **Gemini 2.0 Flash API:** $0.15/1M input tokens → ~$15 for 100 evaluations
- **SendGrid/Email (optional):** Free tier 100 emails/day

**Total Cost:** ~$35-50/month for 100 recordings (vs Supabase $25/mo + limits)

At scale (1,000 recordings/month): ~$250-350/month

**Compare to:** Manual QA at $15/call = $15,000/month → **97% cost savings**

---

## 14. **Technical Architecture Details**

### 14.1 Authentication Flow

**Option 1: Auth0 / Clerk (Recommended for MVP)**
```javascript
// Frontend: Login with Auth0
import { Auth0Provider, useAuth0 } from '@auth0/auth0-react';

const { loginWithRedirect, user, getAccessTokenSilently } = useAuth0();

// Get JWT token for API calls
const token = await getAccessTokenSilently();
const response = await fetch('/api/recordings', {
  headers: { Authorization: `Bearer ${token}` }
});
```

**Option 2: Custom JWT (NextAuth or custom)**
```javascript
// Backend: Verify JWT middleware
import jwt from 'jsonwebtoken';

export const authenticateUser = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'Unauthorized' });
  
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded; // { id, email, company_id, role }
    next();
  } catch (err) {
    res.status(401).json({ error: 'Invalid token' });
  }
};
```

### 14.2 File Upload Flow

**Frontend (React):**
```typescript
import { useDropzone } from 'react-dropzone';

const FileUpload = ({ companyId }: { companyId: string }) => {
  const onDrop = async (files: File[]) => {
    const file = files[0];
    
    // Step 1: Get signed upload URL from backend
    const { signedUrl, fileUrl } = await fetch('/api/storage/signed-url', {
      method: 'POST',
      headers: { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ 
        fileName: file.name,
        contentType: file.type
      })
    }).then(r => r.json());
    
    // Step 2: Upload directly to GCP Storage
    await fetch(signedUrl, {
      method: 'PUT',
      headers: { 'Content-Type': file.type },
      body: file
    });
    
    // Step 3: Create database record
    await fetch('/api/recordings', {
      method: 'POST',
      headers: { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        company_id: companyId,
        file_name: file.name,
        file_url: fileUrl,
        status: 'queued'
      })
    });
    
    // Step 4: Trigger processing (Cloud Function)
    await fetch('/api/recordings/process', {
      method: 'POST',
      headers: { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ file_url: fileUrl })
    });
  };
  
  const { getRootProps, getInputProps } = useDropzone({ onDrop });
  
  return (
    <div {...getRootProps()} className="border-2 border-dashed p-8">
      <input {...getInputProps()} />
      <p>Drag & drop audio files here</p>
    </div>
  );
};
```

**Backend (Node.js/Express on Cloud Run):**
```javascript
import { Storage } from '@google-cloud/storage';
const storage = new Storage();

app.post('/api/storage/signed-url', authenticateUser, async (req, res) => {
  const { fileName, contentType } = req.body;
  const { company_id } = req.user;
  
  const bucket = storage.bucket(process.env.GCP_BUCKET_NAME);
  const blob = bucket.file(`${company_id}/${Date.now()}_${fileName}`);
  
  // Generate signed URL for upload (valid for 15 minutes)
  const [signedUrl] = await blob.getSignedUrl({
    version: 'v4',
    action: 'write',
    expires: Date.now() + 15 * 60 * 1000,
    contentType
  });
  
  // Generate public URL for later access
  const fileUrl = `https://storage.googleapis.com/${bucket.name}/${blob.name}`;
  
  res.json({ signedUrl, fileUrl });
});

app.post('/api/recordings', authenticateUser, async (req, res) => {
  const { company_id, file_name, file_url, status } = req.body;
  
  // Insert into Neon DB
  const result = await pool.query(
    'INSERT INTO recordings (company_id, uploaded_by_user_id, file_name, file_url, status) VALUES ($1, $2, $3, $4, $5) RETURNING *',
    [company_id, req.user.id, file_name, file_url, status || 'queued']
  );
  
  res.json(result.rows[0]);
});
```

### 14.3 Cloud Function Processing

**Cloud Function (Node.js):**
```javascript
// functions/process-recording/index.js
import { Storage } from '@google-cloud/storage';
import { Pool } from 'pg';
import axios from 'axios';

const storage = new Storage();
const pool = new Pool({ connectionString: process.env.DATABASE_URL });

export const processRecording = async (req, res) => {
  const { file_url } = req.body;
  
  try {
    // 1. Get recording from DB
    const recording = await pool.query(
      'SELECT * FROM recordings WHERE file_url = $1',
      [file_url]
    );
    
    // 2. Update status to processing
    await pool.query(
      'UPDATE recordings SET status = $1 WHERE id = $2',
      ['processing', recording.rows[0].id]
    );
    
    // 3. Transcribe with Deepgram
    const transcriptResponse = await axios.post(
      'https://api.deepgram.com/v1/listen?model=nova-3&diarize=true',
      { url: file_url },
      {
        headers: {
          'Authorization': `Token ${process.env.DEEPGRAM_API_KEY}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    const transcript = transcriptResponse.data.results.channels[0].alternatives[0];
    
    // 4. Save transcript
    await pool.query(
      'INSERT INTO transcripts (recording_id, transcript_text, diarized_segments) VALUES ($1, $2, $3)',
      [recording.rows[0].id, transcript.transcript, JSON.stringify(transcript.words)]
    );
    
    // 5. Evaluate with LLM
    const evaluation = await evaluateWithGemini(transcript, recording.rows[0].policy_template_id);
    
    // 6. Save evaluation
    await pool.query(
      'INSERT INTO evaluations (recording_id, overall_score, resolution_detected, llm_analysis) VALUES ($1, $2, $3, $4)',
      [recording.rows[0].id, evaluation.overall_score, evaluation.resolution_detected, JSON.stringify(evaluation)]
    );
    
    // 7. Update status to completed
    await pool.query(
      'UPDATE recordings SET status = $1, processed_at = NOW() WHERE id = $2',
      ['completed', recording.rows[0].id]
    );
    
    res.json({ success: true });
  } catch (error) {
    console.error('Processing failed:', error);
    
    await pool.query(
      'UPDATE recordings SET status = $1 WHERE file_url = $2',
      ['failed', file_url]
    );
    
    res.status(500).json({ error: error.message });
  }
};
```

### 14.4 Deployment Configuration

**Docker Configuration (Cloud Run):**
```dockerfile
# Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

ENV PORT=8080
EXPOSE 8080

CMD ["node", "src/index.js"]
```

**GitHub Actions CI/CD:**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}
      
      - name: Build and Push Docker Image
        run: |
          gcloud builds submit --tag gcr.io/${{ secrets.GCP_PROJECT_ID }}/api:$GITHUB_SHA
      
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy api \
            --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/api:$GITHUB_SHA \
            --platform managed \
            --region us-central1 \
            --allow-unauthenticated
```

---

## 15. **References**

- GCP Cloud Storage: https://cloud.google.com/storage
- GCP Cloud Run: https://cloud.google.com/run
- Neon Database: https://neon.tech
- Deepgram API: https://developers.deepgram.com
- Gemini API: https://ai.google.dev
- Auth0: https://auth0.com
- Clerk: https://clerk.com

---

**Last Updated:** November 8, 2025 (Updated for GCP + Neon architecture)
**Version:** 0.2.0-MVP
