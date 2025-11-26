Phase 6 — Stage LLM Evaluation Engine (Prompting, Privacy, Schema, Reliability)

Purpose: evaluate each stage in the compiled FlowVersion using an LLM to produce structured, human-interpretable stage evaluations (behavior satisfaction, stage score, confidence, evidence, feedback). This layer performs contextual understanding that semantics/embedding detection cannot fully capture: nuances, partial satisfaction, multi-step reasoning, tone, resolution quality. It must be deterministic, auditable, reproducible, and safe (PII-redacted).

This phase spec contains: prompt design rules, PII handling, context windowing, JSON schema and validation, failure/fallback policies, hallucination mitigation, reproducibility controls, metrics/monitoring, operational guidance, test cases, and developer deliverables.

1 — High-level design constraints

Temperature = 0 (deterministic).

Short, stage-scoped prompts only (reduce token cost and error surface).

PII must be redacted prior to prompt assembly. Redaction policy configurable per-company.

Strict JSON output required; responses validated against schema with strong rejection and retry policies.

Prompt versions must be versioned and stored for audit (prompt_version_tag).

Retries limited: 1 retry for transient failures or schema-parsing errors; then fallback to deterministic results.

Zero-data-retention mode honored for companies that require it (do not persist LLM raw response; store only structured evaluation).

SchemaValidator enforces types and value ranges; out-of-spec = failure.

Explainability: include evidence (timestamps, utterance snippets) for every behavior decision.

Cost control: limit tokens per stage; compress transcript where needed.

2 — Inputs to Stage LLM Evaluator

For each stage evaluation call provide only what’s necessary:

stage_descriptor:

stage_id, stage_name, objective (1-sentence), stage_weight

behaviors_list:

List of behaviors for this stage: {behavior_id, behavior_name, behavior_type, detection_mode, phrases(if any), behavior_weight, critical_action, short_description}

deterministic_results (optional but recommended):

From detection engine (exact/hybrid/semantic pre-hits): per-behavior candidate hits and their evidence. This speeds LLM decision and increases reliability.

stage_transcript:

Speaker-tagged, PII-redacted transcript segment for the stage (compressed/summarized if too long) with timestamps and per-utterance confidence.

company_policy_snippets (optional, small): only relevant policy lines if RAG is enabled (limit size).

runtime_parameters:

model (e.g., Gemini-2-Flash), temperature:0, max_tokens_per_stage, prompt_version_tag, evaluation_seed (deterministic seed if used).

Do NOT include full company policy documents, entire conversation transcripts beyond stage, or raw PII.

3 — Prompt Construction Rules (keep prompts minimal, deterministic)
Prompt structure (ordered)

System instruction (single line): role + constraints.

Example: You are an objective QA evaluator. Return strict JSON only, exactly matching the provided schema. No extra commentary. Temperature=0.

Stage objective (1–2 lines).

Behavior list (compact bullet list) with weights and detection hints.

Deterministic pre-hits: present a short table of pre-matched evidence per behavior (if available).

Transcript excerpt: redacted, compressed to token budget; include utterance timestamps and speaker labels.

Explicit instructions:

How to determine satisfaction (define criteria in 1–2 short rules per behavior).

When to mark partial or uncertain (confidence thresholds).

critical actions handling (set critical_violation=true).

Response format: exact JSON schema to output. Example response snippet included.

Final instruction: Return only JSON. If you cannot decide, set satisfied=false and confidence=<0.5>.

Prompt size & compression

Target per-stage token budget: 1,000–3,000 tokens depending on model and company cost profile.

If transcript long: use TranscriptCompressor to produce a short summary + excerpt that contains candidate evidence utterances only.

4 — PII Redaction & Data Safety
Redaction policy (must run before prompt)

Detect and redact: names, emails, phone numbers, account numbers, SSNs, addresses, credit card numbers, dates of birth, and any sensitive identifiers using deterministic regex + NER.

Replace with typed placeholders: [NAME], [EMAIL], [PHONE], [ACCOUNT_NUMBER] — keep mapping in ephemeral job context (not persisted unless policy allows).

For zero-data-retention companies: do not store redacted transcript or LLM raw output. Store only evaluation JSON.

Redaction steps

Apply regex filters first (fast).

Apply NER model to catch names and less-structured PII.

Mask PCI/BANK patterns strictly; if found in phrases used for exact detection, raise a warning to admin and require manual review before publish.

