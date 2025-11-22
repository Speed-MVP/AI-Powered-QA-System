PHASE 4 — LLM STAGE EVALUATION (BARE-MINIMUM, COMPLETE SPEC)

Purpose:
Use an LLM only to interpret deterministic evidence and produce stage-level scores & short human-readable feedback. LLM must not discover rules or override critical deterministic violations. The LLM output is structured JSON that downstream scoring consumes.

This document gives your AI coder everything needed to implement Phase 4 with zero guesswork: exact inputs, prompt template, allowed behavior, output schema, scoring calibration, integration, failure modes, and acceptance tests.

1 — High-level constraints (non-negotiable)

Deterministic-first: The LLM must accept DeterministicResult (Phase 3) and treat rule_evaluations as authoritative. Any severity: critical failure forces final overall fail; LLM may explain but cannot negate it.

Stage-aware: LLM evaluates per stage (Opening, Discovery, Resolution, Closing) using only stage transcripts + deterministic evidence for that stage.

JSON only: LLM must return a strict JSON object that exactly matches the schema in Section 4. Any invalid JSON -> reject and fallback to deterministic scoring.

Brevity: Feedback is short, actionable (1–3 sentences per stage).

Deterministic rationale: Every non-trivial claim must cite a rule id or evidence snippet (timestamped) included in the prompt.

2 — Inputs to the LLM (exact payload)

The service will construct and send the following JSON object (or equivalent fields) to the LLM:

evaluation_id (string)

flow_version_id (string)

recording_id (string)

transcript_segments — array of segments for the stage being evaluated (speaker, text, start_time, end_time)

stage_id — id of stage being evaluated (run LLM separately per stage or send all stages in one call; either is acceptable)

flow_stage_definition — the stage object from FlowVersion (steps, step ids, expected_phrases, timing rules)

deterministic_step_results — step_results for this stage from Phase 3 (passed/failed, evidence, timestamps)

deterministic_rule_evaluations — all rule evaluations relevant to this stage

rubric_mapping_hint — which rubric category this stage primarily maps to (e.g., Communication, Accuracy) — short string

evaluation_config — penalty values / discretionary_max_adjustment (see Section 6)

examples — up to 2 short examples showing input → expected JSON output (optional but strongly recommended)

Size rule: If transcript is large, include only segments for that stage plus deterministic evidence snippets for other stages. Do not exceed the LLM token limit; truncate outer context if needed.

3 — Prompt instructions (exact wording template)

Use a system+user structured prompt. Insert the JSON payload where indicated.

SYSTEM:
You are an impartial quality evaluator. Use only the provided deterministic evidence and transcript. Do not invent rule IDs or remove critical violations. Return JSON only and nothing else.

USER (payload):

CONTEXT:
evaluation_id: {evaluation_id}
flow_version_id: {flow_version_id}
stage_id: {stage_id}
flow_stage_definition: {flow_stage_definition}
deterministic_step_results: {deterministic_step_results}
deterministic_rule_evaluations: {deterministic_rule_evaluations}
transcript_segments: {transcript_segments}
rubric_mapping_hint: {rubric_mapping_hint}
evaluation_config: {evaluation_config}

TASK:
1) For this stage, evaluate each step in flow_stage_definition. Use deterministic_step_results to decide PASS/FAIL; if deterministic result exists, cite it. If no deterministic evidence exists for a step that is required, mark it failed and cite 'no evidence'. Do not invent evidence.

2) Assign a numeric stage_score (0-100). Start at 100, subtract deterministic penalties for failed required steps and rule violations according to evaluation_config. You may apply an extra discretionary adjustment up to +/- evaluation_config.discretionary_max (default 10 points) only when clear, evidence-based reasoning applies. For every discretionary adjustment include short rationale and cite transcript timestamp or rule_id.

3) Provide short actionable stage_feedback (1-3 sentences) referencing step IDs and timestamps or rule IDs.

4) Indicate stage_confidence (0-1) expressing how confident you are in the stage_score given available evidence.

5) Output JSON exactly matching the schema. No other text.

IMPORTANT: If any deterministic_rule_evaluations contains severity == "critical" and passed == false, include field `critical_violation=true` and do not set overall pass flag here (overall decision handled downstream). You must not override or nullify a critical failure.

4 — Required LLM output schema (must match exactly)

LLM must return JSON with these fields only:

{
  "evaluation_id": "<string>",
  "flow_version_id": "<string>",
  "recording_id": "<string>",
  "stage_id": "<string>",
  "stage_score": <int 0-100>,
  "step_evaluations": [
    {
      "step_id": "<string>",
      "passed": true|false,
      "evidence": [
        { "type":"transcript_snippet"|"rule_evidence", "text":"...", "start":<s>, "end":<s>, "rule_id":"<id|null>" }
      ],
      "rationale": "<short string citing evidence>"
    }, ...
  ],
  "stage_feedback": [ "<short sentence>", ... ],
  "stage_confidence": <float 0-1>,
  "critical_violation": true|false,
  "notes": "<optional short admin note>"
}


Numeric fields must be integers or floats as specified.

stage_score integer 0–100.

stage_confidence float 0–1.

critical_violation must be true if Phase 3 reported any critical rule failures for this stage.

If JSON fails validation, the service rejects and falls back to deterministic result (see Section 9).

5 — How LLM must use deterministic evidence (rules)

If deterministic_step_results.step.passed == true → LLM must mark that step as passed and cite the deterministic evidence (timestamp/snippet).

If deterministic_step_results.step.passed == false and required == true → LLM must mark as passed=false, include reason 'required_step_missing'.

