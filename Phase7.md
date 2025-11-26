Phase 7 — Scoring Engine (Aggregation, Pass/Fail, Penalties, Confidence, Audit)

Purpose: turn per-behavior detections and stage LLM evaluations into deterministic, auditable numeric scores and pass/fail decisions. This layer must be transparent, explainable, and tolerant of LLM/detection uncertainty while enforcing critical compliance rules.

1 — High-level design goals

Deterministic, reproducible math.

Critical violations override scoring (configurable auto-fail semantics).

Support partial satisfaction and fractional scoring.

Confidence-aware: low-confidence signals push for human review rather than silently change scores.

Penalties from compliance rules are explicitly visible and reversible.

Produce a single canonical evaluation record with full audit snapshot for every call.

2 — Inputs to scoring engine

llm_stage_evaluations[] — LLM per-stage outputs (stage_score 0–100, stage_confidence 0–1, behaviors with satisfied/partial/none and per-behavior confidence).

detection_engine_results — exact/semantic pre-hits and evidence.

compiled_rubric — stage weights (percent of total), behavior contribution weights within stage.

policy_rule_results — deterministic rule hits, violations (severity: critical/major/minor), penalties.

company_scoring_config — thresholds, penalty rules, confidence thresholds, preset weighting profile.

human_overrides (if available) — human adjustments applied post-hoc.

3 — Core scoring algorithm (step-by-step)
Step A — Normalize weights

Ensure Σ(stage_weight) = 100% (if not, normalize proportionally).

For each stage, ensure Σ(behavior_contribution_weight) = stage_weight (normalize within stage if necessary, or fail earlier at compile time).

Step B — Per-behavior numeric score

Define numeric mapping for satisfaction_level:

full → 1.0

partial → 0.5 (configurable)

none → 0.0

Per-behavior raw score:

behavior_raw_score = behavior_contribution_weight * satisfaction_multiplier


(where behavior_contribution_weight is expressed as percentage of overall score, e.g., 7.5 means 7.5 points of overall 100)

If LLM/detection reports fractional satisfaction (e.g., 0.7), use that directly instead of fixed multiplier.

Step C — Behavior confidence adjustment (optional)

Optionally discount behavior_raw_score by behavior-level confidence when enable_confidence_weighting=true:

behavior_effective_score = behavior_raw_score * (alpha + (1 - alpha) * behavior_confidence)


Where alpha is a floor (e.g., 0.6) to prevent tiny confidences from zeroing-out scores entirely. Example: alpha=0.6, confidence=0.8 → multiplier = 0.6 + 0.4*0.8 = 0.92.

Make alpha company-configurable; default 0.6.

Step D — Stage score aggregation

Stage effective score = Σ(behavior_effective_score for behaviors in stage).

Round stage score to integer or keep float until final aggregation.

Also compute stage_confidence = weighted average of behavior confidences weighted by behavior_contribution_weight.

Step E — Apply deterministic rule penalties

For each rule violation in policy_rule_results apply penalty per rule definition:

critical → apply critical_action (auto-fail stage or overall) immediately (see Section 5).

major → subtract fixed penalty points (e.g., 10 points) or percentage (configurable).

minor → subtract small points (e.g., 2–5).

Penalties are additive but clamped to not reduce below 0.

Keep a penalty_breakdown[] with {rule_id, severity, penalty_points, reason}.

Step F — Overall score calculation

Overall score (before final clamp):

overall_score = Σ(stage_effective_score) - total_penalties


Because stage_effective_score already uses absolute contribution (sum of stage weights = 100), overall_score is on 0–100 scale.

Clamp to [0,100]. Round to nearest integer for UI but store float for audits.

Step G — Pass/fail logic

Critical override: if any critical violation exists with critical_action == fail_overall → overall_passed = false (regardless of numeric score). Mark failure_reason = critical_violation.

Category/Stage thresholds: each stage may have a pass threshold (optional). If any stage score < stage_threshold and stage_threshold_enforced=true → overall_passed=false.

