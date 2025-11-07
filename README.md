AI-Powered Batch QA System MVP
Project Overview
An AI-powered call center quality assurance platform that enables companies to upload pre-recorded call audio, automatically transcribe and evaluate them using LLM-based intelligence (Gemini, Claude), and generate accurate quality scores based on company-specific policies and evaluation criteria.

Core Value Proposition:

Upload call recordings → AI evaluates using custom company policies (not generic keywords) → Get comprehensive QA results in minutes

90-97% cost reduction vs manual QA ($0.50-2 per call vs $15-25)

100% call coverage instead of 1-3% sampling

85-92% accuracy on problem resolution detection

2X better than keyword-based systems through contextual LLM evaluation

Tech Stack: Supabase (backend) + React TypeScript (frontend) + Deepgram (transcription) + Gemini/Claude (LLM evaluation)

Table of Contents
1. Product Requirements

2. Architecture

3. Database Schema (ERD)

4. Development Timeline

5. Setup & Installation

6. API Reference

7. Deployment

8. Future Expansion

1. Product Requirements
1.1 Functional Requirements
Authentication & User Management
Users can sign up, log in, reset password via Supabase Auth

Roles: admin (full access), qa_manager (manage templates, view results), reviewer (view results only)

Multi-tenant: Users associated with a company; Row Level Security enforces data isolation

Email verification for new accounts

Recording Upload
File Upload Interface:

Drag-and-drop or browse file selector

Supported formats: MP3, WAV, M4A, MP4 (audio extracted)

Batch upload: 1-100+ files per session

Max file size: 2GB per file

Progress tracking with upload percentage

Storage:

Files stored in Supabase Storage (CDN-backed, secure)

Signed URLs for secure retrieval

Unique job ID assigned immediately upon upload

Status initialized to queued

Processing Pipeline
When file is uploaded, Supabase Edge Function is triggered:

Update Status: Mark recording as processing

Transcribe: Call Deepgram batch API

Transcription confidence score recorded

Handles various audio qualities and accents

Diarize: Call AssemblyAI API

Separate agent speech from customer speech

Speaker-attributed transcript stored as JSONB

Evaluate: Send diarized transcript to Gemini/Claude with:

Company-specific evaluation criteria

Policy template rules

Custom LLM evaluation prompts

Score: Apply company's rules engine

Calculate category scores (weighted)

Detect policy violations (flag severity)

Determine resolution status with confidence

Generate coaching feedback

Store Results: Save evaluation to database

Update Status: Mark as completed or failed

Notify User: Push notification via Supabase Realtime

Dashboard & Results
Dashboard Page:

Real-time list of uploaded files with status badges

Filter by: status, date range, company, policy template

Sort by: upload date, duration, company, status

Show file name, upload time, duration, status, processed time

Results Viewer:

Full transcript with speaker attribution (Agent/Customer)

Overall QA score (0-100)

Breakdown by category (e.g., Compliance: 95, Empathy: 82, Resolution: 88)

List of policy violations with:

Violation type

Description

Severity (critical/major/minor)

Timestamp of occurrence

Resolution detection: Yes/No with confidence (0.00-1.00)

LLM analysis details (full response JSON)

Coaching recommendations/feedback

Download transcript as PDF

Export results as CSV

Policy Template & Criteria Management
Policy Template Page:

Create new template per company

Template name, description, enabled/disabled toggle

Manage evaluation criteria within template:

Category name (e.g., "Compliance", "Empathy", "Resolution")

Weight (%) — must sum to 100

Passing score (0-100)

LLM evaluation prompt (the instruction sent to Gemini/Claude)

Edit/delete existing criteria

Archive/activate templates

View version history

Real-time Notifications & Updates
WebSocket-powered (Supabase Realtime) updates

Users see status changes instantly (queued → processing → completed)

Email notification when batch completes or fails

In-app toast notifications for errors, completions

Security & Privacy
Row Level Security (RLS): Users only access their company's data

Authentication: JWT-based via Supabase Auth

Encryption: All data in transit (HTTPS) and at rest

Audit Trail: Log all uploads, evaluations, policy changes with user/timestamp

Signed URLs: Temporary secure access to uploaded audio files

Compliance: Support for HIPAA, GDPR, compliance-focused deployments (future)

1.2 Non-Functional Requirements
Performance:

Process 100 recordings in parallel

Total batch processing time <10 minutes for 100 files

Dashboard load time <2 seconds

Real-time notifications <500ms latency

Accuracy:

85-92% resolution detection accuracy

LLM evaluation based on curated company criteria

Minimize false positives on policy violations

Scalability:

Auto-scale Edge Functions based on queue depth

Support 1000+ concurrent users

Handle files up to 2GB

Reliability:

99.5% uptime

