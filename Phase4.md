Phase 4 — Blueprint Compiler

Purpose: translate a published QA Blueprint (stages + behaviors) into the existing internal artifacts your 7-phase pipeline consumes (FlowVersion, FlowStages, FlowSteps, ComplianceRules, RubricTemplate, PolicyRulesVersion, RuleEngine metadata). The Compiler must be reliable, idempotent, auditable, transactional when possible, and provide clear error reports so QA managers can fix problems and re-publish.

This phase spec covers:

goals and constraints

inputs & outputs (schemas)

full mapping logic (behavior → internal artifacts)

compiler architecture and components

validation & compile-time checks (what fails and why)

idempotency / concurrency / transaction behavior

error reporting & remediation guidance for users

tests & CI checks for the compiler

observability, metrics, and audit logs

sample compile flow (step-by-step)

deliverables for devs

1 — High-level goals & constraints

One-click publication: When a user publishes a blueprint, the compiler builds all internal artifacts so the pipeline can evaluate calls using the new blueprint automatically.

Non-destructive: Compiler must not overwrite active FlowVersions used by running evaluations; create new FlowVersion(s) and map them.

Idempotent: Re-publishing the same blueprint version (or retrying a failed compile) must not create duplicate artifacts. Use deterministic IDs or mapping table (qa_blueprint_compiler_map) to detect/reuse.

Transactional: Where possible, create artifacts in a single transaction or with rollback strategy so partial failures don’t leave inconsistent mappings. If full DB transactions across microservices are impossible, implement compensation procedures and robust cleanup.

Auditable: Store compiler inputs, decisions, generated artifacts, prompt versions, LLM responses (if used), and job logs in qa_blueprint_versions & qa_blueprint_compiler_map.

Safe by default: For any ambiguous mapping (weights sum mismatch, overlapping phrases, missing behavior types), fail the publish with a human-readable error rather than trying to guess silently. Provide force_normalize_weights option if the user explicitly requests auto-normalization.

2 — Compiler Inputs & Outputs
Inputs

blueprint_version (from qa_blueprint_versions.snapshot) — canonical JSON snapshot at publish time.

compile_options:

generate_policy_rules (bool) — whether to auto-generate structured policy rules via LLM-assisted rule builder (default true).

prompt_version_tag (string) — tag to record prompt version used.

force_normalize_weights (bool) — if true, auto-normalize stage/behavior weights and proceed.

user_id, request_id, company_id (for audit).

Primary outputs (persisted)

flow_version (new entry in flow_versions): top-level FlowVersion used by evaluation pipeline.

flow_stages entries (one per blueprint stage).

flow_steps entries (one per behavior) with expected_phrases (if detection_mode != semantic), step order mapping, timing constraints if any in metadata.

policy_rules_version (optional): structured rules JSON that rule engine consumes (phrase lists, conditional logic, critical rules flagged).

rubric_template & rubric_mappings (represents scoring weights and mapping of steps → rubric categories/stages).

qa_blueprint_compiler_map record linking blueprint_version_id → {flow_version_id, policy_rules_version_id, rubric_template_id} plus timestamp and compiler metadata.

compiler_job_log (detailed log of compile steps, LLM outputs, warnings, errors).

qa_blueprint_versions.compiled_flow_version_id updated on success.

Secondary outputs (returned to API)

job_result: success | failed, compiled IDs, warnings array, errors array, detailed mapping summary for UI preview.

3 — Mapping logic (detailed)

This is the deterministic mapping ruleset the compiler must implement.

3.1 Top-level mapping

Blueprint.name → FlowVersion.name (append blueprint id and version for uniqueness: "{blueprint_name} (bp:{id} v{version})").

Blueprint.metadata.language → set FlowVersion language.

Blueprint.metadata.retention/PII flags → add to FlowVersion policy metadata.

3.2 Stage → FlowStage

For each qa_blueprint_stage:

Create FlowStage with:

name = stage_name

ordering_index = blueprint ordering_index

expected_duration_hint from metadata (if present)

stage_weight copied from blueprint stage_weight (or computed via behavior weights if absent).

Persist stage-level metadata: ui_label, color, sample_window_seconds.

3.3 Behavior → FlowStep + ComplianceRule

For each behavior in stage:

FlowStep (primary):

