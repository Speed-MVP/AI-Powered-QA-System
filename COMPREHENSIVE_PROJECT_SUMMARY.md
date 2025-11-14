## AI QA System Summary

### TL;DR
- End-to-end FastAPI + React platform that ingests call recordings, runs AI-driven QA scoring, and routes low-confidence cases for human review.
- Backend layers: REST APIs, transcription & evaluation pipeline, rule engine, scoring, audit trails, batch processing, and fine-tuning feedback loops.
- Frontend delivers authenticated dashboards for uploads, evaluations, policy management, team oversight, audits, and knowledge marketing pages.
- Infrastructure docs target GCP Cloud Run + Cloud Storage + Neon Postgres, with detailed deployment, troubleshooting, and phased improvement plans.

### High-Level Architecture
- **Backend (`backend/app`)**: FastAPI app with CORS/middleware, SQLAlchemy models, Alembic migrations, and modular services for AI workflows, storage, emails, and audits.
- **AI Pipeline**: Deepgram transcription + diarization + sentiment, rule engine checks, Gemini-driven rubric evaluation, scoring ensemble, confidence gating, human review routing.
- **Frontend (`web/src`)**: React 19 + Vite + Tailwind UI, Zustand state slices, SEO-aware routing, protected dashboards, upload workflow, and admin tooling.
- **Data Layer**: Neon PostgreSQL via SQLAlchemy models (`company`, `user`, `recording`, `transcript`, `evaluation`, `category_score`, `policy_template`, `rubric_level`, `policy_violation`, `human_review`, `import_job`, `team`, `agent`, `audit_log`).
- **Async & Batch**: Background task `process_recording_task` orchestrates individual evaluations; `BatchProcessingService` handles queues, threading, monitoring, and high-priority bursts.
- **Docs & Ops**: Extensive playbooks for environment setup, GCP configuration, deployment (Cloud Build/Run, Docker, Vercel), troubleshooting, and phased improvement roadmaps.

### End-to-End User Journeys
- **Company Onboarding (Admin)**: Configure company, invite QA managers/reviewers, define policy templates and evaluation criteria, set weights/passing scores, upload rubrics and prompts, verify GCP storage connectivity, and seed agent/team rosters.
- **QA Manager Workflow**: Upload batches (drag-drop or direct stream), monitor dashboard statuses, review evaluation summaries, adjust policy templates/rubrics, create human review assignments, and export reports for leadership.
- **Reviewer / Human QA Flow**: Receive low-confidence tasks, open evaluation + transcript view, compare AI vs rubric, submit corrected scores/feedback via fine-tuning endpoints, and close review for continuous learning.
- **Supervisor Flow**: Use supervisor dashboard to inspect escalations, filter by policy violations or low confidence, requeue problematic evaluations using `/api/recordings/{id}/reevaluate`, and audit activity logs for compliance.
- **Agent & Team Management**: HR ops load rosters (CSV import service), manage memberships via modals, and inspect audit trail for edits to personnel data.

### Evaluation Pipeline Deep Dive (Revenue-Critical)
1. **Recording Intake & Validation**
   - Frontend requests signed URL or streams directly to backend (ingested into GCP bucket).
   - `recordings` table row initialized with status `queued`, uploader reference, metadata.
   - Optional batch queueing triggered via `BatchProcessingService.queue_recordings_for_batch_processing`.
2. **Asynchronous Orchestration**
   - `process_recording_task` invoked by queue workers, Celery-like threading, or manual trigger; immediately flips status to `processing` and persists.
3. **Transcription, Diarization, Sentiment (Voice-First)**
   - `DeepgramService.transcribe` calls Nova-2 with diarization, utterances, sentiment, and adaptive voice baseline algorithms; returns transcript text, diarized segments, agent/caller tone vectors, and confidence.
   - Speaker roles inferred through regex-based context scoring (`_identify_speakers_by_context`) ensuring agent/caller labelling even in atypical openings.
   - Output persisted to `transcripts` table with JSONB diarization + sentiment analysis for downstream analysis and UI playback.
4. **Policy Context Selection**
   - Active `policy_template` fetched by company & status; includes all criteria and rubric levels for rubric-aligned grading.
   - Optional Retrieval Augmented Generation (RAG) fetch (`RAGService`) pulls top policy snippets for prompt grounding.
