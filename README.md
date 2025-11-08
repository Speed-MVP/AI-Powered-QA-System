# AI-Powered Batch QA System MVP

## Project Overview

An AI-powered call center quality assurance platform that enables companies to upload pre-recorded call audio, automatically transcribe and evaluate them using LLM-based intelligence (Gemini, Claude), and generate accurate quality scores based on company-specific policies and evaluation criteria.

**Core Value Proposition:**
- Upload call recordings → AI evaluates using custom company policies (not generic keywords) → Get comprehensive QA results in minutes
- **90-97% cost reduction** vs manual QA ($0.50-2 per call vs $15-25)
- **100% call coverage** instead of 1-3% sampling
- **85-92% accuracy** on problem resolution detection
- **2X better** than keyword-based systems through contextual LLM evaluation

**Tech Stack:** FastAPI (backend) + React TypeScript (frontend) + GCP Cloud Storage + Neon PostgreSQL + Deepgram (transcription) + Gemini/Claude (LLM evaluation)

---

## Table of Contents

- [1. Product Requirements](#1-product-requirements)
- [2. Architecture](#2-architecture)
- [3. Database Schema (ERD)](#3-database-schema-erd)
- [4. Development Timeline](#4-development-timeline)
- [5. Setup & Installation](#5-setup--installation)
- [6. API Reference](#6-api-reference)
- [7. Deployment](#7-deployment)
- [8. Future Expansion](#8-future-expansion)

---

## 1. Product Requirements

### 1.1 Functional Requirements

#### Authentication & User Management
- Users can sign up, log in, reset password via Auth0, Clerk, or custom JWT authentication
- Roles: `admin` (full access), `qa_manager` (manage templates, view results), `reviewer` (view results only)
- Multi-tenant: Users associated with a company; application-level middleware enforces data isolation
- Email verification for new accounts

#### Recording Upload
- **File Upload Interface:**
  - Drag-and-drop or browse file selector
  - Supported formats: MP3, WAV, M4A, MP4 (audio extracted)
  - Batch upload: 1-100+ files per session
  - Max file size: 2GB per file
  - Progress tracking with upload percentage

- **Storage:**
  - Files stored in **GCP Cloud Storage** (CDN-backed, secure)
  - Signed URLs for secure upload and retrieval
  - Unique job ID assigned immediately upon upload
  - Status initialized to `queued`

#### Processing Pipeline
When file is uploaded, **GCP Cloud Function or Cloud Run job** is triggered:

1. **Update Status**: Mark recording as `processing` in Neon DB
2. **Transcribe**: Call Deepgram batch API
   - Transcription confidence score recorded
   - Handles various audio qualities and accents
3. **Diarize**: Call AssemblyAI API or use Deepgram's built-in diarization
   - Separate agent speech from customer speech
   - Speaker-attributed transcript stored as JSONB
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
8. **Notify User**: Send notification via email or optional push notification

#### Dashboard & Results
- **Dashboard Page:**
  - List of uploaded files with status badges (queued, processing, completed, failed)
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

#### Policy Template & Criteria Management
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

#### Real-time Notifications & Updates
- Users can refresh dashboard to see status changes
- Optional: WebSocket or polling mechanism for live updates
- Email notification when batch completes or fails (via SendGrid, AWS SES, or SMTP)
- In-app toast notifications for errors, completions

#### Security & Privacy
- **Application-Level Security:** Middleware checks user `company_id` and role before returning data
- **Authentication:** JWT-based or session-based via Auth0, Clerk, Firebase Auth, or custom implementation
- **Encryption:** All data in transit (HTTPS) and at rest (GCP Storage encryption)
- **Audit Trail:** Log all uploads, evaluations, policy changes with user/timestamp in Neon DB
- **Signed URLs:** Temporary secure access to uploaded audio files in GCP Storage
- **Compliance:** Support for HIPAA, GDPR, compliance-focused deployments (future)

### 1.2 Non-Functional Requirements

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

## 2. Architecture

### 2.1 High-Level Data Flow

```
User Upload
    ↓
[React Frontend] --upload file--> [GCP Cloud Storage]
    ↓
[Cloud Storage Trigger / Pub/Sub]
    ↓
[Cloud Function / Cloud Run: process-recording]
    ├─ Transcribe with Deepgram
    ├─ Diarize with AssemblyAI
    ├─ Evaluate with Gemini/Claude
    ├─ Calculate Scores & Violations
    └─ Update Neon Database
    ↓
[Optional: Pusher/Socket.io/Polling for live updates]
    ↓
[Dashboard] <--refresh/poll-- [Frontend]
```

### 2.2 Tech Stack

#### Backend
- **API Framework:** FastAPI (Python 3.10+)
- **Database:** Neon (serverless PostgreSQL)
- **Storage:** GCP Cloud Storage (for audio files)
- **Compute/API:** GCP Cloud Run (containerized FastAPI app)
- **Background Jobs:** GCP Cloud Functions or Cloud Tasks for async processing
- **Authentication:** Auth0, Clerk, NextAuth (for Next.js), or custom JWT-based auth
- **ORM:** SQLAlchemy 2.0
- **Validation:** Pydantic
- **Server:** Uvicorn (ASGI)

#### Frontend
- **Framework:** React 18 + TypeScript + Vite
- **UI Components:** shadcn/ui + Tailwind CSS
- **State Management:** Zustand or React Query
- **API Client:** Axios or native fetch
- **File Upload:** react-dropzone
- **Real-time (optional):** Pusher, Socket.io, or polling
- **Build Tool:** Vite (fast dev server, optimized builds)

#### External APIs
- **Speech-to-Text:** Deepgram Nova-3 (batch API)
- **Speaker Diarization:** AssemblyAI async API or Deepgram built-in
- **LLM Evaluation:** Google Gemini 2.0 Flash API or Anthropic Claude 3.5 Sonnet
- **Email Notifications:** SendGrid, AWS SES, or SMTP via Cloud Functions

#### DevOps & CI/CD
- **Version Control:** GitHub / GitLab
- **Frontend Hosting:** Vercel, Netlify, or GCP Cloud Storage + CDN
- **Backend Hosting:** GCP Cloud Run (auto-scaling, containerized)
- **Database:** Neon (managed Postgres, serverless)
- **Secrets Management:** GCP Secret Manager
- **CI/CD:** GitHub Actions, GitLab CI, or Google Cloud Build

### 2.3 Component Architecture

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

Backend (FastAPI on Cloud Run)
├── app/
│   ├── main.py             (FastAPI entry point)
│   ├── config.py           (Environment variables)
│   ├── database.py         (Neon DB connection)
│   ├── models/             (SQLAlchemy ORM models)
│   │   ├── company.py
│   │   ├── user.py
│   │   ├── recording.py
│   │   ├── transcript.py
│   │   ├── evaluation.py
│   │   ├── category_score.py
│   │   ├── policy_template.py
│   │   ├── evaluation_criteria.py
│   │   └── policy_violation.py
│   ├── routes/             (API endpoints)
│   │   ├── auth.py         (Login, register)
│   │   ├── recordings.py   (Upload, list, get)
│   │   ├── evaluations.py  (Results)
│   │   └── templates.py    (Policy CRUD)
│   ├── services/           (Business logic)
│   │   ├── storage.py      (GCP Storage)
│   │   ├── deepgram.py     (Transcription)
│   │   ├── assemblyai.py   (Diarization)
│   │   ├── gemini.py       (LLM evaluation)
│   │   └── scoring.py      (Rules engine)
│   ├── middleware/
│   │   ├── auth.py         (JWT verification)
│   │   └── permissions.py  (Role-based access)
│   └── tasks/
│       └── process_recording.py (Background processing)
├── Dockerfile
└── requirements.txt

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

## 3. Database Schema (ERD)

### 3.1 Tables

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

### 3.2 Key Relationships

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

### 3.3 Security Considerations

**Application-Level Row Security:**
- Middleware checks `user.company_id` matches resource `company_id` before queries
- Role-based checks: only `admin` or `qa_manager` can edit policy templates

Example (FastAPI middleware):
```python
app.get('/api/recordings', authenticateUser, async (req, res) => {
  const { company_id } = req.user;
  const recordings = await db.query(
    'SELECT * FROM recordings WHERE company_id = $1',
    [company_id]
  );
  res.json(recordings);
});
```

---

## 4. Development Timeline

### Week 1-2: Setup & Foundation
- [ ] Set up GCP project (Cloud Storage, Cloud Run, Cloud Functions, IAM)
- [ ] Set up Neon database, create schema migrations
- [ ] Initialize React + TypeScript + Vite frontend
- [ ] Set up authentication (Auth0/Clerk or custom JWT)
- [ ] Configure CI/CD pipeline (GitHub Actions or Cloud Build)

**Deliverable:** Working frontend shell, database ready, auth configured

### Week 3-4: Upload & Storage
- [ ] Build file upload component (drag-drop with react-dropzone)
- [ ] Implement GCP Storage integration (signed URLs, bucket policies)
- [ ] Create recordings list view with status display
- [ ] Add status filtering and sorting
- [ ] Build authentication flow (signup, login, logout)

**Deliverable:** Users can upload files, see them in dashboard

### Week 5-6: Processing Pipeline
- [ ] Build Cloud Function for transcription (Deepgram API)
- [ ] Build Cloud Function for evaluation (Gemini/Claude API)
- [ ] Build rules engine for scoring and violations
- [ ] Implement main orchestrator function
- [ ] Add retry logic and error handling
- [ ] Test end-to-end with sample audio files

**Deliverable:** Recordings process through pipeline, results stored in DB

### Week 7-8: Results & Policy Management
- [ ] Build evaluation results viewer
- [ ] Show transcript with speaker attribution
- [ ] Display category scores breakdown
- [ ] Show policy violations with severity
- [ ] Create policy template editor UI
- [ ] Implement evaluation criteria CRUD
- [ ] Add CSV export functionality
- [ ] Polish UI/UX

**Deliverable:** Production-ready MVP

### Ongoing: Testing & Deployment
- [ ] Write integration tests
- [ ] Conduct user testing with QA managers
- [ ] Set up monitoring/logging (Cloud Logging, Sentry)
- [ ] Deploy frontend to Vercel/Netlify
- [ ] Deploy backend to Cloud Run
- [ ] Create user documentation

**Total: 8 weeks to production MVP**

---

## 5. Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL client tools
- Google Cloud SDK
- Docker (for containerization)

### Backend Setup (FastAPI)

#### Step 1: Clone & Create Virtual Environment
```bash
git clone <repo-url>
cd ai-qa-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

#### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
aiohttp==3.9.1
requests==2.31.0
google-cloud-storage==2.10.0
openai==1.3.6
anthropic==0.7.1
email-validator==2.1.0
```

#### Step 3: Set Environment Variables
```bash
# .env
DATABASE_URL=postgresql://user:password@ep-xyz.neon.tech/dbname

# GCP
GCP_PROJECT_ID=my-project-123
GCP_BUCKET_NAME=ai-qa-recordings
GCP_CREDENTIALS_PATH=/path/to/service-account.json

# JWT
JWT_SECRET=your-super-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# APIs
DEEPGRAM_API_KEY=xyz...
GEMINI_API_KEY=xyz...

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=app-password

# Server
ENVIRONMENT=development
LOG_LEVEL=INFO
```

#### Step 4: Run Database Migrations
```bash
alembic upgrade head
```

#### Step 5: Start Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit: http://localhost:8000/docs (Swagger UI)

### Frontend Setup (React + TypeScript)

#### Step 1: Initialize Project
```bash
cd ai-qa-frontend
npm install
```

#### Step 2: Set Environment Variables
```bash
# .env.local
VITE_API_URL=http://localhost:8000
VITE_DEEPGRAM_API_KEY=<your-deepgram-key>
```

#### Step 3: Start Development Server
```bash
npm run dev
```

Visit: http://localhost:5173

---

## 6. API Reference

### Authentication

```
POST   /api/auth/login           → Get JWT token
GET    /api/auth/me              → Get current user
```

### Recordings

```
POST   /api/recordings/signed-url    → Get GCP signed upload URL
POST   /api/recordings/upload        → Create recording entry
GET    /api/recordings/list          → List all company recordings
GET    /api/recordings/{id}          → Get specific recording status
```

### Evaluations

```
GET    /api/evaluations/{recording_id}    → Get evaluation results
GET    /api/evaluations/{id}/scores       → Get category scores
GET    /api/evaluations/{id}/violations   → Get policy violations
```

### Policy Templates

```
POST   /api/templates              → Create new template
GET    /api/templates              → List company templates
PUT    /api/templates/{id}         → Update template
DELETE /api/templates/{id}         → Delete template
POST   /api/templates/{id}/criteria   → Add criteria
```

---

## 7. Deployment

### Frontend Deployment (Vercel)

```bash
# Connect GitHub repo to Vercel
# Environment variables:
# - VITE_API_URL
# - (other frontend vars)

npm run build
vercel deploy
```

### Backend Deployment (Cloud Run)

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose port
EXPOSE 8080

# Run server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

#### Deploy to Cloud Run
```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/api:latest

# Deploy
gcloud run deploy api \
  --image gcr.io/PROJECT_ID/api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=$DATABASE_URL,GCP_PROJECT_ID=$GCP_PROJECT_ID
```

### Production Checklist
- [ ] Configure application-level security middleware
- [ ] Configure API rate limits
- [ ] Set up monitoring/logging (Cloud Logging, Sentry)
- [ ] Enable backup/recovery for Neon DB
- [ ] Configure CORS properly
- [ ] Set up SSL certificates (automatic with Cloud Run)
- [ ] Test with real audio files
- [ ] Load test with 100+ concurrent uploads
- [ ] Document API endpoints
- [ ] Set up CI/CD pipeline
- [ ] Create runbook for common issues

---

## 8. Future Expansion

### Tier 1: Beyond Call Centers (Year 1-2)
- **Sales Teams:** Win/loss analysis, deal risk detection
- **Insurance Claims:** Fraud detection, claim adjuster QA
- **Financial Services:** Compliance monitoring (SEC, FINRA, TCPA)

### Tier 2: High-Value Verticals (Year 2-3)
- **Healthcare:** HIPAA compliance, telemedicine QA
- **Legal:** Deposition analysis, client consultation review
- **Recruitment:** Interview bias reduction, candidate scoring

### Tier 3: Emerging Markets (Year 3+)
- **Market Research:** Focus group analysis, theme detection
- **Government:** Citizen service QA, 311 hotline monitoring
- **Education:** Student advisory consultation QA

### Feature Enhancements
- [ ] Real-time agent coaching during calls
- [ ] Multi-language support (Whisper multilingual)
- [ ] Advanced analytics dashboard
- [ ] Custom branding/white-labeling
- [ ] API for third-party integrations
- [ ] Advanced reporting (PDF, executive summaries)
- [ ] Mobile app (iOS/Android)
- [ ] Advanced conversation insights (emotion detection, topic modeling)
- [ ] Predictive coaching (pre-call recommendations)

---

## Contributing

To contribute to this project:

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and test locally
3. Commit with clear messages: `git commit -m "Add feature"`
4. Push to branch: `git push origin feature/your-feature`
5. Create Pull Request

---

## License

This project is proprietary. Unauthorized use is prohibited.

---

## Support

For issues or questions:
- Create an issue in GitHub
- Email: support@yourcompany.com
- Documentation: [link to docs]

---

## Roadmap

- **Q4 2025:** MVP Launch (Call Centers)
- **Q1 2026:** Sales Team Features, Insurance Integrations
- **Q2 2026:** Healthcare HIPAA Certification
- **Q3 2026:** Legal Services, Recruitment Features
- **Q4 2026+:** Market Research, Government, Education

---

## Authors

- Your Name (@github)
- Team Members

---

**Last Updated:** November 8, 2025  
**Version:** 0.2.0-MVP (FastAPI + GCP + Neon)