Automatic retry on API failures (Deepgram, Gemini, etc.)

Graceful error handling with user feedback

Accessibility:

WCAG 2.1 AA compliance

Keyboard navigation

Screen reader support

2. Architecture
2.1 High-Level Data Flow
text
User Upload
    ↓
[React Frontend] --upload file--> [Supabase Storage]
    ↓
[Storage Trigger]
    ↓
[Supabase Edge Function: process-recording]
    ├─ Transcribe with Deepgram
    ├─ Diarize with AssemblyAI
    ├─ Evaluate with Gemini/Claude
    ├─ Calculate Scores & Violations
    └─ Update Database
    ↓
[Supabase Realtime]
    ↓
[Dashboard] <--live update-- [Frontend]
2.2 Tech Stack
Backend
Database: Supabase PostgreSQL

Authentication: Supabase Auth (JWT)

Storage: Supabase Storage (S3-compatible)

Real-time: Supabase Realtime (WebSocket)

Serverless Functions: Supabase Edge Functions (Deno/TypeScript)

Row Level Security: PostgreSQL RLS policies

Frontend
Framework: React 18 + TypeScript + Vite

UI Components: shadcn/ui + Tailwind CSS

State Management: Zustand

API Client: @supabase/supabase-js

File Upload: react-dropzone

Real-time: Supabase WebSocket subscriptions

Build Tool: Vite (fast dev server, optimized builds)

External APIs
Speech-to-Text: Deepgram Nova-3 (real-time streaming, batch API)

Speaker Diarization: AssemblyAI async API

LLM Evaluation: Google Gemini 2.0 Flash API or Anthropic Claude 3.5 Sonnet

Email Notifications: SendGrid or Supabase Realtime

2.3 Component Architecture
text
Frontend (React)
├── Pages
│   ├── Dashboard.tsx       (List uploads, status tracking)
│   ├── Upload.tsx          (Drag-drop upload)
│   ├── Results.tsx         (View evaluation results)
│   └── PolicyTemplates.tsx (Manage QA criteria)
├── Components
│   ├── FileUpload.tsx      (Upload widget)
│   ├── RecordingsList.tsx  (Table of recordings)
│   ├── EvaluationResults.tsx (Score breakdown)
│   ├── PolicyTemplateEditor.tsx
│   └── ui/                 (shadcn components)
├── Hooks
│   ├── useRecordings.ts    (Fetch & realtime updates)
│   ├── useEvaluations.ts   (Fetch results)
│   └── useRealtime.ts      (Subscribe to status changes)
├── Lib
│   ├── supabase.ts         (Supabase client init)
│   ├── types.ts            (Auto-generated from DB schema)
│   └── utils.ts            (Helper functions)
└── App.tsx

Backend (Supabase)
├── Database (PostgreSQL)
│   ├── companies
│   ├── users
│   ├── policy_templates
│   ├── evaluation_criteria
│   ├── recordings
│   ├── transcripts
│   ├── evaluations
│   ├── category_scores
│   └── policy_violations
├── Edge Functions
│   ├── process-recording/index.ts
│   ├── transcribe-audio/index.ts
│   ├── evaluate-with-llm/index.ts
│   └── calculate-scores/index.ts
├── Storage
│   └── recordings/         (Audio files)
└── RLS Policies            (Security)
3. Database Schema (ERD)
3.1 Tables
companies
id (UUID, PK)

company_name (VARCHAR)

industry (VARCHAR)

created_at (TIMESTAMP, DEFAULT NOW())

users
id (UUID, PK)

company_id (UUID, FK → companies)

email (VARCHAR, UNIQUE)

full_name (VARCHAR)

role (ENUM: admin | qa_manager | reviewer)

created_at (TIMESTAMP)

policy_templates
id (UUID, PK)

company_id (UUID, FK → companies)

template_name (VARCHAR)

description (TEXT)

is_active (BOOLEAN, DEFAULT TRUE)

created_at (TIMESTAMP)

evaluation_criteria
id (UUID, PK)

policy_template_id (UUID, FK → policy_templates)

category_name (VARCHAR)

weight (DECIMAL 5,2) — sum must equal 100 per template

passing_score (INTEGER, 0-100)

evaluation_prompt (TEXT) — LLM instruction for this criteria

created_at (TIMESTAMP)

recordings
id (UUID, PK)

company_id (UUID, FK → companies)

uploaded_by_user_id (UUID, FK → users)

file_name (VARCHAR)

file_url (TEXT) — Supabase Storage signed URL

duration_seconds (INTEGER)

status (ENUM: queued | processing | completed | failed, DEFAULT queued)

uploaded_at (TIMESTAMP, DEFAULT NOW())

processed_at (TIMESTAMP, nullable)