5. **Deterministic Rule Engine (Pre-Scoring)**
   - `RuleEngineService.evaluate_rules` runs “greeting within 15s”, empathy checks, hold etiquette, closing verification, and silence detection using diarized segments and sentiment data.
   - Each triggered rule returns severity-weighted evidence, pre-populating violation set and adjusting category penalty staging.
6. **LLM Evaluation & Prompt Strategy**
   - `GeminiService.evaluate` computes complexity score (length, negativity, rule hits, topic keywords) to choose Flash vs Pro (hybrid toggle fallback to Pro); builds multi-section prompt with rubric levels, RAG context, deterministic violations, human review exemplars, and strict scoring instructions.
   - Prompt enforces exact category names, weighted scoring, tone realism, keyword gaming detection, and JSON schema compliance.
   - Response parsed (JSON-first with markdown fallback); ensures `category_scores`, tone sections, violations, resolution metrics exist, logs category mismatches, attaches model metadata (`model_used`, `complexity_score`, `cost_tier`).
7. **Scoring Ensemble & Confidence Routing**
   - `ScoringService.calculate_scores` matches rubric levels to assign category scores; `calculate_ensemble_scores` merges LLM output and rule penalties (with placeholder for future emotion classifier).
   - `ConfidenceService.calculate_overall_confidence` evaluates rubric alignment, sentiment quality, rule violations, and model metadata to determine `confidence_score` and `requires_human_review`.
8. **Persistence & Compliance**
   - Evaluation record saved with overall score, resolution detection, tone analysis, LLM payload, confidence data; `CategoryScore` rows inserted per criterion; `PolicyViolation` rows created with category mapping heuristics and severity normalization.
   - `AuditService.log_evaluation_event` writes immutable audit log + evaluation version snapshot for traceability; runbook-friendly metadata (model version, complexity, reasoning) stored alongside.
9. **Human Review Loop**
   - If `requires_human_review`, `HumanReview` entry generated with pending status for manual QA; reviewers access combined AI/human scoring UI and submit corrections via fine-tuning routes.
   - Fine-tuning service archives reviewer judgments for future prompt updates or model retraining.
10. **Notifications & Status Finalization**
    - Recording status flipped to `completed` with timestamp; email notifications dispatched to uploader (success/failure). Dashboard auto-refresh/polling surfaces new evaluations.
    - Re-evaluation endpoints allow reprocessing by dropping new job back into queue.

```21:344:backend/app/tasks/process_recording.py
async def process_recording_task(recording_id: str):
    # status transitions, Deepgram transcription, rule engine, Gemini evaluation,
    # scoring ensemble, confidence routing, audit logging, notifications, and final status update
    ...
```

```83:225:backend/app/services/gemini.py
class GeminiService:
    async def evaluate(...):
        # hybrid model routing, policy/RAG context injection, human review exemplars,
        # structured prompt assembly, JSON parsing, mismatch logging, metadata tagging
        ...
```

```85:173:backend/app/routes/evaluations.py
@router.get("/{recording_id}")
async def get_evaluation(...):
    # Company scoping, evaluation retrieval, category scores, violations, tone data exposure
    ...
```

### Backend Breakdown
- **Entry Point (`app/main.py`)**
  - Registers middleware (CORS logging, large upload guard, trusted hosts) and routers for auth, recordings, evaluations, templates, teams, agents, batch processing, fine-tuning, supervisors, and imports.
  - Centralized exception handling with structured JSON responses, startup DB init, and root health message.
- **Configuration & Database**
  - `config.py` loads environment settings (CORS origins, API keys, model toggles, logging levels).
  - `database.py` manages SQLAlchemy session/engine; `SessionLocal` used across services.
  - Alembic migrations under `backend/migrations/versions` track schema evolution.
- **Middleware Layer (`middleware/`)**
  - `auth.py` validates JWT tokens, attaches user context.
  - `permissions.py` enforces role- and company-scoped access control.
- **Routes (`routes/`)**
  - `auth.py`: login, token management, current-user fetch.
  - `recordings.py`: signed URL issuance, direct uploads, listing/filtering, re-evaluation trigger, download links, deletion.
  - `evaluations.py`: evaluation retrieval, transcript access, policy violations, supervisor views.
  - `templates.py`: CRUD for policy templates, criteria, rubric levels.
  - `batch_processing.py`: start/stop queue, status checks, enqueue helpers, high-priority batches.
  - `fine_tuning.py`: surface human review queue, submission endpoint, evaluation-with-template accessor.
  - `supervisor.py`, `teams.py`, `agents.py`, `imports.py`: management endpoints for teams, agents, audits, and CSV imports.