name = behavior_name

stage_id = mapped FlowStage

ordering_index = ui_order within stage

expected_role = "agent" (unless behavior.metadata.speaker overrides)

expected_phrases = if detection_mode != semantic then phrases list else []

detection_hint = detection_mode (recorded)

metadata includes behavior_type, critical_action, examples, language_hint.

ComplianceRule (secondary):

If behavior_type ∈ {required, forbidden, critical} create one or more ComplianceRule records:

rule_type:

required → required_step or required_phrase depending on detection_mode

forbidden → forbidden_phrase

critical → same as required/forbidden but flagged critical (set severity = critical)

target = FlowStep ID

phrases = expected_phrases (if any)

match_mode = semantic | exact | hybrid

action_on_fail = critical_action (fail_stage/fail_overall/flag)

timing_constraints: if provided in behavior.metadata (e.g., must occur within 15 seconds), add numeric constraint fields.

Notes:

Forbidden behaviors generate rules that, when matched in agent speech, are violations with severity major or critical if flagged.

Optional behaviors may not create compliance rules; they only exist as FlowSteps and scoring entries with weight>0. Optionally create a non-blocking rule if desired (configurable).

3.4 Rubric & Scoring mapping

Goal: produce a RubricTemplate that maps FlowStages & FlowSteps → category scores the scoring engine understands.

Approach:

Each FlowStage becomes a rubric category or maps to an existing rubric category (if company has preferred rubric). Use stage_name as category label.

Category weight = stage_weight normalized to sum to 100 across all stages.

For each behavior in stage, produce RubricMapping:

category_id = stage.category

step_id = FlowStep.id

contribution_weight = behavior.weight normalized within stage.

If behavior weights are not provided or sum to zero:

If force_normalize_weights=true → distribute stage_weight evenly across behaviors and issue warning: auto_normalized_behavior_weights.

Else → fail compile with error BEHAVIOR_WEIGHTS_MISSING.

Rubric output:

rubric_template with categories (stages) and mapping entries (step → weight). Save mapping JSON for scoring engine.

3.5 Policy rules generation (optional, LLM-assisted)

If generate_policy_rules true:

For each behavior marked critical or required, run PolicyRuleBuilder (LLM assisted) to produce formal structured rules:

Convert natural language behavior descriptions into structured rule entries: if/then, phrase lists, timing constraints, exceptions.

Validate generated rules using policy_rules_validator service.

If validation fails, include errors in compiler log and either:

fail compile (strict mode)

or skip rule generation and create basic compliance rules from explicit phrases only (non-strict mode configurable).

Store generated rules in policy_rules_version with generated_by=compiler, prompt_version_tag, and llm_response snapshot (only if company policy permits storing LLM outputs).

3.6 Schema for FlowStep / ComplianceRule / RubricEntry

Define the minimal schema to create internal artifacts. Provide as developer docs (here as conceptual fields; devs will map to exact internal models):

FlowStep

id (UUID)

flow_stage_id

name

ordering_index

expected_phrases (array)

detection_hint

metadata (behavior_type, examples, critical_action)

created_by, created_at

ComplianceRule

id

flow_step_id

rule_type

match_mode

phrases

severity (critical/major/minor)

timing (optional)

action_on_fail

created_by, created_at

RubricTemplate

id

name

categories: [{id, name, weight}]

mappings: [{category_id, flow_step_id, contribution_weight}]

created_by, created_at

4 — Compiler architecture & components

Design the compiler as a service composed of modular components. Implement as a background job invoked by the Publish endpoint.

Components

Publisher Controller (API layer): receives publish request, validates blueprint snapshot, enqueues CompileJob with compile options. Returns job id.

Compile Job Worker (background worker): orchestrates compile phases, retries, and writes logs to job store.

Validator: runs publish-time validations (Phase 2 validations); returns errors/warnings.

Mapper: pure logic mapping blueprint JSON → internal artifact models (FlowStage, FlowStep, ComplianceRule, RubricMapping). Stateless and testable.

Artifact Writer: persists generated artifacts to DB in transactions or via an orchestrated saga (if multi-service). Records mapping entries to qa_blueprint_compiler_map.

PolicyRuleBuilder (optional, LLM service wrapper): generates structured rules for behaviors marked for generation.

