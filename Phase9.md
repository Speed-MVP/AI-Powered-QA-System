Phase 9 — Sandbox System (Test Evaluations, Orchestration, UI Integration)

Purpose: provide a safe, cost-effective, and fast environment for QA managers and reviewers to test blueprints against transcripts or audio files before/after publish. Sandbox must support synchronous transcript runs, asynchronous audio runs, reproducible results, debugging info (prompts, detections), rate-limiting/quota, and clear audit logs. It’s also the primary testing ground for tuning detection thresholds and prompt versions.

1 — Goals & constraints

Fast feedback for transcript-only tests (sync).

Robust async pipeline for audio -> transcription -> evaluation.

Cost control: token limits, rate limits, sandbox quotas.

Reproducible: store input snapshot (or hash) and compiler/prompt versions used.

Safe: PII redaction applied before any LLM calls; zero-data-retention option available.

Debuggable: show pre-hit detection, LLM prompt (if permitted), schema outputs, and logs.

Idempotent sandbox runs via Idempotency-Key.

Permissioned: sandbox runs allowed for reviewers but prompt/debug exposure only for admins/qa_manager roles.

2 — High-level architecture & components

API layer: endpoints described in Phase 3 (/sandbox-evaluate, /sandbox-runs/{id}) with sync/async modes.

Orchestrator: short-lived workflow engine (e.g., Celery, Cloud Tasks) that sequences tasks: validate input → fetch compiled artifacts → transcription (if audio) → transcript normalization → detection → per-stage LLM evaluation → scoring → persist sandbox result.

Transcription service: Deepgram or configured provider; uses company keys.

Detection Engine: Phase 5 module.

Stage LLM Evaluator: Phase 6 module.

Scoring Engine: Phase 7 module.

Sandbox Store: DB tables for sandbox_runs, sandbox_inputs and sandbox_results (JSONB). Optionally store artifacts in object storage (S3/GCS) for large audio files or logs.

Job Worker Pool: autoscaling workers handling async sandbox jobs; separate quota from production evaluation workers to protect costs.

Rate limiter & quota service: per-company limits; reject or queue excess runs.

UI integration hooks: websockets or polling endpoints for job updates; downloadable artifacts for debugging.

3 — Sandbox DB schema (minimal)

sandbox_runs:

id UUID PK

company_id UUID

created_by UUID

blueprint_id UUID (optional; may run without blueprint)

blueprint_version_id UUID (which compiled flow used)

input_type ENUM('transcript','audio')

input_location TEXT (s3/gcs path) or input_hash

status ENUM('queued','running','succeeded','failed')

result_id UUID → sandbox_results.id

idempotency_key VARCHAR NULL

created_at, updated_at timestamps

sandbox_results:

id UUID PK

sandbox_run_id UUID FK

transcript_snapshot JSONB (redacted) or transcript_hash

detection_output JSONB

llm_stage_outputs JSONB (optionally redacted)

final_evaluation JSONB

logs JSONB (compile/eval logs, errors)

cost_estimate JSONB (llm_tokens, transcription_seconds, estimated_cost)

created_at timestamp

sandbox_quota (per company):

company_id, monthly_allowed_runs, monthly_used_runs, last_reset

4 — API behavior & workflows
A. Synchronous transcript run (fast feedback)

POST /api/blueprints/{id}/sandbox-evaluate with body:

{
  "mode":"sync",
  "input":{"transcript":"string","language":"en-US"},
  "options":{"use_compiled_flow":true,"target_stage_ids":["..."]}
}


Flow:

Validate blueprint and blueprint compiled status (or allow draft sandbox).

Normalize transcript (Phase 5).

Run Detection Engine (semantic/exact/hybrid) to produce deterministic_results.

Run per-stage LLM evaluation (Phase 6) synchronously (respect token limits).

Run Scoring Engine (Phase 7).

Return 200 OK with sandbox_result JSON (same format as evaluation payload) and run_id.

Persist sandbox_runs & sandbox_results with debug logs per permissions.

Limits: transcript size < X chars (e.g., 20k) for sync. Exceed → return 413 with guidance.

B. Asynchronous audio run

POST /api/blueprints/{id}/sandbox-evaluate with:

{
  "mode":"async",
  "input":{"recording_id":"uuid"} // or upload and get signed URL
}


Flow:

Validate and enqueue CompileJob into Orchestrator; return 202 Accepted and run_id.

Worker steps:

Retrieve audio via signed URL.

Run transcription (Deepgram) → transcript. Track transcription_confidence and store transcript snapshot (redacted).

Normalize transcript.

Run Detection Engine.

For each stage, run Stage LLM Evaluator (use per-stage token budgets).

Run Scoring Engine.

Save sandbox_results, cost estimate, logs.

Notify via webhook and UI (websocket/poll) on completion.

Client polls GET /api/blueprints/{id}/sandbox-runs/{run_id} to get status/result.

Retries: On transient failures (network/LLM throttling), retry with exponential backoff and capped retries (e.g., 3). Log retries.

5 — Cost management & quotas
Cost controls

Per-company token cap (monthly) and per-run maximum tokens. Reject runs that would exceed cap.

Sandbox-specific cheaper models: allow companies to route sandbox LLM calls to cheaper models (e.g., smaller LLM) via company_config. Warning: results may differ from production model; surface this to user.

Sandbox throttling: per-company concurrent runs limit (default 3).

Sandbox run quotas: monthly/daily limits; admin endpoint to top-up quotas.

Estimated cost provided pre-run for async audio: show expected token & transcription cost before enqueueing.

Billing tie-in

Track usage per company: llm_tokens_used, transcription_seconds, estimated_cost. Expose in billing dashboard.