For any rule_evaluation with passed==false:

If severity == critical → set critical_violation=true; LLM may explain but must not clear it.

If severity == major|minor → include the violation in step rationale and apply deterministic penalty per evaluation_config.

LLM may only add evidence if it exists in transcript segments passed into the prompt. It can rephrase transcript snippets but must include exact quoted text for evidence.

6 — Scoring rules & discretionary adjustment (exact)

Base algorithm (implement in prompt-assisted way):

base = 100

For each failed required step: subtract evaluation_config.penalty_missing_required (default 20)

For each failed major compliance rule in stage: subtract evaluation_config.penalty_major (default 40)

For each failed minor compliance rule in stage: subtract evaluation_config.penalty_minor (default 10)

For each timing violation: subtract evaluation_config.penalty_timing (default 10)

After deterministic penalties, LLM may apply discretionary adjustment ∈ [−discretionary_max, +discretionary_max] (default discretionary_max = 10). Any discretionary adjustment must be explicitly justified in notes with cited evidence.

stage_score = clamp(round(base − sum(penalties) + discretionary_adjustment), 0, 100)

Guidelines on discretionary adjustments:

Allowed only when deterministic checks miss nuance (e.g., agent followed step but phrase variant not in expected_phrases; LLM must cite transcript evidence showing intent).

If discretionary moves contradict deterministic major failures by > 10 points, set stage_confidence low (e.g., ≤ 0.6) and flag for human review downstream.

7 — Stage confidence calculation (LLM to provide)

LLM should compute stage_confidence using:

Coverage of deterministic evidence (fraction of required steps with deterministic detection) — weight 0.6

Transcript clarity (qualitative; use deterministic segment confidence if available) — weight 0.3

Ambiguity due to missing evidence or contradictory evidence reduces confidence — weight 0.1

Express final stage_confidence as float 0–1. If stage_confidence < 0.6, set notes recommending human review.

8 — Practical prompt engineering notes (implementation guidance)

Per-stage calls vs single call: You can call LLM once with all stages or call once per stage. Per-stage calls simplify prompt size and make outputs atomic. Use per-stage if transcript long.

Include short examples: Provide 1–2 concise examples of input → expected JSON to reduce hallucinations.

Limit transcript size: Only send segments for the stage plus deterministic evidence for other stages (if needed).

Enforce JSON output: Use wrapper code to validate LLM output; if invalid, log and fallback.

Model selection: Use model best for structured output and low hallucination (choose model you have). Keep temperature = 0 or near 0.

9 — Failure handling & fallbacks (exact behavior)

If any of the following occurs, the service must use deterministic fallback and mark requires_human_review=true in final evaluation:

LLM returns invalid JSON or missing required fields.

LLM returns stage_confidence < 0.4.

LLM output conflicts with deterministic critical violation (i.e., LLM claims no issue but Phase 3 had critical fail). LLM may explain but must not undo it; if it attempts to, reject.

LLM request times out or errors.

Deterministic fallback output to downstream should be a minimal structure:

{
  "stage_id": "<id>",
  "stage_score": <deterministic_score_for_stage_or_aggregate>,
  "stage_confidence": 0.5,
  "notes": "LLM failed — using deterministic fallback",
  "critical_violation": <true|false>
}


Set requires_human_review=true when fallback used.

10 — Integration contract (how system wires Phase 3 → Phase 4 → Phase 5)

Pipeline calls Phase 3 → gets DeterministicResult.

For each stage in FlowVersion:

Build payload as in Section 2 (stage segments + deterministic evidence).

Call LLM evaluator (Phase 4).

Validate JSON output. If valid, persist llm_stage_evaluations. If invalid or low confidence, use deterministic fallback and persist that.

After all stages processed, aggregate category & overall scores in Phase 5 (Rubric Scoring).

Record which model/version was used in evaluation metadata.

11 — Tests & acceptance criteria (must pass)

Test 1 — Deterministic critical enforcement

Given deterministic rule evaluation lists a critical violation, LLM output must include "critical_violation": true. LLM must not claim that the violation did not occur. If LLM output contradicts, it is rejected.

Test 2 — Required step pass propagation

If Phase 3 reports a required step passed with evidence, LLM must mark step passed=true and include evidence snippet with timestamp.

Test 3 — Stage scoring math

Given deterministic penalties (two missing required steps, one minor rule failed), stage_score = 100 − (2×20 + 10) = 50 (± discretionary up to 10, with clear rationale).

Test 4 — Discretionary adjustment justification

If LLM applies +8 discretionary points, notes must include transcript timestamp and short rationale.

Test 5 — Fallback on invalid JSON

LLM returns gibberish → system must fall back to deterministic_stage_score and flag requires_human_review=true.

Test 6 — Confidence thresholds

LLM returns stage_confidence < 0.4 → fallback to deterministic and human review flagged.

Test 7 — Large transcript handling

For a long stage transcript, LLM call with trimmed segment still returns valid JSON and includes evidence for all step evaluations that have deterministic evidence.

12 — Minimal implementation timeline & resources (guidance)

(1 prompt engineer + 1 backend developer)

Prompt template & schema design: 1 day

Integrate LLM call per-stage, validate outputs: 2 days

Implement fallback and logging: 1 day

Test vectors and acceptance tests: 2 days
Total: ~6 working days

13 — Final notes (blunt)

LLM is used to explain and polish deterministic outputs, not to discover or replace them.

Keep temperature = 0. Use examples. Validate schema on every response. Fall back deterministically on any doubt.

Record the model and prompt version with each evaluation for reproducibility.