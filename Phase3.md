Phase 3 — API Layer (Blueprint CRUD, Publish, Sandbox + Contracts)

This phase defines the complete API surface your backend must implement to support the Unified QA Blueprint lifecycle: create/edit/delete blueprints; stage/behavior management; publish/compile workflow; sandbox/test evaluations; version listing; and admin actions. It includes request/response schemas, validation rules, error codes, authentication/authorization, background job behavior, idempotency, webhooks, and operational guardrails. No source code — implementation-ready API contract.

Principles & patterns (applies across endpoints)

Auth: JWT bearer tokens. All endpoints require a valid token except public templates. Use Authorization: Bearer <token>.

RBAC: enforce roles: admin, qa_manager, reviewer, auditor. Only admin/qa_manager can create/publish blueprints. Reviewers may run sandbox.

Multi-tenancy: every request is company-scoped. Enforce company_id from token or header and validate ownership.

Idempotency: For publish and sandbox-run endpoints, accept Idempotency-Key header. Server must store keys and de-duplicate requests for 24 hours.

Optimistic concurrency: Use If-Match: <etag> header for updates. Return 409 Conflict if etag mismatch.

Background processing: Publishing triggers a background compiler job. Publish endpoint returns 202 Accepted + job id; client polls job status endpoint.

Logging & audit: Each mutating request must create an audit log entry with user_id, action, blueprint_id, and request_snapshot. Publishing stores compiled artifact ids in qa_blueprint_versions.

Rate limits: Per-company default: sandbox runs ≤ 10/min (configurable). Enforce in-app; return 429 Too Many Requests.

Schema validation: Reject invalid payloads with 400 and structured errors.

Circuit-breakers & retries: The publish job interacts with LLM / rule-generation pipelines; implement retries/backoff and fallback; expose job failure reasons to API consumer.

Webhooks: Optionally notify clients on publish_complete, publish_failed, and sandbox_result. Allow per-company webhook registration.

Endpoint list (grouped)
A. Blueprint management

POST /api/blueprints — Create blueprint (draft)

GET /api/blueprints — List blueprints (paginated)

GET /api/blueprints/{id} — Retrieve blueprint (with stages + behaviors)

PUT /api/blueprints/{id} — Update blueprint (draft only)

DELETE /api/blueprints/{id} — Delete blueprint (draft only)

POST /api/blueprints/{id}/duplicate — Create a copy (useful for templates)

GET /api/blueprints/{id}/versions — List published versions

GET /api/blueprints/{id}/versions/{version} — Retrieve published snapshot

B. Stage & behavior management (alternative: managed via blueprint payload)

POST /api/blueprints/{id}/stages — Add stage

PUT /api/blueprints/{id}/stages/{stage_id} — Update stage (order, name, weight)

DELETE /api/blueprints/{id}/stages/{stage_id} — Delete stage

POST /api/blueprints/{id}/stages/{stage_id}/behaviors — Add behavior

PUT /api/blueprints/{id}/stages/{stage_id}/behaviors/{behavior_id} — Update behavior

DELETE /api/blueprints/{id}/stages/{stage_id}/behaviors/{behavior_id} — Delete behavior

Note: you may choose a single PUT /api/blueprints/{id} that updates the full blueprint including stages/behaviors; still provide the atomic endpoints for better UX and concurrent editing control.

C. Publish & Compiler

POST /api/blueprints/{id}/publish — Validate + Compile blueprint (triggers background job)

GET /api/blueprints/{id}/publish_status/{job_id} — Poll job status or get result

POST /api/blueprints/{id}/unpublish — Mark blueprint unpublished (admin)

POST /api/blueprints/{id}/recompile — Re-run compiler for existing version

D. Sandbox / Test evaluation

POST /api/blueprints/{id}/sandbox-evaluate — Run sample transcripts/audio against the draft/published blueprint (sync or async depending on input size)

GET /api/blueprints/{id}/sandbox-runs/{run_id} — Get sandbox run result