- **Services (`services/`)**
  - **Transcription**: `deepgram.py` wraps Deepgram API with diarization, sentiment, adaptive speaker baselines, and contextual speaker identification.
  - **LLM Evaluation**: `gemini.py` selects Gemini Pro/Flash models, builds rubric prompts with RAG policy context, human review exemplars, and rule-engine findings.
  - **Rule Engine**: `rule_engine.py` applies deterministic policy checks (greeting, empathy, hold etiquette, closing, silence) before LLM scoring.
  - **Scoring**: `scoring.py` calculates rubric-weighted scores, merges rule penalties, enforces category validation, and aggregates violations.
  - **Confidence**: `confidence.py` determines overall evaluation certainty, toggles human review routing.
  - **Audit & Compliance**: `audit.py` logs every evaluation event, builds version snapshots, and stores change metadata.
  - **Batch Ops**: `batch_processing.py` orchestrates async queues, monitors throughput, supports worker scaling.
  - **Other Utilities**: `storage.py` handles GCP signed uploads, `email.py` sends status notifications, `csv_import_service.py` parses bulk agent uploads, `rag.py` retrieves policy snippets, `fine_tuning.py` manages human review lifecycle, `continuous_learning.py` outlines model feedback loops.
- **Task Orchestration**

```20:110:backend/app/tasks/process_recording.py
async def process_recording_task(recording_id: str):
    """Background task to process recording"""
    # Fetch recording, mark processing
    # Deepgram transcription + diarization + sentiment baselines
    # Determine active policy template for company
    # Run deterministic rule engine on diarized segments
    # Call Gemini evaluation with rubric + RAG context + rule results
    # Compute rubric-weighted scores + ensemble penalties
    # Calculate confidence, trigger human review if needed
    # Persist transcript, evaluation, category scores, violations
    # Append audit log & version, send notifications, update status
```

- **Batch Processing Flow**
  - Workers pop queued recordings, call `process_recording_task`, update throughput metrics, and raise failure alerts.
  - Queue monitor checks backlog, advises scaling, and provides real-time throughput estimates.
- **Human Review & Continuous Learning**
  - Evaluations flagged for review spawn `HumanReview` entries; front-end reviewers correct scores; data feeds fine-tuning endpoints.
  - Gemini prompt pulls human-reviewed exemplars for few-shot alignment.
- **Testing**
  - `backend/app/tests` includes API integration smoke tests.
  - Standalone scripts (`test_gcp_credentials.py`, `test_gemini_models.py`, `test_rule_engine.py`, `test_phase3.py`) validate infrastructure and AI components.

### Evaluation Data Outputs & Surfacing
- **Database Artifacts**
  - `recordings`: ingest metadata, durations, status machine (`queued` → `processing` → `completed|failed`), error messages for postmortems.
  - `transcripts`: raw transcript text, diarized segments JSONB (speaker, text, timestamps), Deepgram confidence, sentiment arrays (voice-derived), voice baseline metadata.
  - `evaluations`: overarching QA score, resolution booleans, resolution confidence, customer tone breakdown, full LLM payload (for auditing), confidence score, human review flag, status (`completed|reviewed`), timestamps.
  - `category_scores`: normalized rubric category scores + textual feedback per criterion.
  - `policy_violations`: deterministic + LLM-detected violations with severity, mapped back to criteria IDs for template-level reporting.
  - `human_review`: pending/completed human QA decisions, overrides, AI accuracy scoring for continuous learning.
  - `audit_log` + evaluation versions: immutable snapshots capturing who/what/when for all evaluation events.
- **API Surface Area**
  - `/api/evaluations/{recording_id}`: returns evaluation summary, category scores, violations, tone analysis, metadata.
  - `/api/evaluations/{recording_id}/transcript`: delivers diarized transcript for UI playback + manual QA checks.
  - `/api/evaluations/{evaluation_id}/with-template`: bundles evaluation with template + rubric levels for human reviewers.
  - `/api/recordings/{id}/reevaluate`: requeues evaluation (post-template tweak or suspected anomaly).
  - `/api/fine-tuning/human-reviews/*`: exposes queues and submission endpoints for manual QA corrections.