Overall threshold: default overall_threshold = company_config.overall_pass_threshold (e.g., 70). If overall_score < overall_threshold → overall_passed=false.

Human override: reviewer can mark overall_passed true/false — record in audit and set human_override=true.

Step H — Requires human review flag

Set requires_human_review = true if any of:

any critical violation occurred (for manual confirmation)

overall or any stage confidence < company_config.human_review_confidence_threshold (default 0.5)

fallback used for any stage (LLM failed and deterministic fallback used)

explicit QA rule (e.g., important accounts)

4 — Confidence-weighted scoring (alternative mode)

For companies that prefer confidence-weighted scoring as primary (not just gating), compute:

weighted_stage_score = stage_score * stage_confidence
overall_score = Σ(weighted_stage_score)


This reduces numeric scores for low-confidence evaluations and helps route to review automatically. Use cautiously because it changes business interpretation of scores; expose as opt-in profile only.

5 — Critical violations & their semantics

Critical behaviors can be configured per-behavior to:

fail_stage: the stage is marked failed; stage_score = 0 (or stage_penalty applied); overall pass may still be possible depending on company rules.

fail_overall: immediate overall fail regardless of points. Still compute numeric score, but overall_passed=false.

flag_only: treat as high-priority human review but do not auto-fail.

When a critical violation happens:

Add entry to policy_violations table with severity critical, evidence, timestamps, and rule id.

Create a human_review record with priority = high.

6 — Penalty mechanics (explicit)

Penalty types: points, percentage, reduction_to_zero (for extreme cases).

Penalty precedence: critical rules applied first, then major, then minor.

Sample: major penalty = 10 points; minor = 3 points. These default values must be configurable per-company and per-rule.

Penalties applied to overall score after stage aggregation. Provide penalty_source mapping so UI can show “-10 (major violation: disclosure missing)”.

7 — Human review integration & reconciliation

When human reviewer edits behavior satisfaction or scores:

Save human_review record with human_scores, human_violations, reviewer_notes, reviewer_id, timestamps.

Compute delta = ai_scores - human_scores per behavior and stage and overall.

Save training_example (input transcript slice, AI output, human corrected output, metadata) for future model fine-tuning.

Update evaluation.final fields with human data and mark status=reviewed.

8 — Audit snapshot structure (persist each evaluation)

Every evaluation must store an immutable snapshot for compliance:

evaluation_record includes:

id, recording_id, blueprint_id, blueprint_version, compiled_flow_version_id

transcript_hash and optionally transcript_snapshot (redacted)

deterministic_results (JSON)

llm_stage_evaluations (JSON) — per-stage LLM responses and debug metadata (prompt_version, model_version, tokens) unless company forbids LLM storage

scoring_snapshot (JSON) containing:

per_behavior: {behavior_id, behavior_name, raw_score, effective_score, confidence, evidence}

per_stage: {stage_id, stage_score, stage_confidence, penalties}

overall_score, total_penalties, overall_passed, requires_human_review

policy_violations array with evidence and severity

created_at, evaluated_by (system), human_review_id (if any)

Store as evaluations.final_evaluation JSONB and also normalized fields for quick queries: overall_score, overall_passed, requires_human_review, confidence_score.

9 — API output (evaluation result example)

GET /api/evaluations/{recording_id} returns:

{
  "evaluation_id": "uuid",
  "recording_id": "uuid",
  "blueprint_id": "uuid",
  "overall_score": 76,
  "total_penalties": 10,
  "overall_passed": false,
  "requires_human_review": true,
  "confidence_score": 0.63,
  "stage_scores": [
    {"stage_id":"s1","name":"Opening","score":18,"weight":20,"confidence":0.9},
    {"stage_id":"s2","name":"Verification","score":26,"weight":30,"confidence":0.7},
    {"stage_id":"s3","name":"Resolution","score":32,"weight":50,"confidence":0.55}
  ],
  "policy_violations": [
    {"rule_id":"r-1","severity":"major","description":"Disclosure missing","penalty_points":10,"evidence":[...]}
  ],
  "created_at":"2025-11-24T...",
  "links":{"human_review":"/api/human_reviews/{id}"}
}