E. Templates & import/export

GET /api/blueprints/templates — List preset templates

POST /api/blueprints/import — Import legacy template JSON (internal mapping) — returns created draft blueprint(s).

POST /api/blueprints/{id}/export — Export blueprint JSON or snapshot.

F. Admin & monitoring

GET /api/admin/compile_errors — list recent compile errors (admin)

GET /api/admin/sandbox_usage — sandbox usage metrics (admin)

POST /api/webhooks — register company webhook (admin)

GET /api/webhooks — list webhooks

Request/Response schemas (core endpoints)
1) Create blueprint

POST /api/blueprints

Headers: Authorization: Bearer, optional Idempotency-Key

Request body (JSON):

{
  "name": "string (required)",
  "description": "string (optional)",
  "metadata": { "language": "en-US", "template_source": "optional" },
  "stages": [
    {
      "stage_name": "Opening",
      "ordering_index": 1,
      "stage_weight": 20,
      "behaviors": [
        {
          "behavior_name": "Greeting",
          "description": "Agent greets customer",
          "behavior_type": "required",
          "detection_mode": "semantic",
          "phrases": null,
          "weight": 5,
          "critical_action": null,
          "metadata": {}
        }
      ]
    }
  ]
}


Success response:

201 Created

Body:

{
  "id": "uuid",
  "name": "Standard Support Blueprint",
  "status": "draft",
  "version_number": 1,
  "created_at": "2025-11-24T...Z",
  "stages_count": 3,
  "links": {
    "self": "/api/blueprints/{id}",
    "publish": "/api/blueprints/{id}/publish"
  }
}


Errors:

400 Bad Request with structured validation errors {"errors":[{"field":"stages[0].behaviors[0].weight","message":"weight must be >=0"}]}

401 Unauthorized / 403 Forbidden / 409 Conflict (duplicate name)

2) Get blueprint (full)

GET /api/blueprints/{id}

Success: 200 OK returns normalized blueprint payload with etag header for concurrency.

Body:

{
  "id":"uuid",
  "company_id":"uuid",
  "name":"Standard Support Blueprint",
  "description":"...",
  "status":"draft",
  "version_number":1,
  "stages":[
    {
      "id":"stage-uuid",
      "stage_name":"Opening",
      "ordering_index":1,
      "stage_weight":20,
      "behaviors":[
        {
          "id":"behavior-uuid",
          "behavior_name":"Greeting",
          "behavior_type":"required",
          "detection_mode":"semantic",
          "phrases":null,
          "weight":5,
          "critical_action":null,
          "metadata":{}
        }
      ]
    }
  ],
  "metadata":{},
  "created_by":"user-uuid",
  "created_at":"..."
}


Headers:

ETag: "<hash>" (use for If-Match in updates)

Errors:

404 Not Found if blueprint doesn't exist or not company-scoped.

3) Update blueprint

PUT /api/blueprints/{id}

Headers: Authorization, If-Match: <etag> (required), optional Idempotency-Key

Request body: same schema as create but allow partial changes. Validate that blueprint is draft. If updating a published blueprint, return 403 (must use versioning/publish flow to change published versions or create new draft).

Success:

200 OK returns updated blueprint with new etag.

Errors:

409 Conflict if etag mismatch. Return current ETag and latest representation in body for client to merge.

400 for schema errors.

403 if user not allowed.

4) Delete blueprint

DELETE /api/blueprints/{id}

Rules:

Only draft blueprints can be deleted.

If blueprint has published versions, advise archive instead; require force=true param for admins to delete compiled artifacts.

Responses:

204 No Content on success.

403 if attempt to delete published blueprint without force.

404 if not found.

5) Publish blueprint (validate + compile)

POST /api/blueprints/{id}/publish

Headers: Authorization, Idempotency-Key recommended.

Request body (optional):