- **Frontend Surfaces**
  - `Results` page renders KPI cards (overall score, resolution state, confidence), table of category scores (with rubric-weighted visualizations), violation timeline, agent/caller tone summaries, and transcript scrubber.
  - `Dashboard` aggregates statuses, applying filters (company, template, date range) and styles for quick triage.
  - `HumanReview` screen juxtaposes AI outputs with rubric guidance, enabling reviewers to override and send corrective feedback.
  - `SupervisorDashboard` and `AuditTrailPage` provide oversight on low-confidence items, reviewer throughput, and compliance changes.
  - Export actions (CSV/PDF hooks) rely on evaluation + category score data for downstream BI ingestion.

### Frontend Breakdown
- **Stack & Tooling (`web/package.json`)**
  - React 19, TypeScript 5.9, Vite 7, Tailwind CSS, lucide icons, React Router v7, Zustand state management.
- **Routing (`App.tsx`)**
  - `Layout` shell wraps all pages; `ProtectedRoute` guards authenticated screens; SEO hook injects metadata per route.
  - Public routes: home, features, pricing, FAQ, sign-in; Protected routes: dashboard, results detail, policy templates, human review, teams, agents, audit log, supervisor board, demo/test upload.
- **State & API**
  - `AuthContext` persists JWT token, hydrates user profile, handles login/logout flows.
  - `lib/api.ts` centralizes backend calls (auth, recordings, evaluations, templates, rubric management, teams/agents CRUD, fine-tuning, supervisor dashboards, audit logs, CSV imports). Handles token sync, FormData uploads, signed URL operations, error messaging.
- **Pages**
  - `Home`, `Features`, `Pricing`, `FAQ`: marketing + feature explanation, integrated with SEO targets (`SEO_IMPLEMENTATION_SUMMARY.md`).
  - `Dashboard`: list recordings with status, filtering, refresh.
  - `Upload`: orchestrates drag-drop uploads (via `react-dropzone`), optional direct backend streaming, signed URL fallback.
  - `Results`: displays evaluation summary, transcript, category scores, violations, tone analysis, download controls.
  - `PolicyTemplates`: create/edit templates, criteria, rubric levels.
  - `HumanReview`: queue of low-confidence evaluations for manual adjudication.
  - `TeamsListPage`, `AgentsListPage`: manage personnel, assignments, imports, audits (uses modals in `components/modals/`).
  - `SupervisorDashboard`: aggregated evaluation queue for oversight roles.
  - `AuditTrailPage`: renders audit log filters for compliance.
  - `SignIn`: credential form hitting `/api/auth/login`.
- **Components**
  - `Layout`, `Footer`, `FloatingButtons`, `SupportChat`, `LazySection`.
  - Modals for team/agent creation and bulk imports.
- **Styling & SEO**
  - Tailwind + custom `index.css`; `hooks/useSEO` updates document metadata; `pageSEO` centralizes per-route metas.

### Data & Domain Model
- **Core Entities**
  - Companies, users (roles: admin, QA manager, reviewer), teams, agents, policy templates, evaluation criteria, rubric levels, recordings, transcripts, evaluations, category scores, policy violations, audit logs, human reviews, import jobs.
- **Key Relationships**
  - Company-scoped data enforced via middleware; recordings tie to transcripts and evaluations; evaluations link to policy templates and human review artifacts; agents map to teams via membership tables.
- **Migrations**
  - Eleven Alembic versions covering teams/agents, template rubrics, human review enhancements, audit trails, sentiment fields, and batch-processing metadata.

### AI & Analytics Capabilities
- **Voice Analytics**: Deepgram diarization + sentiment for both caller and agent, contextual speaker labelling, adaptive voice baselines.
- **Deterministic Policies**: Rule engine enforces greeting windows, empathy requirements, hold etiquette, closing checks, silence thresholds.
- **LLM Evaluation**: Gemini hybrid approach (Flash for routine, Pro for complex) with rubric-level scoring, policy context (RAG), human-review exemplars, tone analysis instructions, violation extraction, resolution detection.
- **Scoring Ensemble**: Combines LLM outputs, rule penalties, and (future) emotion classifiers into weighted category + overall scores; flags violations tied to criteria.
- **Confidence & Routing**: Confidence service calculates reliability; low-confidence cases spawn human review tasks and fine-tuning feedback loops.
- **Auditability**: Audit service writes detailed event logs, evaluation versions, model metadata, ensuring compliance and reproducibility.
- **Continuous Learning**: `continuous_learning.py`, `fine_tuning.py`, and human review endpoints support dataset curation for future model retraining and prompt refinement.