Record redaction log per run (FIELDS redacted count) for audit.

5 — Context Windowing & Transcript Compression
Stage extraction

Use FlowStage sample_window metadata if available. Otherwise derive window using deterministic rule:

Stage start = first agent utterance after previous stage end.

Stage end = when next stage begins or last agent utterance in window.

If stage transcript > token budget:

Run TranscriptCompressor producing:

Short summary (one-line)

Extracted candidate utterances (only those with pre-detected matches or high semantic similarity to behaviors)

Timestamps for each extracted utterance

Provide compressor output in prompt (summary then extracted utterances).

Compression must not remove candidate evidence.

6 — JSON Output Schema (strict) — StageEvaluation

LLM must return exactly this JSON object. Backend enforces schema validation. Any deviation triggers retry/fallback.

{
  "stage_id":"<uuid>",
  "stage_score": <0-100 integer>,
  "stage_confidence": <0.0-1.0 float>,
  "critical_violation": <true|false>,
  "behaviors":[
    {
      "behavior_id":"<uuid>",
      "satisfied": <true|false>,
      "satisfaction_level":"full|partial|none",
      "confidence": <0.0-1.0>,
      "match_type":"semantic|exact|hybrid|none",
      "evidence":[
        {"text":"...","start_time":12.3,"end_time":13.1,"speaker":"agent","source":"transcript|prehit"}
      ],
      "notes": "short string (<=250 chars) - optional"
    }
  ],
  "stage_feedback":"string (<=1000 chars) - optional",
  "debug": {
    "prompt_version": "v1.2",
    "model_version":"gemini-2.0",
    "llm_raw_hash":"sha256:...",
    "llm_tokens_used":123
  }
}


Strict rules:

No extra top-level fields beyond those in schema.

stage_score must be integer 0–100.

stage_confidence float 0.0–1.0.

behaviors array must contain an entry for each behavior provided in the prompt (order preserved).

Each behavior must include behavior_id, satisfied, and confidence. Evidence array may be empty but must be present.

7 — Schema Validation & Retry Policy

Validate JSON with server-side SchemaValidator immediately on response.

If schema OK and stage_confidence >= confidence_threshold (configurable default 0.5): accept.

If schema OK but stage_confidence < lower_threshold (0.3): mark as low-confidence and route to human review. Persist structured output.

If schema invalid:

Retry once with appended instruction: You must return EXACT JSON, no explanation. (include same prompt_version_tag)

If retry fails or returns invalid again, fallback to deterministic results (detection engine outputs) and mark stage_confidence low; record failure in compile logs; route to human review.

If LLM returns hallucinated or contradictory evidence (e.g., evidence timestamps out of transcript bounds), catch as schema+sanity-check failure → retry/fallback.

8 — Hallucination Guards & Sanity Checks

After JSON returned and before acceptance perform these sanity checks:

Evidence alignment: each evidence.timestamp must exist within transcript duration and correspond to agent utterance in diarization metadata. If mismatch → mark that item suspicious and reduce confidence by penalty (e.g., -0.2) or fail schema.

Behavior coverage check: ensure every behavior is present in result (no dropped behaviors). Missing → schema error.

Consistency checks: if satisfied=true for a behavior but evidence empty and match_type=semantic with confidence > 0.9 → flag for manual review (possible hallucination).

Score-range sanity: computed stage_score must be consistent with per-behavior weights (± small tolerance). If inconsistent by >10 points, treat as anomaly, record warning, and optionally recompute stage_score deterministically from behavior satisfaction.

No extraneous text: ensure output is pure JSON (no leading/trailing commentary).

If any sanity check fails, run retry. If retry fails, fallback to deterministic evaluation with stage_confidence reduced and stage_feedback set to "LLM failure — fallback used".

9 — Reproducibility & Determinism

Prompt versioning: store prompt_version_tag used and include in debug. Prompts should be immutable once published for a given blueprint version to ensure reproducibility.

Model metadata: store model name/version, temperature, and seeds (if model supports seed) with evaluation.

Evaluation seed: optionally compute a deterministic evaluation_seed = sha256(blueprint_version_id + recording_id + stage_id) and include in prompt for any nondeterministic model features.

LLM raw hash: store hash of raw LLM response (if allowed). This allows re-checking for drift or later re-evaluations.

Immutable snapshots: for compliance, store stage_transcript snapshot used and deterministic_results input (or hashes) linked to evaluation record.