transcripts
id (UUID, PK)

recording_id (UUID, FK → recordings, UNIQUE 1:1)

transcript_text (TEXT)

diarized_segments (JSONB) — [{speaker: "agent"|"customer", text: "", timestamp: 0.0}, ...]

transcription_confidence (DECIMAL 5,2)

created_at (TIMESTAMP)

evaluations
id (UUID, PK)

recording_id (UUID, FK → recordings, UNIQUE 1:1)

policy_template_id (UUID, FK → policy_templates)

evaluated_by_user_id (UUID, FK → users)

overall_score (INTEGER, 0-100)

resolution_detected (BOOLEAN)

resolution_confidence (DECIMAL 3,2, 0.00-1.00)

llm_analysis (JSONB) — Full LLM response

status (ENUM: pending | completed | reviewed, DEFAULT pending)

created_at (TIMESTAMP)

category_scores
id (UUID, PK)

evaluation_id (UUID, FK → evaluations)

category_name (VARCHAR)

score (INTEGER, 0-100)

feedback (TEXT)

policy_violations
id (UUID, PK)

evaluation_id (UUID, FK → evaluations)

criteria_id (UUID, FK → evaluation_criteria)

violation_type (VARCHAR)

description (TEXT)

severity (ENUM: critical | major | minor)

3.2 Key Relationships
text
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
3.3 RLS Policies
sql
-- Users see only their company's data
CREATE POLICY "Users see own company data"
ON companies FOR SELECT
USING (id = auth.jwt() ->> 'company_id');

-- Users can only view/upload recordings for their company
CREATE POLICY "Users see own company recordings"
ON recordings FOR SELECT
USING (company_id = auth.jwt() ->> 'company_id');

-- Only admins can delete recordings
CREATE POLICY "Only admins can delete recordings"
ON recordings FOR DELETE
USING (
  company_id = auth.jwt() ->> 'company_id'
  AND (auth.jwt() ->> 'role') = 'admin'
);

-- QA managers can manage policy templates
CREATE POLICY "QA managers manage templates"
ON policy_templates FOR UPDATE
USING (
  company_id = auth.jwt() ->> 'company_id'
  AND auth.jwt() ->> 'role' IN ('admin', 'qa_manager')
);
4. Development Timeline
Week 1-2: Setup & Foundation
 Initialize Supabase project

 Create all database migrations (9 tables)

 Set up Row Level Security policies

 Initialize React + TypeScript + Vite project

 Install shadcn/ui, configure Tailwind

 Generate TypeScript types from Supabase schema

 Create Supabase client configuration

Deliverable: Working frontend shell, database ready

Week 3-4: Upload & Storage
 Build file upload component (drag-drop)

 Implement Supabase Storage integration

 Create recordings list view with real-time status

 Add status badges and filtering

 Build authentication flow (signup, login, logout)

 Implement user roles and basic authorization

Deliverable: Users can upload files, see them in dashboard

Week 5-6: Processing Pipeline
 Build Edge Function: transcribe-audio (Deepgram API)

 Build Edge Function: evaluate-with-llm (Gemini/Claude API)

 Build Edge Function: calculate-scores (rules engine)

 Build main orchestrator: process-recording

 Implement retry logic and error handling

 Test end-to-end with sample audio files

Deliverable: Recordings process through pipeline, results stored in DB

Week 7-8: Results & Policy Management
 Build evaluation results viewer

 Show transcript with speaker attribution

 Display category scores breakdown

 Show policy violations with severity

 Create policy template editor UI

 Implement evaluation criteria CRUD

 Add CSV export functionality

 Polish UI/UX

Deliverable: Production-ready MVP

Ongoing: Testing & Deployment
 Write integration tests

 Conduct user testing with QA managers

 Set up monitoring/logging

 Deploy frontend to Vercel/Netlify

 Deploy backend (Supabase hosted)

 Create documentation

Total: 8 weeks to production MVP

5. Setup & Installation
Prerequisites
Node.js 18+

Supabase account (free tier acceptable for MVP)

Deepgram API key

AssemblyAI API key

Google Gemini API key or Claude API key

Git

Local Development Setup
1. Clone Repository & Install Dependencies
bash
git clone <your-repo-url>
cd ai-qa-mvp

# Backend setup (Supabase)
npm install -g supabase
supabase init

# Frontend setup
npm install
npm install @supabase/supabase-js zustand react-dropzone shadcn-ui
2. Create Supabase Project
bash
# Sign up at supabase.com
supabase projects create --name "AI-QA-MVP"