SchemaValidator: validates that generated artifacts meet downstream engine schema expectations (e.g., rule engine accepts rule types, rubric weights within 0-100).

Job Logger & Auditor: stores logs, LLM responses, mapping summary, warnings, and errors for UI consumption.

Rollback / Compensator: in case of failure mid-write, runs compensation actions (delete partial artifacts) or marks mapping as partial-failed and produces remediation instructions.

Recommended flow (worker):

Lock blueprint_version (prevent concurrent compiles) — set compiler_job row with status=running.

Run Validator. If failure → mark job failed and return errors.

Run Mapper → produce in-memory artifact objects (FlowStages, FlowSteps, Rules, Rubric).

Run SchemaValidator on produced artifacts. If failure → job failed.

Begin DB transaction (if all artifacts written in same DB): persist artifacts, create flow_version, flow_stages, flow_steps, compliance_rules, rubric_template. Else (microservice architecture), persist via API calls and capture created IDs.

If generate_policy_rules true → call PolicyRuleBuilder for selected behaviors, validate outputs, persist policy_rules_version, update compliance_rules references.

Create qa_blueprint_compiler_map mapping blueprint_version_id → artifact IDs; create qa_blueprint_versions.compiled_flow_version_id update.

Mark job success, store compiler_job_log and return result.

If any non-recoverable error occurs during persistence, run Compensator: remove created artifacts and mark job failed with full logs. If deletion fails, mark mapping with partial_failure and provide list for manual cleanup.

5 — Validation & compile-time checks (explicit list)

Compiler must run the following checks and fail with explicit error codes/messages if conditions not met. Do NOT silently patch unless force_normalize_weights=true.

Structural checks

Blueprint contains ≥1 stage. Error: NO_STAGES.

Each stage contains ≥1 behavior. Error: NO_BEHAVIORS_IN_STAGE:{stage_name}.

Unique stage names within blueprint. Error: DUPLICATE_STAGE_NAME:{stage_name}.

Unique behavior names within stage. Error: DUPLICATE_BEHAVIOR_NAME:{behavior_name}.

Each behavior weight >= 0. Error: INVALID_BEHAVIOR_WEIGHT:{behavior_name}.

If stage_weight specified, sum(stage_weights) must equal 100 (tolerance 0.01) unless force_normalize_weights true. Error: STAGE_WEIGHTS_MISMATCH.

For each stage, sum(behavior.weights) > 0 unless force_normalize_weights=true. Error: BEHAVIOR_WEIGHTS_MISSING:{stage_name}.

For behaviors with detection_mode != semantic, phrases must be present and each phrase length <= configured limit. Error: MISSING_PHRASES:{behavior_name}.

No conflicting critical rules (two behaviors both critical with contradictory critical_action across same stage?) — warn not fail. Warning: POTENTIAL_CRITICAL_CONFLICT.

Phrase list duplicates across behaviors should be warned but allowed. Warning: DUPLICATE_PHRASE.

Forbidden phrase that matches required phrase in same stage → fail (contradiction). Error: CONTRADICTORY_RULES:{phrase}.

Semantic checks

If the blueprint language is unsupported by the default LLM model, warn and set requires_human_review by default. Warning: UNSUPPORTED_LANGUAGE:{lang}.

Policy rule generation checks

LLM generation must pass policy_rules_validator. If LLM fails N times (configurable, default 1) return error: POLICY_RULE_GEN_FAILED with LLM error details.

6 — Idempotency, concurrency, transactions
Idempotency

Use deterministic resource naming: when compiler creates flow_version for blueprint_version_id, derive a stable external_id (e.g., flow-bp-{blueprint_version_id}) so retries detect existing artifacts.

Store qa_blueprint_compiler_map keyed by blueprint_version_id. If mapping exists and artifact IDs are present with status succeeded, return success with those IDs. If mapping exists with status failed or partial, allow recompile only if force=true or after manual cleanup.

Concurrency

Acquire a compile lock on blueprint_version_id (db row lock or distributed lock). Reject concurrent publish attempts with 409 and return active job_id.

Use optimistic concurrency for artifact updates where possible.

Transactions & Compensation

If your artifacts are in one DB, wrap persistence in a DB transaction and commit at end.