10 — Failure & Fallback Strategies

Transient LLM/network error

Retry once with exponential backoff; if fails, fallback to deterministic detection-only result and flag evaluation requires_human_review.

Schema parse failure

Retry once with stricter JSON-only instruction; if fails, fallback to deterministic results and mark low confidence.

Low confidence (<0.3)

Flag for human review. Persist LLM output for training/analysis.

Hallucination detected via sanity checks

Fallback to deterministic detection; store LLM output as "rejected" for analysis.

Deterministic fallback

Compute stage_score from detection engine; set stage_confidence = min(0.5, detection_engine_confidence). Add stage_feedback: "Fallback deterministic evaluation used".

Human review queueing

All fallback/low-confidence/critical-violation cases generate human_review entries with AI snapshot included for side-by-side review.

11 — Confidence calibration & combining with deterministic signals

Stage confidence = weighted aggregation:

0.6 * llm_stage_confidence (if LLM result accepted)

0.3 * detection_engine_confidence

0.1 * transcript_quality (Deepgram avg confidence)

Calibrate thresholds per-company during pilot: default require re-view if overall confidence < 0.5 or any critical_violation present.

12 — Logging, Monitoring & Metrics

Emit structured telemetry per stage evaluation:

stage_eval.request_id, company_id, blueprint_id, stage_id, model_version, prompt_version_tag, llm_tokens_used, status (success|fallback|failed|retry), stage_confidence, latency_ms.
Track aggregated metrics:

schema validation failure rate (target < 0.5%)

hallucination detection rate

fallback frequency

avg tokens per stage & cost per evaluation

per-model error rates

Store example failed LLM outputs (redacted) for retraining and prompt improvements.

13 — Testing & QA (must-do tests)

Unit & integration tests:

Prompt-to-schema positive test: known transcripts produce exact JSON matching expected values.

Schema-negative tests: ensure invalid responses trigger retry/fallback.

Hallucination tests: fabricated LLM outputs with fake timestamps must be caught.

Deterministic fallback test: simulate LLM outage and confirm deterministic path used.

Reproducibility test: same inputs + prompt_version produce identical outputs (within acceptable deterministic model variance).

Edge tests: long transcripts (compression), multilingual detection, zero-data-retention behavior (no raw LLM stored).

Human-in-the-loop tests:

UX shows LLM evidence and allows reviewer correction; corrected outputs go to training dataset.

14 — Deliverables for devs

Prompt templates (stage-level) with placeholder variables and examples for each behavior type.

Prompt versioning implementation guide and storage plan.

PII redaction module spec (regex + NER + audit log).

TranscriptCompressor rules & library selection.

SchemaValidator code spec with sample schema JSON (stage evaluation schema).

Retry & fallback workflow implementation spec (state machine for retry, fallback, human queue).

Debug & audit logging format and storage.

Test suite: unit/integration/E2E tests for the evaluator.

Monitoring dashboards (metrics to track) and alerts (schema failure rate > X, fallback rate > Y).

Cost-control policy: per-company token caps and sandbox throttle.

Sample transcripts + expected stage JSON test set (for CI).

15 — Improvement strategies (post-launch tuning)

Calibration experiments: collect human-reviewed evaluations, compute precision/recall per behavior, tune LLM prompt wording and confidence aggregation.

Prompt A/B testing: evaluate small prompt variations and measure schema pass rate and accuracy vs human ground truth. Version best-performing prompt as prompt_version_tag.

Active learning: pick borderline cases (confidence 0.4–0.6) for human labeling and incorporate into retraining and prompt improvement.

RAG tuning: for policy-heavy blueprints, selectively include policy snippets relevant to behaviors (limit token cost).

Behavior-level thresholds: allow per-behavior confidence thresholds for auto-pass vs human-review.

Model selection: route easy stages to cheaper models (embedding+rules), complex stages to stronger models (Gemini Pro) based on a complexity heuristic.

Feedback loop: feed human corrections into policy_rules_builder and detection engine to reduce repeated errors.

16 — Acceptance criteria

LLM stage evaluator produces valid JSON for >99% of accepted calls in pilot.

Schema validation failure rate <0.5% after initial tuning.

Fallback frequency <5% for supported languages and good-quality transcripts.

Human-review queue <10% of evaluated calls after calibration.

Logs sufficient to reproduce any evaluation (prompt_version, model_version, transcript snapshot or hash).