# Link local project
supabase link --project-id <your-project-id>
3. Set Environment Variables
bash
# .env.local
VITE_SUPABASE_URL=<your-supabase-url>
VITE_SUPABASE_ANON_KEY=<your-supabase-anon-key>
VITE_DEEPGRAM_API_KEY=<your-deepgram-key>
VITE_ASSEMBLYAI_API_KEY=<your-assemblyai-key>
VITE_GEMINI_API_KEY=<your-gemini-key>
4. Run Database Migrations
bash
# Create tables
supabase db push

# Run migrations
supabase migration list
5. Start Development Servers
bash
# Terminal 1: Supabase local
supabase start

# Terminal 2: React dev server
npm run dev
Visit: http://localhost:5173

6. Generate TypeScript Types from Supabase
bash
supabase gen types typescript --project-id <your-project-id> > src/lib/types.ts
6. API Reference
Supabase Edge Functions
POST /process-recording
Triggered automatically when file uploaded to Supabase Storage.

Input:

json
{
  "recording_id": "uuid",
  "file_url": "https://...",
  "company_id": "uuid",
  "policy_template_id": "uuid"
}
Steps:

Update recording status to "processing"

Call Deepgram transcription API

Call AssemblyAI diarization API

Call Gemini/Claude with company policy context

Apply scoring rules

Save evaluation results

Update recording status to "completed"

Send Realtime notification

Output:

json
{
  "success": true,
  "evaluation_id": "uuid",
  "overall_score": 87,
  "resolution_detected": true
}
Frontend API Calls
Upload Recording
typescript
const { data, error } = await supabase.storage
  .from('recordings')
  .upload(`${companyId}/${Date.now()}_${filename}`, file)
Fetch Recordings
typescript
const { data } = await supabase
  .from('recordings')
  .select('*, evaluations(*)')
  .eq('company_id', companyId)
Subscribe to Status Updates
typescript
const subscription = supabase
  .channel('recordings')
  .on('postgres_changes',
    { event: 'UPDATE', schema: 'public', table: 'recordings' },
    (payload) => console.log(payload)
  )
  .subscribe()
7. Deployment
Frontend Deployment (Vercel)
bash
# Connect GitHub repo to Vercel
# Environment variables:
# - VITE_SUPABASE_URL
# - VITE_SUPABASE_ANON_KEY
# - VITE_DEEPGRAM_API_KEY
# - etc.

npm run build
vercel deploy
Backend Deployment (Supabase)
bash
# Deploy Edge Functions
supabase functions deploy process-recording
supabase functions deploy transcribe-audio
supabase functions deploy evaluate-with-llm
supabase functions deploy calculate-scores

# Database migrations (auto-synced with Supabase project)
supabase db push
Production Checklist
 Enable Row Level Security on all tables

 Configure API rate limits

 Set up monitoring/logging

 Enable backup/recovery

 Configure CORS properly

 Set up SSL certificates

 Test with real audio files

 Load test with 100+ concurrent uploads

 Document API endpoints

 Set up CI/CD pipeline

 Create runbook for common issues

8. Future Expansion
Tier 1: Beyond Call Centers (Year 1-2)
Sales Teams: Win/loss analysis, deal risk detection

Insurance Claims: Fraud detection, claim adjuster QA

Financial Services: Compliance monitoring (SEC, FINRA, TCPA)

Tier 2: High-Value Verticals (Year 2-3)
Healthcare: HIPAA compliance, telemedicine QA

Legal: Deposition analysis, client consultation review

Recruitment: Interview bias reduction, candidate scoring

Tier 3: Emerging Markets (Year 3+)
Market Research: Focus group analysis, theme detection

Government: Citizen service QA, 311 hotline monitoring

Education: Student advisory consultation QA

Feature Enhancements
 Real-time agent coaching during calls

 Multi-language support (Whisper multilingual)

 Advanced analytics dashboard

 Custom branding/white-labeling

 API for third-party integrations

 Advanced reporting (PDF, executive summaries)

 Mobile app (iOS/Android)

 Advanced conversation insights (emotion detection, topic modeling)

 Predictive coaching (pre-call recommendations)

Contributing
To contribute to this project:

Create a feature branch: git checkout -b feature/your-feature

Make changes and test locally

Commit with clear messages: git commit -m "Add feature"

Push to branch: git push origin feature/your-feature

Create Pull Request

License
This project is proprietary. Unauthorized use is prohibited.

Support
For issues or questions:

Create an issue in GitHub

Email: support@yourcompany.com

Documentation: [link to docs]

Roadmap
Q4 2025: MVP Launch (Call Centers)
Q1 2026: Sales Team Features, Insurance Integrations
Q2 2026: Healthcare HIPAA Certification
Q3 2026: Legal Services, Recruitment Features
Q4 2026+: Market Research, Government, Education

Authors
Your Name (@github)

Team Members

Last Updated: November 8, 2025
Version: 0.1.0-MVP