If artifacts span services (e.g., FlowService, RuleService, RubricService), implement a Saga pattern:

Persist orchestrator state in compiler_job table (list of actions and their compensating actions).

On failure, run compensating actions in reverse order to remove created artifacts.

Mark job as partial_failure and surface compensation results.

7 — Error reporting & remediation UX (what to show QA manager)

When a compile job fails, return structured errors grouped into:

Critical Errors — prevent publish (e.g., missing behaviors, contradictory rules). Show user-friendly message and link to blueprint editor with highlighted fields to fix.

Warnings — non-blocking (e.g., duplicate phrase lists). Show toast and include "Proceed anyway" option via force_normalize_weights or force_publish for admins.

Generation Errors — for LLM-based rule gen: show LLM error summary and try again button. If company policy forbids storing LLM output, show suggestion to manually enter rules.

Example failure payload:

{
  "job_id":"job-uuid",
  "status":"failed",
  "errors":[
    {"code":"BEHAVIOR_WEIGHTS_MISSING","message":"Stage 'Verification' has all behavior weights = 0. Provide weights or enable force_normalize_weights."},
    {"code":"CONTRADICTORY_RULES","message":"Behavior 'Tell caller call is recorded' marked required and forbidden in same blueprint."}
  ],
  "warnings":[
    {"code":"DUPLICATE_PHRASE", "message":"Phrase 'this call is recorded' appears in 2 behaviors."}
  ],
  "remediation":[
    {"field":"stages[2].behaviors[1].weight","action":"set_weight","suggested_value":10},
    {"field":"stages[0].behaviors[3]","action":"open_editor","suggested_note":"Check phrase duplication"}
  ]
}


UI should:

Link errors to the exact behavior/stage editors

Provide quick-fix suggestions (auto-fill weight normalization with explicit confirm)

Allow re-run compile after fixes

Allow download of compiler log for audit/troubleshooting

8 — Tests & CI checks (must be implemented)
Unit tests (Mapper & Validator)

Mapping correctness tests for:

stage → flowStage mapping, including ordering & weights

behavior → flowStep mapping for all detection modes (semantic/exact/hybrid)

compliance rule generation for required/forbidden/critical behaviors

rubric mappings normalization when behavior weights sum to >0 or ==0

Validator tests for each validation rule (positive & negative cases)

Integration tests (Compiler end-to-end)

Happy path: publish a simple blueprint, compiler produces FlowVersion + FlowSteps + Rules + RubricTemplate; DB mapping table populated; publish status succeeded.

LLM rule generation path: mock LLM responses (stable), validate policy_rules_version persisted; test LLM failure fallback.

Failure & compensation: simulate persistence failure halfway; ensure compensator removes created artifacts and mapping marked failed.

Idempotency: re-run compile with same blueprint_version_id and confirm no duplicates created.

E2E tests (full system)

Publish blueprint + run sample evaluation via sandbox; check that pipeline uses compiled artifacts and evaluation results align with expected behavior outputs.

Migration import scenarios: import legacy template → produce draft blueprint → publish → check mapping.

Schema tests

Validate generated policy_rules_version against rule engine JSON schema (existing validator).

Security tests

Ensure phrases with potential injection characters are sanitized & rejected when matching validation rules.

Ensure LLM outputs are sanitized before storing when company policy prohibits storage.

9 — Observability & metrics

Emit structured telemetry per compile job:

compiler_job_started, compiler_job_step_completed events with durations

compiler_job_succeeded, compiler_job_failed with error codes

LLM tokens consumed (if used) per job

Number of warnings vs critical errors per compile

Time to compile (median, p95)

Number of compensating actions executed

Expose internal metrics dashboard (Grafana):

compile success rate

average compile time

top failure reasons

compile queue length

LLM error rates

Store human-readable compile logs (linked to job_id) for debugging and compliance.

10 — Audit & provenance

For compliance and reproducibility, persist:

qa_blueprint_versions.snapshot (already stored)

compiler_job record: job_id, blueprint_version_id, user_id, start_ts, end_ts, status, compiled artifact IDs (flow_version_id etc.), options used (prompt_version_tag, generate_policy_rules flag), warnings, errors.

If LLM used: store prompt_version_tag, prompt text (if permitted), truncated llm_response, llm model/version, and decision trace (why rule was generated). Keep LLM raw outputs gated by company policy.