10 — Examples (calculated carefully)
Example input

Stages & stage weights:

Opening = 20

Verification = 30

Resolution = 50
Behavior contributions (overall points):

Opening: Greeting 5, Disclosure 15 (sum 20)

Verification: Ask name 10, Ask email 20 (sum 30)

Resolution: Diagnose 20, Provide solution 20, Confirm next step 10 (sum 50)

LLM/detection results:

Greeting = full (1.0), confidence 0.9 → score = 5 * 1.0 * conf-adjust (alpha=0.6) → multiplier=0.6+0.4*0.9=0.96 → effective = 5 * 0.96 = 4.8

Disclosure = none, confidence 0.0 → effective = 15 * (0.6 + 0.40.0)=150.6=9.0 (this is a design choice — using alpha floor; but critical behavior likely fail_overall. If Disclosure is critical with fail_overall → immediate overall fail; see below.)

Ask name = full, confidence 0.85 → multiplier=0.6+0.40.85=0.94 → 100.94=9.4

Ask email = partial (0.5), confidence 0.7 → partial multiplier=0.5 → raw=200.5=10 → conf-adjust multiplier=0.6+0.40.7=0.88 → effective = 10 * 0.88 = 8.8

Diagnose = full 20 1.0mult=20*0.96=19.2

Provide solution = full 20 1.00.96=19.2

Confirm next step = none 0 → effective = 10 * 0.6 = 6.0

Now stage sums:

Opening = 4.8 + 9.0 = 13.8 (of 20)

Verification = 9.4 + 8.8 = 18.2 (of 30)

Resolution = 19.2 + 19.2 + 6.0 = 44.4 (of 50)

Overall before penalties = 13.8 + 18.2 + 44.4 = 76.4 → round to 76.

If Disclosure was critical with fail_overall, overall_passed = false despite numeric 76. If Disclosure just major violation (penalty 10 points), apply penalty: 76.4 - 10 = 66.4 → round 66 → overall_passed false if threshold 70.

(These numbers are illustrative; devs should implement deterministic math exactly as above and store floats before rounding.)

11 — Tests & validation (must implement)

Unit tests for:

weight normalization

behavior raw → effective score with various confidences and alpha values

penalty application order and clamping

critical override behavior

Integration tests:

pipeline end-to-end: transcript → detection → LLM per-stage → scoring → expected overall_score & requires_human_review

sanity tests where LLM gives impossible evidence (sanity checks must cause fallback and review)

Regression tests:

store canonical evaluation inputs and expected outputs to catch accidental scoring drift.

Human review simulation:

test delta computation and training-data creation.

12 — Monitoring & Key Metrics

avg_overall_score per company / team

percentage_of_calls_auto_passing

human_review_rate (target < X%)

critical_violation_rate

avg_penalty_points_per_call

score_drift (AI vs human averaged delta over time)

scoring_time_ms per evaluation

Set alerts on sudden change in human_review_rate or score_drift.

13 — Deliverables for devs

Scoring engine module with clear interfaces: compute_evaluation(deterministic_results, llm_stage_evaluations, compiled_rubric, policy_rule_results, config) → returns final_evaluation snapshot.

Config schema for company-level scoring (alpha, thresholds, penalty defaults, overall_threshold, enable_confidence_weighting).

Unit & integration tests (including the numeric example above).

DB update logic to persist evaluations JSONB and normalized fields.

API contract update for GET /api/evaluations/{recording_id} including penalty breakdown and audit links.

Dashboard queries & precomputed aggregates for monitoring.

Documentation for QA managers: how scores computed, what critical means, how to tune weights and thresholds.

14 — Operational notes & best practices

Use conservative default settings: alpha=0.6, overall_threshold=70, human_review_confidence_threshold=0.5.

Encourage customers to run pilot with parallel legacy and blueprint scoring for 2–4 weeks to calibrate thresholds and penalties.

Make critical rules explicit and rare; overuse leads to constant human reviews.

Expose “why did I fail” UI showing per-behavior evidence and penalties to speed remediation.