{
  "force_normalize_weights": false,
  "publish_note": "string (optional)",
  "compiler_options": {
    "generate_policy_rules": true,
    "prompt_version_tag": "v1.0"
  }
}


Behavior:

Validate blueprint (publish checks in Phase 2). If validation fails, return 400 with details. If validation passes:

Create qa_blueprint_versions snapshot with incremented version_number.

Kick off background CompilerJob that will:

Convert blueprint → FlowVersion, FlowStages, FlowSteps, ComplianceRules, RubricTemplate

Run rule-generation (if enabled)

Run basic compile tests (run small rule engine simulation)

Persist qa_blueprint_compiler_map

Mark blueprint status=published and set compiled_flow_version_id only after job success.

Immediate response:

202 Accepted

Body:

{
  "job_id":"job-uuid",
  "blueprint_id":"uuid",
  "status":"queued",
  "links":{"job_status":"/api/blueprints/{id}/publish_status/{job-uuid}"}
}


Job polling:
GET /api/blueprints/{id}/publish_status/{job_id}

200 OK with:

{
  "job_id":"job-uuid",
  "status":"running|succeeded|failed",
  "progress":60,
  "compiled_flow_version_id":"flow-uuid (if succeeded)",
  "errors":[{"code":"LLM_SCHEMA_VALIDATION","message":"Stage prompt failed schema."}]
}


On success:

Update qa_blueprints.compiled_flow_version_id and qa_blueprint_versions record with compiled artifacts.

Push webhook publish_complete if configured.

On failure:

publish_status returns failed with errors list; blueprint remains draft or set to published:failed depending on policy. Recommend leaving status=draft and allow fix + re-publish. Allow admin to view logs.

Errors:

400 if validation fails initially (return full list of publish validation errors).

403 if user not allowed.

409 if another publish job in progress (return active job id).

6) Sandbox evaluate (run a transcript or audio against blueprint)

POST /api/blueprints/{id}/sandbox-evaluate

Purpose: let QA managers/testers run sample recordings or transcripts against the blueprint (draft or published) and see behavior detection and scoring.

Headers: Authorization, optional Idempotency-Key

Request body (choose one of transcript or recording_id):

{
  "mode":"sync|async",                 // sync preferred for transcript-only, async for audio
  "input": {
    "transcript": "full transcript text (optional)",
    "language":"en-US",
    "recording_id":"uuid (optional)",
    "segment_timestamps":[{"start":0,"end":120}] // optional stage mapping hints
  },
  "options": {
    "use_compiled_flow": true,
    "target_stage_ids": ["stage-uuid","..."] // optional limit eval to subset
  }
}


Behavior:

If transcript provided and small (< 20k chars), run synchronous evaluation and return JSON result.

If recording_id provided, create async job: transcribe → evaluate → store results. Respond with 202 and run_id.

Respect sandbox rate limit and token limits.

Success (sync):

200 OK with:

{
  "run_id":"run-uuid",
  "blueprint_id":"uuid",
  "used_compiled_version": "version_number",
  "overall_score": 78,
  "overall_passed": true,
  "requires_human_review": false,
  "confidence": 0.85,
  "stages":[
    {
      "stage_id":"stage-uuid",
      "stage_name":"Verification",
      "stage_score": 60,
      "stage_confidence": 0.72,
      "behaviors":[
        {
          "behavior_id":"behavior-uuid",
          "behavior_name":"Ask for email or phone",
          "satisfied": true,
          "confidence": 0.87,
          "evidence": {"text":"Could I get your email?", "timestamp": 92}
        }
      ],
      "critical_violation": false
    }
  ],
  "llm_prompts": [{"stage_id":"stage-uuid","prompt_text":"..."}], // optional, gated by policy
  "created_at":"..."
}


Success (async):

202 Accepted with run_id. Later fetch result with:
GET /api/blueprints/{id}/sandbox-runs/{run_id} returns same structure when ready.

Errors:

400 invalid input

413 Payload Too Large if transcript too large for sync (use async)

