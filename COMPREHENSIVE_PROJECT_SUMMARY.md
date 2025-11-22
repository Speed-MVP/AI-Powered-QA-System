# AI-Powered QA System - Comprehensive Project Summary

## Table of Contents
1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Technology Stack](#technology-stack)
4. [Complete System Flow](#complete-system-flow)
5. [Backend Architecture](#backend-architecture)
6. [Frontend Architecture](#frontend-architecture)
7. [Database Schema](#database-schema)
8. [Evaluation Pipeline](#evaluation-pipeline)
9. [Policy Rules System](#policy-rules-system)
10. [Features & Capabilities](#features--capabilities)
11. [API Endpoints](#api-endpoints)
12. [User Workflows](#user-workflows)
13. [Deployment & Infrastructure](#deployment--infrastructure)

---

## Overview

### TL;DR
End-to-end FastAPI + React platform that ingests call recordings, runs AI-driven QA scoring, and routes low-confidence cases for human review. The system provides automated quality assurance evaluation for call centers using structured policy rules, LLM-based evaluation, deterministic rule engines, and human-in-the-loop review workflows.

### Core Value Proposition
- **90-97% cost reduction** vs manual QA ($0.50-2 per call vs $15-25)
- **100% call coverage** instead of 1-3% sampling
- **85-92% accuracy** on problem resolution detection
- **2X better** than keyword-based systems through contextual LLM evaluation
- **Automated policy compliance** via structured rule engine
- **Confidence-based routing** to human reviewers for edge cases
- **Continuous learning** from human feedback

### Key Differentiators
1. **Structured Policy Rules System**: Machine-readable, versioned rules that can be auto-generated from policy text or manually crafted
2. **Hybrid Evaluation**: Combines deterministic rule engine (pre-scoring) with LLM-based contextual evaluation
3. **Confidence-Based Routing**: Automatically flags low-confidence evaluations for human review
4. **Reproducibility**: Full audit trail with prompt versions, model metadata, and evaluation seeds
5. **Voice-First Analytics**: Deepgram transcription with diarization, sentiment analysis, and speaker identification

---

## Project Structure

### Backend (`backend/`)
```
backend/
├── app/
│   ├── main.py                 # FastAPI entry point, middleware, routers
│   ├── config.py               # Environment settings (pydantic-settings)
│   ├── database.py             # SQLAlchemy setup, session management
│   ├── middleware/
│   │   ├── auth.py             # JWT token validation
│   │   └── permissions.py      # Role-based access control
│   ├── models/                 # SQLAlchemy ORM models (24 models)
│   │   ├── company.py
│   │   ├── user.py
│   │   ├── recording.py
│   │   ├── transcript.py
│   │   ├── evaluation.py
│   │   ├── category_score.py
│   │   ├── policy_template.py
│   │   ├── evaluation_criteria.py
│   │   ├── evaluation_rubric_level.py
│   │   ├── policy_violation.py
│   │   ├── human_review.py
│   │   ├── team.py
│   │   ├── agent_team.py
│   │   ├── audit.py            # AuditLog, EvaluationVersion, ComplianceReport
│   │   ├── policy_rules_*.py   # Rule versioning, drafts, audit logs
│   │   ├── rule_engine_results.py
│   │   └── import_job.py
│   ├── routes/                 # API endpoints (14 routers)
│   │   ├── auth.py             # Login, current user
│   │   ├── recordings.py       # Upload, list, re-evaluate, download
│   │   ├── evaluations.py      # Get evaluation, transcript, violations
│   │   ├── templates.py        # Policy template CRUD
│   │   ├── policy_rules.py     # Rule generation, versioning
│   │   ├── rule_editor.py      # Rule editing endpoints
│   │   ├── batch_processing.py # Queue management
│   │   ├── fine_tuning.py      # Human review data
│   │   ├── human_reviews.py    # Human review queue
│   │   ├── supervisor.py       # Supervisor dashboard
│   │   ├── teams.py            # Team management
│   │   ├── agents.py           # Agent management
│   │   ├── imports.py          # CSV bulk imports
│   │   └── health.py           # Health check
│   ├── services/               # Business logic (33 services)
│   │   ├── deepgram.py         # Transcription + diarization + sentiment
│   │   ├── gemini.py           # LLM evaluation (legacy)
│   │   ├── deterministic_llm_evaluator.py  # Phase 4: Structured rule-based LLM eval
│   │   ├── rule_engine.py      # Legacy rule engine
│   │   ├── rule_engine_v2.py   # Phase 3: Structured policy rules engine
│   │   ├── rule_engine_v2_deterministic.py  # Deterministic rule evaluation
│   │   ├── scoring.py          # Score calculation, ensemble merging
│   │   ├── deterministic_scorer.py  # Phase 4: Deterministic scoring
│   │   ├── confidence.py       # Confidence calculation (legacy)
│   │   ├── confidence_engine.py  # Phase 2: 5-signal confidence scoring
│   │   ├── audit.py            # Audit logging, versioning
│   │   ├── batch_processing.py # Queue orchestration
│   │   ├── storage.py          # GCP Storage integration
│   │   ├── email.py            # Email notifications
│   │   ├── rag.py              # Retrieval Augmented Generation
│   │   ├── csv_import_service.py  # Bulk agent/team imports
│   │   ├── fine_tuning.py      # Human review lifecycle
│   │   ├── continuous_learning.py  # Model feedback loops
│   │   ├── policy_rule_builder.py  # AI rule generation
│   │   ├── policy_rules_validator.py  # Rule validation
│   │   ├── policy_rules_versioning.py  # Rule versioning
│   │   ├── policy_rules_sandbox.py  # Rule testing sandbox
│   │   ├── transcript_normalizer.py  # Transcript preprocessing
│   │   ├── transcript_compressor.py  # Transcript summarization
│   │   ├── schema_validator.py  # LLM response validation
│   │   ├── processing_tracer.py  # Processing event tracking
│   │   ├── dataset_curation.py  # Fine-tuning dataset management
│   │   └── template_seeder.py  # Template seeding utilities
│   ├── schemas/                # Pydantic request/response models
│   │   ├── user.py
│   │   ├── recording.py
│   │   ├── evaluation.py
│   │   ├── policy_template.py
│   │   ├── policy_rules.py     # Policy rules JSON schema
│   │   └── ...
│   ├── tasks/                  # Background processing
│   │   ├── process_recording.py  # Main evaluation orchestration
│   │   └── generate_policy_rules_job.py  # Async rule generation
│   ├── tests/                  # Test suites
│   │   ├── test_deterministic_scorer.py
│   │   ├── test_policy_rule_builder.py
│   │   ├── test_policy_rules_sandbox.py
│   │   ├── test_policy_rules_validator.py
│   │   ├── test_policy_rules_versioning.py
│   │   └── test_rule_engine_v2*.py
│   └── utils/
│       ├── errors.py           # Custom exceptions
│       ├── logger.py           # Logging utilities
│       └── validators.py       # Validation helpers
├── migrations/                 # Alembic migrations (16 versions)
│   └── versions/
├── Dockerfile                  # Container image
├── docker-compose.yml          # Local development
├── cloudbuild.yaml             # GCP Cloud Build
├── deploy.sh                   # Deployment script
├── requirements.txt            # Python dependencies
└── docs/
    └── AUTO_RULE_GENERATION.md  # Rule generation documentation
```

### Frontend (`web/`)
```
web/
├── src/
│   ├── main.tsx                # React entry point
│   ├── App.tsx                 # Routing configuration
│   ├── index.css               # Global styles
│   ├── pages/                  # Route components (17 pages)
│   │   ├── Home.tsx            # Landing page
│   │   ├── Features.tsx        # Feature showcase
│   │   ├── Pricing.tsx         # Pricing page
│   │   ├── FAQ.tsx             # FAQ page
│   │   ├── SignIn.tsx          # Authentication
│   │   ├── Dashboard.tsx       # Recordings list
│   │   ├── Upload.tsx          # File upload interface
│   │   ├── Results.tsx         # Evaluation results viewer
│   │   ├── PolicyTemplates.tsx # Template management
│   │   ├── RuleEditor.tsx      # Structured rule editor (Phase 5)
│   │   ├── RuleHistory.tsx     # Rule version history
│   │   ├── HumanReview.tsx     # Human review queue
│   │   ├── SupervisorDashboard.tsx  # Supervisor oversight
│   │   ├── TeamsListPage.tsx   # Team management
│   │   ├── AgentsListPage.tsx  # Agent management
│   │   └── AuditTrailPage.tsx  # Audit log viewer
│   ├── components/             # Reusable components
│   │   ├── Layout.tsx          # Main layout wrapper
│   │   ├── Footer.tsx
│   │   ├── FloatingButtons.tsx
│   │   ├── SupportChat.tsx
│   │   ├── LazySection.tsx
│   │   ├── RuleWizard.tsx      # Rule creation wizard
│   │   ├── RuleSandbox.tsx     # Rule testing sandbox
│   │   └── modals/
│   │       ├── TeamFormModal.tsx
│   │       ├── AgentFormModal.tsx
│   │       └── BulkImportModal.tsx
│   ├── contexts/
│   │   └── AuthContext.tsx     # Authentication state
│   ├── hooks/
│   │   └── useSEO.ts           # SEO metadata management
│   ├── lib/
│   │   └── api.ts              # API client (centralized)
│   └── store/                  # Zustand state stores
│       ├── policyStore.ts
│       └── themeStore.ts
├── public/                     # Static assets
├── tailwind.config.js          # Tailwind configuration
├── vite.config.ts              # Vite build configuration
├── tsconfig.json               # TypeScript configuration
└── package.json                # Dependencies
```

---

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104+ (Python 3.10+)
- **Database**: Neon PostgreSQL (serverless) via SQLAlchemy 2.0
- **Storage**: GCP Cloud Storage (audio files)
- **Compute**: GCP Cloud Run (containerized)
- **Transcription**: Deepgram Nova-2 API (diarization, sentiment)
- **LLM**: Google Gemini 2.0 Flash/Pro (hybrid model routing)
- **ORM**: SQLAlchemy 2.0 with Alembic migrations
- **Validation**: Pydantic 2.5+
- **Auth**: JWT (python-jose)
- **Email**: SMTP (SendGrid/AWS SES compatible)
- **Background Jobs**: Thread-based executors (future: Cloud Tasks/PubSub)

### Frontend
- **Framework**: React 19 + TypeScript 5.9
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS
- **Routing**: React Router v7
- **State Management**: Zustand
- **Icons**: lucide-react, react-icons
- **File Upload**: react-dropzone
- **Hosting**: Vercel

### Infrastructure
- **Version Control**: Git
- **CI/CD**: GitHub Actions / GCP Cloud Build
- **Monitoring**: Cloud Logging
- **Secrets**: GCP Secret Manager (recommended)

---

## Complete System Flow

### End-to-End Recording Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER UPLOAD                                                  │
│    Frontend (Upload.tsx)                                        │
│    ├─ Drag-drop or file picker                                 │
│    ├─ Validates file type/size (max 2GB)                       │
│    └─ POST /api/recordings/upload-direct                        │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. STORAGE & RECORD CREATION                                    │
│    Backend (routes/recordings.py)                               │
│    ├─ Upload to GCP Cloud Storage (bucket/company_id/file)     │
│    ├─ Create Recording record (status: queued)                 │
│    └─ Trigger background task (process_recording_task)         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. BACKGROUND PROCESSING                                        │
│    Task: process_recording_task(recording_id)                   │
│    Status: queued → processing                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. TRANSCRIPTION                                                │
│    Service: DeepgramService.transcribe()                        │
│    ├─ Deepgram Nova-2 API call                                 │
│    ├─ Diarization (agent/caller separation)                    │
│    ├─ Sentiment analysis (per segment)                         │
│    ├─ Utterance-level timestamps                               │
│    └─ Speaker role identification                              │
│    Output:                                                      │
│    - transcript_text (normalized)                              │
│    - diarized_segments (JSONB)                                 │
│    - sentiment_analysis (JSONB)                                │
│    - transcription_confidence                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. TRANSCRIPT NORMALIZATION                                     │
│    Service: TranscriptNormalizer.normalize_transcript()         │
│    ├─ Text cleaning                                             │
│    ├─ Speaker attribution refinement                           │
│    └─ Quality metrics calculation                              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. POLICY TEMPLATE SELECTION                                    │
│    Fetch active PolicyTemplate for company                      │
│    ├─ EvaluationCriteria (categories)                          │
│    ├─ EvaluationRubricLevel (scoring levels)                   │
│    └─ PolicyRules (structured rules, if enabled)               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. DETERMINISTIC RULE ENGINE                                    │
│    Service: RuleEngineV2.evaluate_rules()                       │
│    (if enable_structured_rules = True)                          │
│    OR: RuleEngineService.evaluate_rules() (legacy)             │
│                                                                 │
│    Rule Types Evaluated:                                        │
│    ├─ Boolean rules (required/forbidden behaviors)             │
│    ├─ Numeric rules (timing thresholds)                        │
│    ├─ Phrase rules (required/forbidden phrases)                │
│    ├─ Conditional rules (if-then logic)                        │
│    ├─ Multi-step rules (sequence verification)                 │
│    ├─ Tone-based rules (sentiment requirements)                │
│    └─ Resolution rules (issue resolution detection)            │
│                                                                 │
│    Output: Rule results by category with severity              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. LLM EVALUATION                                               │
│    Service: DeterministicLLMEvaluator.evaluate_recording()      │
│    (if enable_structured_rules = True)                          │
│    OR: GeminiService.evaluate() (legacy)                       │
│                                                                 │
│    Process:                                                     │
│    ├─ Transcript compression (if needed)                       │
│    ├─ Build evaluation prompt:                                │
│    │   ├─ Policy rules results (pre-populated)                │
│    │   ├─ Categories & rubric levels                          │
│    │   ├─ Transcript summary                                  │
│    │   └─ Tone flags                                          │
│    ├─ Model selection (Flash vs Pro based on complexity)      │
│    ├─ LLM API call (Gemini 2.0)                               │
│    ├─ JSON response parsing                                   │
│    └─ Critical rule overrides (fail-safe)                     │
│                                                                 │
│    Output:                                                     │
│    - Category rubric level assignments                        │
│    - Violations detected                                      │
│    - Resolution status                                        │
│    - Tone analysis                                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. SCORING & ENSEMBLE                                           │
│    Service: ScoringService / DeterministicScorer                │
│    ├─ Map rubric levels to numeric scores                      │
│    ├─ Apply rule penalties                                     │
│    ├─ Calculate weighted category scores                       │
│    ├─ Compute overall score                                    │
│    └─ Aggregate violations                                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 10. CONFIDENCE CALCULATION                                      │
│     Service: ConfidenceEngine.compute_confidence_score()        │
│     5-Signal Confidence Model:                                  │
│     ├─ Transcript quality (Deepgram confidence)                │
│     ├─ LLM response consistency                                │
│     ├─ Rule engine hits                                        │
│     ├─ Category score distribution                             │
│     └─ Schema validation                                       │
│                                                                 │
│     Output: confidence_score (0-1), requires_human_review      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 11. PERSISTENCE                                                 │
│     Save to database:                                           │
│     ├─ Transcript (with normalized text)                       │
│     ├─ Evaluation (scores, confidence, metadata)               │
│     ├─ CategoryScore (per criterion)                           │
│     ├─ PolicyViolation (violations by category)                │
│     ├─ RuleEngineResults (rule evaluation output)              │
│     ├─ HumanReview (if requires_human_review = True)           │
│     └─ AuditLog (evaluation_created event)                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 12. NOTIFICATION & FINALIZATION                                 │
│     ├─ Update Recording status: completed                       │
│     ├─ Send email notification (success/failure)               │
│     └─ Audit trail snapshot created                            │
└─────────────────────────────────────────────────────────────────┘
```

### Human Review Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Human Review Triggered (requires_human_review = True)           │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ HumanReview Record Created                                      │
│ Status: pending                                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Reviewer Views Queue (HumanReview.tsx)                          │
│ GET /api/human_reviews/pending                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Reviewer Opens Evaluation                                       │
│ GET /api/evaluations/{id}/with-template                         │
│ Shows: AI scores, transcript, rubric, violations               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Reviewer Corrects Scores                                        │
│ POST /api/fine-tuning/human-reviews/{id}/submit                 │
│ ├─ Human category scores                                        │
│ ├─ Human overall score                                          │
│ ├─ Reviewer notes                                               │
│ └─ AI accuracy rating                                           │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Update & Archive                                                │
│ ├─ HumanReview status: completed                                │
│ ├─ Evaluation status: reviewed                                  │
│ ├─ Fine-tuning dataset entry created                            │
│ └─ Audit log updated                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Backend Architecture

### API Structure (FastAPI Routers)

#### Authentication (`/api/auth`)
- `POST /login` - User authentication, returns JWT
- `GET /me` - Get current user profile

#### Recordings (`/api/recordings`)
- `POST /signed-url` - Get GCP signed upload URL
- `POST /upload-direct` - Upload file directly through backend
- `GET /list` - List recordings (company-scoped, filtered)
- `GET /{id}` - Get recording details
- `POST /{id}/reevaluate` - Requeue for re-evaluation
- `GET /{id}/download` - Get signed download URL
- `DELETE /{id}` - Delete recording

#### Evaluations (`/api/evaluations`)
- `GET /{recording_id}` - Get evaluation results
- `GET /{recording_id}/transcript` - Get transcript
- `GET /{evaluation_id}/with-template` - Get evaluation with template context
- `GET /{recording_id}/violations` - Get policy violations
- `GET /supervisor/view` - Supervisor dashboard data

#### Policy Templates (`/api/templates`)
- `GET /` - List templates (company-scoped)
- `POST /` - Create template
- `GET /{id}` - Get template details
- `PUT /{id}` - Update template
- `DELETE /{id}` - Delete template
- `POST /{id}/criteria` - Add evaluation criteria
- `PUT /{id}/criteria/{criteria_id}` - Update criteria
- `DELETE /{id}/criteria/{criteria_id}` - Delete criteria
- `POST /{id}/rubric-levels` - Add rubric level
- `PUT /{id}/rubric-levels/{level_id}` - Update rubric level

#### Policy Rules (`/api/policy-templates`)
- `POST /{id}/rules/generate` - AI-generate rules from policy text
- `GET /{id}/rules` - Get structured rules
- `PUT /{id}/rules` - Update rules
- `POST /{id}/rules/draft` - Save draft rules
- `POST /{id}/rules/publish` - Publish rules version
- `GET /{id}/rules/history` - Get rule version history
- `POST /{id}/rules/sandbox` - Test rules against sample transcript

#### Rule Editor (`/api/policy-templates/{id}/rules/editor`)
- Rule CRUD operations
- Rule validation
- Category management

#### Batch Processing (`/api/batch`)
- `POST /start` - Start batch processing queue
- `POST /stop` - Stop batch processing
- `GET /status` - Get queue status
- `POST /queue` - Queue recordings for processing
- `POST /priority-batch` - Process high-priority batch

#### Human Reviews (`/api/human_reviews`)
- `GET /pending` - Get pending reviews
- `GET /{id}` - Get review details
- `POST /{id}/assign` - Assign reviewer
- `POST /{id}/submit` - Submit human review

#### Fine-Tuning (`/api/fine-tuning`)
- `GET /human-reviews/queue` - Get review queue
- `POST /human-reviews/{id}/submit` - Submit corrections
- `GET /dataset` - Get fine-tuning dataset

#### Teams (`/api/teams`)
- CRUD operations for teams

#### Agents (`/api/agents`)
- CRUD operations for agents
- Team assignment

#### Imports (`/api/imports`)
- `POST /agents` - Bulk import agents (CSV)
- `POST /teams` - Bulk import teams (CSV)
- `GET /{job_id}` - Get import job status

#### Supervisor (`/api/supervisor`)
- Dashboard endpoints for supervisor oversight

#### Health (`/health`)
- `GET /` - Health check

### Service Layer

#### Core Processing Services
1. **DeepgramService** - Transcription, diarization, sentiment
2. **GeminiService** - Legacy LLM evaluation
3. **DeterministicLLMEvaluator** - Phase 4: Rule-guided LLM evaluation
4. **RuleEngineService** - Legacy rule engine
5. **RuleEngineV2** - Phase 3: Structured policy rules engine
6. **RuleEngineV2Deterministic** - Deterministic rule evaluation
7. **ScoringService** - Score calculation
8. **DeterministicScorer** - Phase 4: Deterministic scoring
9. **ConfidenceService** - Legacy confidence calculation
10. **ConfidenceEngine** - Phase 2: 5-signal confidence model

#### Supporting Services
11. **AuditService** - Audit logging, versioning
12. **BatchProcessingService** - Queue orchestration
13. **StorageService** - GCP Storage integration
14. **EmailService** - Email notifications
15. **RAGService** - Retrieval Augmented Generation
16. **CSVImportService** - Bulk data imports
17. **FineTuningService** - Human review lifecycle
18. **ContinuousLearningService** - Model feedback loops
19. **PolicyRuleBuilder** - AI rule generation
20. **PolicyRulesValidator** - Rule validation
21. **PolicyRulesVersioning** - Rule version management
22. **PolicyRulesSandbox** - Rule testing environment
23. **TranscriptNormalizer** - Transcript preprocessing
24. **TranscriptCompressor** - Transcript summarization
25. **SchemaValidator** - LLM response validation
26. **ProcessingTracer** - Event tracking
27. **DatasetCurationService** - Fine-tuning dataset management
28. **TemplateSeeder** - Template seeding utilities

### Middleware Layer

1. **CORS Middleware** - Cross-origin request handling with logging
2. **Large Request Middleware** - Handles large file uploads (500MB limit)
3. **Trusted Host Middleware** - Host validation
4. **Auth Middleware** (`middleware/auth.py`) - JWT validation, user context
5. **Permissions Middleware** (`middleware/permissions.py`) - Role-based access control, company scoping

### Background Tasks

1. **process_recording_task** - Main evaluation orchestration (12-step pipeline)
2. **generate_policy_rules_job** - Async rule generation from policy text

---

## Frontend Architecture

### Routing Structure (`App.tsx`)

#### Public Routes
- `/` - Home (landing page)
- `/features` - Features page
- `/pricing` - Pricing page
- `/faq` - FAQ page
- `/sign-in` - Authentication

#### Protected Routes (require authentication)
- `/dashboard` - Recordings list
- `/demo` or `/test` - Test upload page
- `/results/:recordingId` - Evaluation results viewer
- `/policy-templates` - Template management
- `/human-review` - Human review queue
- `/teams` - Team management
- `/agents` - Agent management
- `/audit-log` - Audit trail viewer
- `/supervisor` - Supervisor dashboard

### State Management

#### Context Providers
- **AuthContext** - Authentication state, JWT token, user profile

#### Zustand Stores
- **policyStore** - Policy template state
- **themeStore** - UI theme preferences

#### API Client (`lib/api.ts`)
Centralized API client with:
- JWT token management
- Automatic token refresh
- Error handling
- Request/response interceptors
- FormData support for file uploads

### Page Components

1. **Home.tsx** - Landing page with hero, features, CTA
2. **Features.tsx** - Feature showcase
3. **Pricing.tsx** - Pricing tiers
4. **FAQ.tsx** - Frequently asked questions
5. **SignIn.tsx** - Login form
6. **Dashboard.tsx** - Recordings list with filters
7. **Upload.tsx** - File upload interface (drag-drop)
8. **Results.tsx** - Evaluation results viewer with transcript player
9. **PolicyTemplates.tsx** - Template CRUD, criteria management
10. **RuleEditor.tsx** - Structured rule editor (Phase 5)
11. **RuleHistory.tsx** - Rule version history
12. **HumanReview.tsx** - Human review queue and correction interface
13. **SupervisorDashboard.tsx** - Supervisor oversight dashboard
14. **TeamsListPage.tsx** - Team management
15. **AgentsListPage.tsx** - Agent management
16. **AuditTrailPage.tsx** - Audit log viewer with filters

### Reusable Components

- **Layout.tsx** - Main layout wrapper with header/navigation
- **Footer.tsx** - Footer component
- **FloatingButtons.tsx** - Floating action buttons
- **SupportChat.tsx** - Support chat widget
- **LazySection.tsx** - Lazy-loaded sections
- **RuleWizard.tsx** - Rule creation wizard
- **RuleSandbox.tsx** - Rule testing sandbox
- **Modals**:
  - TeamFormModal.tsx
  - AgentFormModal.tsx
  - BulkImportModal.tsx

### SEO Implementation

- **useSEO hook** - Dynamic SEO metadata management
- **pageSEO config** - Centralized SEO metadata per route
- Meta tags, Open Graph, Twitter Cards support

---

## Database Schema

### Core Entities

#### Companies (`companies`)
- `id` (UUID, PK)
- `company_name` (VARCHAR)
- `industry` (VARCHAR)
- `created_at` (TIMESTAMP)

#### Users (`users`)
- `id` (UUID, PK)
- `company_id` (UUID, FK → companies)
- `email` (VARCHAR, UNIQUE)
- `password_hash` (VARCHAR)
- `full_name` (VARCHAR)
- `role` (ENUM: admin, qa_manager, reviewer)
- `created_at` (TIMESTAMP)

#### Recordings (`recordings`)
- `id` (UUID, PK)
- `company_id` (UUID, FK → companies)
- `uploaded_by_user_id` (UUID, FK → users)
- `file_name` (VARCHAR)
- `file_url` (TEXT) - GCP Storage URL
- `duration_seconds` (INTEGER)
- `status` (ENUM: queued, processing, completed, failed)
- `error_message` (TEXT)
- `uploaded_at` (TIMESTAMP)
- `processed_at` (TIMESTAMP)

#### Transcripts (`transcripts`)
- `id` (UUID, PK)
- `recording_id` (UUID, FK → recordings, UNIQUE)
- `transcript_text` (TEXT)
- `normalized_text` (TEXT) - Phase 2: Normalized version
- `diarized_segments` (JSONB) - Speaker-attributed segments
- `sentiment_analysis` (JSONB) - Voice-based sentiment
- `transcription_confidence` (DECIMAL)
- `deepgram_confidence` (DECIMAL)
- `created_at` (TIMESTAMP)

#### Policy Templates (`policy_templates`)
- `id` (UUID, PK)
- `company_id` (UUID, FK → companies)
- `template_name` (VARCHAR)
- `description` (TEXT)
- `is_active` (BOOLEAN)
- `policy_rules` (JSONB) - Phase 1: Structured rules
- `policy_rules_version` (INTEGER)
- `rules_generated_at` (TIMESTAMP)
- `rules_approved_by_user_id` (UUID, FK → users)
- `rules_generation_method` (VARCHAR) - 'ai', 'manual', or null
- `enable_structured_rules` (BOOLEAN)
- `created_at` (TIMESTAMP)

#### Evaluation Criteria (`evaluation_criteria`)
- `id` (UUID, PK)
- `policy_template_id` (UUID, FK → policy_templates)
- `category_name` (VARCHAR)
- `weight` (DECIMAL 5,2) - Must sum to 100 per template
- `passing_score` (INTEGER, 0-100)
- `evaluation_prompt` (TEXT) - LLM instruction
- `created_at` (TIMESTAMP)

#### Evaluation Rubric Levels (`evaluation_rubric_levels`)
- `id` (UUID, PK)
- `evaluation_criteria_id` (UUID, FK → evaluation_criteria)
- `level_name` (VARCHAR)
- `min_score` (INTEGER)
- `max_score` (INTEGER)
- `description` (TEXT)

#### Evaluations (`evaluations`)
- `id` (UUID, PK)
- `recording_id` (UUID, FK → recordings, UNIQUE)
- `policy_template_id` (UUID, FK → policy_templates)
- `evaluated_by_user_id` (UUID, FK → users)
- `overall_score` (INTEGER, 0-100)
- `resolution_detected` (BOOLEAN)
- `resolution_confidence` (DECIMAL 3,2)
- `confidence_score` (FLOAT) - Phase 1/2: AI confidence
- `requires_human_review` (BOOLEAN) - Phase 1: Routing flag
- `customer_tone` (JSONB)
- `llm_analysis` (JSONB) - Full LLM response
- `status` (ENUM: pending, completed, reviewed)
- `prompt_id` (VARCHAR) - Phase 2: Reproducibility
- `prompt_version` (VARCHAR)
- `model_version` (VARCHAR)
- `model_temperature` (FLOAT)
- `model_top_p` (FLOAT)
- `llm_raw` (JSONB) - Full raw response
- `rubric_version` (VARCHAR)
- `evaluation_seed` (VARCHAR) - Deterministic seed
- `agent_id` (UUID, FK → users)
- `team_id` (UUID, FK → teams)
- `created_at` (TIMESTAMP)

#### Category Scores (`category_scores`)
- `id` (UUID, PK)
- `evaluation_id` (UUID, FK → evaluations)
- `category_name` (VARCHAR)
- `score` (INTEGER, 0-100)
- `feedback` (TEXT)

#### Policy Violations (`policy_violations`)
- `id` (UUID, PK)
- `evaluation_id` (UUID, FK → evaluations)
- `criteria_id` (UUID, FK → evaluation_criteria)
- `violation_type` (VARCHAR)
- `description` (TEXT)
- `severity` (ENUM: critical, major, minor)

#### Human Reviews (`human_reviews`)
- `id` (UUID, PK)
- `recording_id` (UUID, FK → recordings)
- `evaluation_id` (UUID, FK → evaluations, UNIQUE)
- `reviewer_user_id` (UUID, FK → users)
- `review_status` (ENUM: pending, in_review, completed, disputed)
- `human_scores` (JSONB)
- `human_violations` (JSONB)
- `ai_scores` (JSONB) - Snapshot for comparison
- `delta` (JSONB) - AI→Human differences
- `reviewer_notes` (TEXT)
- `ai_score_accuracy` (DECIMAL)
- `human_overall_score` (INTEGER)
- `human_category_scores` (JSONB)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### Teams (`teams`)
- `id` (UUID, PK)
- `company_id` (UUID, FK → companies)
- `team_name` (VARCHAR)
- `description` (TEXT)
- `created_at` (TIMESTAMP)

#### Agents (`users` as agents)
- Same as users table, linked via `agent_id` in evaluations

#### Agent-Team Memberships (`agent_teams`)
- `agent_id` (UUID, FK → users)
- `team_id` (UUID, FK → teams)
- Many-to-many relationship

#### Audit Logs (`audit_logs`)
- `id` (UUID, PK)
- `company_id` (UUID, FK → companies)
- `user_id` (UUID, FK → users)
- `event_type` (ENUM)
- `entity_type` (VARCHAR)
- `entity_id` (UUID)
- `old_values` (JSONB)
- `new_values` (JSONB)
- `description` (TEXT)
- `reason` (TEXT)
- `model_version` (VARCHAR)
- `confidence_score` (FLOAT)
- `created_at` (TIMESTAMP)

#### Evaluation Versions (`evaluation_versions`)
- `id` (UUID, PK)
- `evaluation_id` (UUID, FK → evaluations)
- `version_number` (INTEGER)
- `snapshot` (JSONB) - Full evaluation snapshot
- `created_by` (VARCHAR)
- `change_reason` (TEXT)
- `created_at` (TIMESTAMP)

#### Policy Rules Models
- **PolicyRulesDraft** - Draft rules before publishing
- **PolicyRulesVersion** - Published rule versions
- **RuleDraft** - Individual rule drafts
- **RuleVersion** - Individual rule versions
- **RuleAuditLog** - Rule change audit trail
- **PolicyClarification** - Clarification questions for rule generation

#### Import Jobs (`import_jobs`)
- `id` (UUID, PK)
- `company_id` (UUID, FK → companies)
- `import_type` (ENUM: agents, teams)
- `status` (ENUM: pending, processing, completed, failed)
- `file_name` (VARCHAR)
- `total_records` (INTEGER)
- `processed_records` (INTEGER)
- `failed_records` (INTEGER)
- `error_message` (TEXT)
- `created_at` (TIMESTAMP)

#### Rule Engine Results (`rule_engine_results`)
- `id` (UUID, PK)
- `recording_id` (UUID, FK → recordings)
- `evaluation_id` (UUID, FK → evaluations)
- `rules` (JSONB) - Rule evaluation output
- `created_at` (TIMESTAMP)

#### Recording Processing Events (`recording_processing_events`)
- `id` (UUID, PK)
- `recording_id` (UUID, FK → recordings)
- `event_type` (VARCHAR)
- `event_data` (JSONB)
- `timestamp` (TIMESTAMP)

### Key Relationships

```
companies (1) ────► (N) users
companies (1) ────► (N) policy_templates
companies (1) ────► (N) recordings
companies (1) ────► (N) teams

policy_templates (1) ────► (N) evaluation_criteria
policy_templates (1) ────► (N) evaluations
policy_templates (1) ────► (N) policy_rules_versions

evaluation_criteria (1) ────► (N) evaluation_rubric_levels
evaluation_criteria (1) ────► (N) policy_violations

recordings (1) ────► (1) transcripts
recordings (1) ────► (1) evaluations
recordings (1) ────► (N) recording_processing_events

evaluations (1) ────► (N) category_scores
evaluations (1) ────► (N) policy_violations
evaluations (1) ────► (1) human_review
evaluations (1) ────► (N) evaluation_versions
evaluations (1) ────► (1) rule_engine_results

teams (1) ────► (N) evaluations
users (N) ────► (N) teams (via agent_teams)
```

---

## Evaluation Pipeline

### Phase 1: Structured Rules Foundation
- Structured, machine-readable policy rules stored as JSONB
- Rule types: boolean, numeric, phrase, list, conditional, multi-step, tone-based, resolution
- AI-powered rule generation from policy text
- Rule versioning and audit trail

### Phase 2: MVP Evaluation Improvements
- Transcript normalization
- 5-signal confidence engine
- Schema validation for LLM responses
- Reproducibility metadata (prompt IDs, model versions, seeds)

### Phase 3: Policy-Based Deterministic Evaluation
- RuleEngineV2: Deterministic rule evaluation before LLM
- Rule results pre-populate evaluation context
- Critical rule overrides (fail-safe mechanism)

### Phase 4: Deterministic LLM Evaluator
- DeterministicLLMEvaluator: Uses structured rules to guide LLM
- Transcript compression for efficiency
- Critical rule overrides applied to LLM results
- Rubric level assignment based on rule compliance

### Processing Steps (Detailed)

1. **Recording Upload & Validation**
   - File validation (type, size ≤ 2GB)
   - GCP Storage upload
   - Database record creation (status: queued)

2. **Background Task Initiation**
   - `process_recording_task` invoked
   - Status updated to `processing`

3. **Transcription (Deepgram)**
   - Deepgram Nova-2 API call
   - Features: diarization, sentiment, utterances
   - Output: transcript text, segments, sentiment, confidence

4. **Transcript Normalization**
   - Text cleaning
   - Speaker role refinement
   - Quality metrics

5. **Policy Template Loading**
   - Fetch active template for company
   - Load evaluation criteria, rubric levels
   - Load structured rules (if enabled)

6. **Deterministic Rule Engine**
   - Evaluate structured rules against transcript
   - Output: rule results by category with severity
   - Pre-populate violations

7. **LLM Evaluation**
   - **If structured rules enabled**: DeterministicLLMEvaluator
     - Build evaluation input with rule results
     - Compress transcript
     - Extract tone mismatches
     - Call LLM (Gemini 2.0 Flash/Pro)
     - Apply critical rule overrides
   - **Else**: Legacy GeminiService
     - Build prompt with rubric levels
     - Include RAG context (optional)
     - Call LLM
     - Parse JSON response

8. **Schema Validation**
   - Validate LLM response structure
   - Extract scores and violations
   - Log validation failures

9. **Scoring & Ensemble**
   - Map rubric levels to numeric scores
   - Apply rule penalties
   - Calculate weighted category scores
   - Compute overall score
   - Aggregate violations

10. **Confidence Calculation**
    - 5-signal confidence model:
      - Transcript quality signal
      - LLM consistency signal
      - Rule hits signal
      - Score distribution signal
      - Schema validation signal
    - Output: confidence_score (0-1), requires_human_review boolean

11. **Persistence**
    - Save transcript
    - Save evaluation (with metadata)
    - Save category scores
    - Save policy violations
    - Save rule engine results
    - Create human review record (if needed)
    - Create audit log entry

12. **Finalization**
    - Update recording status: completed
    - Send email notification
    - Create evaluation version snapshot

---

## Policy Rules System

### Rule Types

1. **Boolean Rules** - True/false requirements
   - Example: "Agent must identify themselves"
   - Fields: `required` (boolean), `description`

2. **Numeric Rules** - Threshold-based rules
   - Example: "Greet customer within 15 seconds"
   - Fields: `comparator` (le, lt, eq, ge, gt), `value`, `unit`, `measurement_field`

3. **Phrase Rules** - Required/forbidden phrases
   - Example: "Must say 'This call may be recorded'"
   - Fields: `required` (boolean), `phrases` (list), `case_sensitive`, `fuzzy_match`

4. **List Rules** - Required items from a list
   - Example: "Must verify at least 2 of: name, email, phone"
   - Fields: `required_items` (list), `min_required`, `all_required`

5. **Conditional Rules** - If-then logic
   - Example: "If customer sentiment is negative, agent must apologize"
   - Fields: `condition`, `then_rule`

6. **Multi-Step Rules** - Sequence verification
   - Example: "Must greet, then identify, then ask how to help"
   - Fields: `steps` (list), `strict_order`, `allow_gaps`

7. **Tone-Based Rules** - Sentiment requirements
   - Example: "Agent tone must match customer tone"
   - Fields: `check_agent_tone`, `check_caller_tone`, `baseline_comparison`, `mismatch_threshold`

8. **Resolution Rules** - Issue resolution detection
   - Example: "Must document next steps if issue unresolved"
   - Fields: `must_resolve`, `resolution_markers`, `must_document_next_steps`

### Rule Generation

**AI-Powered Generation** (`PolicyRuleBuilder`):
- Takes policy text as input
- Uses LLM to extract structured rules
- Supports clarification questions for ambiguous policies
- Validates rule structure before saving

**Manual Creation**:
- Rule Editor UI (`RuleEditor.tsx`)
- Rule Wizard (`RuleWizard.tsx`)
- Sandbox testing (`RuleSandbox.tsx`)

### Rule Versioning

- Drafts before publishing
- Version history tracking
- Rollback capability
- Audit trail for rule changes

### Rule Evaluation Flow

1. Rules loaded from `policy_template.policy_rules` (JSONB)
2. RuleEngineV2 evaluates each rule type
3. Results organized by category
4. Critical rules can override LLM results
5. Results stored in `rule_engine_results` table

---

## Features & Capabilities

### Core Features

1. **Automated QA Evaluation**
   - Upload call recordings
   - Automatic transcription and evaluation
   - Customizable scoring rubrics
   - Policy violation detection

2. **Structured Policy Rules**
   - Machine-readable rules
   - AI-powered rule generation
   - Version control and audit trail
   - Deterministic rule evaluation

3. **Hybrid Evaluation**
   - Deterministic rule engine (pre-scoring)
   - LLM-based contextual evaluation
   - Ensemble scoring combining both

4. **Confidence-Based Routing**
   - 5-signal confidence model
   - Automatic human review routing
   - Quality assurance for edge cases

5. **Human Review Workflow**
   - Review queue for low-confidence evaluations
   - Side-by-side AI vs human scoring
   - Fine-tuning dataset capture

6. **Voice Analytics**
   - Speaker diarization (agent/caller)
   - Sentiment analysis (per segment)
   - Tone mismatch detection
   - Voice baseline comparison

7. **Team & Agent Management**
   - Team organization
   - Agent assignment to teams
   - Bulk import via CSV
   - Performance tracking

8. **Audit & Compliance**
   - Complete audit trail
   - Evaluation versioning
   - Compliance reporting
   - Data retention policies

9. **Batch Processing**
   - Queue-based processing
   - Priority batches
   - Throughput monitoring
   - Error handling and retries

10. **Reproducibility**
    - Prompt versioning
    - Model metadata tracking
    - Evaluation seeds
    - Full response storage

### Advanced Features

1. **Transcript Normalization**
   - Text cleaning
   - Speaker role refinement
   - Quality metrics

2. **Transcript Compression**
   - Summarization for long calls
   - Key point extraction
   - Efficient LLM processing

3. **RAG (Retrieval Augmented Generation)**
   - Policy snippet retrieval
   - Context enrichment for LLM
   - Cost-optimized prompting

4. **Fine-Tuning Dataset Curation**
   - Human review data collection
   - Model feedback loops
   - Continuous improvement

5. **Supervisor Dashboard**
   - Escalation oversight
   - Low-confidence filtering
   - Re-evaluation triggers

6. **Export & Reporting**
   - CSV export
   - PDF reports (planned)
   - API access for BI tools

---

## API Endpoints

### Complete API Reference

See Backend Architecture section for detailed endpoint list. Key endpoint groups:

- **Authentication**: `/api/auth/*`
- **Recordings**: `/api/recordings/*`
- **Evaluations**: `/api/evaluations/*`
- **Templates**: `/api/templates/*`
- **Policy Rules**: `/api/policy-templates/*`
- **Human Reviews**: `/api/human_reviews/*`
- **Batch Processing**: `/api/batch/*`
- **Teams**: `/api/teams/*`
- **Agents**: `/api/agents/*`
- **Imports**: `/api/imports/*`
- **Supervisor**: `/api/supervisor/*`
- **Fine-Tuning**: `/api/fine-tuning/*`

---

## User Workflows

### Company Onboarding (Admin)
1. Create company account
2. Configure GCP Storage access
3. Create policy template
4. Define evaluation criteria
5. Set rubric levels
6. Generate or create structured rules
7. Invite QA managers and reviewers
8. Import agents and teams

### QA Manager Workflow
1. Upload recordings (single or batch)
2. Monitor dashboard for processing status
3. Review evaluation results
4. Adjust policy templates/rubrics as needed
5. Assign human reviews
6. Export reports for leadership

### Reviewer Workflow
1. Access human review queue
2. Review low-confidence evaluations
3. Compare AI scores with transcript
4. Submit corrected scores
5. Provide feedback for continuous learning

### Supervisor Workflow
1. Access supervisor dashboard
2. Filter by violations or low confidence
3. Review escalations
4. Trigger re-evaluations
5. Audit activity logs

---

## Deployment & Infrastructure

### Backend Deployment (GCP Cloud Run)

**Docker Container**:
- Python 3.10+ base image
- FastAPI with Uvicorn
- Environment variables via GCP Secret Manager

**Cloud Build**:
- Automated builds on git push
- Container registry storage
- Cloud Run deployment

**Configuration**:
- Environment variables (see `ENV_VARIABLES_CLOUD_RUN.md`)
- CORS configuration
- GCP IAM permissions

### Frontend Deployment (Vercel)

**Build Process**:
- Vite production build
- Static assets to CDN
- Environment variables via Vercel dashboard

**Configuration**:
- `VITE_API_URL` pointing to Cloud Run
- Custom domain setup
- SSL certificates (automatic)

### Database (Neon PostgreSQL)

- Serverless PostgreSQL
- Connection pooling
- Automated backups
- Migration management via Alembic

### Storage (GCP Cloud Storage)

- Bucket per company (or subdirectory)
- Signed URLs for secure access
- CORS configuration
- Lifecycle policies

### Monitoring & Logging

- Cloud Logging for backend
- Structured logging throughout
- Error tracking (recommend Sentry)
- Performance monitoring

### Security

- JWT authentication
- Company-scoped data access
- Role-based permissions
- Audit trails
- HTTPS everywhere
- GCP IAM for service accounts

---

## Environment Configuration

### Backend Environment Variables

```bash
# Database
DATABASE_URL=postgresql://...

# GCP
GCP_PROJECT_ID=...
GCP_BUCKET_NAME=...
GCP_CLIENT_EMAIL=...
GCP_PRIVATE_KEY=...

# JWT
JWT_SECRET=...
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# APIs
DEEPGRAM_API_KEY=...
GEMINI_API_KEY=...

# Email
SMTP_HOST=...
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
SMTP_FROM=...

# CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Feature Flags
ENABLE_STRUCTURED_RULES=false
GEMINI_USE_HYBRID=false
GEMINI_FORCE_PRO=false
```

### Frontend Environment Variables

```bash
VITE_API_URL=https://api.yourdomain.com
VITE_DEEPGRAM_API_KEY=... # Optional for direct uploads
```

---

## Development & Testing

### Backend Testing

- Unit tests in `backend/app/tests/`
- Integration tests for API endpoints
- Standalone test scripts:
  - `test_gcp_credentials.py`
  - `test_gemini_models.py`
  - `test_rule_engine.py`
  - `test_phase3.py`

### Frontend Testing

- Component tests (recommended: Vitest)
- E2E tests (recommended: Playwright)

### Local Development

**Backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend**:
```bash
cd web
npm install
npm run dev
```

---

## Documentation

### Key Documentation Files

- `README.md` - Project overview
- `COMPREHENSIVE_PROJECT_SUMMARY.md` - This document
- `DATA_PRIVACY_AND_LLM_USAGE.md` - Privacy and LLM usage policies
- `ENV_SETUP.md` - Environment setup guide
- `ENV_VARIABLES_CLOUD_RUN.md` - Cloud Run environment variables
- `TROUBLESHOOTING_AUDIO_PROCESSING.md` - Audio processing troubleshooting
- `TROUBLESHOOTING_DEPLOYMENT.md` - Deployment troubleshooting
- `VERCEL_DEPLOYMENT.md` - Frontend deployment guide
- `backend/docs/AUTO_RULE_GENERATION.md` - Rule generation documentation
- Phase documentation: `Standarized-phase1.md` through `Standarized-phase7.md`

---

## Future Enhancements

### Planned Features

1. **Emotion Classifier Integration**
   - Emotion detection beyond sentiment
   - Integration into scoring ensemble

2. **Real-Time Dashboard Updates**
   - WebSocket support
   - Live status updates

3. **Persistent Task Queue**
   - Cloud Tasks integration
   - Pub/Sub for distributed processing

4. **Advanced Analytics**
   - Trend analysis
   - Performance dashboards
   - Predictive insights

5. **Mobile Application**
   - iOS/Android apps
   - Mobile-optimized workflows

6. **API for Third-Party Integrations**
   - Webhook support
   - REST API documentation
   - SDK development

---

## Conclusion

This AI-Powered QA System is a comprehensive platform for automated call center quality assurance. It combines structured policy rules, deterministic rule engines, LLM-based contextual evaluation, and human-in-the-loop workflows to provide accurate, scalable QA evaluation with full audit trails and continuous learning capabilities.

The system is built for scalability, reliability, and compliance, with extensive documentation and deployment guides for production use.

---

**Last Updated**: December 2024  
**Version**: 0.2.0  
**Project Status**: Production-Ready MVP