6 — Security & privacy for sandbox

Apply PII redaction before LLM calls. For transcript-only sync runs, keep transcript snapshot for audit unless company opt-out. For zero-data-retention companies, do not persist transcript or LLM outputs; only store hashes & final evaluation JSON.

Signed URLs for audio access; short TTL. Workers should have restricted IAM permissions.

Store logs and LLM raw outputs in encrypted storage with RBAC (admins & qa_manager only). Reviewers may get redacted views.

Sanitize phrase inputs to prevent prompt injection; escape/encode when inserting into prompts.

Implement Idempotency-Key header handling to avoid duplicate runs.

7 — Debugging, observability & UI debug modes

Provide a debug flag (admin-only) to include:

deterministic_results (pre-hits per behavior)

stage_prompts (redacted if PII), prompt_version_tag, model_version

llm_raw_response (if allowed)

sanitization_log (what PII was redacted)

transcription_log (Deepgram call ids, confidence breakdown)

UI should allow toggling Show debug (permissioned).

Keep sanitized logs for at least 30 days (configurable retention).

8 — Sandbox UX considerations (ties to Phase 8)

Show run progress with stages: Transcribing → Detecting → Evaluating stages → Scoring → Done.

Stream partial results where possible: after transcription complete, show transcript and deterministic detection hits even if LLM stage evaluation running.

For long-running audio runs, allow user to cancel job.

Provide “Retry run” with same idempotency key to re-trigger after fixes.

Allow user to mark a sandbox result as Save as training example to push into fine-tuning dataset with minimal metadata. Store mapping to sandbox_results.id.

9 — Testing & QA for sandbox
Unit & integration tests

Sync transcript run: validate output format, schema, and prompt version used.

Async audio run: full E2E with mocked Deepgram and LLM. Validate sandbox_runs lifecycle and logs.

Idempotency test: same Idempotency-Key returns same run_id and does not double-bill.

Failure & retry tests: simulate LLM throttling and ensure retry/backoff works.

Quota enforcement tests: exceeding quota returns proper 429 and message.

Zero-data-retention behavior test: ensure no transcripts/LLM raw stored.

E2E tests

Upload small audio → sandbox run → verify transcript, detection evidence, stage evaluation, and scoring match expected golden file.

Regression corpus: include 50 sample calls and expected sandbox outputs to detect drift.

10 — Monitoring & metrics (what to track)

sandbox_runs_started, sandbox_runs_completed, sandbox_runs_failed (per company)

avg latency per sandbox run (transcription time + detection + LLM time + scoring)

tokens used per sandbox run, transcription seconds per run

debug-mode enabled rate

idempotency duplicate attempts count

quota exhaustion events

worker queue length & worker error rates

Set alerts:

Production worker error rate > 1% for 5 mins

Sandbox queue length > threshold (indicates underprovisioning)

Unexpected cost spike (>x% in a day)

11 — Deliverables for devs

Implement sandbox_runs & sandbox_results tables and migrations.

API endpoints for sync & async runs and run status (see Phase 3).

Orchestrator worker implementation (Cloud Tasks / Celery / PubSub).

Transcription integration & retry logic (Deepgram wrapper).

Detection + Stage LLM + Scoring invocation pipeline with proper versioning inputs.

Quota & rate-limiter service integrations.

Idempotency key handling & duplicate detection.

Debug logging & redaction module tied to sandbox.

UI hooks: websocket or polling for run updates; partial result streaming.

E2E test suite and regression corpus.

Billing/usage tracking integration (llm tokens, transcription seconds).

Documentation for admins: how to view sandbox logs, re-run jobs, and purge sandbox data (GDPR/retention).

12 — Example sandbox result (trimmed)
{
  "run_id":"sandbox-uuid",
  "blueprint_id":"bp-uuid",
  "used_compiled_version": "v3",
  "input":{"type":"audio","recording_id":"rec-uuid","duration_seconds":420},
  "status":"succeeded",
  "final_evaluation":{
    "overall_score":82,
    "requires_human_review":false,
    "confidence_score":0.78,
    "stage_scores":[ ... ],
    "policy_violations":[ ... ]
  },
  "debug":{
    "transcription":{"provider":"deepgram","confidence":0.93,"id":"dg-123"},
    "detection_pre_hits":{...},
    "llm_stage_prompts":[{"stage_id":"s1","prompt_version":"v1.2","tokens":320}],
    "llm_tokens_total":1200
  },
  "cost_estimate":{"llm_tokens":1200,"transcription_seconds":420,"estimated_cost_usd":0.42},
  "created_at":"2025-11-24T..."
}

13 — Operational runbook (common operator tasks)

Cancel job: provide UI and API to cancel queued/running sandbox job (worker must stop and mark status canceled).

Retry failed job: admin may re-run failed job after fix; support force=true to bypass idempotency in special cases.

Purge sandbox data: provide admin tool to purge sandbox_runs/results for a company (GDPR/retention).

Investigate job logs: expose downloadable JSON logs including transcript snapshot, deterministic hits, prompt version, llm responses (if permitted).

Increase quota: admin endpoint to increase company sandbox quota if they hit limits.

14 — Acceptance criteria

Sync transcript sandbox returns valid evaluation under 2s for typical transcripts (<=5k chars).

Async audio sandbox completes E2E (transcription + eval) within acceptable SLA (typ. < 5x audio duration, ideally < 2x for small files).

Idempotency enforced: duplicate Idempotency-Key within 24h does not double-charge or duplicate runs.

Quotas enforced and reported correctly.

Debug logs provide full traceability of detection and LLM prompts (when permitted).

Zero-data-retention mode verified by tests (no raw transcripts or LLM outputs stored).