429 Too Many Requests if rate-limited

401/403 auth errors

Security note:

Optionally strip LLM prompts from response for clients without permission to view them. If showing prompts, redact PII.

7) List templates

GET /api/blueprints/templates

Outputs a paginated list of template summaries:

{
  "templates":[
    {"id":"template-uuid","name":"Billing Support","description":"...","preview_stages":[...],"recommended_for":["billing"]},
    ...
  ],
  "pagination": { "page":1, "per_page":20, "total":12 }
}

8) Import legacy templates

POST /api/blueprints/import

Request body includes source_type and payload (legacy format). The endpoint tries to map to one or multiple draft blueprints and returns created drafts with mapping errors/warnings.

Response:

201 Created with list of created blueprint IDs and any warnings for manual review.

Error response format (standardize)

Always return JSON with structured errors:

{
  "status": 400,
  "error_code": "INVALID_PAYLOAD",
  "message": "Validation failed",
  "errors": [
    {"field":"stages[0].behaviors[1].phrases","message":"phrases required for detection_mode exact_phrase"},
    {"field":"stages","message":"At least one stage must exist"}
  ],
  "request_id":"uuid-for-trace"
}

Webhooks (optional)

Companies may register webhooks for blueprint events.

Supported events:

blueprint.published — payload includes blueprint id, version number, compiled_flow_version_id, job_id, status.

blueprint.publish_failed — includes error details.

blueprint.sandbox.run_completed — includes run id and evaluation summary.

Security: HMAC signature header X-Signature computed with company webhook secret.

Operational considerations for implementers
A. Compiler job design

Run publish/compile as idempotent job. Store job_id and status in DB.

Use job retries with exponential backoff. If LLM call fails repeatedly, fail job and include LLM error details in publish_status.

Keep compile logs accessible (for admin view).

On success, persist compiled artifacts mapping and link to blueprint version.

B. Sandbox cost control

Support mode=sync only for transcript-only tests to keep LLM costs predictable.

For audio input, always run async: transcribe → evaluate (avoid blocking HTTP).

Limit sandbox runs per company. Provide quota endpoints and usage metrics.

C. Security: prompt exposure

By default, do not return full LLM prompts in sandbox responses.

Add include_debug flag only for internal admins; log this action in audit.

D. Telemetry

Emit structured events for:

blueprint.created, blueprint.published, compiler.success, compiler.failure, sandbox.run.created, sandbox.run.completed.
Include company_id, blueprint_id, user_id, run_id, duration_ms, llm_tokens.

E. Backwards compatibility

Support legacy flow routing: evaluations may still reference older FlowVersions; do not delete mapping artifacts on recompile.

Examples (quick)

Publish request -> initial validation failed

POST /api/blueprints/{id}/publish returns 400:

{
  "status":400,
  "error_code":"PUBLISH_VALIDATION_FAILED",
  "message":"Blueprint failed validation",
  "errors":[{"field":"stages[1].behaviors","message":"Sum of behavior weights in stage must be > 0"}],
  "request_id":"..."
}


Publish accepted

202 Accepted

{
  "job_id":"job-uuid",
  "status":"queued",
  "links":{"job_status":"/api/blueprints/{id}/publish_status/{job-uuid}"}
}


Sandbox sync success

200 OK with evaluation JSON shown earlier.

Deliverables for integration team (what to implement from this phase)

API routes & controllers for endpoints listed above (contract-compliant).

Request/response validation with clear error messages; implement If-Match ETag for updates.

Background job system (queue) for publish/compiler and async sandbox runs.

Idempotency key handling for publish & sandbox run endpoints.

RBAC enforcement & company scoping.

Webhook subsystem (registration, signing, retries).

Rate-limiter & usage accounting for sandbox runs.

Audit log entries for all mutating actions.

Publish/cancel/recompile controls for admin.

Monitoring/metrics for job durations, failure counts, LLM call rates.