qa_blueprint_compiler_map mapping records.

Link compile job id to audit log audit_logs entry for publish action.

11 — Sample compile scenario (step-by-step)

Input: published blueprint bp-123:v2 with stages Opening (20), Verification (30), Resolution (40), Closing (10). Behaviors include two criticals, some exact phrases, others semantic.

User clicks Publish → API POST /api/blueprints/{id}/publish enqueues compile job job-987.

Worker picks job-987, locks bp-123:v2.

Validator checks that stage weights sum to 100 — OK. Behavior weights present — OK.

Mapper creates in-memory artifacts:

FlowStage A,B,C,D with ordering, weights.

FlowStep entries per behavior with expected_phrases where provided.

ComplianceRule entries for required/forbidden/critical behaviors.

RubricTemplate R with categories A..D and mapping step → contribution_weight.

SchemaValidator validates the produced artifacts meet downstream schemas.

Begin persistence transaction:

Create FlowVersion flow-555.

Insert FlowStages, FlowSteps, ComplianceRules, RubricTemplate.

generate_policy_rules true → for 3 critical behaviors call PolicyRuleBuilder:

LLM returns structured rule JSON for each; policy_rules_validator approves.

Persist policy_rules_version id prv-22.

Commit transaction.

Create qa_blueprint_compiler_map linking bp-123:v2 → flow-555, prv-22, rubric-R.

Mark qa_blueprint_versions.compiled_flow_version_id = flow-555.

Mark job success; return compiled IDs to API; emit blueprint.published webhook.

12 — Deliverables for devs (exact list)

Compiler design document (this phase) — include mapping tables, flow diagrams showing relationships.

Compile job worker implementation and job schema in DB.

Mapper module with unit tests (pure function mapping JSON → artifact objects).

Validator module implementing all compile validations and producing machine-readable errors.

Artifact Writer with transaction/compensator logic.

PolicyRuleBuilder integration (LLM wrapper) with retry/backoff and validation.

SchemaValidator to assert compiled artifacts conform to downstream schemas.

Job logging & audit persistence.

Rollback / compensator scripts (automated) and admin manual cleanup tool.

Integration tests & CI for idempotency, failure/retry, and e2e compile.

Operational docs on compile job monitoring & remediation steps.

UI hooks: publish_status endpoint, job logs access, remediation links.

13 — Remediation & operator checklist (when compile fails)

For each common failure, provide operator steps:

BEHAVIOR_WEIGHTS_MISSING → open blueprint editor, set behavior weights or re-run publish with force_normalize_weights=true.

CONTRADICTORY_RULES → identify behaviors with conflicting phrases; either edit behavior or split into separate stages or change type to optional.

POLICY_RULE_GEN_FAILED → inspect LLM logs; if temporary, retry; if persistent, ask user to manually craft rule or disable auto-generation.

ARTIFACT_PERSIST_FAIL → check DB health; run compensator; examine job log for partial artifacts and remove if needed; re-run compile.

LLM_THROTTLE → backoff and retry; notify admins; optionally fall back to deterministic rules only.

Provide links to the exact UI editors to fix the issue.

14 — Security & privacy notes (compiler-specific)

When storing LLM responses, ensure company privacy policy allows it. If not, redact or omit LLM raw responses and store only hashes / derived structured rule outputs.

Limit phrase lists length and content to avoid exposing secrets in prompts; sanitize phrases and forbid full-sensitive identifiers (account numbers).

Ensure compiler job role has restricted IAM/DB permissions; store job logs in secure storage with access controls.

15 — Acceptance criteria (how to know compiler is done)

Given a valid blueprint JSON, compiler creates flow_version, flow_stages, flow_steps, compliance_rules, and rubric_template and persists qa_blueprint_compiler_map (automated tests verify mapping).

Re-running the compiler for same blueprint_version_id either returns existing mapping (idempotent) or updates mapping when force_recompile=true.

System returns clear, actionable errors for each validation failure.

Generated artifacts pass schema validation and downstream scoring pipeline accepts them and produces evaluations in sandbox tests.

All created artifacts are auditable with job logs, LLM prompt versions, and mapping table entries.

CI includes unit, integration, and e2e compile tests passing.