### Async & Batch Processing
- **Standard Flow**: Upload -> `process_recording_task` (transcribe → rule engine → Gemini → scoring → audit → notification).
- **Batch Mode**: `BatchProcessingService` (workers, queue, monitor) processes queued recordings concurrently, supports immediate high-priority batches, tracks throughput and failures.
- **Background Infrastructure**: Intended for deployment on Cloud Run/Cloud Tasks/Functions; uses threaded executors inside service.

### Failure Handling & Observability
- **Error Pathing**: Any exception in `process_recording_task` rolls back transactions, marks recording `failed`, stores `error_message`, and notifies uploader; failure also increments batch stats for monitoring.
- **Retry Strategy**: Operators can requeue via batch service or single reevaluation endpoint; doc guidance outlines Cloud Tasks/PubSub integration for automated retries.
- **Logging**: Structured logging at each pipeline step (transcription start, rule results, model selection, persistence outcomes) with severity gating; CORS middleware logs unexpected origins, upload middleware logs large payloads.
- **Instrumentation Hooks**: Stats dictionary in batch service tracks processed/failed/queued counts and average processing time, enabling throughput dashboards; future TODO points to external metrics sink.
- **Audit Trails**: Evaluation completion logs include model version, confidence, complexity, and reason strings to support compliance reviews and contract SLAs.
- **Testing Scripts**: Dedicated scripts validate third-party credentials and evaluation pipeline correctness before production rollouts.

### Security & Compliance
- JWT auth with bearer tokens; middleware verifies company scoping.
- CORS origins dynamically expanded to cover `www` variants; logging middleware records origin mismatches.
- Trusted host middleware defaults to wildcard but documented for tightening.
- Audit trail records policy edits, evaluation changes, human review adjustments.
- Rule engine and tone analysis guard against keyword gaming by agents.
- Extensive docs on GCP IAM, CORS configuration, environment variables (e.g., `ENV_VARIABLES_CLOUD_RUN.md`, `ENV_SETUP.md`).

### Deployment & Operations
- **Backend**: Dockerfile, docker-compose, Cloud Build `cloudbuild.yaml`, `deploy.sh`, `start_server.py`.
- **Infrastructure Guides**: `BUILD_CONTAINER.md`, `CLOUD_BUILD_SETUP.md`, `CLOUD_RUN_DEPLOYMENT.md`, `DEPLOY_WITHOUT_CLI.md`, `GCP_PERMISSIONS_SETUP.md`, `ENV_VARIABLES_CLOUD_RUN.md`.
- **Frontend**: Vercel deployment instructions (`VERCEL_DEPLOYMENT.md`, `web/QUICK_START.md`, `web/README.md`).
- **Testing & Troubleshooting**: `TROUBLESHOOTING_AUDIO_PROCESSING.md`, `TROUBLESHOOTING_DEPLOYMENT.md`, `VOICE_TONE_DETECTION.md`, `LARGE_FILE_UPLOAD.md`.
- **Playbooks & Roadmaps**: `END_TO_END_FLOW.md`, `ROADMAP_*`, `EVALUATION_PROCESS_DOCUMENTATION.md`, `IMPLEMENTATION_SUMMARY.md`, `Improvement_phase[1-4].md`, `SEO_IMPLEMENTATION_SUMMARY.md`.

### Environment & Configuration
- `.env` variables managed via `pydantic-settings`; required keys include database URL, GCP project/bucket, Deepgram, Gemini, email SMTP, JWT secret, CORS origins, hybrid model flags.
- Frontend expects `VITE_API_URL`, optional Deepgram key for direct uploads.
- Tailwind configured in `tailwind.config.js`; build output in `web/dist`.

### Gaps & Next Steps
- Emotion classifier integration placeholder in scoring ensemble.
- Batch processor logs reference missing variable `successful`/`failed` inside loop (worth review).
- Consider enabling WebSocket/polling for real-time dashboard updates (currently manual/poll based).
- Evaluate persistent task queue (e.g., Cloud Tasks, Pub/Sub) for horizontal scalability beyond in-memory queue.
- Continue curating human review data to tighten Gemini prompt alignment and future fine-tuning.

